import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, canDrinkPotion, battle, parseSave} from '../src/engine.js';

// Original HTML5 demonstration only; no original-SWF combat semantics inferred.
function fighting() {
  const s=initialState();
  s.quest='active';
  s.player.x=19;s.player.y=8;
  s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
  return s;
}

test('combat potion is unavailable without a potion, at full HP, or outside battle',()=>{
  const s=fighting();
  assert.equal(canDrinkPotion(s),false);
  s.inventory=['回春散'];
  assert.equal(canDrinkPotion(s),false,'full HP cannot consume medicine');
  s.player.hp=70;
  assert.equal(canDrinkPotion(s),true);
  s.combat=null;
  assert.equal(canDrinkPotion(s),false,'field medicine is a separate action');
  assert.equal(canDrinkPotion(null),false);
});

test('available combat potion consumes one item, heals and advances exactly one enemy turn',()=>{
  const s=fighting();
  s.player.hp=70;
  s.inventory=['回春散'];
  assert.equal(canDrinkPotion(s),true);
  assert.deepEqual(parseSave(JSON.stringify(s)),s);
  const next=battle(s,'drink');
  assert.equal(next.player.hp,94,'heal 30, then suffer one 6-point counterattack');
  assert.equal(next.inventory.length,0);
  assert.equal(canDrinkPotion(next),false);
  assert.equal(s.player.hp,70,'input state must remain unchanged');
  assert.deepEqual(parseSave(JSON.stringify(next)),next);
});

test('direct invalid combat drink is a complete no-op with full HP or no medicine',()=>{
  for(const [hp,inventory] of [[100,['回春散']],[70,[]]]) {
    const s=fighting();
    s.player.hp=hp;
    s.inventory=inventory;
    s.combat.guard=true;
    s.journal=['原有战斗记录'];
    assert.equal(canDrinkPotion(s),false);
    const before=structuredClone(s);
    const next=battle(s,'drink');
    assert.deepEqual(next,before,'no new journal, no enemy counterattack, no guard or item change');
    assert.deepEqual(s,before,'the input state must stay untouched');
    assert.deepEqual(parseSave(JSON.stringify(next)),next,'unchanged state remains a valid checkpoint');
  }
});
