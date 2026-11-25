import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent} from '../src/event-trigger.js';

// Original Q-style demo only; not a decoded event from jin.swf.
const reward={
  id:'demo_save_roundtrip_reward',
  condition:{path:['quest'],op:'eq',value:'active'},
  effects:[{path:['quest'],value:'done'},{path:['wallet','coins'],value:20}]
};

test('event completion survives JSON save/load and cannot pay twice',()=>{
  const initial={quest:'active',wallet:{coins:0},eventHistory:{}};
  const first=triggerEvent(reward,initial);
  assert.equal(first.applied,true);
  assert.equal(first.state.wallet.coins,20);
  const loaded=JSON.parse(JSON.stringify(first.state));
  assert.equal(loaded.eventHistory.demo_save_roundtrip_reward,true);
  const replay=triggerEvent(reward,loaded);
  assert.equal(replay.applied,false);
  assert.equal(replay.state,loaded);
  assert.equal(loaded.wallet.coins,20);
  assert.equal(initial.wallet.coins,0);
});

test('independent saves do not share completion ledgers',()=>{
  const a={quest:'active',wallet:{coins:0},eventHistory:{}};
  const b=JSON.parse(JSON.stringify(a));
  const awarded=triggerEvent(reward,a);
  assert.equal(awarded.applied,true);
  assert.equal(triggerEvent(reward,b).applied,true);
  assert.deepEqual(a.eventHistory,{});
  assert.deepEqual(b.eventHistory,{});
});
