import {useMemo,useState} from 'react';
import type {Hit} from './session';
import {excerpt,reviewPage,PAGE_SIZE} from './review';
export default function DetectionReview({characters,hits,excluded,pending,onToggle}:{characters:string[];hits:Hit[];excluded:Set<number>;pending:boolean;onToggle:(index:number)=>void}){
 const [category,setCategory]=useState('');const [page,setPage]=useState(0);const [selected,setSelected]=useState<number|null>(null);
 const categories=useMemo(()=>[...new Set(hits.map(h=>h.category))].sort(),[hits]);
 const result=useMemo(()=>reviewPage(hits,category,page),[hits,category,page]);
 const active=selected!==null&&result.indices.includes(selected)?selected:result.indices[0];
 const hit=active===undefined?undefined:hits[active];
 const context=hit?excerpt(characters,hit):null;
 return <details className="detection-review"><summary>Vérifier les détections ({hits.length})</summary>
 <div className="toolbar"><label>Catégorie <select value={category} onChange={e=>{setCategory(e.target.value);setPage(0);setSelected(null);}}><option value="">Toutes les catégories</option>{categories.map(c=><option key={c}>{c}</option>)}</select></label><span>{result.total} résultat(s) · {excluded.size} exclusion(s) au total</span></div>
 <p>Décochez une détection pour laisser sa valeur dans le texte partagé. Sélectionnez « Voir le passage » pour vérifier son contexte.</p>
 <div className="review-layout"><div>{result.indices.map(index=>{const item=hits[index];return <div className={'review-hit'+(active===index?' selected':'')} key={index}><label><input type="checkbox" disabled={pending} checked={!excluded.has(index)} onChange={()=>onToggle(index)}/><strong>{item.category}</strong><code>{item.secret?'Secret masqué':characters.slice(item.start,Math.min(item.end,item.start+80)).join('')+(item.end-item.start>80?'…':'')}</code></label><button aria-pressed={active===index} onClick={()=>setSelected(index)}>Voir le passage {index+1}</button></div>;})}{!result.total&&<p>Aucune détection dans cette catégorie.</p>}</div>
 {hit&&context&&<aside className="review-context"><h3>Passage sélectionné</h3><small>Détection {active!+1} · {hit.category} · {excluded.has(active!)?'Exclue du masquage':'Masquée'}</small><pre>{context.before}<mark>{context.value}</mark>{context.after}</pre><p>{hit.reason}</p><small>Extrait du texte original, limité autour de la détection. Les valeurs originales peuvent être visibles ici.</small></aside>}</div>
 <div className="review-pagination"><button disabled={result.current===0} onClick={()=>setPage(result.current-1)}>Précédent</button><span aria-live="polite">Page {result.current+1} / {result.pages} · {PAGE_SIZE} résultats maximum par page</span><button disabled={result.current+1>=result.pages} onClick={()=>setPage(result.current+1)}>Suivant</button></div></details>;
}
