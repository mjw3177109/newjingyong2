# FFDec 三次导出漂移复核 V1（2026-10-31）

## 发现

在 2026-10-31 的 [Push CI #41224134467](https://github.com/mjw3177109/newjingyong2/actions/runs/41224134467) 中，同一份 jin.swf 经 Java 8 / FFDec 两次导出均成功，各 4,560 个脚本，但第一份得到 469 个字面帧跳转/2 个简单守卫，第二份得到 474/3。两份导出有 **1 个相同匿名路径的内容不同**，候选成员各有 1 个独有条目；当前仍不能判断哪份输出更可信，更不能据此恢复剧情。

## 最小改动

新增 tools/triage_ffdec_three_exports.py。只有前两次导出结果为 divergent 时，CI 才在第三个全新临时目录再次执行 FFDec，随后通过 index_ffdec_scripts.py 生成第三份匿名索引，再比较三个完整的 path_sha256 到 content_sha256 映射。

输出 reports/ffdec_three_run_triage.json，上传 ffdec-source-free-three-run-triage Artifact。记录三份索引的清单哈希、完整映射的相等关系、可观察到的单份异常模式、路径成员差异与内容差异计数，以及最多 20 个匿名路径哈希。三份原始解编译脚本和日志仍仅保存在 CI 临时目录并在退出时删除。

单独运行：

    python tools/triage_ffdec_three_exports.py --index-a A.json --index-b B.json --index-c C.json --out triage.json

## 解释边界

- a_c_equal 只表示 A/C 的**完整匿名内容映射**相同、B 不同；observed_outlier=b 不是判定 B 错误，更不是 FFDec 根因诊断。
- all_distinct 表示三份映射互不相同；all_equal 也不能证明 FFDec 永久稳定。
- 前两次稳定时不运行第三次，Artifact 可以不存在，这属于预期行为。
- 所有原作剧情事件仍为 **0 条语义核实**。索引、哈希和自动测试均不能代替脚本上下文、实际运行时事件、地图和变量副作用的人工复核。
- 该工具不上传原作台词、脚本、图片、音频、原始路径或地图数据，也不构成改编/商业发行授权。

下一步应使用多轮三次导出观察模式，定位特定匿名路径的间歇性差异，并在私有授权环境中审查 12 个 IF 优先目标，逐项核实真实条件与效果。

## 2026-11-01：三次导出全部配对字节差异（增量）

针对历史真实 all_distinct 模式，原有三次导出报告仅比较索引相等关系，原有字节级诊断仅比较 A/B。现在仅在 A/B 发生漂移并触发 C 导出时，复用已经测试的 diagnose_ffdec_drift.py，对 A/C 与 B/C 也分别验证匿名索引、字节数、行数、共同前缀及首个差异行，输出两个额外 JSON 到 ffdec-source-free-third-pair-byte-diagnostics Artifact。A/B 的原有诊断保留不变。

这使得三组配对差异均可复查，尤其能区分同一匿名路径三次不同内容的首次偏离位置。没有新增长期保存的反编译文件；全部私有脚本目录仍在作业结束时删除。三次导出不一致时不能指定任何一份为权威，已语义核实的原作剧情事件仍为 0。新增路径仅在真实漂移时执行，稳定时没有该 Artifact 属于正常情况。
