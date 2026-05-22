# Paper Review Template Health Check v0.1

Paper Review Template Health Check validates an edited `review_updates_template.csv` before `paper-review-decisions` applies it.

It is local-only. It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call market data APIs.

## Why Health Checks Are Needed

`current-to-paper-review` creates a review update template for manual editing. Before that file changes the paper review audit log, the health check catches common problems:

- missing required columns,
- invalid review statuses,
- duplicate decision updates,
- unknown decision IDs when `decisions.csv` is supplied,
- invalid reason codes,
- missing reviewer IDs or notes,
- risky approvals such as approving a non-PASS risk row.

The health check is advisory and validating. It does not apply updates.

## Required Columns

The update template should include:

- `decision_id`
- `manual_review_status`
- `manual_review_notes`
- `reviewer_id`
- `review_reason_code`

Extra context columns such as `symbol`, `final_score`, `risk_precheck_status`, and `risk_precheck_reason` can be present and are preserved for reporting context.

## Status Validation

Allowed `manual_review_status` values:

- `PENDING_REVIEW`
- `APPROVED_FOR_PAPER`
- `REJECTED`
- `WATCH_ONLY`

Invalid status values fail the health check.

## Reason Code Validation

Allowed `review_reason_code` values:

- `SCORE_CONFIRMED`
- `RISK_TOO_HIGH`
- `LIQUIDITY_TOO_LOW`
- `TECHNICAL_WEAK`
- `OVERHEATED`
- `MANUAL_OVERRIDE`
- `WATCHLIST_ONLY`
- `OTHER`

Invalid reason codes warn by default. A blank reason for `APPROVED_FOR_PAPER`, `REJECTED`, or `WATCH_ONLY` also warns.

## Decision-Aware Checks

When a matching `decisions.csv` is supplied, the health check can also detect:

- unknown `decision_id`,
- `APPROVED_FOR_PAPER` on `risk_precheck_status` other than `PASS`,
- approval of a low `final_score`,
- rejection or watch-only status on high-score rows.

These checks help catch risky manual edits before fills are reconciled.

## PASS / WARN / FAIL

- `PASS`: no warnings or errors.
- `WARN`: warnings only.
- `FAIL`: at least one error.

The CLI exits non-zero on `FAIL` by default. With `--strict`, `WARN` also exits non-zero unless `--allow-warn` is passed.

## CLI Usage

Health check an update template:

```cmd
python -m quant_replay_system.cli paper-review-template-health --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv
```

Health check with matching decisions for stronger validation:

```cmd
python -m quant_replay_system.cli paper-review-template-health --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv --decisions outputs\reports\paper_trading\daily\example\decisions.csv
```

Strict warning handling:

```cmd
python -m quant_replay_system.cli paper-review-template-health --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv --decisions outputs\reports\paper_trading\daily\example\decisions.csv --strict
```

Allow warnings in strict workflows:

```cmd
python -m quant_replay_system.cli paper-review-template-health --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv --decisions outputs\reports\paper_trading\daily\example\decisions.csv --strict --allow-warn
```

The CLI prints:

```text
No live trading or broker API was invoked.
```

## Artifact Outputs

Default output folder:

```text
outputs/reports/paper_trading/review_template_health/<health_check_id>/
```

Files:

- `review_template_health_report.md`
- `review_template_health_issues.csv`
- `review_template_health_summary.csv`
- `metadata.json`

`health_check_id` is deterministic from update decision IDs, statuses, reviewer IDs, reason codes, and config version.

## Relationship To The Review Workflow

Recommended local flow:

```text
current-to-paper-review
  -> manually edit review_updates_template.csv
  -> paper-review-template-health
  -> paper-review-decisions
  -> paper-daily --reviewed-decisions
```

This health check does not automatically block `paper-review-decisions`; it gives a local validation step the user can run before applying updates.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not provide an interactive review UI.
- Does not apply review updates.
- Does not auto-approve trades.
- Decision-aware checks require `decisions.csv`.
- Does not place or route orders.
- Does not connect to brokers.
