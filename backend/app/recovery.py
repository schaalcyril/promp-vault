"""One-process local access: deployment hash, bounded in-memory sessions and guard."""
import hashlib
import hmac
import os
import secrets
import threading
import time
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field, ConfigDict
from .credentials import read, password_hash

router=APIRouter(prefix='/api/recovery')
PREFIX='pvlocal_'
_lock=threading.Lock()
_config=None
_session=None
_attempts=0
_window=0.0

def clear_sessions():
    global _session,_attempts,_window
    with _lock:_session=None;_attempts=0;_window=0.0

def initialize():
    global _config
    _config=read(os.environ.get('LOCAL_ADMIN_CREDENTIALS_FILE','/run/secrets/superadmin.json'))
    clear_sessions()

class Login(BaseModel):
    model_config=ConfigDict(extra='forbid')
    username: str=Field(min_length=1,max_length=100)
    password: str=Field(min_length=1,max_length=256)

@router.post('/login')
def login(data:Login):
    global _session,_attempts,_window
    # Nonblocking lock bounds expensive scrypt work and concurrent login requests.
    if not _lock.acquire(blocking=False):raise HTTPException(429,'Connexion en cours. Réessayez.',headers={'Retry-After':'1'})
    try:
        if _config is None:raise HTTPException(503,'Accès local indisponible')
        now=time.monotonic()
        if _attempts==0 or now-_window>=900:_attempts=0;_window=now
        if _attempts>=5:raise HTTPException(429,'Trop de tentatives. Réessayez après 15 minutes.',headers={'Retry-After':str(max(1,int(900-(now-_window))))})
        _attempts+=1
        valid=hmac.compare_digest(password_hash(data.password,_config['salt']),_config['hash'])
        if not (valid and hmac.compare_digest(data.username.encode(),b'superadmin')):raise HTTPException(401,'Identifiants non valides')
        token=PREFIX+secrets.token_urlsafe(32)
        _session=(hashlib.sha256(token.encode()).hexdigest(),time.monotonic()+1800)
        _attempts=0
        return {'access_token':token,'expires_in':1800,'username':'superadmin','roles':['user','admin','superadmin']}
    finally:_lock.release()

def authenticate(token):
    if len(token)>100:raise HTTPException(401,'Session non valide')
    with _lock:
        if not _session or _session[1]<=time.monotonic() or not hmac.compare_digest(_session[0],hashlib.sha256(token.encode()).hexdigest()):
            raise HTTPException(401,'Session locale expirée ou révoquée')
    return {'id':'local:superadmin','username':'superadmin','roles':['user','admin','superadmin'],'authentication':'local'}

@router.post('/logout',status_code=204)
def logout(authorization:str=Header(default='')):
    global _session
    if not authorization.startswith('Bearer '+PREFIX):raise HTTPException(401,'Session locale requise')
    digest=hashlib.sha256(authorization.removeprefix('Bearer ').encode()).hexdigest()
    with _lock:
        if _session and hmac.compare_digest(_session[0],digest):_session=None
