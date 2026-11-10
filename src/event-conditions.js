// Original HTML5 engine infrastructure only. No source-SWF event data.
const OPS = new Set(['eq', 'neq', 'gte', 'lte']);
const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
export function validateCondition(node, depth = 0) {
  try {
    if (!Number.isInteger(depth) || depth < 0 || depth > 12) return false;
    return validateConditionNode(node, depth);
  }
  catch { return false; }
}
function validateConditionNode(node, depth) {
  if (depth > 12 || !node || typeof node !== 'object' || Array.isArray(node)) return false;
  const keys = Object.keys(node);
  if (keys.length === 1 && (keys[0] === 'all' || keys[0] === 'any')) {
    const children = node[keys[0]];
    return Array.isArray(children) && children.length > 0 && children.length <= 32 &&
      // Array#every skips holes: sparse groups must not silently satisfy 'all'.
      Array.from({length: children.length}, (_, i) => own(children, i) &&
        validateCondition(children[i], depth + 1)).every(Boolean);
  }
  if (keys.length === 1 && keys[0] === 'not') return validateCondition(node.not, depth + 1);
  if (keys.length !== 3 || !['path', 'op', 'value'].every(k => own(node, k))) return false;
  if (!Array.isArray(node.path) || node.path.length < 1 || node.path.length > 8 ||
      !node.path.every(k => typeof k === 'string' && /^[a-zA-Z][a-zA-Z0-9_]{0,63}$/.test(k) &&
        !['__proto__', 'constructor', 'prototype'].includes(k))) return false;
  if (!OPS.has(node.op) || !['string', 'number', 'boolean'].includes(typeof node.value) ||
      ((node.op === 'gte' || node.op === 'lte') && typeof node.value !== 'number') ||
      (typeof node.value === 'number' && !Number.isFinite(node.value))) return false;
  return true;
}
export function evaluateCondition(condition, state) {
  const run = node => {
    if (own(node, 'all')) return node.all.every(run);
    if (own(node, 'any')) return node.any.some(run);
    if (own(node, 'not')) return !run(node.not);
    let value = state;
    for (const key of node.path) {
      if (!value || typeof value !== 'object' || !own(value, key)) return false;
      value = value[key];
    }
    if (typeof value !== typeof node.value) return false;
    switch (node.op) {
      case 'eq': return value === node.value;
      case 'neq': return value !== node.value;
      case 'gte': return typeof value === 'number' && Number.isFinite(value) && value >= node.value;
      case 'lte': return typeof value === 'number' && Number.isFinite(value) && value <= node.value;
      default: return false;
    }
  };
  // A condition can be evaluated outside triggerEvent (e.g. dialogue/UI).
  // Imported states may contain throwing getters or proxies; fail closed.
  try { return validateCondition(condition) && run(condition); }
  catch { return false; }
}
