# Release Checkpoint v1.9.0

## Milestone

Universe Profile Split-Worklist Plan Artifact Views and Research Status Integration.

## Completed Capabilities

- Added universe profile split-worklist plan artifact views:
  - `universe-profile-split-worklist-plan-index`
  - `universe-profile-split-worklist-plan-health`
  - `universe-profile-split-worklist-plan-status`
- Integrated `universe-profile-split-worklist-plan-status` into unified `research-status`.
- Exposed latest split plan id, status, stage, health status, row counts, STOCK/ETF counts, legacy mixed-demo counts, recommended future universe counts, profile-conflict counts, report path, and next action.
- Kept profile conflicts visible as planning context for legacy mixed `etf_core` artifacts.
- Preserved later paper workflow priority when split-plan context exists.

## Workflow Impact

The project can now discover, safety-check, summarize, and dashboard future split-worklist planning artifacts. Current mixed `etf_core` rows remain legacy context, while the planner shows how future rows should move toward clarified `stock_core`, `etf_core`, or `mixed_demo_core` profiles.

This checkpoint does not regenerate active worklists. It adds observability before a later explicit replacement-worklist workflow.

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

- The split plan does not create replacement worklists.
- The split plan does not validate PIT evidence sufficiency.
- The split plan does not prove market membership or strategy performance.
- Existing ambiguous `etf_core` rows are not automatically approved or rejected.
- Profile enforcement is not wired into candidate generation.

## Recommended Next Engineering Tasks

- Implement a reviewed replacement-worklist planning workflow that can produce separate future templates for `stock_core`, `etf_core`, and `mixed_demo_core`.
- Keep current ambiguous rows as legacy mixed/demo context until a reviewed migration path creates new artifacts.
- Add profile validation gates before any future PIT approval/export workflow consumes split-profile worklists.
- Continue preserving later paper workflow priority in unified `research-status`.

## Recommended Tag

`v1.9.0`
