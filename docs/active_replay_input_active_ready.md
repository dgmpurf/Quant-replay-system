# Active Replay Input Active-Ready

`active-replay-input-active-ready` is a report-only governance workflow for accepted replay input context. It reviews whether an accepted replay input package has enough authority, lineage, PIT, source, evidence, taxonomy, leakage, side-effect, and overclaim coverage to be ready for a future final review step.

It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-active-ready
python -m quant_replay_system.cli active-replay-input-active-ready-index
python -m quant_replay_system.cli active-replay-input-active-ready-health
python -m quant_replay_system.cli active-replay-input-active-ready-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_active_ready_v0_1/<active_ready_run_id>/`

Expected files include:

- `active_ready_metadata.json`
- `active_ready_report.md`
- gate result CSV files for preconditions, authority, lineage, PIT coverage, source coverage, evidence coverage, taxonomy compliance, leakage guards, side-effect guards, and overclaim guards
- `recommended_next_task.md`

The artifact views write index, health, and status folders under the same root.

## Status Semantics

- `NO_ACTIVE_READY_INPUT`: no accepted input and active-ready governance package is available.
- `ACTIVE_READY_INPUT_FOUND`: input context is present but still needs gate evaluation.
- `ACTIVE_READY_AUTHORITY_BLOCKED`: reviewer authority or active-ready request evidence is incomplete.
- `ACTIVE_READY_LINEAGE_BLOCKED`: accepted replay input lineage is missing or not ready.
- `ACTIVE_READY_PIT_BLOCKED`: PIT universe or timing coverage is incomplete.
- `ACTIVE_READY_SOURCE_BLOCKED`: source permission/hash/revision coverage is incomplete.
- `ACTIVE_READY_EVIDENCE_BLOCKED`: replay evidence bundle coverage is incomplete.
- `ACTIVE_READY_TAXONOMY_BLOCKED`: factor taxonomy coverage is incomplete or too narrow.
- `ACTIVE_READY_LEAKAGE_BLOCKED`: future-label, training, or stock-profile leakage risk exists.
- `ACTIVE_READY_SIDE_EFFECT_BLOCKED`: side-effect safety is not clean.
- `ACTIVE_READY_REVIEW_BLOCKED`: overclaim or final review boundary checks are incomplete.
- `ACTIVE_READY_READY_FOR_FINAL_REVIEW`: report-only final-review context exists.

`ACTIVE_READY_READY_FOR_FINAL_REVIEW` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only.

## Future Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only. It must require a separate explicit final-review/emission workflow. Even then, it must not mean replay was run, labels were computed, weights were trained, stock profiles were created, buy-review eligibility was created, or trading was authorized.

## Research-Status

`research-status` surfaces the latest active-ready context with run id, status, health, workflow stage, artifact path, final-review flag, non-active safety flags, report path, and next action. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; active-ready fields remain visible as context.

## What Remains Blocked

The current no-input state remains blocked until accepted input context, authority manifests, PIT/source/evidence/taxonomy coverage, leakage review, side-effect review, and overclaim review exist. Active-ready artifacts remain non-active and must not be used as replay input.
