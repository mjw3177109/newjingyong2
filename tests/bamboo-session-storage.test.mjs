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
