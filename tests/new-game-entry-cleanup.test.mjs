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

test('load and import abort before replacing progress when bamboo entry cleanup fails',()=>{
 const loadStart=main.indexOf('function load(){');
 const loadEnd=main.indexOf('function newGame(){',loadStart);
 const loadBody=main.slice(loadStart,loadEnd);
 assert.match(loadBody,/if\(!clearBambooEntry\(\)\)\{toast\('无法清除山径入口快照，未读取存档'\);return;\}/);
 assert.ok(loadBody.indexOf('if(!clearBambooEntry())')<loadBody.indexOf('if(!clearBambooSession(localStorage))'));
 assert.ok(loadBody.indexOf('if(!clearBambooEntry())')<loadBody.indexOf('update(parsed)'));
 const importStart=main.indexOf("$('import-save-file').onchange=");
 const importEnd=main.indexOf('function stepTowardKeeper()',importStart);
 const importBody=main.slice(importStart,importEnd);
 assert.match(importBody,/if\(!clearBambooEntry\(\)\)\{toast\('无法清除山径入口快照，未导入存档'\);return;\}/);
 assert.ok(importBody.indexOf('if(!clearBambooEntry())')<importBody.indexOf('if(!clearBambooSession(localStorage))'));
 assert.ok(importBody.indexOf('if(!clearBambooEntry())')<importBody.indexOf('update(imported)'));
});


test('leaving bamboo region restores session and aborts exit when entry cleanup fails',()=>{
 const start=main.indexOf('function action(){');
 const end=main.indexOf('const DEMO_FIRST_VICTORY_MARKER',start);
 assert.ok(start>=0 && end>start);
 const body=main.slice(start,end);
 assert.match(body,/if\(!clearBambooEntry\(\)\)\{/);
 assert.match(body,/const restored=saveBambooSession\(localStorage,bambooSession\)/);
 assert.match(body,/入口快照清理失败且山径记录恢复失败；请勿刷新页面/);
 const guard=body.indexOf('if(!clearBambooEntry())');
 const restore=body.indexOf('saveBambooSession(localStorage,bambooSession)',guard);
 const abort=body.indexOf('return;',restore);
 const leave=body.indexOf('bambooSession=null;update(returned)',guard);
 assert.ok(guard>=0 && restore>guard && abort>restore && leave>abort);
 assert.match(body,/toast\('已返回青竹村'\)/);
});
