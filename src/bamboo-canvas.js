// Original canvas scene for the independent bamboo-pass demo; no SWF assets.
import {BAMBOO_PASS} from './bamboo-pass.js';
import {pathToBambooExit} from './bamboo-exit-path.js';
export function drawBambooPass(ctx,session,canvasWidth=900,canvasHeight=540){
 if(!ctx||session?.regionId!==BAMBOO_PASS.id||!Number.isFinite(canvasWidth)||!Number.isFinite(canvasHeight)||canvasWidth<=0||canvasHeight<=0||!Number.isInteger(session?.position?.x)||!Number.isInteger(session?.position?.y)||session.position.x<0||session.position.y<0||session.position.x>=BAMBOO_PASS.width||session.position.y>=BAMBOO_PASS.height)return false;
 const r=BAMBOO_PASS;
 // Reject impossible session locations before drawing any pixels.
 if(r.blocks.includes(session.position.x+','+session.position.y) ||
    (session.position.x===r.npc.x && session.position.y===r.npc.y))return false;
 const cell=Math.min(canvasWidth/r.width,canvasHeight/r.height);
 if(!Number.isFinite(cell)||cell<=0)return false;
 const ox=(canvasWidth-cell*r.width)/2,oy=(canvasHeight-cell*r.height)/2;
 if(!Number.isFinite(ox)||!Number.isFinite(oy))return false;
 ctx.fillStyle='#193b31';ctx.fillRect(0,0,canvasWidth,canvasHeight);
 const walls=new Set(r.blocks);
 for(let y=0;y<r.height;y++)for(let x=0;x<r.width;x++){
  const X=ox+x*cell,Y=oy+y*cell,blocked=walls.has(x+','+y);
  ctx.fillStyle=blocked?'#35594c':(x+y)%2?'#90af83':'#9bb78a';
  ctx.fillRect(X,Y,cell,cell);
  ctx.strokeStyle='#65866d';ctx.strokeRect(X,Y,cell,cell);
  if(blocked){ctx.fillStyle='#234438';ctx.fillRect(X+cell*.2,Y+cell*.2,cell*.6,cell*.6);}
 }
 const marker=(p,color,radius)=>{ctx.fillStyle=color;ctx.beginPath();ctx.arc(ox+(p.x+.5)*cell,oy+(p.y+.5)*cell,radius,0,Math.PI*2);ctx.fill();};
 // Show the actual walkable shortest route rather than a misleading straight line.
 const exitRoute=pathToBambooExit(session);
 if(exitRoute)for(const step of exitRoute)marker(step,'#f8e6a6',cell*.085);
 // Route status belongs to this canvas too (including fullscreen/embedded views).
 // Never suggest a reachable exit when pathfinding reports no route.
 ctx.textAlign='right';ctx.font='bold 16px system-ui';ctx.fillStyle='#fff0c9';
 ctx.fillText(exitRoute===null?'出口路线不可达':exitRoute.length===0?'已到出口 · 按 E 返回':`距出口 ${exitRoute.length} 步`,canvasWidth-16,30);
 // The first breadcrumb is the next legal step; give keyboard users a direction cue.
 if(exitRoute?.length){
  const step=exitRoute[0],dx=step.x-session.position.x,dy=step.y-session.position.y;
  const direction=dx===1?'右':dx===-1?'左':dy===1?'下':dy===-1?'上':null;
  if(direction){ctx.font='bold 14px system-ui';ctx.fillText(`下一步：${direction}`,canvasWidth-16,52);}
 }
 marker(r.exit,'#e9c66f',cell*.29);
 marker(r.npc,'#496d9b',cell*.28);
 marker(session.position,'#f4e1bd',cell*.29);
 ctx.textAlign='left';ctx.font='bold 20px system-ui';ctx.fillStyle='#fff0c9';ctx.fillText(r.name,20,32);
 return true;
}
