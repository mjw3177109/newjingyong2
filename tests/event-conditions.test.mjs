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

test('condition evaluation fails closed for throwing imported state access', () => {
  const throwingGetter = {get quest() { throw new Error('untrusted getter'); }};
  const throwingProxy = new Proxy({}, {getOwnPropertyDescriptor() { throw new Error('proxy trap'); }});
  assert.equal(evaluateCondition(eq(['quest'], 'active'), throwingGetter), false);
  assert.equal(evaluateCondition(eq(['quest'], 'active'), throwingProxy), false);
  assert.equal(evaluateCondition({all:[eq(['quest'],'active')]}, throwingGetter), false);
  assert.equal(evaluateCondition(eq(['quest'],'active'), state), true);
});

test('condition validation and evaluation fail closed for hostile condition getters', () => {
  const throwingLeaf = {path:['quest'], op:'eq', get value() { throw new Error('condition getter'); }};
  const throwingGroup = {get all() { throw new Error('group getter'); }};
  for (const condition of [throwingLeaf, throwingGroup]) {
    assert.equal(validateCondition(condition), false);
    assert.equal(evaluateCondition(condition, state), false);
  }
});

test('condition evaluation fails closed for hostile condition proxy traps', () => {
  const throwingKeys = new Proxy({}, {ownKeys() { throw new Error('condition ownKeys'); }});
  const throwingDescriptor = new Proxy({path:['quest'], op:'eq', value:'active'}, {
    getOwnPropertyDescriptor() { throw new Error('condition descriptor'); }
  });
  for (const condition of [throwingKeys, throwingDescriptor]) {
    assert.equal(validateCondition(condition), false);
    assert.equal(evaluateCondition(condition, state), false);
  }
  assert.equal(evaluateCondition(eq(['quest'], 'active'), state), true);
});

test('public validation fails closed for cyclic conditions and preserves valid expressions', () => {
  const cyclic = {};
  cyclic.not = cyclic;
  assert.equal(validateCondition(cyclic), false);
  assert.equal(evaluateCondition(cyclic, state), false);
  assert.equal(validateCondition(eq(['quest'], 'active')), true);
});

test('public validation rejects invalid depth arguments without bypassing nesting limit', () => {
  const leaf = eq(['quest'], 'active');
  let nested = leaf;
  for (let i = 0; i < 14; i++) nested = {not:nested};
  assert.equal(validateCondition(nested), false);
  assert.equal(validateCondition(nested, -100), false);
  assert.equal(validateCondition(leaf, -1), false);
  assert.equal(validateCondition(leaf, 1.5), false);
  assert.equal(validateCondition(leaf, NaN), false);
  assert.equal(validateCondition(leaf, 0), true);
  assert.equal(evaluateCondition(nested, state), false);
});

test('numeric comparison thresholds must be finite numbers at validation time', () => {
  for (const op of ['gte', 'lte']) {
    for (const value of ['10', true, false, '0']) {
      const condition = {path:['player','silver'], op, value};
      assert.equal(validateCondition(condition), false);
      assert.equal(evaluateCondition(condition, state), false);
    }
    assert.equal(validateCondition({path:['player','silver'], op, value:10}), true);
  }
});
