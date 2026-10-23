import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import SignIn from './SignIn';
import {initSSO,loadConfig,loadProfile} from './auth';
import './style.css';
import './brand.css';
const root=createRoot(document.getElementById('root')!);
const showApp=()=>{void loadConfig().then(loadProfile).then(()=>root.render(<React.StrictMode><App/></React.StrictMode>)).catch(()=>showLogin('Configuration indisponible.'));};
const recovery=location.pathname==='/secours';
function showLogin(error=''){root.render(<SignIn recovery={recovery} onSuccess={showApp} onSSO={()=>void connect()} error={error}/>);}
async function connect(){
 root.render(<div className="shell"><main><p role="status">Connexion à Keycloak…</p><a href="/secours">Accès administrateur de secours</a></main></div>);
 try{if(await initSSO())showApp();}
 catch{showLogin('Connexion Keycloak indisponible. Rechargez la page pour réessayer ou utilisez l’accès de secours.');}
}
if(!recovery&&/\b(code|error|state)=/.test(location.hash))void connect();else showLogin();
