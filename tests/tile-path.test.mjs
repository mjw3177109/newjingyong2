import test from 'node:test';
import assert from 'node:assert/strict';
import {pathToTile} from '../src/tile-path.js';
import {ACTORS, BLOCKS, WIDTH, HEIGHT} from '../src/demo-data.js';

const fresh = () => ({player:{x:5,y:8},flags:{herbTaken:false,banditBeaten:false}});
const distance = (a,b) => Math.abs(a.x-b.x)+Math.abs(a.y-b.y);

test('tapping a walkable tile produces a shortest cardinal route', () => {
  const s=fresh(), route=pathToTile(s,7,8);
  assert.equal(route.length,2);
  assert.deepEqual(route[0],{x:6,y:8});
  assert.deepEqual(route.at(-1),{x:7,y:8});
});
test('tapping a live NPC stops on a neighboring walkable tile', () => {
  const s=fresh(), route=pathToTile(s,ACTORS.elder.x,ACTORS.elder.y);
  assert.equal(route.length,3);
  assert.equal(distance(route.at(-1),ACTORS.elder),1);
  for(const step of route){
    assert.ok(!BLOCKS.has(`${step.x},${step.y}`));
    assert.ok(!Object.values(ACTORS).some(a=>a.x===step.x&&a.y===step.y));
  }
});
test('cleared herb and defeated trial tiles become walkable', () => {
  const herb=fresh();herb.player={x:12,y:9};herb.flags.herbTaken=true;
  assert.deepEqual(pathToTile(herb,12,10),[{x:12,y:10}]);
  const bandit=fresh();bandit.player={x:19,y:8};bandit.flags.banditBeaten=true;
  assert.deepEqual(pathToTile(bandit,19,7),[{x:19,y:7}]);
});
test('invalid coordinates, walls, and occupied starting cells cannot route', () => {
  const s=fresh();
  for(const [x,y] of [[-1,8],[WIDTH,8],[0,HEIGHT],[1.5,8],[Infinity,8],[2,2]])
    assert.equal(pathToTile(s,x,y),null);
  assert.equal(pathToTile({...s,player:{x:7,y:6}},6,8),null);
  assert.equal(pathToTile(null,6,8),null);
});
test('already standing at destination or beside an NPC yields no movement', () => {
  const s=fresh();
  assert.deepEqual(pathToTile(s,5,8),[]);
  assert.deepEqual(pathToTile({...s,player:{x:7,y:7}},7,6),[]);
});
test('tap routes are deterministic and do not mutate player or quest state', () => {
  const s=fresh(), before=structuredClone(s);
  assert.deepEqual(pathToTile(s,19,7),pathToTile(s,19,7));
  assert.deepEqual(s,before);
});
