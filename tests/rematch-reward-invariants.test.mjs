// Regression coverage for the original HTML5 demo only; not recovered SWF behavior.
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, DEMO_SWORD, canRematch, startRematch, battle, parseSave} from '../src/engine.js';

function completedAtElder() {
  const s = initialState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory.push('清心草', DEMO_SWORD);
  s.player.x = 7;
  s.player.y = 5;
  return s;
}

test('rematch is gated by completion, proximity, and dialogue', () => {
  const base = initialState();
  assert.equal(canRematch(base), false);
  assert.deepEqual(startRematch(base), base);
  const done = completedAtElder();
  assert.equal(canRematch(done), true);
  const distant = structuredClone(done);
  distant.player.x = 5;
  distant.player.y = 8;
  assert.equal(canRematch(distant), false);
  assert.deepEqual(startRematch(distant), distant);
  const talking = structuredClone(done);
  talking.dialog = '正在对话';
  assert.equal(canRematch(talking), false);
});

test('winning a rematch preserves the one-time reward and remains saveable', () => {
  const original = completedAtElder();
  let s = startRematch(original);
  assert.equal(s.combat.enemyHp, 28);
  assert.deepEqual(original, completedAtElder());
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
  const beforeSilver = s.player.silver;
  const beforeInventory = [...s.inventory];
  for (let turn = 0; turn < 3 && s.combat; turn++) s = battle(s, 'attack');
  assert.equal(s.combat, null);
  assert.equal(s.quest, 'completed');
  assert.equal(s.flags.banditBeaten, true);
  assert.equal(s.player.silver, beforeSilver);
  assert.deepEqual(s.inventory, beforeInventory);
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
});

test('fleeing a rematch does not reset completion or duplicate rewards', () => {
  const original = completedAtElder();
  const active = startRematch(original);
  const fled = battle(active, 'flee');
  assert.equal(fled.combat, null);
  assert.equal(fled.quest, 'completed');
  assert.equal(fled.player.silver, original.player.silver);
  assert.deepEqual(fled.inventory, original.inventory);
  assert.equal(canRematch(fled), true);
  assert.deepEqual(parseSave(JSON.stringify(fled)), fled);
});
