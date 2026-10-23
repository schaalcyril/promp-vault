import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parseNetworks,networkId} from './network.ts';
import {Session} from './session.ts';
test('explicit networks, boundaries and longest prefix',()=>{
 const nets=parseNetworks('10.0.0.0/8\n10.20.1.0/24\n10.20.1.0/24');
 assert.equal(nets.length,2);
 assert.equal(networkId('10.20.1.255',nets),2);
 assert.equal(networkId('10.20.2.0',nets),1);
 assert.equal(networkId('11.0.0.0',nets),null);
 assert.equal(networkId('2001:db8::1',nets),null);
 assert.equal(networkId('255.255.255.255',parseNetworks('0.0.0.0/0')),1);
 assert.equal(networkId('10.0.0.1',parseNetworks('10.0.0.1/32')),1);
});
test('reject malformed or ambiguous networks',()=>{
 for(const value of ['10.20.1.12/24','256.0.0.0/8','010.0.0.0/8','10.0.0.0/33','10.0.0.0','::/0'])assert.throws(()=>parseNetworks(value));
 assert.deepEqual(parseNetworks(''),[]);
});
test('related IPs stay distinct and reversible, ports unchanged, secrets remain masked',()=>{
 const text='10.20.1.12:443 10.20.1.18 10.20.1.12 secret';
 const values=['10.20.1.12','10.20.1.18','10.20.1.12','secret'];let from=0;
 const hits=values.map(value=>{const start=text.indexOf(value,from);from=start+value.length;return {start,end:from,category:value==='secret'?'SECRET':'IP',secret:value==='secret',reason:''};});
 const session=new Session();const output=session.protect(text,hits,parseNetworks('10.20.1.0/24'));
 const tokens=output.match(/<PV_[^>]+>/g)!;
 assert.equal(tokens[0],tokens[2]);assert.notEqual(tokens[0],tokens[1]);
 assert.ok(tokens[0].includes('_RESEAU_1_HOTE_'));assert.ok(tokens[1].includes('_RESEAU_1_HOTE_'));
 assert.ok(output.includes(':443'));assert.equal(session.restore(output),text.replace('secret',tokens[3]));
 const ordinary=new Session().protect(text,hits);assert.ok(!ordinary.includes('RESEAU'));
});
