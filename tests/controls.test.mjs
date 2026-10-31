import test from 'node:test';
import assert from 'node:assert/strict';
import {commandForKey} from '../src/controls.js';
const event = (key, extras = {}) => ({key, target: {tagName: 'CANVAS'}, ...extras});

test('world movement allows single-step keyboard navigation and intentional held movement', () => {
  assert.deepEqual(commandForKey(event('ArrowLeft')), {kind: 'move', dx: -1, dy: 0});
  assert.deepEqual(commandForKey(event('W', {repeat: true})), {kind: 'move', dx: 0, dy: -1});
  assert.deepEqual(commandForKey(event('d')), {kind: 'move', dx: 1, dy: 0});
});
test('world interaction and consumable shortcuts do not auto-repeat', () => {
  for (const key of ['e', 'Enter', ' ']) assert.deepEqual(commandForKey(event(key)), {kind: 'interact'});
  assert.deepEqual(commandForKey(event('H')), {kind: 'potion'});
  assert.deepEqual(commandForKey(event('b')), {kind: 'inventory'});
  assert.deepEqual(commandForKey(event('j')), {kind: 'quest'});
  for (const key of ['e', 'Enter', ' ', 'h']) assert.equal(commandForKey(event(key, {repeat: true})), null);
});
test('combat shortcuts are exclusive and non-repeating', () => {
  for (const [key, action] of Object.entries({'1': 'attack', '2': 'guard', '3': 'drink', '4': 'flee'}))
    assert.deepEqual(commandForKey(event(key), true), {kind: 'combat', action});
  for (const key of ['ArrowRight', 'e', 'h', '5', '1'])
    assert.equal(commandForKey(event(key, {repeat: key === '1'}), true), null);
  assert.equal(commandForKey(event('1')), null);
});
test('focused buttons, form controls and editable descendants retain native keyboard behavior', () => {
  for (const tagName of ['BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'A'])
    assert.equal(commandForKey(event('Enter', {target: {tagName}})), null);
  assert.equal(commandForKey(event(' ', {target: {isContentEditable: true}})), null);
  assert.equal(commandForKey(event('e', {target: {closest: () => ({tagName: 'BUTTON'})}})), null);
});
test('modifier chords, composition, cancelled and unknown keys are not hijacked', () => {
  for (const extras of [{ctrlKey: true}, {altKey: true}, {metaKey: true}, {isComposing: true}, {defaultPrevented: true}])
    assert.equal(commandForKey(event('e', extras)), null);
  assert.equal(commandForKey(event('Escape')), null);
  assert.equal(commandForKey(event(undefined)), null);
});
