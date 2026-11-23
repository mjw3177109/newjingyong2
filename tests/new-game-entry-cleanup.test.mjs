import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const main=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');

test('new game refuses to reset if bamboo entry snapshot cannot be removed',()=>{
 const start=main.indexOf('function newGame(){');
 const end=main.indexOf('function doMove(',start);
 assert.ok(start>=0 && end>start);
 const body=main.slice(start,end);
 assert.match(body,/if\(!clearBambooEntry\(\)\)\{toast\('无法清除山径入口快照，未重新开始'\);return;\}/);
 assert.ok(body.indexOf('if(!clearBambooEntry())')<body.indexOf('localStorage.removeItem(keyName)'));
 assert.ok(body.indexOf('if(!clearBambooEntry())')<body.indexOf('update(initialState())'));
});
