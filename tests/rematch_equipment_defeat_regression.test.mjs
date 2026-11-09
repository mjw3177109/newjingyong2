import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, equipWeapon, startRematch, battle, parseSave, DEMO_SWORD} from '../src/engine.js';

// Original Q-style HTML5 demo mechanics only; no SWF event semantics inferred.
function completedNearElder() {
  const s = initialState();
  s.player.x = 7;
  s.player.y = 7;
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD, '回春散'];
  s.player.silver = 40;
  return s;
}

test('equipped sword rematch survives a mid-combat save and awards nothing twice', () => {
  const equipped = equipWeapon(completedNearElder());
  assert.equal(equipped.equipment.weapon, DEMO_SWORD);
  const started = startRematch(equipped);
  const firstHit = battle(started, 'attack');
  assert.equal(firstHit.combat.enemyHp, 12);
  const restored = parseSave(JSON.stringify(firstHit));
  assert.deepEqual(restored, firstHit);
  const won = battle(restored, 'attack');
  assert.equal(won.combat, null);
  assert.equal(won.quest, 'completed');
  assert.equal(won.player.silver, 40);
  assert.equal(won.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.equal(won.equipment.weapon, DEMO_SWORD);
  assert.deepEqual(parseSave(JSON.stringify(won)), won);
});

test('a rematch loss preserves the completed quest and its unique weapon', () => {
  const s = completedNearElder();
  s.player.hp = 5;
  const started = startRematch(s);
  const lost = battle(started, 'attack');
  assert.equal(lost.combat, null);
  assert.equal(lost.player.hp, 50);
  assert.deepEqual([lost.player.x, lost.player.y], [5, 8]);
  assert.equal(lost.quest, 'completed');
  assert.equal(lost.player.silver, 40);
  assert.equal(lost.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.deepEqual(parseSave(JSON.stringify(lost)), lost);
});
