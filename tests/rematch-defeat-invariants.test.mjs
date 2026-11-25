// Original HTML5 demo regression only; this is not recovered SWF gameplay.
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, DEMO_SWORD, startRematch, battle, parseSave, canRematch} from '../src/engine.js';

test('rematch defeat preserves completed quest and one-time rewards', () => {
  const ready = initialState();
  ready.quest = 'completed';
  ready.flags.herbTaken = true;
  ready.flags.banditBeaten = true;
  ready.inventory = ['清心草', DEMO_SWORD];
  ready.player.x = 7;
  ready.player.y = 5;
  ready.player.hp = 3;
  const silver = ready.player.silver;
  const inventory = [...ready.inventory];
  assert.equal(canRematch(ready), true);
  const active = startRematch(ready);
  assert.deepEqual(parseSave(JSON.stringify(active)), active);
  const defeated = battle(active, 'guard');
  assert.equal(defeated.combat, null);
  assert.equal(defeated.player.hp, 50);
  assert.deepEqual([defeated.player.x, defeated.player.y], [5, 8]);
  assert.equal(defeated.quest, 'completed');
  assert.equal(defeated.flags.banditBeaten, true);
  assert.equal(defeated.player.silver, silver);
  assert.deepEqual(defeated.inventory, inventory);
  assert.deepEqual(parseSave(JSON.stringify(defeated)), defeated);
  assert.deepEqual(ready.inventory, inventory);
});
