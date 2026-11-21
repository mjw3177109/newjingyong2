# 原创试玩：战斗无效服药在引擎层完全无副作用（2026-11-02）

## 问题与来源

此前 `src/main.js` 已用 `canDrinkPotion` 禁用战斗服药按钮和数字 3 快捷键，但直接调用 `battle(state, 'drink')` 时，缺药或满血仍会插入一条日志。这与「无效操作不产生回合/记录」的约束不一致，也让 UI 与纯引擎调用的行为分叉。

## 最小修复

- `src/engine.js` 的战斗服药分支在任何修改前调用同一 `canDrinkPotion` 守卫。无效操作返回等值状态，不消耗药品、不产生日志、不触发敌人反击、不改变防御标志。
- `tests/engine.test.mjs` 更新历史测试中对旧无效日志的预期。
- `tests/combat-potion-availability.test.mjs` 增加缺药和满血两种直接引擎调用回归，验证存档仍可读取、入参不变；原有效服药测试仍验证回血、消耗与敌人回合。

## 验收与证据边界

执行 `npm run check`；浏览器行为由 `python tests/browser_smoke.py` 验证；原始 SWF 与 Java 8 FFDec 审计由现有 CI 独立执行。以本提交的 GitHub Actions 最终状态为准。

这是**原创 HTML5 演示游戏**的引擎一致性修复，未声称恢复原作道具、战斗规则或剧情事件。原作语义核实事件数仍为 **0**。未修改存档 v2 schema、`jin.swf`、FFDec、原创美术或其他仓库。
