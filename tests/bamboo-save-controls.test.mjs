import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Wiring regression: no browser runtime is claimed by this source-level check.
const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');
test('bamboo view disables save and export before returning',()=>{
 const start=source.indexOf('function paint(){');
 const branch=source.indexOf('if(bambooSession){',start);
 const returnAt=source.indexOf('return;',branch);
 const block=source.slice(branch,returnAt);
 assert.match(block,/\$\('save'\)\.disabled=true/);
 assert.match(block,/\$\('export-save'\)\.disabled=true/);
});
test('village view restores save and export after bamboo return',()=>{
 const start=source.indexOf('function paint(){');
 const returnAt=source.indexOf('return;',source.indexOf('if(bambooSession){',start));
 const village=source.slice(returnAt,source.indexOf('ctx.clearRect',returnAt));
 assert.match(village,/\$\('save'\)\.disabled=false/);
 assert.match(village,/\$\('export-save'\)\.disabled=false/);
});
