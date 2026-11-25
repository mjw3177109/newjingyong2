import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {routeToRegionNpc} from '../src/region-npc-route.js';
import {stepInRegion,regionInteraction} from '../src/region-navigation.js';

test('NPC route uses legal steps and stops next to the keeper',()=>{
 let position={...BAMBOO_PASS.entry};
 const route=routeToRegionNpc(BAMBOO_PASS,position);
 assert.ok(Array.isArray(route) && route.length>0);
 for(const next of route){
   const moved=stepInRegion(BAMBOO_PASS,position,next.x-position.x,next.y-position.y);
   assert.deepEqual(moved,next);
   position=moved;
 }
 assert.equal(regionInteraction(BAMBOO_PASS,position)?.npcId,BAMBOO_PASS.npc.id);
 assert.notDeepEqual(position,{x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y});
});
test('already adjacent returns empty route and does not mutate inputs',()=>{
 const position={x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y-1};
 const before=JSON.stringify(position);
 assert.deepEqual(routeToRegionNpc(BAMBOO_PASS,position),[]);
 assert.equal(JSON.stringify(position),before);
});
test('invalid or blocked starts do not produce routes',()=>{
 assert.equal(routeToRegionNpc(BAMBOO_PASS,{x:-1,y:0}),null);
 assert.equal(routeToRegionNpc(BAMBOO_PASS,{x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y}),null);
 assert.equal(routeToRegionNpc(BAMBOO_PASS,null),null);
});
