import copy,json
import pytest
from fastapi.testclient import TestClient
from app import configuration,rule_store,auth,system_settings
from app.main import app
from test_recovery import login,headers

RULE={'enabled':True,'definition':{'name':'Serveur','kind':'list','category':'SERVER','secret':False,'terms':['srv-secret-local']}}

def configure(path,**changes):
    data=json.loads(path.read_text());data.update(changes);path.write_text(json.dumps(data));return data

@pytest.mark.parametrize('patch',[
 {'rules':[{'enabled':True,'definition':{'name':'CANARY','kind':'regex','pattern':'('}}]},
 {'networks':[{'name':'A','cidrs':['10.0.0.0/24']},{'name':'B','cidrs':['10.0.0.0/25']}]},
 {'networks':[{'name':'A','vlan':12,'cidrs':['10.0.0.0/24']},{'name':'B','vlan':12,'cidrs':['10.1.0.0/24']}]},
 {'networks':[{'name':'A','cidrs':['2001:db8::/32']}]},
 {'rules':[RULE,RULE]}, {'unexpected':'CANARY'}, {'version':0}
])
def test_invalid_files_fail_closed(deployed,patch):
    configure(deployed[0],**patch)
    with pytest.raises(RuntimeError) as err:configuration.initialize()
    assert 'CANARY' not in str(err.value)

def test_duplicate_json_keys_rejected(deployed):
    deployed[0].write_text('{"version":1,"version":2}')
    with pytest.raises(RuntimeError):configuration.initialize()

@pytest.mark.parametrize('settings',[{'issuer':'http://sso.test/realms/test'},{'issuer':'file:///etc/passwd'},{'max_text_mib':11},{'user_role':'admin'}])
def test_invalid_settings_fail(deployed,settings):
    data=json.loads(deployed[0].read_text());data['settings'].update(settings);deployed[0].write_text(json.dumps(data))
    with pytest.raises(RuntimeError):configuration.initialize()

def test_snapshot_and_readonly_endpoints(deployed):
    configure(deployed[0],rules=[RULE])
    with TestClient(app) as c:
        h=headers(login(c).json()['access_token'])
        before=c.get('/api/admin/rules',headers=h).json()
        configure(deployed[0],rules=[])
        assert c.get('/api/admin/rules',headers=h).json()==before
        for method,path in [('POST','/api/admin/rules'),('PUT','/api/admin/rules/1'),('POST','/api/admin/rules/1/state'),('POST','/api/admin/networks'),('PUT','/api/admin/networks/1'),('PUT','/api/system/settings')]:
            assert c.request(method,path,headers=h,json={}).status_code in (404,405)
        r=c.post('/api/admin/rules/1/test',headers=h,json={'version':1,'text':'srv-secret-local'})
        assert r.status_code==200 and r.json()['count']==1
        assert c.get('/api/admin/rules',headers=h).json()==before
        assert c.post('/api/admin/rules/1/test',headers=h,json={'version':2,'text':'sample'}).status_code==409
        r=c.post('/api/analyze',headers=h,json={'text':'srv-secret-local','language':'fr'})
        assert any(hit['category']=='SERVER' for hit in r.json()['detections'])
        public=c.get('/api/config').json()
        assert 'rules' not in public and 'internal_issuer' not in public
    with TestClient(app) as c:assert rule_store.active_rules()==[]

def test_test_rule_error_does_not_modify_snapshot(deployed):
    rule=copy.deepcopy(RULE);rule['definition'].update(kind='regex',pattern='Opale|(?=X)')
    configure(deployed[0],rules=[rule])
    with TestClient(app) as c:
        h=headers(login(c).json()['access_token']);before=configuration.current()
        assert c.post('/api/admin/rules/1/test',headers=h,json={'version':1,'text':'X'}).status_code==422
        assert configuration.current()==before

def test_access_and_keycloak_check(deployed,monkeypatch):
    with TestClient(app) as c:
        monkeypatch.setitem(app.dependency_overrides,auth.current_user,lambda:{'roles':['user']})
        for path in ['/api/admin/rules','/api/admin/networks','/api/system/settings']:assert c.get(path).status_code==403
        monkeypatch.setitem(app.dependency_overrides,auth.current_user,lambda:{'roles':['admin','superadmin']})
        assert c.get('/api/system/settings').status_code==403
        assert c.get('/api/admin/rules').status_code==200
        app.dependency_overrides.clear()
        h=headers(login(c).json()['access_token'])
        seen=[];monkeypatch.setattr(system_settings,'check',lambda s:seen.append(s.issuer))
        assert c.post('/api/system/settings/test',headers=h).status_code==200
        assert seen==['https://sso.test/realms/test']
