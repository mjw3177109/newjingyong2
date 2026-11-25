// Portable saves for the ORIGINAL HTML5 demonstration, never source-SWF assets.
import {parseSave} from './engine.js';

export const MAX_SAVE_FILE_BYTES = 64 * 1024;
// UTF-8 encodes each UTF-16 code unit to at least one byte. Reject clearly
// oversized inputs before allocating a potentially huge encoded buffer.
const exceedsLimit = text => text.length > MAX_SAVE_FILE_BYTES ||
  new TextEncoder().encode(text).byteLength > MAX_SAVE_FILE_BYTES;

export function exportSaveText(state) {
  const text = JSON.stringify(state);
  if (typeof text !== 'string' || exceedsLimit(text) ||
      !parseSave(text)) throw new Error('Cannot export an invalid demo save');
  return text;
}

export function importSaveText(text) {
  if (typeof text !== 'string' || exceedsLimit(text)) return null;
  return parseSave(text);
}
