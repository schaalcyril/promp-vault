from app.engine import detect
import app.engine as engine

def test_repeated_secrets_keep_all_offsets():
    line='password=RepeatedSyntheticSecret\n'
    text=line*700
    hits=detect(text,use_nlp=False)
    assert len(hits)==700
    assert all(text[h['start']:h['end']]=='RepeatedSyntheticSecret' and h['secret'] for h in hits)
    assert [h['start'] for h in hits]==[9+i*len(line) for i in range(700)]

def test_secret_cache_is_not_shared_between_requests(monkeypatch):
    calls=[]
    original=engine.scan_line
    def scan(line):
        calls.append(line)
        return original(line)
    monkeypatch.setattr(engine,'scan_line',scan)
    text='password=AnotherSyntheticSecret\n'*20
    first=detect(text,use_nlp=False)
    count=len(calls)
    assert count==1
    second=detect(text,use_nlp=False)
    assert len(calls)==2 and first==second
