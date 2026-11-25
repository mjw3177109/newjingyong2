import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, move, interact, battle, parseSave, equipWeapon, startRematch, canRematch, attackDamage, DEMO_SWORD} from '../src/engine.js';
import {ACTORS, BLOCKS, WIDTH, HEIGHT} from '../src/demo-data.js';

// Original demo only; never an assertion about jin.swf mechanics or story.
function approach(state, id) {
  const goal=ACTORS[id], blocked=new Set(BLOCKS);
  for(const [key, actor] of Object.entries(ACTORS)) {
    if(key==='herb' && state.flags.herbTaken) continue;
    if(key==='bandit' && state.flags.banditBeaten) continue;
    blocked.add(`${actor.x},${actor.y}`);
  }
  const queue=[[state.player.x,state.player.y,[]]];
  const seen=new Set([`${state.player.x},${state.player.y}`]);
  for(let i=0;i<queue.length;i++){
    const [x,y,path]=queue[i];
    if(Math.abs(x-goal.x)+Math.abs(y-goal.y)===1){
      for(const [dx,dy] of path) state=move(state,dx,dy);
      return state;
    }
    for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
      const nx=x+dx,ny=y+dy,key=`${nx},${ny}`;
      if(nx<0||ny<0||nx>=WIDTH||ny>=HEIGHT||blocked.has(key)||seen.has(key))continue;
      seen.add(key);queue.push([nx,ny,[...path,[dx,dy]]]);
    }
  }
  throw new Error(`No reachable adjacent tile: ${id}`);
}
function close(s){assert.ok(s.dialog);return interact(s);}
test('original demo: earned sword survives save and strengthens a reward-free rematch',()=>{
  let s=approach(initialState(),'elder');
  s=close(interact(s));
  s=approach(s,'herb');s=close(interact(s));
  s=approach(s,'bandit');s=interact(s);
  assert.ok(s.combat);
  while(s.combat)s=battle(s,'attack');
  s=approach(s,'elder');s=interact(s);
  assert.equal(s.quest,'completed');
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
  s=close(s);
  s=equipWeapon(s);
  assert.equal(attackDamage(s),16);
  s=parseSave(JSON.stringify(s));
  assert.ok(s);
  assert.equal(attackDamage(s),16);
  const silver=s.player.silver;
  assert.equal(canRematch(s),true);
  s=startRematch(s);
  assert.ok(s.combat);
  s=battle(s,'attack');
  assert.equal(s.combat.enemyHp,12);
  s=battle(s,'attack');
  assert.equal(s.combat,null);
  assert.equal(s.player.silver,silver);
  assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
  assert.equal(s.quest,'completed');
  assert.ok(parseSave(JSON.stringify(s)));
});
