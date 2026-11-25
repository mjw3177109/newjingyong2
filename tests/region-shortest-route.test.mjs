import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {shortestRegionRoute,stepInRegion} from '../src/region-navigation.js';

test('shortest route reaches the original demo exit using only legal steps',()=>{
 const start={...BAMBOO_PASS.entry};
 const route=shortestRegionRoute(BAMBOO_PASS,start);
 assert.ok(Array.isArray(route)&&route.length>0);
 let current=start;
 for(const next of route){
   assert.deepEqual(stepInRegion(BAMBOO_PASS,current,next.x-current.x,next.y-current.y),next);
   current=next;
 }
 assert.deepEqual(current,BAMBOO_PASS.exit);
 // Manhattan distance is a lower bound for any walkable route.
 assert.ok(route.length>=Math.abs(start.x-current.x)+Math.abs(start.y-current.y));
});

test('route is empty at target, and rejects blocked, NPC and invalid positions',()=>{
 assert.deepEqual(shortestRegionRoute(BAMBOO_PASS,BAMBOO_PASS.exit),[]);
 assert.equal(shortestRegionRoute(BAMBOO_PASS,{x:4,y:2}),null);
 assert.equal(shortestRegionRoute(BAMBOO_PASS,BAMBOO_PASS.entry,BAMBOO_PASS.npc),null);
 assert.equal(shortestRegionRoute(BAMBOO_PASS,{x:-1,y:0}),null);
 assert.equal(shortestRegionRoute(BAMBOO_PASS,BAMBOO_PASS.entry,{x:99,y:0}),null);
});

test('detour finds shortest route around an obstacle',()=>{
 const region={...BAMBOO_PASS,width:5,height:5,entry:{x:0,y:2},exit:{x:4,y:2},
   npc:{id:'guard',name:'守卫',dialog:'你好',x:4,y:4},blocks:['2,1','2,2','2,3']};
 const route=shortestRegionRoute(region,region.entry);
 assert.equal(route.length,8);
 assert.deepEqual(route.at(-1),region.exit);
});
