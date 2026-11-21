import test from 'node:test';
import assert from 'node:assert/strict';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

test('invalid bamboo player positions never issue canvas draw calls',()=>{
 let calls=0;
 const ctx=new Proxy({}, {get(){return ()=>{calls++;};},set(){calls++;return true;}});
 const invalid=[null,{}, {x:NaN,y:0},{x:Infinity,y:0},{x:0,y:Infinity},{x:-1,y:0},{x:0,y:-1},{x:BAMBOO_PASS.width,y:0},{x:0,y:BAMBOO_PASS.height},{x:0.5,y:0},{x:0,y:1.5}];
 for(const position of invalid){
  assert.equal(drawBambooPass(ctx,{regionId:BAMBOO_PASS.id,position}),false,JSON.stringify(position));
 }
 assert.equal(calls,0);
});
