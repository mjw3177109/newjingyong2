import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave, DEMO_SWORD} from '../src/engine.js';
import {pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {WIDTH, HEIGHT} from '../src/demo-data.js';

// Original HTML5 demonstration regression, not recovered SWF story evidence.
function walkToObjective(state) {
  let s = state;
  for (let i = 0; i < WIDTH * HEIGHT; i++) {
    const route = pathToObjective(s);
    assert.notEqual(route, null);
    if (!route.length) return s;
    s = stepTowardObjective(s);
  }
  assert.fail('objective route did not converge');
}
const checkpoint = s => {
  const restored = parseSave(JSON.stringify(s));
  assert.deepEqual(restored, s);
  return restored;
};

test('losing a saved first trial resets combat without awarding victory or blocking a retry', () => {
  let s = walkToObjective(initialState());
  s = interact(s); // accept quest
  s = walkToObjective(interact(s)); // close dialog, reach herb
  s = interact(s); // collect herb
  s = walkToObjective(interact(s)); // close dialog, reach first trial
  s.player.hp = 6; // valid low-health checkpoint before trial
  s = checkpoint(interact(s));
  assert.ok(s.combat);
  s = checkpoint(battle(s, 'attack')); // enemy counterattack defeats player
  assert.equal(s.combat, null);
  assert.equal(s.player.hp, 50);
  assert.equal(s.flags.banditBeaten, false);
  assert.equal(s.quest, 'active');
  assert.equal(s.inventory.includes(DEMO_SWORD), false);
  s = walkToObjective(s);
  s = checkpoint(interact(s)); // retry remains accessible
  assert.ok(s.combat);
  for (let i = 0; i < 3; i++) s = battle(s, 'attack');
  assert.equal(s.flags.banditBeaten, true);
  assert.equal(s.quest, 'active'); // reward only on elder interaction
  assert.equal(s.inventory.includes(DEMO_SWORD), false);
  s = walkToObjective(checkpoint(s));
  s = checkpoint(interact(s));
  assert.equal(s.quest, 'completed');
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
});
