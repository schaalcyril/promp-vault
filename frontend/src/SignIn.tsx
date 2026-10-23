import {useState,type FormEvent} from 'react';
import {setLocalToken} from './auth';
export default function SignIn({recovery,onSuccess,onSSO,error=''}:{recovery:boolean;onSuccess:()=>void;onSSO:()=>void;error?:string}){
 const [password,setPassword]=useState(''),[name,setName]=useState('superadmin'),[busy,setBusy]=useState(false),[message,setMessage]=useState(error);
 async function submit(event:FormEvent){event.preventDefault();setBusy(true);setMessage('');try{
  const response=await fetch('/api/recovery/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:name,password})});
  const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Connexion impossible');
  setPassword('');setLocalToken(data.access_token);onSuccess();
 }catch(e){setPassword('');setMessage(e instanceof Error?e.message:'Connexion indisponible');}finally{setBusy(false);}}
 return <div className={'shell '+(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'')}><main className="login-page"><section className="login-card"><span className="logo">PV</span><p className="eyebrow">PROMPT VAULT</p><h1>{recovery?'Super administrateur local':'Bienvenue'}</h1><p>{recovery?'Accès indépendant de Keycloak. Configuration gérée au déploiement.':'Connectez-vous pour protéger vos textes et retrouver votre espace de travail.'}</p>
 {recovery?<form onSubmit={submit}><label>Compte local<input autoComplete="username" value={name} maxLength={100} onChange={e=>setName(e.target.value)} required disabled={busy}/></label><label>Mot de passe<input type="password" autoComplete="current-password" value={password} maxLength={256} onChange={e=>setPassword(e.target.value)} required disabled={busy}/></label><button className="primary" disabled={busy}>{busy?'Connexion…':'Se connecter'}</button><p><small>Session de 30 minutes. Un rechargement de la page nécessite une nouvelle connexion.</small></p><a href="/">Retour à la connexion habituelle</a></form>:<><button className="primary" onClick={onSSO}>Se connecter avec Keycloak</button><p><a href="/secours">Super administrateur local</a></p></>}
 {message&&<p role="alert">{message}</p>}</section></main></div>;
}
