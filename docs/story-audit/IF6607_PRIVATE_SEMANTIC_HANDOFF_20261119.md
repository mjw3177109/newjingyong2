# IF 6607 私有语义复核交接单（2026-11-19）

## 已验收的基线

- GitHub 分支 `feature/html5-qstyle-foundation`，基线提交 `7320d7df3d65be35a9e14c9b2ab6d352ecbf3031`。
- [Actions #1544](https://github.com/mjw3177109/newjingyong2/actions/runs/44628434544) 四项作业 `completed/success`：`html5-tests`、`browser-smoke`、`swf-inventory`、`ffdec-java8-probe`。
- 真实 SWF 结构工件 `if6607-structure-evidence`：Artifact ID `14579798322`，ZIP 671 字节，工件摘要 `sha256:5674db7be614edab484615277c6f6a872dd76c01e5b82a89991f48ed42a9ad15`。**仅核对元数据及 CI 作业步骤，未在本次独立解包工件**。
- 审计目标：根时间轴第 55 帧、全局 DoAction 第 9 个、IF 动作字节偏移 6607。此前结构探针记录顺序后继 6612、分支目标 6623；本轮未重新独立解包复核该数值。
- 当前 `condition_stack_origin`、`true_path_effects`、`false_path_effects` 均未获得可复核的语义证据；已核实原作剧情事件 **0**，可映射事件 **0**。

## 下一步只做语义证据，不再机械扩充操作码窗口

1. 在获准接触原始内容的**隔离环境**核对 `jin.swf` 的 SHA-256：`d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`。记录 Java 8、FFDec 的准确版本、导出批次、动作流 SHA-256；任何指纹不符先停止。
2. 对 IF 6607 的栈顶条件进行逆向数据流追踪：逐条记录前驱栈深、Push/GetVariable/SetVariable/Less/Not 的输入输出关系，明确跨基本块来源及未知动态调用；不能只依据 12 条操作码窗口猜测变量名。
3. 对真假路径分别在隔离运行时以**相同初始状态**复现，记录状态差分：任务旗标、地图/帧、NPC、道具、金钱、战斗状态。区分静态可能副作用和实际观测副作用，记录复现步骤及两次结果。
4. 用第二次独立导出或独立解析核对字节偏移与条件/效果；如 FFDec 导出漂移，保留匿名哈希差异并暂停语义升级。
5. 仅将**脱敏摘要、定位哈希、证据级别和独立复核状态**填入 `docs/story-audit/README.md`；不提交脚本原文、原始路径、对白、音频、美术或第三方素材。
6. 原作剧情的改编和发行权利未确认前，保持 Draft PR，禁止把候选事件升级为可公开发行的原作剧情内容。

## 判定门禁

| 条件 | 未满足时状态 |
| --- | --- |
| SWF 与动作流双指纹一致 | `unverified` |
| IF 条件栈来源可解释且有证据 | `unverified` |
| 真假路径各有可复现状态差分 | `unverified` |
| 第二来源或独立复核通过 | `unverified` |
| 授权范围覆盖拟议使用方式 | 不得发布受保护剧情 |

**禁止**把 CI success、工件生成、操作码结构、FFDec 脚本数量或原创试玩事件当作已核实的原作剧情。

## 2026-11-19 16:20 PST：最新 CI 与证据边界复核

- [提交 `1b4b54e` 的 Actions #1546](https://github.com/mjw3177109/newjingyong2/actions/runs/44636612385) 已核对运行与作业：`completed/success`，`html5-tests`、`browser-smoke`、`swf-inventory`、`ffdec-java8-probe` 四项均成功。此为交接文档提交后的远端验收。
- 同一运行生成 `if6607-structure-evidence`：Artifact ID `14584731975`，ZIP 大小 671 字节，GitHub 提供的 ZIP 摘要 `sha256:6efdd9d23f27690a5fff0d0ffdf26858e2f88a1e38de05afca07d1b63cfef37d`，来源分支 `feature/html5-qstyle-foundation`，head `1b4b54e650ad8ab414002683213bdda82ee36e67`。本次核实的是工件元数据、运行作业及步骤，**没有独立解包本次 ZIP，也没有读取私有脚本操作数**。
- `swf-inventory` 的“Probe audited root IF 6607”及“Verify IF 6607 evidence identity and branch offsets”步骤均成功；`ffdec-java8-probe` 的 Java 8/FFDec 临时导出步骤成功。步骤通过不能证明条件栈、真假路径状态差分或剧情语义。
- **执行优先级**：先在授权隔离环境下载并解包该工件，校验其中的 `source_swf_sha256`、`action_sha256`、IF 偏移与真假后继；再对真实动作流执行跨基本块栈追踪及相同初态双路径差分，独立复核后才登记事件。仅在拿到上述证据时才更新原作事件数。
- 本轮没有新增已核实原作事件；`verified_story_events=0`、`ready_for_html5_mapping=0`，保持 Draft PR，不将原创试玩映射为原作剧情。

## 2026-11-19 17:21 PST：首次独立解包最新真实结构工件

- [Push Actions #1548](https://github.com/mjw3177109/newjingyong2/actions/runs/44645138936) 对提交 `fc44b6c6c7107923e7a02c2e2c0ca0ada09f2171` 的四项作业（HTML5、Chromium、SWF、FFDec）均为 `completed/success`。
- **本次已实际下载并解包** `if6607-structure-evidence` Artifact `14587953944`，内部仅有 `if6607_structure.json`；ZIP SHA-256 经本地重新计算为 `93fedcb45a34495765fcfc939aa81a4f3027b626a98a1612e65c2186ae3bbc52`，与 GitHub Artifact 元数据摘要一致。
- JSON 实际核验：`source_swf_sha256=d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`；`action_sha256=d1004ec542e6a47d89f882b6bc5e4bbfca5156d4ce03fa9d65646c61f45f5760`；根帧 `55`、全局 DoAction `9`、IF `6607`、顺序后继 `6612`、跳转目标 `6623`、相对位移 `11`。
- 新发现的**静态窗口关系**：顺序后继的前四条为 `6612:96`（Push）、`6622:1d`（SetVariable）、`6623:96`（Push）、`6628:1c`（GetVariable）；跳转目标窗口前四条为 `6623:96`、`6628:1c`、`6629:96`、`6637:48`（Less2）。窗口重叠偏移恰为 `[6623,6628]`，但这是有限线性窗口交集，**不是运行时执行轨迹或路径等价证明**。
- IF 前窗口尾部 `6604:48`（Less2）、`6605:12`（Not）、`6606:12`（Not）、`6607:9d`（If）；仅可确定这些操作码的静态排列，**不能确定操作数、栈顶值来源或真实条件含义**。
- **下一项有价值的私有验证**：在有权隔离环境读取 `6612` Push 的操作数类型和 `6622` SetVariable 的变量目标，核查这段赋值是否仅在顺序后继路径发生；同时逆向追踪 `6604` 的两个栈操作数，并在同初态下分别执行两条路径。静态存在 SetVariable 不等于确认发生了某项剧情旗标修改。
- 此次是结构证据的首次独立解包核验，不是语义审计完成。维持 `condition_stack_origin=unknown`、`true_path_effects=unknown`、`false_path_effects=unknown`、`verified_story_events=0`、`ready_for_html5_mapping=0`。
