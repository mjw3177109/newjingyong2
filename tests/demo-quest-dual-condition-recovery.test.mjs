import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,interact,battle,DEMO_SWORD} from '../src/engine.js';
import {encodeCheckpoint,decodeCheckpoint} from '../src/browser-checkpoint.js';

// Original Q-style demonstration only; not evidence of jin.swf event semantics.
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
const close=s=>s.dialog?interact(s):s;
function reload(s){
  const raw=encodeCheckpoint(s,{});
  assert.equal(typeof raw,'string');
  const decoded=decodeCheckpoint(raw);
  assert.ok(decoded);
  return decoded.game;
}
function accept(){
  return close(interact(at(initialState(),7,7)));
}
function collect(s){
  return close(interact(at(s,12,9)));
}
function win(s){
  s=interact(at(s,19,8));
  assert.ok(s.combat);
  for(let i=0;i<3;i++)s=battle(s,'attack');
  assert.equal(s.flags.banditBeaten,true);
  return close(s);
}
function assertNoReward(s){
  const silver=s.player.silver;
  s=interact(at(s,7,7));
  assert.equal(s.quest,'active');
  assert.equal(s.player.silver,silver);
  assert.equal(s.inventory.includes(DEMO_SWORD),false);
  return close(reload(s));
}
test('original demo quest requires both herb and trial victory across reloads',()=>{
  let herbOnly=reload(collect(accept()));
  assert.equal(herbOnly.flags.herbTaken,true);
  assert.equal(herbOnly.flags.banditBeaten,false);
  herbOnly=assertNoReward(herbOnly);
  herbOnly=reload(win(herbOnly));
  herbOnly=interact(at(herbOnly,7,7));
  assert.equal(herbOnly.quest,'completed');
  assert.equal(herbOnly.inventory.filter(x=>x===DEMO_SWORD).length,1);

  let trialOnly=reload(win(accept()));
  assert.equal(trialOnly.flags.herbTaken,false);
  assert.equal(trialOnly.flags.banditBeaten,true);
  trialOnly=assertNoReward(trialOnly);
  trialOnly=reload(collect(trialOnly));
  trialOnly=interact(at(trialOnly,7,7));
  assert.equal(trialOnly.quest,'completed');
  assert.equal(trialOnly.inventory.filter(x=>x===DEMO_SWORD).length,1);
});
