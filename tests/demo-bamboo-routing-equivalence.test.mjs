import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {shortestRegionRoute,stepInRegion} from '../src/region-navigation.js';
import {pathToBambooTile} from '../src/bamboo-exit-path.js';

// Original-demo pathfinding equivalence; not evidence of jin.swf maps.
test('click routing and region routing agree on every reachable walkable destination',()=>{
 const start=BAMBOO_PASS.entry;
 const session={regionId:BAMBOO_PASS.id,position:{...start}};
 let checked=0;
 for(let y=0;y<BAMBOO_PASS.height;y++)for(let x=0;x<BAMBOO_PASS.width;x++){
   const destination={x,y};
   const click=pathToBambooTile(session,x,y);
   const route=shortestRegionRoute(BAMBOO_PASS,start,destination);
   if(x===BAMBOO_PASS.npc.x&&y===BAMBOO_PASS.npc.y){
     assert.ok(click,'NPC must be approachable');
     assert.equal(route,null,'NPC tile must remain occupied');
     continue;
   }
   assert.deepEqual(click,route,`routing mismatch at ${x},${y}`);
   if(!click)continue;
   checked++;
   let position={...start};
   for(const tile of click){
     const next=stepInRegion(BAMBOO_PASS,position,tile.x-position.x,tile.y-position.y);
     assert.deepEqual(next,tile,'route must contain legal cardinal steps');
     position=next;
   }
   assert.deepEqual(position,destination);
 }
 assert.ok(checked>0);
 assert.deepEqual(session.position,start,'routing must not mutate checkpoint');
});
