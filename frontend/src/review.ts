import type {Hit} from './session.ts';
export const PAGE_SIZE=50;
export function reviewPage(hits:Hit[],category:string,page:number){
 const indices=hits.flatMap((hit,index)=>!category||hit.category===category?[index]:[]);
 const pages=Math.max(1,Math.ceil(indices.length/PAGE_SIZE));
 const current=Math.max(0,Math.min(page,pages-1));
 return {total:indices.length,pages,current,indices:indices.slice(current*PAGE_SIZE,(current+1)*PAGE_SIZE)};
}
export function excerpt(chars:string[],hit:Hit){
 const start=Math.max(0,hit.start-120),end=Math.min(chars.length,hit.end+120);
 return {before:(start?'…':'')+chars.slice(start,hit.start).join(''),value:chars.slice(hit.start,Math.min(hit.end,hit.start+300)).join('')+(hit.end-hit.start>300?'…':''),after:chars.slice(hit.end,end).join('')+(end<chars.length?'…':'')};
}
