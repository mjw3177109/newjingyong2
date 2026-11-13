// Optional original-demo checkpoint storage, separate from V2 game saves.
// Callers explicitly provide a Storage-like object; no implicit browser writes.
import {encodeBambooSession, decodeBambooSession} from './bamboo-session-codec.js';

export const BAMBOO_SESSION_STORAGE_KEY = 'newjingyong2:bamboo-session:v1';

export function saveBambooSession(storage, session) {
  const encoded = encodeBambooSession(session);
  if (encoded === null || !storage) return false;
  try {
    if (typeof storage.setItem !== 'function') return false;
    storage.setItem(BAMBOO_SESSION_STORAGE_KEY, encoded);
    // A Storage-like adapter may silently drop writes; only report success on readback.
    return typeof storage.getItem === 'function' && storage.getItem(BAMBOO_SESSION_STORAGE_KEY) === encoded;
  } catch {
    return false;
  }
}

export function loadBambooSession(storage) {
  if (!storage) return null;
  try {
    if (typeof storage.getItem !== 'function') return null;
    return decodeBambooSession(storage.getItem(BAMBOO_SESSION_STORAGE_KEY));
  } catch {
    return null;
  }
}

export function clearBambooSession(storage) {
  if (!storage) return false;
  try {
    if (typeof storage.removeItem !== 'function') return false;
    storage.removeItem(BAMBOO_SESSION_STORAGE_KEY);
    // Some Storage-like adapters silently ignore deletes. Verify removal before
    // allowing callers to reset game state and assume the checkpoint is gone.
    return typeof storage.getItem === 'function' && storage.getItem(BAMBOO_SESSION_STORAGE_KEY) === null;
  } catch {
    return false;
  }
}
