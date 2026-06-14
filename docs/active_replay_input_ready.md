# Active Replay Input Ready

`active-replay-input-ready` is a report-only governance workflow for the final `ACTIVE_REPLAY_INPUT_READY` readiness boundary. It checks ready-decision lineage, final reviewer authority, attestation, PIT/source evidence, taxonomy evidence, leakage and side-effect evidence, and overclaim guards.

It can reach `READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY`, but it does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not create replay decisions. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-ready
python -m quant_replay_system.cli active-replay-input-ready-index
python -m quant_replay_system.cli active-replay-input-ready-health
python -m quant_replay_system.cli active-replay-input-ready-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_ready_v0_1/<active_ready_run_id>/`

Expected files include `metadata.json`, `active_replay_input_ready_report.md`, gate result CSV files, `ready_candidate.json`, and `recommended_next_task.md`. The artifact views write `index`, `health`, and `status` folders under the same root.

## Status Semantics

- `NO_ACTIVE_REPLAY_INPUT_READY_GOVERNANCE_INPUT`: no governance input package was supplied.
- `ACTIVE_REPLAY_INPUT_READY_*_BLOCKED`: one or more lineage, authority, attestation, PIT/source, taxonomy, leakage, side-effect, overclaim, or review gates remain blocked.
- `ACTIVE_REPLAY_INPUT_READY_HEALTH_FAILED`: artifact health checks failed.
- `READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY`: report-only governance context is ready to be reviewed for a future emission decision.

`READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only.

## Research-Status

`research-status` surfaces the latest active-ready workflow context with run id, status, health, workflow stage, artifact path, ready-to-emit flag, non-active safety flags, report path, and next action. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; active-ready workflow fields remain visible as context.

## Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only. A later explicit decision would have to review and promote this report-only context. This workflow must not be interpreted as active replay input creation, real replay execution, replay decision creation, forward-label computation, trained weights, active stock profiles, real buy-review eligibility, performance validation, or trading authorization.

## What Remains Blocked

Active-ready workflow artifacts are governance context only. They must not be used as active replay input, replay execution input, current-candidates input, snapshot input, forward-label input, training input, stock-profile input, buy-review input, broker input, order input, or message input.
