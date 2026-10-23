"""Reproducible synthetic throughput probe; no accuracy claim for these logs."""
import json,time,resource,signal,argparse
from app.engine import analyzer,detect
p=argparse.ArgumentParser();p.add_argument('--size',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--profile',choices=['repeated','varied'],default='repeated');a=p.parse_args()
line='INFO service request completed status=200 duration=42ms operation=read route=/health check=ready\n'
prefix='password=SyntheticBenchmarkSecret\nserver=192.0.2.15\n'
if a.profile=='repeated':
    text=(prefix+(line*((a.size//len(line))+1)))[:a.size]
else:
    lines=(f'INFO event={i:08d} status=200 duration={i%97}ms operation=read route=/health check=ready\n' for i in range(a.size//70+1))
    text=(prefix+''.join(lines))[:a.size]
analyzer()
def expired(*args):raise TimeoutError()
signal.signal(signal.SIGALRM,expired);signal.alarm(300)
start=time.perf_counter();last=0
try:
    def progress(percent,phase):
        global last
        if percent>=last+10:print(json.dumps({'percent':percent,'phase':phase}),flush=True);last=percent
    hits=detect(text,progress=progress)
    result={'bytes':len(text.encode()),'seconds':round(time.perf_counter()-start,2),'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),'detections':len(hits),'status':'completed'}
except TimeoutError:
    result={'bytes':a.size,'seconds':round(time.perf_counter()-start,2),'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),'status':'timeout_300s'}
signal.alarm(0)
result['profile']=a.profile
with open(a.output,'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
