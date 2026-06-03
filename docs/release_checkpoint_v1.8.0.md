# Release Checkpoint v1.8.0

## Milestone

Universe Profile Policy Audit Artifact Views and Research Status Integration.

## Completed Capabilities

- Added universe profile policy audit artifact views:
  - `universe-profile-policy-audit-index`
  - `universe-profile-policy-audit-health`
  - `universe-profile-policy-audit-status`
- Integrated `universe-profile-policy-audit-status` into unified `research-status`.
- Exposed mixed STOCK/ETF universe context for legacy `etf_core` artifacts.
- Preserved split guidance counts for future `stock_core`, `etf_core`, and `mixed_demo_core` worklists.
- Kept ambiguous mixed-universe warnings visible without treating them as row approvals or rejections.
- Preserved later paper workflow priority when policy audit context exists.

## Workflow Impact

The project can now discover, safety-check, summarize, and dashboard universe profile policy audit artifacts. Current ambiguous mixed `etf_core` context is visible as `UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE`, while `research-status` can still remain on later stages such as `PAPER_WORKFLOW_READY`.

This checkpoint clarifies that existing mixed `etf_core` artifacts are policy context only. They should not be treated as ETF-only, and they should not authorize PIT universe approval.

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

- The audit does not validate PIT evidence sufficiency.
- The audit does not prove market membership or strategy performance.
- Existing ambiguous `etf_core` rows are not automatically rejected.
- No config-backed universe profile registry exists yet.
- Future worklists are not regenerated under split profile names yet.
- Profile-policy findings are not yet enforced by PIT approval/export health gates.

## Recommended Next Engineering Tasks

- Design a universe profile registry with explicit `stock_core`, `etf_core`, and `mixed_demo_core` semantics.
- Add future-only validation that blocks STOCK rows from ETF-only worklists and ETF rows from stock-only worklists.
- Create a split-worklist planning/report workflow before applying policy enforcement to active PIT evidence work.
- Keep current ambiguous rows as legacy mixed/demo context until a reviewed migration path exists.

## Recommended Tag

`v1.8.0`
