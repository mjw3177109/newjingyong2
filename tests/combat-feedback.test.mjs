import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, interact, battle, equipWeapon, attackDamage, attackName, DEMO_SWORD, parseSave} from '../src/engine.js';

// Original HTML5 demo only: these are not source-SWF battle data.
test('unarmed trial combat uses fists in the log and applies 12 damage', () => {
  const s=initialState();
  s.player.x=19;s.player.y=8;
  const fighting=interact(s);
  assert.ok(fighting.combat);
  assert.equal(attackName(fighting),'拳脚');
  assert.equal(attackDamage(fighting),12);
  const next=battle(fighting,'attack');
  assert.equal(next.combat.enemyHp,16);
  assert.match(next.journal.find(line=>line.includes('造成')),/拳脚，造成 12 点伤害/);
  assert.ok(!next.journal.some(line=>line.includes('青竹剑')));
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
  assert.equal(fighting.combat.enemyHp,28,'combat must not mutate input');
});

test('equipped demo sword updates attack name and damage without changing unarmed baseline', () => {
  const s=initialState();
  s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;
  s.inventory=['清心草',DEMO_SWORD];
  const armed=equipWeapon(s);
  assert.equal(attackName(s),'拳脚');
  assert.equal(attackDamage(s),12);
  assert.equal(attackName(armed),'青竹剑');
  assert.equal(attackDamage(armed),16);
  // Synthetic combat-only state: rematches are not yet available in the demo.
  const simulated={...armed,combat:{enemyHp:28,enemyMaxHp:28,guard:false}};
  const result=battle(simulated,'attack');
  assert.equal(result.combat.enemyHp,12);
  assert.match(result.journal.find(line=>line.includes('造成')),/青竹剑，造成 16 点伤害/);
  assert.equal(attackName(equipWeapon(armed)),'拳脚');
});
