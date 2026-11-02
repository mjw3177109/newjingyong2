import {initialState,move,interact,battle,questStatus,equipWeapon,attackDamage,DEMO_SWORD,discardPotion,usePotion} from './engine.js';
import {ACTORS,WIDTH,HEIGHT,TILE,BLOCKS} from './demo-data.js';
import {commandForKey} from './controls.js';
import {MAX_SAVE_FILE_BYTES, exportSaveText, importSaveText} from './save-transfer.js';
import {nextObjective,pathToObjective,stepTowardObjective} from './objectives.js';
import {pathToTile} from './tile-path.js';
let state=initialState();
const $=id=>document.getElementById(id), canvas=$('game'),ctx=canvas.getContext('2d');
const images={};
for(const id of ['hero','elder','merchant','herb','bandit']){
 const img=new Image();img.src=`./assets/${id}.svg`;img.onload=()=>paint();images[id]=img;
}
const keyName = 'jianghu-q-save-v1';
function toast(txt){const t=$('toast');t.textContent=txt;t.classList.remove('hidden');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.add('hidden'),1800);}
function update(next){state=next;paint();}
function save(){try{localStorage.setItem(keyName,exportSaveText(state));toast('进度已存入本机浏览器');}catch{toast('存档无效或浏览器存储不可用');}}
function load(){let raw;try{raw=localStorage.getItem(keyName);}catch{toast('浏览器存储不可用');return;}
 // Apply the same UTF-8 byte cap as portable JSON imports before parsing local data.
 if(raw && new TextEncoder().encode(raw).byteLength>MAX_SAVE_FILE_BYTES){toast('本机存档超过 64 KB，已拒绝读取');return;}
 const parsed=raw&&importSaveText(raw);if(!parsed){toast('没有有效的存档');return;}
 // Loading a checkpoint must not silently destroy unsaved progress.
 const questLabel={unstarted:'未开始',active:'进行中',completed:'已完成'}[parsed.quest];
 const preview=`即将读取本机存档：任务${questLabel}，气血 ${parsed.player.hp}，银两 ${parsed.player.silver}。\n这会替换当前未保存的游戏进度，但不会删除或修改本机存档。确定继续？`;
 if(!window.confirm(preview)){toast('已取消读取，当前进度未变');return;}
 update(parsed);toast('进度读取成功');}
