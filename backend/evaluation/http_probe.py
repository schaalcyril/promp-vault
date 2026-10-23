"""Run against the local pilot to verify disconnect cleanup through nginx."""
import json,time,urllib.request,urllib.error
URL='http://localhost:3080/api/analyze-stream'
def request(text):
    return urllib.request.Request(URL,data=json.dumps({'text':text,'language':'fr'}).encode(),headers={'Content-Type':'application/json'})
response=urllib.request.urlopen(request('INFO completed status=200\n'*50000),timeout=30)
assert json.loads(response.readline())['type']=='progress'
response.close();started=time.monotonic()
while True:
    try:
        with urllib.request.urlopen(request('password=SyntheticCancelProbe'),timeout=30) as response:
            events=[json.loads(line) for line in response]
        assert events[-1]['type']=='result'
        break
    except urllib.error.HTTPError as error:
        if error.code!=429 or time.monotonic()-started>5:raise
        time.sleep(.1)
print(json.dumps({'cancel_then_small_analysis_seconds':round(time.monotonic()-started,3),'completed':True}))
