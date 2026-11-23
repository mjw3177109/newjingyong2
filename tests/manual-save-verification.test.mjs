import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');

test('manual save verifies the stored bytes before showing success',()=>{
 const start=source.indexOf('function save(){');
 const end=source.indexOf('function load(){',start);
 assert.ok(start>=0 && end>start);
 const body=source.slice(start,end);
 const write=body.indexOf('localStorage.setItem(keyName,raw)');
 const verify=body.indexOf('localStorage.getItem(keyName)!==raw');
 const success=body.indexOf("toast('进度已存入本机浏览器')");
 assert.ok(write>=0 && verify>write && success>verify);
 assert.match(body,/throw new Error\('checkpoint write not verified'\)/);
 assert.match(body,/catch\{toast\('存档无效或浏览器存储不可用'\);\}/);
});
