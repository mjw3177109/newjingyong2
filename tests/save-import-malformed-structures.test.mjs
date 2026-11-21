import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, parseSave} from '../src/engine.js';

// Original demo import hardening only; not evidence of recovered SWF rules.
const importValue = value => parseSave(JSON.stringify(value));

test('save import rejects malformed top-level and nested structures without throwing', () => {
  const valid = initialState();
  assert.deepEqual(importValue(valid), valid);
  for (const value of [null, [], true, 3, 'hello', {}, {version:2}]) {
    assert.doesNotThrow(() => importValue(value));
    assert.equal(importValue(value), null);
  }
  for (const [key, value] of [
    ['player', null], ['player', []], ['player', 1],
    ['flags', null], ['flags', []], ['flags', 'yes'],
    ['equipment', null], ['equipment', []], ['equipment', 'sword'],
    ['inventory', null], ['inventory', {}],
    ['journal', null], ['journal', {}],
    ['combat', []], ['combat', 1], ['combat', 'bad']
  ]) {
    const forged = structuredClone(valid);
    forged[key] = value;
    assert.doesNotThrow(() => importValue(forged), key);
    assert.equal(importValue(forged), null, key);
  }
});

test('save import rejects broken JSON and non-finite or fractional player values', () => {
  for (const raw of ['{', 'undefined', '', '{"version":2,']) {
    assert.equal(parseSave(raw), null);
  }
  for (const [key, value] of [
    ['x', 1.5], ['y', -1], ['hp', 0], ['hp', 1.5],
    ['silver', -1], ['silver', 1.5], ['silver', Number.MAX_SAFE_INTEGER]
  ]) {
    const forged = initialState();
    forged.player[key] = value;
    assert.equal(importValue(forged), null, key);
  }
});
