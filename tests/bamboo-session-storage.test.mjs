import test from 'node:test';
import assert from 'node:assert/strict';
import {saveBambooSession, loadBambooSession, clearBambooSession, BAMBOO_SESSION_STORAGE_KEY} from '../src/bamboo-session-storage.js';

function memoryStorage() {
  const data = new Map();
  return {
    getItem: key => data.has(key) ? data.get(key) : null,
    setItem: (key, value) => { data.set(key, String(value)); },
    removeItem: key => { data.delete(key); },
  };
}

test('valid original-demo position round-trips without changing V2 saves', () => {
  const storage = memoryStorage();
  const position = {regionId:'bamboo-pass',position:{x:2,y:4}};
  assert.equal(saveBambooSession(storage, position), true);
  assert.deepEqual(loadBambooSession(storage), position);
  assert.equal(clearBambooSession(storage), true);
  assert.equal(loadBambooSession(storage), null);
});

test('invalid positions never overwrite a previous checkpoint', () => {
  const storage = memoryStorage();
  const valid = {regionId:'bamboo-pass',position:{x:2,y:4}};
  assert.equal(saveBambooSession(storage, valid), true);
  assert.equal(saveBambooSession(storage, {regionId:'bamboo-pass',position:{x:4,y:1}}), false);
  assert.deepEqual(loadBambooSession(storage), valid);
});

test('corrupt storage and storage exceptions fail closed', () => {
  const storage = memoryStorage();
  storage.setItem(BAMBOO_SESSION_STORAGE_KEY, '{bad json');
  assert.equal(loadBambooSession(storage), null);
  const broken = {getItem(){throw Error('denied');},setItem(){throw Error('quota');},removeItem(){throw Error('denied');}};
  assert.equal(loadBambooSession(broken), null);
  assert.equal(saveBambooSession(broken, {regionId:'bamboo-pass',position:{x:2,y:4}}), false);
  assert.equal(clearBambooSession(broken), false);
});
