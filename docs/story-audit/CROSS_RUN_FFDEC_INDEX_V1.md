# FFDec 跨 GitHub Actions 运行匿名索引对比 V1（2026-11-01）

## 发现与最小实现

同一个 `jin.swf` 在独立 CI 运行中曾出现 FFDec 语法计数 474/3 与 469/2；此前的双导出和三导出工具主要诊断**同一作业内部**的一致性，无法直接比较两个历史运行上传的脚本索引。

新增 `tools/compare_ffdec_run_baselines.py`，输入两次运行各自的 `ffdec-source-free-script-index` JSON（从 GitHub Actions Artifact 解压获得），验证两份索引的 SWF SHA-256、文件计数、匿名路径和内容 SHA-256，输出：

- 两份匿名导出清单指纹及脚本数量；
- 同匿名路径内容变化数量、只存在于某次运行的路径数量；
- 最多 20 个变化路径的 SHA-256 与变化类别（可用 `--limit` 调整到 1–100），不包含原始路径、脚本、台词或素材。

```bash
python tools/compare_ffdec_run_baselines.py \
  --index-a /private/run_A/ffdec_script_index.json \
  --index-b /private/run_B/ffdec_script_index.json \
  --out /private/cross_run_comparison.json
python -m unittest discover -s tests -p 'test_*.py'
```

## 验证边界与下一步

对比前必须确认两个 Actions 的原始 SWF SHA-256 一致，并记录 FFDec JAR、Java、工具代码版本。相同 SWF 不保证工具版本相同；相同索引也不能证明 FFDec 始终稳定。脚本内容发生变化的匿名路径，应在授权隔离环境内进一步检查 FFDec 私有导出与原始 AVM1 字节码，不得仅凭哈希推断剧情。

本工具的合成回归覆盖完全一致、同路径内容变化、路径增删、截断不影响计数、篡改/不同 SWF 拒绝；真实跨运行历史 Artifact 对比尚需执行，**已语义核实原作剧情事件仍为 0**。不改变原始 SWF、游戏玩法、其他仓库或发布状态。

## 2026-11-01 真实历史 Artifact 跨运行复核

已实际下载并解压 GitHub Actions 的匿名 `ffdec-source-free-script-index`，在隔离分析环境执行新增比较器：

- [2026-10-30 Actions #41054786935](https://github.com/mjw3177109/newjingyong2/actions/runs/41054786935)（[索引 Artifact #12975558396](https://github.com/mjw3177109/newjingyong2/actions/runs/41054786935/artifacts/12975558396)）对比 [2026-11-01 Actions #41297356839](https://github.com/mjw3177109/newjingyong2/actions/runs/41297356839)（[索引 Artifact #13079991362](https://github.com/mjw3177109/newjingyong2/actions/runs/41297356839/artifacts/13079991362)）：SWF SHA-256 均为 `d762a8f95d22b87916ae375968d425b4d4d34390bbc5d234338bfb58f85d4a30`；各 4,560 脚本，**同匿名路径内容变化恰好 1 个**，没有路径增删。
- 变化路径的匿名 SHA-256：`026c710e9fae5d272072a9055aea211c4a5a5750024397bece78d762b0b5f8bb`。旧索引记录该脚本 **604 字节 / 21 行 / timeline_goto 启发式 1**；新索引为 **11,381 字节 / 268 行 / timeline_goto 启发式 14**。两份全局 `timeline_goto` 启发式计数分别 **3,552** 和 **3,565**，恰好相差 13。该信息来自索引元数据，不是脚本正文或剧情语义。
- [2026-10-30 Actions #41063299964](https://github.com/mjw3177109/newjingyong2/actions/runs/41063299964)（[索引 Artifact #12982610406](https://github.com/mjw3177109/newjingyong2/actions/runs/41063299964/artifacts/12982610406)）对比 #41297356839：两份匿名索引完全一致，内容变化路径 **0**。

**结论边界：** 历史运行间歇差异已经缩小到一个匿名脚本及其字节数/行数变化，可能涉及反编译输出完整性，但尚不能确定 FFDec、执行环境或其他因素为根因；跨运行工具版本也需要核对。 `timeline_goto` 是启发式词法计数，不等于严格字面帧跳转数，更不是原作事件数。**已语义核实原作剧情事件仍为 0。** 下一步在可授权的私有运行环境里，对此匿名路径的导出完整性、原始 AVM1 对应字节码和 FFDec 日志进行交叉检查。

### 同源文件版本复核

通过 GitHub Git tree 在旧运行提交 `6881e527` 与新运行提交 `8e3a542` 逐项对照，`jin.swf` blob SHA-1 均为 `7ac95c272a71c06a86dc7dc772c647a0d1410f60`；`FFDec/ffdec.jar` 均为 `1cdf7c93c0c008e55cd94cc3bce39d7be0a82424`；`tools/index_ffdec_scripts.py` 均为 `c029d0241760074acb6299d4f5bd7a35219854be`；`tools/build_frame_jump_evidence.py` 均为 `468613a4b0e071f7ff4ef2922f8466b7673feaa1`。这些 Git blob 身份一致，进一步排除了上述四个文件在两次运行之间发生版本变更的解释，但仍不能排除 runner、Java/系统环境或 FFDec 运行时不确定性。
