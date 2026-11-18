import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, discardPotion, parseSave, DEMO_SWORD, MAX_INVENTORY, MAX_POTIONS} from '../src/engine.js';

// Original HTML5 demo only; no quest rules inferred from jin.swf.
const roundTrip = state => parseSave(JSON.stringify(state));

test('full bag defers quest reward; discard one potion then claim exactly once', () => {
  const initial = initialState();
  initial.quest = 'active';
  initial.flags.herbTaken = true;
  initial.flags.banditBeaten = true;
  initial.inventory = ['清心草', ...Array(MAX_POTIONS).fill('回春散')];
  initial.player.x = 6;
  initial.player.y = 6;
  assert.deepEqual(roundTrip(initial), initial);

  const blocked = interact(initial);
  assert.equal(blocked.quest, 'completed');
  assert.equal(blocked.player.silver, initial.player.silver + 30);
  assert.equal(blocked.inventory.length, MAX_INVENTORY);
  assert.equal(blocked.inventory.at(-1), DEMO_SWORD);
  assert.deepEqual(roundTrip(blocked), blocked);

  const closed = interact(blocked);
  assert.equal(closed.dialog, '');
  const freed = discardPotion(closed);
  assert.equal(freed.inventory.length, MAX_INVENTORY - 1);
  assert.equal(freed.quest, 'completed');
  assert.deepEqual(roundTrip(freed), freed);

  const awarded = interact(freed);
  assert.equal(awarded.quest, 'completed');
  assert.equal(awarded.player.silver, initial.player.silver + 30);
  assert.equal(awarded.inventory.length, MAX_INVENTORY - 1);
  assert.equal(awarded.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.deepEqual(roundTrip(awarded), awarded);

  const closedReward = interact(awarded);
  const repeated = interact(closedReward);
  assert.equal(repeated.player.silver, awarded.player.silver);
  assert.equal(repeated.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.deepEqual(roundTrip(repeated), repeated);
});
