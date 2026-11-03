import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, DEMO_SWORD, startRematch, battle, parseSave} from '../src/engine.js';

// Original demo mechanics only; no original-SWF event or numerical claim.
function completedCheckpoint() {
  const s = initialState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD, '回春散'];
  s.player.x = 6;
  s.player.y = 6; // one tile from elder at (7,6)
  s.player.hp = 4;
  s.player.silver = 40;
  return s;
}

test('rematch defeat returns to village without duplicate rewards or corrupting save', () => {
  const original = completedCheckpoint();
  const started = startRematch(original);
  assert.equal(started.combat.enemyHp, 28);
  assert.deepEqual(parseSave(JSON.stringify(started)), started);
  const lost = battle(started, 'attack');
  assert.equal(lost.combat, null);
  assert.equal(lost.player.hp, 50);
  assert.deepEqual([lost.player.x, lost.player.y], [5, 8]);
  assert.equal(lost.quest, 'completed');
  assert.equal(lost.flags.banditBeaten, true);
  assert.equal(lost.player.silver, 40);
  assert.deepEqual(lost.inventory, original.inventory);
  assert.deepEqual(parseSave(JSON.stringify(lost)), lost);
  assert.equal(original.combat, null);
});

test('fleeing a rematch preserves completed quest, inventory and currency', () => {
  const original = completedCheckpoint();
  const fled = battle(startRematch(original), 'flee');
  assert.equal(fled.combat, null);
  assert.equal(fled.quest, 'completed');
  assert.equal(fled.player.silver, original.player.silver);
  assert.deepEqual(fled.inventory, original.inventory);
  assert.deepEqual(parseSave(JSON.stringify(fled)), fled);
});

test('rematch cannot start without completed quest or while a dialog is open', () => {
  const s = completedCheckpoint();
  const speaking = structuredClone(s);
  speaking.dialog = '对话中';
  assert.deepEqual(startRematch(speaking), speaking);
  const unfinished = structuredClone(s);
  unfinished.quest = 'active';
  assert.deepEqual(startRematch(unfinished), unfinished);
});
