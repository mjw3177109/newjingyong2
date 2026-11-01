import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState, move, interact, battle, parseSave, questStatus, equipWeapon, attackDamage, DEMO_SWORD, discardPotion, MAX_INVENTORY, MAX_POTIONS, usePotion} from '../src/engine.js';
const at=(s,x,y)=>({...s,player:{...s.player,x,y}});
test('world movement obeys boundaries, solid tiles, actor collision',()=>{
 let s=initialState();assert.equal(move(at(s,0,0),-1,0).player.x,0);
 assert.equal(move(at(s,2,4),0,-1).player.y,4);
 assert.equal(move(at(s,7,7),0,-1).player.y,7);
 assert.equal(move(at(s,5,8),1,0).player.x,6);
});
test('quest needs both herb and trial, then completion awards silver once',()=>{
 let s=interact(at(initialState(),7,7));assert.equal(s.quest,'active');
 s=interact(s);s=interact(at(s,12,9));assert.equal(s.flags.herbTaken,true);
 s=interact(s);s=interact(at(s,19,8));assert.ok(s.combat);
 for(let i=0;i<3;i++)s=battle(s,'attack');
 assert.equal(s.flags.banditBeaten,true);assert.equal(s.combat,null);
 s=interact(at(s,7,7));assert.equal(s.quest,'completed');assert.equal(s.player.silver,40);
 s=interact(s);s=interact(s);assert.equal(s.player.silver,40);
});
test('merchant sells potion; battle healing caps HP; missing potion is non-consuming',()=>{
 let s=interact(at(initialState(),16,8));assert.ok(s.inventory.includes('回春散'));assert.equal(s.player.silver,5);
 s=interact(s);s=interact(at(s,19,8));s.player.hp=92;
 s=battle(s,'drink');assert.equal(s.player.hp,94);assert.ok(!s.inventory.includes('回春散'));
 const hp=s.player.hp;s=battle(s,'drink');assert.equal(s.player.hp,hp);
});
test('save parsing rejects invalid / incompatible structures',()=>{
 const s=initialState();assert.ok(parseSave(JSON.stringify(s)));
 assert.equal(parseSave('{'),null);assert.equal(parseSave(JSON.stringify({...s,version:3})),null);
 assert.equal(parseSave(JSON.stringify({...s,player:{x:100,y:0,hp:100}})),null);
});
test('quest status phases',()=>{
 let s=initialState();assert.equal(questStatus(s).progress,'未接受');s.quest='completed';assert.match(questStatus(s).progress,/已完成/);
});

test('save parser accepts a legitimate combat checkpoint',()=>{
 let s=interact(at(initialState(),19,8));
 assert.ok(s.combat);
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});
test('save parser rejects impossible world coordinates and economy',()=>{
 const s=initialState();
 for(const p of [
  {...s.player,x:2,y:2},
  {...s.player,maxHp:0},
  {...s.player,hp:101},
  {...s.player,silver:-5},
  {...s.player,silver:1.25}
 ])assert.equal(parseSave(JSON.stringify({...s,player:p})),null);
});
test('save parser rejects malformed inventory and contradictory quest flags',()=>{
 const s=initialState();
 assert.equal(parseSave(JSON.stringify({...s,inventory:[42]})),null);
 assert.equal(parseSave(JSON.stringify({...s,inventory:['未知物品']})),null);
 assert.equal(parseSave(JSON.stringify({...s,quest:'completed'})),null);
 assert.equal(parseSave(JSON.stringify({...s,flags:{...s.flags,herbTaken:true}})),null);
});
test('save parser rejects malformed combat and unbounded UI strings',()=>{
 const s=initialState();
 for(const combat of [{enemyHp:-1,enemyMaxHp:28,guard:false},{enemyHp:28,enemyMaxHp:28,guard:'no'}])
  assert.equal(parseSave(JSON.stringify({...s,combat})),null);
 assert.equal(parseSave(JSON.stringify({...s,dialog:'x'.repeat(501)})),null);
 assert.equal(parseSave(JSON.stringify({...s,journal:['x'.repeat(301)]})),null);
});


