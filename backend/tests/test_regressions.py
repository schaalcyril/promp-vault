import pytest
from app.engine import detect,resolve

@pytest.mark.parametrize('text,value,category', [
 ('[2001:db8:1234::ab]:443','2001:db8:1234::ab','IP'),
 ('réseau fdab:cdef::/64','fdab:cdef::/64','IP'),
 ('interface fe80::abcd%enp2s0','fe80::abcd%enp2s0','IP'),
 ('MAC 12:34:56:78:9a:bc','12:34:56:78:9a:bc','MAC'),
 ('{"password":"valeur autre avec espaces"}','valeur autre avec espaces','PASSWORD'),
 ('<password>différent &amp; secret</password>','différent &amp; secret','PASSWORD'),
 ('API_KEY = "autre_token_fictif"','autre_token_fictif','TOKEN'),
 ('postgres://bob:AutreSecret@db.example.net:5432/a','bob','USERNAME'),
 ('credentials: operator / AnotherSecret!','AnotherSecret!','PASSWORD'),
 ('Compte EXAMPLE\\operator.','EXAMPLE\\operator','USERNAME'),
 ('Le client Nova Industrie signale un incident.','Nova Industrie','ORGANIZATION'),
])
def test_exact_spans(text,value,category):
    hits=detect(text,use_nlp=False)
    assert any(text[h['start']:h['end']]==value and h['category']==category for h in hits)

@pytest.mark.parametrize('text',[
 'Le compte est verrouillé. Un utilisateur signale une panne.',
 'Ouvrir config.yaml puis main.ts et README.md.',
 'Adresse 999.1.2.3 invalide ; IPv6 2001:db8::gg invalide.',
])
def test_negative_rules(text):
    assert detect(text,use_nlp=False)==[]

def test_domain_with_file_suffix_is_not_globally_allowed():
    assert any(h['category']=='FQDN' for h in detect('https://client.sh/login',use_nlp=False))

def test_overlapping_secret_cannot_become_restorable():
    candidates=[dict(start=0,end=10,category='PERSON',secret=False,_priority=1),dict(start=3,end=8,category='PASSWORD',secret=True,_priority=4)]
    assert resolve(candidates)==[dict(start=3,end=8,category='PASSWORD',secret=True)]

def test_secret_across_nlp_boundary():
    value='mot secret synthétique'
    text=' ' * 17990 + '<password>'+value+'</password>'
    hits=detect(text)
    assert any(text[h['start']:h['end']]==value and h['secret'] for h in hits)

def test_email_in_url_query_is_not_ignored():
    text='https://portal.example.net/?email=alice@example.org'
    assert any(text[h['start']:h['end']]=='alice@example.org' and h['category']=='EMAIL' for h in detect(text,use_nlp=False))

def test_secret_json_escaped_quote():
    value=r'a\"b secret'
    text='{"password":"'+value+'"}'
    assert any(text[h['start']:h['end']]==value and h['secret'] for h in detect(text,use_nlp=False))

def test_ipv4_trailing_punctuation():
    text='Joindre 192.0.2.42.'
    assert any(text[h['start']:h['end']]=='192.0.2.42' for h in detect(text,use_nlp=False))

def test_uri_components_remain_separate():
    text='mysql://alice:AnotherSecret@db.customer.internal:3306/service'
    hits=detect(text,use_nlp=False)
    assert [(text[h['start']:h['end']],h['category']) for h in hits]==[('alice','USERNAME'),('AnotherSecret','PASSWORD'),('db.customer.internal','FQDN')]
