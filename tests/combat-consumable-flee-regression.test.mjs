import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, battle, parseSave} from '../src/engine.js';

// Original HTML5 demo regression only; no jin.swf gameplay claim.
const checkpoint = () => {
  const s = initialState();
  s.quest = 'active';
  s.player.x = 18;
  s.player.y = 7;
  s.player.hp = 90;
  s.inventory.push('回春散');
  s.combat = {enemyHp:28, enemyMaxHp:28, guard:false};
  return s;
};

test('combat potion heals only missing HP, consumes one item and one enemy response', () => {
  const before = checkpoint();
  before.player.hp = 95;
  const after = battle(before, 'drink');
  assert.equal(after.player.hp, 94); // +5 heal, then 6 damage
  assert.equal(after.inventory.length, 0);
  assert.equal(after.combat.enemyHp, 28);
  assert.equal(before.player.hp, 95); // pure state transition
  assert.equal(before.inventory.length, 1);
  assert.deepEqual(parseSave(JSON.stringify(after)), after);
});

test('flee ends combat without consuming items or awarding trial victory', () => {
  const before = checkpoint();
  const after = battle(before, 'flee');
  assert.equal(after.combat, null);
  assert.equal(after.player.hp, before.player.hp);
  assert.deepEqual(after.inventory, before.inventory);
  assert.equal(after.flags.banditBeaten, false);
  assert.deepEqual(parseSave(JSON.stringify(after)), after);
});

test('unknown battle action preserves the checkpoint and cannot spend a turn', () => {
  const before = checkpoint();
  const after = battle(before, 'teleport');
  assert.deepEqual(after, before);
  assert.deepEqual(parseSave(JSON.stringify(after)), after);
});
