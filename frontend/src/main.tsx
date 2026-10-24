import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {loadConfig} from './api';
import './style.css';
import './brand.css';
const root=createRoot(document.getElementById('root')!);
async function start(){
 root.render(<div className="shell"><main><p role="status">Chargement…</p></main></div>);
 try{await loadConfig();root.render(<React.StrictMode><App/></React.StrictMode>);}
 catch{root.render(<div className="shell"><main><p role="alert">Configuration indisponible.</p><button onClick={()=>void start()}>Réessayer</button></main></div>);}
}
void start();
