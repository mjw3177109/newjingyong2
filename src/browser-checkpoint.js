// Original demo browser checkpoint compatibility layer.
// Legacy strict-v2 saves remain readable; event-aware checkpoints use the
// versioned envelope without adding fields to the strict game schema.
import {parseSave} from './engine.js';
import {packEventSave,unpackEventSave} from './event-save-adapter.js';

export function encodeCheckpoint(game,eventHistory={}) {
  return packEventSave(game,eventHistory);
}

export function decodeCheckpoint(raw) {
  if(typeof raw!=='string')return null;
  const wrapped=unpackEventSave(raw);
  if(wrapped)return wrapped;
  // Do not downgrade a malformed envelope to a legacy game save.
  let parsed;
  try { parsed=JSON.parse(raw); } catch { return null; }
  if(!parsed || typeof parsed!=='object' || Array.isArray(parsed) ||
     Object.hasOwn(parsed,'format') || Object.hasOwn(parsed,'eventHistory'))return null;
  const game=parseSave(raw);
  return game ? {game,eventHistory:{}} : null;
}
