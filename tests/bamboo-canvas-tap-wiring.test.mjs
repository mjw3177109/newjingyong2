import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Wiring regression only; real pointer behavior must also pass Chromium CI.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
test('bamboo canvas taps only request adjacent moves and return before village routing',()=>{
 const start=source.indexOf("canvas.addEventListener('click'");
 const end=source.indexOf("document.addEventListener('keydown'",start);
 assert.ok(start>=0&&end>start);
 const handler=source.slice(start,end);
 assert.match(handler,/if\(bambooSession\)/);
 assert.match(handler,/Math\.abs\(dx\)\+Math\.abs\(dy\)===1/);
 assert.match(handler,/doMove\(dx,dy\)/);
 assert.ok(handler.indexOf('return;',handler.indexOf('if(bambooSession)'))<handler.indexOf('pathToTile(state')));
});
