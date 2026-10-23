import pytest
from app.auth import current_user

@pytest.fixture(autouse=True)
def authenticated_job_tests(monkeypatch):
    from app.main import app
    from app.rule_store import active_rules
    app.dependency_overrides[active_rules]=lambda:[]
    app.dependency_overrides[current_user]=lambda:{"id":"synthetic","roles":["user"]}
    yield
    app.dependency_overrides.pop(current_user,None)
    app.dependency_overrides.pop(active_rules,None)

import time
import multiprocessing as mp
from app.jobs import start,stop

def test_progress_result_and_cleanup():
    process,reader=start('password=AnotherSyntheticSecret','fr')
    messages=[]
    try:
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if reader.poll(.1):
                message=reader.recv();messages.append(message)
                if message['type'] in ('result','error'):break
        assert messages[-1]['type']=='result'
        percentages=[m['percent'] for m in messages if m['type']=='progress']
        assert percentages==sorted(percentages)
        assert messages[-1]['detections']
    finally:stop(process,reader)
    assert not process.is_alive()

def test_terminate_stops_actual_computation():
    process,reader=start('ordinary log line\n'*100000,'fr')
    pid=process.pid
    started=time.monotonic();stop(process,reader)
    assert not process.is_alive()
    assert process.exitcode is not None
    assert time.monotonic()-started<3
    assert pid not in [p.pid for p in mp.active_children()]

def test_stream_response_complete():
    from fastapi.testclient import TestClient
    from app.main import app
    import json
    with TestClient(app) as client:
        response=client.post('/api/analyze-stream',json={'text':'password=StreamSyntheticSecret','language':'fr'})
        assert response.status_code==200
        events=[json.loads(line) for line in response.text.splitlines()]
        assert events[0]['type']=='progress'
        assert events[-1]['type']=='result'
        assert response.headers['cache-control']=='no-store'


def test_busy_stream_rejects_without_queueing():
    from fastapi.testclient import TestClient
    import app.main as main
    import asyncio
    class Busy:
        def locked(self):return True
    saved=main.semaphore;main.semaphore=Busy()
    try:
        with TestClient(main.app) as client:
            response=client.post('/api/analyze-stream',json={'text':'synthetic','language':'fr'})
            assert response.status_code==429
    finally:main.semaphore=saved
