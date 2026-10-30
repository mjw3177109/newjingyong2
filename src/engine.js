import {ACTORS, BLOCKS, WIDTH, HEIGHT, QUEST} from './demo-data.js';
export const SAVE_VERSION = 2;
export const DEMO_SWORD = '竹纹短剑';
export const MAX_INVENTORY = 65;
export const MAX_POTIONS = 63;
const potionCount = s => s.inventory.filter(item => item === '回春散').length;
export const attackDamage = s => 12 + (s.equipment?.weapon === DEMO_SWORD ? 4 : 0);
export function initialState() {
  return {version:SAVE_VERSION, player:{x:5,y:8,hp:100,maxHp:100,silver:10},
    quest:'unstarted',inventory:[],flags:{herbTaken:false,banditBeaten:false},
    equipment:{weapon:null},combat:null,dialog:'',journal:['抵达青竹村，江湖之路由此开始。']};
}
const copy = s => structuredClone(s);
const dist = (a,b) => Math.abs(a.x-b.x)+Math.abs(a.y-b.y);
const addLog = (s,msg) => {s.journal.unshift(msg);s.journal=s.journal.slice(0,6);};
export function move(state,dx,dy) {
  const s=copy(state); if(s.combat || s.dialog) return s;
  const x=s.player.x+dx,y=s.player.y+dy;
  if(x<0||x>=WIDTH||y<0||y>=HEIGHT||BLOCKS.has(`${x},${y}`))return s;
  if(Object.entries(ACTORS).some(([id,p])=>(id!=='herb'||!s.flags.herbTaken)&&(id!=='bandit'||!s.flags.banditBeaten)&&p.x===x&&p.y===y)) return s;
  s.player.x=x;s.player.y=y;return s;
}
export function interact(state) {
  const s=copy(state);
  if(s.combat) return s;
  if(s.dialog){s.dialog='';return s;}
  const near=Object.entries(ACTORS).find(([id,p])=>dist(s.player,p)<=1&&(id!=='herb'||!s.flags.herbTaken)&&(id!=='bandit'||!s.flags.banditBeaten));
  if(!near){s.dialog='此处宁静无事。靠近人物或闪光草药后再按 E。';return s;}
  const [id]=near;
  if(id==='elder'){
    if(s.quest==='unstarted') {s.quest='active';s.dialog='竹隐老人：山间有清心草，也有试炼者。带回药草，通过试炼，便算你踏出了江湖第一步。';addLog(s,'接受原创演示任务：竹影试炼。');}
    else if(s.quest==='active'&&s.flags.banditBeaten&&s.flags.herbTaken){
      if(s.inventory.length>=MAX_INVENTORY){s.dialog='竹隐老人：行囊已满，先整理一包回春散，再来领取奖励。';}
      else {s.quest='completed';s.player.silver+=30;s.inventory.push(DEMO_SWORD);s.dialog='竹隐老人：很好！今日起，你便有了闯荡江湖的底气。';addLog(s,'竹影试炼完成，获得银两 30 与原创竹纹短剑。');}
    }
    else if(s.quest==='completed'){s.dialog='竹隐老人：江湖路远，且行且珍重。';}
    else s.dialog='竹隐老人：清心草与竹林试炼，缺一不可。';
  } else if(id==='merchant'){
    if(s.inventory.length>=MAX_INVENTORY||potionCount(s)>=MAX_POTIONS){s.dialog='行脚商人：回春散已足够多，请先整理行囊再购买。';}
    else if(s.player.silver>=5){s.player.silver-=5;s.inventory.push('回春散');s.dialog='行脚商人：五两银子一包回春散，少侠拿好。';addLog(s,'购买回春散，花费 5 银两。');}
    else s.dialog='行脚商人：银两不足，改日再来吧。';
  } else if(id==='herb'){
    if(s.inventory.length>=MAX_INVENTORY){s.dialog='行囊已满，请先整理回春散再采集清心草。';}
    else {s.flags.herbTaken=true;s.inventory.push('清心草');s.dialog='获得清心草。叶片带着清香，像把竹林的晨露也收进了行囊。';addLog(s,'采集：清心草。');}
  } else if(id==='bandit'){
    s.combat={enemyHp:28,enemyMaxHp:28,guard:false};addLog(s,'进入试炼战斗。');
  }
  return s;
}
export function battle(state,action){
  const s=copy(state); if(!s.combat) return s;
  if(!['attack','guard','drink','flee'].includes(action))return s;
  if(action==='flee'){s.combat=null;addLog(s,'退出试炼，随时可以再次挑战。');return s;}
  if(action==='drink'){
    const at=s.inventory.indexOf('回春散');
    if(at<0){addLog(s,'行囊里没有回春散。');return s;}
    s.inventory.splice(at,1);s.player.hp=Math.min(s.player.maxHp,s.player.hp+30);addLog(s,'使用回春散，恢复 30 点气血（上限 100）。');
  }
  if(action==='guard'){s.combat.guard=true;addLog(s,'凝神防御，下次受击伤害减半。');}
  if(action==='attack'){const damage=attackDamage(s);s.combat.enemyHp=Math.max(0,s.combat.enemyHp-damage);addLog(s,`使出一式青竹剑，造成 ${damage} 点伤害。`);}
  if(s.combat.enemyHp<=0){s.flags.banditBeaten=true;s.combat=null;addLog(s,'试炼胜利！返回竹隐老人处复命。');return s;}
  const damage=s.combat.guard?3:6;s.player.hp=Math.max(0,s.player.hp-damage);s.combat.guard=false;
  addLog(s,`试炼者反击，气血减少 ${damage}。`);
  if(s.player.hp===0){s.player.hp=50;s.player.x=5;s.player.y=8;s.combat=null;addLog(s,'气血耗尽，被送回村口，恢复至 50 点。');}
  return s;
}
export function discardPotion(state){
  const s=copy(state);
  if(s.combat||s.dialog)return s;
  const index=s.inventory.indexOf('回春散');
  if(index<0)return s;
  s.inventory.splice(index,1);
  addLog(s,'整理行囊：丢弃一包回春散。');
  return s;
}
export function equipWeapon(state){
  const s=copy(state);
  if(s.combat || s.dialog || !s.inventory.includes(DEMO_SWORD)) return s;
  s.equipment.weapon=s.equipment.weapon===DEMO_SWORD?null:DEMO_SWORD;
  addLog(s,s.equipment.weapon?'装备竹纹短剑：攻击 +4。':'卸下竹纹短剑。');
  return s;
}
export function questStatus(s){
 if(s.quest==='completed')return {title:QUEST.name,description:'试炼已经完成。',progress:'已完成 · 银两 +30'};
 if(s.quest==='unstarted')return {title:'初入江湖',description:'找到青竹村的竹隐老人，开启原创试玩任务。',progress:'未接受'};
 return {title:QUEST.name,description:QUEST.description,progress:`清心草 ${s.flags.herbTaken?'✓':'○'}　试炼 ${s.flags.banditBeaten?'✓':'○'}`};
}
export function parseSave(raw){
  let s;try{s=JSON.parse(raw);}catch{return null;}
  if(!s || typeof s!=='object' || Array.isArray(s))return null;
  if(s.version===1){
    if(Object.hasOwn(s,'equipment') || !Array.isArray(s.inventory) || s.inventory.length>64 ||
       s.inventory.some(item=>!['清心草','回春散'].includes(item)))return null;
    s={...s,version:SAVE_VERSION,equipment:{weapon:null},inventory:[...s.inventory]};
    // Completed V1 saves get the same demo reward; no original SWF story is inferred.
    if(s.quest==='completed' && s.inventory.length<65)s.inventory.push(DEMO_SWORD);
  }
  if(s.version!==SAVE_VERSION || !s.player || typeof s.player!=='object' || Array.isArray(s.player))return null;
  const p=s.player;
  if(!Number.isInteger(p.x)||!Number.isInteger(p.y)||p.x<0||p.x>=WIDTH||p.y<0||p.y>=HEIGHT||BLOCKS.has(`${p.x},${p.y}`))return null;
  if(!Number.isInteger(p.maxHp)||p.maxHp<1||p.maxHp>100||!Number.isInteger(p.hp)||p.hp<0||p.hp>p.maxHp)return null;
  if(!Number.isSafeInteger(p.silver)||p.silver<0||p.silver>1_000_000_000)return null;
  if(!['unstarted','active','completed'].includes(s.quest))return null;
  if(!s.flags||typeof s.flags.herbTaken!=='boolean'||typeof s.flags.banditBeaten!=='boolean')return null;
  if(!Array.isArray(s.inventory)||s.inventory.length>MAX_INVENTORY||s.inventory.some(item=>!['清心草','回春散',DEMO_SWORD].includes(item)))return null;
  if(s.inventory.filter(item=>item===DEMO_SWORD).length>1 ||
     (s.inventory.includes(DEMO_SWORD) && s.quest!=='completed'))return null;
  if(!s.equipment || typeof s.equipment!=='object' || Array.isArray(s.equipment) ||
     Object.keys(s.equipment).length!==1 ||
     ![null,DEMO_SWORD].includes(s.equipment.weapon) ||
     (s.equipment.weapon===DEMO_SWORD && !s.inventory.includes(DEMO_SWORD)))return null;
  if(s.flags.herbTaken!==s.inventory.includes('清心草'))return null;
  if(s.quest==='completed'&&(!s.flags.herbTaken||!s.flags.banditBeaten))return null;
  if(!Array.isArray(s.journal)||s.journal.length>6||s.journal.some(line=>typeof line!=='string'||line.length>300))return null;
  if(typeof s.dialog!=='string'||s.dialog.length>500)return null;
  if(s.combat!==null){
    const c=s.combat;
    if(!c||!Number.isInteger(c.enemyMaxHp)||c.enemyMaxHp<1||c.enemyMaxHp>100||
       !Number.isInteger(c.enemyHp)||c.enemyHp<1||c.enemyHp>c.enemyMaxHp||
       typeof c.guard!=='boolean'||s.flags.banditBeaten)return null;
  }
  return s;
}
