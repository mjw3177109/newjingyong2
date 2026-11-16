// Original demo-only navigation; never interpreted as SWF pathfinding evidence.
import {BAMBOO_PASS} from './bamboo-pass.js';
import {normalizeBambooCheckpoint} from './bamboo-checkpoint.js';

// Return the shortest walkable path to a clicked tile. Occupied NPC tiles
// are approached from an adjacent tile; neither routing nor clicking interacts.
export function pathToBambooTile(session, tx, ty) {
  // Treat malformed external session objects as an unreachable route, not a UI crash.
  try {
  const valid = normalizeBambooCheckpoint(session);
  if (!valid || !Number.isInteger(tx) || !Number.isInteger(ty) ||
      tx < 0 || ty < 0 || tx >= BAMBOO_PASS.width || ty >= BAMBOO_PASS.height ||
      BAMBOO_PASS.blocks.includes(tx + ',' + ty)) return null;
  const start = valid.position;
  const npcTarget = tx === BAMBOO_PASS.npc.x && ty === BAMBOO_PASS.npc.y;
  const reached = p => npcTarget
    ? Math.abs(p.x - tx) + Math.abs(p.y - ty) === 1
    : p.x === tx && p.y === ty;
  if (reached(start)) return [];
  const key = p => p.x + ',' + p.y;
  // Store one predecessor per tile rather than copying an entire route for
  // every queued node. This keeps breadth-first search memory linear in tiles.
  const startKey = key(start);
  const parents = new Map([[startKey, null]]);
  const positions = new Map([[startKey, start]]);
  const queue = [start];
  // Region is fixed and checkpoint validated. Avoid revalidating the entire
  // map on every BFS edge (stepInRegion does this for isolated moves).
  const blocked = new Set(BAMBOO_PASS.blocks);
  const npcKey = BAMBOO_PASS.npc.x + ',' + BAMBOO_PASS.npc.y;
  for (let head = 0; head < queue.length; head++) {
    const current = queue[head];
    for (const [dx, dy] of [[0,-1],[1,0],[0,1],[-1,0]]) {
      const next = {x: current.x + dx, y: current.y + dy};
      if (next.x < 0 || next.y < 0 || next.x >= BAMBOO_PASS.width || next.y >= BAMBOO_PASS.height) continue;
      const nextKey = key(next);
      if (blocked.has(nextKey) || nextKey === npcKey) continue;
      if (parents.has(nextKey)) continue;
      parents.set(nextKey, key(current));
      positions.set(nextKey, next);
      if (reached(next)) {
        const route = [];
        for (let k = nextKey; k !== startKey; k = parents.get(k)) {
          route.push(positions.get(k));
        }
        return route.reverse();
      }
      queue.push(next);
    }
  }
  return null;
  } catch {
    return null;
  }
}

// Backward-compatible exit guidance; no automatic region transition.
export function pathToBambooExit(session) {
  return pathToBambooTile(session, BAMBOO_PASS.exit.x, BAMBOO_PASS.exit.y);
}
