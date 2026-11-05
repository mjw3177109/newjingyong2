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

test('overlapping effect paths fail atomically instead of throwing', () => {
  const before = initial();
  const overlap = {...event, effects: [
    {path: ['inventory'], value: 'replaced'},
    {path: ['inventory', 'herbs'], value: 5}
  ]};
  assert.doesNotThrow(() => triggerEvent(overlap, before));
  const result = triggerEvent(overlap, before);
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.deepEqual(before, initial());
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});

test('duplicate destination paths are rejected before state mutation', () => {
  const before = initial();
  const duplicate = {...event, effects: [
    {path: ['quest'], value: 'done'},
    {path: ['quest'], value: 'overwritten'}
  ]};
  const result = triggerEvent(duplicate, before);
  assert.equal(result.applied, false);
  assert.deepEqual(before, initial());
});


test('uncloneable imported state fails without throwing or partially applying effects', () => {
  const before = {...initial(), legacyCallback: () => 'not serializable'};
  let result;
  assert.doesNotThrow(() => { result = triggerEvent(event, before); });
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.equal(before.quest, 'active');
  assert.equal(before.inventory.herbs, 0);
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});


test('malformed imported event history is rejected without reward mutation', () => {
  for (const eventHistory of [new Date('2020-01-01'), {old_event: false}, {old_event: 1}]) {
    const before = {...initial(), eventHistory};
    const result = triggerEvent(event, before);
    assert.equal(result.applied, false);
    assert.equal(result.state, before);
    assert.equal(before.quest, 'active');
    assert.equal(before.inventory.herbs, 0);
  }
});

test('unsafe or malformed imported history keys are rejected atomically', () => {
  for (const key of ['__proto__', 'constructor', 'prototype', 'bad.key', '1invalid']) {
    const history = JSON.parse('{"' + key + '":true}');
    const before = {...initial(), eventHistory: history};
    const result = triggerEvent(event, before);
    assert.equal(result.applied, false, key);
    assert.equal(result.state, before, key);
    assert.equal(before.inventory.herbs, 0, key);
    assert.equal(before.quest, 'active', key);
  }
});

test('unknown final destination is rejected without creating state fields', () => {
  const before = initial();
  const unknown = {...event, effects: [
    {path: ['quest'], value: 'done'},
    {path: ['inventory', 'unverifiedReward'], value: 99}
  ]};
  const result = triggerEvent(unknown, before);
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.deepEqual(before, initial());
  assert.equal(Object.hasOwn(before.inventory, 'unverifiedReward'), false);
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});

test('existing final destination still accepts a valid event transaction', () => {
  const before = initial();
  const result = triggerEvent(event, before);
  assert.equal(result.applied, true);
  assert.equal(result.state.quest, 'done');
  assert.equal(result.state.inventory.herbs, 2);
  assert.equal(result.state.eventHistory.demo_save_reward, true);
  assert.deepEqual(before, initial());
});

test('throwing legacy condition accessor is rejected without mutating rewards', () => {
  const before = initial();
  Object.defineProperty(before, 'quest', {
    enumerable: true, configurable: true,
    get() { throw new Error('legacy accessor'); }
  });
  let result;
  assert.doesNotThrow(() => { result = triggerEvent(event, before); });
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.equal(before.inventory.herbs, 0);
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});

test('throwing imported event history getter is rejected without reward mutation', () => {
  const before = initial();
  Object.defineProperty(before, 'eventHistory', {
    enumerable: true, configurable: true,
    get() { throw new Error('invalid legacy history'); }
  });
  let result;
  assert.doesNotThrow(() => { result = triggerEvent(event, before); });
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.equal(before.quest, 'active');
  assert.equal(before.inventory.herbs, 0);
});


test('throwing nested state getter is rejected atomically during preflight', () => {
  const before = initial();
  Object.defineProperty(before.inventory, 'herbs', {
    enumerable: true, configurable: true,
    get() { throw new Error('corrupt imported getter'); }
  });
  let result;
  assert.doesNotThrow(() => { result = triggerEvent(event, before); });
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.equal(before.quest, 'active');
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});

test('throwing nested proxy lookup is rejected without modifying state', () => {
  const before = initial();
  before.inventory = new Proxy(before.inventory, {
    getOwnPropertyDescriptor(target, key) {
      if (key === 'herbs') throw new Error('corrupt imported proxy');
      return Reflect.getOwnPropertyDescriptor(target, key);
    }
  });
  let result;
  assert.doesNotThrow(() => { result = triggerEvent(event, before); });
  assert.equal(result.applied, false);
  assert.equal(result.state, before);
  assert.equal(before.quest, 'active');
  assert.equal(Object.hasOwn(before, 'eventHistory'), false);
});
