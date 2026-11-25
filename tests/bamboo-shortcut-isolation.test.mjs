import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');

test('bamboo region rejects village shortcuts while allowing exit routing',()=>{
 const start=source.indexOf("document.addEventListener('keydown'");
 const end=source.indexOf('function exportSave()',start);
 assert.ok(start>=0&&end>start);
 const handler=source.slice(start,end);
 assert.match(handler,/if\(bambooSession && !\['move','interact','dismiss-dialog','route-step','npc-step'\]\.includes\(command\.kind\)\)return;/);
 assert.match(handler,/else if\(command\.kind==='route-step'\)stepRoute\(\);/);
 assert.match(handler,/else if\(command\.kind==='npc-step' && bambooSession\)stepTowardKeeper\(\);/);
 assert.match(handler,/else if\(command\.kind==='inventory'\)/);
 assert.match(handler,/else if\(command\.kind==='quest'\)/);
 assert.match(source,/function stepRoute\(\)\{\s*if\(!bambooSession\)\{update\(stepTowardObjective\(state\)\);return;\}/);
 assert.match(source,/const route=pathToBambooExit\(bambooSession\);/);
});
