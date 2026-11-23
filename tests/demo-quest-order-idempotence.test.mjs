import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, DEMO_SWORD} from '../src/engine.js';
import {encodeCheckpoint, decodeCheckpoint} from '../src/browser-checkpoint.js';

// Original demonstration quest; NOT a verified jin.swf storyline.
const at = (s,x,y) => ({...s,player:{...s.player,x,y}});
const close = s => s.dialog ? interact(s) : s;
function reload(s) {
  const raw = encodeCheckpoint(s,{});
  assert.equal(typeof raw,'string');
  const parsed = decodeCheckpoint(raw);
  assert.ok(parsed);
  return parsed.game;
}
function accept(s) { return close(interact(at(s,7,7))); }
function herb(s) { return close(interact(at(s,12,9))); }
function trial(s) {
  s = interact(at(s,19,8));
  assert.ok(s.combat);
  for (let i=0;i<3;i++) s=battle(s,'attack');
  assert.equal(s.flags.banditBeaten,true);
  return close(s);
}
for (const order of ['herb-first','trial-first']) {
  test('demo reward remains single after '+order+' completion and repeated checkpoint reload',()=>{
    let s=accept(initialState());
    s=reload(s);
    s=order==='herb-first' ? herb(s) : trial(s);
    s=reload(s);
    s=order==='herb-first' ? trial(s) : herb(s);
    s=reload(s);
    s=interact(at(s,7,7));
    assert.equal(s.quest,'completed');
    const silver=s.player.silver;
    assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
    for(let i=0;i<5;i++){
      s=reload(close(s));
      s=close(interact(at(s,7,7)));
      assert.equal(s.quest,'completed');
      assert.equal(s.player.silver,silver);
      assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
    }
  });
}
