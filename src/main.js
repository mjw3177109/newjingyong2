import {initialState,move,interact,battle,questStatus,equipWeapon,attackDamage,attackName,DEMO_SWORD,discardPotion,sellPotion,usePotion,canRematch,startRematch,canDrinkPotion,canRestAtVillage,restAtVillage} from './engine.js';
import {ACTORS,WIDTH,HEIGHT,TILE,BLOCKS} from './demo-data.js';
import {commandForKey} from './controls.js';
import {MAX_SAVE_FILE_BYTES} from './save-transfer.js';
import {encodeCheckpoint,decodeCheckpoint} from './browser-checkpoint.js';
import {applySavedEvent} from './event-save-adapter.js';
import {nextObjective,pathToObjective,stepTowardObjective} from './objectives.js';
import {pathToTile} from './tile-path.js';
import {enterBambooPass,moveBambooSession,talkBambooSession,leaveBambooPass,VILLAGE_GATE} from './region-travel.js';
import {drawBambooPass} from './bamboo-canvas.js';
import {bambooTileFromPointer} from './bamboo-pointer.js';
import {pathToBambooExit,pathToBambooTile} from './bamboo-exit-path.js';
import {BAMBOO_PASS} from './bamboo-pass.js';
import {routeToRegionNpc} from './region-npc-route.js';
import {saveBambooSession,loadBambooSession,clearBambooSession} from './bamboo-session-storage.js';
import {decodeBambooEntry} from './bamboo-entry-validation.js';
// Optional original-demo region recovery; never changes the V2 save schema.
let bambooSession=loadBambooSession(typeof localStorage==='undefined'?null:localStorage);
let state=initialState();
let eventHistory={};
const $=id=>document.getElementById(id), canvas=$('game'),ctx=canvas.getContext('2d');
const images={};
for(const id of ['hero','elder','merchant','herb','bandit']){
 const img=new Image();img.src=`./assets/${id}.svg`;img.onload=()=>paint();images[id]=img;
}
const keyName = 'jianghu-q-save-v1';
// Private region entry snapshot: independent of the user's manually saved V2 checkpoint.
const bambooEntryKey = 'newjingyong2:bamboo-entry:v1';
function clearBambooEntry(){try{localStorage.removeItem(bambooEntryKey);return localStorage.getItem(bambooEntryKey)===null;}catch{return false;}}
function persistBambooEntry(){
 try{
  const raw=encodeCheckpoint(state,eventHistory);
  if(!raw||new TextEncoder().encode(raw).byteLength>MAX_SAVE_FILE_BYTES)return false;
  localStorage.setItem(bambooEntryKey,raw);
  return localStorage.getItem(bambooEntryKey)===raw;
 }catch{return false;}
}

// A restored bamboo session must retain its matching village gate checkpoint.
// Never trust arbitrary localStorage state or bypass the normal save validator.
if(bambooSession){
 let validEntry=false;
 try{
  const checkpoint=decodeBambooEntry(localStorage.getItem(bambooEntryKey));
  if(checkpoint){
   state=checkpoint.game;
   eventHistory=checkpoint.eventHistory;
   validEntry=true;
  }
 }catch{/* Invalid or unavailable storage must not activate an orphaned region. */}
 // A region session without its validated village entry would otherwise
 // render a playable scene with an unrelated default village checkpoint.
 if(!validEntry){
  // Discard an orphaned region checkpoint as well as its in-memory copy.
  // Otherwise every reload attempts the same invalid recovery indefinitely.
  clearBambooSession(typeof localStorage==='undefined'?null:localStorage);
  bambooSession=null;
 }
}
function toast(txt){const t=$('toast');t.textContent=txt;t.classList.remove('hidden');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.add('hidden'),1800);}
function update(next){state=next;paint();}
function save(){if(bambooSession){toast('请先返回青竹村再保存；山径探索暂不支持存档');return;}try{const raw=encodeCheckpoint(state,eventHistory);if(!raw || new TextEncoder().encode(raw).byteLength>MAX_SAVE_FILE_BYTES)throw new Error('invalid checkpoint');localStorage.setItem(keyName,raw);toast('进度已存入本机浏览器');}catch{toast('存档无效或浏览器存储不可用');}}
function load(){let raw;try{raw=localStorage.getItem(keyName);}catch{toast('浏览器存储不可用');return;}
 // Apply the same UTF-8 byte cap as portable JSON imports before parsing local data.
 if(raw && new TextEncoder().encode(raw).byteLength>MAX_SAVE_FILE_BYTES){toast('本机存档超过 64 KB，已拒绝读取');return;}
 const checkpoint=raw&&decodeCheckpoint(raw);if(!checkpoint){toast('没有有效的存档');return;}
 const parsed=checkpoint.game;
 // Loading a checkpoint must not silently destroy unsaved progress.
 const questLabel={unstarted:'未开始',active:'进行中',completed:'已完成'}[parsed.quest];
 const preview=`即将读取本机存档：任务${questLabel}，气血 ${parsed.player.hp}，银两 ${parsed.player.silver}。\n这会替换当前未保存的游戏进度，但不会删除或修改本机存档。确定继续？`;
 if(!window.confirm(preview)){toast('已取消读取，当前进度未变');return;}
 if(!clearBambooEntry()){toast('无法清除山径入口快照，未读取存档');return;}
 if(!clearBambooSession(localStorage)){toast('无法清除山径记录，未读取存档');return;}
 bambooSession=null;eventHistory=checkpoint.eventHistory;update(parsed);toast('进度读取成功');}
