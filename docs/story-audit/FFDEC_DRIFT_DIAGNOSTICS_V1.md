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
