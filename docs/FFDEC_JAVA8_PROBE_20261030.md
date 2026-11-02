# FFDec / Java 8 可执行链路验收（2026-10-30）

## 实际执行证据

- 代码：[`tools/extract_reference.sh`](../tools/extract_reference.sh) 的同等 CLI 参数，在 GitHub Actions 隔离 runner 上运行。
- GitHub Actions：[run 41019489909](https://github.com/mjw3177109/newjingyong2/actions/runs/41019489909)，作业 `ffdec-java8-probe`。
- 运行时：Temurin OpenJDK 8u504（日志：`openjdk version "1.8.0_504"`）。
- SWF 输入：仓库 `jin.swf`，SHA-256 见 [SWF 结构证据](SWF_SOURCE_EVIDENCE_20261030.md)。
- 命令：`java -Djava.awt.headless=true -Xmx2g -jar FFDec/ffdec.jar -cli -export script <临时目录>/scripts jin.swf`。
- 实际退出码：**0**。
- 导出脚本文件计数（包括 FFDec 导出的不同脚本文件类型，未逐项人工复核）：**4,560**。
- 产物处理：脚本内容仅在临时 runner 中，退出时删除；不上传 Action artifact，不提交源码仓库。
- 同次 GitHub Actions：`html5-tests`、`swf-inventory`、`ffdec-java8-probe` 全部成功。

## 可确认与不可确认

**可确认**：仓库所带 FFDec Jar 可在 Java 8 的 Linux CI 中读取 `jin.swf` 并导出脚本文件，工具链可用。

**尚不可确认**：4,560 个文件并不代表 4,560 个剧情事件，也不代表已经分析出原始人物、地图、NPC、战斗数值或剧情主线。未完成对每个脚本的语义验证。

## 下一步

1. 为临时导出脚本生成**无源代码**的审计索引：脚本哈希、文件路径哈希、行数、候选控制流标记、所在时间轴/标签来源（可确认时）。
2. 由私有分析核对剧情触发条件、变量变化与分支，公开仅保留精炼事实摘要、证据指纹和测试链接。
3. 每条经过核实的原作事件单独录入 [story-audit](story-audit/README.md)，再对接 HTML5 的数据驱动事件引擎。

不得将私有导出文件、SWF 美术、音频或未经授权的原剧情直接发布。
