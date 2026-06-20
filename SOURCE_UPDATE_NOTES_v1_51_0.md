# Source Update Notes v1.51.0

## Scope

This update integrates report-only Model Weights / Versioning / Threshold / Prediction Phase 1 artifact views into `research-status`.

## Files Updated

- `src/quant_replay_system/local_research_dashboard.py`
- `src/quant_replay_system/cli.py`
- `tests/test_local_research_dashboard.py`
- `README.md`
- `docs/local_research_dashboard.md`
- `docs/model_weight_versioning.md`
- `docs/release_checkpoint_v1.51.0.md`

## Safety Notes

`MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED` is report-only. It is not an active model, not a promoted model, not a production model, not active parameters, not active thresholds, not advisory predictions, not active probabilities, not active feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.

The integration preserves `PAPER_WORKFLOW_READY` priority in `research-status`.

docs/project_sources/ is intentionally absent from Git. Do not create it for this checkpoint; refresh any external source bundle manually only after tag/release procedures require it.

## Next Task

Run a report-only model-weight-versioning acceptance / governance design audit before any active model promotion, advisory prediction production, stock_profile work, buy-review work, paper approval, performance validation, or trading workflow.
