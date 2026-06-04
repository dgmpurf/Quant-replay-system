# Release Checkpoint v1.12.0

## Milestone

Guarded Replacement Worklist Activation as report-only planning context.

## Completed Capabilities

- Added `reviewed-replacement-worklist-activation`.
- Added activation index, health, and status views.
- Integrated activation status into unified `research-status`.
- Preserved lineage to the legacy worklist, policy audit, split plan, replacement plan, and acceptance artifact.
- Wrote activated planning artifacts under `outputs/reports/reviewed_replacement_worklist_activation/<activation_id>/`.
- Kept stock/ETF split counts visible: 56 `stock_core`, 16 `etf_core`, 0 `mixed_demo_core` for the current lineage.

## Workflow Impact

Activation acknowledges accepted replacement templates as planning context only. It does not replace the active legacy worklist and does not make any row usable for current-candidates generation.

`research-status` shows activation context while preserving later paper workflow priority.

## Validation Baseline

Validation for this checkpoint should run:

```powershell
python -m pytest
python -m pytest -m "not slow"
```

## Safety Guarantees

- No approval or rejection is applied.
- No active legacy worklist is mutated.
- No universe export is produced.
- No `data/raw` or `data/processed` write is performed.
- No current-candidates generation is run.
- No snapshot manifests are built.
- No forward labels are computed.
- No cache mutation is performed.
- No live trading, broker API, order placement, or message delivery is implemented or invoked.
- No network/API/LLM calls are required.
- Generated outputs under `outputs/reports` remain ignored and must not be committed.

## Known Limitations

- Activated templates are not active worklists.
- Rows remain evidence-incomplete and `NEEDS_MANUAL_REVIEW`.
- Profile conflicts remain planning context.
- The workflow does not validate strategy performance or market edge.
- Follow-on PIT evidence review and export readiness still require explicit manual review.

## Recommended Next Engineering Tasks

1. Add guarded downstream planning for evidence-update work against activated replacement templates.
2. Keep active legacy worklist unchanged until a separate, explicit replacement handoff is designed.
3. Continue preserving paper workflow priority in unified research-status.

## Recommended Tag

`v1.12.0`
