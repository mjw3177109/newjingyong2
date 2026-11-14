# FFDec Java 8 私有日志指纹（V1）

## 发现与目的

同一仓库的 `jin.swf` 在相同 Git tree / Java 8 / FFDec JAR 的连续导出中，历史上出现单个匿名脚本内容漂移：同一路径在一次三导出中分别为 11,381 / 7,300 / 11,381 字节，另一次观察到 11,381 / 840 / 11,381 字节。现有匿名脚本索引能定位差异，却没有可跨 A/B/C 关联的 **FFDec CLI 原始运行日志指纹**。仅凭脚本差异不能判断根因。

## 本轮最小实现

`tools/summarize_ffdec_logs.py` 在 GitHub Actions **同一个 `ffdec-java8-probe` 作业**内读取临时 A、B 日志；仅在双导出脚本不一致、触发第三次导出时读取 C 日志。工具输出：每份日志的 SHA-256、字节数、行数，以及包含 `error` / `exception` / `warn` / `warning` 字样的行数（**粗略关键词命中，不是错误判定**）；按日志字节哈希分类两次或三次运行的相等关系。日志原文、临时文件名、路径、脚本名、源代码及素材不进入报告或 Artifact。所有原始日志随 CI 临时目录删除。

脱敏产物：`ffdec-source-free-log-fingerprints`。如果 FFDec 脚本漂移但日志指纹相同，说明**可见 CLI 日志没有反映字节差异**；若日志指纹不同，也可能只是时间、路径或进度信息不同，**不能推断故障原因**。三次日志中任意两份相同都不能选出权威反编译脚本。

## 验证

- 合成测试：`python -m unittest discover -s tests -p 'test_*.py'`（从仓库根目录运行）；覆盖两次/三次模式、脱敏、关键词命中、符号链接、非文件与超限日志。
- 真正 FFDec 执行：feature 分支 push CI 的 `ffdec-java8-probe`；必须检查新 Artifact 是否生成、脚本索引差异状态与日志指纹模式是否相关。
- 原作剧情/地图/战斗数值仍需结合原始 AVM1 字节码与隔离环境运行时人工核验；**本工具不会增加已语义核实的原作剧情事件数（仍为 0）**。

## 来源

- 仓库输入：`jin.swf`（只读）、`FFDec/ffdec.jar`。
- 已有真实差异证据：`docs/story-audit/FFDEC_DRIFT_DIAGNOSTICS_V1.md`。
- CI 调用位置：`.github/workflows/validate.yml`。
