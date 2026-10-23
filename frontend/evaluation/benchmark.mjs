import {Session} from '../src/session.ts';
const unit='192.0.2.1 request completed\n';
const text=(unit.repeat(Math.ceil(10485760/unit.length))).slice(0,10485760);
const hits=[];for(let start=0;start+9<=text.length;start+=unit.length)hits.push({start,end:start+9,category:'IP',secret:false,reason:''});
const session=new Session();const start=performance.now();const out=session.protect(text,hits);
console.log(JSON.stringify({bytes:text.length,detections:hits.length,seconds:(performance.now()-start)/1000,output_bytes:out.length,peak_rss_mib:process.resourceUsage().maxRSS/1024}));
