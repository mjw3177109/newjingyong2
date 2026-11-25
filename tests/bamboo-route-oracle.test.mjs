// Independent region-router oracle for original demo map (not SWF evidence).
import test from 'node:test';
import assert from 'node:assert/strict';
import {BAMBOO_PASS} from '../src/bamboo-pass.js';
import {shortestRegionRoute} from '../src/region-navigation.js';
import {pathToBambooTile} from '../src/bamboo-exit-path.js';

const session = position => ({regionId:BAMBOO_PASS.id, position});
const occupied = new Set([...BAMBOO_PASS.blocks, BAMBOO_PASS.npc.x+','+BAMBOO_PASS.npc.y]);
const inside = p => p.x>=0 && p.y>=0 && p.x<BAMBOO_PASS.width && p.y<BAMBOO_PASS.height;
const walkable = p => inside(p) && !occupied.has(p.x+','+p.y);
const manhattan = (a,b) => Math.abs(a.x-b.x)+Math.abs(a.y-b.y);

test('bamboo BFS matches independent region shortest distance for every walkable pair', () => {
  const tiles = [];
  for (let y=0;y<BAMBOO_PASS.height;y++) for (let x=0;x<BAMBOO_PASS.width;x++) {
    if (walkable({x,y})) tiles.push({x,y});
  }
  for (const start of tiles) for (const destination of tiles) {
    const expected = shortestRegionRoute(BAMBOO_PASS,start,destination);
    const actual = pathToBambooTile(session(start),destination.x,destination.y);
    assert.equal(actual?.length,expected?.length,JSON.stringify({start,destination}));
    if (actual) {
      let previous=start;
      for (const next of actual) {
        assert.ok(walkable(next));
        assert.equal(manhattan(previous,next),1);
        previous=next;
      }
      assert.deepEqual(previous,destination);
    }
  }
});

test('NPC approach has shortest possible safe length for each starting tile', () => {
  const npc = BAMBOO_PASS.npc;
  const neighbors = [[1,0],[-1,0],[0,1],[0,-1]]
    .map(([dx,dy])=>({x:npc.x+dx,y:npc.y+dy})).filter(walkable);
  for(let y=0;y<BAMBOO_PASS.height;y++) for(let x=0;x<BAMBOO_PASS.width;x++){
    const start={x,y};
    if(!walkable(start))continue;
    const lengths=neighbors.map(p=>shortestRegionRoute(BAMBOO_PASS,start,p)?.length)
      .filter(v=>v!==undefined);
    const route=pathToBambooTile(session(start),npc.x,npc.y);
    assert.equal(route?.length,lengths.length?Math.min(...lengths):undefined);
    if(route?.length)assert.equal(manhattan(route.at(-1),npc),1);
  }
});
