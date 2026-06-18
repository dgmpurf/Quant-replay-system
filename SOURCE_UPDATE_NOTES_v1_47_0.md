# Source Update Notes v1.47.0

## Summary

Metric Computation Phase 1 is now represented in `research-status` as report-only historical metric context.

## Added Context

- `metric-computation-status` is visible in unified research status.
- The dashboard exposes latest metric computation run id, status/stage, health, source lineage, allowed first metric set, bounded sample counts, result counts, report path, next action, and safety flags.
- Later paper workflow priority remains preserved; `PAPER_WORKFLOW_READY` is not overridden.

## Safety Boundary

`METRIC_COMPUTATION_REPORT_CREATED` means report-only historical metric artifacts were created for a bounded sample and the allowed first metric set: `sample_count`, `label_coverage`, `average_return`, `median_return`, and `hit_rate`.

It is not strategy performance validation, not training_result, not weights, not model_version, not thresholds, not predictions, not calibrated probabilities, not feature importance, not stock_profile, not buy-review, not paper approval, and not trading.

No ChatGPT Project Source files are created in this update. The `docs/project_sources/` folder remains absent.

## Next Source Refresh

After a future commit and tag, refresh the ChatGPT Project Source with the v1.47.0 checkpoint, metric computation docs, and source update notes.
