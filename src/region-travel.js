// Original demo-only region travel. Runtime state is deliberately separate from V2 saves.
// No source-SWF map or story claims are made by these transitions.
import {BAMBOO_PASS} from './bamboo-pass.js';
import {WIDTH,HEIGHT,BLOCKS,ACTORS} from './demo-data.js';
import {stepInRegion,regionInteraction,reachedRegionExit} from './region-navigation.js';

export const VILLAGE_GATE=Object.freeze({x:24,y:7});
export const VILLAGE_RETURN=Object.freeze({x:23,y:7});
const same=(a,b)=>a?.x===b.x&&a?.y===b.y;
const villageWalkable=p=>!!p&&Number.isInteger(p.x)&&Number.isInteger(p.y)&&
 p.x>=0&&p.x<WIDTH&&p.y>=0&&p.y<HEIGHT&&!BLOCKS.has(p.x+','+p.y)&&
 !Object.values(ACTORS).some(a=>same(a,p));

export function enterBambooPass(game){
 if(!game||game.combat||game.dialog||!villageWalkable(game.player)||!same(game.player,VILLAGE_GATE))return null;
 return {regionId:BAMBOO_PASS.id,position:{...BAMBOO_PASS.entry}};
}
export function moveBambooSession(session,dx,dy){
 if(session?.regionId!==BAMBOO_PASS.id)return null;
 const next=stepInRegion(BAMBOO_PASS,session.position,dx,dy);
 return next?{regionId:BAMBOO_PASS.id,position:next}:null;
}
export function talkBambooSession(session){
 return session?.regionId===BAMBOO_PASS.id?regionInteraction(BAMBOO_PASS,session.position):null;
}
export function leaveBambooPass(session,game){
 if(session?.regionId!==BAMBOO_PASS.id||!reachedRegionExit(BAMBOO_PASS,session.position)||
    !game||game.combat||game.dialog||!villageWalkable(VILLAGE_RETURN))return null;
 // Caller must replace the game state only on successful exit; no save-schema changes.
 return {...game,player:{...game.player,...VILLAGE_RETURN}};
}
