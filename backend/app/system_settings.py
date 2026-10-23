"""Read-only deployment settings and diagnostic Keycloak check."""
import os
from urllib.parse import urlsplit
import httpx
from pydantic import BaseModel, Field, ConfigDict, model_validator
from fastapi import APIRouter, Depends, HTTPException

class Settings(BaseModel):
    model_config=ConfigDict(extra='forbid')
    issuer: str=Field(max_length=500)
    internal_issuer: str=Field(default='',max_length=500)
    client_id: str=Field(min_length=1,max_length=100)
    audience: str=Field(min_length=1,max_length=100)
    user_role: str=Field(default='user',min_length=1,max_length=100)
    admin_role: str=Field(default='admin',min_length=1,max_length=100)
    default_language: str=Field(default='auto',pattern='^(auto|fr|en)$')
    max_text_mib: int=Field(default=10,ge=1,le=10)

    @model_validator(mode='after')
    def urls(self):
        self.issuer=self.issuer.rstrip('/')
        self.internal_issuer=self.internal_issuer.rstrip('/')
        for value in (self.issuer,self.internal_issuer):
            if not value:continue
            parsed=urlsplit(value)
            if '/realms/' not in parsed.path or not parsed.path.rsplit('/realms/',1)[1] or '/' in parsed.path.rsplit('/realms/',1)[1]:
                raise ValueError('URL complète du realm requise')
            if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.scheme not in ('http','https'):
                raise ValueError('URL du realm non valide')
            if parsed.scheme=='http' and parsed.hostname not in ('localhost','127.0.0.1','::1') and os.getenv('ALLOW_INSECURE_OIDC')!='true':
                raise ValueError('HTTPS requis')
        if not self.issuer or self.user_role==self.admin_role:
            raise ValueError('Realm et rôles distincts requis')
        return self

def load():
    from .configuration import current
    config=current()
    return {'definition':config['settings'],'version':config['version']}

def jwks_url(config):
    return (config['internal_issuer'] or config['issuer'])+'/protocol/openid-connect/certs'

def check(config):
    base=config.internal_issuer or config.issuer
    try:
        with httpx.Client(timeout=4,follow_redirects=False,trust_env=False) as client:
            def fetch(url):
                with client.stream('GET',url) as response:
                    response.raise_for_status();body=b''
                    for chunk in response.iter_bytes():
                        body+=chunk
                        if len(body)>131072:raise ValueError()
                    import json
                    return json.loads(body)
            metadata=fetch(base+'/.well-known/openid-configuration')
            if metadata.get('issuer')!=config.issuer or 'S256' not in metadata.get('code_challenge_methods_supported',[]):raise ValueError()
            keys=fetch(jwks_url(config.model_dump()))
            if not any(k.get('kty')=='RSA' and k.get('use','sig')=='sig' for k in keys.get('keys',[])):raise ValueError()
    except (httpx.HTTPError,ValueError,TypeError,AttributeError):
        raise HTTPException(422,'Connexion Keycloak non validée. Vérifiez les URL du realm, sa disponibilité et PKCE S256.') from None

from .auth import super_administrator
router=APIRouter(prefix='/api/system',dependencies=[Depends(super_administrator)])

@router.get('/settings')
def get_settings():return load()

@router.post('/settings/test')
def test_settings():
    check(Settings.model_validate(load()['definition']))
    return {'message':'Realm et clés publiques accessibles. Vérifiez ensuite la connexion utilisateur.'}
