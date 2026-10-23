import {test} from 'node:test';
import assert from 'node:assert/strict';
import {reviewPage,excerpt} from './review.ts';
const hits=Array.from({length:701},(_,i)=>({start:i,end:i+1,category:i%2?'HOST':'EMAIL',secret:false,reason:''}));
test('all detections remain reachable, including after index 300',()=>{
 const indices=Array.from({length:reviewPage(hits,'',0).pages},(_,page)=>reviewPage(hits,'',page).indices).flat();
 assert.deepEqual(indices,hits.map((_,i)=>i));
});
test('filtering preserves original indices for exclusion and clamps pagination',()=>{
 const result=reviewPage(hits,'HOST',999);
 assert.equal(result.current,6);assert.equal(result.total,350);
 assert.ok(result.indices.every(i=>hits[i].category==='HOST'));
 assert.deepEqual(reviewPage(hits,'UNKNOWN',2).indices,[]);
});
test('context uses Unicode code points and bounds large matches',()=>{
 assert.deepEqual(excerpt(Array.from('😀 Jean fin'),{...hits[0],start:2,end:6}),{before:'😀 ',value:'Jean',after:' fin'});
 const result=excerpt(Array.from('x'.repeat(10000)),{...hits[0],start:1000,end:9000});
 assert.equal(result.value.length,301);assert.equal(result.before.length,121);assert.equal(result.after.length,121);
});
