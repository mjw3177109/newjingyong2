import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, startRematch, battle, parseSave, DEMO_SWORD} from '../src/engine.js';

// Original HTML5 demo behavior; not recovered SWF combat evidence.
function ready(hp, potions = []) {
  const s = initialState();
  s.player.x = 7;
  s.player.y = 7;
  s.player.hp = hp;
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD, ...potions];
  return startRematch(s);
}

test('rematch refuses medicine at full HP without enemy retaliation or journal mutation', () => {
  const before = ready(100, ['回春散']);
  assert.ok(before.combat);
  const after = battle(before, 'drink');
  assert.deepEqual(after, before);
  assert.deepEqual(parseSave(JSON.stringify(after)), after);
});

test('rematch refuses medicine when none is held without consuming a turn', () => {
  const before = ready(70);
  assert.ok(before.combat);
  const after = battle(before, 'drink');
  assert.deepEqual(after, before);
  assert.deepEqual(parseSave(JSON.stringify(after)), after);
});
