import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, parseSave, MAX_SILVER, DEMO_SWORD} from '../src/engine.js';

// Original HTML5 demo economy; these values are not recovered from jin.swf.
test('elder reward respects silver ceiling without duplicating the unique sword', () => {
  const s = initialState();
  s.player.x = 7;
  s.player.y = 7;
  s.player.silver = MAX_SILVER - 2;
  s.quest = 'active';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草'];
  const completed = interact(s);
  assert.equal(completed.quest, 'completed');
  assert.equal(completed.player.silver, MAX_SILVER);
  assert.equal(completed.inventory.filter(x => x === DEMO_SWORD).length, 1);
  assert.deepEqual(parseSave(JSON.stringify(completed)), completed);
  const again = interact({...completed, dialog: ''});
  assert.equal(again.player.silver, MAX_SILVER);
  assert.equal(again.inventory.filter(x => x === DEMO_SWORD).length, 1);
});

test('elder grants a unique sword even when reward silver is capped at zero', () => {
  const s = initialState();
  s.player.x = 7;
  s.player.y = 7;
  s.player.silver = MAX_SILVER;
  s.quest = 'active';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草'];
  const completed = interact(s);
  assert.equal(completed.quest, 'completed');
  assert.equal(completed.player.silver, MAX_SILVER);
  assert.equal(completed.inventory.filter(x => x === DEMO_SWORD).length, 1);
  assert.deepEqual(parseSave(JSON.stringify(completed)), completed);
});
