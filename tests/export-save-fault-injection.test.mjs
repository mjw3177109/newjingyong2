import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

// Exercise the production export handler, not a copied implementation.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
const start=source.indexOf('function exportSave() {');
const end=source.indexOf("\n$('interact').onclick=",start);
assert.ok(start>=0 && end>start,'export handler must be present');
const exportSource=source.slice(start,end);

function exercise({session=null,raw='{"version":2}',fail=false,clickFail=false,removeFail=false,appendFail=false}={}){
 const messages=[],links=[],urls=[],revoked=[];
 const context={
  bambooSession:session,state:{},eventHistory:{},MAX_SAVE_FILE_BYTES:65536,
  encodeCheckpoint:()=>raw,TextEncoder,Blob,
  URL:{createObjectURL:()=>{if(fail)throw Error('blocked');urls.push('blob:test');return 'blob:test';},revokeObjectURL:url=>revoked.push(url)},
  document:{
   createElement:()=>{const link={click(){link.clicked=true;if(clickFail)throw Error('download blocked')},remove(){link.removed=true;if(removeFail)throw Error('remove blocked')}};links.push(link);return link},
   body:{appendChild(){if(appendFail)throw Error('append blocked')}}
  },
  setTimeout:fn=>fn(),toast:msg=>messages.push(msg)
 };
 runInNewContext(exportSource+'\nexportSave();',context,{timeout:1000});
 return {messages,links,urls,revoked};
}

test('export refuses to serialize a live bamboo session',()=>{
 const r=exercise({session:{region:'bamboo-pass'}});
 assert.deepEqual(r.messages,['请先返回青竹村再导出；山径探索暂不支持存档']);
 assert.equal(r.links.length,0);
});
test('export rejects empty or oversized checkpoint without creating download',()=>{
 for(const raw of ['', '汉'.repeat(22000)]){
  const r=exercise({raw});
  assert.deepEqual(r.messages,['存档导出失败']);
  assert.equal(r.links.length,0);
 }
});
test('export creates and revokes JSON download for valid checkpoint',()=>{
 const r=exercise();
 assert.deepEqual(r.messages,['已导出原创试玩存档 JSON']);
 assert.equal(r.links.length,1);
 assert.equal(r.links[0].download,'zhuying-jianghu-save-v2.json');
 assert.equal(r.links[0].clicked,true);
 assert.equal(r.links[0].removed,true);
 assert.deepEqual(r.revoked,['blob:test']);
});
test('export reports object URL failure without claiming success',()=>{
 const r=exercise({fail:true});
 assert.deepEqual(r.messages,['存档导出失败']);
 assert.equal(r.links.length,0);
});

test('export revokes object URL and removes link when click throws',()=>{
 const r=exercise({clickFail:true});
 assert.deepEqual(r.messages,['存档导出失败']);
 assert.equal(r.links.length,1);
 assert.equal(r.links[0].removed,true);
 assert.deepEqual(r.revoked,['blob:test']);
});

test('export revokes Blob URL even if link removal throws',()=>{
 const r=exercise({removeFail:true});
 assert.deepEqual(r.messages,['存档导出失败']);
 assert.equal(r.links.length,1);
 assert.equal(r.links[0].clicked,true);
 assert.deepEqual(r.revoked,['blob:test']);
});


test('export revokes Blob URL when inserting download link fails',()=>{
 const r=exercise({appendFail:true});
 assert.deepEqual(r.messages,['存档导出失败']);
 assert.equal(r.links.length,1);
 assert.equal(r.links[0].clicked,undefined);
 assert.equal(r.links[0].removed,true);
 assert.deepEqual(r.revoked,['blob:test']);
});
