import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave} from '../src/engine.js';

// These checks cover original HTML5 demo rules, not recovered jin.swf events.
const roundTrip = state => parseSave(JSON.stringify(state));

test('first trial flee preserves accepted quest and allows a fresh retry', () => {
  const state = initialState();
  state.quest = 'active';
  state.player.x = 18;
  state.player.y = 7;
  const started = interact(state);
  assert.equal(started.combat?.enemyHp, 28);
  const guarded = battle(started, 'guard');
  assert.equal(guarded.player.hp, 97);
  const fled = battle(guarded, 'flee');
  assert.equal(fled.combat, null);
  assert.equal(fled.quest, 'active');
  assert.equal(fled.flags.banditBeaten, false);
  assert.equal(fled.player.hp, 97);
  assert.deepEqual(roundTrip(fled), fled);
  const retried = interact(roundTrip(fled));
  assert.equal(retried.combat?.enemyHp, 28);
  assert.equal(retried.combat?.guard, false);
  assert.deepEqual(roundTrip(retried), retried);
});

test('fleeing first trial never grants victory or quest rewards', () => {
  const state = initialState();
  state.quest = 'active';
  state.player.x = 18;
  state.player.y = 7;
  const fled = battle(interact(state), 'flee');
  assert.equal(fled.flags.banditBeaten, false);
  assert.equal(fled.player.silver, 10);
  assert.deepEqual(fled.inventory, []);
  assert.equal(fled.quest, 'active');
  assert.deepEqual(roundTrip(fled), fled);
});
