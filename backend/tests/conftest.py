import json
import pytest
from app import configuration,recovery
from app.credentials import password_hash
PASSWORD='synthetic-local-password-for-tests'

@pytest.fixture(scope='session')
def credential():
    salt='ab'*32
    return {'salt':salt,'hash':password_hash(PASSWORD,salt)}

@pytest.fixture(autouse=True)
def deployed(tmp_path,monkeypatch,credential):
    from app.main import app
    config={'version':1,'settings':{'issuer':'https://sso.test/realms/test','client_id':'prompt-vault-web','audience':'prompt-vault-api'},'rules':[],'networks':[]}
    path=tmp_path/'application.json';path.write_text(json.dumps(config))
    secret=tmp_path/'superadmin.json';secret.write_text(json.dumps(credential))
    monkeypatch.setenv('APP_CONFIG_FILE',str(path));monkeypatch.setenv('LOCAL_ADMIN_CREDENTIALS_FILE',str(secret))
    monkeypatch.delenv('ALLOW_INSECURE_OIDC',raising=False)
    configuration.initialize();recovery.initialize()
    yield path,secret
    app.dependency_overrides.clear();recovery.clear_sessions()
