// Original HTML5 demo invariants; no original SWF reward rules are inferred.
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, parseSave, MAX_SILVER, MAX_INVENTORY, DEMO_SWORD} from '../src/engine.js';

function readyToClaim() {
  const s=initialState();
  s.quest='active';
  s.flags.herbTaken=true;
  s.flags.banditBeaten=true;
  s.inventory=['清心草'];
  s.player.x=7;
  s.player.y=5;
  return s;
}

test('quest reward never overflows silver cap and is issued once', () => {
  const s=readyToClaim();
  s.player.silver=MAX_SILVER-1;
  const claimed=interact(s);
  assert.equal(claimed.quest,'completed');
  assert.equal(claimed.player.silver,MAX_SILVER);
  assert.equal(claimed.inventory.filter(x=>x===DEMO_SWORD).length,1);
  assert.deepEqual(parseSave(JSON.stringify(claimed)),claimed);
  const closed=interact(claimed);
  const again=interact(closed);
  assert.equal(again.player.silver,MAX_SILVER);
  assert.equal(again.inventory.filter(x=>x===DEMO_SWORD).length,1);
});

test('full inventory defers reward without changing quest or silver', () => {
  const s=readyToClaim();
  s.inventory.push(...Array(MAX_INVENTORY-s.inventory.length).fill('回春散'));
  const before=structuredClone(s);
  const next=interact(s);
  assert.equal(next.quest,'active');
  assert.equal(next.player.silver,before.player.silver);
  assert.deepEqual(next.inventory,before.inventory);
  assert.equal(next.inventory.includes(DEMO_SWORD),false);
  assert.deepEqual(s,before);
});
