import {initialState,move,interact,battle,questStatus,parseSave,equipWeapon,attackDamage,DEMO_SWORD,discardPotion,usePotion} from './engine.js';
import {ACTORS,WIDTH,HEIGHT,TILE,BLOCKS} from './demo-data.js';
let state=initialState();
const $=id=>document.getElementById(id), canvas=$('game'),ctx=canvas.getContext('2d');
const images={};
for(const id of ['hero','elder','merchant','herb','bandit']){
 const img=new Image();img.src=`./assets/${id}.svg`;img.onload=()=>paint();images[id]=img;
}
const keyName = 'jianghu-q-save-v1';
function toast(txt){const t=$('toast');t.textContent=txt;t.classList.remove('hidden');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.add('hidden'),1800);}
function update(next){state=next;paint();}
function save(){try{localStorage.setItem(keyName,JSON.stringify(state));toast('进度已存入本机浏览器');}catch{toast('浏览器存储不可用');}}
function load(){let raw;try{raw=localStorage.getItem(keyName);}catch{toast('浏览器存储不可用');return;}
 const parsed=raw&&parseSave(raw);if(!parsed){toast('没有有效的存档');return;}update(parsed);toast('进度读取成功');}
function doMove(dx,dy){update(move(state,dx,dy));}
function action(){update(interact(state));}
const dirs={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0],w:[0,-1],s:[0,1],a:[-1,0],d:[1,0]};
document.addEventListener('keydown',e=>{
 const key=e.key.length===1?e.key.toLowerCase():e.key;
 if(dirs[key]){e.preventDefault();doMove(...dirs[key]);}
 else if(key==='e'||key==='Enter'||key===' '){e.preventDefault();action();}
 else if(key==='h'){e.preventDefault();update(usePotion(state));}
 else if(key==='b')toast(`背包：${state.inventory.join('、')||'空空如也'}`);
 else if(key==='j')toast(questStatus(state).progress);
});
$('interact').onclick=action;$('save').onclick=save;$('load').onclick=load;
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
 actor('hero',state.player.x,state.player.y,59);
 ctx.textAlign='left';ctx.fillStyle='#17362b';ctx.font='bold 14px system-ui';ctx.fillText('青 竹 村',18,27);
 const d=$('dialog');d.textContent=state.dialog?state.dialog+'　[按 E 继续]':'';d.classList.toggle('hidden',!state.dialog);
 const c=$('combat');c.classList.toggle('hidden',!state.combat);
 if(state.combat)$('combat-info').textContent=`试炼者气血 ${state.combat.enemyHp}/${state.combat.enemyMaxHp}　｜　少侠气血 ${state.player.hp}/100`;
 $('attack-num').textContent=attackDamage(state);
 $('discard-potion').disabled=!state.inventory.includes('回春散')||!!state.combat||!!state.dialog;
 $('use-potion').disabled=!state.inventory.includes('回春散')||state.player.hp>=state.player.maxHp||!!state.combat||!!state.dialog;
 const equip=$('equip-weapon');equip.disabled=!state.inventory.includes(DEMO_SWORD)||!!state.combat||!!state.dialog;
 equip.textContent=state.equipment.weapon===DEMO_SWORD?'卸下竹纹短剑':'装备竹纹短剑（攻击 +4）';
 $('hp-num').textContent=`${state.player.hp} / 100`;$('hp-bar').style.width=state.player.hp+'%';$('silver').textContent=state.player.silver;
 const q=questStatus(state);$('quest-title').textContent=q.title;$('quest-desc').textContent=q.description;$('quest-progress').textContent=q.progress;
 const inv=$('inventory');inv.replaceChildren();for(const item of state.inventory){const b=document.createElement('span');b.className='item';b.textContent=item;inv.appendChild(b);}if(!state.inventory.length){const n=document.createElement('span');n.className='empty';n.textContent='暂无物品';inv.appendChild(n);}
 const j=$('journal');j.replaceChildren();for(const note of state.journal){const p=document.createElement('p');p.textContent=note;j.appendChild(p);}
}
paint();
