// Original demo-only bamboo session serialization; independent of v2 game saves.
// This module does not alter the existing save schema or claim SWF provenance.
import {normalizeBambooCheckpoint} from './bamboo-checkpoint.js';

export const MAX_BAMBOO_SESSION_BYTES = 256;

export function encodeBambooSession(session) {
  const normalized = normalizeBambooCheckpoint(session);
  if (!normalized) return null;
  return JSON.stringify(normalized);
}

export function decodeBambooSession(text) {
  if (typeof text !== 'string' || new TextEncoder().encode(text).byteLength > MAX_BAMBOO_SESSION_BYTES) return null;
  try {
    return normalizeBambooCheckpoint(JSON.parse(text));
  } catch {
    return null;
  }
}
