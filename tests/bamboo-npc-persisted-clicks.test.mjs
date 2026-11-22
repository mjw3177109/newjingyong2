import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {routeToRegionNpc} from '../src/region-npc-route.js';
import {moveBambooSession,talkBambooSession} from '../src/region-travel.js';
import {saveBambooSession,loadBambooSession} from '../src/bamboo-session-storage.js';

// Reproduce the browser handler's one-step-per-click and write/readback gate.
// This is a Node integration test, not a Chromium mouse-event test.
function memoryStorage() {
 const values=new Map();
 return {
  getItem:k=>values.has(k)?values.get(k):null,
  setItem:(k,v)=>values.set(k,String(v)),
  removeItem:k=>values.delete(k)
 };
}
test('every reachable start can approach NPC via repeated persisted clicks',()=>{
 const region=BAMBOO_PASS;
 let checked=0;
 for(let y=0;y<region.height;y++)for(let x=0;x<region.width;x++){
  const initial={x,y};
  if(routeToRegionNpc(region,initial)===null)continue;
  const storage=memoryStorage();
  let session={regionId:region.id,position:initial};
  assert.equal(saveBambooSession(storage,session),true);
  for(let clicks=0;clicks<=region.width*region.height;clicks++){
   const route=routeToRegionNpc(region,session.position);
   assert.notEqual(route,null);
   if(route.length===0)break;
   assert.ok(clicks<region.width*region.height,'must terminate');
   const first=route[0];
   const moved=moveBambooSession(session,first.x-session.position.x,first.y-session.position.y);
   assert.ok(moved,'step is legal');
   assert.equal(saveBambooSession(storage,moved),true,'step persisted');
   session=loadBambooSession(storage);
   assert.deepEqual(session,moved,'readback agrees with UI state');
  }
  assert.deepEqual(routeToRegionNpc(region,session.position),[]);
  assert.equal(talkBambooSession(session)?.npcId,region.npc.id);
  checked++;
 }
 assert.ok(checked>0);
});
test('failed persistence does not authorize advancing the visible session',()=>{
 const storage=memoryStorage();
 let session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
 assert.equal(saveBambooSession(storage,session),true);
 const before=loadBambooSession(storage);
 const route=routeToRegionNpc(BAMBOO_PASS,session.position);
 assert.ok(route?.length);
 const first=route[0];
 const moved=moveBambooSession(session,first.x-session.position.x,first.y-session.position.y);
 assert.ok(moved);
 const failing={getItem:k=>storage.getItem(k),setItem(){throw Error('quota');}};
 assert.equal(saveBambooSession(failing,moved),false);
 assert.deepEqual(loadBambooSession(storage),before);
 // Mirror the browser's commit-on-success rule: session is not replaced.
 assert.deepEqual(session,before);
});
