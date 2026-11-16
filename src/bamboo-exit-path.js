// Original demo-only navigation; never interpreted as SWF pathfinding evidence.
import {BAMBOO_PASS} from './bamboo-pass.js';
import {normalizeBambooCheckpoint} from './bamboo-checkpoint.js';
import {stepInRegion} from './region-navigation.js';

// Return the shortest walkable path to a clicked tile. Occupied NPC tiles
// are approached from an adjacent tile; neither routing nor clicking interacts.
export function pathToBambooTile(session, tx, ty) {
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
  const visited = new Set([key(start)]);
  const queue = [{position:start, path:[]}];
  for (let head=0; head<queue.length; head++) {
    const current = queue[head];
    for (const [dx,dy] of [[0,-1],[1,0],[0,1],[-1,0]]) {
      const next = stepInRegion(BAMBOO_PASS,current.position,dx,dy);
      if (!next || visited.has(key(next))) continue;
      const path = [...current.path,next];
      if (reached(next)) return path;
      visited.add(key(next));
      queue.push({position:next,path});
    }
  }
  return null;
}

// Backward-compatible exit guidance; no automatic region transition.
export function pathToBambooExit(session) {
  return pathToBambooTile(session, BAMBOO_PASS.exit.x, BAMBOO_PASS.exit.y);
}
