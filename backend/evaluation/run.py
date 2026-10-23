"""Exact-span and typed metrics, plus complete coverage against annotated fixtures."""
import argparse,json,time,resource,socket
from collections import defaultdict
from app.engine import detect,analyzer
from evaluation.corpus import CASES

def run():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    # No outbound connection is allowed during warmup or evaluation.
    def blocked(*args, **kwargs): raise RuntimeError('Network forbidden during evaluation')
    socket.socket.connect=blocked
    analyzer()
    rows=[]; totals=defaultdict(lambda:dict(tp=0,fp=0,fn=0,covered=0,expected=0))
    for case in CASES:
        started=time.perf_counter();hits=detect(case['text'],case['language']);elapsed=time.perf_counter()-started
        gold={(x['start'],x['end'],x['category']) for x in case['expected']}
        pred={(x['start'],x['end'],x['category']) for x in hits}
        for key in ['all',case['split']]:
            t=totals[key];t['tp']+=len(gold&pred);t['fp']+=len(pred-gold);t['fn']+=len(gold-pred);t['expected']+=len(gold)
            t['covered']+=sum(any(h['start']<=g['start'] and h['end']>=g['end'] for h in hits) for g in case['expected'])
        for category in {x[2] for x in gold|pred}:
            t=totals['category:'+category];g={x for x in gold if x[2]==category};p={x for x in pred if x[2]==category}
            t['tp']+=len(g&p);t['fp']+=len(p-g);t['fn']+=len(g-p);t['expected']+=len(g)
            t['covered']+=sum(any(h['start']<=start and h['end']>=end for h in hits) for start,end,_ in g)
        rows.append(dict(name=case['name'],split=case['split'],latency_ms=round(elapsed*1000,2),missing=sorted(gold-pred),extra=sorted(pred-gold)))
    for t in totals.values():
        t['precision']=round(t['tp']/(t['tp']+t['fp']),4) if t['tp']+t['fp'] else None
        t['recall']=round(t['tp']/(t['tp']+t['fn']),4) if t['tp']+t['fn'] else None
        t['f1']=round(2*t['tp']/(2*t['tp']+t['fp']+t['fn']),4) if 2*t['tp']+t['fp']+t['fn'] else None
    report=dict(note='Synthetic development corpus, not representative production accuracy. Challenge fixtures are not an independent blind holdout.',cases=len(rows),metrics=dict(totals),peak_rss_mib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),results=rows)
    with open(args.output,'w') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if __name__=='__main__':run()
