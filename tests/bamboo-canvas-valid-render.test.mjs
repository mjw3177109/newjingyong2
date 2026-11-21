import test from 'node:test';
import assert from 'node:assert/strict';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

test('valid bamboo session draws centered grid and markers',()=>{
 const calls=[];
 const ctx=new Proxy({},{
  get(_target,key){return (...args)=>calls.push([key,...args]);},
  set(_target,key,value){calls.push(['set',key,value]);return true;}
 });
 const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 assert.equal(drawBambooPass(ctx,session,900,540),true);
 const fills=calls.filter(c=>c[0]==='fillRect');
 const strokes=calls.filter(c=>c[0]==='strokeRect');
 const arcs=calls.filter(c=>c[0]==='arc');
 assert.equal(strokes.length,BAMBOO_PASS.width*BAMBOO_PASS.height);
 assert.ok(fills.length>=1+BAMBOO_PASS.width*BAMBOO_PASS.height);
 assert.equal(arcs.length,3,'exit, NPC, player');
 for(const call of calls){
  if(['fillRect','strokeRect','arc'].includes(call[0])){
   assert.ok(call.slice(1).every(Number.isFinite),JSON.stringify(call));
  }
 }
});

test('wrong region never paints the bamboo canvas',()=>{
 let count=0;
 const ctx=new Proxy({}, {get(){return ()=>{count++;};},set(){count++;return true;}});
 assert.equal(drawBambooPass(ctx,{regionId:'other',position:{...BAMBOO_PASS.entry}},900,540),false);
 assert.equal(count,0);
});
