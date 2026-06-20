# Model Weight Versioning

`model-weight-versioning` creates report-only Model Weights / Versioning / Threshold / Prediction Phase 1 research artifacts from approved upstream report-only training result lineage.

The workflow is deliberately bounded. `MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED` means audit artifacts exist for model research review only. It is not an active model, not a promoted model, not a production model, not active parameters, not active thresholds, not advisory predictions, not active probabilities, not active feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.

## Commands

Core workflow:

```bash
python -m quant_replay_system.cli model-weight-versioning
```

Artifact views:

```bash
python -m quant_replay_system.cli model-weight-versioning-index
python -m quant_replay_system.cli model-weight-versioning-health
python -m quant_replay_system.cli model-weight-versioning-status
```

Dashboard integration:

```bash
python -m quant_replay_system.cli research-status
```

## Statuses

- `NO_MODEL_WEIGHT_VERSIONING_INPUT`: no model-weight-versioning input package was supplied.
- `READY_FOR_MODEL_WEIGHT_VERSIONING`: all gates are reviewable, but explicit report-only artifact creation was not allowed.
- `MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED`: report-only research artifacts were created after explicit allow.
- `MODEL_WEIGHT_VERSIONING_HEALTH_FAILED`: artifact views found a safety or contract failure.

## Artifact Boundaries

The workflow may create report-only files under `outputs/reports/manual_diagnostics/model_weight_versioning_v0_1/<model_workflow_run_id>/`, including model weights reference, model version metadata, parameter version metadata, threshold plan, prediction rows, probability calibration report, feature importance report, lineage matrices, limitation notes, overfit warnings, safety flags, and a report.

These files are research artifacts only. They must not be treated as active parameters, active thresholds, advisory predictions, active probabilities, active feature importance, active stock_profile, buy-review eligibility, paper approval, strategy performance validation, broker instructions, order instructions, or trading authorization.

## Research Status

`research-status` includes the latest model workflow fields:

- `latest_model_workflow_run_id`
- `latest_model_weight_versioning_status`
- `latest_model_weight_versioning_health_status`
- `latest_model_weight_versioning_workflow_stage`
- `model_weight_versioning_training_result_row_count`
- `model_weight_versioning_metric_evidence_reference_count`
- `model_weights_reference_created`
- `model_version_metadata_created`
- `parameter_version_metadata_created`
- `threshold_plan_created`
- `prediction_rows_created`
- `probability_calibration_report_created`
- `feature_importance_report_created`
- `active_model=false`
- `promoted_model=false`
- `production_model=false`
- `active_parameters=false`
- `active_thresholds=false`
- `advisory_predictions_created=false`
- `active_probabilities_created=false`
- `active_feature_importance_created=false`

Later paper workflow artifacts preserve final `PAPER_WORKFLOW_READY` priority. Model-weight-versioning fields remain visible as context only.

## Safety Rules

The health/status layer fails or warns if artifacts imply unsafe promotion or downstream use. In particular, the workflow must not create or imply:

- active, promoted, or production model state;
- active parameters or thresholds;
- advisory predictions or active probabilities;
- active feature importance;
- stock_profile creation;
- real buy-review eligibility;
- paper approval;
- strategy performance validation;
- live trading, broker API calls, orders, messages, external API calls, cache mutation, or data writes.

## Next Action

Review the report-only model artifacts and their source lineage. A later governance task may design acceptance criteria for model research artifacts, but that should still remain separate from active model promotion, advisory prediction production, stock_profile creation, paper approval, and trading.
