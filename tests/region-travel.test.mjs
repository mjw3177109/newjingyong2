import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {VILLAGE_GATE,VILLAGE_RETURN,enterBambooPass,moveBambooSession,talkBambooSession,leaveBambooPass} from '../src/region-travel.js';

test('entry requires village gate and no dialog or combat',()=>{
 const game=initialState();
 assert.equal(enterBambooPass(game),null);
 const atGate={...game,player:{...game.player,...VILLAGE_GATE}};
 assert.deepEqual(enterBambooPass(atGate),{regionId:BAMBOO_PASS.id,position:BAMBOO_PASS.entry});
 assert.equal(enterBambooPass({...atGate,dialog:'busy'}),null);
 assert.equal(enterBambooPass({...atGate,combat:{enemyHp:1}}),null);
});
test('travel respects collision and keeps the original game untouched',()=>{
 const game={...initialState(),player:{...initialState().player,...VILLAGE_GATE}};
 const session=enterBambooPass(game);
 assert.deepEqual(moveBambooSession(session,1,0)?.position,{x:2,y:4});
 assert.equal(moveBambooSession(session,2,0),null);
 assert.equal(talkBambooSession(session),null);
 assert.equal(leaveBambooPass(session,game),null);
 assert.deepEqual(game.player,{...initialState().player,...VILLAGE_GATE});
});
test('exit returns to a walkable village tile without mutating the source',()=>{
 const game=initialState();
 const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.exit}};
 const returned=leaveBambooPass(session,game);
 assert.deepEqual({x:returned.player.x,y:returned.player.y},VILLAGE_RETURN);
 assert.deepEqual(game,initialState());
 assert.equal(leaveBambooPass({...session,regionId:'unknown'},game),null);
 assert.equal(leaveBambooPass(session,{...game,dialog:'busy'}),null);
});
