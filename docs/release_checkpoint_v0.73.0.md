# Release Checkpoint v0.73.0

## Release Summary

`v0.73.0` marks the Policy-plan Source Comparison Diagnostics through Research Status Integration checkpoint.

This milestone adds source-comparison evidence to policy-aware cache export planning and carries that evidence through policy-plan artifact views and the unified `research-status` dashboard. The system can now show whether policy-plan recommendations are comparison-supported, comparison-warning, comparison-failing, or comparison-unavailable before larger reviewed exports.

It is a local research workflow and dashboard-semantics checkpoint. It is not a live trading release, broker integration, automated order system, scheduler, source-selection autopilot, strategy-quality proof, or profit guarantee.

## Completed Capabilities

This checkpoint includes:

- Source-comparison diagnostics in `market-cache-export-plan` recommendations.
- Per-row comparison fields for reference source/upstream, matched rows, source-only rows, close difference, volume ratio, amount ratio, diagnostic classification, and warning reason.
- Comparison status counts for `PASS`, `WARN`, `FAIL`, and `UNAVAILABLE`.
- Policy-plan index, health, and status summaries for comparison support.
- Health classification for comparison diagnostics:
  - `PASS` comparisons are healthy.
  - `UNAVAILABLE` comparisons for provisional ETF/Sina rows are reviewable warnings.
  - stock comparison failures remain actionable when the policy plan is active.
- `research-status` CSV, metadata, Markdown, and CLI fields for policy-plan comparison counts.
- ETF/Sina provisional comparison-unavailable warnings remain visible and review-required.
- Later reviewed export, current-candidates, market-update-handoff, historical-backfill, and paper workflow priority is preserved.

## Workflow Chain

The completed local workflow chain is:

```text
market cache
-> market source policy
-> market-cache-export-plan
-> source comparison diagnostics
-> market-cache-export-plan index / health / status
-> research-status
-> reviewed export / current-candidates / paper workflow as later stages
```

Comparison diagnostics support manual review of generated manifests. They do not approve source selections automatically.

## Workflow Impact

`research-status` can now expose policy-plan comparison evidence alongside recommendation counts and downstream export/snapshot context.

The dashboard can distinguish:

- stock recommendations supported by cross-source comparison,
- policy-plan comparison warnings or failures,
- ETF/Sina recommendations where comparison is unavailable because no second ETF reference exists locally,
- older policy-plan warnings that should remain visible but not override later reviewed export or paper workflow progress.

Latest local dry-run behavior:

- Latest plan ID: `ffc61101d243`
- Policy-plan comparison counts: `PASS=2`, `WARN=0`, `FAIL=0`, `UNAVAILABLE=2`
- Unified `research-status` final workflow stage: `PAPER_WORKFLOW_READY`
- Next manual action stayed on the demo paper workflow path.
- Later workflow priority was preserved.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Backend tests: `python -m pytest`, 989 passed, 2 warnings.
- Quick tests: `python -m pytest -m "not slow"`, 880 passed, 109 deselected, 2 warnings.
- No live trading.
- No broker integration.
- No automated orders.
- No scheduler, cron job, background job, or GitHub Actions workflow.
- No secrets printed or stored.
- No real network/API calls in automated tests.
- No market cache mutation during planning, artifact status, dashboard reporting, or checkpoint documentation.

## Safety Boundaries

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- Policy planning, artifact views, and dashboard reporting do not mutate the market cache.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Comparison diagnostics provide evidence only; they do not approve recommendations.
- `PROVISIONAL` recommendations remain visible and review-required.
- Data-quality and snapshot-quality gates remain required before research use.
- Demo candidates and paper workflow outputs remain workflow-validation artifacts, not strategy recommendations.

## Known Limitations

- Source comparison uses a preferred reference source, not exhaustive pairwise comparison.
- ETF/Sina remains provisional because no second ETF reference source is available locally.
- Comparison counts are review evidence only.
- Policy-plan does not automatically approve or execute exports.
- Broader reviewed symbol sets still need staged validation.
- Source-comparison diagnostics do not certify source truth or strategy quality.

## Recommended Next Engineering Tasks

1. Run a larger staged policy-plan/export smoke over a reviewed symbol universe with explicit pass/fail thresholds.
2. Add optional pairwise source-comparison diagnostics for symbols with more than two viable sources.
3. Add a reviewed manifest promotion workflow for naming and freezing approved local export sets.
4. Expand ETF reference-source evaluation before changing ETF/Sina provisional status.
5. Continue current-candidates and paper workflow smoke tests from comparison-supported reviewed exports.

## Git Tag

Recommended milestone tag:

```text
v0.73.0 = Policy-plan Source Comparison Diagnostics through Research Status Integration
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
git tag -a v0.73.0 -m "Policy-plan Source Comparison Diagnostics through Research Status Integration"
git push origin v0.73.0
```
