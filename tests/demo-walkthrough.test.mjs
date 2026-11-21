import test from 'node:test';
import assert from 'node:assert/strict';
import { initialState, interact, battle, equipWeapon, parseSave, DEMO_SWORD, attackDamage } from '../src/engine.js';

// Synthetic original-demo walkthrough, not evidence of any jin.swf storyline.
const at = (state, x, y) => ({...state, player: {...state.player, x, y}});
const checkpoint = state => {
  const restored = parseSave(JSON.stringify(state));
  assert.deepEqual(restored, state, 'every milestone must survive save/load');
  return restored;
};
const closeDialog = state => state.dialog ? interact(state) : state;

test('original Q-style demo: full quest, saved checkpoints, unique reward and rematch-safe equipment', () => {
  let s = checkpoint(initialState());
  s = checkpoint(interact(at(s, 7, 7)));
  assert.equal(s.quest, 'active');
  s = closeDialog(s);
  s = checkpoint(interact(at(s, 12, 9)));
  assert.equal(s.flags.herbTaken, true);
  s = closeDialog(s);
  s = checkpoint(interact(at(s, 19, 8)));
  assert.ok(s.combat, 'accepted trial must begin combat');
  for (let i = 0; i < 3; i++) s = checkpoint(battle(s, 'attack'));
  assert.equal(s.flags.banditBeaten, true);
  assert.equal(s.combat, null);
  s = checkpoint(interact(at(s, 7, 7)));
  assert.equal(s.quest, 'completed');
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.equal(s.player.silver, 40);
  s = closeDialog(s);
  s = checkpoint(equipWeapon(s));
  assert.equal(attackDamage(s), 16);
  s = checkpoint(interact(at(s, 7, 7)));
  s = closeDialog(s);
  s = checkpoint(interact(at(s, 7, 7)));
  assert.equal(s.inventory.filter(item => item === DEMO_SWORD).length, 1);
  assert.equal(s.player.silver, 40);
});
