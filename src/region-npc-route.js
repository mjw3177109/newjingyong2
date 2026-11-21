// Original-demo NPC approach planner; not derived from jin.swf.
// Choose the shortest walkable route to an adjacent tile, never onto the NPC.
import {shortestRegionRoute} from './region-navigation.js';
import {validateRegion} from './bamboo-pass.js';

export function routeToRegionNpc(region, start) {
  if (!validateRegion(region) || !start) return null;
  const {x,y}=region.npc;
  const candidates=[[0,-1],[-1,0],[1,0],[0,1]]
    .map(([dx,dy])=>({x:x+dx,y:y+dy}));
  let best=null;
  for (const destination of candidates) {
    const route=shortestRegionRoute(region,start,destination);
    if (route!==null && (best===null || route.length<best.length)) best=route;
  }
  return best;
}
