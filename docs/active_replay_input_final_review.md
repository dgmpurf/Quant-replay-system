# Active Replay Input Final-Review

`active-replay-input-final-review` is a report-only governance workflow for final-review emission-readiness context. It reviews whether an `ACTIVE_READY_READY_FOR_FINAL_REVIEW` artifact has final reviewer package, authority, attestation, PIT/source/evidence, taxonomy, leakage, side-effect, overclaim, and emission-request coverage.

It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading.

## Commands

```powershell
python -m quant_replay_system.cli active-replay-input-final-review
python -m quant_replay_system.cli active-replay-input-final-review-index
python -m quant_replay_system.cli active-replay-input-final-review-health
python -m quant_replay_system.cli active-replay-input-final-review-status
python -m quant_replay_system.cli research-status
```

## Artifact Layout

The core workflow writes report-only artifacts under:

`outputs/reports/manual_diagnostics/active_replay_input_final_review_v0_1/<final_review_run_id>/`

Expected files include:

- `final_review_metadata.json`
- `final_review_report.md`
- gate result CSV files for package manifests, active-ready lineage, final reviewer authority, final reviewer attestation, PIT/source evidence attachments, taxonomy attachments, leakage/side-effect evidence, overclaim guards, and emission readiness
- `recommended_next_task.md`

The artifact views write index, health, and status folders under the same root.

## Status Semantics

- `NO_FINAL_REVIEW_PACKAGE`: no final-review package was supplied.
- `FINAL_REVIEW_PACKAGE_FOUND`: final-review package context is present but still needs gate evaluation.
- `FINAL_REVIEW_LINEAGE_BLOCKED`: active-ready lineage is missing or not final-review-ready.
- `FINAL_REVIEW_AUTHORITY_BLOCKED`: final reviewer authority evidence is incomplete.
- `FINAL_REVIEW_ATTESTATION_BLOCKED`: final reviewer attestation evidence is incomplete.
- `FINAL_REVIEW_PIT_BLOCKED`: PIT universe or available-time evidence attachments are incomplete.
- `FINAL_REVIEW_SOURCE_BLOCKED`: source permission/hash/revision coverage is incomplete.
- `FINAL_REVIEW_EVIDENCE_BLOCKED`: replay evidence bundle coverage is incomplete.
- `FINAL_REVIEW_TAXONOMY_BLOCKED`: factor taxonomy coverage is incomplete or too narrow.
- `FINAL_REVIEW_LEAKAGE_BLOCKED`: future-label, training, or stock-profile leakage risk exists.
- `FINAL_REVIEW_SIDE_EFFECT_BLOCKED`: side-effect safety is not clean.
- `FINAL_REVIEW_OVERCLAIM_BLOCKED`: overclaim guards are incomplete.
- `FINAL_REVIEW_REVIEW_BLOCKED`: emission-request boundaries are incomplete.
- `FINAL_REVIEW_READY_FOR_EMISSION_REVIEW`: report-only emission-readiness review context exists.

`FINAL_REVIEW_READY_FOR_EMISSION_REVIEW` is not `ACTIVE_REPLAY_INPUT_READY`. It is a reviewable governance milestone only.

## Future Boundary

`ACTIVE_REPLAY_INPUT_READY` remains future-only. It must require a separate explicit emission workflow, and even that status must not mean replay was run, labels were computed, weights were trained, stock profiles were created, buy-review eligibility was created, or trading was authorized.

## Research-Status

`research-status` surfaces the latest final-review context with run id, status, health, workflow stage, artifact path, emission-review flag, non-active safety flags, report path, and next action. Later paper workflow artifacts keep `PAPER_WORKFLOW_READY`; final-review fields remain visible as context.

## What Remains Blocked

The current no-package state remains blocked until active-ready lineage, final reviewer package/authority/attestation manifests, PIT/source/evidence/taxonomy coverage, leakage review, side-effect review, overclaim review, and emission-request boundaries exist. Final-review artifacts remain non-active and must not be used as replay input.
