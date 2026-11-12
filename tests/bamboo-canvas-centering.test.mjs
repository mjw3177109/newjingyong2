import test from 'node:test';
import assert from 'node:assert/strict';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';

// Regression: canvas rendering must agree with centered hit-testing for
// wide and tall viewports. All geometry is original demo content.
for(const [width,height] of [[900,540],[1200,360],[360,900]]){
 test(`bamboo markers remain centered in ${width}x${height} canvas`,()=>{
  const arcs=[];
  const ctx={
   fillRect(){},strokeRect(){},beginPath(){},fill(){},fillText(){},
   arc(...args){arcs.push(args);}
  };
  const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
  assert.equal(drawBambooPass(ctx,session,width,height),true);
  assert.equal(arcs.length,3);
  const cell=Math.min(width/BAMBOO_PASS.width,height/BAMBOO_PASS.height);
  const ox=(width-cell*BAMBOO_PASS.width)/2;
  const oy=(height-cell*BAMBOO_PASS.height)/2;
  const expected=[BAMBOO_PASS.exit,BAMBOO_PASS.npc,BAMBOO_PASS.entry];
  expected.forEach((point,index)=>{
   assert.ok(Math.abs(arcs[index][0]-(ox+(point.x+.5)*cell))<1e-9);
   assert.ok(Math.abs(arcs[index][1]-(oy+(point.y+.5)*cell))<1e-9);
   assert.ok(arcs[index][2]>0);
  });
 });
}
