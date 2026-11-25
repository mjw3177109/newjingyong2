import test from 'node:test';
import assert from 'node:assert/strict';
import { BAMBOO_PASS, validateRegion } from '../src/bamboo-pass.js';
import { shortestRegionRoute } from '../src/region-navigation.js';
import { routeToRegionNpc } from '../src/region-npc-route.js';

function reference(region,start) {
  let best=null;
  for(const [dx,dy] of [[0,-1],[-1,0],[1,0],[0,1]]) {
    const route=shortestRegionRoute(region,start,{x:region.npc.x+dx,y:region.npc.y+dy});
    if(route!==null && (best===null || route.length<best.length)) best=route;
  }
  return best;
}
test('NPC route matches independent searches for every bamboo tile',()=>{
  for(let y=-1;y<=BAMBOO_PASS.height;y++) for(let x=-1;x<=BAMBOO_PASS.width;x++)
    assert.deepEqual(routeToRegionNpc(BAMBOO_PASS,{x,y}),reference(BAMBOO_PASS,{x,y}));
});
test('NPC route preserves exact paths on deterministic obstacle layouts',()=>{
  let valid=0;
  for(let mask=0;mask<256;mask++){
    const region={...BAMBOO_PASS,width:5,height:5,entry:{x:0,y:0},exit:{x:4,y:4},npc:{...BAMBOO_PASS.npc,x:2,y:2},blocks:['1,0','0,1','2,1','1,2','3,2','2,3','3,4','4,3'].filter((_,i)=>mask&(1<<i))};
    if(!validateRegion(region)) continue;
    valid++;
    for(let y=0;y<5;y++) for(let x=0;x<5;x++)
      assert.deepEqual(routeToRegionNpc(region,{x,y}),reference(region,{x,y}), 'mask='+mask+' start='+x+','+y);
  }
  assert.ok(valid>0);
});
