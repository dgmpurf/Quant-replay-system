# Active Replay Input Emission

`active-replay-input-emission` is a report-only governance workflow for active replay input emission context. It reviews whether a final-review emission-ready artifact has explicit emission request, reviewer authority, attestation, PIT/source evidence, taxonomy coverage, leakage and side-effect checks, and overclaim guards.

It does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-emission
python -m quant_replay_system.cli active-replay-input-emission-index
python -m quant_replay_system.cli active-replay-input-emission-health
python -m quant_replay_system.cli active-replay-input-emission-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_emission_v0_1/<emission_run_id>/`

Expected files include:

- `emission_metadata.json`
- `emission_report.md`
- gate result CSV files for final-review lineage, emission request, reviewer authority, attestation, PIT/source evidence, taxonomy coverage, leakage and side-effect checks, overclaim guards, and non-emission safety
- `recommended_next_task.md`

The artifact views write index, health, and status folders under the same root.

## Status Semantics

- `NO_EMISSION_INPUT`: no emission input package was supplied.
- `EMISSION_NO_INPUT`: no reviewable emission input exists.
- `EMISSION_BLOCKED`: report-only emission gates remain blocked.
- `EMISSION_HEALTH_FAILED`: artifact health checks failed.
- `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW`: report-only emission context is ready for human review.

`EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only.

## Research-Status

`research-status` surfaces the latest emission context with run id, status, health, workflow stage, artifact path, active-ready-review flag, non-active safety flags, report path, and next action. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; emission fields remain visible as context.

## Future Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only. A later explicit workflow would have to promote report-only emission context into an active-ready artifact with reviewed authorization. Even then, active-ready must not mean replay was run, labels were computed, weights were trained, stock profiles were created, buy-review eligibility was created, or trading was authorized.

## What Remains Blocked

Emission artifacts are governance context only. They must not be used as replay input, current-candidates input, snapshot input, forward-label input, training input, stock-profile input, buy-review input, broker input, order input, or message input.
