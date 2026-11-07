# 根时间轴条件分支审查队列 v1

本轮新增 `tools/build_root_conditional_review_queue.py`，交叉校验真实 SWF 的根时间轴顶层 AVM1 `If` 指令索引与精灵 Depth 变化帧索引。输入为两份**脱敏结构报告**，不读取或公开原始 ActionScript、文字、图像或音频。仅在同一 SWF SHA-256、主时间轴帧数、动作标签数量、每帧动作数和 opcode 总计一致时建立候选队列；解析存在警告的动作标签自动排除。

优先审查“含 `If` 且同帧有精灵变化”的动作标签，其次是其他含 `If` 的动作标签。队列最多 50 条，按是否重合、条件分支数、跳转数、帧号及标签序号确定性排序。输出包含帧号、动作标签序号、动作标签 SHA-256、条件分支计数、是否同帧精灵变化和 `unverified` 状态。**同帧不代表因果关系；分支不代表剧情事件。** `verified_story_events` 固定为 0。

运行：
```bash
python tools/index_swf_timeline.py jin.swf --out reports/swf_main_timeline_evidence.json
python tools/index_swf_action_opcodes.py jin.swf --timeline reports/swf_main_timeline_evidence.json --out reports/swf_root_action_opcode_evidence.json
python tools/index_swf_root_depth.py jin.swf --out reports/swf_root_depth_evidence.json
python tools/correlate_root_action_depth.py --timeline reports/swf_main_timeline_evidence.json --depth reports/swf_root_depth_evidence.json --out reports/swf_root_action_depth_correlation.json
python tools/build_root_conditional_review_queue.py --opcodes reports/swf_root_action_opcode_evidence.json --correlation reports/swf_root_action_depth_correlation.json --out reports/swf_root_conditional_review_queue.json --limit 50
python -m unittest discover -s tests -p 'test_*.py'
```

CI 将执行真实 SWF 交叉校验并上传 `swf-root-conditional-review-queue` 脱敏 Artifact。具体候选数量以对应 CI 运行日志与 Artifact 为准，不能由此前的 608 条 `If` 指令推断。FFDec 的偶发漂移仍需单独诊断。后续在有改编审查权利的隔离环境中，按队列逐条核实时间轴归属、条件表达式、变量写入、跳转结果和场景/战斗效果；仅核实后的事件才进入剧情事件对照表。商业发布前须核实剧情改编及发布权利。
