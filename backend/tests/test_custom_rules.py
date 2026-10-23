import pytest
from pydantic import ValidationError
from app.custom_rules import RuleDefinition, match_rules, RuleExecutionError
from app.engine import detect

def definition(**changes):
    return RuleDefinition(**({'name':'Projets fictifs','terms':['Opale'],'secret':False,'category':'PROJET'}|changes)).model_dump()

def test_list_boundaries_unicode_and_literal_punctuation():
    text='😀 Opale opale Opales préOpale A+B'
    hits=match_rules(text,[definition(terms=['Opale','A+B'])])
    assert [text[h['start']:h['end']] for h in hits]==['Opale','opale','A+B']
    assert not any(h['secret'] for h in hits)
    assert len(match_rules(text,[definition(case_sensitive=True)]))==1

@pytest.mark.parametrize('changes',[{'kind':'regex','pattern':'('},{'kind':'regex','pattern':'.*'}, {'terms':[' ']},{'name':' '},{'terms':['x'*201]},{'category':'bad-category'}])
def test_invalid_definitions(changes):
    with pytest.raises(ValidationError):definition(**changes)

def test_regex_whole_match_and_secret_enforcement():
    text='😀 DOSSIER-123456'
    rule=definition(kind='regex',pattern=r'DOSSIER-([0-9]{6})',category='SECRET',secret=False)
    hit=match_rules(text,[rule])[0]
    assert text[hit['start']:hit['end']]=='DOSSIER-123456'
    assert hit['secret']

def test_empty_context_match_fails_instead_of_ignoring():
    rule=definition(kind='regex',pattern=r'(?=Opale)')
    with pytest.raises(RuleExecutionError,match='vide'):match_rules('Opale',[rule])

def test_regex_timeout_and_match_limit_fail_closed():
    with pytest.raises(RuleExecutionError,match='Délai'):
        match_rules('a'*100000+'!',[definition(kind='regex',pattern=r'(a+)+$')],budget=.01)
    with pytest.raises(RuleExecutionError,match='Trop'):
        match_rules('Opale Opale',[definition()],max_hits=1)

def test_custom_rule_cannot_make_builtin_password_restorable():
    text='password=Opale'
    hits=detect(text,use_nlp=False,custom_rules=[definition()])
    assert any(h['secret'] and text[h['start']:h['end']]=='Opale' for h in hits)

def test_global_secret_wins_over_builtin_nonsecret():
    text='10.20.30.40'
    hits=detect(text,use_nlp=False,custom_rules=[definition(terms=[text],secret=True)])
    assert len(hits)==1 and hits[0]['secret']

def test_missing_config_never_silently_drops_rules(monkeypatch):
    from app import configuration
    from app.main import app
    from fastapi.testclient import TestClient
    monkeypatch.setenv('APP_CONFIG_FILE','/missing/application.json')
    with pytest.raises(RuntimeError,match='Configuration'):
        with TestClient(app):pass
