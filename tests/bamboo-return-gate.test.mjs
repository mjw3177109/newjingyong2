import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {VILLAGE_GATE,VILLAGE_RETURN,enterBambooPass,leaveBambooPass} from '../src/region-travel.js';

// Original Q-style demo only: these checkpoints are not extracted SWF events.
const at=(game,x,y)=>({...game,player:{...game.player,x,y}});
const atGate=()=>at(initialState(),VILLAGE_GATE.x,VILLAGE_GATE.y);
const atExit=()=>({regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.exit}});

test('return requires the original village gate checkpoint',()=>{
 const checkpoint=atGate();
 const exit=atExit();
 assert.equal(leaveBambooPass(exit,at(checkpoint,0,0)),null);
 assert.equal(leaveBambooPass(exit,at(checkpoint,-1,7)),null);
 assert.equal(leaveBambooPass(exit,at(checkpoint,1.5,7)),null);
 const returned=leaveBambooPass(exit,checkpoint);
 assert.ok(returned);
 assert.deepEqual({x:returned.player.x,y:returned.player.y},VILLAGE_RETURN);
 assert.deepEqual(checkpoint.player,{...initialState().player,...VILLAGE_GATE},'checkpoint must not mutate');
});

test('return rejects dialogue and combat checkpoint and never changes source state',()=>{
 const checkpoint=atGate(),exit=atExit();
 const dialogue={...checkpoint,dialog:'test'};
 const combat={...checkpoint,combat:{active:true}};
 assert.equal(leaveBambooPass(exit,dialogue),null);
 assert.equal(leaveBambooPass(exit,combat),null);
 assert.ok(enterBambooPass(checkpoint));
 assert.equal(enterBambooPass(dialogue),null);
 assert.equal(enterBambooPass(combat),null);
});
