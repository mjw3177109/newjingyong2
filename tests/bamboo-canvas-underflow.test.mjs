import test from 'node:test';
import assert from 'node:assert/strict';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

test('subnormal canvas dimensions do not draw zero-sized tiles',()=>{
 let draws=0;
 const ctx=new Proxy({}, {get(target,key){if(key==='fillRect')return ()=>{draws++};return ()=>{}},set(target,key,value){target[key]=value;return true}});
 const session={regionId:BAMBOO_PASS.id,position:{x:0,y:0}};
 assert.equal(drawBambooPass(ctx,session,Number.MIN_VALUE,Number.MIN_VALUE),false);
 assert.equal(draws,0);
});
