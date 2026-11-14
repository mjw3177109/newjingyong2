import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave, equipWeapon, startRematch, DEMO_SWORD} from '../src/engine.js';
import {pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {WIDTH, HEIGHT} from '../src/demo-data.js';

// Original HTML5 demonstration only; not evidence of source-SWF story fidelity.
function walk(state) {
  let current = state;
  for (let i = 0; i < WIDTH * HEIGHT; i++) {
    const path = pathToObjective(current);
    assert.notEqual(path, null, 'demo objective must remain reachable');
    if (path.length === 0) return current;
    current = stepTowardObjective(current);
  }
  assert.fail('demo objective route did not converge');
}
function reload(state) {
  const loaded = parseSave(JSON.stringify(state));
  assert.deepEqual(loaded, state, 'checkpoint must survive strict save validation');
  return loaded;
}

test('completed demo reward and equipment persist across checkpoints and repeat sparring', () => {
  let s = walk(initialState());
  s = reload(interact(s)); // accept quest
  s = walk(interact(s)); // close dialogue and navigate to herb
  s = reload(interact(s)); // collect herb
  s = walk(interact(s)); // close dialogue and navigate to trial
  s = reload(interact(s)); // enter first battle
  for (let i = 0; i < 3; i++) s = battle(s, 'attack');
  assert.equal(s.flags.banditBeaten, true);
  s = walk(reload(s));
  s = reload(interact(s)); // claim reward
  assert.equal(s.quest, 'completed');
  assert.equal(s.player.silver, 40);
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
  s = reload(equipWeapon(interact(s))); // dismiss dialogue, equip sword
  assert.equal(s.equipment.weapon, DEMO_SWORD);
  assert.equal(s.player.silver, 40);
  s = reload(startRematch(s));
  assert.ok(s.combat, 'repeat sparring must remain available after reload');
  s = battle(s, 'attack');
  s = reload(battle(s, 'attack'));
  assert.equal(s.combat, null);
  assert.equal(s.quest, 'completed');
  assert.equal(s.player.silver, 40, 'rematch must not grant duplicate silver');
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1, 'rematch must not duplicate weapon');
  assert.equal(s.equipment.weapon, DEMO_SWORD);
});
