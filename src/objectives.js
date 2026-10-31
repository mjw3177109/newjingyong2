import {ACTORS, BLOCKS, WIDTH, HEIGHT} from './demo-data.js';
import {move} from './engine.js';

// These hints describe the original HTML5 demonstration, NOT verified SWF events.
// Do not use this module as a source for the original game's quest sequence.
export function nextObjective(state) {
  if (!state || state.quest === 'completed') return null;
  let id, label;
  if (state.quest === 'unstarted') {
    id = 'elder'; label = '拜访竹隐老人';
  } else if (state.quest === 'active') {
    if (!state.flags?.herbTaken) {
      id = 'herb'; label = '采集清心草';
    } else if (!state.flags?.banditBeaten) {
      id = 'bandit'; label = '挑战竹林试炼者';
    } else {
      id = 'elder'; label = '返回竹隐老人处复命';
    }
  } else return null;
  const actor = ACTORS[id];
  return {id, label, x: actor.x, y: actor.y};
}

// Shortest walkable route to an adjacent interaction tile, never into an NPC.
// [] means the player can already interact; null means no valid route/target.
// The original SWF map and navigation are not used here.
export function pathToObjective(state) {
  const target = nextObjective(state);
  const p = state?.player;
  if (!target || !p || !Number.isInteger(p.x) || !Number.isInteger(p.y) ||
      p.x < 0 || p.y < 0 || p.x >= WIDTH || p.y >= HEIGHT) return null;
  const key = (x, y) => `${x},${y}`;
  const occupied = new Set(BLOCKS);
  for (const [id, actor] of Object.entries(ACTORS)) {
    if ((id === 'herb' && state.flags?.herbTaken) ||
        (id === 'bandit' && state.flags?.banditBeaten)) continue;
    occupied.add(key(actor.x, actor.y));
  }
  const start = key(p.x, p.y);
  if (occupied.has(start)) return null;
  const adjacent = (x, y) => Math.abs(x - target.x) + Math.abs(y - target.y) === 1;
  if (adjacent(p.x, p.y)) return [];
  const queue = [{x:p.x, y:p.y}];
  const parents = new Map([[start, null]]);
  for (let i = 0; i < queue.length; i++) {
    const cell = queue[i];
    for (const [dx, dy] of [[0,-1],[1,0],[0,1],[-1,0]]) {
      const x = cell.x + dx, y = cell.y + dy, k = key(x, y);
      if (x < 0 || y < 0 || x >= WIDTH || y >= HEIGHT ||
          occupied.has(k) || parents.has(k)) continue;
      parents.set(k, key(cell.x, cell.y));
      if (adjacent(x, y)) {
        const route = [];
        for (let current = k; current !== start; current = parents.get(current)) {
          const [rx, ry] = current.split(',').map(Number);
          route.push({x:rx, y:ry});
        }
        return route.reverse();
      }
      queue.push({x, y});
    }
  }
  return null;
}

// One deliberate input advances exactly one legal tile toward the current demo objective.
// No automatic interactions, combat turns or timers; recompute the path on every press.
export function stepTowardObjective(state) {
  if (!state || state.dialog || state.combat) return state;
  const route = pathToObjective(state);
  if (!route?.length) return state;
  const first = route[0];
  return move(state, first.x - state.player.x, first.y - state.player.y);
}
