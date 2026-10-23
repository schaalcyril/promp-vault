"""Offline language selection; no prompt cache survives an analysis."""
import re
import threading
from functools import lru_cache
from langid.langid import LanguageIdentifier,model
_LOCK=threading.Lock()
@lru_cache(maxsize=1)
def identifier():return LanguageIdentifier.from_modelstring(model,norm_probs=True)
def choose(text):
    # Technical fragments and short inputs do not provide reliable linguistic evidence.
    words=re.findall(r'[^\W\d_]{2,}',text,flags=re.UNICODE)
    if len(words)<8:return ('fr','en'),'uncertain'
    with _LOCK:code,score=identifier().classify(text[:4000])
    if score<0.90:return ('fr','en'),'uncertain'
    if code not in ('fr','en'):return ('fr','en'),'unsupported'
    return (code,),code

def passages(text):
    start=0
    for match in re.finditer(r'\n[ \t]*\n',text):
        end=match.end()
        if end-start>=100:
            for base in range(start,end,18000):yield base,text[base:min(base+20000,end)]
            start=end
    for base in range(start,len(text),18000):yield base,text[base:base+20000]
