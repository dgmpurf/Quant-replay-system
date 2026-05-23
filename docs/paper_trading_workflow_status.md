# Paper Trading Workflow Status Dashboard v0.1

Paper Trading Workflow Status Dashboard scans local paper-trading artifacts and writes one overview report for the current manual workflow.

It is local-only. It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call market data APIs.

## Purpose

The manual paper trading workflow now writes many artifacts:

- current-candidate reports,
- current-to-paper handoff reports,
- review template handoff reports,
- review template health reports,
- paper review reports,
- daily paper reports,
- reconciliation reports,
- artifact index and health reports.

The dashboard answers:

- What is the latest current-candidate run?
- Has it been handed off to paper trading?
- Has a review template been generated?
- Has the review template health check passed?
- Has `paper-review-decisions` been applied?
- Has `paper-daily` run with reviewed decisions?
- Has fill reconciliation run?
- Are artifact index and health checks available?
- What is the next manual action?

## Scanned Components

The dashboard scans metadata under:

```text
outputs/reports/current_candidates/
outputs/reports/current_candidates/index/
outputs/reports/current_candidates/health/
outputs/reports/current_to_paper_handoff/
outputs/reports/current_to_paper_review_handoff/
outputs/reports/paper_trading/review_template_health/
outputs/reports/paper_trading/reviews/
outputs/reports/paper_trading/daily/
outputs/reports/paper_trading/reconciliation/
outputs/reports/paper_trading/index/
outputs/reports/paper_trading/health/
```

It reads existing `metadata.json` files only. It does not rerun workflow steps.

## Active Reviewed Workflow Chain

When daily paper artifacts exist, the dashboard first selects the latest relevant `DAILY_PAPER` artifact and prefers a daily run with `reviewed_decisions_used=true`.

If that daily metadata includes `reviewed_decisions_path`, the dashboard follows that path back to the matching paper review artifact and then to the template-health artifact recorded in the review metadata. This keeps the active workflow status aligned with the reviewed decisions that the daily paper report actually used.

Older review or template-health artifacts remain discoverable through `paper-index` and `paper-health-check`, and stale warnings can appear in component notes. They do not define the active workflow stage when a later linked reviewed flow is available.

## Stage Meanings

- `NO_CURRENT_CANDIDATES`: no current-candidate artifact found.
- `CURRENT_CANDIDATES_READY`: candidates exist and can be handed to paper trading.
- `HANDOFF_READY`: current-to-paper handoff exists and review template generation is next.
- `REVIEW_TEMPLATE_READY`: review template exists; manual edit and review apply are next.
- `REVIEW_TEMPLATE_HEALTH_WARN`: template health warnings need review.
- `REVIEW_TEMPLATE_HEALTH_FAIL`: template health errors must be fixed.
- `REVIEW_READY`: reviewed decisions exist and can feed `paper-daily`.
- `DAILY_PAPER_READY`: daily paper report exists and fills/reconciliation are next.
- `RECONCILIATION_READY`: reconciliation exists and artifact index/health checks are next.
- `WORKFLOW_COMPLETE`: the discovered workflow appears complete and health checks pass.
- `WORKFLOW_NEEDS_ATTENTION`: one or more explicit failures or warnings need review.

## Next Manual Action Logic

The dashboard recommends one next step based on the inferred stage:

- Run `current-candidates`.
- Run `current-to-paper`.
- Run `current-to-paper-review`.
- Manually edit `review_updates_template.csv`.
- Run `paper-review-decisions --health-check`.
- Run `paper-daily --reviewed-decisions`.
- Enter manual fills CSV or run `paper-reconcile-fills`.
- Run `paper-index` and `paper-health-check`.
- Review warnings/errors.

These are workflow prompts, not trading instructions.

## CLI Usage

Build a workflow status dashboard from the default report root:

```cmd
python -m quant_replay_system.cli paper-workflow-status
```

Use a custom report root:

```cmd
python -m quant_replay_system.cli paper-workflow-status --root outputs\reports
```

Filter by decision date and universe:

```cmd
python -m quant_replay_system.cli paper-workflow-status --decision-date 2024-05-20 --universe etf_core
```

Write dashboard artifacts to a custom folder:

```cmd
python -m quant_replay_system.cli paper-workflow-status --output-dir outputs\reports\paper_trading\workflow_status
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
outputs/reports/paper_trading/workflow_status/<workflow_status_id>/
```

Files:

- `paper_workflow_status_report.md`
- `paper_workflow_status.csv`
- `paper_workflow_summary.csv`
- `metadata.json`

`workflow_status_id` is deterministic from the decision date filter, discovered artifact IDs, statuses, and config version.

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

- Uses local CSV/mock artifacts only.
- Relies on existing `metadata.json` files.
- Does not repair missing or stale artifact references.
- Does not verify full CSV schemas; artifact health modules handle file readability.
- Stage inference is conservative when metadata is incomplete.
- Does not replace manual review.
