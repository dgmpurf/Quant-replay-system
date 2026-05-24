# Unified Local Research Workflow Dashboard v0.1

The Unified Local Research Workflow Dashboard is a local-only top-level status report for the research flow from data preparation to current candidates to manual paper trading.

It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call network APIs.

## Purpose

The project now has separate dashboards and health checks for data preparation, current-candidate artifacts, and paper trading. The unified dashboard answers:

- Has data preparation produced usable artifacts?
- Has snapshot quality run?
- Has a reviewed offline market update handoff produced snapshot/current-candidate artifacts?
- Have current candidates been generated?
- Are current-candidate artifacts healthy?
- Has the current-to-paper handoff run?
- Has the paper review template been created and checked?
- Have reviewed decisions, daily paper reports, and reconciliation artifacts been produced?
- Has the paper workflow dashboard run?
- What is the next manual action?

## Workflow Areas

The dashboard scans metadata under:

```text
outputs/reports/data_preparation/workflow_status/
outputs/reports/snapshot_quality/
outputs/reports/market_update_handoff/status/
outputs/reports/current_candidates/
outputs/reports/current_candidates/health/
outputs/reports/current_to_paper_handoff/
outputs/reports/current_to_paper_review_handoff/
outputs/reports/paper_trading/review_template_health/
outputs/reports/paper_trading/reviews/
outputs/reports/paper_trading/daily/
outputs/reports/paper_trading/reconciliation/
outputs/reports/paper_trading/workflow_status/
```

It reads existing local `metadata.json` or `handoff_metadata.json` files only. It does not rerun any workflow step.

## Market Update Handoff Status

`research-status` includes `market-update-handoff-status` as a pre-paper workflow component when those artifacts exist.

The unified summary records the latest handoff id, handoff status/stage, linked pipeline id, linked snapshot-quality status, linked current-candidate run id, and the handoff's next manual action. When the handoff stage is `CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST`, the dashboard treats current candidates as ready for a local paper workflow smoke test and recommends `current-to-paper`.

If a handoff is `WARN` only because provisional rows such as AKShare/Sina ETF `WARN_ACCEPT` rows were included, the warning remains visible but is classified as non-blocking for the active workflow. Broken handoff health or missing linked artifacts remain actionable when the handoff is the active stage.

## Active Paper Flow Selection

For paper trading components, `research-status` uses the same active reviewed-flow idea as `paper-workflow-status`.

When the latest daily paper artifact used reviewed decisions, the dashboard follows `reviewed_decisions_path` to the matching paper review artifact and then uses that review's linked template-health metadata. This prevents an older unrelated warning template from making the active paper workflow look stale.

Stale artifacts are still useful audit evidence. They remain available in paper indexes and health reports, and stale warning counts may be noted, but the unified dashboard stage follows the active daily reviewed workflow chain.

If a paper workflow has already advanced beyond the market-update-handoff stage, the paper workflow state takes precedence. Older handoff warnings or failures remain visible as stale audit context and do not move the active stage back to "run current-to-paper."

## Warning Actionability

`research-status` preserves raw warning counts and adds actionability counts inherited from component dashboards where available:

- `EXPECTED_DEMO_WARNING`: expected in explicit local dry-run workflows, such as a `WATCH_ONLY` paper daily run with no fills.
- `STALE_ARTIFACT_WARNING`: warning from an older dry-run artifact that is no longer part of the active workflow chain.
- `ACTIONABLE_WARNING`: warning that should be reviewed before continuing.
- `BLOCKING_ERROR`: missing, unreadable, or failed active artifacts.

If the only warnings are expected demo or stale artifact warnings, the dashboard does not treat them as active blockers. It keeps the raw `WARN` status for audit visibility and recommends the demo-specific next action instead of the generic `Review warnings/errors` prompt.

Prior current-candidate health warnings from old dry runs can be classified as stale when the health issue `run_id` does not match the active current-candidate run.

## Stage Meanings

- `NO_DATA`: no useful local workflow artifacts were found.
- `DATA_PREPARATION_READY`: data preparation status exists; current candidates are next.
- `SNAPSHOT_READY`: snapshot quality exists; current candidates are next.
- `CURRENT_CANDIDATES_READY`: current-candidate artifacts exist; index/health checks are next.
- `CURRENT_CANDIDATES_HEALTH_READY`: current-candidate health exists; current-to-paper is next.
- `CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST`: a market-update-handoff produced current candidates ready for a local paper workflow smoke test.
- `PAPER_HANDOFF_READY`: current-to-paper handoff exists; review template generation is next.
- `REVIEW_TEMPLATE_READY`: review template exists and needs manual editing.
- `REVIEW_TEMPLATE_HEALTH_READY`: template health passed; review decisions can be applied.
- `REVIEW_APPLIED`: reviewed decisions exist; daily paper trading is next.
- `PAPER_DAILY_READY`: daily paper report exists; manual fills and reconciliation are next.
- `RECONCILIATION_READY`: reconciliation exists; paper workflow status is next.
- `PAPER_WORKFLOW_READY`: paper workflow status exists and should be reviewed.
- `LOCAL_RESEARCH_WORKFLOW_COMPLETE`: the discovered workflow appears complete.
- `LOCAL_RESEARCH_NEEDS_ATTENTION`: at least one warning or error needs review.

## Next Manual Action Logic

The dashboard recommends one conservative next step, such as:

- Run `data-pipeline`.
- Run `current-candidates`.
- Run `current-candidates-index`.
- Run `current-candidates-health`.
- Run `current-to-paper`.
- Run `current-to-paper-review`.
- Manually edit `review_updates_template.csv`.
- Run `paper-review-decisions --health-check`.
- Run `paper-daily --reviewed-decisions`.
- Enter manual fills CSV.
- Run `paper-reconcile-fills`.
- Run `paper-workflow-status`.
- Review warnings/errors.
- Continue or clean up expected demo/stale warning artifacts when they are not active blockers.

These prompts are workflow reminders, not trading advice.

## CLI Usage

Build the unified dashboard from the default report root:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports
```

Filter by decision date and universe:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --decision-date 2024-05-20 --universe etf_core
```

Write to a custom output directory:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --output-dir outputs/reports/local_research_dashboard
```

Strict mode exits non-zero when the dashboard status is `WARN`:

```powershell
python -m quant_replay_system.cli research-status --root outputs/reports --strict
```

The CLI prints:

- overall status,
- workflow stage,
- latest decision date,
- next manual action,
- report path,
- `No live trading or broker API was invoked.`

## Artifact Outputs

Default output folder:

```text
outputs/reports/local_research_dashboard/<dashboard_id>/
```

Files:

- `local_research_dashboard.md`
- `local_research_dashboard.csv`
- `local_research_summary.csv`
- `metadata.json`

`dashboard_id` is deterministic from the decision date filter, discovered artifact IDs, statuses, and config version.

## Relationship To Other Dashboards

- `data-prep-status` focuses on local data preparation.
- `paper-workflow-status` focuses on the manual paper trading workflow.
- `research-status` combines those local artifact signals with current-candidate and handoff artifacts into one top-level view.

## Local-Only Guarantee

The dashboard only reads local metadata and writes local report artifacts.

It does not:

- place orders,
- connect to brokers,
- automate manual review,
- auto-approve trades,
- call network APIs,
- read or print secrets.

## Known MVP Limitations

- Uses local metadata only.
- Does not repair missing or stale artifact references.
- Does not validate full CSV schemas; artifact health modules handle file readability.
- Does not rerun failed data-prep, current-candidate, or paper workflow steps.
- Stage inference is conservative when metadata is incomplete.