// Reset both in-memory progress and this browser's saved checkpoint only after consent.
// If storage is blocked, keep the current run rather than leaving a stale save.
function newGame(){
 if(!window.confirm('确定重新开始原创试玩并清除本机存档？此操作无法撤销。'))return;
 try{localStorage.removeItem(keyName);}catch{toast('无法清除本机存档，未重新开始');return;}
 update(initialState());toast('已重新开始原创试玩');
}
function doMove(dx,dy){update(move(state,dx,dy));}
function action(){update(interact(state));}
// Mouse and touch taps move only one legal tile; they never auto-trigger dialogue or combat.
canvas.addEventListener('click', event => {
 if(state.dialog || state.combat)return;
 const rect=canvas.getBoundingClientRect();
 if(rect.width<=0 || rect.height<=0)return;
 const tx=Math.floor((event.clientX-rect.left)*WIDTH/rect.width);
 const ty=Math.floor((event.clientY-rect.top)*HEIGHT/rect.height);
 const route=pathToTile(state,tx,ty);
 if(!route?.length)return;
 const first=route[0];
 update(move(state,first.x-state.player.x,first.y-state.player.y));
});
document.addEventListener('keydown',e=>{
 const command=commandForKey(e,!!state.combat,!!state.dialog);
 if(!command)return;
 e.preventDefault();
 if(command.kind==='move')doMove(command.dx,command.dy);
 else if(command.kind==='interact')action();
 else if(command.kind==='dismiss-dialog')action();
 else if(command.kind==='potion')update(usePotion(state));
 else if(command.kind==='route-step')update(stepTowardObjective(state));
 else if(command.kind==='combat')update(battle(state,command.action));
 else if(command.kind==='inventory')toast(`背包：${state.inventory.join('、')||'空空如也'}`);
 else if(command.kind==='quest')toast(questStatus(state).progress);
});
function exportSave() {
 try {
  const blob = new Blob([exportSaveText(state)], {type:'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = 'zhuying-jianghu-save-v2.json';
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('已导出原创试玩存档 JSON');
 } catch { toast('存档导出失败'); }
}
$('interact').onclick=action;$('save').onclick=save;$('load').onclick=load;
$('new-game').onclick=newGame;
$('export-save').onclick=exportSave;
$('import-save').onclick=()=>$('import-save-file').click();
$('import-save-file').onchange=async e=>{
 const file=e.target.files?.[0];e.target.value='';
 if(!file)return;
 if(file.size>MAX_SAVE_FILE_BYTES){toast('存档文件超过 64 KB');return;}
 try {
  const imported=importSaveText(await file.text());
  if(!imported){toast('存档文件无效或版本不兼容');return;}
  const questLabel={unstarted:'未开始',active:'进行中',completed:'已完成'}[imported.quest];
  const preview=`即将导入存档：任务${questLabel}，气血 ${imported.player.hp}，银两 ${imported.player.silver}。\n这会替换当前未保存的游戏进度，但不会自动覆盖本机存档。确定继续？`;
  if(!window.confirm(preview)){toast('已取消导入，当前进度未变');return;}
  update(imported);
  toast('已导入当前游戏，请点击保存进度以持久化');
 } catch { toast('读取存档文件失败'); }
};
$('step-route').onclick=()=>update(stepTowardObjective(state));
$('equip-weapon').onclick=()=>update(equipWeapon(state));
$('discard-potion').onclick=()=>update(discardPotion(state));
$('use-potion').onclick=()=>update(usePotion(state));
for(const a of ['attack','guard','drink','flee'])$(a).onclick=()=>update(battle(state,a));
for(const b of document.querySelectorAll('[data-direction]')) b.onclick=()=>{const d={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]}[b.dataset.direction];doMove(...d);};
function poly(points,fill){ctx.beginPath();ctx.moveTo(...points[0]);for(const p of points.slice(1))ctx.lineTo(...p);ctx.closePath();ctx.fillStyle=fill;ctx.fill();}
function tile(x,y){
 const X=x*TILE,Y=y*TILE,v=(x*17+y*31)%7;
 ctx.fillStyle=v<3?'#88ab84':v<5?'#8eae86':'#94b28b';ctx.fillRect(X,Y,TILE,TILE);
 if((x+y*3)%6===0){ctx.fillStyle='#6b9771';ctx.beginPath();ctx.ellipse(X+8,Y+19,2,7,.5,0,Math.PI*2);ctx.fill();}
 if((x*7+y*11)%9===0){ctx.fillStyle='#d7d09d';ctx.fillRect(X+26,Y+29,3,2);}
}
function roof(x,y,w,h){const X=x*TILE,Y=y*TILE,W=w*TILE,H=h*TILE;
 ctx.fillStyle='#ccbb91';ctx.fillRect(X+4,Y+H-4,W-8,10);
 ctx.fillStyle='#e8d3a4';ctx.fillRect(X+12,Y+30,W-24,H-31);
 poly([[X-9,Y+34],[X+W/2,Y-11],[X+W+9,Y+34]],'#425e58');
 poly([[X+2,Y+30],[X+W/2,Y],[X+W-2,Y+30]],'#587269');
 ctx.strokeStyle='#f0db9b';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(X+2,Y+34);ctx.lineTo(X+W-2,Y+34);ctx.stroke();
 ctx.fillStyle='#5d7160';ctx.fillRect(X+W/2-11,Y+H-25,22,25);
}
function drawTree(x,y,scale=1){const X=x*TILE,Y=y*TILE;
 ctx.fillStyle='#536147';ctx.fillRect(X+13*scale,Y+15*scale,8*scale,19*scale);
 for(const [ox,oy,r] of [[16,12,15],[4,17,11],[27,18,11]]){ctx.beginPath();ctx.fillStyle=(ox===4?'#497c61':'#47795c');ctx.arc(X+ox*scale,Y+oy*scale,r*scale,0,Math.PI*2);ctx.fill();}
 ctx.beginPath();ctx.fillStyle='#7fae78';ctx.arc(X+11*scale,Y+9*scale,9*scale,0,Math.PI*2);ctx.fill();
}
function actor(id,x,y,size=55){const im=images[id],X=x*TILE+TILE/2,Y=y*TILE+TILE/2;
 ctx.fillStyle='#274b4160';ctx.beginPath();ctx.ellipse(X,Y+16,18,5,0,0,Math.PI*2);ctx.fill();
 if(im?.complete&&im.naturalWidth)ctx.drawImage(im,X-size/2,Y-size*.8,size,size);
 else {ctx.fillStyle='#ffedc1';ctx.beginPath();ctx.arc(X,Y-9,13,0,Math.PI*2);ctx.fill();}
}
function paint(){
 ctx.clearRect(0,0,900,540);
 for(let y=0;y<HEIGHT;y++)for(let x=0;x<WIDTH;x++)tile(x,y);
 // Hand-authored scene geography; original visual geometry, not Flash-exported tiles.
 for(let x=0;x<WIDTH;x++)for(let y=0;y<HEIGHT;y++) if((x+y*2)%5===0){ctx.fillStyle='#a1b991';ctx.fillRect(x*TILE+3,y*TILE+3,2,3);}
 // stone path crossing the village
 for(let x=0;x<WIDTH;x++)for(let y=0;y<HEIGHT;y++)if((y>=6&&y<=8)||(x>=9&&x<=11)){ctx.fillStyle=(x*13+y*3)%3===0?'#d6c3a2':'#d9c6aa';ctx.fillRect(x*TILE,y*TILE,TILE,TILE);ctx.strokeStyle='#c4b18e';ctx.strokeRect(x*TILE,y*TILE,TILE,TILE);}
 roof(2,2,3,2);roof(13,2,3,2);roof(21,10,3,2);
 for(const [x,y] of [[0,1],[1,5],[4,0],[8,2],[19,1],[22,3],[24,6],[18,12],[6,13],[0,10]])drawTree(x,y);
 ctx.fillStyle='#486b5c';ctx.fillRect(11*TILE,0,3,12);ctx.fillStyle='#bfd3a0';ctx.fillRect(11*TILE+3,0,3,12);
 for(const [id,obj] of Object.entries(ACTORS)){
  if(id==='herb'&&state.flags.herbTaken||id==='bandit'&&state.flags.banditBeaten)continue;
  actor(id,obj.x,obj.y,id==='herb'?37:56);
  if(id==='elder'||id==='merchant'){ctx.font='bold 13px system-ui';ctx.fillStyle='#19392e';ctx.textAlign='center';ctx.fillText(obj.name,obj.x*TILE+18,obj.y*TILE-22);}
  if(id==='herb') {ctx.font='20px serif';ctx.fillStyle='#f3e1a8';ctx.fillText('✧',obj.x*TILE+12,obj.y*TILE-18);}
 }
 // Original demo-only objective indicator; not a reconstructed SWF quest marker.
 const objective=nextObjective(state);
 const route=pathToObjective(state);
 if(objective){
  const cx=(objective.x+.5)*TILE,cy=(objective.y+.5)*TILE;
  ctx.beginPath();ctx.strokeStyle='#ffe2a0';ctx.lineWidth=3;
  ctx.arc(cx,cy,25,0,Math.PI*2);ctx.stroke();
 }
 // Walkable shortest-path markers stop next to the target, never on the actor.
 if(route?.length){
  for(const [i,step] of route.entries()){
   const x=(step.x+.5)*TILE,y=(step.y+.5)*TILE;
   ctx.beginPath();ctx.fillStyle=i===route.length-1?'#f6d88a':'#f4e8b7';
   ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
  }
 }
 actor('hero',state.player.x,state.player.y,59);
 ctx.textAlign='left';ctx.fillStyle='#17362b';ctx.font='bold 14px system-ui';ctx.fillText('青 竹 村',18,27);
 const d=$('dialog');d.textContent=state.dialog?state.dialog+'　[按 E 或 Esc 关闭]':'';d.classList.toggle('hidden',!state.dialog);
 const c=$('combat');c.classList.toggle('hidden',!state.combat);
 if(state.combat)$('combat-info').textContent=`试炼者气血 ${state.combat.enemyHp}/${state.combat.enemyMaxHp}　｜　少侠气血 ${state.player.hp}/100`;
 $('attack-num').textContent=attackDamage(state);
 $('discard-potion').disabled=!state.inventory.includes('回春散')||!!state.combat||!!state.dialog;
 $('use-potion').disabled=!state.inventory.includes('回春散')||state.player.hp>=state.player.maxHp||!!state.combat||!!state.dialog;
 const equip=$('equip-weapon');equip.disabled=!state.inventory.includes(DEMO_SWORD)||!!state.combat||!!state.dialog;
 equip.textContent=state.equipment.weapon===DEMO_SWORD?'卸下竹纹短剑':'装备竹纹短剑（攻击 +4）';
 $('hp-num').textContent=`${state.player.hp} / 100`;$('hp-bar').style.width=state.player.hp+'%';$('silver').textContent=state.player.silver;
 const q=questStatus(state);
 $('step-route').disabled=!!state.dialog||!!state.combat||!route?.length;
 const routeHint=!objective?'':route===null?'（路径暂不可达）':route.length===0?'（已靠近，按 E 交互）':`（沿金色路标 ${route.length} 步）`;
 $('quest-title').textContent=q.title;$('quest-desc').textContent=q.description+(objective?`　下一步：${objective.label}${routeHint}`:'');$('quest-progress').textContent=q.progress;
 const inv=$('inventory');inv.replaceChildren();for(const item of state.inventory){const b=document.createElement('span');b.className='item';b.textContent=item;inv.appendChild(b);}if(!state.inventory.length){const n=document.createElement('span');n.className='empty';n.textContent='暂无物品';inv.appendChild(n);}
 const j=$('journal');j.replaceChildren();for(const note of state.journal){const p=document.createElement('p');p.textContent=note;j.appendChild(p);}
}
paint();
