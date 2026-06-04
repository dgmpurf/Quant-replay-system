# Release Checkpoint v1.14.0

## Milestone

PIT Evidence Checklist Validator as a report-only strict evidence quality gate.

## Completed Capabilities

- Added `pit-evidence-checklist-validator`.
- Added validator index, health, and status views.
- Integrated validator status into unified `research-status`.
- Validated completed or draft PIT evidence update rows against strict `stock_core` and `etf_core` checklists.
- Preserved leading-zero symbols such as `000001`.
- Reported missing evidence, unacceptable/context-only sources, PIT timing blockers, survivorship blockers, and stock ST/no-ST blockers.
- Produced an approval-candidate preview only when rows pass the checklist.
- Kept later paper workflow priority intact in `research-status`.

## Workflow Impact

The project now has a report-only strict checklist gate between evidence update ingestion and any explicit PIT universe overlay review. The validator can show that evidence rows are blocked or candidate-like, but it does not turn rows into approved PIT universe rows.

For the current 16-row draft validation, all rows remain blocked:

- `row_count=16`
- `checklist_pass_count=0`
- `blocked_count=16`
- `stock_core_blocked_count=8`
- `etf_core_blocked_count=8`

The validator stage is visible in `research-status` as PIT evidence context. If later paper workflow artifacts exist, the final workflow stage remains on the paper workflow path.

## Validation Baseline

Validation for this checkpoint should run:

```powershell
python -m pytest
python -m pytest -m "not slow"
```

Focused regression coverage includes:

- strict checklist blocking for the current 16-row draft shape;
- stock ST/no-ST requirement without imposing the same requirement on ETF rows;
- active/not-delisted, PIT timing, source, and survivorship blockers;
- leading-zero symbol preservation;
- index, health, status, CLI, and `research-status` visibility.

## Safety Guarantees

- No approval is applied.
- No rejection is applied.
- No `APPROVED_FOR_PIT_UNIVERSE` status is set.
- No PIT overlay review is run.
- No export readiness or export staging workflow is run.
- No universe export is produced.
- No `data/raw` write is performed.
- No `data/processed` write is performed.
- No current-candidates generation is run.
- No snapshot manifests are built.
- No forward labels are computed.
- No cache mutation is performed.
- No network/API/LLM calls are required.
- No live trading, broker API, order placement, or message delivery is implemented or invoked.
- Generated outputs under `outputs/reports` remain ignored and must not be committed.

## Known Limitations

- The validator does not verify external evidence documents.
- The source acceptance matrix is applied conservatively from local row text and checklist context.
- Post-close local market-cache evidence remains blocked unless a later reviewed EOD decision-time policy is added.
- A checklist pass is only an approval-candidate preview, not a reviewed PIT universe row.
- The workflow does not validate strategy performance or market edge.

## Recommended Next Engineering Tasks

1. Complete missing PIT evidence for a tiny profile-specific batch without using future-dated hints as authority.
2. Rerun `pit-universe-evidence-update-ingestion` and then `pit-evidence-checklist-validator`.
3. Only after checklist-pass rows exist, consider a separate explicit `pit-universe-overlay-review` run.
4. Continue preserving paper workflow priority in unified `research-status`.

## Recommended Tag

`v1.14.0`
