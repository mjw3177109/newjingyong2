// Independent original demonstration. Do not label this as extracted SWF story data.
export const WIDTH = 25;
export const HEIGHT = 15;
export const TILE = 36;
export const ACTORS = Object.freeze({
  elder: { x: 7, y: 6, name: '竹隐老人', sprite: 'elder' },
  merchant: { x: 16, y: 9, name: '行脚商人', sprite: 'merchant' },
  herb: { x: 12, y: 10, name: '清心草', sprite: 'herb' },
  bandit: { x: 19, y: 7, name: '蒙面试炼者', sprite: 'bandit' },
});
export const BLOCKS = new Set([
  '2,2','3,2','4,2','2,3','3,3','4,3',
  '13,2','14,2','15,2','13,3','14,3','15,3',
  '21,10','22,10','23,10','21,11','22,11','23,11',
  '1,12','2,12','1,13','2,13'
]);
export const QUEST = Object.freeze({name:'竹影试炼',description:'寻得清心草，击败竹林试炼者，再向竹隐老人复命。'});
