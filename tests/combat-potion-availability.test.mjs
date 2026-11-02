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
