import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {shortestRegionRoute} from '../src/region-navigation.js';
import {enterBambooPass,moveBambooSession,talkBambooSession,leaveBambooPass,VILLAGE_GATE,VILLAGE_RETURN} from '../src/region-travel.js';
import {pathToBambooTile,pathToBambooExit} from '../src/bamboo-exit-path.js';

// Full original-demo region journey, not an extracted jin.swf storyline.
test('village gate -> keeper dialogue -> exit -> village return preserves quest state',()=>{
 const base=initialState();
 const game={...base,player:{...base.player,...VILLAGE_GATE}};
 let session=enterBambooPass(game);
 assert.ok(session,'village gate must enter bamboo pass');
 const npc=BAMBOO_PASS.npc;
 const approach=pathToBambooTile(session,npc.x,npc.y);
 assert.ok(approach?.length,'keeper must be reachable from entry');
 for(const tile of approach){
   const dx=tile.x-session.position.x,dy=tile.y-session.position.y;
   assert.equal(Math.abs(dx)+Math.abs(dy),1);
   session=moveBambooSession(session,dx,dy);
   assert.ok(session,'every planned step must be legal');
 }
 assert.equal(Math.abs(session.position.x-npc.x)+Math.abs(session.position.y-npc.y),1);
 assert.equal(talkBambooSession(session)?.npcId,npc.id);
 assert.equal(leaveBambooPass(session,game),null,'keeper tile must not exit');
 const route=pathToBambooExit(session);
 assert.ok(route?.length,'exit must be reachable after dialogue');
 for(const tile of route){
   session=moveBambooSession(session,tile.x-session.position.x,tile.y-session.position.y);
   assert.ok(session);
 }
 assert.deepEqual(session.position,BAMBOO_PASS.exit);
 const returned=leaveBambooPass(session,game);
 assert.ok(returned,'exit must return to village');
 assert.equal(returned.player.x,VILLAGE_RETURN.x);
 assert.equal(returned.player.y,VILLAGE_RETURN.y);
 assert.equal(returned.quest,game.quest);
 assert.deepEqual(returned.inventory,game.inventory);
 assert.deepEqual(returned.flags,game.flags);
 assert.equal(game.player.x,VILLAGE_GATE.x,'entry game state must not be mutated');
 assert.equal(shortestRegionRoute(BAMBOO_PASS,BAMBOO_PASS.entry,BAMBOO_PASS.exit)?.length>0,true);
});
