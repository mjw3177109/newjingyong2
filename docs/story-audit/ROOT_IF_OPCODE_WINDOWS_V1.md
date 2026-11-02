# 根时间轴 IF 原始字节码上下文 V1（2026-10-31）

## 本轮目的

为已有的 12 个优先 IF 审查目标增加**直接取自 `jin.swf` 的操作码上下文**，使私有审查者能按 `review_id`、帧号、DoAction 序号和 IF 字节偏移定位证据，并快速判断是否存在比较运算、变量读取、调用或不透明控制流。此前仅有分支坐标和前八条状态访问提示，不能看出更一般的操作码类别。

## 执行

```bash
python tools/index_root_if_opcode_windows.py jin.swf \
  --packets reports/swf_root_if_review_packets.json \
  --out reports/swf_root_if_opcode_windows.json --width 12
python -m unittest discover -s tests -p 'test_*.py'
```

GitHub Actions 的 `swf-inventory` 作业将上传 `swf-root-if-opcode-windows` Artifact，包含每个目标 IF 前最多 12 条**线性字节码记录**的偏移与安全分类、比较操作码数量、是否存在分支或不透明控制流、SWF 指纹和审查 ID。对 SWF 指纹、动作 SHA-256、审查 ID、帧号、IF 字节偏移、分支目标和局部可达性进行独立复核；不一致直接拒绝。

**证据边界：** 线性前驱不等于执行路径，更不等于条件表达式。即使出现比较操作码，也不能推断比较对象、值、NPC、任务、地图、战斗机制或剧情含义。不会导出 Push 操作数、变量名、字符串、ActionScript、原始路径、音频或图像。所有条目仍是 `unverified`，`verified_story_events=0`。

## 后续

在有权利的隔离环境中，对照本次字节码类别与 FFDec 私有脚本，并以运行时证据核实触发条件、状态副作用、地图和事件效果。只有独立复核的真实事件才能加入正式剧情对照表；本次输出不能作为改编发布授权或 1:1 完成证明。

## 保守直线前驱边界（2026-11-01 增量）

原有 `preceding_opcode_classes` 是纯线性前 12 条记录，可能跨越无条件跳转、IF 跳转目标、Return/Throw 或不透明控制指令，不能直接当作 IF 条件的执行前驱。本轮保留原始字段以兼容旧审查数据，增加 `straight_line_preceding_record_offsets`、`straight_line_preceding_opcode_classes`、`straight_line_preceding_record_count` 和 `straight_line_boundary_limited`。保守边界包括动作入口、分支目标、跳转/条件/终止指令后的记录及不透明控制指令后的记录。新的短窗口仅用于避免把明显跨控制流的指令错误拼接成条件，**不证明这些指令实际执行、栈值来源或原作剧情语义**。新增 3 个合成 AVM1 回归测试（跳转目标、不透明控制、IF 自身为分支目标）。

## IF 入口分支汇合标记（2026-11-01 增量）

新增从原始 AVM1 记录边界独立计算的 `if_incoming_syntactic_edges`（仅源字节偏移与 branch/fallthrough 类型）、`if_incoming_syntactic_source_count`、`if_has_multiple_syntactic_predecessors`、`if_has_backward_or_self_incoming_branch`、`if_is_action_entry`、`if_has_opaque_immediate_predecessor`。这些字段用于提醒审查者：即使前驱操作码窗口看起来连续，IF 仍可能是多路汇合点或循环入口，不能将某个线性前驱当作唯一条件来源。

该图只表示**语法边**，包含可能不可达的分支；不透明控制、函数体、运行时跳转可能引入图中未覆盖的行为。**不导出 Push 内容、变量名、源码或媒体，也不证明条件、地图、剧情或运行时可达性**。新增 3 项合成字节码测试（分支汇合、自环、普通直线入口），原作已核实剧情事件仍为 0。

## IF 入边的结构可达性筛选（2026-11-01 增量）

先前的 `if_incoming_syntactic_source_count` 会包含静态不可达的前驱：例如无条件 Jump 跳过的记录仍可能在字节排列上紧邻 IF，导致审查者误认为存在两条有效来源。现在独立从原始 DoAction 首记录遍历本地语法后继，增加 `if_incoming_reachable_syntactic_source_count`、`if_incoming_unreachable_syntactic_source_count`、`if_incoming_unreachable_syntactic_source_offsets` 和 `if_has_multiple_reachable_syntactic_predecessors`。保留旧字段，避免破坏已有审查产物；新增合成回归覆盖不可达的线性前驱、两条可达前驱和自环。

**限制：** 这只是忽略不透明控制语义的静态图遍历，不是运行时执行证据。被标为结构不可达的记录也可能通过 AVM1 不透明指令或外部行为到达。不能据此确认剧情、地图、任务、人物或战斗数值；已核实原作事件仍为 0。
