# Active Model

`active-model` creates report-only Active Model Phase 1 research-governed artifacts from approved upstream model-weight-versioning lineage.

The workflow is deliberately bounded. `ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED` means active-model reference artifacts exist for research governance review only. It is not active production serving, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, not stock_profile, not buy-review, not paper approval, not performance validation, not current-candidates, not snapshot, not signal_semantics, and not trading.

## Commands

Core workflow:

```bash
python -m quant_replay_system.cli active-model
```

Artifact views:

```bash
python -m quant_replay_system.cli active-model-index
python -m quant_replay_system.cli active-model-health
python -m quant_replay_system.cli active-model-status
```

Dashboard integration:

```bash
python -m quant_replay_system.cli research-status
```

## Statuses

- `NO_ACTIVE_MODEL_INPUT`: no active-model input package was supplied.
- `READY_FOR_ACTIVE_MODEL`: all gates are reviewable, but explicit report-only artifact creation was not allowed.
- `ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED`: report-only research-governed active-model artifacts were created after explicit allow.
- `ACTIVE_MODEL_HEALTH_FAILED`: artifact views found a safety or contract failure.

## Artifact Boundaries

The workflow may create report-only files under `outputs/reports/manual_diagnostics/active_model_v0_1/<active_model_run_id>/`, including active model metadata, active model pointer, registry entry, active parameter pointer, activation status, rollback plan, input index, lineage matrix, limitations, overfit warnings, safety flags, a report, and recommended next task.

These files are governance artifacts only. They must not be interpreted as a promoted model, production model, active thresholds, advisory predictions, active probabilities, stock_profile creation, buy-review eligibility, paper approval, strategy performance validation, current-candidates generation, snapshot creation, signal_semantics changes, broker instructions, order instructions, or trading authorization.

## Research Status

`research-status` includes the latest active-model fields:

- `latest_active_model_run_id`
- `latest_active_model_status`
- `latest_active_model_health_status`
- `latest_active_model_workflow_stage`
- `active_model_artifact_path`
- `ready_for_active_model`
- `active_model_executed`
- `active_model_artifacts_created`
- `active_model_pointer_created`
- `active_model_registry_entry_created`
- `active_parameter_pointer_created`
- `active_model_activation_status_created`
- `active_model_rollback_plan_created`
- `active_model_input_index_created`
- `active_model_lineage_matrix_created`
- `active_model_limitations_created`
- `active_model_overfit_warnings_created`
- `active_model_safety_flags_created`
- `active_model_source_model_workflow_run_id`
- `active_model_model_weight_reference_id`
- `active_model_model_version_id`
- `active_model_parameter_version_id`
- `active_model_promoted_model_created=false`
- `active_model_production_model_created=false`
- `active_model_active_thresholds_created=false`
- `active_model_advisory_predictions_created=false`
- `active_model_active_probabilities_created=false`
- `active_model_stock_profile_created=false`
- `active_model_buy_review_allowed=false`
- `active_model_approved_for_paper=false`
- `active_model_strategy_performance_validated=false`
- `active_model_trading_allowed=false`
- `active_model_current_candidates_run=false`
- `active_model_snapshot_built=false`
- `active_model_signal_semantics_changed=false`

Later paper workflow artifacts preserve final `PAPER_WORKFLOW_READY` priority. Active-model fields remain visible as context only.

## Safety Rules

The health/status layer fails or warns if artifacts imply unsafe promotion or downstream use. In particular, the workflow must not create or imply:

- promoted model or production model state;
- active thresholds;
- advisory predictions or active probabilities;
- stock_profile creation;
- buy-review eligibility;
- paper approval;
- performance validation;
- current-candidates generation;
- snapshot creation;
- signal_semantics changes;
- live trading, broker API calls, order placement, or messages.

The next governance step should remain report-only until a later accepted design explicitly scopes active model or stock_profile approval review.
