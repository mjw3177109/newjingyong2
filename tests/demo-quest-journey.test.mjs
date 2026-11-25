import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, move, interact, battle, parseSave, DEMO_SWORD} from '../src/engine.js';
import {ACTORS, BLOCKS, WIDTH, HEIGHT} from '../src/demo-data.js';

// End-to-end ORIGINAL demo journey, not a reconstructed jin.swf quest.
function walkToAdjacent(state, actor) {
  const target=ACTORS[actor];
  const blocked=new Set(BLOCKS);
  for(const a of Object.values(ACTORS)) blocked.add(`${a.x},${a.y}`);
  const queue=[[state.player.x,state.player.y,[]]];
  const seen=new Set([`${state.player.x},${state.player.y}`]);
  for(let i=0;i<queue.length;i++){
    const [x,y,path]=queue[i];
    if(Math.abs(x-target.x)+Math.abs(y-target.y)===1){
      for(const [dx,dy] of path) state=move(state,dx,dy);
      assert.equal(Math.abs(state.player.x-target.x)+Math.abs(state.player.y-target.y),1);
      return state;
    }
    for(const [dx,dy] of [[0,-1],[1,0],[0,1],[-1,0]]){
      const nx=x+dx,ny=y+dy,key=`${nx},${ny}`;
      if(nx<0||ny<0||nx>=WIDTH||ny>=HEIGHT||blocked.has(key)||seen.has(key))continue;
      seen.add(key);queue.push([nx,ny,[...path,[dx,dy]]]);
    }
  }
  throw new Error(`No walkable path to ${actor}`);
}
function closeDialogue(s){assert.ok(s.dialog);return interact(s);}
test('original HTML5 demo quest is playable by movement, survives save, and pays only once',()=>{
  let s=initialState();
  s=walkToAdjacent(s,'elder');
  s=interact(s);assert.equal(s.quest,'active');
  s=closeDialogue(s);
  s=walkToAdjacent(s,'herb');
  s=interact(s);assert.equal(s.flags.herbTaken,true);
  s=closeDialogue(s);
  s=parseSave(JSON.stringify(s));assert.ok(s,'mid-quest save must load');
  s=walkToAdjacent(s,'bandit');
  s=interact(s);assert.ok(s.combat);
  while(s.combat) s=battle(s,'attack');
  assert.equal(s.flags.banditBeaten,true);
  s=parseSave(JSON.stringify(s));assert.ok(s,'post-battle save must load');
  s=walkToAdjacent(s,'elder');
  s=interact(s);assert.equal(s.quest,'completed');
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
  const silver=s.player.silver;
  s=closeDialogue(s);
  s=parseSave(JSON.stringify(s));assert.ok(s,'completed save must load');
  s=interact(s);assert.equal(s.player.silver,silver);
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
});
