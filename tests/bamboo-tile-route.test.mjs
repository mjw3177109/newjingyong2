import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {pathToBambooTile,pathToBambooExit} from '../src/bamboo-exit-path.js';
import {stepInRegion} from '../src/region-navigation.js';

const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
test('clicked bamboo destination has a deterministic shortest legal route',()=>{
 const route=pathToBambooTile(session,BAMBOO_PASS.exit.x,BAMBOO_PASS.exit.y);
 assert.deepEqual(route,pathToBambooExit(session));
 assert.ok(route.length>1);
 let p=session.position;
 for(const next of route){
  assert.deepEqual(stepInRegion(BAMBOO_PASS,p,next.x-p.x,next.y-p.y),next);
  p=next;
 }
 assert.deepEqual(p,BAMBOO_PASS.exit);
});
test('blocked, out-of-bounds, noninteger and invalid sessions never route',()=>{
 for(const [x,y] of [[4,1],[-1,2],[12,2],[NaN,3],[2.5,3]]){
  assert.equal(pathToBambooTile(session,x,y),null);
 }
 assert.equal(pathToBambooTile(null,2,2),null);
 assert.equal(pathToBambooTile(session,session.position.x,session.position.y).length,0);
});
test('clicking NPC routes to adjacent tile without entering occupied position',()=>{
 const route=pathToBambooTile(session,BAMBOO_PASS.npc.x,BAMBOO_PASS.npc.y);
 assert.ok(route.length>0);
 const end=route.at(-1);
 assert.equal(Math.abs(end.x-BAMBOO_PASS.npc.x)+Math.abs(end.y-BAMBOO_PASS.npc.y),1);
 assert.ok(route.every(p=>p.x!==BAMBOO_PASS.npc.x||p.y!==BAMBOO_PASS.npc.y));
});
