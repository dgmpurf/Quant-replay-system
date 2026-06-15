# Active Replay Input Creation

`active-replay-input-create` is a report-only diagnostics workflow that can create a governed active replay input artifact after an actual marker-only `ACTIVE_REPLAY_INPUT_READY` artifact and explicit creation evidence are reviewed.

`ACTIVE_REPLAY_INPUT_CREATED` means only that `active_replay_input.json` exists as a governed report-only input artifact for a future separate replay execution workflow. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-create
python -m quant_replay_system.cli active-replay-input-create-index
python -m quant_replay_system.cli active-replay-input-create-health
python -m quant_replay_system.cli active-replay-input-create-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes manual diagnostics under:

`outputs/reports/manual_diagnostics/active_replay_input_create_v0_1/<active_input_creation_run_id>/`

Expected files include:

- `active_input_creation_metadata.json`
- `active_input_creation_report.md`
- gate result CSV files for preconditions, authority, lineage, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect guards, and overclaim guards
- `active_replay_input.json`
- `recommended_next_task.md`

The artifact views write `index`, `health`, and `status` folders under the same root.

## Status Semantics

- `NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT`: no creation input package was supplied, so the run writes a no-input diagnostics artifact with all execution, label, training, profile, buy-review, and trading flags false.
- `READY_FOR_ACTIVE_REPLAY_INPUT_CREATION`: all required evidence appears present, but the explicit allow flag was not supplied; no active replay input is created.
- `ACTIVE_REPLAY_INPUT_CREATED`: the explicit allow flag was supplied and `active_replay_input.json` was created as a report-only diagnostics artifact.
- `ACTIVE_REPLAY_INPUT_CREATION_*_BLOCKED`: one or more lineage, authority, attestation, PIT/source, taxonomy, leakage, side-effect, overclaim, or review gates remain blocked.
- `ACTIVE_REPLAY_INPUT_CREATE_HEALTH_FAILED`: artifact health checks failed.

## Explicit Allow Flag

The creation happy path requires `--allow-active-replay-input-creation`. Without that flag, a complete input package can only reach `READY_FOR_ACTIVE_REPLAY_INPUT_CREATION`.

The allow flag does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not authorize trading, does not call broker/order/message/API systems, does not mutate cache, does not write `data/raw`, does not write `data/processed`, does not write `data/cache`, does not run current-candidates, does not build snapshots, does not change signal semantics, does not apply `APPROVED_FOR_PAPER`, and does not validate strategy performance.

## No-Input Behavior

When no input package is supplied, the workflow records `NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT`, writes safe default diagnostics, and keeps `active_replay_input_created=false` and `active_replay_input=false`.

## Pre-Creation Happy Path

When all evidence gates pass but the allow flag is absent, the workflow records `READY_FOR_ACTIVE_REPLAY_INPUT_CREATION`. This is reviewable context only. It is not replay input creation, not replay execution, and not permission to compute labels, train, create stock profiles, perform buy review, or trade.

## Active-Input-Created Happy Path

When all gates pass and the allow flag is present, the workflow records `ACTIVE_REPLAY_INPUT_CREATED` and writes `active_replay_input.json`. The artifact may carry PIT universe references, source registry references, evidence bundle references, source hash coverage, revision id coverage, available-time policy, taxonomy coverage, and marker lineage.

Even in this state, the artifact remains report-only and diagnostic-only. It is not real replay execution. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## active_replay_input.json Contract

The contract records:

- `active_input_creation_run_id`
- `active_replay_input_created`
- `active_replay_input`
- `source_marker_run_id`
- `marker_status`
- `marker_file_exists`
- `active_replay_input_ready_marker_emitted`
- `marker_only_semantics_confirmed`
- `replay_as_of_date`
- `pit_universe_ref`
- `source_registry_ref`
- `evidence_bundle_ref`
- `source_hash_coverage`
- `revision_id_coverage`
- `available_time_policy`
- `taxonomy_coverage`
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
- `signal_semantics_changed=false`
- `report_only=true`
- `diagnostic_only=true`

## Health Semantics

Health checks pass only when required files and columns exist, the active input file exists for created artifacts, overclaim guards pass, and all downstream execution, label, training, stock-profile, buy-review, trading, API, cache, data-write, current-candidates, snapshot, and signal-semantics side-effect flags remain safe.

Health fails if `ACTIVE_REPLAY_INPUT_CREATED` is converted into replay permission, replay decisions, labels, training, stock profiles, buy-review eligibility, paper approval, broker/order/message/API side effects, cache mutation, data writes, current-candidates generation, snapshot builds, signal semantics changes, or trading authorization.

## Research-Status

`research-status` exposes the latest active input creation run id, status, health status, workflow stage, artifact path, active input flags, marker lineage, PIT/source/taxonomy coverage, report path, next action, and safety flags.

Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; active replay input creation fields remain visible as context. `ACTIVE_REPLAY_INPUT_CREATED` is not treated as real replay.

## Future Boundary

Real replay execution remains a separate future workflow. Active replay input creation only emits a governed report-only input artifact. It does not run replay, does not create replay decisions, does not compute labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not validate strategy performance, and does not authorize trading.
