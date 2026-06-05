# First-Batch Partial Completion Impact v0.1

`first-batch-partial-completion-impact` is a report-only workflow for comparing a first-batch reviewer evidence completion plan with an optional diagnostics-only partial reviewer completion fixture.

It reports which reviewer fields were filled, which blockers were reduced, and which PIT evidence requirements remain. It does not approve or reject rows, create clean `review_updates.csv`, run PIT review, run export-readiness, run staging, export universe files, write `data/raw`, write `data/processed`, mutate active worklists, mutate cache, run `current-candidates`, build snapshots, compute forward labels, call APIs, send messages, connect to brokers, or place orders.

## Commands

Build the core impact artifact:

```bash
python -m quant_replay_system.cli first-batch-partial-completion-impact
```

Build artifact views:

```bash
python -m quant_replay_system.cli first-batch-partial-completion-impact-index
python -m quant_replay_system.cli first-batch-partial-completion-impact-health
python -m quant_replay_system.cli first-batch-partial-completion-impact-status
```

## Artifacts

Artifacts are written under:

```text
outputs/reports/first_batch_partial_completion_impact/<impact_id>/
```

Expected files:

- `first_batch_partial_completion_impact.csv`
- `completed_field_to_blocker_matrix.csv`
- `still_missing_after_partial_completion.csv`
- `checklist_pass_requirements_remaining.csv`
- `report.md`
- `metadata.json`

## Status Stages

`first-batch-partial-completion-impact-status` reports one of:

- `NO_FIRST_BATCH_PARTIAL_COMPLETION_IMPACT`
- `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_NO_COMPLETION`
- `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_METADATA_ONLY_REDUCTION`
- `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_MATERIAL_BLOCKERS_REMAIN`
- `FIRST_BATCH_PARTIAL_COMPLETION_IMPACT_FAILED`

`NO_COMPLETION` means no partial reviewer completion fixture was linked. `METADATA_ONLY_REDUCTION` means reviewer metadata was observed, but material PIT blockers remain. `MATERIAL_BLOCKERS_REMAIN` means at least one material blocker delta is visible, but the workflow is still report-only and does not create approval-ready rows.

## Health Checks

Health fails if an impact artifact implies approval or downstream execution, including:

- `approval_applied=true`
- clean `review_updates.csv` or `clean_review_updates.csv` files
- `APPROVED_FOR_PIT_UNIVERSE`
- `include_flag=true`
- `valid_for_signal_date=true`
- PIT review, export-readiness, staging, universe export, data writes, current-candidates, snapshots, or forward labels

## Research Status

`research-status` exposes the latest first-batch partial completion impact as context with completed row count, completed field count, blocker reduction count, material blocker reduction count, checklist pass count, remaining blocked count, clean-review-update flag, approval-applied flag, report path, and next action.

This context does not imply PIT approval, export readiness, staging, accepted export, snapshot build, current-candidates generation, or trading. Later paper workflow artifacts keep final workflow priority while partial completion impact fields remain visible for reviewer planning.

