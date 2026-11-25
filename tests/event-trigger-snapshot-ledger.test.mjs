import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent} from '../src/event-trigger.js';

// Original demo infrastructure only; no claim about source SWF events.
const event = {
  id:'demo_snapshot_reward',
  condition:{path:['quest'],op:'eq',value:'active'},
  effects:[{path:['quest'],value:'done'},{path:['flags','rewarded'],value:true}]
};

test('event history and rewards commit to one cloned snapshot', () => {
  const state={quest:'active',flags:{rewarded:false},eventHistory:{prior_event:true}};
  const result=triggerEvent(event,state);
  assert.equal(result.applied,true);
  assert.notEqual(result.state,state);
  assert.deepEqual(result.state.eventHistory,{prior_event:true,demo_snapshot_reward:true});
  assert.equal(result.state.quest,'done');
  assert.equal(result.state.flags.rewarded,true);
  assert.deepEqual(state,{quest:'active',flags:{rewarded:false},eventHistory:{prior_event:true}});
  const again=triggerEvent(event,result.state);
  assert.equal(again.applied,false);
  assert.equal(again.state,result.state);
});

test('legacy state without history gets a ledger only on successful clone', () => {
  const state={quest:'active',flags:{rewarded:false}};
  const result=triggerEvent(event,state);
  assert.equal(result.applied,true);
  assert.deepEqual(result.state.eventHistory,{demo_snapshot_reward:true});
  assert.equal(Object.hasOwn(state,'eventHistory'),false);
});
