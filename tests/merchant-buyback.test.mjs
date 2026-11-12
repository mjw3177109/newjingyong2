import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, sellPotion, MAX_SILVER} from '../src/engine.js';
import {ACTORS} from '../src/demo-data.js';

test('merchant buys one potion for two silver only when adjacent', () => {
 const s=initialState();s.inventory=['回春散'];s.player.x=ACTORS.merchant.x-1;s.player.y=ACTORS.merchant.y;
 const next=sellPotion(s);
 assert.equal(next.player.silver,12);
 assert.deepEqual(next.inventory,[]);
 assert.equal(s.player.silver,10);
 assert.deepEqual(s.inventory,['回春散']);
});
test('buy-back refuses distant, dialog, combat, missing stock and silver overflow',()=>{
 const base=initialState();base.inventory=['回春散'];
 assert.deepEqual(sellPotion(base),base);
 base.player.x=ACTORS.merchant.x-1;base.player.y=ACTORS.merchant.y;
 base.dialog='对话中';assert.deepEqual(sellPotion(base),base);base.dialog='';
 base.combat={enemyHp:28,enemyMaxHp:28,guard:false};assert.deepEqual(sellPotion(base),base);base.combat=null;
 base.inventory=[];assert.deepEqual(sellPotion(base),base);
 base.inventory=['回春散'];base.player.silver=MAX_SILVER-1;assert.deepEqual(sellPotion(base),base);
});
