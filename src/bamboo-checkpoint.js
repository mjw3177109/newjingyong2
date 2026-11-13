// Original-demo region session validation for a future checkpoint extension.
// No SWF-derived content; does not change the current v2 save format.
import {BAMBOO_PASS} from './bamboo-pass.js';

export function normalizeBambooCheckpoint(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join(',') !== 'position,regionId') return null;
  if (value.regionId !== BAMBOO_PASS.id) return null;
  const p = value.position;
  if (!p || typeof p !== 'object' || Array.isArray(p) ||
      Object.keys(p).sort().join(',') !== 'x,y' ||
      !Number.isSafeInteger(p.x) || !Number.isSafeInteger(p.y) ||
      p.x < 0 || p.y < 0 || p.x >= BAMBOO_PASS.width || p.y >= BAMBOO_PASS.height ||
      BAMBOO_PASS.blocks.includes(p.x + ',' + p.y) ||
      (p.x === BAMBOO_PASS.npc.x && p.y === BAMBOO_PASS.npc.y)) return null;
  return {regionId:BAMBOO_PASS.id,position:{x:p.x,y:p.y}};
}
