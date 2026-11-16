// Original Q-style demo routing regression tests; not evidence from jin.swf.
import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {pathToBambooTile, pathToBambooExit} from '../src/bamboo-exit-path.js';

const session = (x = BAMBOO_PASS.entry.x, y = BAMBOO_PASS.entry.y) =>
  ({regionId: BAMBOO_PASS.id, position: {x, y}});
const blocked = new Set(BAMBOO_PASS.blocks);
const key = ({x,y}) => x + ',' + y;
function assertWalkableRoute(start, route) {
  assert.ok(Array.isArray(route));
  let previous = start;
  const visited = new Set([key(start)]);
  for (const tile of route) {
    assert.equal(Math.abs(tile.x - previous.x) + Math.abs(tile.y - previous.y), 1);
    assert.ok(tile.x >= 0 && tile.x < BAMBOO_PASS.width);
    assert.ok(tile.y >= 0 && tile.y < BAMBOO_PASS.height);
    assert.ok(!blocked.has(key(tile)));
    assert.notDeepEqual(tile, {x:BAMBOO_PASS.npc.x,y:BAMBOO_PASS.npc.y});
    assert.ok(!visited.has(key(tile)), 'shortest route cannot contain a cycle');
    visited.add(key(tile));
    previous = tile;
  }
}
test('clicking the exit yields contiguous safe route and legacy exit helper agrees', () => {
  const start = session();
  const route = pathToBambooTile(start, BAMBOO_PASS.exit.x, BAMBOO_PASS.exit.y);
  assertWalkableRoute(start.position, route);
  assert.deepEqual(route.at(-1), BAMBOO_PASS.exit);
  assert.deepEqual(route, pathToBambooExit(start));
});
test('NPC click stops next to NPC and never steps onto occupied tile', () => {
  const start = session();
  const route = pathToBambooTile(start, BAMBOO_PASS.npc.x, BAMBOO_PASS.npc.y);
  assertWalkableRoute(start.position, route);
  const last = route.at(-1);
  assert.equal(Math.abs(last.x - BAMBOO_PASS.npc.x) + Math.abs(last.y - BAMBOO_PASS.npc.y), 1);
});
test('already at destination returns empty route; obstacle and out of bounds return null', () => {
  assert.deepEqual(pathToBambooTile(session(), 1, 4), []);
  assert.equal(pathToBambooTile(session(), 4, 2), null);
  assert.equal(pathToBambooTile(session(), -1, 4), null);
  assert.equal(pathToBambooTile(session(), 12, 4), null);
  assert.equal(pathToBambooTile(session(), 1.5, 4), null);
});
test('malformed or hostile checkpoint never throws and never returns a route', () => {
  assert.equal(pathToBambooTile(null, 10, 4), null);
  assert.equal(pathToBambooTile({regionId:'wrong',position:{x:1,y:4}}, 10, 4), null);
  assert.equal(pathToBambooTile(new Proxy({}, {ownKeys(){throw new Error('bad checkpoint');}}), 10, 4), null);
});
