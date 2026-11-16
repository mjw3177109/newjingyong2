// Original demo-only route determinism and read-only checkpoint contract.
// This test does not claim any event or movement rule from jin.swf.
import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {pathToBambooTile, pathToBambooExit} from '../src/bamboo-exit-path.js';

test('BFS is repeatable and never mutates a frozen checkpoint', () => {
  const position = Object.freeze({...BAMBOO_PASS.entry});
  const checkpoint = Object.freeze({regionId: BAMBOO_PASS.id, position});
  const first = pathToBambooExit(checkpoint);
  assert.ok(Array.isArray(first), 'entry should have an exit route');
  assert.ok(first.length > 0, 'entry should not already be the exit');
  assert.deepEqual(pathToBambooExit(checkpoint), first);
  assert.deepEqual(pathToBambooTile(checkpoint, BAMBOO_PASS.exit.x, BAMBOO_PASS.exit.y), first);
  assert.deepEqual(checkpoint.position, BAMBOO_PASS.entry);
  // A consumer may mutate the returned route without changing later results.
  first[0].x = -999;
  first.push({x: -999, y: -999});
  const again = pathToBambooExit(checkpoint);
  assert.ok(again.every(p => p.x >= 0 && p.x < BAMBOO_PASS.width));
  assert.notDeepEqual(again, first);
});
