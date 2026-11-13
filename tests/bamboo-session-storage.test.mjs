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

test('silent or altered writes must not be reported as successful', () => {
  const valid = {regionId:'bamboo-pass',position:{x:2,y:4}};
  const dropped = {setItem(){},getItem(){return null;}};
  assert.equal(saveBambooSession(dropped, valid), false);
  const altered = {setItem(){},getItem(){return '{}';}};
  assert.equal(saveBambooSession(altered, valid), false);
  const noReadback = {setItem(){}};
  assert.equal(saveBambooSession(noReadback, valid), false);
});

test('silent, altered, or unreadable deletes cannot claim a cleared checkpoint', () => {
  const key = BAMBOO_SESSION_STORAGE_KEY;
  const retained = {getItem: () => '{"still":"present"}', removeItem() {}};
  assert.equal(clearBambooSession(retained), false);
  const unreadable = {removeItem() {}};
  assert.equal(clearBambooSession(unreadable), false);
  const altered = {getItem: () => '{}', removeItem() {}};
  assert.equal(clearBambooSession(altered), false);
  const empty = {getItem: () => null, removeItem() {}};
  assert.equal(clearBambooSession(empty), true);
  const storage = memoryStorage();
  storage.setItem(key, 'checkpoint');
  assert.equal(clearBambooSession(storage), true);
  assert.equal(storage.getItem(key), null);
});

test('readback exceptions after a write or delete fail closed', () => {
  const valid = {regionId:'bamboo-pass',position:{x:2,y:4}};
  let written = false;
  const writeUnreadable = {
    setItem() { written = true; },
    getItem() { throw Error('read access revoked'); },
  };
  assert.equal(saveBambooSession(writeUnreadable, valid), false);
  assert.equal(written, true);
  let deleted = false;
  const deleteUnreadable = {
    removeItem() { deleted = true; },
    getItem() { throw Error('read access revoked'); },
  };
  assert.equal(clearBambooSession(deleteUnreadable), false);
  assert.equal(deleted, true);
});

test('region operations do not touch an unrelated V2 save key', () => {
  const storage = memoryStorage();
  storage.setItem('newjingyong2:save:v2', 'opaque-v2-save');
  const valid = {regionId:'bamboo-pass',position:{x:2,y:4}};
  assert.equal(saveBambooSession(storage, valid), true);
  assert.equal(clearBambooSession(storage), true);
  assert.equal(storage.getItem('newjingyong2:save:v2'), 'opaque-v2-save');
});


test('storage method failures preserve an existing checkpoint and unrelated save', () => {
  const key = BAMBOO_SESSION_STORAGE_KEY;
  const storage = memoryStorage();
  const valid = {regionId:'bamboo-pass',position:{x:2,y:4}};
  assert.equal(saveBambooSession(storage, valid), true);
  storage.setItem('newjingyong2:save:v2', 'untouched');
  const before = storage.getItem(key);
  const failingWrite = {
    getItem: k => storage.getItem(k),
    setItem() { throw Error('quota exceeded'); },
  };
  assert.equal(saveBambooSession(failingWrite, valid), false);
  const failingDelete = {
    getItem: k => storage.getItem(k),
    removeItem() { throw Error('permission denied'); },
  };
  assert.equal(clearBambooSession(failingDelete), false);
  assert.equal(storage.getItem(key), before);
  assert.equal(storage.getItem('newjingyong2:save:v2'), 'untouched');
});
