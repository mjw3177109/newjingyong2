# 原创试玩：战斗服药可用性与快捷键一致性

## 发现问题

战斗界面的「服药（3）」按钮此前即使没有回春散或气血已满也保持可点；按数字 3 会产生一条无效操作日志。引擎不会扣药或让敌人额外攻击，但 UI 没有清楚表示操作不可用。

## 最小实现

- `src/engine.js` 导出 `canDrinkPotion`，统一定义「正在战斗、持有回春散、气血未满」三个条件。
- `src/main.js` 在战斗面板显示回春散数量，按同一规则禁用按钮和数字 3 快捷键。有效服药仍执行原有恢复与敌人反击逻辑。
- `tests/combat-potion-availability.test.mjs` 覆盖缺药、满血、非战斗、有效服药、存档与状态不可变性；`tests/browser_smoke.py` 覆盖真实 Chromium 禁用按钮与快捷键。
- 不修改存档 v2 schema，不修改 `jin.swf`、FFDec、地图、装备或任务事件。

## 证据边界

本变更仅属于**原创 HTML5 试玩**的操作反馈与回归测试，不是原作回春散、战斗回合或道具数量的复刻证据。原始 SWF 已语义核实的剧情事件仍为 **0**；12 个优先 IF 仍需在授权隔离环境结合 AVM1、FFDec 脚本及运行时交叉核验。

验收命令：`npm run check`、`python tests/browser_smoke.py`（需 Playwright Chromium）、`python -m unittest discover -s tests -p 'test_*.py'`。最终结果以提交后的 GitHub Actions 为准。
