import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');

test('bamboo region rejects village inventory and quest shortcuts',()=>{
 const start=source.indexOf("document.addEventListener('keydown'");
 const end=source.indexOf('function exportSave()',start);
 assert.ok(start>=0&&end>start);
 const handler=source.slice(start,end);
 assert.match(handler,/if\(bambooSession && !\['move','interact','dismiss-dialog'\]\.includes\(command\.kind\)\)return;/);
 assert.match(handler,/else if\(command\.kind==='inventory'\)/);
 assert.match(handler,/else if\(command\.kind==='quest'\)/);
});
