import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, startRematch, battle, parseSave, DEMO_SWORD} from '../src/engine.js';

// Original HTML5 demo only. These are not recovered SWF combat rules.
function ready() {
  const s = initialState();
  s.player.x = 7;
  s.player.y = 7;
  s.player.hp = 70;
  s.player.silver = 40;
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD, '回春散'];
  return s;
}

test('rematch potion heals and consumes one turn, then survives save/load', () => {
  const started = startRematch(ready());
  assert.ok(started.combat);
  const drank = battle(started, 'drink');
  assert.equal(drank.player.hp, 94); // +30 healing, then 6 counterdamage
  assert.equal(drank.inventory.includes('回春散'), false);
  assert.equal(drank.combat.enemyHp, 28);
  assert.deepEqual(parseSave(JSON.stringify(drank)), drank);
});

test('fleeing an equipped rematch keeps quest reward and permits a fresh rematch', () => {
  const before = ready();
  before.equipment.weapon = DEMO_SWORD;
  const started = startRematch(before);
  const hit = battle(started, 'attack');
  const fled = battle(hit, 'flee');
  assert.equal(fled.combat, null);
  assert.equal(fled.quest, 'completed');
  assert.equal(fled.player.silver, 40);
  assert.equal(fled.equipment.weapon, DEMO_SWORD);
  assert.deepEqual(fled.inventory, before.inventory);
  assert.deepEqual(parseSave(JSON.stringify(fled)), fled);
  const restarted = startRematch(fled);
  assert.equal(restarted.combat.enemyHp, 28);
});
