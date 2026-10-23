"""Verify local recovery against running API, including when Keycloak is stopped."""
from pathlib import Path
import json
import re
import urllib.request
import urllib.error
base='http://localhost:3080'

import argparse,getpass
parser=argparse.ArgumentParser();parser.add_argument('--prompt-password',action='store_true');args=parser.parse_args()
password=getpass.getpass('Mot de passe superadmin : ')
def call(path,token=None,data=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    request=urllib.request.Request(base+path,headers=headers,data=None if data is None else json.dumps(data).encode())
    try:
        with urllib.request.urlopen(request,timeout=15) as response:return response.status,response.read()
    except urllib.error.HTTPError as error:return error.code,error.read()
status,body=call('/api/recovery/login',data={'username':'superadmin','password':password})
assert status==200,f'Login failed: {status}'
payload=json.loads(body)
token=payload['access_token']
try:
    assert call('/api/system/settings',token)[0]==200
    assert call('/api/admin/rules',token)[0]==200
    print('Super administrateur local : consultation configuration et règles : OK')
finally:
    assert call('/api/recovery/logout',token,data={})[0]==204
assert call('/api/admin/rules',token)[0]==401
print('Déconnexion et révocation immédiate : OK')
