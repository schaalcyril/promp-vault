from app.languages import choose,passages
from app.engine import detect
FR='Bonjour, je vous contacte car notre serveur de production ne répond plus depuis ce matin. Pouvez-vous nous aider à comprendre cette panne et à rétablir le service ?'
EN='Hello, I am contacting you because our production server has stopped responding this morning. Could you please help us investigate this issue and restore the service?'
def test_local_language_recognition_and_uncertainty():
    assert choose(FR)==(('fr',),'fr')
    assert choose(EN)==(('en',),'en')
    assert choose('192.168.1.10 500')==(('fr','en'),'uncertain')
    assert choose('Este documento contiene información sobre los empleados de nuestra empresa y explica cómo resolver los problemas de acceso a los servicios internos.')[1]=='unsupported'
def test_mixed_passages_and_unicode_offsets():
    text='😀 '+FR+'\n\n'+EN+' Contact Sarah Johnson at sarah@example.com.'
    info={};hits=detect(text,'auto',language_info=info)
    assert set(info['detected'])=={'fr','en'}
    assert any(text[h['start']:h['end']]=='sarah@example.com' for h in hits)
    assert ''.join(chunk for _,chunk in passages(text))==text

def test_short_text_keeps_secrets_and_reports_fallback():
    info={};hits=detect('password=VerySecretExample123','auto',language_info=info)
    assert info['uncertain']
    assert any(hit['secret'] for hit in hits)
def test_manual_override():
    info={};detect(EN,'fr',language_info=info)
    assert info=={'mode':'fr','detected':['fr'],'uncertain':False,'unsupported':False}
