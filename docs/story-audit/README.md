# 原始剧情/事件审计表（仅存可验证摘要）

本表只记录可溯源证据，**不公开原始 SWF 的反编译源码、音视频、美术素材**。结构性 SWF Tag 统计不等于已验证的剧情事件。

| source_event_id | 事件/条件摘要 | 原始证据定位 | 可信度 | HTML5 对应 | 验证状态 |
| --- | --- | --- | --- | --- | --- |
| （暂无） | 尚未通过 FFDec 脚本定位确认具体剧情/事件 | 待 FFDec Java 8 探针与私有脚本审计 | 未验证 | 不可映射 | 待核验 |

## 已核实的结构性事实（不是剧情）

| 结构项 | 实测数量 | 证据 |
| --- | ---: | --- |
| DoAction (SWF tag 12) | 2468 | [2026-10-30 SWF 结构报告](../SWF_SOURCE_EVIDENCE_20261030.md) |
| FrameLabel (SWF tag 43) | 243 | 同上 |
| DefineSprite (SWF tag 39) | 372 | 同上 |

## 原创演示事件（非原作）

| demo_event_id | 触发条件 | 结果 | 证据 |
| --- | --- | --- | --- |
| DEMO_QUEST_ACCEPT | 靠近竹隐老人，任务未开始 | 接受竹影试炼 | `src/engine.js`、`tests/engine.test.mjs` |
| DEMO_HERB_PICKUP | 靠近清心草，未采集 | 获得清心草，旗标更新 | 同上 |
| DEMO_TRIAL_VICTORY | 试炼战斗敌人 HP 降至 0 | 标记战斗胜利 | 同上 |
| DEMO_QUEST_COMPLETE | 已采草且已胜利，再次与老人交互 | 任务完成，银两 +30（仅一次） | 同上 |

以上 DEMO 项均为原创占位数据，不能作为 SWF 复刻进度。

## 后续逐事件登记格式

每条原作事件仅在**真实脚本证据**存在后登记：
- `source_event_id`：文件哈希 + SWF 时间轴/脚本定位 + 本地稳定编号
- `source_evidence`：FFDec 导出路径、行号或字节码偏移、脚本 SHA-256（不公开脚本全文）
- `trigger`：原作确认的地图/人物/任务旗标条件
- `effects`：已确认的变量变化、道具、战斗、传送、对话摘要
- `html5_event_id`：对应实现及自动化测试名称
- `confidence`：已证实 / 部分证实 / 未证实
- `rights_status`：原作剧情改编和发布授权确认情况

不得将未经核实的故事记忆或网络攻略当作已解析的 SWF 证据。
