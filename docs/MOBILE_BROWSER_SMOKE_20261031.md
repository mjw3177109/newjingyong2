# 原创 HTML5 试玩：Chromium 触屏回归验收（2026-10-31）

本轮补充了真实 Chromium 的移动端仿真测试，避免桌面浏览器流程通过后，触屏按钮、移动端 Canvas 缩放、任务寻路或存档恢复发生未发现的回归。

## 测试范围与证据

- 使用 Playwright Chromium 的独立浏览器上下文：390×844 CSS 像素、`is_mobile=True`、`has_touch=True`，与桌面 1440×960 测试隔离。
- 断言移动方向盘显示、Canvas 不超出视口；通过真实 `.tap()` 点击向右方向键，验证玩家从 (5,8) 移动到 (6,8)。
- 通过移动端按钮保存进度、刷新页面、读取存档并导出 JSON，核对位置确实恢复。
- 通过移动端「沿路前进一步」逐步到达竹隐老人，触屏交互领取原创任务并关闭对话。
- 检查浏览器 JavaScript 异常，分别生成 `reports/browser_smoke.png` 与 `reports/browser_smoke_mobile.png`。GitHub Actions 只上传本项目原创试玩截图，不上传 `jin.swf` 的任何美术或音频。

## 执行方式

```bash
python -m pip install playwright==1.55.0
python -m playwright install --with-deps chromium
python tests/browser_smoke.py
```

GitHub Actions 的 `browser-smoke` 作业负责实际浏览器运行和截图。**是否通过必须以对应提交的 Actions 作业为准**；静态代码检查不能代替浏览器验证。

## 范围限制

这是原创 Q 版 HTML5 演示的移动端操作回归测试，并非真机 iOS/Android 浏览器测试，更不是原始 SWF 的地图、剧情、数值或战斗 1:1 复刻证据。原作已语义核实剧情事件仍为 **0**。后续继续核实 12 个 IF 条件审查目标的触发条件、变量变化和运行时效果，只有独立证据充分才可填入正式剧情对照表。
