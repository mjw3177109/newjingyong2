# 原作剧情事件语义核验门禁 v1（2026-11-03，2026-11-04 增补）

> 本文是审计流程和证据模板，不是已核实的原作剧情。已核实原作事件：**0**。不得把原创试玩任务、FFDec 控制流候选数或帧跳转次数计入原作还原率。

## 输入与保密边界

- 只在获授权的隔离环境中读取仓库原始 `jin.swf`，使用 Java 8 + FFDec；记录 SWF SHA-256、FFDec 版本、Java 版本、导出批次及每个脚本 SHA-256。
- 对同一 SWF 独立导出两次，先执行仓库现有的匿名索引、双导出比较与稳定候选筛选。若目标脚本出现内容漂移，标记 `blocked_export_drift`，不得登记为“已证实”。
- 原始 ActionScript、脚本中的原文对白、可识别美术/音频、原始路径不得进入公开 PR、CI Artifact 或日志。公开记录仅放匿名脚本 ID、摘要、散列、证据类型和审核状态。
- **公开记录采用严格字段白名单**：不允许附加 `source_text`、`raw_actionscript`、`dialogue`、`source_path`、媒体 URL 等字段；证据摘要限制为单行短文本，不能把原始脚本/对白当作摘要粘贴。该检查是防误提交门禁，不是完整的版权内容识别器。

## 单条事件核验步骤

1. **定位**：确认 DoAction 所在 SWF 时间轴（主时间轴或具体 DefineSprite）、帧号、脚本匿名 ID、导出哈希和可复现的语法行号/字节码偏移。仅知道“第 55 帧 Action 9”不足以判定事件。
2. **条件**：人工复核条件栈，追踪读取的变量及其初始化和写入位置；区分布尔判断、帧跳转、UI 分支和真正的任务触发。
3. **效果**：核实条件成立和不成立两条路径；记录变量写入、对话调用、地图切换、道具变更或战斗调用。无法证明的字段写“未知”，不可猜测。
4. **交叉证据**：在独立导出或原始字节码中复核相同控制流；必要时用获授权的本地运行观察验证，记录可重复步骤。单次 FFDec 反编译的启发式文本不等于充分证据。
5. **权利检查**：即使事件已核实，也必须单独确认改编/发布权限，才可将受保护剧情内容用于可公开发行版本。

## 审核记录模板（每个候选一条）

| 字段 | 必填说明 |
| --- | --- |
| `candidate_id` | 匿名、稳定的候选标识 |
| `swf_sha256` / `export_pair_id` | 原文件指纹与两次导出批次 |
| `timeline_and_frame` | 已证实的时间轴归属、帧号；否则 unknown |
| `script_sha256` / `evidence_offset` | 脚本哈希和行号或字节码偏移 |
| `trigger_summary` | 仅在条件链核实后填写的非原文摘要，最多 240 字符、单行 |
| `effect_summary` | 仅在效果链核实后填写的非原文摘要，最多 240 字符、单行 |
| `negative_path_checked` | 是否核实条件不成立路径 |
| `cross_check` | 独立导出/字节码/授权运行验证方式，最多 240 字符、单行 |
| `status` | unverified / partial / verified / blocked_export_drift |
| `html5_mapping` | 未验证时必须为 none；实现后填写测试路径 |
| `rights_status` | unknown / authorized / restricted |
| `rights_scope` | none / analysis_only / adaptation_only / distribution_only / adaptation_and_distribution |
| `rights_evidence_ref` | 授权或限制文件的短引用；无证据时为 null |

## 发布门禁

- `rights_status=authorized` 必须有非占位的 `rights_evidence_ref`，并明确声明授权范围；不能仅凭一个布尔值或口头描述通过。
- `publication_ready=true` 必须同时满足：`status=verified`、`rights_status=authorized`、`rights_scope=adaptation_and_distribution`、存在具体权利证据引用、存在具体 HTML5 映射。
- `analysis_only`、`adaptation_only` 或 `distribution_only` 均不能通过商业发行门禁。权利未知时 scope 必须为 `none`；权利受限时不得声明改编/发行授权。
- 这只是仓库内的最低机器门禁，引用文件仍需由项目负责人核验签署方、权利主体、地域、期限、平台、商业使用及再许可范围；机器校验不能替代法律审查。

## 登记规则与下一阶段

- `verified` 必须同时满足：稳定来源、时间轴归属、条件及效果双路径、交叉证据和可定位记录；否则只能标为 `partial` 或 `unverified`。
- 首个目标是历史候选“第 55 帧 Action 9”：先确定它属于哪条时间轴，再核实变量读写与分支；目前**不声明其剧情语义**。
- 原作剧情事件对照表只接纳 `verified`，部分证据留在私有审核记录；公开汇总不包含受保护原文。
- HTML5 原创试玩的现有自动化测试可继续用于底座稳定性，但不能替代原作事件核验。
