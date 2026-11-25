import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, battle, canRematch, startRematch, parseSave} from '../src/engine.js';

// Original HTML5 demo only: these tests do not assert recovered SWF mechanics.
const at = (state, x, y) => ({...state, player: {...state.player, x, y}});
const completed = () => {
  const s = initialState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', '竹纹短剑'];
  return at(s, 7, 7);
};

test('rematch requires a completed quest, elder proximity, and no modal state', () => {
  const s = completed();
  assert.equal(canRematch(s), true);
  for (const blocked of [
    {...s, quest: 'active'},
    at(s, 5, 8),
    {...s, dialog: '交谈中'},
    {...s, combat: {enemyHp: 28, enemyMaxHp: 28, guard: false}}
  ]) {
    assert.equal(canRematch(blocked), false);
    assert.deepEqual(startRematch(blocked), blocked);
  }
});

test('rematch starts with a valid reloadable checkpoint and does not duplicate rewards', () => {
  const before = completed();
  const s = startRematch(before);
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
  assert.equal(s.combat.enemyHp, 28);
  assert.equal(s.player.silver, before.player.silver);
  assert.deepEqual(s.inventory, before.inventory);
  assert.equal(s.quest, 'completed');
  assert.equal(before.combat, null);
});

test('guard halves one incoming hit; fleeing exits without changing quest rewards', () => {
  const s = startRematch(completed());
  const guarded = battle(s, 'guard');
  assert.equal(guarded.player.hp, s.player.hp - 3);
  assert.equal(guarded.combat.guard, false);
  const attacked = battle(guarded, 'attack');
  assert.equal(attacked.player.hp, guarded.player.hp - 6);
  const fled = battle(attacked, 'flee');
  assert.equal(fled.combat, null);
  assert.equal(fled.quest, 'completed');
  assert.equal(fled.flags.banditBeaten, true);
  assert.deepEqual(fled.inventory, s.inventory);
  assert.deepEqual(parseSave(JSON.stringify(fled)), fled);
});
