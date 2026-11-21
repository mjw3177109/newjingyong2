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

test('sparse effect lists and property paths fail closed', () => {
  const sparseEffects = new Array(2);
  sparseEffects[1] = {path:['quest'], value:'done'};
  const sparsePath = new Array(2);
  sparsePath[1] = 'quest';
  for (const bad of [
    {...event, effects:sparseEffects},
    {...event, effects:[{path:sparsePath,value:'done'}]}
  ]) {
    assert.equal(validateEvent(bad),false);
    const before=state();
    const result=triggerEvent(bad,before);
    assert.equal(result.applied,false);
    assert.equal(result.state,before);
    assert.equal(before.quest,'active');
  }
});
test('hostile event getters and proxies cannot crash validation', () => {
  const getter={...event,get effects(){throw new Error('bad getter');}};
  const proxy=new Proxy(event,{ownKeys(){throw new Error('bad proxy');}});
  for (const bad of [getter,proxy]) {
    assert.equal(validateEvent(bad),false);
    assert.equal(triggerEvent(bad,state()).applied,false);
  }
  assert.equal(validateEvent(event),true);
});

test('overlapping effect targets are rejected atomically', () => {
  const before=state();
  const overlapping={...event,effects:[
    {path:['flags'],value:'replaced'},
    {path:['flags','rewarded'],value:true}
  ]};
  assert.equal(validateEvent(overlapping),false);
  const result=triggerEvent(overlapping,before);
  assert.equal(result.applied,false);
  assert.equal(result.state,before);
  assert.deepEqual(before.flags,{rewarded:false});
  assert.equal(Object.hasOwn(before,'eventHistory'),false);
});

test('uncloneable imported state fails without partial event application', () => {
  const before={...state(),foreignCallback:()=>{}};
  const result=triggerEvent(event,before);
  assert.equal(result.applied,false);
  assert.equal(result.state,before);
  assert.equal(before.quest,'active');
  assert.equal(before.flags.rewarded,false);
  assert.equal(Object.hasOwn(before,'eventHistory'),false);
});

test('non-record intermediate effect targets are rejected without mutation', () => {
  for (const value of [new Date('2020-01-01T00:00:00Z'), new Map(), new Set()]) {
    const before={...state(),flags:value};
    const result=triggerEvent(event,before);
    assert.equal(result.applied,false);
    assert.equal(result.state,before);
    assert.equal(before.quest,'active');
    assert.equal(Object.hasOwn(before,'eventHistory'),false);
  }
});

test('event definitions reject duplicate and reversed overlapping writes', () => {
  for (const effects of [
    [{path:['quest'],value:'done'},{path:['quest'],value:'other'}],
    [{path:['flags','rewarded'],value:true},{path:['flags'],value:'replaced'}]
  ]) {
    const candidate={...event,effects};
    assert.equal(validateEvent(candidate),false);
    const before=state();
    const result=triggerEvent(candidate,before);
    assert.equal(result.applied,false);
    assert.equal(result.state,before);
    assert.equal(before.quest,'active');
  }
  assert.equal(validateEvent(event),true);
});
