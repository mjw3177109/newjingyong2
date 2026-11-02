# 原始 SWF 根时间轴 IF 审查任务包 V1

本轮新增 `tools/build_root_if_review_packets.py`，从**同一 SWF 指纹**的四份已生成结构证据（候选队列、条件边、状态访问提示、局部控制流图）构建逐条 IF 审查任务包。每个任务有稳定匿名 `review_id`、根帧号、DoAction 标签序号、动作 SHA-256、IF 字节偏移、跳转目标、顺序后继、局部可达性、前八条记录内的状态访问指令类型与偏移。

## 审查规则

- 交叉校验源文件 SHA-256、候选顺序、动作哈希、帧号、标签序号、IF/Jump 数量、IF 目标与 CFG 后继及访问提示。证据不一致直接失败。
- 优先选择**局部控制流图中语法可达**的 IF：可达 +8、同帧精灵变化 +4、前八条记录存在状态访问 +2、分支与顺序后继不同 +1。这样不可达 IF 不会挤占有限的 12 个优先审查名额；仅属于静态结构优先级，**不证明运行时可达，更不证明剧情重要性**。同时输出全量可达/不可达数量及本批可达数量。
- `trigger`、`effects`、`map_id`、`html5_event_id` 保持 `null`，`review_status=unverified`，`verified_story_events=0`。
- 输出不含 ActionScript 源码、字符串、变量名、脚本原始路径、美术、音频或任何原作素材。原始 SWF 仍在既有 CI 结构审计中验证，脚本不复制或上传。

## 执行与产物

```bash
python -m unittest discover -s tests -p 'test_*.py'
python tools/build_root_if_review_packets.py \
  --queue reports/swf_root_conditional_review_queue.json \
  --edges reports/swf_root_conditional_edges.json \
  --access reports/swf_root_state_access_hints.json \
  --cfg reports/swf_root_local_control_flow.json \
  --out reports/swf_root_if_review_packets.json --limit 12
```

GitHub Actions `swf-inventory` 将运行并上传 `swf-root-if-review-packets`。真实数量、测试及上传结果应以对应提交的 Actions 为准。

## 下一阶段

在具备合法授权的隔离环境中，按 `review_id` 对照私有 FFDec 脚本和原始时间轴，逐条记录条件表达式、变量写入、实际运行结果与证据偏移。只有独立核实的事件才可填入正式 [剧情/事件审计表](README.md)。本阶段仍然**没有核实任何原作剧情事件**，也不能据此宣称完成 1:1 复刻或拥有商业改编权。
