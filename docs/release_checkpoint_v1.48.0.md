# Release Checkpoint v1.48.0

v1.48.0 adds Metric Extension Phase 1 research-status integration and checkpoint documentation. The metric extension workflow remains report-only historical metric context for bounded samples and the allowed extension metric set.

## Completed

- `metric-extension` creates report-only extended historical metric artifacts when explicitly allowed.
- `metric-extension-index`, `metric-extension-health`, and `metric-extension-status` expose artifact views.
- `research-status` now surfaces latest metric extension context, source lineage, requested and allowed extension metric sets, mapping counts, denominator counts, result counts, report path, next action, and safety flags.
- Later paper workflow priority is preserved; `PAPER_WORKFLOW_READY` is not overridden by metric extension context.
- Documentation now explains metric extension semantics and safety boundaries.

## Local State

- `metric-extension`: report-only command implemented.
- `metric-extension-index`: artifact discovery works.
- `metric-extension-health`: safety checks are available.
- `metric-extension-status`: latest-artifact status is available.
- `research-status`: final workflow stage remains `PAPER_WORKFLOW_READY` when later paper workflow artifacts exist.

`METRIC_EXTENSION_REPORT_CREATED` means report-only extended metric artifacts exist. It is not performance validation, not a training result, does not create weights, does not create model versions, does not create thresholds, does not create predictions or probabilities, does not create feature importance, does not create stock profiles, does not create buy-review eligibility, does not approve paper trading, does not allow live trading, does not call broker APIs, does not place orders, and does not send messages.

## Boundaries

- No strategy performance validation is claimed.
- No training result, weights, model version, thresholds, predictions, probabilities, or feature importance are created.
- No stock profiles, buy-review eligibility, paper approval, live trading, broker API calls, orders, or messages are created.
- No current-candidates generation, snapshot build, cache mutation, data/raw write, data/processed write, or data/cache write is part of this checkpoint.
- `docs/project_sources/` was not created; Project Source remains an external ChatGPT project artifact.

## Validation

Run:

```bash
python -m pytest tests/test_metric_extension.py -q
python -m pytest -m "not slow" -q
python -m pytest -q
python -m quant_replay_system.cli metric-extension
python -m quant_replay_system.cli metric-extension-index
python -m quant_replay_system.cli metric-extension-health
python -m quant_replay_system.cli metric-extension-status
python -m quant_replay_system.cli research-status
```

## Source Refresh

Project Source should be refreshed after commit and tag with this checkpoint, `docs/metric_extension.md`, `docs/local_research_dashboard.md`, `README.md`, and `SOURCE_UPDATE_NOTES_v1_48_0.md`. Do not recreate `docs/project_sources/`.

## Next Task

Run `Metric Extension Acceptance / Governance Design Audit Report-Only v0.1` before any broader metric set, training-result workflow, model/weights workflow, stock-profile workflow, buy-review workflow, paper approval, performance validation, or trading workflow is considered.

