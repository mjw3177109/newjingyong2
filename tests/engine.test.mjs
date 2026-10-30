import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, move, interact, battle, parseSave, questStatus} from '../src/engine.js';
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
test('world movement obeys boundaries, solid tiles, actor collision',()=>{
 let s=initialState();assert.equal(move(at(s,0,0),-1,0).player.x,0);
 assert.equal(move(at(s,2,4),0,-1).player.y,4);
 assert.equal(move(at(s,7,7),0,-1).player.y,7);
 assert.equal(move(at(s,5,8),1,0).player.x,6);
});
test('quest needs both herb and trial, then completion awards silver once',()=>{
 let s=interact(at(initialState(),7,7));assert.equal(s.quest,'active');
 s=interact(s);s=interact(at(s,12,9));assert.equal(s.flags.herbTaken,true);
 s=interact(s);s=interact(at(s,19,8));assert.ok(s.combat);
 for(let i=0;i<3;i++)s=battle(s,'attack');
 assert.equal(s.flags.banditBeaten,true);assert.equal(s.combat,null);
 s=interact(at(s,7,7));assert.equal(s.quest,'completed');assert.equal(s.player.silver,40);
 s=interact(s);s=interact(s);assert.equal(s.player.silver,40);
});
test('merchant sells potion; battle healing caps HP; missing potion is non-consuming',()=>{
 let s=interact(at(initialState(),16,8));assert.ok(s.inventory.includes('回春散'));assert.equal(s.player.silver,5);
 s=interact(s);s=interact(at(s,19,8));s.player.hp=92;
 s=battle(s,'drink');assert.equal(s.player.hp,94);assert.ok(!s.inventory.includes('回春散'));
 const hp=s.player.hp;s=battle(s,'drink');assert.equal(s.player.hp,hp);
});
test('save parsing rejects invalid / incompatible structures',()=>{
 const s=initialState();assert.ok(parseSave(JSON.stringify(s)));
 assert.equal(parseSave('{'),null);assert.equal(parseSave(JSON.stringify({...s,version:2})),null);
 assert.equal(parseSave(JSON.stringify({...s,player:{x:100,y:0,hp:100}})),null);
});
test('quest status phases',()=>{
 let s=initialState();assert.equal(questStatus(s).progress,'未接受');s.quest='completed';assert.match(questStatus(s).progress,/已完成/);
});
