import test from 'node:test';
import assert from 'node:assert/strict';
import {nextObjective, pathToObjective, stepTowardObjective} from '../src/objectives.js';
import {ACTORS, BLOCKS, WIDTH, HEIGHT} from '../src/demo-data.js';

const fresh = () => ({quest:'unstarted', flags:{herbTaken:false,banditBeaten:false}, player:{x:5,y:8}});
const distance = (a,b) => Math.abs(a.x-b.x)+Math.abs(a.y-b.y);

test('route reaches a walkable adjacent interaction tile, never the elder tile', () => {
  const s=fresh(), route=pathToObjective(s), target=nextObjective(s);
  assert.equal(route.length,3); // Manhattan 4 to the elder; stop one tile early.
  assert.equal(distance(route.at(-1),target),1);
  let prev=s.player;
  for (const step of route) {
    assert.equal(distance(prev,step),1);
    assert.ok(step.x>=0 && step.x<WIDTH && step.y>=0 && step.y<HEIGHT);
    assert.ok(!BLOCKS.has(`${step.x},${step.y}`));
    assert.ok(!Object.values(ACTORS).some(a=>a.x===step.x&&a.y===step.y));
    prev=step;
  }
});
test('already adjacent to the target returns an empty route', () => {
  const s=fresh();s.player={x:7,y:7};
  assert.deepEqual(pathToObjective(s),[]);
});
test('active quest routes around buildings and live actors', () => {
  const s=fresh();s.quest='active';
  const route=pathToObjective(s), target=nextObjective(s);
  assert.ok(route.length>0);
  assert.equal(distance(route.at(-1),target),1);
  for(const step of route){
    assert.ok(!BLOCKS.has(`${step.x},${step.y}`));
    assert.ok(!Object.values(ACTORS).some(a=>a.x===step.x&&a.y===step.y));
  }
});
test('collected herb tile is traversable when guiding to the trial', () => {
  const s=fresh();s.quest='active';s.flags.herbTaken=true;s.player={x:12,y:10};
  const route=pathToObjective(s);
  assert.ok(route?.length>0);
  assert.equal(distance(route.at(-1),ACTORS.bandit),1);
});
test('completed and malformed objectives or blocked starting tiles produce no route', () => {
  const s=fresh();s.quest='completed';assert.equal(pathToObjective(s),null);
  s.quest='unknown';assert.equal(pathToObjective(s),null);
  s.quest='unstarted';s.player={x:2,y:2};assert.equal(pathToObjective(s),null);
  s.player={x:7,y:6};assert.equal(pathToObjective(s),null);
  s.player={x:NaN,y:1};assert.equal(pathToObjective(s),null);
  assert.equal(pathToObjective(null),null);
});
test('route calculation is deterministic and does not mutate game state', () => {
  const s=fresh();const before=structuredClone(s);
  assert.deepEqual(pathToObjective(s),pathToObjective(s));
  assert.deepEqual(s,before);
});

test('route-step advances exactly one cardinal tile and never mutates its input', () => {
  const s=fresh(), before=structuredClone(s), first=pathToObjective(s)[0];
  const next=stepTowardObjective(s);
  assert.deepEqual(next.player,{...s.player,x:first.x,y:first.y});
  assert.equal(distance(s.player,next.player),1);
  assert.deepEqual(s,before);
});
test('route-step can be repeated to reach an interaction tile without entering NPC tile', () => {
  let s=fresh();const target=nextObjective(s);
  for(let i=0;i<20 && pathToObjective(s)?.length;i++) s=stepTowardObjective(s);
  assert.equal(distance(s.player,target),1);
  assert.deepEqual(pathToObjective(s),[]);
  assert.deepEqual(stepTowardObjective(s),s);
});
test('route-step is inert during dialog, combat, invalid and completed objectives', () => {
  const s=fresh();
  for(const patch of [{dialog:'对话中'}, {combat:{enemyHp:10}}, {quest:'completed'}, {player:{x:2,y:2}}]) {
    const blocked={...s,...patch};
    assert.deepEqual(stepTowardObjective(blocked),blocked);
  }
  assert.equal(stepTowardObjective(null),null);
});
test('route-step recomputes after quest progress and does not skip interactions', () => {
  let s=fresh();
  while(pathToObjective(s)?.length) s=stepTowardObjective(s);
  assert.equal(s.quest,'unstarted');
  assert.equal(s.flags.herbTaken,false);
  assert.equal(s.flags.banditBeaten,false);
});
