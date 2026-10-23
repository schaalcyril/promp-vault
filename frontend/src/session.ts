import {networkId,type Network} from './network.ts';
export type Hit = {start:number;end:number;category:string;reason:string;secret:boolean;network_label?:string;score?:number};
export class Session {
  prefix = crypto.randomUUID().slice(0,8);
  mapping = new Map<string,{value:string;secret:boolean}>();
  values = new Map<string,string>();
  protect(text:string,hits:Hit[],networks:Network[]=[]) {
    const chars=Array.from(text); // Backend offsets are Unicode code points, not UTF-16.
    const secrets=new Set(hits.filter(hit=>hit.secret).map(hit=>chars.slice(hit.start,hit.end).join('')));
    for(const entry of this.mapping.values())if(entry.secret)secrets.add(entry.value);
    for(const entry of this.mapping.values())if(secrets.has(entry.value))entry.secret=true;
    const reserved=new Set(text.match(/<PV_[A-Za-z0-9_]+>/g)||[]);
    const parts:string[]=[];let cursor=0;
    for(const hit of [...hits].sort((a,b)=>a.start-b.start)) {
      if(hit.start<cursor) continue;
      const value=chars.slice(hit.start,hit.end).join('');
      const valueKey=hit.network_label?JSON.stringify([value,hit.network_label]):value;
      let token=this.values.get(valueKey);
      if(!token) {
        const group=hit.category==='IP'&&!hit.secret?networkId(value,networks):null;
        const category=hit.network_label&&!hit.secret?`${hit.network_label}_HOTE`:group===null?hit.category:`RESEAU_${group}_HOTE`;
        let n=this.mapping.size+1;
        do { token=`<PV_${this.prefix}_${category}_${n++}>`; } while(reserved.has(token)||this.mapping.has(token));
        this.values.set(valueKey,token);
        this.mapping.set(token,{value,secret:hit.secret||secrets.has(value)});
      } else if(hit.secret) this.mapping.get(token)!.secret=true;
      parts.push(chars.slice(cursor,hit.start).join(''),token); cursor=hit.end;
    }
    parts.push(chars.slice(cursor).join(''));return parts.join('');
  }
  restorationReport(text:string) {
    const counts={restored:0,secrets:0,unknown:0,suspected:0};
    const issues=new Map<string,{marker:string;kind:'secret'|'unknown'|'suspected';count:number}>();
    let omitted=0;
    const record=(marker:string,kind:'secret'|'unknown'|'suspected')=>{
      const key=kind+':'+marker,existing=issues.get(key);
      if(existing)existing.count++;
      else if(issues.size<50)issues.set(key,{marker,kind,count:1});
      else omitted++;
    };
    const output=text.replace(/<PV_[A-Za-z0-9_]+>/g,token=>{
      const entry=this.mapping.get(token);
      if(!entry){counts.unknown++;record(token,'unknown');return token;}
      if(entry.secret){counts.secrets++;record(token,'secret');return token;}
      counts.restored++;return entry.value;
    });
    // Inspect the input only: restored values must never be interpreted recursively.
    const possible=/(?:<|\[|&lt;)?\bPV(?:[_ -][A-Za-z0-9_-]+)+(?:>|\]|&gt;)?/gi;
    for(const match of text.matchAll(possible)){
      if(/^<PV_[A-Za-z0-9_]+>$/.test(match[0]))continue;
      counts.suspected++;record(match[0],'suspected');
    }
    return {output,...counts,issues:[...issues.values()],omitted,hasMapping:this.mapping.size>0};
  }
  restore(text:string) { return this.restorationReport(text).output; }
}
