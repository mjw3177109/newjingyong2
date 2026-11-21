# SWF 精灵时间轴结构证据 v1（不含原始素材）

## 目的

主时间轴索引只记录顶层 `DoAction` 与 `FrameLabel`，而 `DefineSprite`（SWF Tag 39）有独立时间轴，可能包含另外的动作与帧标签。本工具新增逐精灵结构索引，避免把精灵脚本错误归为主时间轴，也避免因忽略精灵而遗漏审查入口。

## 实现和复现

- 入口：`python3 tools/index_swf_sprite_timeline.py jin.swf --out reports/swf_sprite_timeline_evidence.json`
- 使用 SWF Tag 39 的 `SpriteID`、声明帧数、内部 `ShowFrame`、`DoAction`（Tag 12）、`FrameLabel`（Tag 43）。
- 顶层 `DoInitAction`（Tag 59）仅按目标 `SpriteID` 计数关联，不公开脚本。
- 对每个有动作/帧标签的精灵帧，记录帧号、标签数量、动作数量与动作载荷 SHA-256 摘要。
- 拒绝截断的标签、重复 SpriteID、缺失 End 标签及无效压缩流；声明帧数不一致单独标记，避免误判。
- 只在 GitHub Actions 上传脱敏 JSON；不上传源脚本、文字、图片、音频或反编译目录。
- 合成 SWF 的 5 项测试位于 `tests/test_index_swf_sprite_timeline.py`。

## 限制与下一阶段

结构计数、帧号与 SHA-256 **不证明剧情事件语义**，`SpriteID` 也不是人物或地图编号。主时间轴与精灵时间轴不能直接相加为剧情条目。需要在有权利的隔离环境中核对具体 FFDec 代码、时间轴归属、条件变量及效果后，才可将事件登记为已核实。

真实 `jin.swf` 的精灵计数应以对应 GitHub Actions 生成的 `swf-sprite-timeline-evidence` Artifact 为准，禁止以合成测试数据冒充真实统计。原作已核实剧情事件仍为 **0**。
