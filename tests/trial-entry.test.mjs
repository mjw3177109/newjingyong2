import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, parseSave} from '../src/engine.js';

// These rules are original HTML5 demo design, not extracted source-SWF events.
const nearTrial = state => {
  const s=structuredClone(state);
  s.player.x=19;s.player.y=8;
  return s;
};

test('unaccepted trial is gated without combat, reward or flag changes',()=>{
  const before=nearTrial(initialState());
  const next=interact(before);
  assert.equal(next.combat,null);
  assert.equal(next.flags.banditBeaten,false);
  assert.equal(next.quest,'unstarted');
  assert.match(next.dialog,/先去拜访竹隐老人/);
  assert.match(next.journal[0],/未进入战斗/);
  assert.deepEqual(before,nearTrial(initialState()),'interaction must not mutate input');
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
});

test('repeated interaction cannot bypass the trial acceptance gate',()=>{
  let s=nearTrial(initialState());
  s=interact(s);
  s=interact(s); // close dialogue
  assert.equal(s.dialog,'');
  s=interact(s); // still unaccepted
  assert.equal(s.combat,null);
  assert.equal(s.flags.banditBeaten,false);
  assert.match(s.dialog,/先去拜访/);
});

test('accepted quest enters battle, can retreat and save normally',()=>{
  const accepted=initialState();accepted.quest='active';
  const s=nearTrial(accepted);
  const fighting=interact(s);
  assert.ok(fighting.combat);
  assert.equal(fighting.dialog,'');
  assert.deepEqual(parseSave(JSON.stringify(fighting)),fighting);
  const retreated=battle(fighting,'flee');
  assert.equal(retreated.combat,null);
  assert.equal(retreated.quest,'active');
  assert.equal(retreated.flags.banditBeaten,false);
  assert.deepEqual(parseSave(JSON.stringify(retreated)),retreated);
});
