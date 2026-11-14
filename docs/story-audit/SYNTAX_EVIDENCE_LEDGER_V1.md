# FFDec 脚本语法证据定位表 v1（非剧情复刻）

2026-10-30 起，`tools/build_evidence_ledger.py` 使用**同一次 FFDec Java 8 临时导出**的脚本目录、原始 `jin.swf`、`ffdec_review_queue.json`，生成 `ffdec_syntax_evidence_ledger.json`。GitHub Actions 上传的仅是匿名 JSON，不上传反编译源码、脚本路径、字符串常量、人物名字、图片或音频。

## 证据链与数据限制

`jin.swf` SHA-256 → 脱敏脚本索引的路径/内容 SHA-256 → `SRC-` 候选 ID → 该脚本中 `if`、`else`、`gotoAndPlay/Stop`、`on/onClipEvent`、`function` 的**1 起始行号**及匹配次数。

工具严格核对原始 SWF 哈希、脚本文件数量、候选 ID、每个候选脚本内容哈希；发生变更或文件丢失则失败。每类提示最多输出 16 个去重行号，并报告是否截断；行号对应 FFDec 导出文件而非 SWF 字节码偏移，FFDec 版本或导出顺序变化可能改变行号。

**这些是正则表达式识别的语法提示，可能匹配注释或字符串，并不等于 AST 或真实事件语义。** `source_event_id`、`trigger`、`effects`、`html5_event_id` 均保留为 `null`，`semantic_status=unverified`，已核实剧情事件数仍为 **0**。不能把它们当作剧情、地图、武功或战斗数值。

## 后续审核步骤

在有权利的隔离环境中，用候选的 `path_sha256` 与 `content_sha256` 定位原始导出脚本，结合行号查看其上下文和时间轴，逐条验证触发条件、变量变化、转场与结果。**只有实际确认且附证据的事件**才能进入 `docs/story-audit/README.md` 的正式剧情/事件对照表。公开仓库只保留必要的独立事实摘要和哈希，不公开原始代码。

测试：`python -m unittest discover -s tests -p 'test_*.py'`；本文件所述工具的 4 个单元测试均使用合成脚本。
