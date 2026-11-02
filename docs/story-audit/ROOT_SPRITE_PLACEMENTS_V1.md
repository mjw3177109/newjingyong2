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

## 2026-10-30：PlaceObject3 增量解析（v2）

- `tools/index_swf_sprite_placements.py` 新增 SWF tag 70 的安全 CharacterId 读取：先读 Flags1、Flags2、Depth，再按 HasClassName 或 (HasImage 且 HasCharacter) 跳过 NUL 结尾的可选类名，最后仅在 HasCharacter 存在时读取 UI16 CharacterId。
- 类名原文、后续可选字段、原始美术与脚本均不进入输出；无字符 ID 的移动/更新标签只计数。未知 CharacterId 仅进入非精灵合计，不猜测对象身份。
- 新增合成测试覆盖无 CharacterId、普通 CharacterId、ClassName、HasImage、CWS/FWS、非精灵 ID、截断与未终止类名；旧的“PlaceObject3 全部未解析”口径已废弃。
- 输出 schema 升级为 `swf-root-sprite-placement-evidence-v2`，新增 `placeobject3_tag_count`、`placeobject3_without_character_count` 和每帧 `placeobject3_count`。原 v1 数字不能与 v2 直接混用。
- **仅解析主时间轴的直接引用**；没有处理嵌套放置、运行时遮挡、实例生命周期或语义关联。后续仍需从隔离环境中的 FFDec 脚本逐条核实剧情/地图/战斗事件。已核实原作剧情事件仍为 0。
- 实际 SWF 计数和 CI 通过状态必须以本次提交对应的成功 Actions 日志为准，不能预先推定全部 1,188 个 PlaceObject3 标签均为精灵放置。
