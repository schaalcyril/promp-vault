import RestorationSummary from './RestorationSummary';
import LanguageChoice from './LanguageChoice';
import ActiveRules from './ActiveRules';
import {useRef,useState,useMemo} from 'react';
import DetectionReview from './DetectionReview';
import {appConfig} from './api';
import {Session,type Hit} from './session';
const demo='Bonjour,\n\nJean Dupont ne peut pas joindre srv-prod-db01.client.local (10.20.30.15).\nLe compte utilisateur est jean.dupont.\npassword=SuperSecret123\n\nPostgreSQL écoute sur le port 5432. Comment diagnostiquer ce problème ?';
export default function App(){
 const [dark,setDark]=useState(matchMedia('(prefers-color-scheme: dark)').matches);
 const [rulesOpen,setRulesOpen]=useState(location.pathname==='/regles');
 const [tab,setTab]=useState('analyze'); const [text,setText]=useState('');
 const [hits,setHits]=useState<Hit[]>([]); const [disabled,setDisabled]=useState<Set<number>>(new Set());
 const [output,setOutput]=useState(''); const [reply,setReply]=useState('');
 const [status,setStatus]=useState('Prêt à analyser'); const [busy,setBusy]=useState(false);
 const [language,setLanguage]=useState(appConfig.default_language); const [valid,setValid]=useState(false);
 const [mappingRevision,setMappingRevision]=useState(0);
 const session=useRef(new Session()); const input=useRef<HTMLTextAreaElement>(null); const request=useRef<AbortController|null>(null);
 const transform=useRef<Worker|null>(null);const transformReject=useRef<((error:Error)=>void)|null>(null);
 function stopTransform(){transform.current?.terminate();transform.current=null;transformReject.current?.(new Error('Préparation annulée'));transformReject.current=null;}
 const restoration=useMemo(()=>session.current.restorationReport(reply),[reply,mappingRevision]);
 const bytes=useMemo(()=>new TextEncoder().encode(text).length,[text]);
 const characters=useMemo(()=>Array.from(text),[text]);
 const [languageReport,setLanguageReport]=useState('');
 const [progress,setProgress]=useState(0);
 function update(value:string){stopTransform();request.current?.abort();setBusy(false);setText(value);setLanguageReport('');setValid(false);setHits([]);setOutput('');setStatus('Texte modifié — analyse nécessaire');}
 async function render(next:Hit[],excluded:Set<number>){
  stopTransform();setValid(false);
  const worker=new Worker(new URL('./protect.worker.ts',import.meta.url),{type:'module'});transform.current=worker;
  try {
   const result=await new Promise<{output:string;mapping:[string,{value:string;secret:boolean}][];values:[string,string][]}>((resolve,reject)=>{
    transformReject.current=reject;
    worker.onmessage=event=>event.data.error?reject(new Error(event.data.error)):resolve(event.data);
    worker.onerror=()=>reject(new Error('Préparation du résultat impossible'));
    worker.postMessage({text,networks:[],hits:next.filter((_,i)=>!excluded.has(i)),prefix:session.current.prefix,mapping:[...session.current.mapping],values:[...session.current.values]});
   });
   if(transform.current!==worker)return false;
   session.current.mapping=new Map(result.mapping);session.current.values=new Map(result.values);setMappingRevision(value=>value+1);
   setOutput(result.output);setValid(true);return true;
  }catch(error){if(transform.current===worker)setStatus(error instanceof Error?error.message:'Préparation impossible');return false;}
  finally{worker.terminate();if(transform.current===worker){transform.current=null;transformReject.current=null;}}
 }
 async function analyze(){
  const controller=new AbortController();request.current=controller;setBusy(true);setValid(false);setHits([]);setOutput('');setProgress(0);setLanguageReport('');setStatus('Démarrage de l’analyse…');
  try {const res=await fetch('/api/analyze-stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,language}),signal:controller.signal});
   if(!res.ok){let detail='Service indisponible. Réessayez dans quelques instants.';try{const error=await res.json();detail=error.detail||detail;}catch{}throw new Error(detail);}
   const reader=res.body!.getReader();const decoder=new TextDecoder();let buffer='',completed=false;
   while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});
    let newline;
    while((newline=buffer.indexOf('\n'))>=0){const message=JSON.parse(buffer.slice(0,newline));buffer=buffer.slice(newline+1);
     if(controller.signal.aborted)return;
     if(message.type==='progress'){setProgress(message.percent);setStatus(message.phase+' — '+message.percent+' %');}
     if(message.type==='error')throw new Error(message.detail);
     if(message.type==='result'){setStatus('Préparation de l’affichage…');setProgress(100);await new Promise(resolve=>setTimeout(resolve,0));if(controller.signal.aborted)return;
      setHits(message.detections);setDisabled(new Set());if(!await render(message.detections,new Set())||controller.signal.aborted)return;const info=message.language_info;if(info){setLanguageReport((info.mode==='auto'?'Détection automatique : ':'Langue choisie : ')+(info.detected.map((code:string)=>code==='fr'?'français':'anglais').join(' + ')||'indéterminée')+(info.uncertain?' · passages incertains : analyse FR et EN.':'')+(info.unsupported?' · langue hors FR/EN probable : couverture limitée, repli FR et EN.':''));}setStatus('Analyse terminée — vérifiez le résultat');completed=true;}
    }
   }
   if(!completed)throw new Error('Analyse interrompue sans résultat complet');
  }catch(error){if(!controller.signal.aborted)setStatus(error instanceof Error?error.message:'Analyse impossible');}
  finally{if(request.current===controller)setBusy(false);}
 }
 function clear(){stopTransform();request.current?.abort();session.current=new Session();setMappingRevision(value=>value+1);setText('');setLanguageReport('');setHits([]);setOutput('');setReply('');setDisabled(new Set());setBusy(false);setValid(false);setStatus('Session effacée');}
 function manual(){const el=input.current;if(!el||el.selectionStart===el.selectionEnd)return;const start=Array.from(text.slice(0,el.selectionStart)).length;const end=Array.from(text.slice(0,el.selectionEnd)).length;
  const next=hits.filter(h=>h.end<=start||h.start>=end);next.push({start,end,category:'MANUAL',secret:true,reason:'Masquage manuel, non restaurable par précaution'});next.sort((a,b)=>a.start-b.start);setHits(next);setDisabled(new Set());void render(next,new Set());
 }
 async function copy(value:string){try{await navigator.clipboard.writeText(value);setStatus('Texte copié');}catch{setStatus('Copie refusée par le navigateur');}}
 return <div className={dark?'shell dark':'shell'}><header><div className="brand"><span className="logo">PV</span><strong>Prompt Vault</strong><span className="badge">CONFIGURATION DÉPLOYÉE</span></div><div className="header-actions"><button className={rulesOpen?'workspace-switch active':'workspace-switch'} aria-pressed={rulesOpen} onClick={()=>setRulesOpen(!rulesOpen)}>{rulesOpen?'← Espace de travail':'Règles actives'}</button><button onClick={()=>setDark(!dark)}>{dark?'☀ Clair':'☾ Sombre'}</button></div></header>
 <main><div className="intro"><div><p className="eyebrow">{rulesOpen?'CONFIGURATION DÉPLOYÉE':'ESPACE DE TRAVAIL'}</p><h1>{rulesOpen?'Règles actives':'Votre expertise, sans vos secrets.'}</h1><p>{rulesOpen?'Consultez les protections appliquées à vos textes.':'Préparez vos prompts et gardez la maîtrise des informations partagées.'}</p></div>{!rulesOpen&&<button onClick={clear}>Effacer la session</button>}</div>
 <div className="notice">Accès direct · Règles gérées au déploiement.</div>
 {rulesOpen&&<ActiveRules/>}
 <div hidden={rulesOpen}><nav className="work-nav" aria-label="Actions sur les textes"><button className={tab==='analyze'?'active':''} aria-current={tab==='analyze'?'page':undefined} onClick={()=>setTab('analyze')}>Protéger un texte</button><button className={tab==='restore'?'active':''} aria-current={tab==='restore'?'page':undefined} onClick={()=>setTab('restore')}>Restaurer une réponse</button></nav>
 {tab==='analyze'?<><div className="toolbar analysis-toolbar"><LanguageChoice disabled={busy} value={language} onChange={value=>{setLanguage(value);setLanguageReport('');setValid(false);setHits([]);setOutput('');}}/><button onClick={()=>update(demo)}>Exemple fictif</button><span className="grow"/><span className="text-volume">{(bytes/1024).toFixed(1)} Ko / {appConfig.max_text_mib} Mio</span>{busy?<button onClick={()=>{stopTransform();request.current?.abort();setBusy(false);setStatus('Analyse annulée — arrêt du calcul serveur demandé.');}}>Annuler</button>:<button className="primary" disabled={!text||bytes>appConfig.max_text_mib*1048576} onClick={analyze}>Analyser le texte →</button>}</div>

 {languageReport&&<p role="status" className="notice">{languageReport}</p>}
 {busy&&<progress max={100} value={progress} aria-label="Progression de l’analyse"/>}
 <div className="grid"><section><div className="panel-title"><h2>Texte original</h2><span>ENTRÉE</span></div><textarea ref={input} value={text} onChange={e=>update(e.target.value)} placeholder="Collez ici un prompt, un extrait de log ou une configuration…" spellCheck={false}/><div className="panel-bottom"><button disabled={!valid||busy} onClick={manual}>Masquer la sélection</button><small>Après analyse, sélectionnez un passage oublié.</small></div></section>
 <section><div className="panel-title"><h2>Texte protégé</h2><span>SORTIE</span></div><textarea readOnly value={output} placeholder="Le résultat apparaîtra après l’analyse."/><div className="panel-bottom"><small>{hits.length} détection(s)</small><button className="primary" disabled={!valid||busy} onClick={()=>copy(output)}>Copier le texte protégé</button></div></section></div>
 {hits.length>0&&!busy&&<DetectionReview characters={characters} hits={hits} excluded={disabled} pending={!valid} onToggle={i=>{const next=new Set(disabled);next.has(i)?next.delete(i):next.add(i);setDisabled(next);void render(hits,next);}}/>}</>:<><RestorationSummary report={restoration} hasReply={!!reply}/><div className="grid"><section><div className="panel-title"><h2>Réponse de l’IA</h2></div><textarea value={reply} onChange={e=>setReply(e.target.value)} placeholder="Collez la réponse contenant les placeholders de cette session."/></section><section><div className="panel-title"><h2>Réponse restaurée</h2></div><textarea readOnly value={restoration.output}/><div className="panel-bottom"><small>Les secrets restent masqués.</small><button onClick={()=>copy(restoration.output)} disabled={!reply}>Copier la réponse restaurée</button></div></section></div></>}
 </div>
 <footer role="status"><span className={busy?'pulse':''}>●</span> {status}<span className="grow"/><small>Une analyse automatique peut omettre des données sensibles.</small></footer>
 </main></div>
}
