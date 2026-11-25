import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {stepInRegion,regionInteraction,reachedRegionExit} from '../src/region-navigation.js';
test('walks one tile and rejects walls, NPC tiles and non-cardinal moves',()=>{
 assert.deepEqual(stepInRegion(BAMBOO_PASS,{x:1,y:4},1,0),{x:2,y:4});
 assert.equal(stepInRegion(BAMBOO_PASS,{x:4,y:4},0,-1),null);
 assert.equal(stepInRegion(BAMBOO_PASS,{x:5,y:3},1,0),null);
 assert.equal(stepInRegion(BAMBOO_PASS,{x:1,y:4},2,0),null);
 assert.equal(stepInRegion(BAMBOO_PASS,{x:0,y:0},-1,0),null);
});
test('NPC dialogue requires adjacent valid walkable tile',()=>{
 assert.deepEqual(regionInteraction(BAMBOO_PASS,{x:5,y:3}),{npcId:'pass-keeper',dialog:BAMBOO_PASS.npc.dialog});
 assert.equal(regionInteraction(BAMBOO_PASS,{x:1,y:4}),null);
 assert.equal(regionInteraction(BAMBOO_PASS,{x:6,y:3}),null);
 assert.equal(regionInteraction(BAMBOO_PASS,{x:4,y:3}),null);
});
test('exit is exact and invalid region cannot be traversed',()=>{
 assert.equal(reachedRegionExit(BAMBOO_PASS,{x:10,y:4}),true);
 assert.equal(reachedRegionExit(BAMBOO_PASS,{x:9,y:4}),false);
 assert.equal(stepInRegion({...BAMBOO_PASS,name:''},{x:1,y:4},1,0),null);
});
