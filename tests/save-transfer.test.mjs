import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, parseSave, SAVE_VERSION} from '../src/engine.js';
import {MAX_SAVE_FILE_BYTES, exportSaveText, importSaveText} from '../src/save-transfer.js';

// Portable saves contain only original-demo state; no source SWF files or assets.
test('portable demo save round-trips without mutating its source state', () => {
  const state = initialState();
  const before = structuredClone(state);
  const exported = exportSaveText(state);
  assert.deepEqual(importSaveText(exported), before);
  assert.deepEqual(state, before);
  assert.equal(JSON.parse(exported).version, SAVE_VERSION);
});

test('import rejects corrupt, oversized and incompatible save files', () => {
  const state = initialState();
  assert.equal(importSaveText('{not json'), null);
  assert.equal(importSaveText(JSON.stringify({...state, version: 999})), null);
  assert.equal(importSaveText('x'.repeat(MAX_SAVE_FILE_BYTES + 1)), null);
  assert.equal(importSaveText(null), null);
});

test('export refuses invalid states rather than creating broken downloads', () => {
  assert.throws(() => exportSaveText({...initialState(), quest: 'completed'}));
  assert.throws(() => exportSaveText({...initialState(), journal: ['x'.repeat(MAX_SAVE_FILE_BYTES)]}));
});

test('portable import supports validated v1 to v2 migration', () => {
  const legacy = initialState();
  legacy.version = 1;
  delete legacy.equipment;
  const expected = parseSave(JSON.stringify(legacy));
  assert.ok(expected);
  assert.deepEqual(importSaveText(JSON.stringify(legacy)), expected);
  assert.equal(expected.version, SAVE_VERSION);
});
