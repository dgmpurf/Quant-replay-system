# Release Checkpoint v1.17.0

## Milestone

Reviewed No-Hit Support in PIT Evidence Policy Profile Comparison.

## Completed Capabilities

- Extended `pit-evidence-policy-profile-comparison` with opt-in `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT`.
- Preserved `STRICT_PIT` as the reference profile.
- Preserved existing `EOD_POST_CLOSE_LOW_BUDGET_PIT` behavior.
- Added comparison fields for reviewed no-hit support pass count, no-hit context support, reviewer acceptance requirements, documented source coverage, and remaining blockers.
- Updated index, health, status, and `research-status` context fields.
- Added health checks so reviewed no-hit support cannot become default, apply approval, or resolve survivorship automatically.

## Workflow Impact

The profile comparison can now show when official same-date quotation evidence and documented official no-hit source chains may provide supporting context under a reviewed EOD/post-close policy. This is still comparison-only. It does not approve PIT universe rows and does not create usable universe input.

Current expected first-batch interpretation:

- `STRICT_PIT`: blocked.
- `EOD_POST_CLOSE_LOW_BUDGET_PIT`: blocked.
- `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT`: reviewed no-hit context may be visible, but rows remain blocked without reviewer acceptance, complete metadata, and survivorship-bias rationale.

## Validation Baseline

- Targeted policy/profile and dashboard tests passed during implementation.
- Full validation baseline should be refreshed with:
  - `python -m pytest`
  - `python -m pytest -m "not slow"`

## Safety Guarantees

- No approvals are applied.
- `APPROVED_FOR_PIT_UNIVERSE` is not set.
- PIT review is not run.
- Export-readiness and staging are not run.
- Universe files are not exported.
- `data/raw` and `data/processed` are not written.
- Active worklists and market cache are not mutated.
- Current-candidates are not run.
- Snapshots and forward labels are not built.
- Broker, live trading, order placement, and message delivery remain out of scope.

## Known Limitations

- Official no-hit evidence is supporting context only and remains policy-dependent.
- Current/default no-hit pages do not prove complete historical coverage by themselves.
- Survivorship-bias resolution still requires explicit human reviewer rationale.
- A comparison pass, if one appears later, is only a manual preview and not approval.
- No strategy performance is validated.

## Recommended Next Engineering Tasks

- Add a report-only no-hit source coverage acceptance artifact if reviewer policy needs to be tracked separately.
- Enrich evidence packets with structured no-hit source coverage once official historical coverage is reviewed.
- Keep PIT review, export-readiness, staging, and current-candidates blocked until explicit approval evidence is complete.

## Recommended Tag

`v1.17.0`
