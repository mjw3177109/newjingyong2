import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, startRematch, battle, parseSave, DEMO_SWORD} from '../src/engine.js';

// Original HTML5 demo regression only; no source-SWF mechanic is asserted.
function ready() {
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

test('winning a rematch never duplicates quest rewards or changes completion', () => {
  const before = ready();
  let s = startRematch(before);
  assert.ok(s.combat);
  s = battle(s, 'attack');
  assert.ok(s.combat);
  s = battle(s, 'attack');
  assert.equal(s.combat, null);
  assert.equal(s.quest, 'completed');
  assert.equal(s.flags.banditBeaten, true);
  assert.equal(s.player.silver, before.player.silver);
  assert.deepEqual(s.inventory, before.inventory);
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
});

test('repeated rematch victories preserve a single quest weapon', () => {
  let s = ready();
  for (let i = 0; i < 3; i++) {
    s = startRematch(s);
    assert.ok(s.combat);
    s = battle(s, 'attack');
    s = battle(s, 'attack');
    assert.equal(s.combat, null);
    assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
    assert.equal(s.player.silver, 40);
    assert.deepEqual(parseSave(JSON.stringify(s)), s);
  }
});
