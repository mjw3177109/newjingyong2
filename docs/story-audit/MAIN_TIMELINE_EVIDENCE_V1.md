# 主时间轴动作标签证据索引 V1（2026-10-30）

本工具只扫描原始 `jin.swf` 顶层时间轴的 `ShowFrame`、`DoAction` 和 `FrameLabel` 标签，输出**帧号、标签计数、DoAction 内容的不可逆摘要**。不会输出解编译脚本、FrameLabel 原文、原始图片、音频或文本。精灵内部的嵌套脚本不属于本次统计范围。

## 运行

```sh
python tools/index_swf_timeline.py jin.swf --out reports/swf_main_timeline_evidence.json
python -m unittest discover -s tests -p 'test_*.py'
```

CI 的 `swf-inventory` 作业会自动执行并上传 `swf-main-timeline-evidence` Artifact。输出的 `source_swf_sha256` 可与 [SWF 结构报告](../SWF_SOURCE_EVIDENCE_20261030.md) 交叉核对。每个 `evidence_frames` 条目仅表示对应主时间轴帧存在动作标签或标签名，不能推断剧情事件、NPC、地图或战斗数值。

## 限制与下一步

- 本工具不解析 ActionScript 语义，不把 DoAction 数量解释为剧情事件数量。
- `FrameLabel` 只计数，标签名称不公开；`action_payload_digest` 仅用于同一输入的结构变化检测。
- 若声明帧数与观察到的 `ShowFrame` 数不同，`main_timeline_frame_count_matches` 会显式记录差异。
- 后续在有权利的隔离环境中，将帧位置与 FFDec 私有导出脚本对应，再人工核验条件与效果；原作已核实剧情事件数在此之前仍为 **0**。
