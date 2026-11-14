import test from 'node:test';
import assert from 'node:assert/strict';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

test('invalid canvas dimensions never issue draw calls',()=>{
 let calls=0;
 const ctx=new Proxy({}, {get(){return ()=>{calls++;};},set(){calls++;return true;}});
 const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 for(const [w,h] of [[0,540],[900,0],[-1,540],[900,-1],[NaN,540],[900,Infinity],[Infinity,540],[900,NaN]]){
  assert.equal(drawBambooPass(ctx,session,w,h),false,`dimensions ${w}x${h}`);
 }
 assert.equal(calls,0);
});
