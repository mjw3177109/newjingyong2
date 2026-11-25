import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, parseSave, DEMO_SWORD, MAX_POTIONS, MAX_INVENTORY} from '../src/engine.js';

// Original HTML5 demo compatibility tests, not evidence about jin.swf.
function legacyState() {
  const s = initialState();
  delete s.equipment;
  s.version = 1;
  return s;
}

test('completed V1 save at 64 slots migrates with sword into slot 65', () => {
  const s = legacyState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = [...Array(MAX_POTIONS).fill('回春散'), '清心草'];
  assert.equal(s.inventory.length, 64);
  const migrated = parseSave(JSON.stringify(s));
  assert.ok(migrated, 'valid legacy save must remain loadable');
  assert.equal(migrated.version, 2);
  assert.equal(migrated.inventory.length, MAX_INVENTORY);
  assert.equal(migrated.inventory.at(-1), DEMO_SWORD);
  assert.equal(migrated.inventory.filter(i => i === '回春散').length, MAX_POTIONS);
  assert.equal(migrated.equipment.weapon, null);
});

test('V1 save with 64 potions is rejected instead of silently deleting an item', () => {
  const s = legacyState();
  s.inventory = Array(MAX_POTIONS + 1).fill('回春散');
  assert.equal(parseSave(JSON.stringify(s)), null);
});

test('completed V1 save without room for sword is rejected if potion count exceeds cap', () => {
  const s = legacyState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = [...Array(MAX_POTIONS + 1).fill('回春散'), '清心草'];
  assert.equal(parseSave(JSON.stringify(s)), null);
});
