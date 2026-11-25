import test from 'node:test';
import assert from 'node:assert/strict';
import {bambooTileFromPointer} from '../src/bamboo-pointer.js';
const rect={left:10,top:20,width:900,height:540};
test('centered 12x9 grid rejects left and right letterbox margins',()=>{
 assert.equal(bambooTileFromPointer(40,290,rect,900,540),null);
 assert.equal(bambooTileFromPointer(880,290,rect,900,540),null);
 assert.deepEqual(bambooTileFromPointer(100,50,rect,900,540),{x:0,y:0});
 assert.deepEqual(bambooTileFromPointer(819,559,rect,900,540),{x:11,y:8});
});
test('CSS-scaled canvas maps the same tiles and rejects outside pointer',()=>{
 const scaled={left:5,top:8,width:450,height:270};
 assert.deepEqual(bambooTileFromPointer(55,33,scaled,900,540),{x:0,y:0});
 assert.equal(bambooTileFromPointer(6,100,scaled,900,540),null);
 assert.equal(bambooTileFromPointer(460,100,scaled,900,540),null);
 assert.equal(bambooTileFromPointer(100,100,{...scaled,width:0},900,540),null);
});
