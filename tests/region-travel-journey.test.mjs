import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {VILLAGE_GATE,VILLAGE_RETURN,enterBambooPass,moveBambooSession,talkBambooSession,leaveBambooPass} from '../src/region-travel.js';

// Exercise the actual travel API rather than only validating static map reachability.
test('a player can enter, reach the keeper, talk, and return to the village',()=>{
 const original=initialState();
 const atGate={...original,player:{...original.player,...VILLAGE_GATE}};
 const start=enterBambooPass(atGate);
 assert.ok(start);
 const queue=[start],seen=new Set([start.position.x+','+start.position.y]);
 let keeperTalk=null,exitSession=null;
 for(let i=0;i<queue.length;i++){
  const session=queue[i];
  if(talkBambooSession(session))keeperTalk=talkBambooSession(session);
  if(session.position.x===BAMBOO_PASS.exit.x && session.position.y===BAMBOO_PASS.exit.y)exitSession=session;
  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
   const next=moveBambooSession(session,dx,dy);
   if(!next)continue;
   const key=next.position.x+','+next.position.y;
   if(!seen.has(key)){seen.add(key);queue.push(next);}
  }
 }
 assert.ok(keeperTalk,'keeper must be interactable through actual movement');
 assert.ok(exitSession,'exit must be reachable through actual movement');
 const returned=leaveBambooPass(exitSession,atGate);
 assert.ok(returned);
 assert.deepEqual({x:returned.player.x,y:returned.player.y},VILLAGE_RETURN);
 assert.deepEqual(atGate.player,{...original.player,...VILLAGE_GATE},'travel must not mutate caller state');
 assert.equal(leaveBambooPass(start,atGate),null,'entry must not count as exit');
});
