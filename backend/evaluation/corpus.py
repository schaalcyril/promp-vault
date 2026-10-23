"""Versioned synthetic fixtures. No production data. Spans are code points."""
def case(name, text, entities=(), language='fr', split='regression'):
    spans=[]
    for value, category in entities:
        start=text.index(value)
        spans.append(dict(start=start,end=start+len(value),category=category))
    return dict(name=name,text=text,expected=spans,language=language,split=split)

CASES = [
 case('ipv4-cidr','Source 10.20.30.15/24 vers 172.16.1.2.', [('10.20.30.15/24','IP'),('172.16.1.2','IP')]),
 case('ipv6','Connexion à [2001:db8::15]:443 puis fe80::1%eth0.', [('2001:db8::15','IP'),('fe80::1%eth0','IP')]),
 case('ipv6-cidr','Route 2001:db8:abcd::/48 via 2001:db8::1.', [('2001:db8:abcd::/48','IP'),('2001:db8::1','IP')]),
 case('mac','Interface MAC aa:bb:cc:dd:ee:ff.', [('aa:bb:cc:dd:ee:ff','MAC')]),
 case('fqdn','SSH srv-prod-db01.client.local port 22.', [('srv-prod-db01.client.local','FQDN')]),
 case('host','Redémarrer srv-prod-01 avec systemctl.', [('srv-prod-01','HOSTNAME')]),
 case('email','Contacter jean.dupont@example.com.', [('jean.dupont@example.com','EMAIL')]),
 case('person-fr','Jean Dupont rencontre un problème de connexion.', [('Jean Dupont','PERSON')]),
 case('person-en','John Smith cannot connect to the server.', [('John Smith','PERSON')], 'en'),
 case('password','password=SuperSecret123', [('SuperSecret123','PASSWORD')]),
 case('json-secret','{"password": "Secret Avec Espaces!", "port": 5432}', [('Secret Avec Espaces!','PASSWORD')]),
 case('yaml-secret','password: "Secret Avec Espaces!"\nport: 5432', [('Secret Avec Espaces!','PASSWORD')]),
 case('xml-secret','<password>Secret Avec Espaces!</password>', [('Secret Avec Espaces!','PASSWORD')]),
 case('env-secret','export CLIENT_SECRET="secret-exemple-2026"', [('secret-exemple-2026','TOKEN')]),
 case('bearer','Authorization: Bearer abcdef0123456789', [('abcdef0123456789','TOKEN')]),
 case('uri','postgres://alice:Secret%402026@db.client.local:5432/app', [('alice','USERNAME'),('Secret%402026','PASSWORD'),('db.client.local','FQDN')]),
 case('ad','Compte CORP\\jdupont.', [('CORP\\jdupont','USERNAME')]),
 case('username','Le compte utilisateur est jean.dupont.', [('jean.dupont','USERNAME')]),
 case('private-key','-----BEGIN PRIVATE KEY-----\nYWJjZGVm\n-----END PRIVATE KEY-----', [('-----BEGIN PRIVATE KEY-----\nYWJjZGVm\n-----END PRIVATE KEY-----','PRIVATE_KEY')]),
 case('iban','IBAN FR1420041010050500013M02606', [('FR1420041010050500013M02606','IBAN')]),
 case('card','Carte 4111 1111 1111 1111', [('4111 1111 1111 1111','CARD')]),
 case('technology','PostgreSQL utilise SSH sur le port 5432. HTTP 502, TLS 1.3.'),
 case('filename','Ouvrir package.json puis settings.yaml et app.py.'),
 case('invalid-ip','La valeur 999.999.999.999 est invalide.'),
 case('username-negative','Le compte est bloqué. Un utilisateur rencontre une erreur.'),
 case('unicode','😀 Contact jean.dupont@example.com', [('jean.dupont@example.com','EMAIL')]),
 case('holdout-json','{"api_key":"demo_key_ABC987!", "timeout":30}', [('demo_key_ABC987!','TOKEN')],split='challenge'),
 case('holdout-ip','Host [fd12:3456:789a::7]:8443', [('fd12:3456:789a::7','IP')],'en','challenge'),
 case('unknown-secret','Voici les identifiants : admin / Soleil2026!', [('admin','USERNAME'),('Soleil2026!','PASSWORD')],split='challenge'),
 case('client-name','Le client Acme Horizon signale un incident.', [('Acme Horizon','ORGANIZATION')],split='challenge'),
]
