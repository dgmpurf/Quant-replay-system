# Release Checkpoint v1.47.0

## Scope

v1.47.0 adds Metric Computation Phase 1 research-status integration and checkpoint documentation. The metric computation workflow remains report-only historical metric context for bounded samples and the allowed first metric set.

## Completed

- `metric-computation` creates report-only historical metric artifacts.
- `metric-computation-index`, `metric-computation-health`, and `metric-computation-status` expose artifact views.
- `research-status` now surfaces latest metric computation context, source lineage, bounded sample counts, result/summary counts, report path, next action, and safety flags.
- Later paper workflow priority is preserved; `PAPER_WORKFLOW_READY` is not overridden by metric computation context.
- Documentation now explains metric computation semantics and safety boundaries.

## Validation State

Known local dry-run status at checkpoint creation:

- `metric-computation`: `NO_METRIC_COMPUTATION_INPUT`
- latest dry-run id: `f8e1ff64e6aa`
- `metric-computation-index`: artifact discovery works
- `metric-computation-health`: `PASS`
- `metric-computation-status`: `METRIC_COMPUTATION_NO_INPUT`
- `research-status`: final workflow stage remains `PAPER_WORKFLOW_READY`

The no-input path remains valid and report-only. The no-allow ready path is represented by `READY_FOR_METRIC_COMPUTATION`: required inputs may be reviewable, but no metric computation artifacts are created without explicit allow. The explicit-allow path is represented by `METRIC_COMPUTATION_REPORT_CREATED`: bounded report-only historical metric artifacts may exist in diagnostics.

Validation completed for this checkpoint:

- `tests/test_metric_computation.py`
- related replay/training/evaluation/dashboard suites
- `pytest -m "not slow"`
- full `pytest`

## Safety Boundary

Metric Computation Phase 1 is limited to the allowed first metric set: `sample_count`, `label_coverage`, `average_return`, `median_return`, and `hit_rate`.

`METRIC_COMPUTATION_REPORT_CREATED` is report-only historical metric context. It is not strategy performance validation, not training_result, not weights, not model_version, not thresholds, not predictions, not calibrated probabilities, not feature importance, not stock_profile, not buy-review, not paper approval, and not trading.

The workflow also does not run current-candidates, does not build snapshots, does not compute forward labels, does not mutate cache, and does not write `data/raw`, `data/processed`, or `data/cache`.

## Current Interpretation

`METRIC_COMPUTATION_REPORT_CREATED` means bounded report-only metric artifacts exist for review. It is not an evaluation execution result, not model training, not paper approval, not strategy performance validation, and not trading permission.

## Recommended Next Task

Run `Metric Computation Acceptance / Governance Design Audit Report-Only v0.1` before any broader metric set, model training, evaluation governance, paper approval, or buy-review workflow is considered.
