import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, DEMO_SWORD, startRematch, battle, parseSave} from '../src/engine.js';

// Original HTML5 demo only; no gameplay values inferred from jin.swf.
test('winning an elder rematch keeps rewards single-issue and save valid', () => {
  const s = initialState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD, '回春散'];
  s.player.x = 6;
  s.player.y = 6;
  s.player.silver = 40;
  const before = structuredClone(s);
  let current = startRematch(s);
  assert.equal(current.combat?.enemyHp, 28);
  current = battle(current, 'attack');
  assert.equal(current.combat?.enemyHp, 16);
  current = battle(current, 'attack');
  assert.equal(current.combat?.enemyHp, 4);
  current = battle(current, 'attack');
  assert.equal(current.combat, null);
  assert.equal(current.flags.banditBeaten, true);
  assert.equal(current.quest, 'completed');
  assert.equal(current.player.silver, before.player.silver);
  assert.deepEqual(current.inventory, before.inventory);
  assert.equal(current.player.hp, 88);
  assert.deepEqual(parseSave(JSON.stringify(current)), current);
  assert.deepEqual(s, before);
});
