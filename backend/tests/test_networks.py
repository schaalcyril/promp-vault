import json
from fastapi.testclient import TestClient
from app import networks
from app.main import app
from test_configuration import configure
from test_recovery import login,headers
D={'name':'Production','vlan':120,'cidrs':['10.20.1.0/24','10.20.2.0/24'],'enabled':True}

def test_network_snapshot_api_and_stream(deployed):
    configure(deployed[0],networks=[D])
    with TestClient(app) as c:
        h=headers(login(c).json()['access_token'])
        configure(deployed[0],networks=[])
        assert len(networks.snapshot())==2
        assert c.post('/api/admin/networks/test',headers=h,json={'address':'10.20.2.9'}).json()['matches'][0]['name']=='Production'
        for path in ['/api/analyze','/api/analyze-stream']:
            r=c.post(path,headers=h,json={'text':'10.20.1.12 contacte 10.20.2.18','language':'fr'})
            assert r.status_code==200
            result=r.json() if path=='/api/analyze' else next(m for m in map(json.loads,r.text.splitlines()) if m['type']=='result')
            assert [x.get('network_label') for x in result['detections'] if x['category']=='IP']==['VLAN_1_RESEAU_1','VLAN_1_RESEAU_2']
            assert 'Production' not in r.text
    with TestClient(app):assert networks.snapshot()==[]
