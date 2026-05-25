# Release Checkpoint v0.75.0

## Release Summary

`v0.75.0` marks the 9-symbol Policy-Aware Export to WATCH_ONLY Paper Workflow Validation checkpoint.

This milestone verifies that a policy-aware reviewed cache export can produce demo current-candidates artifacts and flow through the local paper workflow using WATCH_ONLY review only. It validates artifact handoff, review-template health, reviewed-decision application, paper-daily reporting, `paper-workflow-status`, and `research-status` without approving paper trades or creating positions.

It is a controlled local workflow validation checkpoint. It is not a live trading release, broker integration, automated order system, scheduler, strategy recommendation, full-universe validation, trade-approval workflow, fill-reconciliation proof, or profit guarantee.

## Completed Workflow Chain

The validated local workflow chain is:

```text
policy-aware reviewed cache export
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates --selection-profile demo
-> current-to-paper
-> current-to-paper-review
-> WATCH_ONLY paper-review-decisions
-> paper-daily --reviewed-decisions
-> paper-workflow-status
-> research-status
```

The chain confirms that demo candidates can be transformed into paper workflow artifacts, reviewed as WATCH_ONLY, and reported by paper-daily without approvals, fills, open positions, closed trades, live trading, or broker access.

## Key Artifact IDs

Current-candidates artifact:

- Current candidate run ID: `f484cd4648`
- Candidates shape: `(9, 70)`
- Symbols: `601318, 000001, 300750, 510300, 159915, 000002, 688981, 600000, 600519`
- `selection_profile`: `demo`
- `demo_mode`: `True`
- `not_strategy_recommendation`: `True`
- `action` / `score_action`: `NO_TRADE`
- Symbol preservation confirmed: `000001` remained `000001`

Paper workflow artifacts:

- Current-to-paper handoff ID: `b8bf9da33531`
- Decision count: `9`
- Decision actions: `SKIP=9`
- Default review status: `PENDING_REVIEW=9`
- Current-to-paper-review handoff ID: `7e7bac33e5e9`
- Original review template health: `WARN` due missing reviewer fields
- WATCH_ONLY review update health: `PASS`
- Paper review ID: `4d0db99db3`
- Reviewed decisions: `WATCH_ONLY=9`
- Approved count: `0`
- `APPROVED_FOR_PAPER`: not present
- `paper-daily --reviewed-decisions`: `reviewed_decisions_used=True`
- Open positions: `0`
- Closed trades: `0`

Workflow status:

- `paper-workflow-status`: `WARN` / `WORKFLOW_NEEDS_ATTENTION`
- `research-status`: `WARN` / `PAPER_WORKFLOW_READY`
- Next action stayed on the demo paper workflow path.
- Expected no-fills/manual-attention warnings remained visible.

## Validation Baseline

Latest validation baseline for this checkpoint:

- Repository health before checkpoint:
  - `python -m pytest`: 999 passed, 2 warnings.
  - `python -m pytest -m "not slow"`: 890 passed, 109 deselected, 2 warnings.
  - `git status --short`: clean.
- Smoke validation:
  - 9 demo candidates flowed through current-to-paper.
  - 9 review update rows were converted to WATCH_ONLY.
  - WATCH_ONLY review-template health passed.
  - `paper-review-decisions --health-check` produced `WATCH_ONLY=9` and `approved_count=0`.
  - `paper-daily --reviewed-decisions` produced `open_position_count=0` and `closed_trade_count=0`.
  - `paper-workflow-status` and `research-status` ran successfully.
- Checkpoint validation:
  - Run `python -m pytest -m "not slow"` after documentation updates.

## Safety Guarantees

The checkpoint preserves these boundaries:

- No live trading is implemented.
- No broker API is invoked.
- No automated order placement is implemented.
- No scheduler, cron job, background job, or GitHub Actions workflow is added.
- No `APPROVED_FOR_PAPER` review status is used.
- WATCH_ONLY review is used for all 9 decisions.
- Demo candidates are not strategy recommendations.
- Candidate actions remain `NO_TRADE`; paper decisions remain `SKIP`.
- No market cache mutation occurs during the WATCH_ONLY paper workflow smoke.
- No real network/API calls are used for the checkpoint smoke or documentation validation.
- No secrets are printed or stored.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are local/ignored and must not be committed.
- Paper workflow warnings are expected because no fills were supplied.

## Known Limitations

- WATCH_ONLY smoke validates artifact handoff only; it does not validate trade approval or manual fill reconciliation.
- `paper-workflow-status` remains `WARN` because no fills were supplied and manual attention remains expected.
- ETF/Sina remains PROVISIONAL until another ETF reference source is validated.
- BaoStock `300750` remains outside the default cache pending separate review.
- This is a controlled local smoke, not full-universe backfill or strategy validation.
- The 9-symbol universe is representative, not exhaustive.
- Broader symbol universe validation and fill reconciliation remain future tasks.
- The checkpoint does not certify source truth, data quality beyond the already-run gates, strategy quality, or profitability.

## Recommended Next Engineering Tasks

1. Add a focused paper workflow status improvement so WATCH_ONLY no-fill smoke runs can be summarized with clearer non-blocking actionability.
2. Run a controlled paper fill reconciliation smoke with synthetic/manual fills only, keeping live trading and broker APIs disabled.
3. Add a reviewed decision log for WATCH_ONLY, REJECTED, and future paper approval review outcomes.
4. Continue staged source-universe validation before any larger cache expansion or full-universe workflow.
5. Revisit BaoStock `300750` only after separate source-semantics review.

## Git Tag

Recommended milestone tag:

```text
v0.75.0 = 9-symbol Policy-Aware Export to WATCH_ONLY Paper Workflow Validation
```

Before tagging, run validation and inspect the working tree:

```cmd
python -m pytest -m "not slow"
git status --short
git ls-files | findstr /R /C:"^data/cache" /C:"^data/raw" /C:"^data/processed" /C:"^outputs" /C:"^\.env" /C:"^\.venv" /C:"^secrets"
```

Create the tag only after ChatGPT or the user confirms the checkpoint:

```cmd
git tag -a v0.75.0 -m "9-symbol Policy-Aware Export to WATCH_ONLY Paper Workflow Validation"
git push origin v0.75.0
```
