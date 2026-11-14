import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,parseSave} from '../src/engine.js';
import {packEventSave,unpackEventSave,applySavedEvent} from '../src/event-save-adapter.js';

const demoEvent = {
  id:'demo_accept',
  condition:{path:['quest'],op:'eq',value:'unstarted'},
  effects:[{path:['quest'],value:'active'}]
};

test('envelope round trip keeps strict v2 game save valid', () => {
  const game=initialState();
  const raw=packEventSave(game);
  assert.ok(raw);
  const restored=unpackEventSave(raw);
  assert.deepEqual(restored.game,game);
  assert.deepEqual(restored.eventHistory,{});
  assert.ok(parseSave(JSON.stringify(restored.game)));
  assert.equal(Object.hasOwn(restored.game,'eventHistory'),false);
});

test('event survives envelope save/reload without replay', () => {
  const first=applySavedEvent(demoEvent,initialState());
  assert.equal(first.applied,true);
  assert.equal(first.game.quest,'active');
  const restored=unpackEventSave(packEventSave(first.game,first.eventHistory));
  assert.ok(restored);
  const replay=applySavedEvent(demoEvent,restored.game,restored.eventHistory);
  assert.equal(replay.applied,false);
  assert.equal(replay.game.quest,'active');
  assert.equal(replay.eventHistory.demo_accept,true);
});

test('reject event effect that would violate strict v2 quest invariants', () => {
  const invalid={...demoEvent,effects:[{path:['quest'],value:'completed'}]};
  const before=initialState();
  const result=applySavedEvent(invalid,before);
  assert.equal(result.applied,false);
  assert.deepEqual(result.game,before);
  assert.deepEqual(result.eventHistory,{});
});

test('reject unknown envelope fields and unsafe replay keys', () => {
  const game=initialState();
  assert.equal(unpackEventSave(JSON.stringify({format:'demo-event-envelope',version:1,game,eventHistory:{},extra:true})),null);
  assert.equal(unpackEventSave(JSON.stringify({format:'demo-event-envelope',version:1,game,eventHistory:JSON.parse('{"__proto__":true}')})),null);
  assert.equal(packEventSave({...game,unknown:1}),null);
});


test('unserializable game state fails closed without throwing', () => {
  const circular = initialState();
  circular.loop = circular;
  assert.equal(packEventSave(circular), null);
  const getter = initialState();
  Object.defineProperty(getter, 'quest', {enumerable:true, get(){throw new Error('bad getter');}});
  assert.equal(packEventSave(getter), null);
  const result = applySavedEvent(demoEvent, getter);
  assert.equal(result.applied, false);
  assert.equal(result.game, getter);
});
