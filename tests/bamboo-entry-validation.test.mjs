import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState} from '../src/engine.js';
import {encodeCheckpoint} from '../src/browser-checkpoint.js';
import {decodeBambooEntry} from '../src/bamboo-entry-validation.js';
import {VILLAGE_GATE} from '../src/region-travel.js';
import {MAX_SAVE_FILE_BYTES} from '../src/save-transfer.js';

// Original demo only: these assertions do not describe recovered SWF events.
function entry() {
  const game=initialState();
  game.player.x=VILLAGE_GATE.x;
  game.player.y=VILLAGE_GATE.y;
  return game;
}
test('valid village-gate checkpoint restores its event ledger',()=>{
  const game=entry();
  const raw=encodeCheckpoint(game,{});
  const restored=decodeBambooEntry(raw);
  assert.ok(restored);
  assert.deepEqual(restored.game,game);
  assert.deepEqual(restored.eventHistory,{});
});
test('missing, corrupt and oversized entry checkpoints are rejected',()=>{
  assert.equal(decodeBambooEntry(null),null);
  assert.equal(decodeBambooEntry('{bad'),null);
  assert.equal(decodeBambooEntry('x'.repeat(MAX_SAVE_FILE_BYTES+1)),null);
});
test('entry recovery rejects a checkpoint away from village gate',()=>{
  const game=entry();
  game.player.x=VILLAGE_GATE.x+1;
  assert.equal(decodeBambooEntry(encodeCheckpoint(game)),null);
});
test('entry recovery rejects active combat or dialog checkpoints',()=>{
  const game=entry();
  const combat=structuredClone(game);
  combat.combat={enemyHp:12};
  assert.equal(decodeBambooEntry(encodeCheckpoint(combat)),null);
  const dialog=structuredClone(game);
  dialog.dialog={text:'busy'};
  assert.equal(decodeBambooEntry(encodeCheckpoint(dialog)),null);
});
