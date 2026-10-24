from . import networks
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
import asyncio
import json
import time
from .system_settings import load as load_settings
from . import rule_store, configuration
from .custom_rules import RuleExecutionError
from .jobs import start, stop, warmup
from .engine import detect, analyzer
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    configuration.initialize()
    analyzer()
    warmup()
    yield

app = FastAPI(title="Prompt Vault — pilote local", lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
semaphore = asyncio.Semaphore(1)
MAX_SECONDS = 600
LIMIT = 10 * 1024 * 1024

@app.middleware("http")
async def protections(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        body_limit = LIMIT * 6 + 1024
        total = 0
        chunks = []
        async for chunk in request.stream():
            total += len(chunk)
            if total > body_limit:
                return JSONResponse({"detail": "Requête trop volumineuse"}, status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({"detail": "Données non valides. Vérifiez les champs et les limites indiquées."}, status_code=422)

@app.exception_handler(Exception)
async def safe_error(request, exc):
    return JSONResponse({"detail": "Analyse interrompue. Aucun résultat validé."}, status_code=500)

class Input(BaseModel):
    text: str = Field(max_length=LIMIT)
    language: str = Field(pattern="^(auto|fr|en)$", default="auto")

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "deployment-config", "authentication": False}

@app.post("/api/analyze")
async def analyze(data: Input, rules=Depends(rule_store.active_rules), settings=Depends(load_settings), network_snapshot=Depends(networks.snapshot)):
    if len(data.text.encode("utf-8")) > settings['definition']['max_text_mib'] * 1024 * 1024:
        return JSONResponse({"detail": "Limite de taille configurée dépassée"}, status_code=413)
    if semaphore.locked():
        return JSONResponse({"detail":"Une analyse est déjà en cours. Réessayez ensuite."},status_code=429)
    async with semaphore:
        language_info={}
        hits = await run_in_threadpool(detect, data.text, data.language, custom_rules=rules,language_info=language_info)
    return {"detections": networks.annotate(data.text,hits,network_snapshot),"language_info":language_info}

@app.post("/api/analyze-stream")
async def analyze_stream(data: Input, rules=Depends(rule_store.active_rules), settings=Depends(load_settings), network_snapshot=Depends(networks.snapshot)):
    if len(data.text.encode("utf-8")) > settings['definition']['max_text_mib'] * 1024 * 1024:
        return JSONResponse({"detail":"Limite de taille configurée dépassée"},status_code=413)
    if semaphore.locked():
        return JSONResponse({"detail":"Une analyse est déjà en cours. Réessayez ensuite."},status_code=429)
    await semaphore.acquire()
    try:
        process,reader=start(data.text,data.language,rules)
    except Exception:
        semaphore.release()
        return JSONResponse({"detail":"Analyse indisponible"},status_code=503)
    async def events():
        started=time.monotonic()
        try:
            while True:
                if time.monotonic()-started>MAX_SECONDS:
                    yield json.dumps({"type":"error","detail":"Durée maximale dépassée (10 minutes). Réduisez le volume."})+"\n"
                    break
                if reader.poll():
                    try:message=reader.recv()
                    except EOFError:message={"type":"error","detail":"Analyse interrompue"}
                    if message['type']=='result':networks.annotate(data.text,message['detections'],network_snapshot)
                    yield json.dumps(message,ensure_ascii=False)+"\n"
                    if message['type'] in ('result','error'):break
                elif not process.is_alive():
                    yield json.dumps({"type":"error","detail":"Analyse interrompue"})+"\n"
                    break
                else:await asyncio.sleep(0.05)
        finally:
            # Runs also on client disconnect: terminate the computing process.
            stop(process,reader)
            semaphore.release()
    return StreamingResponse(events(),media_type="application/x-ndjson",headers={"Cache-Control":"no-store","X-Accel-Buffering":"no"})

@app.get('/api/rules')
def active_rule_catalogue():
    return rule_store.public_catalogue()

@app.exception_handler(RuleExecutionError)
async def rule_error(request, exc):
    return JSONResponse({"detail":str(exc)},status_code=422)

@app.get('/api/config')
def public_config():
    config=load_settings()['definition']
    return {k:config[k] for k in ('default_language','max_text_mib')}
