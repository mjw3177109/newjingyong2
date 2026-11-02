import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,interact,battle,equipWeapon,canRematch,startRematch,DEMO_SWORD,parseSave} from '../src/engine.js';

function completedNearElder(){
 const s=initialState();
 s.player.x=7;s.player.y=7;
 s.player.silver=40;
 s.quest='completed';s.flags.herbTaken=true;s.flags.banditBeaten=true;
 s.inventory=['清心草',DEMO_SWORD];
 return s;
}

test('completed demo quest unlocks an equipped rematch with no repeated rewards',()=>{
 const s=completedNearElder();
 const equipped=equipWeapon(s);
 assert.equal(canRematch(equipped),true);
 const fighting=startRematch(equipped);
 assert.ok(fighting.combat);
 assert.deepEqual(parseSave(JSON.stringify(fighting)),fighting,'mid-rematch v2 checkpoint is valid');
 assert.equal(equipped.combat,null,'input state is immutable');
 const hit=battle(fighting,'attack');
 assert.equal(hit.combat.enemyHp,12);
 const won=battle(hit,'attack');
 assert.equal(won.combat,null);
 assert.equal(won.player.silver,40);
 assert.equal(won.inventory.filter(x=>x===DEMO_SWORD).length,1);
 assert.equal(won.quest,'completed');
 assert.equal(won.flags.banditBeaten,true);
 assert.match(won.journal.join(' '),/再试胜利.*不重复发放任务奖励/);
 assert.deepEqual(parseSave(JSON.stringify(won)),won);
});

test('rematch is gated by quest completion, proximity, dialogue and battle state',()=>{
 const s=completedNearElder();
 const uncompleted={...s,quest:'active'};
 assert.equal(canRematch(uncompleted),false);
 assert.deepEqual(startRematch(uncompleted),uncompleted);
 const far=structuredClone(s);far.player.x=5;far.player.y=8;
 assert.equal(canRematch(far),false);
 assert.deepEqual(startRematch(far),far);
 const talking={...s,dialog:'竹隐老人：江湖路远。'};
 assert.equal(canRematch(talking),false);
 assert.deepEqual(startRematch(talking),talking);
 const active=startRematch(s);
 assert.equal(canRematch(active),false);
 assert.deepEqual(startRematch(active),active);
});

test('rematch retreat permits another attempt, never alters reward or save version',()=>{
 const s=completedNearElder();
 const retreated=battle(startRematch(s),'flee');
 assert.equal(retreated.combat,null);
 assert.equal(retreated.player.silver,40);
 assert.equal(canRematch(retreated),true);
 assert.ok(startRematch(retreated).combat);
 assert.equal(retreated.version,2);
});

test('first-time trial and previously valid completed v2 saves remain compatible',()=>{
 const s=initialState();s.player.x=19;s.player.y=8;
 const fighting=interact(s);
 assert.ok(fighting.combat);
 assert.deepEqual(parseSave(JSON.stringify(fighting)),fighting);
 const firstWin=battle(battle(battle(fighting,'attack'),'attack'),'attack');
 assert.equal(firstWin.flags.banditBeaten,true);
 assert.match(firstWin.journal.join(' '),/试炼胜利！返回竹隐老人处复命/);
 const legacy=completedNearElder();
 legacy.player.x=19;legacy.player.y=7; // old v2 allowed walking onto a defeated actor's tile
 assert.deepEqual(parseSave(JSON.stringify(legacy)),legacy);
});