test('original demo quest grants unique sword and equipment toggles',()=>{
 let s=initialState();s.quest='active';s.flags.herbTaken=true;s.flags.banditBeaten=true;s.inventory=['清心草'];
 s=interact(at(s,7,7));assert.equal(s.quest,'completed');assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
 s=interact(s);s=interact(s);assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
 s=interact(s); // Close the repeated elder dialog before using equipment.
 assert.equal(attackDamage(s),12);s=equipWeapon(s);assert.equal(s.equipment.weapon,DEMO_SWORD);
 assert.equal(attackDamage(s),16);assert.deepEqual(parseSave(JSON.stringify(s)),s);
 s=equipWeapon(s);assert.equal(s.equipment.weapon,null);assert.equal(attackDamage(s),12);
});
test('equipped sword changes combat damage but cannot toggle during battle',()=>{
 let s=initialState();s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;s.inventory=['清心草',DEMO_SWORD];
 s=equipWeapon(s);s.flags.banditBeaten=false;s.quest='active';s.inventory=['清心草',DEMO_SWORD];
 // Battle mechanics test with a synthetic state, independent of story mapping.
 s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
 const locked=equipWeapon(s);assert.equal(locked.equipment.weapon,DEMO_SWORD);
 s=battle(s,'attack');assert.equal(s.combat.enemyHp,12);
});
test('version 1 save migrates without losing quest and receives demo reward if completed',()=>{
 const s=initialState();s.version=1;delete s.equipment;
 const old=parseSave(JSON.stringify(s));assert.equal(old.version,2);assert.deepEqual(old.equipment,{weapon:null});
 assert.equal(old.inventory.length,0);
 s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;s.inventory=['清心草'];
 const migrated=parseSave(JSON.stringify(s));assert.ok(migrated.inventory.includes(DEMO_SWORD));
 assert.equal(migrated.quest,'completed');assert.equal(migrated.player.silver,10);
});
test('save rejects forged sword, invalid equipment and tampered legacy format',()=>{
 const s=initialState();
 assert.equal(parseSave(JSON.stringify({...s,equipment:{weapon:DEMO_SWORD}})),null);
 assert.equal(parseSave(JSON.stringify({...s,inventory:[DEMO_SWORD]})),null);
 assert.equal(parseSave(JSON.stringify({...s,equipment:{weapon:'未知武器'}})),null);
 assert.equal(parseSave(JSON.stringify({...s,version:1,inventory:[DEMO_SWORD]})),null);
 assert.equal(parseSave(JSON.stringify({...s,version:1})),null);
});


test('merchant reserves inventory slots for quest items and reward',()=>{
 let s=initialState();s.inventory=Array(MAX_POTIONS).fill('回春散');s.player.silver=1000;
 s=interact(at(s,16,8));
 assert.equal(s.inventory.length,MAX_POTIONS);
 assert.equal(s.player.silver,1000);
 assert.match(s.dialog,/整理行囊/);
});
test('legacy full bag blocks reward safely, then recovers after explicit discard',()=>{
 let s=initialState();s.quest='active';s.flags.herbTaken=true;s.flags.banditBeaten=true;
 s.inventory=['清心草',...Array(64).fill('回春散')];
 assert.equal(s.inventory.length,MAX_INVENTORY);
 assert.ok(parseSave(JSON.stringify(s)));
 s=interact(at(s,7,7));
 assert.equal(s.quest,'active');assert.equal(s.inventory.length,MAX_INVENTORY);
 assert.match(s.dialog,/行囊已满/);
 s=interact(s);s=discardPotion(s);
 assert.equal(s.inventory.length,MAX_INVENTORY-1);
 s=interact(at(s,7,7));
 assert.equal(s.quest,'completed');assert.equal(s.inventory.length,MAX_INVENTORY);
 assert.equal(s.inventory.filter(x=>x===DEMO_SWORD).length,1);
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});
test('herb pickup never exceeds bag capacity and can resume after discard',()=>{
 let s=initialState();s.inventory=Array(MAX_INVENTORY).fill('回春散');
 s=interact(at(s,12,9));
 assert.equal(s.flags.herbTaken,false);assert.equal(s.inventory.length,MAX_INVENTORY);
 assert.match(s.dialog,/行囊已满/);
 s=interact(s);s=discardPotion(s);s=interact(at(s,12,9));
 assert.equal(s.flags.herbTaken,true);assert.equal(s.inventory.length,MAX_INVENTORY);
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});
test('discard is explicit and forbidden during dialog or combat',()=>{
 let s=initialState();s.inventory=['回春散'];
 assert.equal(discardPotion({...s,dialog:'交谈中'}).inventory.length,1);
 assert.equal(discardPotion({...s,combat:{enemyHp:28,enemyMaxHp:28,guard:false}}).inventory.length,1);
 s=discardPotion(s);assert.equal(s.inventory.length,0);
 assert.match(s.journal[0],/丢弃一包回春散/);
 assert.equal(discardPotion(s).inventory.length,0);
});

test('out-of-combat potion restores at most 30 HP and persists',()=>{
 let s=initialState();s.player.hp=62;s.inventory=['回春散','回春散'];
 s=usePotion(s);assert.equal(s.player.hp,92);assert.equal(s.inventory.length,1);
 s=usePotion(s);assert.equal(s.player.hp,100);assert.equal(s.inventory.length,0);
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});
test('out-of-combat potion cannot be wasted at full HP or without stock',()=>{
 let s=initialState();s.inventory=['回春散'];
 assert.deepEqual(usePotion(s),s);
 s.player.hp=70;s.inventory=[];
 assert.deepEqual(usePotion(s),s);
});
test('out-of-combat potion is locked during dialogue and battle',()=>{
 let s=initialState();s.player.hp=50;s.inventory=['回春散'];
 assert.deepEqual(usePotion({...s,dialog:'正在交谈'}),{...s,dialog:'正在交谈'});
 const fighting={...s,combat:{enemyHp:28,enemyMaxHp:28,guard:false}};
 assert.deepEqual(usePotion(fighting),fighting);
});
test('combat drink at full HP does not consume potion or enemy turn',()=>{
 let s=initialState();s.inventory=['回春散'];s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
 const next=battle(s,'drink');
 assert.equal(next.player.hp,100);assert.equal(next.inventory.length,1);
 assert.equal(next.combat.enemyHp,28);assert.match(next.journal[0],/气血已满/);
});

