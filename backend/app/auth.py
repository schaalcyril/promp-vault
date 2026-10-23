"""Validate API access tokens; no insecure development bypass."""
import jwt
from functools import lru_cache
from jwt import PyJWKClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer=HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials | None=Security(bearer)):
    if credentials is None or credentials.scheme.lower()!='bearer':
        raise HTTPException(401,'Connexion requise',headers={'WWW-Authenticate':'Bearer'})
    from .recovery import PREFIX, authenticate
    if credentials.credentials.startswith(PREFIX):
        return authenticate(credentials.credentials)
    from .system_settings import load, jwks_url
    config=load()['definition']
    client=key_client(jwks_url(config))
    try:
        key=client.get_signing_key_from_jwt(credentials.credentials)
        claims=jwt.decode(credentials.credentials,key.key,algorithms=['RS256'],audience=config['audience'],issuer=config['issuer'],options={'require':['exp','iat','sub','iss','aud']})
        if claims.get('azp')!=config['client_id'] or claims.get('typ')!='Bearer':
            raise jwt.InvalidTokenError()
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503,'Service de connexion indisponible') from None
    except jwt.PyJWTError:
        raise HTTPException(401,'Session non valide ou expirée',headers={'WWW-Authenticate':'Bearer'}) from None
    roles=claims.get('realm_access',{}).get('roles',[])
    if not {config['user_role'],config['admin_role']}.intersection(roles):
        raise HTTPException(403,'Accès non autorisé')
    return {'id':claims['sub'],'username':claims.get('preferred_username',''),'roles':(['user','admin'] if config['admin_role'] in roles else ['user'])}

def administrator(user=Security(current_user)):
    if 'admin' not in user['roles']:
        raise HTTPException(403,'Rôle administrateur requis')
    return user

@lru_cache(maxsize=8)
def key_client(url):
    from .tls import oidc_ssl_context
    return PyJWKClient(url,timeout=5,ssl_context=oidc_ssl_context())

def super_administrator(user=Security(current_user)):
    if user.get('authentication')!='local' or 'superadmin' not in user['roles']:
        raise HTTPException(403,'Super administrateur local requis')
    return user
