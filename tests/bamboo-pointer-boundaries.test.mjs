import test from 'node:test';
import assert from 'node:assert/strict';
import {bambooTileFromPointer} from '../src/bamboo-pointer.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

// Test actual rendered-map boundaries, not the surrounding letterboxed canvas.
test('pointer respects inclusive top-left and exclusive right-bottom map bounds under CSS scaling', () => {
 const width=1200,height=360;
 const rect={left:37,top:51,width:600,height:180};
 const cell=Math.min(width/BAMBOO_PASS.width,height/BAMBOO_PASS.height);
 const ox=(width-cell*BAMBOO_PASS.width)/2;
 const oy=(height-cell*BAMBOO_PASS.height)/2;
 const point=(px,py)=>[
  rect.left+px*rect.width/width,
  rect.top+py*rect.height/height
 ];
 const at=(px,py)=>bambooTileFromPointer(...point(px,py),rect,width,height);
 assert.deepEqual(at(ox,oy),{x:0,y:0});
 assert.deepEqual(at(ox+cell*.5,oy+cell*.5),{x:0,y:0});
 assert.deepEqual(at(ox+(BAMBOO_PASS.width-.5)*cell,oy+(BAMBOO_PASS.height-.5)*cell),
  {x:BAMBOO_PASS.width-1,y:BAMBOO_PASS.height-1});
 assert.equal(at(ox-cell*.5,oy+cell*.5),null);
 assert.equal(at(ox+cell*.5,oy-cell*.5),null);
 assert.equal(at(ox+BAMBOO_PASS.width*cell,oy+cell*.5),null);
 assert.equal(at(ox+cell*.5,oy+BAMBOO_PASS.height*cell),null);
});
