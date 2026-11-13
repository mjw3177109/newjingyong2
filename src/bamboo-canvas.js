// Original canvas scene for the independent bamboo-pass demo; no SWF assets.
import {BAMBOO_PASS} from './bamboo-pass.js';
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
 marker(r.exit,'#e9c66f',cell*.29);
 marker(r.npc,'#496d9b',cell*.28);
 marker(session.position,'#f4e1bd',cell*.29);
 ctx.textAlign='left';ctx.font='bold 20px system-ui';ctx.fillStyle='#fff0c9';ctx.fillText(r.name,20,32);
 return true;
}
