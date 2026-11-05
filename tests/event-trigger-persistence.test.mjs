import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent} from '../src/event-trigger.js';

// Original demonstration data only; not extracted from the protected SWF.
const event = {
  id: 'demo_save_reward',
  condition: {path: ['quest'], op: 'eq', value: 'active'},
  effects: [
    {path: ['quest'], value: 'done'},
    {path: ['inventory', 'herbs'], value: 2}
  ]
};
const initial = () => ({quest: 'active', inventory: {herbs: 0}});

test('event history survives JSON save/load and prevents replay', () => {
  const first = triggerEvent(event, initial());
  assert.equal(first.applied, true);
  const loaded = JSON.parse(JSON.stringify(first.state));
  const replay = triggerEvent(event, loaded);
  assert.equal(replay.applied, false);
  assert.deepEqual(replay.state, loaded);
  assert.equal(loaded.inventory.herbs, 2);
});

test('independent event IDs remain separately replay protected after reload', () => {
  const first = triggerEvent(event, initial());
  const loaded = JSON.parse(JSON.stringify(first.state));
  const next = {
    ...event,
    id: 'demo_followup',
    condition: {path: ['quest'], op: 'eq', value: 'done'},
    effects: [{path: ['inventory', 'herbs'], value: 3}]
  };
  const second = triggerEvent(next, loaded);
  assert.equal(second.applied, true);
  assert.equal(second.state.inventory.herbs, 3);
  assert.equal(triggerEvent(event, second.state).applied, false);
  assert.equal(triggerEvent(next, second.state).applied, false);
});

test('invalid nested destination does not write any earlier effect or history', () => {
  const broken = {...event, effects: [
    {path: ['quest'], value: 'done'},
    {path: ['inventory', 'missing', 'value'], value: 2}
  ]};
  const before = initial();
  const result = triggerEvent(broken, before);
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.deepEqual(before, initial());
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});
