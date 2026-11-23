import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Browser wiring regression: the village engine state must not be mutated
// by shortcuts or button callbacks while an independent region is active.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
test('region keyboard shortcuts are limited to region-safe commands',()=>{
 assert.match(source,/if\(bambooSession && !\['move','interact','dismiss-dialog','route-step','npc-step'\]\.includes\(command\.kind\)\)return;/);
 assert.match(source,/else if\(command\.kind==='npc-step' && bambooSession\)stepTowardKeeper\(\);/);
 assert.match(source,/function combatAction\(command\)\{\s*if\(bambooSession\)return;/);
});
test('village action buttons are guarded while exploring bamboo pass',()=>{
 for(const id of ['rematch','rest-village','equip-weapon','discard-potion','sell-potion','use-potion']){
  assert.ok(source.includes("$('"+id+"').onclick=()=>{if(!bambooSession)"),id);
  assert.ok(source.includes("'"+id+"'"),id);
 }
 // The shared route button is intentionally repurposed for the region, not disabled.
 assert.match(source,/function stepRoute\(\)\{\s*if\(!bambooSession\)\{update\(stepTowardObjective\(state\)\);return;\}/);
 assert.match(source,/\$\('step-route'\)\.onclick=stepRoute;/);
 assert.match(source,/else if\(command\.kind==='route-step'\)stepRoute\(\);/);
 assert.match(source,/const route=pathToBambooExit\(bambooSession\);/);
 assert.match(source,/doMove\(first\.x-bambooSession\.position\.x,first\.y-bambooSession\.position\.y\);/);
 assert.match(source,/if\(bambooSession\)\{\s*drawBambooPass/);
});
