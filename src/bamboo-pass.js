// Original Q-style demo region design, not extracted from jin.swf.
// This module is intentionally independent of the existing save schema until
// region transitions and legacy-save migration are implemented and tested.
export const BAMBOO_PASS = Object.freeze({
  id: 'bamboo-pass',
  name: '竹风山径',
  width: 12,
  height: 9,
  entry: Object.freeze({x: 1, y: 4}),
  exit: Object.freeze({x: 10, y: 4}),
  blocks: Object.freeze(['4,1','4,2','4,3','7,5','7,6','7,7']),
  npc: Object.freeze({id:'pass-keeper',name:'守径人',x:6,y:3,dialog:'山路曲折，沿石阶向东可到竹风亭。'}),
});
export function validateRegion(region) {
  if(!region || !Number.isInteger(region.width) || !Number.isInteger(region.height) || region.width<3 || region.height<3)return false;
  const inside=p=>p && Number.isInteger(p.x) && Number.isInteger(p.y) && p.x>=0 && p.y>=0 && p.x<region.width && p.y<region.height;
  if(!inside(region.entry)||!inside(region.exit)||!inside(region.npc)||!Array.isArray(region.blocks))return false;
  const blocked=new Set(region.blocks);
  if(blocked.size!==region.blocks.length || [...blocked].some(v=>typeof v!=='string'||!/^(0|[1-9]\d*),(0|[1-9]\d*)$/.test(v)))return false;
  if([...blocked].some(v=>{const [x,y]=v.split(',').map(Number);return !inside({x,y});}))return false;
  const key=p=>p.x+','+p.y;
  if([region.entry,region.exit,region.npc].some(p=>blocked.has(key(p))))return false;
  if(key(region.entry)===key(region.exit)||key(region.entry)===key(region.npc)||key(region.exit)===key(region.npc))return false;
  const visited=new Set([key(region.entry)]),queue=[region.entry];
  for(let i=0;i<queue.length;i++){
    const p=queue[i];
    for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
      const next={x:p.x+dx,y:p.y+dy},k=key(next);
      if(inside(next)&&!blocked.has(k)&&k!==key(region.npc)&&!visited.has(k)){visited.add(k);queue.push(next);}
    }
  }
  return visited.has(key(region.exit)) && [[1,0],[-1,0],[0,1],[0,-1]].some(([dx,dy])=>visited.has(key({x:region.npc.x+dx,y:region.npc.y+dy})));
}
