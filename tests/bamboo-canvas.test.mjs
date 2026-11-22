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
 const atExit={...session,position:{...BAMBOO_PASS.exit}};
 const finished=fakeCanvas();
 assert.deepEqual(pathToBambooExit(atExit),[]);
 assert.equal(drawBambooPass(finished.ctx,atExit),true);
 assert.equal(finished.calls.filter(c=>c[0]==='arc').length,3);
});
