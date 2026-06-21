# Paper Workflow Phase 1

Paper Workflow Phase 1 creates report-only, research-governed paper workflow context from accepted upstream research artifacts. It is intentionally bounded to metadata, lineage, review context, draft paper decision rows, review queue rows, limitations, overfit warnings, safety flags, and status/report artifacts.

Use:

```bash
python -m quant_replay_system.cli paper-workflow-phase1
python -m quant_replay_system.cli paper-workflow-phase1-index
python -m quant_replay_system.cli paper-workflow-phase1-health
python -m quant_replay_system.cli paper-workflow-phase1-status
python -m quant_replay_system.cli research-status
```

The workflow can report `NO_PAPER_WORKFLOW_PHASE1_INPUT`, `READY_FOR_PAPER_WORKFLOW_PHASE1`, or `PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED`. The created state requires explicit allow text and complete upstream lineage from stock profile, active model, model weight versioning, training result, training result planning, metric extension, metric computation, metric evaluation, training evaluation, forward return labels, and frozen replay decisions.

`PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` is not APPROVED_FOR_PAPER, not real buy-review, not strategy performance validation, not current-candidates, not snapshot, not signal_semantics, not active stock_profile, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading.

Research-status exposes the latest Paper Workflow Phase 1 run id, status/stage, health, artifact path, source stock-profile lineage, source active-model lineage, source model-weight-versioning lineage, model reference ids, paper workflow artifact flags, report path, next action, and safety fields. It preserves later `PAPER_WORKFLOW_READY` priority and does not override the existing paper workflow status layer.

Safety fields must remain false for `approved_for_paper`, `approved_for_paper_created`, `paper_approval_created`, `real_buy_review_eligible`, `buy_review_allowed`, `strategy_performance_validated`, `trading_allowed`, `current_candidates_run`, `snapshot_built`, `signal_semantics_changed`, `active_stock_profile_created`, `promoted_model_created`, `production_model_created`, `active_thresholds_created`, `advisory_predictions_created`, `active_probabilities_created`, broker/order/message/API side effects, cache mutation, and data writes.
