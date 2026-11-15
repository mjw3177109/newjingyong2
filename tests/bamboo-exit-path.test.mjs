import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {stepInRegion} from '../src/region-navigation.js';
import {pathToBambooExit} from '../src/bamboo-exit-path.js';

test('bamboo exit route is deterministic, legal and does not mutate session', () => {
  const session={regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
  const before=structuredClone(session);
  const route=pathToBambooExit(session);
  assert.ok(Array.isArray(route) && route.length>0);
  let previous=session.position;
  for(const tile of route){
    const dx=tile.x-previous.x,dy=tile.y-previous.y;
    assert.deepEqual(stepInRegion(BAMBOO_PASS,previous,dx,dy),tile);
    previous=tile;
  }
  assert.deepEqual(previous,BAMBOO_PASS.exit);
  assert.deepEqual(pathToBambooExit(session),route);
  assert.deepEqual(session,before);
});
test('already at exit returns empty path and invalid sessions are rejected',()=>{
  assert.deepEqual(pathToBambooExit({regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.exit}}),[]);
  assert.equal(pathToBambooExit(null),null);
  assert.equal(pathToBambooExit({regionId:'unknown',position:{...BAMBOO_PASS.entry}}),null);
  assert.equal(pathToBambooExit({regionId:BAMBOO_PASS.id,position:{x:Infinity,y:1}}),null);
});
