import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Session} from './session.ts';
test('consistent mapping and no secret restoration',()=>{
 const s=new Session(); const t='abc abc pwd';
 const out=s.protect(t,[{start:0,end:3,category:'HOST',secret:false,reason:''},{start:4,end:7,category:'HOST',secret:false,reason:''},{start:8,end:11,category:'PASSWORD',secret:true,reason:''}]);
 assert.equal(out.split(' ')[0],out.split(' ')[1]);
 assert.ok(s.restore(out).startsWith('abc abc <PV_'));
 assert.equal(new Session().restore(out),out);
});
test('Unicode offsets and single-pass restoration',()=>{
 const s=new Session(); const out=s.protect('😀 abc',[{start:2,end:5,category:'HOST',secret:false,reason:''}]);
 assert.equal(s.restore(out),'😀 abc');
});

test('central VLAN grouping preserves subnets and old mappings without restoring secrets',()=>{
 const session=new Session();const text='10.20.1.1';
 const hit={start:0,end:text.length,category:'IP',secret:false,reason:'',network_label:'VLAN_1_RESEAU_1'};
 const first=session.protect(text,[hit]);assert.ok(first.includes('VLAN_1_RESEAU_1_HOTE'));
 const second=session.protect(text,[{...hit,network_label:'VLAN_2_RESEAU_1'}]);
 assert.notEqual(first,second);assert.equal(session.restore(first),text);
 session.protect(text,[{...hit,secret:true,category:'SECRET',network_label:undefined}]);
 assert.equal(session.restore(first),first);assert.equal(session.restore(second),second);
 const later=session.protect(text,[{...hit,network_label:'VLAN_3_RESEAU_1'}]);assert.equal(session.restore(later),later);
});

test('restoration summary counts occurrences and leaves secrets and unknown markers intact',()=>{
 const s=new Session();s.mapping.set('<PV_a_PERSON_1>',{value:'Alice',secret:false});s.mapping.set('<PV_a_SECRET_2>',{value:'never-show',secret:true});
 const report=s.restorationReport('<PV_a_PERSON_1> <PV_a_PERSON_1> <PV_a_SECRET_2> <PV_other_IP_1>');
 assert.equal(report.restored,2);assert.equal(report.secrets,1);assert.equal(report.unknown,1);assert.equal(report.suspected,0);
 assert.equal(report.output,'Alice Alice <PV_a_SECRET_2> <PV_other_IP_1>');assert.ok(!JSON.stringify(report).includes('never-show'));
});
test('suspected altered markers are reported but never guessed',()=>{
 const s=new Session();const text='[PV_a_PERSON_1] &lt;PV_a_PERSON_1&gt; <pv_a_PERSON_1> PV_a_PERSON_1';
 const report=s.restorationReport(text);assert.equal(report.suspected,4);assert.equal(report.output,text);assert.equal(report.restored,0);
});
test('report uses original input only and bounds detailed output',()=>{
 const s=new Session();s.mapping.set('<PV_a_PERSON_1>',{value:'<PV_other_TOKEN_1>',secret:false});
 const report=s.restorationReport('<PV_a_PERSON_1>');assert.equal(report.restored,1);assert.equal(report.unknown,0);assert.equal(report.output,'<PV_other_TOKEN_1>');
 const many=s.restorationReport(Array.from({length:1000},(_,i)=>`<PV_unknown_IP_${i}>`).join(' '));assert.equal(many.unknown,1000);assert.equal(many.issues.length,50);assert.equal(many.omitted,950);
 assert.equal(new Session().restorationReport('ordinary response').hasMapping,false);
});
