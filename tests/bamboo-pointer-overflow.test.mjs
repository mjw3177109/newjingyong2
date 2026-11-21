import test from 'node:test';
import assert from 'node:assert/strict';
import {bambooTileFromPointer} from '../src/bamboo-pointer.js';

test('pointer rejects overflow produced from individually finite inputs',()=>{
 const rect={left:-1e308,top:0,width:1,height:540};
 assert.equal(bambooTileFromPointer(1e308,270,rect,900,540),null);
});

test('pointer rejects underflowed cell dimensions',()=>{
 const rect={left:0,top:0,width:900,height:540};
 assert.equal(bambooTileFromPointer(450,270,rect,Number.MIN_VALUE,Number.MIN_VALUE),null);
});

test('ordinary centered pointer still maps to a tile',()=>{
 const rect={left:10,top:20,width:900,height:540};
 const tile=bambooTileFromPointer(460,290,rect,900,540);
 assert.ok(tile);
 assert.ok(Number.isSafeInteger(tile.x)&&Number.isSafeInteger(tile.y));
});
