// Pure, original-demo navigation for bamboo pass; no SWF-derived data.
import {validateRegion} from './bamboo-pass.js';
const same=(a,b)=>a.x===b.x&&a.y===b.y;
const inside=(p,r)=>Number.isInteger(p.x)&&Number.isInteger(p.y)&&p.x>=0&&p.y>=0&&p.x<r.width&&p.y<r.height;
export function stepInRegion(region,position,dx,dy){
 if(!validateRegion(region)||!position||!inside(position,region)||!Number.isInteger(dx)||!Number.isInteger(dy)||Math.abs(dx)+Math.abs(dy)!==1)return null;
 const blocked=new Set(region.blocks);
 if(blocked.has(position.x+','+position.y)||same(position,region.npc))return null;
 const next={x:position.x+dx,y:position.y+dy};
 if(!inside(next,region)||blocked.has(next.x+','+next.y)||same(next,region.npc))return null;
 return next;
}
export function regionInteraction(region,position){
 if(!validateRegion(region)||!position||!inside(position,region)||region.blocks.includes(position.x+','+position.y)||same(position,region.npc))return null;
 const distance=Math.abs(position.x-region.npc.x)+Math.abs(position.y-region.npc.y);
 return distance===1?{npcId:region.npc.id,dialog:region.npc.dialog}:null;
}
export function reachedRegionExit(region,position){
 return !!(validateRegion(region)&&position&&inside(position,region)&&same(position,region.exit));
}
