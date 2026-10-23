import type {Network} from './network';
import {Session,type Hit} from './session';
self.onmessage=(event:MessageEvent<{text:string;hits:Hit[];networks:Network[];prefix:string;mapping:[string,{value:string;secret:boolean}][];values:[string,string][]}>)=>{
 try{
  const session=new Session();session.prefix=event.data.prefix;
  session.mapping=new Map(event.data.mapping);session.values=new Map(event.data.values);
  const output=session.protect(event.data.text,event.data.hits,event.data.networks);
  self.postMessage({output,mapping:[...session.mapping],values:[...session.values]});
 }catch{self.postMessage({error:'Impossible de préparer le résultat. Réduisez le volume.'});}
};
