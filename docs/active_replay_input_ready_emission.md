# Active Replay Input Ready Emission Decision

`active-replay-input-ready-emission` is a report-only governance workflow for `ACTIVE_REPLAY_INPUT_READY` emission-decision context. It checks whether ready-to-emit active-ready context has explicit final emission request evidence, reviewer authority, attestation, PIT/source evidence, taxonomy evidence, leakage and side-effect evidence, and overclaim guards before a future human emission decision review.

It does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-ready-emission
python -m quant_replay_system.cli active-replay-input-ready-emission-index
python -m quant_replay_system.cli active-replay-input-ready-emission-health
python -m quant_replay_system.cli active-replay-input-ready-emission-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_ready_emission_v0_1/<active_ready_emission_run_id>/`

Expected files include:

- `active_ready_emission_metadata.json`
- `active_ready_emission_report.md`
- gate result CSV files for preconditions, authority, lineage, attestation, PIT/source evidence, taxonomy evidence, leakage/side-effect guards, and overclaim guards
- `active_replay_input_ready_emission_candidate_manifest.json`
- `recommended_next_task.md`

The artifact views write `index`, `health`, and `status` folders under the same root.

## Status Semantics

- `NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT`: no emission-decision input package was supplied.
- `ACTIVE_REPLAY_INPUT_READY_EMISSION_*_BLOCKED`: one or more lineage, authority, attestation, PIT/source, taxonomy, leakage, side-effect, overclaim, or review gates remain blocked.
- `ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_HEALTH_FAILED`: artifact health checks failed.
- `READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION`: report-only emission-decision context is ready for human review.

`READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only. It must not be interpreted as active replay input, replay permission, replay-decision permission, forward-label permission, training permission, stock-profile permission, buy-review eligibility, performance validation, paper approval, broker permission, order permission, message permission, or trading authorization.

## Gate Groups

The workflow checks final emission preconditions, reviewer authority, ready-to-emit lineage, reviewer attestation, PIT/source evidence, 8-layer taxonomy evidence, leakage and side-effect safeguards, and overclaim guards.

Every gate is report-only. Passing the gates can only produce `READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION` context for human review. It cannot emit `ACTIVE_REPLAY_INPUT_READY`.

## No-Input And Happy-Path Behavior

No-input runs produce `NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT`, health-checkable report artifacts, and all active/replay/label/training/profile/buy/trading flags set to false.

Happy-path fixture runs can reach `READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION`. Even then, `active_replay_input_ready`, `active_replay_input`, `active_ready_emitted`, `replay_execution_allowed`, `replay_decisions_exist`, `forward_labels_allowed`, `forward_labels_exist`, `training_allowed`, `weights_trained`, `stock_profile_allowed`, `active_stock_profile_exists`, `buy_review_allowed`, `real_buy_review_eligible`, and `trading_allowed` remain false.

## Research-Status

`research-status` surfaces the latest emission-decision run id, status, health status, workflow stage, artifact path, readiness-for-emission-decision flag, report path, next action, and safety fields. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; emission-decision fields remain visible as context.

## Future Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only unless a later explicit task scopes actual emission. Even a future emitted `ACTIVE_REPLAY_INPUT_READY` would still not mean active replay input creation, real replay, replay decisions, forward labels, training, stock_profile creation, buy-review eligibility, performance validation, paper approval, broker integration, order placement, messages, or trading.

## What Remains Blocked

This workflow does not create an active replay input package, does not run real replay, does not create replay decisions, does not compute forward labels or forward returns, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not apply `APPROVED_FOR_PAPER`, does not write `data/raw`, `data/processed`, or `data/cache`, does not run current-candidates, does not build snapshots, does not change signal semantics, does not call APIs, does not mutate cache, and does not authorize trading.
