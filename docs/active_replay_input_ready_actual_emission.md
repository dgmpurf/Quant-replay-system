# Actual ACTIVE_REPLAY_INPUT_READY Marker-Only Emission

`active-replay-input-ready-actual-emission` is a report-only governance workflow that can emit an `ACTIVE_REPLAY_INPUT_READY` marker only after explicit marker-only authority and evidence checks pass.

`ACTIVE_REPLAY_INPUT_READY` in this workflow is marker-only. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-ready-actual-emission
python -m quant_replay_system.cli active-replay-input-ready-actual-emission-index
python -m quant_replay_system.cli active-replay-input-ready-actual-emission-health
python -m quant_replay_system.cli active-replay-input-ready-actual-emission-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only manual diagnostics under:

`outputs/reports/manual_diagnostics/active_replay_input_ready_actual_emission_v0_1/<actual_emission_run_id>/`

Expected files include:

- `actual_emission_metadata.json`
- `actual_emission_report.md`
- gate result CSV files for preconditions, authority, lineage, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect guards, and overclaim guards
- `active_replay_input_ready_marker.json`
- `recommended_next_task.md`

The artifact views write `index`, `health`, and `status` folders under the same root.

## Status Semantics

- `NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT`: no actual marker-emission input package was supplied.
- `READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION`: all checks passed, but the explicit allow flag was not supplied; no marker was emitted.
- `ACTIVE_REPLAY_INPUT_READY`: an explicit allow flag was supplied and the workflow emitted a marker-only diagnostics artifact.
- `ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_*_BLOCKED`: one or more lineage, authority, attestation, PIT/source, taxonomy, leakage, side-effect, overclaim, or review gates remain blocked.
- `ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_FAILED`: artifact health checks failed.

## Explicit Allow Flag

The marker-only happy path requires the explicit `--allow-active-replay-input-ready-marker-emission` flag. Without that flag, a complete input package can only reach `READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION`.

The allow flag does not create active replay input, run replay, create replay decisions, compute labels, train weights, create stock profiles, create buy-review eligibility, approve paper workflow, validate strategy performance, call broker/order/message/API systems, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, run current-candidates, build snapshots, change signal semantics, or authorize trading.

## Marker File Contract

`active_replay_input_ready_marker.json` records marker-only status and safety fields:

- `active_replay_input_ready_marker_emitted`
- `active_replay_input_ready`
- `active_ready_emitted`
- `active_replay_input=false`
- `replay_execution_allowed=false`
- `replay_decisions_exist=false`
- `forward_labels_allowed=false`
- `forward_labels_exist=false`
- `training_allowed=false`
- `weights_trained=false`
- `stock_profile_allowed=false`
- `active_stock_profile_exists=false`
- `buy_review_allowed=false`
- `real_buy_review_eligible=false`
- `trading_allowed=false`
- `order_placed=false`
- `broker_api_called=false`
- `message_sent=false`
- `llm_api_called=false`
- `external_api_called=false`
- `cache_mutated=false`
- `data_raw_written=false`
- `data_processed_written=false`
- `data_cache_written=false`
- `current_candidates_run=false`
- `snapshot_built=false`
- `report_only=true`
- `diagnostic_only=true`

Health checks fail if marker-only `ACTIVE_REPLAY_INPUT_READY` is converted into active replay input, replay permission, replay decisions, labels, training, active stock profiles, buy-review eligibility, broker/order/message/API/cache/data side effects, current-candidates, snapshots, or trading.

## Research-Status

`research-status` surfaces the latest actual marker-only emission run id, status, health status, workflow stage, artifact path, marker-emitted flag, marker-file flag, marker-only-semantics flag, report path, next action, and safety fields.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; actual marker-only emission fields remain visible as context. Marker-only `ACTIVE_REPLAY_INPUT_READY` is not treated as active replay input and does not override paper workflow state.

## Future Boundary

Active replay input creation remains a separate future workflow. The marker-only actual emission workflow only records a governance marker. It is not a replay input package, not a replay run, not a replay-decision artifact, not a label/training/profile workflow, not buy-review eligibility, not paper approval, not performance validation, and not trading authorization.

## What Remains Blocked

This workflow does not create active replay input, does not run real replay, does not create replay decisions, does not compute forward labels or forward returns, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not apply `APPROVED_FOR_PAPER`, does not write `data/raw`, `data/processed`, or `data/cache`, does not run current-candidates, does not build snapshots, does not change signal semantics, does not call APIs, does not mutate cache, and does not authorize trading.
