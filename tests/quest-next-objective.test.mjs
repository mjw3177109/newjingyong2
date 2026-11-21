import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, questStatus} from '../src/engine.js';

// Original demo quest guidance only; no source-SWF event is asserted.
test('quest panel guides each incomplete objective without awarding rewards', () => {
  const initial = initialState();
  assert.match(questStatus(initial).description, /竹隐老人/);
  const active = {...initial, quest:'active'};
  assert.match(questStatus(active).description, /采集清心草/);
  const herb = {...active, flags:{...active.flags, herbTaken:true}, inventory:['清心草']};
  assert.match(questStatus(herb).description, /寻找竹林试炼者/);
  const ready = {...herb, flags:{...herb.flags, banditBeaten:true}};
  assert.match(questStatus(ready).description, /返回竹隐老人/);
  assert.equal(questStatus(ready).progress.includes('✓'), true);
  assert.equal(ready.quest, 'active');
  assert.equal(ready.player.silver, 10);
});
