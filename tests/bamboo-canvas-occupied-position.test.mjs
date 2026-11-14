import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {drawBambooPass} from '../src/bamboo-canvas.js';

test('bamboo renderer rejects blocked and NPC-occupied session positions without drawing',()=>{
 let calls=0;
 const ctx={fillRect(){calls++;}};
 for(const position of [{x:4,y:1},{x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y}]){
  assert.equal(drawBambooPass(ctx,{regionId:BAMBOO_PASS.id,position},900,540),false);
 }
 assert.equal(calls,0);
});
