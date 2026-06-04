# Release Checkpoint v1.11.0

## Milestone

Reviewed Replacement Worklist Acceptance v0.1.

## Completed Capabilities

- Added `reviewed-replacement-worklist-acceptance`.
- Added acceptance index, health, and status commands.
- Integrated reviewed replacement worklist acceptance into unified `research-status`.
- Preserved lineage to:
  - legacy worklist `1c7972988f59`
  - policy audit `844794b3aae1`
  - split plan `db2c09268c14`
  - replacement plan `0774d0a1fdb9`
- Wrote accepted planning artifacts under `outputs/reports` only.
- Kept replacement worklists non-active and row-level PIT evidence incomplete.

## Workflow Impact

The project can now acknowledge replacement worklist templates as reviewed planning context without activating them. This gives the dashboard a clean milestone between replacement planning and any future guarded acceptance/apply workflow.

`research-status` shows acceptance context but preserves later workflow priority, including `PAPER_WORKFLOW_READY`.

## Validation Baseline

Run for this checkpoint:

- `python -m pytest`
- `python -m pytest -m "not slow"`

## Safety Guarantees

- No active worklist mutation.
- No active artifact replacement.
- No PIT row approval.
- No PIT row rejection.
- No universe export.
- No `data/raw` write.
- No `data/processed` write.
- No current-candidates generation.
- No snapshot build.
- No forward labels.
- No market cache mutation.
- No live trading.
- No broker API.
- No order placement.
- No message delivery.
- No LLM/API or network calls.
- No strategy performance validation claim.
- Generated outputs remain ignored and must not be committed.

## Known Limitations

- Acceptance is only a planning acknowledgement.
- Accepted templates are not active worklists.
- Rows remain `NEEDS_MANUAL_REVIEW`, `include_flag=false`, and `valid_for_signal_date=false`.
- No PIT evidence is completed by this workflow.
- No universe export or candidate generation is enabled.

## Recommended Next Engineering Tasks

1. Design a guarded replacement-worklist activation audit before any active worklist mutation is considered.
2. Continue PIT universe evidence completion for profile-split rows.
3. Keep export/candidate-generation blocked until PIT evidence, snapshot inputs, and safety gates pass.

## Recommended Tag

`v1.11.0`
