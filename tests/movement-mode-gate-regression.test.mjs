import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, move, interact, parseSave} from '../src/engine.js';

// Original HTML5 demo controls only; not recovered from jin.swf.
const roundTrip = state => parseSave(JSON.stringify(state));

test('movement rejects teleport, diagonal, fractional and nonnumeric vectors without changing state', () => {
  const start = initialState();
  for (const [dx, dy] of [[2,0],[0,-2],[1,1],[0,0],[0.5,0.5],[NaN,0],[Infinity,0],['1',0]]) {
    assert.deepEqual(move(start, dx, dy), start);
  }
  assert.deepEqual(roundTrip(start), start);
});

test('dialog and combat prevent movement until the mode is exited', () => {
  const dialogState = interact(initialState());
  assert.ok(dialogState.dialog);
  assert.deepEqual(move(dialogState,1,0), dialogState);
  assert.deepEqual(roundTrip(dialogState), dialogState);

  const accepted = initialState();
  accepted.quest = 'active';
  accepted.player.x = 18;
  accepted.player.y = 7;
  const fighting = interact(accepted);
  assert.ok(fighting.combat);
  assert.deepEqual(move(fighting,-1,0), fighting);
  assert.deepEqual(roundTrip(fighting), fighting);
});
