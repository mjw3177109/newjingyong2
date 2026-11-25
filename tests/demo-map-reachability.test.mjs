import test from 'node:test';
import assert from 'node:assert/strict';
import {ACTORS, BLOCKS, WIDTH, HEIGHT} from '../src/demo-data.js';
import {initialState, move} from '../src/engine.js';

// Original Q-style demo map contract, NOT evidence recovered from jin.swf.
// Validate the actual movement rules, including actor occupancy, rather than
// trusting a geometric path that the player cannot traverse.
test('all required demo actors have a reachable interaction tile', () => {
  const start = initialState();
  const key = (x, y) => `${x},${y}`;
  const occupied = new Set(Object.values(ACTORS).map(a => key(a.x, a.y)));
  const visited = new Set([key(start.player.x, start.player.y)]);
  const queue = [{x:start.player.x, y:start.player.y}];
  const dirs = [[1,0],[-1,0],[0,1],[0,-1]];
  assert.ok(!BLOCKS.has(key(start.player.x,start.player.y)));
  assert.ok(!occupied.has(key(start.player.x,start.player.y)));
  for (const [id, actor] of Object.entries(ACTORS)) {
    assert.ok(Number.isInteger(actor.x) && Number.isInteger(actor.y), id);
    assert.ok(actor.x >= 0 && actor.x < WIDTH && actor.y >= 0 && actor.y < HEIGHT, id);
    assert.ok(!BLOCKS.has(key(actor.x, actor.y)), `${id} embedded in obstacle`);
  }
  for (let i = 0; i < queue.length; i++) {
    const pos = queue[i];
    for (const [dx,dy] of dirs) {
      const x=pos.x+dx, y=pos.y+dy, k=key(x,y);
      if (x<0 || y<0 || x>=WIDTH || y>=HEIGHT || visited.has(k)) continue;
      if (BLOCKS.has(k) || occupied.has(k)) continue;
      // Assert engine movement agrees with the map's expected passability.
      const moved = move({...start, player:{...start.player, ...pos}},dx,dy);
      assert.deepEqual([moved.player.x,moved.player.y],[x,y], `engine blocked ${k}`);
      visited.add(k);queue.push({x,y});
    }
  }
  for (const [id, actor] of Object.entries(ACTORS)) {
    assert.ok(queue.some(p => Math.abs(p.x-actor.x)+Math.abs(p.y-actor.y)===1),
      `${id} has no reachable cardinal interaction tile`);
  }
});
