"""Generate local-only credentials once, without printing them."""
import json, secrets, os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
private=root/'.local'; private.mkdir(mode=0o700,exist_ok=True)
if (private/'realm.json').exists():
    print('Configuration locale déjà présente ; conservée.')
    raise SystemExit(0)
passwords={name:secrets.token_urlsafe(24) for name in ('keycloak-admin','utilisateur','administrateur')}
realm={'realm':'prompt-vault','enabled':True,'displayName':'Prompt Vault','internationalizationEnabled':True,'supportedLocales':['fr'],'defaultLocale':'fr','sslRequired':'none','registrationAllowed':False,'resetPasswordAllowed':False,'roles':{'realm':[{'name':'user'},{'name':'admin'}]},'clients':[{'clientId':'prompt-vault-web','enabled':True,'publicClient':True,'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':['http://localhost:3080/'],'webOrigins':['http://localhost:3080'],'attributes':{'pkce.code.challenge.method':'S256','post.logout.redirect.uris':'http://localhost:3080/'},'protocolMappers':[{'name':'api-audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':'prompt-vault-api','access.token.claim':'true','id.token.claim':'false'}}]}],'users':[{'username':name,'enabled':True,'firstName':name,'lastName':'Test','email':name+'@example.test','emailVerified':True,'requiredActions':[],'credentials':[{'type':'password','value':passwords[name],'temporary':False}],'realmRoles':['user','admin'] if name=='administrateur' else ['user']} for name in ('utilisateur','administrateur')]}
(private/'realm.json').write_text(json.dumps(realm,indent=2))
# Docker must be able to read this bind mount; its parent is owner-only.
(private/'realm.json').chmod(0o644)
(root/'.env').write_text('KC_BOOTSTRAP_ADMIN_PASSWORD='+passwords['keycloak-admin']+'\n')
(root/'.env').chmod(0o600)
(private/'ACCES.md').write_text('# Comptes locaux de développement\n\nApplication : http://localhost:3080/\nConsole Keycloak : http://localhost:3080/auth/admin/\n\n'+''.join(f'- {name} : `{password}`\n' for name,password in passwords.items()))
(private/'ACCES.md').chmod(0o600)
print('Comptes générés dans .local/ACCES.md (lecture réservée au propriétaire).')
