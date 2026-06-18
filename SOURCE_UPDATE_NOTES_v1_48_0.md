# Source Update Notes v1.48.0

Metric Extension Phase 1 is now represented in `research-status` as report-only historical metric extension context.

## Added Context

- `metric-extension-status` is visible in unified research status.
- The dashboard exposes latest metric extension run id, status/stage, health, source metric-computation lineage, upstream metric/evaluation, training/evaluation, forward-return-label, and replay-decision-freeze lineage, requested and allowed extension metric sets, bounded sample counts, mapping counts, denominator counts, result counts, report path, next action, and safety flags.
- Later paper workflow priority remains preserved; `PAPER_WORKFLOW_READY` is not overridden.

## Safety Interpretation

`METRIC_EXTENSION_REPORT_CREATED` is report-only context. It is not performance validation, not a training result, does not create weights, does not create model versions, does not create thresholds, does not create predictions or probabilities, does not create feature importance, does not create stock profiles, does not create buy-review eligibility, does not approve paper trading, does not allow live trading, does not call broker APIs, does not place orders, and does not send messages.

It also does not run current-candidates, does not build snapshots, does not mutate cache, and does not write data/raw, data/processed, or data/cache.

## Project Source Refresh

Project Source should be refreshed after commit and tag with:

- `docs/release_checkpoint_v1.48.0.md`
- `docs/metric_extension.md`
- `docs/local_research_dashboard.md`
- `README.md`
- `SOURCE_UPDATE_NOTES_v1_48_0.md`

ChatGPT Project Source is maintained outside Git; do not recreate `docs/project_sources/`.

## Recommended Next Branch

The next branch should be `Metric Extension Acceptance / Governance Design Audit Report-Only v0.1`, unless code or docs reveal a safer preceding audit. Do not proceed directly to training_result, weights, model_version, thresholds, predictions, probabilities, feature importance, stock_profile, buy-review, paper approval, performance validation, or trading.
