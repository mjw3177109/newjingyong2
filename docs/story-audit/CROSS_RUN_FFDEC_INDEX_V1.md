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
