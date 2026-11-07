import test from 'node:test';
import assert from 'node:assert/strict';
import {triggerEvent,validateEvent} from '../src/event-trigger.js';
const event={id:'demo_herb',condition:{all:[
  {path:['quest'],op:'eq',value:'active'},
  {path:['player','silver'],op:'gte',value:5}
]},effects:[{path:['quest'],value:'done'},{path:['flags','rewarded'],value:true}]};
const state=()=>({quest:'active',player:{silver:10},flags:{rewarded:false}});
test('atomic event applies once without mutating input',()=>{
  const before=state(),result=triggerEvent(event,before);
  assert.equal(result.applied,true);assert.equal(before.quest,'active');
  assert.equal(result.state.quest,'done');assert.equal(result.state.flags.rewarded,true);
  assert.equal(result.state.eventHistory.demo_herb,true);
  const again=triggerEvent(event,result.state);
  assert.equal(again.applied,false);assert.equal(again.state,result.state);
});
test('failed conditions and absent paths do not partially mutate',()=>{
  const before=state();before.player.silver=4;
  assert.equal(triggerEvent(event,before).applied,false);
  const broken={...event,effects:[event.effects[0],{path:['missing','child'],value:true}]};
  const result=triggerEvent(broken,state());
  assert.equal(result.applied,false);assert.equal(result.state.quest,'active');
});
test('unsafe or malformed event definitions are rejected',()=>{
  for(const bad of [{...event,id:'constructor'},
    {...event,effects:[{path:['eventHistory','x'],value:true}]},
    {...event,effects:[{path:['__proto__'],value:true}]},
    {...event,script:'alert(1)'},
    {...event,effects:[{path:['quest'],value:Infinity}]}]){
    assert.equal(validateEvent(bad),false);
    assert.equal(triggerEvent(bad,state()).applied,false);
  }
});

test('inherited history properties do not block a valid first trigger',()=>{
  const first={...event,id:'toString'};
  const result=triggerEvent(first,state());
  assert.equal(result.applied,true);
  assert.equal(Object.prototype.hasOwnProperty.call(result.state.eventHistory,'toString'),true);
  assert.equal(triggerEvent(first,result.state).applied,false);
});
