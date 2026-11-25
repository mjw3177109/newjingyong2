import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, DEMO_SWORD, MAX_SILVER} from '../src/engine.js';
import {encodeCheckpoint, decodeCheckpoint} from '../src/browser-checkpoint.js';

// Original Q-style demo only; no jin.swf quest or currency behavior is inferred.
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
const close=s=>s.dialog?interact(s):s;
const reload=s=>{
  const raw=encodeCheckpoint(s,{});
  assert.equal(typeof raw,'string');
  const restored=decodeCheckpoint(raw);
  assert.ok(restored,'checkpoint must be readable');
  return restored.game;
};
const ready=()=>{
  let s=initialState();
  s=close(interact(at(s,7,7)));
  s=close(interact(at(s,12,9)));
  s=interact(at(s,19,8));
  assert.ok(s.combat);
  for(let i=0;i<3;i++)s=battle(s,'attack');
  assert.equal(s.flags.banditBeaten,true);
  return close(s);
};

test('quest silver reward respects currency cap and remains one-time after reload',()=>{
  for(const [before,expected] of [
    [MAX_SILVER-10,MAX_SILVER],
    [MAX_SILVER,MAX_SILVER],
  ]){
    let s=ready();
    s.player.silver=before;
    s=reload(s);
    s=interact(at(s,7,7));
    assert.equal(s.quest,'completed');
    assert.equal(s.player.silver,expected);
    assert.equal(s.inventory.filter(item=>item===DEMO_SWORD).length,1);
    s=reload(s);
    s=close(s);
    s=interact(s);
    assert.equal(s.player.silver,expected);
    assert.equal(s.inventory.filter(item=>item===DEMO_SWORD).length,1);
    assert.ok(reload(s));
  }
});
