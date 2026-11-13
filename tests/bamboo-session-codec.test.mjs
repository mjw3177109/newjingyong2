import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeBambooSession,decodeBambooSession,MAX_BAMBOO_SESSION_BYTES} from '../src/bamboo-session-codec.js';

test('legal session survives JSON roundtrip without sharing references',()=>{
 const input={regionId:'bamboo-pass',position:{x:1,y:4}};
 const restored=decodeBambooSession(encodeBambooSession(input));
 assert.deepEqual(restored,input);
 assert.notStrictEqual(restored,input);
 assert.notStrictEqual(restored.position,input.position);
});

test('invalid or oversized session payloads are rejected',()=>{
 for(const value of [null,undefined,'','{', 'null', '[]',
  JSON.stringify({regionId:'bamboo-pass',position:{x:4,y:1}}),
  JSON.stringify({regionId:'bamboo-pass',position:{x:1,y:4},extra:true}),
  ' '.repeat(MAX_BAMBOO_SESSION_BYTES+1)]){
  assert.equal(decodeBambooSession(value),null);
 }
 assert.equal(encodeBambooSession({regionId:'bamboo-pass',position:{x:4,y:1}}),null);
});
