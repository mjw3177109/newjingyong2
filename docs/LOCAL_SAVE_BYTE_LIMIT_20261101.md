# 本机存档与 JSON 导入统一大小门禁（2026-11-01）

## 发现
浏览器导入 JSON 已通过 `MAX_SAVE_FILE_BYTES = 64 * 1024` 限制 UTF-8 字节数，但“读取本机存档”此前直接将 localStorage 原始字符串交给 `parseSave`，缺少同等大小门禁；“保存进度”也绕过了 `exportSaveText` 的完整 schema 与大小检查。被手动写入的异常超大本机数据会先进入 JSON 解析，且两种存档入口的验证标准不一致。

## 最小实现
- `src/main.js`：本机保存改用 `exportSaveText(state)`，在写入前验证存档 schema 与大小。
- 本机读取先按 **UTF-8 字节数**拒绝超过 64 KiB 的 localStorage 字符串，再调用 `importSaveText`；不改变或删除超限检查点，不覆盖当前未保存进度。
- 合法 v1→v2 迁移、读取确认框、JSON 导入/导出以及游戏任务和战斗逻辑均保持不变。

## 回归与验收
`tests/browser_smoke.py` 新增真实 Chromium 回归：将 22,000 个汉字（UTF-8 66,000 字节）写入 localStorage；点击读取应提示超限，当前银两和原始存储数据均保持不变。此前已有合法存档读取、取消确认、移动端读取及 JSON 导入/导出测试继续覆盖兼容性。

运行 `npm run check`、`python -m unittest discover -s tests -p 'test_*.py'` 和 CI 的 `browser-smoke` 作业。

**证据边界：** 这是原创 HTML5 试玩的数据安全改进，不是从 `jin.swf` 还原的剧情、地图、道具、数值或战斗机制。原作已语义核实剧情事件仍为 **0**；FFDec 历史漂移仍待独立核验。
