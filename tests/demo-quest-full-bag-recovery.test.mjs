import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,interact,battle,discardPotion,DEMO_SWORD,MAX_POTIONS} from '../src/engine.js';
import {encodeCheckpoint,decodeCheckpoint} from '../src/browser-checkpoint.js';

// Original Q-style demo only; this does not assert any recovered jin.swf quest behavior.
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
const reload=s=>{
  const raw=encodeCheckpoint(s,{});
  assert.equal(typeof raw,'string');
  const restored=decodeCheckpoint(raw);
  assert.ok(restored,'checkpoint must remain readable');
  return restored.game;
};
const close=s=>s.dialog?interact(s):s;

test('maximum legal potion stack leaves a slot for the quest reward and never duplicates across reloads',()=>{
  let s=initialState();
  s=close(interact(at(s,7,7)));
  assert.equal(s.quest,'active');
  s=close(interact(at(s,12,9)));
  s=interact(at(s,19,8));
  assert.ok(s.combat);
  for(let i=0;i<3;i++)s=battle(s,'attack');
  assert.equal(s.flags.banditBeaten,true);
  assert.equal(s.combat,null);
  s.inventory.push(...Array(MAX_POTIONS).fill('回春散'));
  assert.equal(s.inventory.length,MAX_POTIONS+1);
  s=reload(s);
  const beforeSilver=s.player.silver;
  s=interact(at(s,7,7));
  assert.equal(s.quest,'completed');
  assert.equal(s.player.silver,beforeSilver+30);
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
  s=reload(s);
  for(let i=0;i<3;i++)s=interact(s);
  s=reload(s);
  assert.equal(s.player.silver,beforeSilver+30);
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
});
