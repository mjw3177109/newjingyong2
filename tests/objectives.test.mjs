import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {nextObjective, pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {pathToTile} from '../src/tile-path.js';
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

test('objective guidance and Canvas taps share the same route across demo quest phases', () => {
  const states = [];
  const unstarted = initialState(); states.push(unstarted);
  const herb = initialState(); herb.quest = 'active'; states.push(herb);
  const bandit = initialState(); bandit.quest = 'active';
  bandit.flags.herbTaken = true; bandit.inventory.push('清心草'); states.push(bandit);
  const returnElder = structuredClone(bandit); returnElder.flags.banditBeaten = true; states.push(returnElder);
  for (const s of states) {
    const target = nextObjective(s);
    const before = structuredClone(s);
    assert.deepEqual(pathToObjective(s), pathToTile(s, target.x, target.y), target.id);
    assert.deepEqual(s, before, 'route to ' + target.id + ' mutated state');
  }
});

test('guidance is inert for completed quest and cannot move during dialogue', () => {
  const s = initialState();
  s.quest = 'completed';
  assert.equal(pathToObjective(s), null);
  assert.deepEqual(stepTowardObjective(s), s);
  const dialog = initialState(); dialog.dialog = '原创演示对话';
  assert.equal(stepTowardObjective(dialog), dialog);
});

test('guidance takes exactly one cardinal step and stops adjacent to its target', () => {
  let s = initialState();
  for (let i = 0; i < 200 && pathToObjective(s)?.length; i++) {
    const before = s.player;
    s = stepTowardObjective(s);
    assert.equal(Math.abs(s.player.x - before.x) + Math.abs(s.player.y - before.y), 1);
  }
  assert.deepEqual(pathToObjective(s), []);
  assert.equal(Math.abs(s.player.x - ACTORS.elder.x) + Math.abs(s.player.y - ACTORS.elder.y), 1);
});
