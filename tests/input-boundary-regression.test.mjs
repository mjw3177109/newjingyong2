import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,move,battle,interact,parseSave} from '../src/engine.js';

// Original Q-style demo safety tests, not evidence about jin.swf.
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
test('malformed movement commands cannot teleport or mutate the caller',()=>{
 const start=initialState();
 for(const [dx,dy] of [[0,0],[2,0],[-2,0],[1,1],[0.5,0],[NaN,0],[Infinity,0],['1',0],[null,1]]){
  assert.deepEqual(move(start,dx,dy),start);
 }
 assert.deepEqual(parseSave(JSON.stringify(start)),start);
});
test('invalid combat commands are no-op and survive checkpoint',()=>{
 let s=interact(at(initialState(),7,7));
 s=interact(s); // dismiss elder dialog
 s=interact(at(s,19,8));
 assert.ok(s.combat);
 for(const action of ['unknown','',null,0,{},['attack']]){
  assert.deepEqual(battle(s,action),s);
 }
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});
