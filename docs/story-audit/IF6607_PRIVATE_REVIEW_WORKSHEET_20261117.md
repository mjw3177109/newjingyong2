# IF 6607 私有语义复核工作单（待执行）

> 状态：**unverified / ready_for_html5_mapping=0**。此文件是可执行审查清单，不是已经获得的剧情证据。不得在公开仓库记录反编译源码、对白、原始文件路径、素材或密钥。

## 审查对象和已知边界

- 输入：仓库原始 `jin.swf`，需在隔离环境内计算 SHA-256 并写入私有记录。
- 结构定位：根时间轴第 55 帧、DoAction #9、AVM1 IF 偏移 6607；顺序后继 6612、跳转目标 6623。**这些仅是历史结构候选坐标，必须在本次实际导出中重新确认。**
- 当前没有经过复核的条件栈、真假分支副作用、地图/人物/任务/战斗归属；已核实原作事件 **0**。

## 私有环境执行步骤

1. 记录 `java -version`、FFDec 版本、SWF SHA-256、运行时间及两次独立导出批次 ID。仅在隔离临时目录操作，原始导出不得提交 Git。
2. 用现有 Java 8 + FFDec CI 探针及仓库审计工具重新定位帧 55 / DoAction #9；比较两次导出内容哈希。若漂移，保存私有差异定位并停止语义升级。
3. 在真实 AVM1 动作流中，从 IF 6607 向前追溯栈值来源，逐条标记常量、GetVariable、GetMember、CallFunction、CallMethod、比较/逻辑操作；遇到未知调用不得猜测条件。
4. 分别跟踪 fallthrough 6612 与 branch target 6623，直到共同汇合点或作用域边界；记录每条路径的 SetVariable、SetMember、帧跳转、对象变化及外部调用。不能仅靠静态反编译文本断言运行时效果。
5. 在有权执行的受控环境中，用可复现的前置状态分别触发两条路径，记录可观测状态前后差异；若无法触发，明确标为“静态推断、运行时未证实”。
6. 由第二名审查者独立检查偏移、条件栈和两路径效果；只有通过后才向 `docs/story-audit/README.md` 登记**脱敏摘要**，并在获得对应改编/发行权利后考虑 HTML5 映射。

## 私有审查记录字段（不可直接上传）

| 字段 | 要求 |
| --- | --- |
| source_sha256 / ffdec_version / java_version | 必填，真实命令输出 |
| export_a_id / export_b_id / hashes_equal | 必填；不一致时解释差异 |
| timeline / frame / action_tag / if_offset | 重新核实实际定位 |
| condition_stack_provenance | 每个栈操作数的来源与未知项 |
| false_path / true_path | 分别记录偏移链、调用、副作用 |
| reproducible_prestate / observed_poststate | 运行时双路径证据或明确缺失 |
| independent_reviewer / reviewed_at | 独立复核记录 |
| rights_scope / rights_evidence_ref | 未授权时标记 unknown，禁止发布 |

## 公开仓库允许的最小摘要

仅记录匿名证据 ID、SWF 哈希、稳定的偏移定位、非侵权的触发/效果概述、验证等级、对应 HTML5 测试及权利状态。**不得把 13 个 IF 结构候选、FFDec 导出成功或 CI success 记为 13 个已复刻事件。**

## 本工作单的验收标准

- [ ] 真实 SWF 哈希和工具版本已记录
- [ ] 两次导出一致，或差异已解释
- [ ] IF 6607 条件栈来源已复核
- [ ] 两条路径的副作用已复核
- [ ] 运行时可复现或明确说明无法复现
- [ ] 独立审查完成
- [ ] 权利范围确认后才建立可发布的剧情映射

在上述证据缺失时，维持 `unverified`，不填造剧情内容。
