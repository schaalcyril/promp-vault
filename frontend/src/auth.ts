import Keycloak from 'keycloak-js';
export let auth:Keycloak;
export let appConfig={issuer:'',client_id:'',default_language:'auto',max_text_mib:10};
export async function loadConfig(){const response=await fetch('/api/config');if(!response.ok)throw new Error('Configuration indisponible');appConfig=await response.json();}
export async function initSSO(){await loadConfig();const separator=appConfig.issuer.lastIndexOf('/realms/');if(separator<0)throw new Error('URL du realm incorrecte');auth=new Keycloak({url:appConfig.issuer.slice(0,separator),realm:decodeURIComponent(appConfig.issuer.slice(separator+8)),clientId:appConfig.client_id});return auth.init({onLoad:'login-required',pkceMethod:'S256',checkLoginIframe:false,redirectUri:location.origin+'/'});}
let localToken:string|null=null;
export function setLocalToken(token:string){localToken=token||null;}
export function isRecovery(){return localToken!==null;}
let profile:{roles:string[]}={roles:[]};
export async function loadProfile(){const response=await authorizedFetch('/api/me');if(!response.ok)throw new Error('Profil indisponible');profile=await response.json();}
export function isAdmin(){return isRecovery()||profile.roles.includes('admin');}
export function username(){return isRecovery()?'superadmin':auth?.tokenParsed?.preferred_username;}
export async function logout(){
 if(localToken){
  const response=await fetch('/api/recovery/logout',{method:'POST',headers:{Authorization:'Bearer '+localToken}});
  if(!response.ok)throw new Error('Déconnexion impossible. Réessayez.');
  localToken=null;location.assign('/secours');
 }else await auth.logout({redirectUri:location.origin+'/'});
}
export async function authorizedFetch(url:string,options:RequestInit={}){
 let token=localToken;
 if(!token){await auth.updateToken(30);token=auth.token||null;}
 if(!token)throw new Error('Connexion requise');
 const headers=new Headers(options.headers);headers.set('Authorization','Bearer '+token);
 const response=await fetch(url,{...options,headers});
 if(response.status===401&&localToken)throw new Error('Session de secours expirée. Déconnectez-vous puis reconnectez-vous.');
 return response;
}
