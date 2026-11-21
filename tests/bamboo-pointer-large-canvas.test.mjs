import test from 'node:test';
import assert from 'node:assert/strict';
import {bambooTileFromPointer} from '../src/bamboo-pointer.js';

test('CSS coordinate mapping avoids intermediate overflow for finite huge canvases',()=>{
 const rect={left:0,top:0,width:120,height:90};
 const tile=bambooTileFromPointer(65,45,rect,1e308,7.5e307);
 assert.deepEqual(tile,{x:6,y:4});
});

test('ordinary CSS-scaled canvas still maps to the same tile',()=>{
 const rect={left:10,top:20,width:120,height:90};
 assert.deepEqual(bambooTileFromPointer(75,65,rect,1200,900),{x:6,y:4});
});
