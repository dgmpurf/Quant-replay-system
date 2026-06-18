# Metric Computation Phase 1

Metric Computation Phase 1 is a report-only historical metric workflow. It consumes accepted Metric / Evaluation Phase 1 planning context and bounded Training / Evaluation sample rows, then writes historical metric artifacts for review.

This workflow is intentionally narrow. It can compute only the allowed first metric set for a bounded sample:

- `sample_count`
- `label_coverage`
- `average_return`
- `median_return`
- `hit_rate`

It is not strategy performance validation, not training_result, not weights, not model_version, not thresholds, not predictions, not calibrated probabilities, not feature importance, not stock_profile, not buy-review, not paper approval, and not trading.

## Commands

- `metric-computation`
- `metric-computation-index`
- `metric-computation-health`
- `metric-computation-status`

The core command writes artifacts under `outputs/reports/manual_diagnostics/metric_computation_v0_1/<metric_computation_run_id>/` by default. The index, health, and status commands summarize those report-only artifacts for local review and `research-status` integration.

## Artifact Layout

Each run writes:

- `metric_computation_metadata.json`
- `metric_computation_report.md`
- `metric_computation_input_index.csv`
- `metric_computation_metric_definitions_used.csv`
- `metric_computation_sample_scope_used.csv`
- `metric_computation_denominator_rules_used.csv`
- `metric_computation_result_rows.csv`
- `metric_computation_summary.csv`
- `metric_computation_safety_flags.json`
- gate and guard result CSVs
- `recommended_next_task.md`

These artifacts are bounded report-only metric rows. They are not evaluation execution, model output, training output, paper approval evidence, buy-review evidence, or trading permission.

## Status Semantics

`NO_METRIC_COMPUTATION_INPUT` means required Metric / Evaluation Phase 1 context, Training / Evaluation sample rows, approval manifest, request manifest, governance evidence, or safety inputs were not provided or were incomplete.

`READY_FOR_METRIC_COMPUTATION` means the gates appear ready for a report-only metric computation run, but the explicit allow flag was not supplied. No metric computation artifacts are created beyond diagnostics.

`METRIC_COMPUTATION_REPORT_CREATED` means report-only historical metric artifacts were created after explicit allow for a bounded sample and the allowed first metric set.

`METRIC_COMPUTATION_HEALTH_FAILED` means the latest artifact failed health checks and must be repaired before its report-only context is used.

## Required Contracts

The metadata records lineage to the source Metric / Evaluation Phase 1 planning run and source Training / Evaluation Phase 1 run where available. It includes source status and health fields, allowed and requested metric sets, unsupported metric flags, sample counts, eligible and quarantined sample counts, label coverage counts, result/summary row counts, artifact paths, and safety flags.

The safety flags must keep these values false:

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

`metric-computation-index` discovers metric computation run folders and exports one row per artifact. It preserves source lineage, counts, safety flags, and artifact paths.

`metric-computation-health` checks that required files are present and that the safety boundary is intact. It fails if an artifact claims unsupported metrics, training_result, weights, model_version, thresholds, predictions or probabilities, feature importance, stock profiles, buy-review eligibility, paper approval, strategy performance validation, trading/broker/order/message/API/cache side effects, data writes, current-candidates generation, snapshot builds, or signal semantics changes.

`metric-computation-status` summarizes the latest artifact and reports the current stage, health, counts, next action, and safety statement.

## Research-Status Integration

`research-status` exposes the latest metric computation fields, including source Metric / Evaluation Phase 1 lineage, source Training / Evaluation Phase 1 lineage, allowed metric set, requested metric set, bounded sample counts, result counts, report path, next action, and safety flags.

Later paper workflow priority is preserved. If paper artifacts already indicate `PAPER_WORKFLOW_READY`, the final workflow stage remains `PAPER_WORKFLOW_READY` while metric computation context stays visible as report-only historical metric context.
