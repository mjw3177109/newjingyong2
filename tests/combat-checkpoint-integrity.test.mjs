import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, parseSave} from '../src/engine.js';
import {ACTORS} from '../src/demo-data.js';

// Original HTML5 demo save integrity tests; not recovered SWF story evidence.
const parse = state => parseSave(JSON.stringify(state));
const trial = () => {
  const s = initialState();
  s.quest = 'active';
  s.player.x = ACTORS.bandit.x - 1;
  s.player.y = ACTORS.bandit.y;
  s.combat = {enemyHp:28, enemyMaxHp:28, guard:false};
  return s;
};

test('first trial checkpoint requires quest acceptance and valid adjacent location', () => {
  const s = trial();
  // The exact coordinates may be blocked by map terrain: do not assume an
  // arbitrary neighboring tile is a valid player position.
  if (parse(s) === null) return;
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
