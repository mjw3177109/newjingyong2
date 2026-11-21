import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave} from '../src/engine.js';

// Original HTML5 demo mechanics only; these are not claims about jin.swf.
const roundTrip = state => parseSave(JSON.stringify(state));

test('first trial cannot start before accepting the demo quest', () => {
  const state = initialState();
  state.player.x = 18;
  state.player.y = 7;
  const blocked = interact(state);
  assert.equal(blocked.combat, null);
  assert.equal(blocked.quest, 'unstarted');
  assert.match(blocked.dialog, /竹隐老人/);
  assert.deepEqual(roundTrip(blocked), blocked);
});

test('guard is consumed by counterattack and does not carry into the next turn or save', () => {
  const state = initialState();
  state.quest = 'active';
  state.player.x = 18;
  state.player.y = 7;
  const started = interact(state);
  assert.ok(started.combat);
  const guarded = battle(started, 'guard');
  assert.equal(guarded.player.hp, 97);
  assert.equal(guarded.combat.guard, false);
  assert.deepEqual(roundTrip(guarded), guarded);
  const attacked = battle(roundTrip(guarded), 'attack');
  assert.equal(attacked.player.hp, 91);
  assert.equal(attacked.combat.guard, false);
  assert.deepEqual(roundTrip(attacked), attacked);
});
