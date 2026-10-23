import {useEffect,useState} from 'react';
import {authorizedFetch} from './auth';
export default function SystemSettings(){
 const [config,setConfig]=useState<{version:number;definition:Record<string,string|number>}|null>(null),[status,setStatus]=useState('Chargement…'),[busy,setBusy]=useState(false);
 useEffect(()=>{void authorizedFetch('/api/system/settings').then(async r=>{if(!r.ok)throw new Error('Configuration indisponible');setConfig(await r.json());setStatus('');}).catch(e=>setStatus(e.message));},[]);
 const labels:Record<string,string>={issuer:'URL publique du realm Keycloak',internal_issuer:'URL interne du realm',client_id:'Client public',audience:'Audience API',user_role:'Rôle utilisateur',admin_role:'Rôle administrateur',default_language:'Langue par défaut',max_text_mib:'Taille maximale du texte (Mio)'};
 async function test(){setBusy(true);try{const r=await authorizedFetch('/api/system/settings/test',{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Test impossible');setStatus(d.message);}catch(e){setStatus(e instanceof Error?e.message:'Test impossible');}finally{setBusy(false);}}
 return <div className="admin-rules"><h2>Configuration système déployée</h2><p className="notice">Lecture seule. La configuration et le mot de passe local se changent au déploiement.</p>{config&&<section className="rule-editor"><p>Version {config.version}</p>{Object.entries(config.definition).map(([key,value])=><label key={key}>{labels[key]||key}<input readOnly value={String(value)}/></label>)}<button disabled={busy} onClick={()=>void test()}>Tester la connexion Keycloak</button></section>}<p role="status">{busy?'Vérification…':status}</p></div>;
}
