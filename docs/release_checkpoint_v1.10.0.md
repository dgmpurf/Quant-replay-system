# Release Checkpoint v1.10.0

## Milestone

Reviewed Replacement Worklist Planning.

## Completed Capabilities

- Added `reviewed-replacement-worklist-plan`.
- Created report-only future replacement templates for:
  - `stock_core`
  - `etf_core`
  - `mixed_demo_core`
- Added replacement-plan artifact views:
  - `reviewed-replacement-worklist-plan-index`
  - `reviewed-replacement-worklist-plan-health`
  - `reviewed-replacement-worklist-plan-status`
- Integrated replacement-plan status into unified `research-status`.
- Preserved visibility for source split plan id, row counts, profile conflicts, report path, and next action.
- Preserved later paper workflow priority.

## Workflow Impact

The project now has a safe planning layer after universe profile split guidance. Legacy mixed `etf_core` rows can be previewed as future replacement templates under clarified `stock_core`, `etf_core`, and `mixed_demo_core` labels without mutating active artifacts.

This milestone is still planning/reporting only. Replacement templates are not active worklists and do not authorize current-candidates generation.

## Validation Baseline

Validation for this checkpoint should include:

```powershell
python -m pytest
python -m pytest -m "not slow"
```

The local run for this checkpoint refreshed the baseline after implementation.

## Safety Guarantees

- No approval was applied.
- No rejection was applied.
- No active worklist was mutated.
- No universe export occurred.
- No `data/raw` write occurred.
- No `data/processed` write occurred.
- No `current-candidates` generation occurred.
- No snapshot manifest was built.
- No forward labels were computed.
- No market cache mutation occurred.
- No network, external API, or LLM/API call was made.
- No live trading, broker API, automated order placement, or message delivery was implemented or invoked.
- Generated outputs under `outputs/reports` remain ignored diagnostics/artifacts and must not be committed.

## Known Limitations

- Replacement templates are not activated worklists.
- The workflow does not validate PIT evidence sufficiency.
- The workflow does not make rows eligible for candidate generation.
- The workflow does not enforce profile rules inside current-candidates.
- No replacement-worklist acceptance or staging workflow exists yet.

## Recommended Next Engineering Tasks

- Add a reviewed replacement-worklist staging or acceptance readiness workflow.
- Keep active legacy worklists unchanged until a separate explicit migration is reviewed.
- Add safety checks that prevent replacement templates from being mistaken for approved PIT universe inputs.
- Continue preserving paper workflow priority in unified `research-status`.

## Recommended Tag

`v1.10.0`
