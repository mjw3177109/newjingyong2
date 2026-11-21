import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,canRestAtVillage,restAtVillage,parseSave,interact} from '../src/engine.js';
import {commandForKey} from '../src/controls.js';

// All scenarios exercise the ORIGINAL HTML5 demo, not reconstructed SWF events.
const nearElder = () => {
  const s=initialState();s.player.x=7;s.player.y=7;return s;
};

test('village rest heals exactly 20 HP, logs it and preserves valid save',()=>{
  const s=nearElder();s.player.hp=60;
  assert.equal(canRestAtVillage(s),true);
  const rested=restAtVillage(s);
  assert.equal(rested.player.hp,80);
  assert.equal(s.player.hp,60,'input is not mutated');
  assert.match(rested.journal[0],/恢复 20 点气血/);
  assert.deepEqual(parseSave(JSON.stringify(rested)),rested);
  assert.equal(rested.quest,s.quest);
  assert.equal(rested.player.silver,s.player.silver);
});

test('rest caps healing at max HP and does not create free turns at full HP',()=>{
  let s=nearElder();s.player.hp=95;
  const rested=restAtVillage(s);
  assert.equal(rested.player.hp,100);
  assert.match(rested.journal[0],/恢复 5 点气血/);
  assert.equal(canRestAtVillage(rested),false);
  assert.deepEqual(restAtVillage(rested),rested);
});

test('rest is forbidden remotely, during dialogue or combat',()=>{
  let s=initialState();s.player.hp=50;
  assert.equal(canRestAtVillage(s),false);
  assert.deepEqual(restAtVillage(s),s);
  s=nearElder();s.player.hp=50;
  const talking={...s,dialog:'正在交谈'};
  assert.equal(canRestAtVillage(talking),false);
  assert.deepEqual(restAtVillage(talking),talking);
  const fighting={...s,combat:{enemyHp:28,enemyMaxHp:28,guard:false}};
  assert.equal(canRestAtVillage(fighting),false);
  assert.deepEqual(restAtVillage(fighting),fighting);
});

test('rest works after completed quest without replaying rewards',()=>{
  const s=nearElder();s.player.hp=50;
  s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;
  s.inventory=['清心草','竹纹短剑'];
  const rested=restAtVillage(s);
  assert.equal(rested.player.hp,70);
  assert.equal(rested.quest,'completed');
  assert.deepEqual(rested.inventory,s.inventory);
  assert.deepEqual(parseSave(JSON.stringify(rested)),rested);
});

test('R shortcut is single-shot and never becomes a combat action',()=>{
  const key={key:'r',target:{tagName:'BODY'}};
  assert.deepEqual(commandForKey(key,false,false),{kind:'rest'});
  assert.equal(commandForKey({...key,repeat:true},false,false),null);
  assert.equal(commandForKey(key,true,false),null);
});
