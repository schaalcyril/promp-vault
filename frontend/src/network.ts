export type Network={base:number;prefix:number;id:number};
function ipv4(value:string):number|null {
 const parts=value.split('.');
 if(parts.length!==4||parts.some(p=>! /^(0|[1-9][0-9]{0,2})$/.test(p)||Number(p)>255))return null;
 return parts.reduce((address,part)=>address*256+Number(part),0);
}
export function parseNetworks(value:string):Network[]{
 const lines=value.split(/[\n,;]+/).map(line=>line.trim()).filter(Boolean);
 if(lines.length>100)throw new Error('Déclarez au maximum 100 sous-réseaux.');
 const networks:Network[]=[];
 for(const line of lines){
  const match=/^([^/]+)\/(0|[1-9]|[12][0-9]|3[0-2])$/.exec(line);
  const address=match?ipv4(match[1]):null;
  if(!match||address===null)throw new Error('Sous-réseau invalide : utilisez une adresse IPv4 suivie de /0 à /32.');
  const prefix=Number(match[2]),size=2**(32-prefix),base=Math.floor(address/size)*size;
  if(base!==address)throw new Error('Indiquez l’adresse de début du sous-réseau, par exemple 10.20.1.0/24.');
  if(!networks.some(n=>n.base===base&&n.prefix===prefix))networks.push({base,prefix,id:networks.length+1});
 }
 return networks;
}
export function networkId(value:string,networks:Network[]):number|null{
 const address=ipv4(value);if(address===null)return null;
 let best:Network|undefined;
 for(const network of networks){const size=2**(32-network.prefix);
  if(Math.floor(address/size)*size===network.base&&(!best||network.prefix>best.prefix))best=network;
 }
 return best?.id??null;
}
