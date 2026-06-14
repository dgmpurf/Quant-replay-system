# Active Replay Input Ready Decision

`active-replay-input-ready-decision` is a report-only governance workflow for active replay input ready-decision context. It checks whether emission-ready context has explicit decision request, reviewer authority, attestation, PIT/source evidence, taxonomy coverage, leakage and side-effect evidence, and overclaim guards before a future active-ready decision review.

It does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-ready-decision
python -m quant_replay_system.cli active-replay-input-ready-decision-index
python -m quant_replay_system.cli active-replay-input-ready-decision-health
python -m quant_replay_system.cli active-replay-input-ready-decision-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_ready_decision_v0_1/<decision_run_id>/`

Expected files include metadata, decision report, gate result CSV files, an active-ready candidate manifest for review context only, and `recommended_next_task.md`. The artifact views write index, health, and status folders under the same root.

## Status Semantics

- `NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT`: no ready-decision input package was supplied.
- `ACTIVE_REPLAY_INPUT_READY_DECISION_*_BLOCKED`: one or more lineage, authority, attestation, PIT/source, taxonomy, leakage, side-effect, overclaim, or review gates remain blocked.
- `READY_DECISION_HEALTH_FAILED`: artifact health checks failed.
- `READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION`: report-only ready-decision context is ready for human review.

`READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only.

## Research-Status

`research-status` surfaces the latest ready-decision context with decision run id, status, health, workflow stage, artifact path, ready-decision flag, non-active safety flags, report path, and next action. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; ready-decision fields remain visible as context.

## Future Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only. A later explicit workflow would have to review and promote ready-decision context. Even future `ACTIVE_REPLAY_INPUT_READY` would still not mean active replay input creation, real replay execution, forward labels, trained weights, active stock profiles, real buy-review eligibility, performance validation, or trading authorization.

## What Remains Blocked

Ready-decision artifacts are governance context only. They must not be used as active replay input, replay execution input, current-candidates input, snapshot input, forward-label input, training input, stock-profile input, buy-review input, broker input, order input, or message input.
