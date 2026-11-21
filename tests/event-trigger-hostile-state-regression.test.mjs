import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent} from '../src/event-trigger.js';

// Original demo-only event; not a verified source-SWF story event.
const event = {
  id:'demo_once',
  condition:{path:['quest'],op:'eq',value:'active'},
  effects:[{path:['quest'],value:'done'},{path:['flags','rewarded'],value:true}]
};
const fresh = () => ({quest:'active',flags:{rewarded:false}});

test('hostile event-history getters reject without applying rewards', () => {
  const state=fresh();
  Object.defineProperty(state,'eventHistory',{enumerable:true,get(){throw Error('corrupt save');}});
  const result=triggerEvent(event,state);
  assert.equal(result.applied,false);
  assert.equal(result.state,state);
  assert.equal(state.quest,'active');
  assert.equal(state.flags.rewarded,false);
});

test('inherited event history cannot impersonate a completed event', () => {
  const state=fresh();
  state.eventHistory=Object.create({demo_once:true});
  const result=triggerEvent(event,state);
  assert.equal(result.applied,false);
  assert.equal(result.state,state);
  assert.equal(state.quest,'active');
});

test('malformed replay histories reject without mutation', () => {
  for (const history of [[],null,{demo_once:false},{other:1},new Date(0)]) {
    const state={...fresh(),eventHistory:history};
    const result=triggerEvent(event,state);
    assert.equal(result.applied,false);
    assert.equal(result.state,state);
    assert.equal(state.flags.rewarded,false);
  }
});

test('a valid event applies once even with null-prototype history', () => {
  const state={...fresh(),eventHistory:Object.create(null)};
  const first=triggerEvent(event,state);
  assert.equal(first.applied,true);
  assert.equal(first.state.flags.rewarded,true);
  assert.equal(state.flags.rewarded,false);
  const second=triggerEvent(event,first.state);
  assert.equal(second.applied,false);
  assert.equal(second.state,first.state);
});
