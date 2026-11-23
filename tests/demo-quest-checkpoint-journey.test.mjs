import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,interact,battle,DEMO_SWORD} from '../src/engine.js';
import {encodeCheckpoint,decodeCheckpoint} from '../src/browser-checkpoint.js';

// Original Q-style demo only; never interpreted as a recovered jin.swf event.
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
function roundTrip(state){
 const raw=encodeCheckpoint(state,{});
 assert.equal(typeof raw,'string');
 const loaded=decodeCheckpoint(raw);
 assert.ok(loaded,'checkpoint must decode at each quest milestone');
 assert.deepEqual(loaded.game,state);
 return loaded.game;
}
test('original demo NPC quest survives checkpoints at each milestone without duplicate rewards',()=>{
 let s=roundTrip(initialState());
 s=interact(at(s,7,7));
 assert.equal(s.quest,'active');
 s=roundTrip(s);
 s=interact(s); // close NPC dialogue
 s=interact(at(s,12,9));
 assert.equal(s.flags.herbTaken,true);
 s=roundTrip(s);
 s=interact(s); // close herb dialogue
 s=interact(at(s,19,8));
 assert.ok(s.combat);
 s=roundTrip(s);
 for(let i=0;i<3;i++)s=battle(s,'attack');
 assert.equal(s.flags.banditBeaten,true);
 assert.equal(s.combat,null);
 s=roundTrip(s);
 s=interact(at(s,7,7));
 assert.equal(s.quest,'completed');
 assert.equal(s.player.silver,40);
 assert.equal(s.inventory.filter(item=>item===DEMO_SWORD).length,1);
 s=roundTrip(s);
 for(let i=0;i<3;i++)s=interact(s);
 s=roundTrip(s);
 assert.equal(s.player.silver,40);
 assert.equal(s.inventory.filter(item=>item===DEMO_SWORD).length,1);
});
