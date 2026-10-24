import copy,json
import pytest
from fastapi.testclient import TestClient
from app import configuration,rule_store
from app.main import app

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

def test_snapshot_and_public_readonly_endpoints(deployed):
    inactive=copy.deepcopy(RULE);inactive['enabled']=False;inactive['definition']['name']='INACTIVE_CANARY'
    configure(deployed[0],rules=[RULE,inactive])
    with TestClient(app) as c:
        before=c.get('/api/rules').json()
        assert len(before['custom'])==1
        assert before['custom'][0]['name']=='Serveur'
        assert 'srv-secret-local' not in json.dumps(before)
        assert 'INACTIVE_CANARY' not in json.dumps(before)
        configure(deployed[0],rules=[])
        assert c.get('/api/rules').json()==before
        for method,path in [('POST','/api/rules'),('GET','/api/me'),('POST','/api/recovery/login'),('GET','/api/admin/rules'),('GET','/api/system/settings')]:
            assert c.request(method,path,json={}).status_code in (404,405)
        r=c.post('/api/analyze',json={'text':'srv-secret-local','language':'fr'})
        assert r.status_code==200
        assert any(hit['category']=='SERVER' for hit in r.json()['detections'])
        assert c.get('/api/config').json()=={'default_language':'auto','max_text_mib':10}
        assert c.get('/api/health').json()['authentication'] is False
    with TestClient(app) as c:assert c.get('/api/rules').json()['custom']==[]
