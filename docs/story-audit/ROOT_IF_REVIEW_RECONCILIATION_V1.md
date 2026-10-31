# IF 私有复核结果对账门禁 V1（2026-10-31）

新增 `tools/reconcile_root_if_review.py`，在不上传原作脚本、台词、地图、美术或音频的前提下，对比不可变的 12 条 IF 审查交接单与人工填写的私有复核副本。对账时严格检查原始 SWF SHA-256、review_id、原始帧/动作/分支偏移、候选数量与字段结构。

运行示例（未人工审查时使用同一文件，输出计数为 0）：

```sh
python tools/reconcile_root_if_review.py \
  --handoff reports/swf_root_if_audit_handoff.json \
  --reviewed reports/swf_root_if_audit_handoff.json \
  --out reports/swf_root_if_review_reconciliation.json
python -m unittest discover -s tests -p 'test_*.py'
```

私有审查者可复制交接单，逐条填写 `ffdec_script_sha256` 和条件、状态变化、地图上下文、运行时复现、独立复核的布尔确认，全部满足后才能把状态标为 `reviewed_private`。授权确认另行记录，不能由技术勾选代替法律证据。

**重要限制：** 该工具只能验证对账一致性，不能独立读取或理解私有脚本、验证布尔确认的真实性，也不能授予改编权。即使出现 `reviewed_private`，输出 `verified_story_events` 和 `ready_for_html5_mapping` 仍固定为 **0**。真实事件必须经过来源定位、运行时核验、独立复核及权利审查，才能在另外的正式剧情对照表登记。

当前没有任何真实复核结果，本轮新增的是可测试的防伪/防泄漏门禁，不是剧情恢复成果。FFDec 导出偶发漂移仍待解决。
