# FFDec 双导出匿名差异诊断 V1（2026-10-30）

## 已证实的问题
相同 jin.swf 在此前 Java 8 + FFDec 独立导出中出现过 474/3 与 469/2 的字面帧跳转/简单守卫差异，且匿名脚本内容指纹发生变化。最近一次双导出稳定并不代表根因已排除。

## 本轮最小修复
新增 tools/diagnose_ffdec_drift.py，直接在 CI 临时目录核对两次导出文件与索引哈希，拒绝缺失、额外、被篡改的文件及符号链接。对不同内容的同一路径，仅输出匿名 SHA-256 路径、字节数、行数、首个差异行及粗粒度差异类别：line_endings_only、whitespace_normalized_equal、other_content_difference。示例最多 20 个，但总计数完整保留。

结果为 ffdec-source-free-drift-diagnostics Artifact。脚本原文、原始路径、图片和音频均不上传；分类只是排障提示，不代表两个脚本语义相同，更不是已核实的剧情事件。

## 复现与验收
- Python: python -m unittest discover -s tests -p 'test_*.py'
- FFDec Java 8: 由 feature 分支 push 的 ffdec-java8-probe 作业进行两次独立导出，并运行匿名差异诊断。
- 当出现 divergent 时检查差异类别和匿名行号；如属于 other_content_difference，下一阶段在隔离环境检查 FFDec 版本、并发/静态状态及具体导出阶段日志，不公开原作源代码。
- 本轮没有证明任何原始剧情触发条件、地图或战斗数值；已核实原作剧情事件数仍为 0。

## 来源
- 仓库原始输入：jin.swf
- 前期证据：docs/story-audit/FFDEC_REPRODUCIBILITY_V1.md
- CI 流程：.github/workflows/validate.yml

## 2026-11-01：精确前缀差异识别（增量）

针对历史跨运行中同一匿名脚本曾出现 604 字节与 11,381 字节的异常差异，双导出诊断新增 `a_exact_prefix_of_b`、`b_exact_prefix_of_a` 两类**严格字节前缀**关系，并在每个脱敏样本中记录 `common_prefix_bytes`。此功能可在下一次真实差异复现时区分“短文件恰为长文件前缀”和“文件内容从中途发生变化”，无需公开反编译文本。两项合成回归覆盖前缀方向及首个差异字节位置。

**证据限制：** 604/11,381 字节是历史跨运行索引观测值，未取得对应私有原文，故**不能声称历史异常已经被判定为截断或前缀**。严格前缀也不能单独证明 FFDec 截断、运行时原因、原作剧情或事件语义；需等待真实双导出差异并结合私有原始 AVM1 与日志复核。

## 2026-11-01：保留空白分隔的词边界（增量）

修复诊断分类器将所有空白直接删除后比较的问题：旧逻辑会把 `foo bar` 与 `foobar` 错误归为 `whitespace_normalized_equal`，尽管二者的词边界不同。现在仅在 `bytes.split()` 的分段序列完全相等时才给出该分类；原有 CRLF 归一化和严格前缀判定保持不变。新增合成回归覆盖词边界差异，原空白用例改为词边界不变的多空格场景。

该分类仍是**字节级排障提示，不是词法/语义等价证明**；历史报告中的旧分类不能自动按新规则追认。没有读取或发布原始 ActionScript 内容，原作已语义核实剧情事件仍为 0。
