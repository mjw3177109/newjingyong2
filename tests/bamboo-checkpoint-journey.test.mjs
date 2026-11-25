import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,parseSave} from '../src/engine.js';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {encodeBambooSession,decodeBambooSession} from '../src/bamboo-session-codec.js';
import {VILLAGE_GATE,VILLAGE_RETURN,enterBambooPass,moveBambooSession,leaveBambooPass} from '../src/region-travel.js';

// Original Q-style demo only; no claim about the source SWF's locations or events.
test('bamboo journey survives independent village and region checkpoints',()=>{
 const base=initialState();
 const atGate={...base,player:{...base.player,...VILLAGE_GATE}};
 const village= parseSave(JSON.stringify(atGate));
 assert.deepEqual(village,atGate);
 const entry=enterBambooPass(village);
 assert.ok(entry);
 const queue=[entry],seen=new Set([entry.position.x+','+entry.position.y]);
 let exit=null;
 for(let i=0;i<queue.length;i++){
  const current=decodeBambooSession(encodeBambooSession(queue[i]));
  assert.deepEqual(current,queue[i],'every reachable region checkpoint must roundtrip');
  if(current.position.x===BAMBOO_PASS.exit.x&&current.position.y===BAMBOO_PASS.exit.y){
   exit=current;break;
  }
  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
   const next=moveBambooSession(current,dx,dy);
   if(!next)continue;
   const key=next.position.x+','+next.position.y;
   if(!seen.has(key)){seen.add(key);queue.push(next);}
  }
 }
 assert.ok(exit,'the exit must remain reachable after repeated checkpoint restores');
 const returned=leaveBambooPass(exit,village);
 assert.ok(returned);
 assert.deepEqual({x:returned.player.x,y:returned.player.y},VILLAGE_RETURN);
 assert.deepEqual(parseSave(JSON.stringify(returned)),returned,'return to village must survive a v2 save');
 assert.deepEqual(village,atGate,'travel must not mutate the saved village state');
});
