import {ACTORS} from './demo-data.js';
import {move} from './engine.js';
import {pathToTile} from './tile-path.js';

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

// Reuse the same four-direction shortest-path planner as Canvas taps.
// [] means already beside the live objective; null means invalid/unreachable.
// No original SWF map, pathfinding or quest logic is inferred here.
export function pathToObjective(state) {
  const target = nextObjective(state);
  return target ? pathToTile(state, target.x, target.y) : null;
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
