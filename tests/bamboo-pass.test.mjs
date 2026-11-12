import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS,validateRegion} from '../src/bamboo-pass.js';

test('original bamboo pass has a reachable exit and accessible NPC',()=>{
 assert.equal(validateRegion(BAMBOO_PASS),true);
});
test('region rejects blocked exits, duplicate or out-of-bounds walls',()=>{
 assert.equal(validateRegion({...BAMBOO_PASS,blocks:[...BAMBOO_PASS.blocks,'10,4']}),false);
 assert.equal(validateRegion({...BAMBOO_PASS,blocks:[...BAMBOO_PASS.blocks,'4,1']}),false);
 assert.equal(validateRegion({...BAMBOO_PASS,blocks:[...BAMBOO_PASS.blocks,'12,1']}),false);
});
test('region rejects an unreachable exit and an isolated NPC',()=>{
 assert.equal(validateRegion({...BAMBOO_PASS,blocks:[...BAMBOO_PASS.blocks,'9,4','10,3','10,5','11,4']}),false);
 assert.equal(validateRegion({...BAMBOO_PASS,blocks:[...BAMBOO_PASS.blocks,'5,3','6,2','6,4','7,3']}),false);
});
