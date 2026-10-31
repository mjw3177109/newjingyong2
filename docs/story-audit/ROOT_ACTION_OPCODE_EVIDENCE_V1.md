# 根时间轴 DoAction 指令结构审计 v1

新增 `tools/index_swf_action_opcodes.py`，在不公开 ActionScript 源码、字符串、素材的前提下，对 `jin.swf` 根时间轴 `DoAction` 标签进行 AS1/AS2 顶层指令记录解析。统计 `If`、`Jump`、`GotoFrame`、`GotoLabel`、`WaitForFrame`、`DefineFunction` 等指令，记录帧号、动作标签序号、SHA-256 与有限错误类别。**函数定义体不递归解析**，条件真假、变量读写、跳转目标所属时间轴、剧情语义均未验证。

```bash
python tools/index_swf_timeline.py jin.swf --out reports/swf_main_timeline_evidence.json
python tools/index_swf_action_opcodes.py jin.swf --timeline reports/swf_main_timeline_evidence.json --out reports/swf_root_action_opcode_evidence.json
python -m unittest discover -s tests -p 'test_*.py'
```

工具对源 SWF 指纹、根时间轴 ShowFrame 和 DoAction 总数进行独立交叉校验；解析错误记录为 `parse_warnings`，不能视作已成功解析的逻辑。GitHub Actions 上传仅包含数字、帧号、SHA-256 和预定义错误类别的 `swf-root-action-opcode-evidence` Artifact。此报告不包含 ActionScript 原文、标签名称、素材或音频。`verified_story_events` 恒为 0。

下一步应在有权利的隔离环境中针对少量带条件分支的动作帧复核脚本的具体条件、变量写入、运行时跳转及对应地图/任务/战斗效果。语义核实前不得计入已复刻剧情，商业发布前须核实改编和发布权利。

## v1.1：AVM1 条件跳转目标边界审计（2026-10-30）

对顶层 `If` (0x9D) 和 `Jump` (0x99) 且负载长度正确的指令，按**有符号 16 位相对偏移**计算目标字节位置，并与本 `DoAction` 标签内解析到的顶层动作记录起点比对。新增三个脱敏计数：

- `branch_targets_on_record_boundary`：目标落在已解析动作记录起点（包含 `ActionEnd`）；
- `branch_targets_inside_record`：目标在当前标签字节范围内，但不在顶层记录起点；
- `out_of_bounds_branch_targets`：目标在本标签范围外（原有指标）。

仅统计结构，不输出偏移、指令字节、字符串或原始路径；函数体仍保持不透明。**落在记录内部不等于原作程序必然错误**：可能涉及未解析的函数体或特殊控制流，需要隔离环境人工核实，不能自动修正或据此认定剧情条件。分支目标边界通过不代表触发条件、变量效果或故事事件已验证。已有条件候选队列仍保持 `unverified`，原作已核实事件为 **0**。

测试覆盖向前、向后、跳至 `ActionEnd` 和记录内部目标。真实 `jin.swf` 的三类计数必须以本次新增代码的 GitHub Actions 结果为准，不引用旧运行结果臆测。
