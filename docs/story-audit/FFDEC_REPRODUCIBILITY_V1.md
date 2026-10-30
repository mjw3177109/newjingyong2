# FFDec 两次独立导出一致性核验（2026-10-30）

## 已观察到的问题

同一原始 SWF 的不同 GitHub Actions 运行曾出现前 100 个审查候选的整数字面帧跳转统计 **474/3** 与 **469/2**（前者为跳转数，后者为严格简单 if 守卫数）。尚未证明差异源于 FFDec、导出文件内容、候选排序还是脚本扫描器。不能把任意一次数字当作稳定的原作事件计数。

## 本轮最小实现

- 在 \`ffdec-java8-probe\` 同一作业里用 Java 8 + 仓库 FFDec，对同一个 \`jin.swf\` 分别导出两次到不同的临时目录。
- 两份导出分别生成匿名索引、前 100 个候选队列、帧跳转证据；用 \`tools/compare_ffdec_exports.py\` 做逐层比较。
- 输出仅含 SWF 哈希、两份导出的匿名清单指纹、脚本/候选/跳转/守卫计数，以及新增/缺失路径数、同路径内容变化数、共同候选跳转数变化数。
- 临时脚本、路径、对话、音频、图像及 FFDec 原始日志不公开上传。报告中的 \`stable\` 只表示本次同环境两次导出相同，不代表跨运行稳定或剧情语义已核实。
- 不同 SWF 哈希、队列成员被篡改、候选 ID 不一致、帧跳转总数不匹配时直接报错；对真实差异生成 \`divergent\` 报告，保留证据而不是伪装成功。

## 验收与下一步

使用 \`python -m unittest discover -s tests -p 'test_*.py'\` 验证合成输入；真实数据以 GitHub Actions 的 \`ffdec-source-free-reproducibility\` Artifact 为准。后续若同轮稳定而跨轮仍不稳定，比较不同 Actions 的匿名指纹和候选重叠；若同轮不稳定，先定位 FFDec 导出或排序问题。**已核实原作剧情事件仍为 0 条**，不把语法统计接入正式剧情。

## 真实线上双导出验收（2026-10-30 13:25 UTC）

- 功能提交：[aa963cb](https://github.com/mjw3177109/newjingyong2/commit/aa963cb03a5998fc7d15f78e53d57fcc9ec5fc0b)。
- [GitHub Actions #41062957723](https://github.com/mjw3177109/newjingyong2/actions/runs/41062957723)：三个作业均 success；Python 19/19、Node 13/13。FFDec Java 8 两次退出码均为 0。
- 同一 CI 作业内，两次独立导出各 **4,560** 个脚本文件、各 **2,323** 个控制流候选，前 100 个候选各检测到 **474** 个字面跳转与 **3** 个简单 if 守卫；匿名索引和逐候选语法统计对比结果 **stable**，同路径脚本内容变化数 **0**。
- 对照 [早前 Actions #41054786935](https://github.com/mjw3177109/newjingyong2/actions/runs/41054786935) 的 **469/2**，说明 **跨运行仍有未解释差异**。同轮 stable 不能证明跨机器或跨时间稳定，也不能直接认定 FFDec 存在缺陷。
- 下一步：对比两个 Actions 的 `ffdec-source-free-script-index`、`ffdec-source-free-review-queue` 和 `ffdec-source-free-frame-jumps` 归档，先区分导出内容差异、排序差异还是扫描器差异；必要时增加跨运行指纹基线。当前原作剧情语义核实仍为 **0 条**。

## 同一作业内出现真实差异（2026-10-30 13:27 UTC）

- [GitHub Actions #41063299964](https://github.com/mjw3177109/newjingyong2/actions/runs/41063299964) 在相同 Java 8、FFDec JAR 和 `jin.swf` 下，**第一次 474/3、第二次 469/2**，两次各导出 4,560 个脚本文件、筛选 2,323 个控制流候选。
- 脱敏比较结果为 **divergent**：**至少 1 个相同匿名路径的导出脚本内容发生变化**；共同入选候选的跳转/守卫计数没有差异。具体候选集合是否变化应继续查 `ffdec-source-free-reproducibility` Artifact，不能仅凭总数推断。
- 这证明同环境连续导出也可能不一致。上一轮双导出稳定是单次观察，不能概括为 FFDec 全局稳定。后续需固定/复核该匿名脚本，并对剧情审计只采纳经复核的稳定证据。
- 本次 CI 的 20 项 Python 测试、13 项 Node 测试均通过；FFDec 可执行性成功，但**导出可复现性不通过**。诊断工作流保留成功并发出警告，PR 继续 Draft。
