import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,parseSave} from '../src/engine.js';
import {encodeCheckpoint,decodeCheckpoint} from '../src/browser-checkpoint.js';

test('legacy strict v2 checkpoint upgrades in memory without changing game schema',()=>{
 const game=initialState();
 const result=decodeCheckpoint(JSON.stringify(game));
 assert.deepEqual(result,{game,eventHistory:{}});
 assert.ok(parseSave(JSON.stringify(result.game)));
 assert.equal(Object.hasOwn(result.game,'eventHistory'),false);
});
test('event envelope retains replay history across browser checkpoint round trip',()=>{
 const game=initialState(),history={demo_accept:true};
 const raw=encodeCheckpoint(game,history);
 assert.ok(raw);
 assert.deepEqual(decodeCheckpoint(raw),{game,eventHistory:history});
});
test('invalid envelope never silently downgrades to a legacy save',()=>{
 const game=initialState();
 assert.equal(decodeCheckpoint(JSON.stringify({format:'demo-event-envelope',version:2,game,eventHistory:{}})),null);
 assert.equal(decodeCheckpoint(JSON.stringify({...game,eventHistory:{demo_accept:true}})),null);
 assert.equal(decodeCheckpoint(JSON.stringify({...game,format:'legacy'})),null);
});
test('reject malformed and non-string checkpoints',()=>{
 assert.equal(decodeCheckpoint('{'),null);
 assert.equal(decodeCheckpoint(null),null);
 assert.equal(decodeCheckpoint('[]'),null);
 assert.equal(encodeCheckpoint({...initialState(),extra:1}),null);
});
