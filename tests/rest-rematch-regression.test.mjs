import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, canRestAtVillage, restAtVillage, canRematch, startRematch, battle, parseSave, DEMO_SWORD} from '../src/engine.js';

// Original HTML5 demo only; these tests do not assert source-SWF mechanics.
const nearElder = state => ({...state, player:{...state.player,x:7,y:7}});
test('rest heals only missing HP, preserves inventory and creates a valid save', () => {
  const s=nearElder(initialState());
  s.player.hp=93;
  assert.equal(canRestAtVillage(s),true);
  const healed=restAtVillage(s);
  assert.equal(healed.player.hp,100);
  assert.equal(s.player.hp,93);
  assert.deepEqual(healed.inventory,s.inventory);
  assert.match(healed.journal[0],/恢复 7 点气血/);
  assert.deepEqual(parseSave(JSON.stringify(healed)),healed);
  assert.equal(canRestAtVillage(healed),false);
  assert.deepEqual(restAtVillage(healed),healed);
});
test('rest is blocked during dialogue, combat and away from elder', () => {
  const s=nearElder(initialState());s.player.hp=40;
  for(const blocked of [{...s,dialog:'交谈中'},{...s,combat:{enemyHp:28,enemyMaxHp:28,guard:false}},initialState()]){
    assert.equal(canRestAtVillage(blocked),false);
    assert.deepEqual(restAtVillage(blocked),blocked);
  }
});
test('completed demo rematch preserves reward and does not repeat payout', () => {
  const s=nearElder(initialState());
  s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;
  s.inventory=['清心草',DEMO_SWORD];s.player.silver=40;
  assert.equal(canRematch(s),true);
  let next=startRematch(s);
  assert.equal(next.combat.enemyHp,28);
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
  for(let i=0;i<3;i++)next=battle(next,'attack');
  assert.equal(next.combat,null);
  assert.equal(next.player.silver,40);
  assert.equal(next.inventory.filter(item=>item===DEMO_SWORD).length,1);
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
});
