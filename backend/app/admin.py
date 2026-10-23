import threading
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .auth import administrator
from .custom_rules import match_rules, RuleExecutionError
from . import rule_store

router=APIRouter(prefix='/api/admin', dependencies=[Depends(administrator)])
tests=threading.BoundedSemaphore(2)

class Sample(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: int=Field(ge=1)
    text: str=Field(min_length=1,max_length=20000)

@router.get('/rules')
def rules():return rule_store.list_rules()

@router.post('/rules/{rule_id}/test')
def test(rule_id:int,data:Sample):
    rule=rule_store.get(rule_id)
    if rule['version']!=data.version:raise HTTPException(409,'Version déployée différente. Rechargez la page.')
    if not tests.acquire(blocking=False):raise HTTPException(429,'Deux tests sont déjà en cours.')
    try:
        try:hits=match_rules(data.text,[rule['definition']],budget=0.5,max_hits=2000)
        except RuleExecutionError as error:raise HTTPException(422,str(error)) from None
        return {'count':len(hits),'matches':[{'start':h['start'],'end':h['end']} for h in hits[:100]],
                'message':'Test terminé. La configuration déployée reste inchangée.'}
    finally:tests.release()
