# 根时间轴精灵放置引用证据 v1（source-free）

## 本轮目的

此前的 `swf-main-timeline-evidence` 与 `swf-sprite-timeline-evidence` 分别记录主时间轴和精灵内部动作/标签，但没有说明**哪些精灵 ID 被主时间轴直接引用**。本轮增加一个只读索引，为后续人工核实场景与时间轴上下文提供可复现入口。

## 实现

- `python3 tools/index_swf_sprite_placements.py jin.swf --out reports/swf_root_sprite_placements.json`
- 复用已测试的 FWS/CWS 解压及 SWF Tag 边界检查；先扫描顶层 `DefineSprite` (39) 的 SpriteID，再读取顶层 `PlaceObject` (4) 和 `PlaceObject2` (26) 的 CharacterId。
- `PlaceObject2` 只有 `HasCharacter` 标志存在时才读取 CharacterId；只移动已有实例的标签不当成新精灵放置。
- 仅对确认为顶层 DefineSprite 的 CharacterId 输出数值 `sprite_id`、根时间轴帧号、两种放置标签计数。对非精灵 CharacterId 只输出总数。
- `PlaceObject3` (70) 有可选 ClassName 等变长字段，当前**仅计数、不解析、不推测 CharacterId**；精灵内部放置不计入主时间轴直接放置。
- 原始脚本、字符串、路径、场景名称、图像及音频不进入输出；保留源 SWF SHA-256 以防混淆。
- 5 项纯合成 SWF 单元测试：直接引用、压缩一致性、嵌套隔离、PlaceObject3 保守处理、异常标签拒绝。

## 证据与边界

CI 产物：`swf-root-sprite-placement-evidence`。统计以具体成功的 GitHub Actions 运行日志和 Artifact 为准，不预先填写未经运行的真实数量。

**放置标签不是 NPC、地图或剧情事件**，一个 SpriteID 也不等于一个角色。尤其 PlaceObject3、嵌套精灵和时间轴运行时状态未解析，不能声称已恢复可见对象、地图关系或剧情。原作剧情语义已核实事件仍为 **0**。下一步在有权利的隔离环境中将结构证据与 FFDec 私有脚本、实际变量变化和触发条件交叉核验，逐事件登记，且不公开原作受保护素材。
