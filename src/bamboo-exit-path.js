// Original demo-only exit guidance; never interpreted as SWF pathfinding evidence.
import {BAMBOO_PASS} from './bamboo-pass.js';
import {normalizeBambooCheckpoint} from './bamboo-checkpoint.js';
import {stepInRegion} from './region-navigation.js';

// Deterministic breadth-first search; no session mutation or automatic transition.
export function pathToBambooExit(session) {
  const valid = normalizeBambooCheckpoint(session);
  if (!valid) return null;
  const start = valid.position;
  const goal = BAMBOO_PASS.exit;
  if (start.x === goal.x && start.y === goal.y) return [];
  const key = p => p.x + ',' + p.y;
  const visited = new Set([key(start)]);
  const queue = [{position:start, path:[]}];
  const directions = [[0,-1],[1,0],[0,1],[-1,0]];
  for (let head=0; head<queue.length; head++) {
    const current = queue[head];
    for (const [dx,dy] of directions) {
      const next = stepInRegion(BAMBOO_PASS,current.position,dx,dy);
      if (!next || visited.has(key(next))) continue;
      const path = [...current.path,next];
      if (next.x === goal.x && next.y === goal.y) return path;
      visited.add(key(next));
      queue.push({position:next,path});
    }
  }
  return null;
}
