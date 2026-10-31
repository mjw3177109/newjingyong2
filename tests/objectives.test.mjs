import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {nextObjective} from '../src/objectives.js';
import {ACTORS} from '../src/demo-data.js';

// Quest hints are exclusively for the original demo; never count as SWF story evidence.
test('new player is guided to the elder using the live demo actor position', () => {
  const s = initialState();
  assert.deepEqual(nextObjective(s), {id:'elder', label:'拜访竹隐老人', x:ACTORS.elder.x, y:ACTORS.elder.y});
});
test('active quest selects remaining objectives in deterministic order', () => {
  const s = initialState(); s.quest = 'active';
  assert.equal(nextObjective(s).id, 'herb');
  s.flags.banditBeaten = true;
  assert.equal(nextObjective(s).id, 'herb');
  s.flags.banditBeaten = false; s.flags.herbTaken = true;
  assert.equal(nextObjective(s).id, 'bandit');
  s.flags.banditBeaten = true;
  assert.equal(nextObjective(s).id, 'elder');
  assert.equal(nextObjective(s).label, '返回竹隐老人处复命');
});
test('completed or unknown quest never points to a removed actor', () => {
  const s = initialState(); s.quest = 'completed';
  assert.equal(nextObjective(s), null);
  s.quest = 'invalid';
  assert.equal(nextObjective(s), null);
  assert.equal(nextObjective(null), null);
});
test('objective calculation does not mutate the game state', () => {
  const s = initialState(); s.quest = 'active';
  const before = structuredClone(s);
  nextObjective(s);
  assert.deepEqual(s, before);
});
