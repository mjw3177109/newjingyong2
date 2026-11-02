# 原创 HTML5 试玩：任务引导与 Canvas 点按寻路统一

## 发现的问题

`src/objectives.js` 和 `src/tile-path.js` 各维护一套四方向 BFS 寻路逻辑。两套算法目前目标相近，但后续若只更新一处的碰撞、已移除对象或最短路规则，会出现任务引导与地图点按不一致的问题。

## 本轮最小变更

- `src/objectives.js` 保留原创演示任务的目标选择和单步操作，将 `pathToObjective()` 改为调用共享 `pathToTile()`，不再维护第二份 BFS。
- `tests/objectives.test.mjs` 增加三项回归：四种原创任务阶段的路径一致性和状态不可变性；任务结束/对话中禁止引导移动；单次移动一格且最终停在 NPC 相邻格。
- 未修改存档版本、战斗、原始 `jin.swf`、FFDec、音视频或素材。地图点按与任务按钮仍均为一次输入最多走一格，不会自动触发交互。

## 验证与边界

测试命令：`npm run check`；浏览器验收：`python tests/browser_smoke.py`（需 Playwright/Chromium）。以 GitHub Actions 最终作业状态为准。

此变更只修正原创试玩的工程一致性，**不表示已还原任何原作剧情、地图或数值**。原作 IF 字节码结构匹配不能替代剧情语义核实，原作剧情事件对照表仍以独立来源证据为准。PR 保持 Draft，不合并 `main`，不公开受保护的反编译素材。
