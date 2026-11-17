// Original HTML5 demo save boundary tests; no source-SWF semantics are asserted.
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, parseSave, interact, startRematch} from '../src/engine.js';

const load = s => parseSave(JSON.stringify(s));

test('first trial cannot be injected before quest acceptance', () => {
  const forged = initialState();
  forged.player.x = 18;
  forged.player.y = 7;
  forged.combat = {enemyHp:28, enemyMaxHp:28, guard:false};
  assert.equal(load(forged), null);
  const accepted = structuredClone(forged);
  accepted.quest = 'active';
  assert.deepEqual(load(accepted), accepted);
});

test('active first-trial save must be adjacent to trial actor', () => {
  const state = initialState();
  state.quest = 'active';
  state.player.x = 18;
  state.player.y = 7;
  const fighting = interact(state);
  assert.ok(fighting.combat);
  assert.deepEqual(load(fighting), fighting);
  const moved = structuredClone(fighting);
  moved.player.x = 5;
  moved.player.y = 8;
  assert.equal(load(moved), null);
});

test('completed rematch save is accepted only by elder and without dialog', () => {
  const state = initialState();
  state.quest = 'completed';
  state.flags.herbTaken = true;
  state.flags.banditBeaten = true;
  state.inventory = ['清心草', '竹纹短剑'];
  state.player.x = 7;
  state.player.y = 5;
  const fighting = startRematch(state);
  assert.ok(fighting.combat);
  assert.deepEqual(load(fighting), fighting);
  const displaced = structuredClone(fighting);
  displaced.player.x = 18;
  displaced.player.y = 7;
  assert.equal(load(displaced), null);
  const dialog = structuredClone(fighting);
  dialog.dialog = 'forged';
  assert.equal(load(dialog), null);
});
