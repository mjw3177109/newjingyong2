import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {routeToRegionNpc} from '../src/region-npc-route.js';
import {moveBambooSession,talkBambooSession} from '../src/region-travel.js';

// Reproduce the Canvas click handler's one-step-per-click behavior using
// production route and session APIs; this is not a browser event test.
test('repeated NPC clicks approach the keeper without skipping persistence steps',()=>{
  let session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
  const visited=new Set([session.position.x+','+session.position.y]);
  let clicks=0;
  while(clicks< BAMBOO_PASS.width*BAMBOO_PASS.height){
    const route=routeToRegionNpc(BAMBOO_PASS,session.position);
    assert.ok(route!==null,'keeper remains reachable');
    if(route.length===0)break;
    const next=route[0];
    const moved=moveBambooSession(session,next.x-session.position.x,next.y-session.position.y);
    assert.ok(moved,'every click must make one legal move');
    assert.deepEqual(moved.position,next);
    assert.notDeepEqual(next,{x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y});
    session=moved;
    visited.add(next.x+','+next.y);
    clicks++;
  }
  assert.ok(clicks>0 && clicks<BAMBOO_PASS.width*BAMBOO_PASS.height);
  assert.deepEqual(routeToRegionNpc(BAMBOO_PASS,session.position),[]);
  assert.equal(talkBambooSession(session)?.npcId,BAMBOO_PASS.npc.id);
  assert.ok(visited.size>1);
});
