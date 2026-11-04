# 2026-11-04：第 55 帧 IF 候选与 FFDec 三次导出证据

## 本轮来源与边界

- GitHub Actions Push：[#41887040731](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731)，提交 `c374cc92948cc7e63ed3d41960ae36d207cc003c`。
- 输入：仓库 `jin.swf`，文件大小 24,206,878 bytes；本次审计记录的 SWF SHA-256：`d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`。
- FFDec：仓库 `FFDec/ffdec.jar`，由 Temurin Java `1.8.0_504` 执行。三次独立 CLI 导出均退出码 0，每次索引到 4,560 个脚本。
- 原始导出目录和 FFDec 日志留在 CI 临时目录，作业结束清理；以下仅记录脱敏哈希、计数和字节码坐标，不含脚本原文、原始路径、台词、素材或媒体。

## 三次导出复核

本次真实结果：

| 项目 | 结果 |
| --- | ---: |
| A / B / C 导出脚本数 | 4,560 / 4,560 / 4,560 |
| A 与 B 完整匿名内容映射 | divergent |
| B 与 C 完整匿名内容映射 | equal |
| 三次导出观察模式 | `b_c_equal`，A 为本次观察到的 outlier |
| 路径成员变化 | 0 |
| 同一路径内容变化 | 1 |
| 两次导出候选 A / B | 100 / 100 |
| A/B 双导出一致候选 | 99 |
| 与第三次 C 内容一致的保留候选 | 99 |
| 第三次导出额外隔离候选 | 0 |
| 已语义核实原作剧情事件 | **0** |

唯一变化路径的匿名 SHA-256：`19ce41914ff7c65c7f520027e13882e0b6e2171c0dd0a28dde3d6b3808b77dfb`。A/B 诊断显示大小分别为 7,582 / 11,381 bytes，行数 162 / 268，共同前缀 7,497 bytes，首个不同位置均在第 158 行，类别为 `other_content_difference`。三次对照为 B/C 完整映射相等，因此本次可保留的 99 个候选也通过第三份内容哈希核对。

**解释限制：** A 是本次三次采样中的 outlier，不代表 A 一定错误；B/C 相同也不构成 FFDec 的规范输出或跨运行确定性证明。99 是三次内容一致的匿名语法候选数，不是剧情事件数，也不代表语义已确认。

证据 Artifact：
- [匿名脚本索引](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13350614970)
- [三次导出对照](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13352775447)
- [第三次导出候选隔离结果](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13352026958)
- [双导出差异诊断](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13352850293)

## 第 55 帧根时间轴 IF 结构候选

同一 SWF 指纹下，结构审查包与操作码窗口交叉核验得到 12 个目标。下表中的 `comparison` 和 `write hints` 只是有限字节码窗口中的操作码类别计数，不是已恢复的比较值、变量身份或实际状态副作用。

| rank | candidate_id | root frame / DoAction | IF offset | branch target | fallthrough | comparison opcodes | branch / fallthrough write hints | status |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `cdb2bff81843c4578e6514aa` | 55 / 9 | 6523 | 6539 | 6528 | 1 | 0 / 1 | unverified |
| 2 | `92e54231fd673ea6e8f6e689` | 55 / 9 | 6556 | 6572 | 6561 | 2 | 2 / 1 | unverified |
| 3 | `3d9a54e4fd91c051c87c6050` | 55 / 9 | 6607 | 6623 | 6612 | 1 | 0 / 1 | unverified |
| 4 | `c129bb397ede9b1ad08adc07` | 55 / 9 | 6640 | 6656 | 6645 | 2 | 0 / 1 | unverified |
| 5 | `a521de797f0ce64b42757bc0` | 55 / 9 | 6673 | 6689 | 6678 | 2 | 0 / 1 | unverified |
| 6 | `d2522a904088bab58e3bc662` | 55 / 9 | 6706 | 6722 | 6711 | 2 | 0 / 1 | unverified |
| 7 | `be27ee49a3e64c4efe1bb529` | 55 / 9 | 6739 | 6755 | 6744 | 2 | 0 / 1 | unverified |
| 8 | `69081877e99309e0428958c0` | 55 / 9 | 6772 | 6788 | 6777 | 2 | 0 / 1 | unverified |
| 9 | `f0546f46b12d7fa9301bed1b` | 55 / 9 | 6805 | 6821 | 6810 | 2 | 0 / 1 | unverified |
| 10 | `e569b99ba59ce00dab97877c` | 55 / 9 | 6838 | 6854 | 6843 | 2 | 0 / 1 | unverified |
| 11 | `eabaf0a62e40305a2c98a8c3` | 55 / 9 | 6871 | 6887 | 6876 | 2 | 0 / 1 | unverified |
| 12 | `9d3e97d6eb97c36ec39d89cc` | 55 / 9 | 6904 | 6920 | 6909 | 2 | 0 / 1 | unverified |

来源 Artifact：
- [IF 操作码窗口](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13351048155)
- [交接窗口交叉核验](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13350788644)
- [私有人工审查交接单（当前为空白）](https://github.com/mjw3177109/newjingyong2/actions/runs/41887040731/artifacts/13351842034)

交叉核验确认 12/12 个候选在同一 SWF 指纹、根帧、DoAction 序号、IF 偏移及双后继坐标上对齐；12/12 的有限后继窗口均有不同的写操作码提示计数。它只证明审计定位与脱敏结构摘要自洽，**不证明** IF 谓词、变量名/值、运行时路径、地图、NPC、任务、道具、战斗或剧情含义。

## 原作事件对照表状态

正式表不把结构候选写成剧情事件：

| source_event_id | 触发条件 | 效果 | HTML5 映射 | 状态 |
| --- | --- | --- | --- | --- |
| （暂无） | 未经私有脚本上下文及运行时核实 | 未知 | none | 未验证 |

`verified_story_events=0`，`ready_for_html5_mapping=0`。当前 12 条只作为私有审查候选；不得用原创试玩事件填充原作事件表。

## 下一阶段

1. 在获授权、隔离且不向公开 CI 上传脚本内容的环境中，对 12 条候选逐项查看私有 FFDec 上下文，先追踪 IF 条件栈与变量初始化/写入来源。
2. 对每条候选分别验证分支成立与不成立两条路径，并核对时间轴/精灵归属；无法证实的地图、对话、任务、道具和战斗字段保持 unknown。
3. 先对 6607、6640 两个已有操作码结构对照目标建立独立私有复核记录；仅在脚本哈希稳定且有运行时/独立交叉证据后，才允许登记 verified。
4. 权利确认独立于技术核验；在改编与发布权利未确认前，不将受保护剧情纳入可公开发行版本。

本报告记录的是可复查的结构性进展，不是全量 1:1 复刻完成声明。
