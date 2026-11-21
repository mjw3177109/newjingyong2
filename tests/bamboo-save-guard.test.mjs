import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
function functionBodyUntil(start,next){
 const a=source.indexOf(start),b=source.indexOf(next,a+start.length);
 assert.ok(a>=0&&b>a,'expected function boundaries');
 return source.slice(a,b);
}
test('local save refuses to silently discard an active bamboo session',()=>{
 const body=functionBodyUntil('function save(){','function load(){');
 assert.match(body,/if\(bambooSession\)\{[^}]*return;/);
 assert.ok(body.indexOf('if(bambooSession)')<body.indexOf('encodeCheckpoint('));
});
test('portable export refuses to silently discard an active bamboo session',()=>{
 const body=functionBodyUntil('function exportSave() {',"$('interact').onclick");
 assert.match(body,/if\(bambooSession\)\{[^}]*return;/);
 assert.ok(body.indexOf('if(bambooSession)')<body.indexOf('encodeCheckpoint('));
});
