// Original HTML5 engine infrastructure; no source-SWF event data.
import {validateCondition, evaluateCondition} from './event-conditions.js';
const own = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
const safePath = p => Array.isArray(p) && p.length >= 1 && p.length <= 8 &&
  p.every(k => typeof k === 'string' && /^[a-zA-Z][a-zA-Z0-9_]{0,63}$/.test(k) &&
    !['__proto__','constructor','prototype'].includes(k));
const scalar = v => ['string','boolean','number'].includes(typeof v) &&
  (typeof v !== 'number' || Number.isFinite(v));
export function validateEvent(e) {
  return !!e && typeof e === 'object' && !Array.isArray(e) &&
    Object.keys(e).sort().join(',') === 'condition,effects,id' &&
    typeof e.id === 'string' && /^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(e.id) &&
    !['__proto__','constructor','prototype'].includes(e.id) &&
    validateCondition(e.condition) && Array.isArray(e.effects) &&
    e.effects.length > 0 && e.effects.length <= 16 &&
    e.effects.every(x => x && typeof x === 'object' && !Array.isArray(x) &&
      Object.keys(x).sort().join(',') === 'path,value' &&
      safePath(x.path) && x.path[0] !== 'eventHistory' && scalar(x.value));
}
export function triggerEvent(event,state) {
  if (!validateEvent(event) || !state || typeof state !== 'object' || Array.isArray(state))
    return {applied:false,state};
  // Legacy in-memory states can expose throwing accessors or proxies.
  // Reject them without crashing a dialogue/quest handler or mutating state.
  let history, conditionMet;
  try {
    history = own(state,'eventHistory') ? state.eventHistory : {};
    if (!history || typeof history !== 'object' || Array.isArray(history) ||
        ![Object.prototype, null].includes(Object.getPrototypeOf(history)) ||
        Object.keys(history).some(k => !/^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(k) ||
          ['__proto__','constructor','prototype'].includes(k) || history[k] !== true) ||
        own(history,event.id)) return {applied:false,state};
    conditionMet = evaluateCondition(event.condition,state);
  } catch { return {applied:false,state}; }
  if (!conditionMet) return {applied:false,state};
  for (const effect of event.effects) {
    let cursor=state;
    for (const key of effect.path.slice(0,-1)) {
      if (!cursor || typeof cursor !== 'object' || Array.isArray(cursor) ||
          !own(cursor,key) || !cursor[key] || typeof cursor[key] !== 'object' ||
          Array.isArray(cursor[key])) return {applied:false,state};
      cursor=cursor[key];
    }
    // Do not silently create arbitrary state fields from malformed event data.
    if (!own(cursor, effect.path.at(-1))) return {applied:false,state};
  }
  // Reject overlapping write targets: an earlier effect may replace an object
  // required by a later effect, otherwise causing a partial/throwing transaction.
  for (let i=0;i<event.effects.length;i++) {
    const a=event.effects[i].path;
    for (let j=i+1;j<event.effects.length;j++) {
      const b=event.effects[j].path;
      const n=Math.min(a.length,b.length);
      if (a.slice(0,n).every((key,k)=>key===b[k]))
        return {applied:false,state};
    }
  }
  // Imported or legacy state may contain values that cannot be cloned.
  // Reject safely rather than throwing midway through a quest interaction.
  let next;
  try { next=structuredClone(state); }
  catch { return {applied:false,state}; }
  for (const effect of event.effects) {
    let cursor=next;
    for (const key of effect.path.slice(0,-1)) cursor=cursor[key];
    cursor[effect.path.at(-1)]=effect.value;
  }
  next.eventHistory={...history,[event.id]:true};
  return {applied:true,state:next};
}