test('save parser rejects active actor occupancy but accepts cleared encounter tiles',()=>{
 const s=initialState();
 for(const [x,y] of [[7,6],[16,9],[12,10],[19,7]])
  assert.equal(parseSave(JSON.stringify(at(s,x,y))),null);
 const herb=at(initialState(),12,10);herb.flags.herbTaken=true;herb.inventory=['清心草'];
 assert.deepEqual(parseSave(JSON.stringify(herb)),herb);
 const trial=at(initialState(),19,7);trial.flags.banditBeaten=true;
 assert.deepEqual(parseSave(JSON.stringify(trial)),trial);
});
test('save parser rejects duplicated quest herb and completed quest without sword',()=>{
 const duplicated=initialState();duplicated.flags.herbTaken=true;duplicated.inventory=['清心草','清心草'];
 assert.equal(parseSave(JSON.stringify(duplicated)),null);
 const missingReward=initialState();missingReward.quest='completed';
 missingReward.flags.herbTaken=true;missingReward.flags.banditBeaten=true;missingReward.inventory=['清心草'];
 assert.equal(parseSave(JSON.stringify(missingReward)),null);
});
test('save parser only accepts combat at a reachable adjacent trial position',()=>{
 const s=initialState();s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
 assert.equal(parseSave(JSON.stringify(s)),null);
 const adjacent=at(s,19,8);
 assert.deepEqual(parseSave(JSON.stringify(adjacent)),adjacent);
});
test('combat potion reports actual capped healing rather than nominal amount',()=>{
 let s=at(initialState(),19,8);
 s.player.hp=92;s.inventory=['回春散'];s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
 s=battle(s,'drink');
 assert.equal(s.player.hp,94);
 assert.equal(s.inventory.length,0);
 assert.ok(s.journal.some(line=>line.includes('恢复 8 点气血')));
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
});

test('save parser rejects tampered trial maximum HP and over-healed enemy',()=>{
 const s=at(initialState(),19,8);
 for(const combat of [
  {enemyHp:29,enemyMaxHp:29,guard:false},
  {enemyHp:27,enemyMaxHp:27,guard:false},
  {enemyHp:29,enemyMaxHp:28,guard:false}
 ])assert.equal(parseSave(JSON.stringify({...s,combat})),null);
});
test('save parser rejects simultaneous battle and dialogue',()=>{
 const s=at(initialState(),19,8);
 s.combat={enemyHp:28,enemyMaxHp:28,guard:false};
 s.dialog='不能在战斗中保持对话';
 assert.equal(parseSave(JSON.stringify(s)),null);
});
test('legitimate guarded low-HP battle loads but zero-HP checkpoint does not',()=>{
 const s=at(initialState(),19,8);
 s.player.hp=1;
 s.combat={enemyHp:1,enemyMaxHp:28,guard:true};
 assert.deepEqual(parseSave(JSON.stringify(s)),s);
 s.player.hp=0;
 assert.equal(parseSave(JSON.stringify(s)),null);
 s.combat=null;
 assert.equal(parseSave(JSON.stringify(s)),null);
});

// Original-demo state invariants; these are not claims about the source SWF.
test('movement rejects diagonal, multi-tile, fractional and non-finite input',()=>{
 const s=initialState();
 for(const [dx,dy] of [[1,1],[2,0],[0,-2],[0.5,0],[NaN,0],[Infinity,0],[0,0]])
  assert.deepEqual(move(s,dx,dy),s);
 assert.equal(move(s,1,0).player.x,s.player.x+1);
});
test('save parser rejects forged player maximum HP while retaining valid low HP',()=>{
 const s=initialState();
 for(const maxHp of [1,99,101,0,null,'100'])
  assert.equal(parseSave(JSON.stringify({...s,player:{...s.player,maxHp,hp:1}})),null);
 const low={...s,player:{...s.player,hp:1}};
 assert.deepEqual(parseSave(JSON.stringify(low)),low);
});

test('quest reward cannot overflow the silver cap or corrupt a valid checkpoint',()=>{
 for(const [silver,expectedReward] of [[999_999_995,5],[1_000_000_000,0]]) {
  let s=initialState();s.quest='active';s.flags.herbTaken=true;s.flags.banditBeaten=true;
  s.inventory=['清心草'];s.player.silver=silver;s=at(s,7,7);
  assert.deepEqual(parseSave(JSON.stringify(s)),s);
  const completed=interact(s);
  assert.equal(completed.quest,'completed');
  assert.equal(completed.player.silver,1_000_000_000);
  assert.equal(completed.inventory.filter(x=>x===DEMO_SWORD).length,1);
  assert.ok(completed.journal[0].includes(`银两 ${expectedReward}`));
  assert.deepEqual(parseSave(JSON.stringify(completed)),completed);
 }
});
