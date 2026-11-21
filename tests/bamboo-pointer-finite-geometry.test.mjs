import test from 'node:test';
import assert from 'node:assert/strict';
import {bambooTileFromPointer} from '../src/bamboo-pointer.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

// A corrupted canvas or DOM rectangle must not create a bogus movement target.
test('bamboo pointer rejects non-finite geometry without throwing',()=>{
 const rect={left:10,top:20,width:900,height:540};
 const valid=bambooTileFromPointer(460,290,rect,900,540);
 assert.ok(valid);
 for(const value of [NaN,Infinity,-Infinity]){
  for(const key of ['left','top','width','height']){
   assert.equal(bambooTileFromPointer(460,290,{...rect,[key]:value},900,540),null,key);
  }
  assert.equal(bambooTileFromPointer(460,290,rect,value,540),null);
  assert.equal(bambooTileFromPointer(460,290,rect,900,value),null);
 }
 for(const key of ['width','height']){
  assert.equal(bambooTileFromPointer(460,290,{...rect,[key]:0},900,540),null);
 }
 assert.equal(bambooTileFromPointer(460,290,{...rect,left:undefined},900,540),null);
});
test('bamboo pointer maps the centered entry tile under CSS scaling',()=>{
 const width=1200,height=360,rect={left:50,top:80,width:600,height:180};
 const cell=Math.min(width/BAMBOO_PASS.width,height/BAMBOO_PASS.height);
 const ox=(width-cell*BAMBOO_PASS.width)/2,oy=(height-cell*BAMBOO_PASS.height)/2;
 const {x,y}=BAMBOO_PASS.entry;
 const clientX=rect.left+(ox+(x+.5)*cell)*rect.width/width;
 const clientY=rect.top+(oy+(y+.5)*cell)*rect.height/height;
 assert.deepEqual(bambooTileFromPointer(clientX,clientY,rect,width,height),{x,y});
});
