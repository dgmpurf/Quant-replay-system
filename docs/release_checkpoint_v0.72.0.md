# Release Checkpoint v0.72.0

## Release Summary

`v0.72.0` marks the Policy-aware Reviewed Cache Export through Research Status Integration checkpoint.

This milestone adds a policy-aware planning layer for reviewed cache exports and surfaces that policy-plan state in the unified `research-status` dashboard. The system can now recommend source/upstream selections from the local market cache using `market_source_policy`, generate an explicit reviewed export manifest, validate the downstream export/snapshot path, and keep policy warnings visible without letting them override later workflow stages.

It is a local research workflow and dashboard-context checkpoint. It is not a live trading release, broker integration, automated order system, scheduler, source-selection autopilot, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Market source field reliability policy by source, upstream source, security type, and field.
- Policy-aware reviewed cache export planning with `market-cache-export-plan`.
- Local cache inspection for available source/upstream rows before recommendation.
- Simple policy ranking that favors `RELIABLE` fields, preserves `PROVISIONAL` warnings, and rejects unavailable or unsafe candidates.
- Generated reviewed export manifests that remain explicit and reviewable.
- Reviewed `market-cache-export` execution from the generated manifest.
- Duplicate-key protection before data-pipeline use.
- Downstream validation through `data-pipeline`, `data-quality`, and `snapshot-quality`.
- `market-cache-export` index, health, and status artifact views.
- `market-cache-export-plan` index, health, and status artifact views.
- `research-status` integration for market-cache-export-plan fields as policy recommendation context.
- Later reviewed export, current-candidates, market-update-handoff, historical-backfill, and paper workflow priority preservation.
- Visible `PROVISIONAL` ETF/Sina warnings that remain review-required and are not treated as automatic approval.
- Exported CSV, metadata JSON, Markdown, and CLI reporting coverage for policy-plan dashboard fields.

## Workflow Chain

The completed local workflow chain is:

```text
market cache
-> market source policy
-> market-cache-export-plan
-> reviewed export manifest
-> market-cache-export
-> data-pipeline
-> data-quality
-> snapshot-quality
-> market-cache-export-status
-> market-cache-export-plan-status
-> research-status
```

The policy-plan layer recommends a reviewed source/upstream selection. The reviewed manifest remains the explicit selection boundary before any export is run.

## Workflow Impact

`research-status` can now show policy recommendation context alongside reviewed export and downstream workflow status. This helps distinguish:

- A policy plan that is ready for review.
- A policy plan with reviewable `PROVISIONAL` source warnings.
- A policy plan whose generated manifest or required source/upstream fields are broken.
- A reviewed export or snapshot path that is already more advanced than the policy plan.
- A paper workflow path that should keep priority over older planning/export stages.

When a plan reaches `SNAPSHOT_READY_FROM_POLICY_PLAN`, the dashboard can report the linked reviewed export and snapshot-quality result while still preserving the final stage from newer current-candidates or paper workflow artifacts.

## Latest Local Verification Baseline

Latest policy-plan dry run:

- Plan ID: `44e00d723291`
- Plan status: `WARN`
- Plan stage: `SNAPSHOT_READY_FROM_POLICY_PLAN`
- `000001` recommendation: `AKSHARE_OPTIONAL / TENCENT`
- `510300` recommendation: `AKSHARE_OPTIONAL / SINA` with `PROVISIONAL` warning
- Linked downstream export ID: `790c276db1c2`
- Linked downstream snapshot quality: `PASS`
- Unified `research-status` final workflow stage: `PAPER_WORKFLOW_READY`

## Validation Baseline

Latest validation baseline for this checkpoint:

- Focused `local_research_dashboard` tests: `python -m pytest tests/test_local_research_dashboard.py`, 59 passed.
- Policy artifact focused tests: `python -m pytest tests/test_market_cache_export_policy_artifact_views.py`, 11 passed.
- Backend tests: `python -m pytest`, 982 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 873 passed, 109 deselected, 2 warnings.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, background job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.
- No market cache mutation during policy planning or dashboard verification.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- Policy planning does not mutate the market cache.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Policy plans produce recommendations only; the user-reviewed manifest remains the explicit source/upstream selection boundary.
- `PROVISIONAL` recommendations remain visible, review-required warnings.
- Data-quality and snapshot-quality gates remain required before research use.
- Demo candidates and paper workflow outputs remain workflow-validation artifacts, not strategy recommendations.

## Known Limitations

- Policy-aware planning uses simple reliability ranking plus configured source preference order.
- Policy planning does not perform source comparison or numerical cross-source reconciliation during planning.
- Policy planning does not auto-run `market-cache-export` by default.
- ETF/Sina remains `PROVISIONAL` until another ETF reference source is validated.
- Automatic policy-aware source selection is not enabled for production workflows.
- Broader historical backfill and larger-symbol-universe validation still need controlled verification.
- Policy-plan health/status checks artifact completeness and reviewability; they do not certify strategy quality.

## Recommended Next Engineering Tasks

1. Run a broader controlled policy-plan smoke test over a larger reviewed symbol set.
2. Add policy-plan source-comparison diagnostics that can compare candidate source/upstream rows before recommendation approval.
3. Add a reviewed workflow for promoting a generated recommended manifest into a named local research export set.
4. Extend policy preference configuration documentation with examples for stocks, ETFs, and future asset classes.
5. Continue current-candidates validation from the linked reviewed export snapshot while preserving demo/non-recommendation boundaries.

## Git Tag

Recommended milestone tag:

```text
v0.72.0 = Policy-aware Reviewed Cache Export through Research Status Integration
```

Before tagging, run validation and inspect the working tree:

```cmd
python -m pytest
python -m pytest -m "not slow"
git status --short
git ls-files | findstr /R /C:"^data/cache" /C:"^data/raw" /C:"^data/processed" /C:"^outputs" /C:"^\.env" /C:"^\.venv" /C:"^secrets"
```

Create the tag only after ChatGPT or the user confirms the checkpoint:

```cmd
git tag -a v0.72.0 -m "Policy-aware Reviewed Cache Export through Research Status Integration"
git push origin v0.72.0
```
