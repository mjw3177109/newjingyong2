import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, DEMO_SWORD, parseSave, startRematch} from '../src/engine.js';

// These are original HTML5 demo invariants, not recovered jin.swf rules.
const checkpoint = () => {
  const s = initialState();
  s.quest = 'completed';
  s.flags.herbTaken = true;
  s.flags.banditBeaten = true;
  s.inventory = ['清心草', DEMO_SWORD];
  s.player.x = 6;
  s.player.y = 6;
  return startRematch(s);
};
const loaded = s => parseSave(JSON.stringify(s));

test('valid elder rematch checkpoint survives save/load', () => {
  const s = checkpoint();
  assert.equal(s.combat?.enemyHp, 28);
  assert.deepEqual(loaded(s), s);
});

test('rematch checkpoint cannot be relocated to first-trial arena', () => {
  const s = checkpoint();
  s.player.x = 18;
  s.player.y = 7;
  assert.equal(loaded(s), null);
});

test('rematch checkpoint rejects dialog overlay and invalid enemy HP', () => {
  const s = checkpoint();
  const dialog = structuredClone(s);
  dialog.dialog = '不能在战斗时交谈';
  assert.equal(loaded(dialog), null);
  for (const enemyHp of [0, 29, 1.5, '28']) {
    const modified = structuredClone(s);
    modified.combat.enemyHp = enemyHp;
    assert.equal(loaded(modified), null);
  }
});

test('rematch checkpoint cannot lose completed quest or unique sword', () => {
  const s = checkpoint();
  const missingSword = structuredClone(s);
  missingSword.inventory = ['清心草'];
  assert.equal(loaded(missingSword), null);
  const unstarted = structuredClone(s);
  unstarted.quest = 'unstarted';
  assert.equal(loaded(unstarted), null);
});
