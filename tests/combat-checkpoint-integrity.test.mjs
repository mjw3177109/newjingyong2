import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, parseSave} from '../src/engine.js';
import {pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {WIDTH, HEIGHT} from '../src/demo-data.js';

// Original HTML5 demo save integrity tests; not recovered SWF story evidence.
const parse = state => parseSave(JSON.stringify(state));
const trial = () => {
  let s = initialState();
  for (let stage = 0; stage < 3; stage++) {
    for (let i = 0; i < WIDTH * HEIGHT; i++) {
      const route = pathToObjective(s);
      assert.notEqual(route, null);
      if (!route.length) break;
      s = stepTowardObjective(s);
    }
    s = interact(s);
    if (stage < 2) s = interact(s); // dismiss dialogue
  }
  assert.ok(s.combat, 'expected real trial checkpoint');
  assert.deepEqual(parse(s), s);
  return s;
};

test('first trial checkpoint requires quest acceptance and valid adjacent location', () => {
  const s = trial();
  assert.deepEqual(parse(s), s);
  const notAccepted = structuredClone(s);
  notAccepted.quest = 'unstarted';
  assert.equal(parse(notAccepted), null);
  const alreadyWon = structuredClone(s);
  alreadyWon.flags.banditBeaten = true;
  assert.equal(parse(alreadyWon), null);
  const outOfRange = structuredClone(s);
  outOfRange.player.x = 5;
  outOfRange.player.y = 8;
  assert.equal(parse(outOfRange), null);
});

test('battle checkpoint rejects forged enemy health and guard fields', () => {
  const s = trial();
  for (const patch of [
    {enemyHp:0}, {enemyHp:29}, {enemyHp:1.5},
    {enemyMaxHp:999}, {guard:'true'}, {extra:true}
  ]) {
    const forged = structuredClone(s);
    Object.assign(forged.combat, patch);
    assert.equal(parse(forged), null, JSON.stringify(patch));
  }
});
