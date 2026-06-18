# Metric Extension Phase 1

Metric Extension Phase 1 is a report-only workflow for extending bounded historical metric context after Metric Computation Phase 1. It consumes metric-computation artifacts plus metric/evaluation, training/evaluation, forward-return-label, and replay-decision-freeze lineage, then writes extended metric review artifacts under diagnostics.

The workflow is intentionally narrow. It can create report-only extension rows for the allowed extension metric set:

- `benchmark_relative_return`
- `industry_relative_return`

Metric extension is not performance validation, not a training result, and not trading. It does not create weights, does not create model versions, does not create thresholds, does not create predictions or probabilities, does not create feature importance, does not create stock profiles, does not create buy-review eligibility, does not approve paper trading, does not allow live trading, does not call broker APIs, does not place orders, and does not send messages.

## Commands

- `metric-extension`
- `metric-extension-index`
- `metric-extension-health`
- `metric-extension-status`

The core command writes artifacts under `outputs/reports/manual_diagnostics/metric_extension_v0_1/<metric_extension_run_id>/` by default. The index, health, and status commands summarize those report-only artifacts for local review and `research-status` integration.

## Artifact Layout

Each run writes:

- `metric_extension_metadata.json`
- `metric_extension_report.md`
- `metric_extension_input_index.csv`
- `metric_extension_metric_definitions_used.csv`
- `metric_extension_sample_scope_used.csv`
- `metric_extension_denominator_rules_used.csv`
- `metric_extension_benchmark_mapping_used.csv`
- `metric_extension_industry_mapping_used.csv`
- `metric_extension_result_rows.csv`
- `metric_extension_summary.csv`
- `metric_extension_safety_flags.json`
- gate and guard result CSVs
- `recommended_next_task.md`

These artifacts are bounded report-only metric extension rows. They are not model output, training output, paper approval evidence, buy-review evidence, or trading permission.

## Status Semantics

`NO_METRIC_EXTENSION_INPUT` means required source artifacts, approval manifest, extension request manifest, benchmark/industry mappings, return rows, governance evidence, or safety inputs were not provided or were incomplete.

`READY_FOR_METRIC_EXTENSION` means the gates appear ready for report-only metric extension, but the explicit allow flag was not supplied. No extended metric result rows are created.

`METRIC_EXTENSION_REPORT_CREATED` means report-only extended metric artifacts were created after explicit allow for the bounded sample and the allowed extension metric set.

`METRIC_EXTENSION_HEALTH_FAILED` means the latest artifact failed health checks and must be repaired before its report-only context is used.

## Safety Boundary

The safety flags must keep downstream fields false, including training result creation, weights, model versions, thresholds, predictions, calibrated probabilities, feature importance, stock profiles, buy-review eligibility, paper approval, strategy performance validation, trading, broker/order/message/API/cache side effects, data writes, current-candidates generation, snapshot builds, and signal-semantics changes.

`report_only=true` and `diagnostic_only=true` remain true.

## Artifact Views

`metric-extension-index` discovers metric extension run folders and exports one row per artifact. It preserves source lineage, requested and allowed metric sets, mapping counts, denominator counts, result counts, safety flags, and artifact paths.

`metric-extension-health` checks that required files are present and that the safety boundary is intact. It fails if an artifact claims unsupported metrics, training results, weights, model versions, thresholds, predictions or probabilities, feature importance, stock profiles, buy-review eligibility, paper approval, strategy performance validation, trading/broker/order/message/API/cache side effects, data writes, current-candidates generation, snapshot builds, or signal-semantics changes.

`metric-extension-status` summarizes the latest artifact and reports the current stage, health, lineage, counts, next action, and safety statement.

## Research-Status Integration

`research-status` exposes the latest metric extension fields, including source metric-computation lineage, upstream metric/evaluation, training/evaluation, forward-return-label, and replay-decision-freeze lineage, requested and allowed extension metric sets, bounded sample counts, mapping counts, denominator counts, result counts, report path, next action, and safety flags.

Later paper workflow priority is preserved. If paper artifacts already indicate `PAPER_WORKFLOW_READY`, the final workflow stage remains `PAPER_WORKFLOW_READY` while metric extension context stays visible as report-only historical metric context.
