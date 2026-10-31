import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave, equipWeapon, DEMO_SWORD} from '../src/engine.js';
import {pathToObjective, stepTowardObjective, nextObjective} from '../src/objectives.js';
import {WIDTH, HEIGHT} from '../src/demo-data.js';

// Integration tests for the ORIGINAL HTML5 demonstration only.
// They do not assert that the demo storyline matches the source SWF.
function walkToObjective(state) {
  let s = state;
  const limit = WIDTH * HEIGHT;
  for (let i = 0; i < limit; i++) {
    const path = pathToObjective(s);
    assert.notEqual(path, null, 'current demo objective must be reachable');
    if (path.length === 0) return s;
    const next = stepTowardObjective(s);
    assert.equal(Math.abs(next.player.x - s.player.x) + Math.abs(next.player.y - s.player.y), 1);
    assert.deepEqual(parseSave(JSON.stringify(next)), next, 'each navigated tile must remain saveable');
    s = next;
  }
  assert.fail('route did not converge within map area');
}

test('full original-demo quest is playable through movement, interactions, combat, reward and save', () => {
  let s = initialState();
  assert.equal(nextObjective(s).id, 'elder');
  s = walkToObjective(s);
  s = interact(s);
  assert.equal(s.quest, 'active');
  s = interact(s); // Dismiss the dialogue, as the browser E button does.
  assert.equal(nextObjective(s).id, 'herb');
  s = walkToObjective(s);
  s = interact(s);
  assert.equal(s.flags.herbTaken, true);
  assert.ok(s.inventory.includes('清心草'));
  s = interact(s);
  assert.equal(nextObjective(s).id, 'bandit');
  s = walkToObjective(s);
  s = interact(s);
  assert.ok(s.combat);
  for (let i = 0; i < 3; i++) s = battle(s, 'attack');
  assert.equal(s.flags.banditBeaten, true);
  assert.equal(s.combat, null);
  assert.equal(nextObjective(s).id, 'elder');
  s = walkToObjective(s);
  s = interact(s);
  assert.equal(s.quest, 'completed');
  assert.equal(s.player.silver, 40);
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.equal(nextObjective(s), null);
  s = interact(s);
  s = equipWeapon(s);
  assert.equal(s.equipment.weapon, DEMO_SWORD);
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
});

test('combat checkpoint resumes with guard and still allows completing the demo quest', () => {
  let s = initialState();
  s = walkToObjective(s);
  s = interact(s);
  s = interact(s);
  s = walkToObjective(s);
  s = interact(s);
  s = interact(s);
  s = walkToObjective(s);
  s = interact(s);
  s = battle(s, 'guard');
  assert.ok(s.combat);
  assert.equal(s.player.hp, 97);
  const resumed = parseSave(JSON.stringify(s));
  assert.deepEqual(resumed, s);
  s = resumed;
  for (let i = 0; i < 3; i++) s = battle(s, 'attack');
  assert.equal(s.flags.banditBeaten, true);
  s = walkToObjective(s);
  s = interact(s);
  assert.equal(s.quest, 'completed');
  assert.deepEqual(parseSave(JSON.stringify(s)), s);
});

test('route stepping cannot silently accept quests or start battles', () => {
  let s = initialState();
  s = walkToObjective(s);
  assert.equal(s.quest, 'unstarted');
  assert.equal(s.dialog, '');
  assert.equal(s.combat, null);
  assert.deepEqual(stepTowardObjective(s), s);
  assert.equal(nextObjective(s).id, 'elder');
});