// Reset both in-memory progress and this browser's saved checkpoint only after consent.
// If storage is blocked, keep the current run rather than leaving a stale save.
function newGame(){
 if(!window.confirm('确定重新开始原创试玩并清除本机存档？此操作无法撤销。'))return;
 // Do not reset the live game if the independent region checkpoint remains.
 if(!clearBambooSession(localStorage)){toast('无法清除山径记录，未重新开始');return;}
 // Do not reset while a stale village entry can reactivate an inconsistent region recovery.
 if(!clearBambooEntry()){toast('无法清除山径入口快照，未重新开始');return;}
 try{
  localStorage.removeItem(keyName);
  if(localStorage.getItem(keyName)!==null){toast('本机存档未能清除，未重新开始');return;}
 }catch{toast('无法清除本机存档，未重新开始');return;}
 bambooSession=null;eventHistory={};update(initialState());toast('已重新开始原创试玩');
}
function doMove(dx,dy){
 if(bambooSession){const next=moveBambooSession(bambooSession,dx,dy);if(next){if(!saveBambooSession(localStorage,next)){toast('山径位置保存失败，移动已取消');return;}bambooSession=next;paint();}return;}
 update(move(state,dx,dy));
}
// Original-demo milestone only; this is not a recovered jin.swf story event.
// The replay marker is committed only after a real quest acceptance transition.
const DEMO_ACCEPT_MARKER={
 id:'demo_quest_accepted',
 condition:{path:['quest'],op:'eq',value:'active'},
 effects:[{path:['quest'],value:'active'}]
};
const DEMO_COMPLETION_MARKER={
 id:'demo_quest_completed',
 condition:{path:['quest'],op:'eq',value:'completed'},
 effects:[{path:['quest'],value:'completed'}]
};
function action(){
 if(bambooSession){
  const returned=leaveBambooPass(bambooSession,state);
  if(returned){
   // Do not leave the region while its persisted checkpoint still exists.
   if(!clearBambooSession(localStorage)){toast('无法清除山径记录，未离开山径');return;}
   clearBambooEntry();bambooSession=null;update(returned);toast('已返回青竹村');return;
  }
  const talk=talkBambooSession(bambooSession);
  toast(talk?.dialog||'山径中暂无可交互目标；到达东侧出口按 E 返回');return;
 }
 const entered=enterBambooPass(state);
 if(entered){if(!persistBambooEntry()){toast('村庄入口快照保存失败，未进入山径');return;}
 if(!saveBambooSession(localStorage,entered)){clearBambooEntry();toast('山径位置保存失败，未进入山径');return;}bambooSession=entered;paint();toast('进入竹风山径（独立记录位置，不写入 V2 存档）');return;}
 const previous=state;
 const next=interact(previous);
 if(previous.quest==='active' && next.quest==='completed'){
  const result=applySavedEvent(DEMO_COMPLETION_MARKER,next,eventHistory);
  if(result.applied){eventHistory=result.eventHistory;update(result.game);return;}
 }
 if(previous.quest==='unstarted' && next.quest==='active'){
  const result=applySavedEvent(DEMO_ACCEPT_MARKER,next,eventHistory);
  if(result.applied){eventHistory=result.eventHistory;update(result.game);return;}
 }
 update(next);
}
// Original-demo combat milestone only; never infer a jin.swf event from this marker.
const DEMO_FIRST_VICTORY_MARKER={
 id:'demo_first_bandit_victory',
 condition:{path:['flags','banditBeaten'],op:'eq',value:true},
 effects:[{path:['flags','banditBeaten'],value:true}]
};
function combatAction(command){
 if(bambooSession)return;
 const previous=state;
 const next=battle(previous,command);
 if(previous.combat && !previous.flags.banditBeaten && next.flags.banditBeaten && !next.combat){
  const result=applySavedEvent(DEMO_FIRST_VICTORY_MARKER,next,eventHistory);
  if(result.applied){eventHistory=result.eventHistory;update(result.game);return;}
 }
 update(next);
}
// Mouse and touch taps move only one legal tile; they never auto-trigger dialogue or combat.
canvas.addEventListener('click', event => {
 if(state.dialog || state.combat)return;
 if(bambooSession){
  const rect=canvas.getBoundingClientRect();
  if(rect.width<=0||rect.height<=0)return;
  // Click-to-route takes exactly one legal step; never auto-interacts or bypasses persistence.
  const tile=bambooTileFromPointer(event.clientX,event.clientY,rect,canvas.width,canvas.height);
  if(!tile)return;
  // Tapping the keeper walks one legal step toward an adjacent tile.
  // Dialogue still requires E; no automatic interaction or save bypass.
  const npc=BAMBOO_PASS.npc;
  const isNpc=tile.x===npc.x&&tile.y===npc.y;
  const route=isNpc
    ?routeToRegionNpc(BAMBOO_PASS,bambooSession.position)
    :pathToBambooTile(bambooSession,tile.x,tile.y);
  if(!route?.length){if(isNpc&&route?.length===0)toast('已靠近守径人，按 E 交谈');return;}
  const first=route[0];
  const dx=first.x-bambooSession.position.x,dy=first.y-bambooSession.position.y;
  if(Math.abs(dx)+Math.abs(dy)===1){
   doMove(dx,dy);
   // Only show the dialogue hint after the persisted move actually succeeded.
   if(isNpc && bambooSession && routeToRegionNpc(BAMBOO_PASS,bambooSession.position)?.length===0)
    toast('已靠近守径人，按 E 交谈');
  }
  return;
 }
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
 // The independent region must not mutate the village state through shortcuts.
 if(bambooSession && !['move','interact','dismiss-dialog','route-step','npc-step'].includes(command.kind))return;
 e.preventDefault();
 if(command.kind==='move')doMove(command.dx,command.dy);
 else if(command.kind==='interact')action();
 else if(command.kind==='dismiss-dialog')action();
 else if(command.kind==='potion')update(usePotion(state));
 else if(command.kind==='rest')update(restAtVillage(state));
 else if(command.kind==='route-step')stepRoute();
 else if(command.kind==='npc-step' && bambooSession)stepTowardKeeper();
 else if(command.kind==='combat' && (command.action!=='drink' || canDrinkPotion(state))) combatAction(command.action);
 else if(command.kind==='inventory')toast(`背包：${state.inventory.join('、')||'空空如也'}`);
 else if(command.kind==='quest')toast(questStatus(state).progress);
});
function exportSave() {
 if(bambooSession){toast('请先返回青竹村再导出；山径探索暂不支持存档');return;}
 try {
  const raw=encodeCheckpoint(state,eventHistory);
  if(!raw || new TextEncoder().encode(raw).byteLength>MAX_SAVE_FILE_BYTES)throw new Error('invalid checkpoint');
  const blob = new Blob([raw], {type:'application/json;charset=utf-8'});
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
  const checkpoint=decodeCheckpoint(await file.text());
  if(!checkpoint){toast('存档文件无效或版本不兼容');return;}
  const imported=checkpoint.game;
  const questLabel={unstarted:'未开始',active:'进行中',completed:'已完成'}[imported.quest];
  const preview=`即将导入存档：任务${questLabel}，气血 ${imported.player.hp}，银两 ${imported.player.silver}。\n这会替换当前未保存的游戏进度，但不会自动覆盖本机存档。确定继续？`;
  if(!window.confirm(preview)){toast('已取消导入，当前进度未变');return;}
  if(!clearBambooEntry()){toast('无法清除山径入口快照，未导入存档');return;}
  if(!clearBambooSession(localStorage)){toast('无法清除山径记录，未导入存档');return;}
  bambooSession=null;eventHistory=checkpoint.eventHistory;update(imported);
  toast('已导入当前游戏，请点击保存进度以持久化');
 } catch { toast('读取存档文件失败'); }
};
function stepTowardKeeper(){
 if(!bambooSession)return;
 const route=routeToRegionNpc(BAMBOO_PASS,bambooSession.position);
 if(route===null){toast('守径人当前不可达');return;}
 if(route.length===0){toast('已靠近守径人，按 E 交谈');return;}
 const next=route[0];
 doMove(next.x-bambooSession.position.x,next.y-bambooSession.position.y);
}
function stepRoute(){
 if(!bambooSession){update(stepTowardObjective(state));return;}
 const route=pathToBambooExit(bambooSession);
 if(!route?.length){toast(route?'已到达山径出口，按 E 返回':'当前无法找到出口路线');return;}
 const first=route[0];
 doMove(first.x-bambooSession.position.x,first.y-bambooSession.position.y);
}
$('step-route').onclick=stepRoute;
$('step-npc').onclick=stepTowardKeeper;
$('rematch').onclick=()=>{if(!bambooSession)update(startRematch(state));};
$('rest-village').onclick=()=>{if(!bambooSession)update(restAtVillage(state));};
$('equip-weapon').onclick=()=>{if(!bambooSession)update(equipWeapon(state));};
$('discard-potion').onclick=()=>{if(!bambooSession)update(discardPotion(state));};
$('sell-potion').onclick=()=>{if(!bambooSession)update(sellPotion(state));};
$('use-potion').onclick=()=>{if(!bambooSession)update(usePotion(state));};
for(const a of ['attack','guard','drink','flee'])$(a).onclick=()=>combatAction(a);
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
 if(bambooSession){
  drawBambooPass(ctx,bambooSession,canvas.width,canvas.height);
  $('dialog').classList.add('hidden');$('combat').classList.add('hidden');
  // Village controls otherwise retain stale enabled state while this scene is shown.
  for(const id of ['rematch','rest-village','equip-weapon','discard-potion','sell-potion','use-potion','attack','guard','drink','flee'])$(id).disabled=true;
  const exitRoute=pathToBambooExit(bambooSession);
  $('step-route').disabled=!exitRoute?.length;
  $('step-route').textContent=exitRoute===null ? '出口路线不可达' : exitRoute.length ? `向山径出口走一步（剩余 ${exitRoute.length} 步）` : '已到山径出口（按 E 返回）';
  $('save').disabled=true;$('export-save').disabled=true;
  const npcRoute=routeToRegionNpc(BAMBOO_PASS,bambooSession.position);
  $('step-npc').disabled=!npcRoute?.length;
  $('step-npc').textContent=npcRoute===null?'守径人不可达':npcRoute.length===0?'已靠近守径人（按 E 交谈）':`靠近守径人一步（剩余 ${npcRoute.length} 步 · N）`;
  const npcHint=npcRoute===null?'守径人当前不可达':npcRoute.length===0?'已靠近守径人，按 E 交谈':`距守径人交谈位置 ${npcRoute.length} 步（按 N 或点击守径人逐步靠近）`;
  const exitHint=exitRoute===null?'出口路线暂不可达':exitRoute.length===0?'已到达出口，按 E 返回青竹村':`距离东侧出口 ${exitRoute.length} 步`;
  $('quest-title').textContent='竹风山径 · 探索';
  document.querySelector('.scene-heading').setAttribute('aria-label','当前地图：竹风山径');
  document.querySelector('.scene-heading').firstElementChild.querySelector('.scene-name').textContent='竹风山径';
  $('quest-progress').textContent=npcRoute===null?'守径人路线不可达':npcRoute.length===0?'守径人：可交谈（按 E）':`守径人：还需 ${npcRoute.length} 步`;
  const exitAction=exitRoute===null?'请改用方向键探索可通行道路':exitRoute.length===0?'按 E 返回青竹村':'可点击出口寻路按钮逐步前进';
  $('quest-desc').textContent=`竹风山径：${npcHint}；${exitHint}。${exitAction}。区域位置独立保存于本机；不写入 V2 存档。`;
  return;
 }
 document.querySelector('.scene-heading').setAttribute('aria-label','当前地图：青竹村');
 document.querySelector('.scene-heading').firstElementChild.querySelector('.scene-name').textContent='青竹村';
 $('save').disabled=false;$('export-save').disabled=false;
 // The keeper only exists in the bamboo region; disable its touch shortcut in the village.
 $('step-npc').disabled=true;
 $('step-npc').textContent='靠近守径人（仅竹风山径可用）';
 $('step-route').textContent='沿任务路标走一步';
 for(const id of ['attack','guard','flee'])$(id).disabled=false;
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
 // The attack control must show the actual demo action and damage for current equipment.
 $('attack').textContent=`${attackName(state)}（1） · ${attackDamage(state)} 伤害`;
 // Combat consumable availability and the 3 shortcut share one rule.
 const combatPotion=$('drink');
 const combatPotionCount=state.inventory.filter(item=>item==='回春散').length;
 combatPotion.disabled=!canDrinkPotion(state);
 combatPotion.textContent=`服药（3） · ${combatPotionCount} 包`;
 $('sell-potion').disabled=!!state.combat||!!state.dialog||!state.inventory.includes('回春散')||state.player.silver>999999998||Math.abs(state.player.x-ACTORS.merchant.x)+Math.abs(state.player.y-ACTORS.merchant.y)>1;
 $('discard-potion').disabled=!state.inventory.includes('回春散')||!!state.combat||!!state.dialog;
 $('use-potion').disabled=!state.inventory.includes('回春散')||state.player.hp>=state.player.maxHp||!!state.combat||!!state.dialog;
 const equip=$('equip-weapon');equip.disabled=!state.inventory.includes(DEMO_SWORD)||!!state.combat||!!state.dialog;
 equip.textContent=state.equipment.weapon===DEMO_SWORD?'卸下竹纹短剑':'装备竹纹短剑（攻击 +4）';
 $('hp-num').textContent=`${state.player.hp} / 100`;$('hp-bar').style.width=state.player.hp+'%';$('silver').textContent=state.player.silver;
 const q=questStatus(state);
 $('step-route').disabled=!!state.dialog||!!state.combat||!route?.length;
 $('rematch').disabled=!canRematch(state);
 const restButton=$('rest-village');
 const restAllowed=canRestAtVillage(state);
 restButton.disabled=!restAllowed;
 restButton.textContent=restAllowed
  ? `竹下调息（R · 恢复 ${Math.min(20,state.player.maxHp-state.player.hp)} 气血）`
  : '竹下调息（R · 至多恢复 20 气血）';
 const routeHint=!objective?'':route===null?'（路径暂不可达）':route.length===0
  ?(state.quest==='completed'?(state.dialog?'（先关闭对话，再点击「竹影再试」）':'（已靠近，点击「竹影再试」）'):'（已靠近，按 E 交互）')
  :`（沿金色路标 ${route.length} 步）`;
 $('quest-title').textContent=q.title;$('quest-desc').textContent=q.description+(objective?`　下一步：${objective.label}${routeHint}`:'');$('quest-progress').textContent=q.progress;
 const inv=$('inventory');inv.replaceChildren();for(const item of state.inventory){const b=document.createElement('span');b.className='item';b.textContent=item;inv.appendChild(b);}if(!state.inventory.length){const n=document.createElement('span');n.className='empty';n.textContent='暂无物品';inv.appendChild(n);}
 const j=$('journal');j.replaceChildren();for(const note of state.journal){const p=document.createElement('p');p.textContent=note;j.appendChild(p);}
}
paint();
