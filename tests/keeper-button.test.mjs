import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const main=readFileSync(new URL('../src/main.js',import.meta.url),'utf8');

test('keeper step button exists for pointer and touch navigation',()=>{
 assert.match(html,/<button id="step-npc" disabled aria-label="向守径人前进一步">/);
 assert.match(main,/\$\('step-npc'\)\.onclick=stepTowardKeeper;/);
});
test('keeper navigation uses the existing guarded single-step movement and disables outside region',()=>{
 assert.match(main,/function stepTowardKeeper\(\)\{[\s\S]*?routeToRegionNpc\(BAMBOO_PASS,bambooSession.position\)/);
 assert.match(main,/doMove\(next.x-bambooSession.position.x,next.y-bambooSession.position.y\)/);
 assert.match(main,/\$\('step-npc'\)\.disabled=!npcRoute\?\.length;/);
 assert.match(main,/\$\('step-npc'\)\.disabled=true;/);
});
