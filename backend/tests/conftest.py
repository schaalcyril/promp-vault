import json
import pytest
from app import configuration
@pytest.fixture(autouse=True)
def deployed(tmp_path,monkeypatch):
    from app.main import app
    config={'version':1,'settings':{'default_language':'auto','max_text_mib':10},'rules':[],'networks':[]}
    path=tmp_path/'application.json';path.write_text(json.dumps(config))
    monkeypatch.setenv('APP_CONFIG_FILE',str(path))
    configuration.initialize()
    yield (path,)
    app.dependency_overrides.clear()
