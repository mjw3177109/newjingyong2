import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, startRematch, battle, DEMO_SWORD, parseSave} from '../src/engine.js';
import {ACTORS} from '../src/demo-data.js';

// Original demo only. This is not a reconstructed jin.swf event.
test('completed quest rematch preserves one-time rewards and remains saveable', () => {
  const before=initialState();
  before.quest='completed';
  before.flags.herbTaken=true;
  before.flags.banditBeaten=true;
  before.inventory=['清心草',DEMO_SWORD];
  before.player.x=ACTORS.elder.x+1;
  before.player.y=ACTORS.elder.y;
  const silver=before.player.silver;
  const inventory=[...before.inventory];
  let current=startRematch(before);
  assert.ok(current.combat,'rematch should begin beside elder');
  assert.ok(parseSave(JSON.stringify(current)),'active rematch checkpoint should validate');
  for(let i=0;i<3&&current.combat;i++)current=battle(current,'attack');
  assert.equal(current.combat,null);
  assert.equal(current.quest,'completed');
  assert.equal(current.player.silver,silver);
  assert.deepEqual(current.inventory,inventory);
  assert.ok(parseSave(JSON.stringify(current)),'completed rematch should remain saveable');
  assert.deepEqual(before.inventory,inventory,'input state must remain immutable');
});
