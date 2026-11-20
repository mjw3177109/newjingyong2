# IF 6607 Push 类型真实工件复核（2026-11-20）

## 来源与可复现定位
- GitHub Actions [#1581](https://github.com/mjw3177109/newjingyong2/actions/runs/44701824626)，PR #1，head `59426790ca4d8e31425ad03d4635868e40f69d21`。
- `swf-inventory` 成功执行真实 SWF Push 类型探针并上传 `if6607-push-type-evidence`，Artifact ID `14613391581`，ZIP 大小 429 字节，GitHub ZIP digest `sha256:4596456408dc81b015558298d2f169e6466b052d108f42c155d8d91097fe4a54`。
- 本次**独立下载并解包**该 ZIP，读取唯一文件 `if6607_push_types.json`；仅公开操作数类型代码和数量，不公开字面值、原始脚本或素材。

## 已核实的静态结果
| 指令偏移 | 操作 | Push 类型代码 | 值个数 | 备注 |
| --- | --- | --- | --- | --- |
| 6612 | Push | 8, 7 | 2 | 该 Push 恰在 6622 SetVariable 前结束 |
| 6622 | SetVariable | — | — | 操作码边界已确认 |
| 6623 | Push | 8 | 1 | 非上述 SetVariable 的直接前驱 |
| 6629 | Push | 7 | 1 | 非上述 SetVariable 的直接前驱 |

AVM1 Push 类型代码 8 表示常量池 8-bit 索引；7 表示 32-bit 整数。**这是编码类型，不是实际变量名、常量池内容或赋值语义**。本工件的 `set_variable_target`、`set_variable_value`、`condition_stack_origin` 均为 `unknown`，`verified_story_events=0`。

## 同一 CI 的失败及影响
- 四项作业中 `html5-tests`、`browser-smoke`、`swf-inventory` 成功；`ffdec-java8-probe` 失败。
- [失败作业日志](https://github.com/mjw3177109/newjingyong2/actions/runs/44701824626)：`actions/setup-java@v4` 获取 Temurin Java 8.0.514+1 后，`tar` 报 `gzip: stdin: not in gzip format`，退出码 2；FFDec 步骤被跳过。故本轮**没有新的 FFDec 导出结果**，不可将该运行称为 4/4 成功。
- 此失败发生于 Java 安装/下载解包阶段，尚无证据证明是 SWF 或 FFDec 解析错误；后续应单独重试并检查下载产物 HTTP 状态、格式及完整性，避免直接改动 SWF 解析逻辑。

## 下一阶段门禁
1. 对同一真实动作流做栈回溯：确认 6612 的两个 Push 值如何流入 6622 SetVariable，检查跨分支栈深和常量池来源；不要仅由指令相邻推断写入内容。
2. 逆向追踪 6604 Less2、6605/6606 Not 到 6607 If 的条件栈来源。
3. 在授权隔离环境对真假路径进行相同初态的运行差分，并用独立解析/FFDec 复核；必要时修复 Java 8 下载稳定性。
4. 仅经语义和独立证据复核的原作事件才进入正式对照表；保持 `verified_story_events=0`、PR Draft、禁止未经授权发行受保护剧情。

本次仅为真实工件取证与故障记录，不代表原作剧情复刻完成。
