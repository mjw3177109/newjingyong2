# 2026-11-01 原创 HTML5 试玩存档字段白名单

## 发现
旧版 `parseSave` 验证了玩家坐标、气血、银两、背包、装备与战斗的部分字段值，却允许 JSON 存档在顶层、`player`、`flags` 或 `combat` 中携带未识别字段。这些字段不是演示游戏状态，可能被导入并随下一次导出继续传播。它们不应被误认为已恢复的原始 SWF 剧情或战斗字段。

## 最小修复
`src/engine.js` 对 v2 存档（以及 v1 迁移后的状态）检查精确字段集合：
- 顶层：`version, player, quest, inventory, flags, equipment, combat, dialog, journal`
- `player`：`x, y, hp, maxHp, silver`
- `flags`：`herbTaken, banditBeaten`
- 非空 `combat`：`enemyHp, enemyMaxHp, guard`

保留既有数值范围、任务一致性与旧版 v1→v2 迁移校验；不增加新的存档版本，不改变游戏玩法或任何原始 `jin.swf` 文件。

## 验证与边界
`tests/engine.test.mjs` 增加两项回归测试：拒绝顶层、玩家、任务旗标、战斗的未知字段；验证正常 v2 与合法 v1 仍能读取，同时拒绝带额外字段的 v1。CI 入口：`npm run check`，真实浏览器：`python tests/browser_smoke.py`。以对应 GitHub Actions 最终执行结果为准。

**此变更仅加强原创试玩存档的完整性。原作剧情/事件语义已核实数量仍为 0；未经 FFDec 私有脚本、AVM1 字节码及运行时交叉核验，不得登记原作事件或宣称 1:1 完成。**
