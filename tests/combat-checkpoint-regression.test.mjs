import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, battle, parseSave} from '../src/engine.js';

// Original HTML5 demo invariants, not claims about jin.swf mechanics.
const fighting = () => {
  const s=initialState();
  s.quest='active';
  s.player.x=18;s.player.y=7;
  s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
  return s;
};

test('invalid battle medicine does not spend a turn or mutate the checkpoint', () => {
  const s=fighting();
  const result=battle(s,'drink');
  assert.deepEqual(result,s);
  assert.deepEqual(parseSave(JSON.stringify(result)),result);
});

test('guard reduces exactly one counterattack and resets before next turn', () => {
  const s=fighting();
  const guarded=battle(s,'guard');
  assert.equal(guarded.player.hp,97);
  assert.equal(guarded.combat.guard,false);
  const next=battle(guarded,'guard');
  assert.equal(next.player.hp,94);
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
});

test('combat defeat returns player to village with valid save and no victory flag', () => {
  const s=fighting();
  s.player.hp=2;
  const defeated=battle(s,'guard');
  assert.equal(defeated.combat,null);
  assert.equal(defeated.player.hp,50);
  assert.deepEqual([defeated.player.x,defeated.player.y],[5,8]);
  assert.equal(defeated.flags.banditBeaten,false);
  assert.deepEqual(parseSave(JSON.stringify(defeated)),defeated);
});
