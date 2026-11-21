import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {routeToRegionNpc} from '../src/region-npc-route.js';
import {moveBambooSession,talkBambooSession} from '../src/region-travel.js';

// Original demo only. Exhaustive route-to-interaction verification across the
// map, not evidence of any jin.swf NPC or story condition.
test('every reachable bamboo tile can approach the keeper by legal moves',()=>{
 const region=BAMBOO_PASS;
 let checked=0;
 for(let y=0;y<region.height;y++)for(let x=0;x<region.width;x++){
  const origin={x,y};
  const route=routeToRegionNpc(region,origin);
  if(route===null)continue; // blocked, occupied or disconnected tile
  let session={regionId:region.id,position:{...origin}};
  const seen=new Set([x+','+y]);
  assert.ok(route.length<=region.width*region.height,'route is bounded');
  for(const step of route){
   const dx=step.x-session.position.x,dy=step.y-session.position.y;
   assert.equal(Math.abs(dx)+Math.abs(dy),1,'one orthogonal step');
   assert.notDeepEqual(step,{x:region.npc.x,y:region.npc.y},'never enter NPC tile');
   assert.ok(!seen.has(step.x+','+step.y),'shortest path has no cycles');
   seen.add(step.x+','+step.y);
   const next=moveBambooSession(session,dx,dy);
   assert.ok(next,'every planned step must be executable');
   assert.deepEqual(next.position,step);
   session=next;
  }
  assert.deepEqual(routeToRegionNpc(region,session.position),[],'arrived within dialogue range');
  assert.equal(talkBambooSession(session)?.npcId,region.npc.id,'NPC can be talked to');
  checked++;
 }
 assert.ok(checked>0,'at least one reachable start');
});
