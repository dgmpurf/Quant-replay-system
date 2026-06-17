# Metric / Evaluation Phase 1

Metric / Evaluation Phase 1 is a report-only structural planning workflow. It prepares metric definitions, sample scope, denominator rules, and governance plans from Training / Evaluation Phase 1 context so a later acceptance/governance task can decide whether evaluation should proceed. It does not compute metrics, does not create metric/evaluation result rows, does not execute evaluation, does not create training_result, does not train weights, does not create model_version, does not optimize thresholds, does not create predictions, does not create calibrated probabilities, does not create feature importance, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not claim strategy performance validation, and does not authorize trading.

## Commands

- `metric-evaluation`
- `metric-evaluation-index`
- `metric-evaluation-health`
- `metric-evaluation-status`

The core command writes artifacts under `outputs/reports/manual_diagnostics/metric_evaluation_v0_1/<metric_evaluation_run_id>/` by default. The index, health, and status commands summarize those report-only artifacts for local review and `research-status` integration.

## Artifact Layout

Each run writes:

- `metric_evaluation_metadata.json`
- `metric_evaluation_report.md`
- `metric_evaluation_input_index.csv`
- `metric_definition_plan.csv`
- `sample_scope_plan.csv`
- `denominator_rule_plan.csv`
- `benchmark_industry_plan.csv`
- `metric_evaluation_gate_results.csv`
- `metric_evaluation_blocker_matrix.csv`
- `metric_evaluation_safety_flags.json`
- `recommended_next_task.md`

These artifacts are structural planning context only. They are not metric results, evaluation outputs, model outputs, or performance evidence.

## Status Semantics

`NO_METRIC_EVALUATION_INPUT` means the required Training / Evaluation Phase 1 context, request manifest, governance evidence, or safety inputs were not provided or were incomplete.

`READY_FOR_METRIC_EVALUATION_PLANNING_ARTIFACTS` means the gates appear ready for a report-only structural planning run, but the explicit allow flag was not supplied. No planning artifacts are created beyond diagnostics.

`METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED` means report-only metric/evaluation planning artifacts were created after explicit allow. It does not compute metrics. It does not create metric/evaluation result rows, execute evaluation, create training_result, train weights, create model_version, optimize thresholds, create predictions, create calibrated probabilities, create feature importance, create active stock profiles, create real buy-review eligibility, apply paper approval, claim strategy performance validation, or authorize trading.

`METRIC_EVALUATION_HEALTH_FAILED` means the latest artifact failed health checks and must be repaired before its structural planning context is used.

## Required Contracts

The metadata records lineage to the source Training / Evaluation Phase 1 run, source forward-return label run, and source replay decision freeze run where available. It includes source status and health fields, sample and label counts, symbol counts, label name sets, metric definition counts, sample scope counts, denominator rule counts, artifact paths, and safety flags.

The planning artifacts define what a future metric/evaluation workflow would need to review:

- metric definitions and intended labels;
- sample scope and denominator rules;
- benchmark/industry comparison planning;
- gate and blocker matrices;
- health/status integration expectations.

The safety flags must keep these values false:

- `metrics_computed`
- `metric_result_rows_created`
- `metric_evaluation_results_created`
- `evaluation_execution_completed`
- `training_allowed`
- `weights_trained`
- `training_result_created`
- `model_version_created`
- `thresholds_optimized`
- `predictions_created`
- `calibrated_probabilities_created`
- `feature_importance_created`
- `stock_profile_allowed`
- `active_stock_profile_exists`
- `stock_profile_created`
- `buy_review_allowed`
- `real_buy_review_eligible`
- `approved_for_paper`
- `strategy_performance_validated`
- `trading_allowed`
- `order_placed`
- `broker_api_called`
- `message_sent`
- `llm_api_called`
- `external_api_called`
- `cache_mutated`
- `data_raw_written`
- `data_processed_written`
- `data_cache_written`
- `current_candidates_run`
- `snapshot_built`
- `signal_semantics_changed`

`report_only=true` and `diagnostic_only=true` remain true.

## Artifact Views

`metric-evaluation-index` discovers metric/evaluation run folders and exports one row per artifact. It preserves source lineage, counts, safety flags, and artifact paths.

`metric-evaluation-health` checks that required files are present and that the safety boundary is intact. It fails if an artifact claims metrics were computed, metric/evaluation result rows were created, evaluation execution completed, training_result was created, weights were trained, model_version was created, thresholds were optimized, predictions or probabilities were created, feature importance was created, stock profiles were created, buy-review eligibility was created, paper approval was applied, strategy performance was validated, trading/broker/order/message/API/cache side effects occurred, data was written, current-candidates ran, snapshots were built, or signal semantics changed.

`metric-evaluation-status` summarizes the latest artifact and reports the current stage, health, counts, next action, and safety statement.

## Research-Status Integration

`research-status` exposes the latest metric/evaluation fields, including source Training / Evaluation Phase 1 lineage, source forward-label and replay-freeze lineage, sample counts, label counts, planning artifact booleans, report paths, and safety flags. Later paper workflow priority is preserved: if paper artifacts already indicate `PAPER_WORKFLOW_READY`, the final workflow stage remains `PAPER_WORKFLOW_READY` while metric/evaluation context stays visible.

Metric / Evaluation Phase 1 is intentionally separated from any future metric result rows, evaluation execution, training_result, model_version, stock_profile, buy-review, paper approval, strategy performance validation, or trading workflow.
