# FFDec 源码隔离索引 V1（2026-10-30）

目的：对 Java 8 / FFDec 临时导出的文件生成**不包含源代码、文件名、目录名、对话或素材**的可复核证据索引。源文件在 runner 临时目录中生成并清理，GitHub Actions 仅上传脱敏 JSON。

## 证据字段

- \`source_swf_sha256\`：本次输入 \`jin.swf\` 的哈希。
- \`path_sha256\`：FFDec 输出目录内相对路径的 SHA-256，**不是原路径**。
- \`content_sha256\`：导出文件原始字节的 SHA-256，**不是脚本内容**。
- \`bytes\`、\`lines\`、\`extension\`：文件体量、行数和粗略后缀分类。
- \`hint_counts\`：对 \`if\`、\`else\`、\`gotoAndPlay/Stop\`、\`on\`、\`function\` 的简单文本计数。**不能据此认定任何剧情事件、变量含义或战斗数值**。

## 验证与使用

\`python3 -m unittest discover -s tests -p 'test_*.py'\` 运行隔离、稳定性与禁止泄漏测试。

\`python3 tools/index_ffdec_scripts.py /tmp/private/scripts --source-swf jin.swf --out /tmp/private/index.json\`

自动化流水线将上传 \`ffdec-source-free-script-index\` artifact；FFDec 原始导出文本仍在私有临时目录。审计员可在获授权的隔离环境中通过 \`path_sha256\` / \`content_sha256\` 对应原始文件，再人工核实具体触发条件与分支。公开仓库的 \`docs/story-audit/README.md\` 只有在完成**原始证据定位和语义核对**后才添加剧情事件行。

该索引是**来源目录**，不是剧情事件表，也不能代表 1:1 复刻进度。
