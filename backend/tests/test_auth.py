import time
from types import SimpleNamespace
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from app import auth
from app.main import app

@pytest.fixture
def signing(monkeypatch):
    from app import system_settings
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    monkeypatch.setattr(auth,'key_client',lambda url:SimpleNamespace(get_signing_key_from_jwt=lambda token:SimpleNamespace(key=key.public_key())))
    def token(**changes):
        claims={'sub':'test','iss':'https://sso.test/realms/test','aud':'prompt-vault-api','azp':'prompt-vault-web','typ':'Bearer','iat':int(time.time()),'exp':int(time.time())+60,'realm_access':{'roles':['user']}}
        claims.update(changes)
        return jwt.encode(claims,key,algorithm='RS256')
    return token

def test_all_sensitive_endpoints_require_login():
    with TestClient(app,raise_server_exceptions=False) as client:
        for path in ('/api/analyze','/api/analyze-stream'):
            assert client.post(path,json={'text':'synthetic'}).status_code==401
        assert client.get('/api/me').status_code==401
        assert client.get('/api/admin/status').status_code==401
        assert client.get('/api/health').status_code==200

@pytest.mark.parametrize('changes',[{'exp':0},{'iss':'https://wrong.test'},{'aud':'wrong'},{'azp':'other-client'},{'typ':'ID'},{'sub':None}])
def test_invalid_claims_rejected(signing,changes):
    with pytest.raises(HTTPException) as error:
        auth.current_user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=signing(**changes)))
    assert error.value.status_code==401

def test_roles_enforced(signing):
    client=TestClient(app)
    headers={'Authorization':'Bearer '+signing()}
    assert client.get('/api/me',headers=headers).json()['roles']==['user']
    assert client.get('/api/admin/status',headers=headers).status_code==403
    headers={'Authorization':'Bearer '+signing(realm_access={'roles':['admin','user']})}
    assert client.get('/api/admin/status',headers=headers).status_code==200
    headers={'Authorization':'Bearer '+signing(realm_access={'roles':[]})}
    assert client.get('/api/me',headers=headers).status_code==403

def test_modified_signature_rejected(signing):
    token=signing(); parts=token.split('.');parts[2]=('A' if parts[2][0]!='A' else 'B')+parts[2][1:]
    assert TestClient(app).get('/api/me',headers={'Authorization':'Bearer '+'.'.join(parts)}).status_code==401

def test_dynamic_oidc_configuration_and_external_roles_never_grant_superadmin(signing,monkeypatch):
    from app import system_settings
    config=system_settings.load()['definition']|{'issuer':'https://sso.test/realms/new','audience':'new-api','client_id':'new-web','admin_role':'rules-manager','user_role':'member'}
    monkeypatch.setattr(system_settings,'load',lambda:{'definition':config,'version':2})
    token=signing(iss=config['issuer'],aud=config['audience'],azp=config['client_id'],realm_access={'roles':['rules-manager','superadmin']})
    client=TestClient(app);headers={'Authorization':'Bearer '+token}
    response=client.get('/api/me',headers=headers)
    assert response.status_code==200 and response.json()['roles']==['user','admin']
    assert client.get('/api/system/settings',headers=headers).status_code==403
    assert client.get('/api/me',headers={'Authorization':'Bearer '+signing()}).status_code==401
