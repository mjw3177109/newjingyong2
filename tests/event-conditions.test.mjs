import test from 'node:test';
import assert from 'node:assert/strict';
import {validateCondition, evaluateCondition} from '../src/event-conditions.js';
const state = {quest:'active', flags:{herbTaken:true}, player:{silver:10}};
const eq = (path, value) => ({path, op:'eq', value});
test('declarative event conditions combine flags and numeric requirements', () => {
  const condition = {all:[eq(['quest'],'active'), eq(['flags','herbTaken'],true), {path:['player','silver'],op:'gte',value:5}]};
  assert.equal(validateCondition(condition),true);
  assert.equal(evaluateCondition(condition,state),true);
  assert.equal(evaluateCondition(condition,{...state,player:{silver:4}}),false);
  assert.equal(evaluateCondition({any:[eq(['quest'],'completed'),{not:eq(['flags','herbTaken'],false)}]},state),true);
});
test('missing state fields do not match; negation follows Boolean semantics', () => {
  assert.equal(evaluateCondition(eq(['flags','unknown'],false),state),false);
  assert.equal(evaluateCondition({not:eq(['flags','unknown'],false)},state),true);
});
test('reject malformed and prototype traversal expressions', () => {
  for(const condition of [null, {}, {all:[]}, {any:[eq(['quest'],'active')], extra:1},
    eq(['__proto__'],'x'),eq(['constructor'],'x'), {path:['player','silver'],op:'gte',value:Infinity},
    {path:['quest'],op:'eval',value:'active'}, {path:['quest'],op:'eq',value:'active',script:'evil'}]) {
    assert.equal(validateCondition(condition),false);
    assert.equal(evaluateCondition(condition,state),false);
  }
});
test('numeric comparisons reject mismatched types', () => {
  assert.equal(evaluateCondition({path:['quest'],op:'gte',value:1},state),false);
  assert.equal(evaluateCondition({path:['player','silver'],op:'lte',value:10},state),true);
});
