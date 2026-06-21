# Stock Profile

`stock-profile` creates report-only Stock Profile Phase 1 research-governed artifacts from approved upstream active-model, model-weight-versioning, training-result, metric, label, and replay-decision lineage.

The workflow is deliberately bounded. `STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED` means stock-profile research artifacts exist for governance review only. It is not active stock_profile, not real buy-review, not paper approval, not performance validation, not current-candidates, not snapshot, not signal_semantics, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, and not trading.

## Commands

Core workflow:

```bash
python -m quant_replay_system.cli stock-profile
```

Artifact views:

```bash
python -m quant_replay_system.cli stock-profile-index
python -m quant_replay_system.cli stock-profile-health
python -m quant_replay_system.cli stock-profile-status
```

Dashboard integration:

```bash
python -m quant_replay_system.cli research-status
```

## Statuses

- `NO_STOCK_PROFILE_INPUT`: no stock-profile input package was supplied.
- `READY_FOR_STOCK_PROFILE_PHASE1`: all gates are reviewable, but explicit report-only artifact creation was not allowed.
- `STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED`: report-only research-governed stock-profile artifacts were created after explicit allow.
- `STOCK_PROFILE_HEALTH_FAILED`: artifact views found a safety or contract failure.

## Artifact Boundaries

The workflow may create report-only files under `outputs/reports/manual_diagnostics/stock_profile_v0_1/<stock_profile_run_id>/`, including stock profile metadata, input index, lineage matrix, factor coverage summary, symbol coverage, market regime coverage, metric summary, limitations, overfit warnings, safety flags, and recommended next task.

These files are governance artifacts only. They must not be interpreted as active stock_profile creation, real buy-review eligibility, paper approval, strategy performance validation, current-candidates generation, snapshot creation, signal_semantics changes, promoted model state, production model state, active thresholds, advisory predictions, active probabilities, broker instructions, order instructions, or trading authorization.

## Research Status

`research-status` includes the latest stock-profile fields:

- `latest_stock_profile_run_id`
- `latest_stock_profile_status`
- `latest_stock_profile_health_status`
- `latest_stock_profile_workflow_stage`
- `stock_profile_artifact_path`
- `ready_for_stock_profile_phase1`
- `stock_profile_phase1_executed`
- `stock_profile_phase1_report_only_artifacts_created`
- `stock_profile_metadata_created`
- `stock_profile_input_index_created`
- `stock_profile_lineage_matrix_created`
- `stock_profile_factor_coverage_summary_created`
- `stock_profile_symbol_coverage_created`
- `stock_profile_market_regime_coverage_created`
- `stock_profile_metric_summary_created`
- `stock_profile_limitations_created`
- `stock_profile_overfit_warnings_created`
- `stock_profile_safety_flags_created`
- `stock_profile_source_active_model_run_id`
- `stock_profile_source_active_model_status`
- `stock_profile_source_active_model_health_status`
- `stock_profile_source_model_workflow_run_id`
- `stock_profile_source_model_weight_versioning_status`
- `stock_profile_source_model_weight_versioning_health_status`
- `stock_profile_model_weight_reference_id`
- `stock_profile_model_version_id`
- `stock_profile_parameter_version_id`
- `stock_profile_active_stock_profile_created=false`
- `stock_profile_real_buy_review_eligible=false`
- `stock_profile_buy_review_allowed=false`
- `stock_profile_approved_for_paper=false`
- `stock_profile_strategy_performance_validated=false`
- `stock_profile_trading_allowed=false`
- `stock_profile_current_candidates_run=false`
- `stock_profile_snapshot_built=false`
- `stock_profile_signal_semantics_changed=false`
- `stock_profile_promoted_model_created=false`
- `stock_profile_production_model_created=false`
- `stock_profile_active_thresholds_created=false`
- `stock_profile_advisory_predictions_created=false`
- `stock_profile_active_probabilities_created=false`

Later paper workflow artifacts preserve final `PAPER_WORKFLOW_READY` priority. Stock-profile fields remain visible as context only.

## Safety Rules

The health/status layer fails or warns if artifacts imply unsafe downstream use. In particular, the workflow must not create or imply:

- active stock_profile creation;
- real buy-review eligibility;
- paper approval;
- performance validation;
- current-candidates generation;
- snapshot creation;
- signal_semantics changes;
- promoted model or production model state;
- active thresholds;
- advisory predictions or active probabilities;
- live trading, broker API calls, order placement, or messages.

The next governance step should remain report-only until a later accepted design explicitly scopes stock-profile acceptance, buy-review eligibility, paper workflow validation, or trading review.
