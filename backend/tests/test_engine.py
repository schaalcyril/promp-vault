from app.engine import detect

def test_secrets_and_network():
    text = 'password=SuperSecret123\nBearer abcdef0123456789\nsrv-prod-01.local 10.2.3.4/24 PostgreSQL port 5432'
    hits = detect(text, use_nlp=False)
    values = [text[h['start']:h['end']] for h in hits]
    assert 'SuperSecret123' in values
    assert '10.2.3.4/24' in values
    assert 'srv-prod-01.local' in values
    assert not any('5432' in v or 'PostgreSQL' in v for v in values)

def test_private_key_multiline():
    text = '-----BEGIN PRIVATE KEY-----\nabcdefghi\n-----END PRIVATE KEY-----'
    hits = detect(text, use_nlp=False)
    assert len(hits) == 1 and hits[0]['secret'] and hits[0]['end'] == len(text)

def test_url_credentials_never_restorable():
    text = 'postgres://admin:SuperSecret123@db.client.local:5432/app'
    hits = detect(text, use_nlp=False)
    assert any(h['secret'] and 'SuperSecret123' in text[h['start']:h['end']] for h in hits)

def test_no_invalid_ip():
    assert not any(h['category']=='IP' for h in detect('999.999.999.999', use_nlp=False))

def test_nlp_offline(monkeypatch):
    import socket
    def blocked(*args, **kwargs):
        raise AssertionError('Unexpected network access')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    text = 'Jean Dupont est joignable à jean.dupont@example.com et au 10.20.30.15.'
    hits = detect(text)
    assert any(h['category'] == 'EMAIL' for h in hits)
    assert any(h['category'] == 'IP' for h in hits)


def test_validation_does_not_echo_input(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.rule_store import active_rules
    monkeypatch.setitem(app.dependency_overrides,active_rules,lambda:[])
    from app.auth import current_user
    monkeypatch.setitem(app.dependency_overrides,current_user,lambda:{"id":"test","roles":["user"]})
    with TestClient(app) as client:
        response = client.post('/api/analyze', json={'text':'PRIVATE_CANARY', 'language':'PRIVATE_CANARY'})
        assert response.status_code == 422
        assert 'PRIVATE_CANARY' not in response.text
