// Original demo infrastructure only. Keep the strict v2 game save unchanged.
// This adapter stores event replay metadata in a separate, versioned envelope.
import {parseSave} from './engine.js';
import {triggerEvent} from './event-trigger.js';

const ID = /^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/;
const FORBIDDEN = new Set(['__proto__', 'constructor', 'prototype']);
const validHistory = h => h && typeof h === 'object' && !Array.isArray(h) &&
  Object.getPrototypeOf(h) === Object.prototype &&
  Object.keys(h).length <= 256 &&
  Object.keys(h).every(k => ID.test(k) && !FORBIDDEN.has(k) && h[k] === true);

export function packEventSave(gameState, eventHistory = {}) {
  if (!parseSave(JSON.stringify(gameState)) || !validHistory(eventHistory)) return null;
  return JSON.stringify({format:'demo-event-envelope',version:1,game:gameState,eventHistory});
}

export function unpackEventSave(raw) {
  let data;
  try { data = JSON.parse(raw); } catch { return null; }
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).sort().join(',') !== 'eventHistory,format,game,version' ||
      data.format !== 'demo-event-envelope' || data.version !== 1 ||
      !validHistory(data.eventHistory)) return null;
  const game = parseSave(JSON.stringify(data.game));
  if (!game) return null;
  return {game, eventHistory: data.eventHistory};
}

// Execute against a disposable projection; only commit a result that still
// satisfies the exact demo v2 save schema. Never inject eventHistory into game.
export function applySavedEvent(event, game, eventHistory = {}) {
  const packed = packEventSave(game, eventHistory);
  if (!packed) return {applied:false,game,eventHistory};
  const projection = {...game,eventHistory};
  const result = triggerEvent(event,projection);
  if (!result.applied) return {applied:false,game,eventHistory};
  const {eventHistory:nextHistory,...nextGame} = result.state;
  if (!packEventSave(nextGame,nextHistory))
    return {applied:false,game,eventHistory};
  return {applied:true,game:nextGame,eventHistory:nextHistory};
}
