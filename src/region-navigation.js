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

/**
 * Find a shortest walkable route within an original-demo region.
 * Returns coordinates after the starting tile, including the destination.
 * Null means invalid/unreachable; [] means already at the destination.
 * This never reads source-SWF map or event data.
 */
export function shortestRegionRoute(region, start, destination = region?.exit) {
 if (!validateRegion(region) || !start || !destination ||
     !inside(start,region) || !inside(destination,region)) return null;
 const forbidden=new Set(region.blocks);
 const key=p=>p.x+','+p.y;
 forbidden.add(key(region.npc));
 if(forbidden.has(key(start)) || forbidden.has(key(destination))) return null;
 if(same(start,destination)) return [];
 const queue=[start], parents=new Map([[key(start),null]]), positions=new Map([[key(start),start]]);
 for(let i=0;i<queue.length;i++){
   const here=queue[i];
   for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
     const next={x:here.x+dx,y:here.y+dy},k=key(next);
     if(!inside(next,region)||forbidden.has(k)||parents.has(k))continue;
     parents.set(k,key(here));positions.set(k,next);
     if(same(next,destination)){
       const route=[];
       for(let cursor=k;cursor!==key(start);cursor=parents.get(cursor))
         route.push(positions.get(cursor));
       return route.reverse();
     }
     queue.push(next);
   }
 }
 return null;
}
