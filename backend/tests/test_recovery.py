import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import recovery,auth
from conftest import PASSWORD

def login(client,password=PASSWORD):return client.post('/api/recovery/login',json={'username':'superadmin','password':password})
def headers(token):return {'Authorization':'Bearer '+token}

def test_local_independent_of_oidc_logout_and_single_session(monkeypatch):
    monkeypatch.setattr(auth,'key_client',lambda url:(_ for _ in ()).throw(AssertionError('OIDC must not be used')))
    with TestClient(app) as c:
        one=login(c).json()['access_token'];two=login(c).json()['access_token']
        assert c.get('/api/me',headers=headers(one)).status_code==401
        assert c.get('/api/me',headers=headers(two)).json()['authentication']=='local'
        assert c.get('/api/system/settings',headers=headers(two)).status_code==200
        assert two not in repr(recovery._session)
        assert c.post('/api/recovery/logout',headers=headers(two)).status_code==204
        assert c.get('/api/me',headers=headers(two)).status_code==401

def test_throttle_and_expiration(monkeypatch):
    with TestClient(app) as c:
        for _ in range(5):assert login(c,'wrong').status_code==401
        assert login(c).status_code==429
        base=recovery.time.monotonic()
        monkeypatch.setattr(recovery.time,'monotonic',lambda:base+901)
        token=login(c).json()['access_token']
        monkeypatch.setattr(recovery.time,'monotonic',lambda:base+2702)
        assert c.get('/api/me',headers=headers(token)).status_code==401

def test_restart_revokes_session_and_credential_snapshot(deployed):
    path,secret=deployed
    with TestClient(app) as c:
        token=login(c).json()['access_token']
        # Mounted changes are not hot-reloaded into a running process.
        secret.write_text('{"salt":"invalid"}')
        assert login(c).status_code==200
    secret.write_text(json.dumps({'salt':'ab'*32,'hash':recovery.password_hash(PASSWORD,'ab'*32)}))
    with TestClient(app) as c:assert c.get('/api/me',headers=headers(token)).status_code==401

@pytest.mark.parametrize('value',[None,'{}','{"salt":"bad","hash":"bad"}'])
def test_missing_or_invalid_secret_blocks_startup(deployed,value):
    secret=deployed[1]
    if value is None:secret.unlink()
    else:secret.write_text(value)
    with pytest.raises(RuntimeError,match='Secret'):
        with TestClient(app):pass

def test_login_does_not_echo_or_accept_oversized_input():
    with TestClient(app) as c:
        r=c.post('/api/recovery/login',json={'username':'x','password':'CANARY'*100})
        assert r.status_code==422 and 'CANARY' not in r.text
        assert c.post('/api/recovery/login',content=b'x'*4097).status_code==413
        assert c.get('/api/recovery/setup').status_code==404
        assert c.post('/api/recovery/setup',json={}).status_code==404
        assert c.post('/api/recovery/password',json={}).status_code==404


def test_rotation_requires_restart_and_invalidates_old_password(deployed):
    _,secret=deployed
    new_password='another-synthetic-local-password'
    with TestClient(app) as c:
        token=login(c).json()['access_token']
        salt='cd'*32
        secret.write_text(json.dumps({'salt':salt,'hash':recovery.password_hash(new_password,salt)}))
        assert c.get('/api/me',headers=headers(token)).status_code==200
    with TestClient(app) as c:
        assert c.get('/api/me',headers=headers(token)).status_code==401
        assert login(c).status_code==401
        assert login(c,new_password).status_code==200


def test_concurrent_login_is_bounded():
    with TestClient(app) as c:
        recovery._lock.acquire()
        try:assert login(c).status_code==429
        finally:recovery._lock.release()
