import {useEffect,useState} from 'react';
type Rule={name:string;category:string;secret:boolean;kind?:string};
type Catalogue={version:number;builtin:Rule[];custom:Rule[]};
export default function ActiveRules(){
 const [data,setData]=useState<Catalogue|null>(null),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 useEffect(()=>{const controller=new AbortController();setError('');
  void fetch('/api/rules',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error();return r.json();}).then(setData).catch(()=>{if(!controller.signal.aborted)setError('Impossible de charger les règles.');});
  return()=>controller.abort();
 },[attempt]);
 if(error)return <section className="rules-catalogue"><p role="alert">{error}</p><button onClick={()=>setAttempt(n=>n+1)}>Réessayer</button></section>;
 if(!data)return <p role="status">Chargement des règles…</p>;
 function rows(rules:Rule[]){return <ul className="rule-list">{rules.map(r=><li key={r.category+':'+r.name}><div><strong>{r.name}</strong><p>{r.category}{r.kind?' · '+(r.kind==='list'?'Liste de mots-clés':'Expression régulière'):''}</p></div><span className="badge">{r.secret?'Non restaurable':'Restaurable'}</span></li>)}</ul>;}
 return <div className="rules-catalogue"><p>Version de configuration : <strong>{data.version}</strong>. Les changements nécessitent un redéploiement.</p>
 <section><div className="panel-title"><h2>Protections intégrées</h2><span>{data.builtin.length} catégories</span></div>{rows(data.builtin)}<p className="rules-note">Analyse français/anglais et détecteurs techniques. La couverture dépend du format et du contexte : vérifiez toujours le résultat.</p></section>
 <section><div className="panel-title"><h2>Règles personnalisées actives</h2><span>{data.custom.length} règles</span></div>{data.custom.length?rows(data.custom):<p className="rules-note">Aucune règle personnalisée active.</p>}<p className="rules-note">Les termes et expressions ne sont pas publiés dans cette page. Les secrets restent masqués lors de la restauration.</p></section></div>;
}
