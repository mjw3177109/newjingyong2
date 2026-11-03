import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, parseSave, DEMO_SWORD, MAX_INVENTORY, MAX_POTIONS, MAX_SILVER} from '../src/engine.js';

// Original HTML5 demo only; these are not rules recovered from jin.swf.
function readyToClaim(silver, potions) {
  const s = initialState();
  s.quest = 'active';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', ...Array(potions).fill('回春散')];
  s.player.silver = silver;
  s.player.x = 6;
  s.player.y = 6;
  return s;
}
const load = state => parseSave(JSON.stringify(state));

test('quest reward respects silver cap and remains one-time at cap', () => {
  const before = readyToClaim(MAX_SILVER - 2, 0);
  assert.deepEqual(load(before), before);
  const awarded = interact(before);
  assert.equal(awarded.quest, 'completed');
  assert.equal(awarded.player.silver, MAX_SILVER);
  assert.equal(awarded.inventory.filter(x => x === DEMO_SWORD).length, 1);
  assert.deepEqual(load(awarded), awarded);
  const afterDialog = interact(awarded);
  const repeated = interact(afterDialog);
  assert.equal(repeated.player.silver, MAX_SILVER);
  assert.equal(repeated.inventory.filter(x => x === DEMO_SWORD).length, 1);
  assert.deepEqual(load(repeated), repeated);
});

test('full inventory defers reward without consuming quest completion', () => {
  const full = readyToClaim(10, MAX_INVENTORY - 1);
  assert.equal(full.inventory.length, MAX_INVENTORY);
  assert.deepEqual(load(full), full); // imported legacy-shaped inventory may exceed merchant purchase cap
  const deferred = interact(full);
  assert.equal(deferred.quest, 'active');
  assert.equal(deferred.player.silver, full.player.silver);
  assert.equal(deferred.inventory.length, MAX_INVENTORY);
  assert.match(deferred.dialog, /行囊已满/);
  assert.deepEqual(load(deferred), deferred);
  const allowed = readyToClaim(10, MAX_POTIONS);
  assert.equal(allowed.inventory.length, MAX_POTIONS + 1);
  assert.deepEqual(load(allowed), allowed);
  const rewarded = interact(allowed);
  assert.equal(rewarded.quest, 'completed');
  assert.equal(rewarded.inventory.length, MAX_INVENTORY);
  assert.equal(rewarded.inventory.at(-1), DEMO_SWORD);
  assert.deepEqual(load(rewarded), rewarded);
});
