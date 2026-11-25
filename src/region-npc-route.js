// Original-demo NPC approach planner; not derived from jin.swf.
// One breadth-first traversal; preserve destination and path tie-breaking.
import {validateRegion} from './bamboo-pass.js';

export function routeToRegionNpc(region, start) {
  if (!validateRegion(region) || !start) return null;
  const inside=p=>Number.isInteger(p.x)&&Number.isInteger(p.y)&&p.x>=0&&p.y>=0&&p.x<region.width&&p.y<region.height;
  const key=p=>p.x+','+p.y;
  const blocked=new Set(region.blocks);
  blocked.add(key(region.npc));
  if(!inside(start)||blocked.has(key(start))) return null;
  const {x,y}=region.npc;
  const candidates=[[0,-1],[-1,0],[1,0],[0,1]].map(([dx,dy])=>({x:x+dx,y:y+dy})).filter(p=>inside(p)&&!blocked.has(key(p)));
  const targets=new Set(candidates.map(key));
  const queue=[start], parents=new Map([[key(start),null]]), distances=new Map([[key(start),0]]);
  let bestDistance=Infinity;
  for(let i=0;i<queue.length;i++){
    const here=queue[i], k=key(here), d=distances.get(k);
    if(d>bestDistance) break;
    if(targets.has(k)) bestDistance=d;
    if(d>=bestDistance) continue;
    for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
      const next={x:here.x+dx,y:here.y+dy}, nk=key(next);
      if(!inside(next)||blocked.has(nk)||parents.has(nk)) continue;
      parents.set(nk,k); distances.set(nk,d+1); queue.push(next);
    }
  }
  const best=candidates.find(p=>distances.get(key(p))===bestDistance);
  if(!best) return null;
  const route=[];
  for(let cursor=key(best);cursor!==key(start);cursor=parents.get(cursor)){
    const [x,y]=cursor.split(',').map(Number); route.push({x,y});
  }
  return route.reverse();
}
