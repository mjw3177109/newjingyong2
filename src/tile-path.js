import {ACTORS, BLOCKS, WIDTH, HEIGHT} from './demo-data.js';

const key = (x, y) => `${x},${y}`;
const inside = (x, y) => Number.isInteger(x) && Number.isInteger(y) &&
  x >= 0 && y >= 0 && x < WIDTH && y < HEIGHT;

// Original HTML5 demo only. One tap selects a destination; no auto-interaction or timers.
// Returns the shortest walkable route, [] when already there, null when invalid/unreachable.
// Tapping a live actor stops beside it rather than stepping onto its occupied tile.
export function pathToTile(state, tx, ty) {
  const p = state?.player;
  if (!p || !inside(p.x, p.y) || !inside(tx, ty)) return null;
  const occupied = new Set(BLOCKS);
  let liveActorTarget = false;
  for (const [id, actor] of Object.entries(ACTORS)) {
    if ((id === 'herb' && state.flags?.herbTaken) ||
        (id === 'bandit' && state.flags?.banditBeaten)) continue;
    occupied.add(key(actor.x, actor.y));
    if (actor.x === tx && actor.y === ty) liveActorTarget = true;
  }
  if (occupied.has(key(p.x, p.y)) || BLOCKS.has(key(tx, ty))) return null;
  const reached = (x, y) => liveActorTarget
    ? Math.abs(x - tx) + Math.abs(y - ty) === 1
    : x === tx && y === ty;
  if (reached(p.x, p.y)) return [];
  const start = key(p.x, p.y);
  const parents = new Map([[start, null]]);
  const queue = [{x: p.x, y: p.y}];
  for (let i = 0; i < queue.length; i++) {
    const cell = queue[i];
    for (const [dx, dy] of [[0,-1], [1,0], [0,1], [-1,0]]) {
      const x = cell.x + dx, y = cell.y + dy, k = key(x, y);
      if (!inside(x, y) || occupied.has(k) || parents.has(k)) continue;
      parents.set(k, key(cell.x, cell.y));
      if (reached(x, y)) {
        const route = [];
        for (let current = k; current !== start; current = parents.get(current)) {
          const [rx, ry] = current.split(',').map(Number);
          route.push({x: rx, y: ry});
        }
        return route.reverse();
      }
      queue.push({x, y});
    }
  }
  return null;
}
