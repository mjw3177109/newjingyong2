# IF 6607 隔离取证执行单（2026-11-14）

> 状态：**unverified / ready_for_html5_mapping=0**。这是待执行的核验协议，不是已取得的原作剧情证据，也不包含原始反编译代码、台词或素材。

## 已有结构定位（来源）
- 文件：仓库内 `jin.swf`，根时间轴第 55 帧、DoAction 9。
- 候选：AVM1 IF 动作偏移 **6607**；顺序后继 **6612**；已记录跳转目标 **6623**。
- 来源：[ROOT_FRAME55_CANDIDATES_20261104.md](ROOT_FRAME55_CANDIDATES_20261104.md) 与 [README.md](README.md) 中 2026-11-08 的取证门禁。
- 注意：这些偏移仅代表既有结构审计记录，未在本文件中重新反汇编或确认语义。

## 私有隔离环境执行步骤
1. 固定输入：记录 `jin.swf` SHA-256、字节数、FFDec 版本、Java 8 版本、导出命令和 UTC 时间；仅在授权环境保存原始脚本。
2. 独立导出 A/B：逐文件哈希比较；若内容不同，停止语义升级并记录差异范围与重现命令。
3. 核对动作流：定位根帧 55 / DoAction 9 / 6607，核验动作长度、下一指令 6612 和分支目标 6623 是否落在有效动作边界；偏移不匹配则标记 `blocked_offset_mismatch`。
4. 重建 IF 入栈来源：从该 IF 前最近的控制流汇合点沿所有可达路径做栈追踪，列出每个入栈操作、变量读取、函数调用及可能的副作用；遇到未知 opcode、动态调用或不确定栈深，标记 `blocked_stack_unknown`，不得猜测条件。
5. 分别运行条件真/假路径：在可复现的同一初始状态下记录前后状态差异、时间轴跳转、事件回调和可观测效果；无法控制输入或无法运行两条路径时标记 `blocked_runtime`。
6. 独立复核：另一名审查者对照原始动作流、导出哈希和两路径记录复核；仅将脱敏摘要及证据哈希写入公开审计表。

## 最小证据记录（不包含受保护原文）
| 字段 | 当前值 |
| --- | --- |
| candidate_id | root-f55-doaction9-if6607 |
| source_sha256 | 待采集 |
| ffdec_version / java_version | 待采集 |
| export_A_sha256 / export_B_sha256 | 待采集 |
| offset_6607_verified | 未核实 |
| stack_condition_verified | 未核实 |
| true_path_effects_verified | 未核实 |
| false_path_effects_verified | 未核实 |
| independent_reviewer | 待复核 |
| rights_evidence_ref | 未提供 |
| html5_event_id | 不可映射 |
| verification_status | unverified |

## 验收门禁
只有输入及双导出可复核、偏移和栈条件完整、真假分支均有可重现记录、独立复核完成且权利范围得到确认后，才可考虑将其登记为已核实事件并映射到 HTML5。任何一项失败都保持 0 条已核实事件；**不因 CI 成功而自动放行**。
