"""Snapshot spans for generated varied fixtures before and after an optimization."""
import json,sys,hashlib
from app.engine import detect,analyzer
analyzer()
cases={
 'mixed-fr':('Jean Dupont contacte alice@example.com. Tel +33 6 12 34 56 78. Carte 4111 1111 1111 1111.\n'*240,'fr'),
 'mixed-en':('John Smith reports an issue. Phone +1 202-555-0123. Host srv-prod-42.\n'*300,'en'),
 'varied':(''.join(f'INFO event={i:06d} status=200 duration={i%97}ms operation=read\n' for i in range(450)),'fr'),
 'boundaries':('x '*8987+'😀 Jean Dupont\npassword="Secret With Space"\n'+('A short sentence. '*1200),'fr'),
}
output={}
for name,(text,lang) in cases.items():
 hits=detect(text,lang)
 output[name]={'sha256':hashlib.sha256(text.encode()).hexdigest(),'hits':hits}
with open(sys.argv[1],'w') as f:json.dump(output,f,ensure_ascii=False,indent=2)
print({k:len(v['hits']) for k,v in output.items()})
