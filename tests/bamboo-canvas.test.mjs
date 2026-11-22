import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {pathToBambooExit} from '../src/bamboo-exit-path.js';
import {drawBambooPass} from '../src/bamboo-canvas.js';
import {enterBambooPass,moveBambooSession} from '../src/region-travel.js';
import {initialState} from '../src/engine.js';
import {VILLAGE_GATE} from '../src/region-travel.js';

function fakeCanvas(){
 const calls=[];
 const ctx={fillRect:(...v)=>calls.push(['fillRect',...v]),strokeRect:(...v)=>calls.push(['strokeRect',...v]),beginPath:()=>{},arc:(...v)=>calls.push(['arc',...v]),fill:()=>{},fillText:(...v)=>calls.push(['text',...v])};
 return {ctx,calls};
}
test('renderer rejects missing or unrelated session',()=>{
 const {ctx,calls}=fakeCanvas();
 assert.equal(drawBambooPass(ctx,null),false);
 assert.equal(drawBambooPass(ctx,{regionId:'village'}),false);
 assert.equal(calls.length,0);
});
test('original bamboo pass draws all tiles and markers without external image assets',()=>{
 const {ctx,calls}=fakeCanvas();
 assert.equal(drawBambooPass(ctx,{regionId:BAMBOO_PASS.id,position:BAMBOO_PASS.entry}),true);
 assert.equal(calls.filter(c=>c[0]==='strokeRect').length,BAMBOO_PASS.width*BAMBOO_PASS.height);
 assert.ok(calls.some(c=>c[0]==='text'&&c[1]===BAMBOO_PASS.name));
});
test('browser entry gate uses the existing legal village position',()=>{
 const game=initialState();
 game.player={...game.player,...VILLAGE_GATE};
 const session=enterBambooPass(game);
 assert.ok(session);
 assert.equal(moveBambooSession(session,1,0)?.position.x,2);
});

test('bamboo canvas shows one breadcrumb per legal remaining exit step',()=>{
 const {ctx,calls}=fakeCanvas();
 const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 const route=pathToBambooExit(session);
 assert.ok(route?.length>0);
 assert.equal(drawBambooPass(ctx,session),true);
 // Exit, keeper and hero markers are three additional circles.
 assert.equal(calls.filter(c=>c[0]==='arc').length,route.length+3);
 // Breadcrumb geometry must match each legal path cell, not merely its count.
 const cell=Math.min(900/BAMBOO_PASS.width,540/BAMBOO_PASS.height);
 const ox=(900-cell*BAMBOO_PASS.width)/2;
 const oy=(540-cell*BAMBOO_PASS.height)/2;
 const circles=calls.filter(c=>c[0]==='arc');
 for(let i=0;i<route.length;i++){
  const [,x,y,radius]=circles[i];
  assert.ok(Math.abs(x-(ox+(route[i].x+.5)*cell))<1e-8);
  assert.ok(Math.abs(y-(oy+(route[i].y+.5)*cell))<1e-8);
  assert.ok(Math.abs(radius-cell*.085)<1e-8);
 }
 const atExit={...session,position:{...BAMBOO_PASS.exit}};
 const finished=fakeCanvas();
 assert.deepEqual(pathToBambooExit(atExit),[]);
 assert.equal(drawBambooPass(finished.ctx,atExit),true);
 assert.equal(finished.calls.filter(c=>c[0]==='arc').length,3);
});

test('breadcrumb route updates after a legal step and never draws the old starting tile',()=>{
 const start={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 const route=pathToBambooExit(start);
 assert.ok(route?.length>1);
 const next={...start,position:{...route[0]}};
 const remaining=pathToBambooExit(next);
 assert.ok(remaining);
 assert.equal(remaining.length,route.length-1);
 assert.deepEqual(remaining,route.slice(1));
 const {ctx,calls}=fakeCanvas();
 assert.equal(drawBambooPass(ctx,next),true);
 const arcs=calls.filter(c=>c[0]==='arc');
 assert.equal(arcs.length,remaining.length+3);
 const cell=Math.min(900/BAMBOO_PASS.width,540/BAMBOO_PASS.height);
 const ox=(900-cell*BAMBOO_PASS.width)/2;
 const oy=(540-cell*BAMBOO_PASS.height)/2;
 for(let i=0;i<remaining.length;i++){
  assert.ok(Math.abs(arcs[i][1]-(ox+(remaining[i].x+.5)*cell))<1e-8);
  assert.ok(Math.abs(arcs[i][2]-(oy+(remaining[i].y+.5)*cell))<1e-8);
 }
});

test('canvas announces remaining exit steps and arrival without stale distance',()=>{
 const start={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 const route=pathToBambooExit(start);
 assert.ok(route?.length>0);
 const before=fakeCanvas();
 assert.equal(drawBambooPass(before.ctx,start),true);
 assert.ok(before.calls.some(c=>c[0]==='text'&&c[1]===`距出口 ${route.length} 步`));
 const moved=fakeCanvas();
 assert.equal(drawBambooPass(moved.ctx,{...start,position:{...route[0]}}),true);
 assert.ok(moved.calls.some(c=>c[0]==='text'&&c[1]===`距出口 ${route.length-1} 步`));
 const arrived=fakeCanvas();
 assert.equal(drawBambooPass(arrived.ctx,{...start,position:{...BAMBOO_PASS.exit}}),true);
 assert.ok(arrived.calls.some(c=>c[0]==='text'&&c[1]==='已到出口 · 按 E 返回'));
});


test('canvas next-step hint follows the actual route and disappears at the exit',()=>{
 const start={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 const route=pathToBambooExit(start);
 assert.ok(route?.length>0);
 const first=route[0],dx=first.x-start.position.x,dy=first.y-start.position.y;
 const direction=dx===1?'右':dx===-1?'左':dy===1?'下':dy===-1?'上':null;
 assert.ok(direction,'first step must be adjacent');
 const before=fakeCanvas();
 assert.equal(drawBambooPass(before.ctx,start),true);
 assert.ok(before.calls.some(c=>c[0]==='text'&&c[1]===`下一步：${direction}`));
 const arrived=fakeCanvas();
 assert.equal(drawBambooPass(arrived.ctx,{...start,position:{...BAMBOO_PASS.exit}}),true);
 assert.equal(arrived.calls.some(c=>c[0]==='text'&&String(c[1]).startsWith('下一步：')),false);
});
