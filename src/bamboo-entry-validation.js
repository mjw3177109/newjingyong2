// Original-demo region entry validation. Never interpret this as jin.swf story evidence.
import {decodeCheckpoint} from './browser-checkpoint.js';
import {MAX_SAVE_FILE_BYTES} from './save-transfer.js';
import {VILLAGE_GATE} from './region-travel.js';

export function decodeBambooEntry(raw) {
  if (typeof raw !== 'string') return null;
  try {
    if (new TextEncoder().encode(raw).byteLength > MAX_SAVE_FILE_BYTES) return null;
    const checkpoint = decodeCheckpoint(raw);
    if (!checkpoint || checkpoint.game.combat || checkpoint.game.dialog) return null;
    const {x,y} = checkpoint.game.player;
    return x === VILLAGE_GATE.x && y === VILLAGE_GATE.y ? checkpoint : null;
  } catch {
    return null;
  }
}
