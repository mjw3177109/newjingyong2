import {ACTORS} from './demo-data.js';

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
