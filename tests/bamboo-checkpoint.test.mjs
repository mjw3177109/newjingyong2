import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeBambooCheckpoint} from '../src/bamboo-checkpoint.js';

test('accepts a legal bamboo position without sharing mutable input',()=>{
 const input={regionId:'bamboo-pass',position:{x:1,y:4}};
 const result=normalizeBambooCheckpoint(input);
 assert.deepEqual(result,input);
 assert.notStrictEqual(result,input);
 assert.notStrictEqual(result.position,input.position);
});
test('rejects blocked, occupied and out-of-range positions',()=>{
 for(const [x,y] of [[4,1],[6,3],[-1,4],[12,4],[1,9],[1.5,4],[Infinity,4],[NaN,4]]){
  assert.equal(normalizeBambooCheckpoint({regionId:'bamboo-pass',position:{x,y}}),null);
 }
});
test('rejects forged region, prototype-adjacent and extra schema fields',()=>{
 for(const value of [null,[],{}, {regionId:'unknown',position:{x:1,y:4}},
  {regionId:'bamboo-pass',position:{x:1,y:4,z:0}},
  {regionId:'bamboo-pass',position:{x:1,y:4},game:{}},
  {regionId:'bamboo-pass',position:{x:'1',y:4}}]){
  assert.equal(normalizeBambooCheckpoint(value),null);
 }
});
