import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent} from '../src/event-trigger.js';

// Original demo event only; these cases do not assert source-SWF story semantics.
const event = {
  id: 'demo_safe_commit',
  condition: {path:['quest'],op:'eq',value:'active'},
  effects: [{path:['quest'],value:'done'},{path:['flags','rewarded'],value:true}]
};
const fresh = () => ({quest:'active',flags:{rewarded:false},eventHistory:{}});

test('throwing nested getter rejects before applying either effect', () => {
  const state=fresh();
  Object.defineProperty(state,'flags',{enumerable:true,get(){throw Error('bad nested state');}});
  const result=triggerEvent(event,state);
  assert.equal(result.applied,false);
  assert.equal(result.state,state);
  assert.equal(state.quest,'active');
  assert.deepEqual(state.eventHistory,{});
});

test('uncloneable unrelated state rejects atomically without a reward', () => {
  const state={...fresh(),callback:()=>{}};
  const result=triggerEvent(event,state);
  assert.equal(result.applied,false);
  assert.equal(result.state,state);
  assert.equal(state.quest,'active');
  assert.equal(state.flags.rewarded,false);
  assert.deepEqual(state.eventHistory,{});
});

test('unmet condition never applies effects or records history', () => {
  const state={...fresh(),quest:'not_started'};
  const result=triggerEvent(event,state);
  assert.equal(result.applied,false);
  assert.equal(result.state,state);
  assert.equal(state.flags.rewarded,false);
  assert.deepEqual(state.eventHistory,{});
});
