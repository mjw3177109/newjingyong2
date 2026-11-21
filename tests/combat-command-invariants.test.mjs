// Original HTML5 demo regression tests; no source-SWF semantics are inferred.
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, battle, parseSave} from '../src/engine.js';

const trial = () => {
  const s = initialState();
  s.quest = 'active';
  s.player.x = 19;
  s.player.y = 8;
  s.combat = {enemyHp:28,enemyMaxHp:28,guard:false};
  return s;
};

test('unknown combat command cannot consume a turn or mutate its input', () => {
  const state = trial();
  const snapshot = structuredClone(state);
  for (const action of ['cast', '', null, 0, {}, ['attack']]) {
    assert.deepEqual(battle(state,action),snapshot);
    assert.deepEqual(state,snapshot);
  }
});

test('guard mitigates exactly one immediate counterattack and resets before saving', () => {
  let state = trial();
  state = battle(state,'guard');
  assert.equal(state.player.hp,97);
  assert.equal(state.combat.guard,false);
  assert.equal(state.combat.enemyHp,28);
  assert.deepEqual(parseSave(JSON.stringify(state)),state);
  state = battle(state,'guard');
  assert.equal(state.player.hp,94);
  assert.equal(state.combat.guard,false);
});

test('flee leaves trial available and does not award victory', () => {
  const state = trial();
  const fled = battle(state,'flee');
  assert.equal(fled.combat,null);
  assert.equal(fled.flags.banditBeaten,false);
  assert.equal(fled.quest,'active');
  assert.equal(fled.player.hp,100);
  assert.deepEqual(parseSave(JSON.stringify(fled)),fled);
  assert.deepEqual(state,trial());
});
