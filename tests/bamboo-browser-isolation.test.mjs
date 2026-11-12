import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Browser wiring regression: the village engine state must not be mutated
// by shortcuts or button callbacks while an independent region is active.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
test('region keyboard shortcuts are limited to region-safe commands',()=>{
 assert.match(source,/if\(bambooSession && !\['move','interact','dismiss-dialog','inventory','quest'\]\.includes\(command\.kind\)\)return;/);
 assert.match(source,/function combatAction\(command\)\{\s*if\(bambooSession\)return;/);
});
test('village action buttons are guarded while exploring bamboo pass',()=>{
 for(const id of ['step-route','rematch','rest-village','equip-weapon','discard-potion','sell-potion','use-potion']){
  assert.ok(source.includes("$('"+id+"').onclick=()=>{if(!bambooSession)"),id);
  assert.ok(source.includes("'"+id+"'"),id);
 }
 assert.match(source,/if\(bambooSession\)\{\s*drawBambooPass/);
});
