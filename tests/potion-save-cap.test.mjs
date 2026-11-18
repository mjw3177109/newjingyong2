import test from 'node:test';
import assert from 'node:assert/strict';
import { initialState, parseSave, MAX_POTIONS, MAX_INVENTORY } from '../src/engine.js';

// Original HTML5 demo invariant only; no rule is inferred from jin.swf.
test('imported demo save rejects potion stack beyond merchant limit', () => {
  const state = initialState();
  state.inventory = Array(MAX_POTIONS + 1).fill('回春散');
  assert.ok(state.inventory.length <= MAX_INVENTORY);
  assert.equal(parseSave(JSON.stringify(state)), null);
});

test('imported demo save accepts potion stack exactly at merchant limit', () => {
  const state = initialState();
  state.inventory = Array(MAX_POTIONS).fill('回春散');
  assert.deepEqual(parseSave(JSON.stringify(state)), state);
});
