import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave} from '../src/engine.js';
import {pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {WIDTH, HEIGHT} from '../src/demo-data.js';

// Original-demo regression only; not evidence of recovered SWF combat rules.
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
const reload = s => {
  const loaded = parseSave(JSON.stringify(s));
  assert.deepEqual(loaded, s);
  return loaded;
};

test('combat guard checkpoint preserves turn state; invalid medicine and flee cannot award trial', () => {
  let s = walkToObjective(initialState());
  s = interact(s); // accept quest
  s = walkToObjective(interact(s));
  s = interact(s); // herb
  s = walkToObjective(interact(s));
  s = reload(interact(s)); // enter first trial
  assert.ok(s.combat);
  s = reload(battle(s, 'guard'));
  assert.equal(s.combat.guard, false); // guard is consumed by the counterattack
  assert.equal(s.player.hp, 97);
  const beforeInvalid = structuredClone(s);
  s = battle(s, 'drink'); // no medicine; must not consume a turn
  assert.deepEqual(s, beforeInvalid);
  s = reload(battle(s, 'flee'));
  assert.equal(s.combat, null);
  assert.equal(s.quest, 'active');
  assert.equal(s.flags.banditBeaten, false);
  assert.equal(s.inventory.includes('竹纹短剑'), false);
  s = walkToObjective(s);
  s = reload(interact(s));
  assert.ok(s.combat); // fleeing cannot lock the original trial
});
