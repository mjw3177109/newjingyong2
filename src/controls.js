// Original HTML5 demo input router; no controls are inferred from the source SWF.
const DIRECTIONS = Object.freeze({
  ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0],
  w: [0, -1], s: [0, 1], a: [-1, 0], d: [1, 0],
});
const COMBAT_ACTIONS = Object.freeze({'1': 'attack', '2': 'guard', '3': 'drink', '4': 'flee'});
const INTERACTIVE_SELECTOR = 'button, input, textarea, select, a, [contenteditable="true"], [role="button"]';

export function commandForKey(event, inCombat = false) {
  if (!event || event.defaultPrevented || event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return null;
  const target = event.target;
  if (target && (target.isContentEditable ||
      ['BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'A'].includes(String(target.tagName || '').toUpperCase()) ||
      (typeof target.closest === 'function' && target.closest(INTERACTIVE_SELECTOR)))) return null;
  if (typeof event.key !== 'string') return null;
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  if (inCombat) {
    if (event.repeat) return null;
    const action = COMBAT_ACTIONS[key];
    return action ? {kind: 'combat', action} : null;
  }
  if (Object.hasOwn(DIRECTIONS, key)) {
    const [dx, dy] = DIRECTIONS[key];
    return {kind: 'move', dx, dy};
  }
  // Holding an action key must not close a dialogue and immediately retrigger it.
  if (event.repeat) return null;
  if (key === 'e' || key === 'Enter' || key === ' ') return {kind: 'interact'};
  if (key === 'h') return {kind: 'potion'};
  if (key === 'g') return {kind: 'route-step'};
  if (key === 'b') return {kind: 'inventory'};
  if (key === 'j') return {kind: 'quest'};
  return null;
}
