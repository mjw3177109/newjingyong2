import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

// Execute the actual browser save function with an injected storage boundary.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
const start=source.indexOf('function save(){');
const end=source.indexOf('function load(){',start);
assert.ok(start>=0 && end>start,'manual save implementation must be found');
const saveSource=source.slice(start,end);

function exercise(storage, raw='{"version":2}', session=null){
 const messages=[];
 const context={
  bambooSession:session,
  state:{},eventHistory:{},
  encodeCheckpoint:()=>raw,
  MAX_SAVE_FILE_BYTES:65536,
  TextEncoder,
  localStorage:storage,
  keyName:'test-checkpoint',
  toast:message=>messages.push(message)
 };
 runInNewContext(`${saveSource}\nsave();`,context,{timeout:1000});
 return messages;
}

test('manual save reports success only after an exact storage readback',()=>{
 const values=new Map();
 const messages=exercise({setItem:(k,v)=>values.set(k,v),getItem:k=>values.get(k)});
 assert.deepEqual(messages,['进度已存入本机浏览器']);
 assert.equal(values.get('test-checkpoint'),'{"version":2}');
});

test('manual save rejects silently dropped writes',()=>{
 assert.deepEqual(exercise({setItem:()=>{},getItem:()=>null}),['存档无效或浏览器存储不可用']);
});

test('manual save rejects readback corruption',()=>{
 assert.deepEqual(exercise({setItem:()=>{},getItem:()=>'{"version":1}'}),['存档无效或浏览器存储不可用']);
});

test('manual save rejects quota and readback exceptions',()=>{
 for(const storage of [
  {setItem:()=>{throw new Error('QuotaExceededError')},getItem:()=>null},
  {setItem:()=>{},getItem:()=>{throw new Error('SecurityError')}}
 ]) assert.deepEqual(exercise(storage),['存档无效或浏览器存储不可用']);
});

test('manual save refuses invalid and oversized checkpoints without writing',()=>{
 let writes=0;
 const storage={setItem:()=>{writes++},getItem:()=>null};
 assert.deepEqual(exercise(storage,''),['存档无效或浏览器存储不可用']);
 assert.deepEqual(exercise(storage,'汉'.repeat(22000)),['存档无效或浏览器存储不可用']);
 assert.equal(writes,0);
});


test('manual save refuses to overwrite village checkpoint while exploring bamboo pass',()=>{
 let writes=0,reads=0;
 const storage={setItem:()=>{writes++},getItem:()=>{reads++;return null}};
 assert.deepEqual(exercise(storage,'{"version":2}',{region:'bamboo-pass'}),['请先返回青竹村再保存；山径探索暂不支持存档']);
 assert.equal(writes,0);
 assert.equal(reads,0);
});

test('manual save rejects encoder failure without touching browser storage',()=>{
 let writes=0;
 const storage={setItem:()=>{writes++},getItem:()=>null};
 const messages=exercise(storage,null);
 assert.deepEqual(messages,['存档无效或浏览器存储不可用']);
 assert.equal(writes,0);
});
