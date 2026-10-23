"""Local integration check: authorization code + PKCE; never print tokens/passwords."""
import base64, hashlib, json, secrets, urllib.parse, urllib.request, http.cookiejar
from html.parser import HTMLParser
from pathlib import Path
base='http://localhost:3080'
realm=base+'/auth/realms/prompt-vault/protocol/openid-connect'
users=json.loads((Path(__file__).resolve().parents[1]/'.local/realm.json').read_text())['users']
class Form(HTMLParser):
    action=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='form' and attrs.get('id')=='kc-form-login':self.action=attrs['action']
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def api(path,token=None,data=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    request=urllib.request.Request(base+path,headers=headers,data=None if data is None else json.dumps(data).encode())
    try:
        with urllib.request.urlopen(request) as response:return response.status,response.read()
    except urllib.error.HTTPError as error:return error.code,error.read()

def login(user):
    verifier=secrets.token_urlsafe(48)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state=secrets.token_urlsafe(16)
    # Browsers treat localhost as a secure context; reproduce that only for this local test.
    cookies=urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar(policy=http.cookiejar.DefaultCookiePolicy(secure_protocols=("https","wss","http"))))
    opener=urllib.request.build_opener(cookies)
    url=realm+'/auth?'+urllib.parse.urlencode({'client_id':'prompt-vault-web','response_type':'code','scope':'openid','redirect_uri':base+'/','code_challenge':challenge,'code_challenge_method':'S256','state':state})
    form=Form();form.feed(opener.open(url).read().decode());assert form.action,'Login form missing'
    no_redirect=urllib.request.build_opener(cookies,NoRedirect())
    try:
        no_redirect.open(form.action,urllib.parse.urlencode({'username':user['username'],'password':user['credentials'][0]['value'],'credentialId':''}).encode())
        raise AssertionError('Expected authorization redirect')
    except urllib.error.HTTPError as response:
        
        if response.code!=302:
            import re
            page=response.read().decode()
            print(re.findall(r'<(?:span|p)[^>]*(?:error|instruction)[^>]*>(.*?)</(?:span|p)>',page,re.S))
        assert response.code==302,f'Unexpected login status {response.code}'
        params=urllib.parse.parse_qs(urllib.parse.urlsplit(response.headers['Location']).query)
    assert params['state']==[state]
    payload=urllib.parse.urlencode({'grant_type':'authorization_code','client_id':'prompt-vault-web','redirect_uri':base+'/','code':params['code'][0],'code_verifier':verifier}).encode()
    return json.load(opener.open(realm+'/token',payload)), opener

def main():
    for user in users:
        tokens,opener=login(user);token=tokens['access_token']
        status,body=api('/api/me',token);assert status==200
        assert json.loads(body)['username']==user['username']
        expected=200 if user['username']=='administrateur' else 403
        assert api('/api/admin/status',token)[0]==expected
        status,body=api('/api/analyze-stream',token,{'text':'password=SyntheticIntegrationSecret','language':'fr'})
        assert status==200
        result=json.loads(body.decode().splitlines()[-1]);assert result['type']=='result' and any(hit['secret'] for hit in result['detections'])
        refreshed=json.load(opener.open(realm+'/token',urllib.parse.urlencode({'grant_type':'refresh_token','client_id':'prompt-vault-web','refresh_token':tokens['refresh_token']}).encode()))
        opener.open(realm+'/logout',urllib.parse.urlencode({'client_id':'prompt-vault-web','refresh_token':refreshed['refresh_token']}).encode()).close()
        try:
            opener.open(realm+'/token',urllib.parse.urlencode({'grant_type':'refresh_token','client_id':'prompt-vault-web','refresh_token':refreshed['refresh_token']}).encode())
            raise AssertionError('Refresh succeeded after logout')
        except urllib.error.HTTPError as error:assert error.code==400
        print(user['username']+': connexion PKCE, rôle, analyse, renouvellement et déconnexion OK')
    assert api('/api/analyze-stream',data={'text':'synthetic'})[0]==401
    print('Accès anonyme refusé : OK')

if __name__=='__main__':
    main()
