// Portable saves for the ORIGINAL HTML5 demonstration, never source-SWF assets.
import {parseSave} from './engine.js';

export const MAX_SAVE_FILE_BYTES = 64 * 1024;
const byteLength = text => new TextEncoder().encode(text).byteLength;

export function exportSaveText(state) {
  const text = JSON.stringify(state);
  if (typeof text !== 'string' || byteLength(text) > MAX_SAVE_FILE_BYTES ||
      !parseSave(text)) throw new Error('Cannot export an invalid demo save');
  return text;
}

export function importSaveText(text) {
  if (typeof text !== 'string' || byteLength(text) > MAX_SAVE_FILE_BYTES) return null;
  return parseSave(text);
}
