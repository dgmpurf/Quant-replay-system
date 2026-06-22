# APPROVED_FOR_PAPER Phase 1

APPROVED_FOR_PAPER Phase 1 creates scoped, report-only approved-for-paper phase-1 context from complete upstream Paper Workflow Phase 1, Stock Profile, Active Model, Model Weight Versioning, training, metric, label, and replay-decision lineage.

Use:

```bash
python -m quant_replay_system.cli approved-for-paper-phase1
python -m quant_replay_system.cli approved-for-paper-phase1-index
python -m quant_replay_system.cli approved-for-paper-phase1-health
python -m quant_replay_system.cli approved-for-paper-phase1-status
python -m quant_replay_system.cli research-status
```

The workflow can report `NO_APPROVED_FOR_PAPER_PHASE1_INPUT`, `READY_FOR_APPROVED_FOR_PAPER_PHASE1`, or `APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED`.

`APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` means scoped metadata, lineage, review context, decision draft, limitations, overfit warning, safety flag, gate, and precondition artifacts exist for audit. It is not global APPROVED_FOR_PAPER, not real buy-review, not strategy performance validation, not current-candidates, not snapshot, not signal_semantics, not active stock_profile, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading.

Research-status exposes the latest APPROVED_FOR_PAPER Phase 1 run id, status/stage, health, artifact path, source paper-workflow lineage, source stock-profile lineage, source active-model lineage, source model-weight-versioning lineage, model reference ids, scoped report-only flags, report path, next action, and downstream safety fields. It preserves existing paper-workflow priority and does not treat the scoped phase-1 state as global approval.

Safety fields must remain false for real buy-review eligibility, buy-review allowed, strategy performance validation, trading allowed, current-candidates, snapshots, signal_semantics mutation, active stock_profile creation, promoted/production model creation, active thresholds, advisory predictions, active probabilities, broker/order/message/API side effects, cache mutation, and data writes.

Any future real buy-review, performance validation, paper approval, current-candidates, snapshot, signal semantics, model promotion, active threshold, advisory prediction, active probability, broker/order/message/API, or trading workflow requires a separate exact approval and a separate scoped implementation.
