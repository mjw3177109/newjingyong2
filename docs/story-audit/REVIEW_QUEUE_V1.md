# FFDec 脱敏脚本审查队列 V1（2026-10-30）

## 目的与证据链

真实 SWF 的 FFDec Java 8 导出已通过 CI；原始脚本只存在于 GitHub Actions 临时目录。此阶段没有可核实的原作剧情条件，**不能将自动检出的控制流当作剧情事件**。

为减少人工审计工作量，本阶段在 `ffdec-source-free-script-index` 的基础上新增 `ffdec-source-free-review-queue` Artifact，记录最多 100 个**待审查脚本候选**，而不是虚构事件表。

来源：`jin.swf` → `FFDec/ffdec.jar`（Java 8）→ 临时脚本目录 → `tools/index_ffdec_scripts.py` → `tools/build_review_queue.py` → GitHub Actions Artifact。

## 队列规则

- 仅使用已有脱敏索引里的 `if`、`else`、`gotoAndPlay/Stop`、`on/onClipEvent`、`function` 文本计数；分别赋予 2、1、6、5、1 的启发式权重。
- 至少出现一个 `if`、`goto` 或 `on` 才入队；按权重降序、路径哈希升序确定排序，结果稳定可复现。
- 公开记录仅含 SWF SHA-256、路径/内容 SHA-256、匿名候选 ID、计数、排序分数和 `semantic_status: unverified`。
- **不包含**脚本正文、原始路径、文件名、角色名、剧情台词、原始美术或音频。
- 同一条脚本可能含多个事件；多个脚本也可能属于一个事件。分数只是审查顺序，不能代表任务数量、剧情重要性或还原进度。

## 核验流程

1. 下载对应 CI 的 `ffdec-source-free-review-queue` Artifact，记录 SWF 哈希、工作流链接和候选 ID。
2. 仅在有权限的隔离分析环境中，通过路径/内容哈希定位候选脚本，逐条人工核对触发条件、变量变化、时间轴跳转及结果。
3. 将**已核实**的事实摘要登记至 `docs/story-audit/README.md`，保留来源哈希、偏移/行号、证据验证方式；未经核实的候选不得填入原作事件表。
4. 先用原创占位数据和独立 Q 版国风素材测试引擎；有权利证明后才考虑复刻受保护剧情的发布。

验证：`python3 -m unittest discover -s tests -p 'test_*.py'`。脚本独立运行：`python3 tools/build_review_queue.py reports/ffdec_script_index.json --out reports/ffdec_review_queue.json --limit 100`。

**当前确认数：原作剧情事件 0 条；待审查候选数以本次 CI Artifact 实测为准。**
