# Paper Trading Review Workflow v0.1

Paper Trading Review Workflow adds a local manual review layer between generated paper decisions and manual paper fills.

It is not live trading. It does not connect to brokers, submit orders, automate order placement, or call broker APIs.

## Why Manual Review Is Required

Generated candidates are research outputs, not orders. Before a manual paper fill can be recorded, a human reviewer should decide whether each candidate is approved, rejected, watch-only, or still pending.

This keeps the paper journal auditable and prevents fills from being entered against unreviewed decisions.

## Review Statuses

- `PENDING_REVIEW`: no final paper decision yet.
- `APPROVED_FOR_PAPER`: allowed for manual hypothetical paper fills.
- `REJECTED`: not allowed for fills.
- `WATCH_ONLY`: monitored but not approved for fills.

The fill recorder and reconciliation logic require `APPROVED_FOR_PAPER` by default.

`WATCH_ONLY` is useful for local workflow smoke tests. A reviewed decision set with all rows marked `WATCH_ONLY`, zero approvals, no fills, and no open or closed positions can validate that current-candidates artifacts pass through paper handoff, review, and daily reporting. It does not approve paper trades, and fills against `WATCH_ONLY` decisions still fail reconciliation by default.

## Review Reason Codes

Supported reason codes:

- `SCORE_CONFIRMED`
- `RISK_TOO_HIGH`
- `LIQUIDITY_TOO_LOW`
- `TECHNICAL_WEAK`
- `OVERHEATED`
- `MANUAL_OVERRIDE`
- `WATCHLIST_ONLY`
- `OTHER`

## Update CSV Format

The update CSV should include:

- `decision_id`
- `manual_review_status`
- `manual_review_notes`
- `reviewer_id`
- `review_reason_code`

`decision_id` and `manual_review_status` are required. If `reviewer_id` is omitted in a row, the CLI-level `--reviewer-id` can fill it.

Example:

```csv
decision_id,manual_review_status,manual_review_notes,reviewer_id,review_reason_code
abc123,APPROVED_FOR_PAPER,Score and liquidity confirmed,msj,SCORE_CONFIRMED
def456,REJECTED,Risk too high,msj,RISK_TOO_HIGH
ghi789,WATCH_ONLY,Monitor only,msj,WATCHLIST_ONLY
```

## Symbol Integrity

Paper review CSVs must preserve market symbols as strings. Leading zeros are part of the identifier: `000001` must remain `000001`, not `1` or `1.0`.

This applies to decisions, review update templates, edited review updates, reviewed decisions, fills, reconciliation, and daily paper reports. The invariant is protected by `tests/test_paper_workflow_symbol_preservation.py`.

## Audit Log

Each review update writes one audit row:

- `audit_id`
- `decision_id`
- `old_status`
- `new_status`
- `old_notes`
- `new_notes`
- `reviewer_id`
- `review_reason_code`
- `review_time`

Audit IDs are deterministic from the decision, status change, reviewer, reason, review time, and config version.

## CLI Usage

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\example\decisions.csv --updates data\paper\review_updates.csv --reviewer-id msj
```

Options:

- `--decisions` required paper decisions CSV.
- `--updates` required review updates CSV.
- `--output-dir` optional review artifact output directory.
- `--reviewer-id` optional default reviewer ID.
- `--allow-pending` allows decisions to remain `PENDING_REVIEW`.
- `--health-check` runs review template health preflight before applying updates.
- `--require-template-health-pass` blocks update application unless template health status is `PASS`.
- `--allow-template-health-warn` explicitly allows `WARN` health status to continue.
- `--template-health-output-dir` optional health artifact output directory.
- `--config` optional config YAML path.

The command writes artifacts and prints the review summary plus the no-live-trading statement. When `--health-check` is used, it prints template health status and report path before applying updates.

Recommended preflight apply command:

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\example\decisions.csv --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv --health-check --reviewer-id msj
```

## Daily Runner Integration

Use the generated `reviewed_decisions.csv` as the preferred input to `paper-daily`:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\reviews\example\reviewed_decisions.csv --fills data\paper\fills.csv
```

`paper-daily` preserves review statuses, notes, reviewer ID, reason code, and review time. If raw candidates are also supplied, reviewed decisions are preferred by default and the runner records a warning.

## Relationship To Fills And Reconciliation

The intended local workflow is:

1. Generate paper decisions.
2. Create and manually edit a review update template.
3. Run health preflight and apply updates with `paper-review-decisions --health-check`.
4. Use `reviewed_decisions.csv` in `paper-daily`.
5. Reconcile fills against reviewed decisions.
6. Generate daily paper reports.

Fills against `REJECTED`, `WATCH_ONLY`, or `PENDING_REVIEW` decisions fail reconciliation by default.

For WATCH_ONLY/no-fills smoke runs, no-fills warnings are expected unless fill reconciliation is explicitly being tested. They should remain visible in reports but should not be confused with broken workflow artifacts when `paper-workflow-status` classifies the run as `WATCH_ONLY_DEMO_VALIDATED_NO_FILLS`.

Synthetic/manual reconciliation diagnostics can intentionally prove that fills against `WATCH_ONLY` decisions are rejected with `DECISION_NOT_APPROVED`. Those failed diagnostics are audit artifacts, not approvals. When they are not linked to the active daily paper run, `paper-workflow-status` keeps them visible as diagnostic reconciliation failures without letting them override the active WATCH_ONLY/no-fills demo state. A failed reconciliation linked to the active daily run remains actionable.

For future synthetic diagnostics, run `paper-reconcile-fills` with `--artifact-scope diagnostic` and an optional `--diagnostic-reason`. This writes explicit metadata such as `artifact_scope=diagnostic`, `diagnostic_artifact=true`, and `active_workflow_artifact=false`. The default scope is `active`; failures from active scoped reconciliation artifacts remain blocking.

## Artifacts

Default output folder:

```text
outputs/reports/paper_trading/reviews/<review_id>/
  reviewed_decisions.csv
  review_audit_log.csv
  review_summary.csv
  paper_review_report.md
  metadata.json
```

`review_id` is deterministic from decision IDs, the update payload, reviewer ID, review time if provided, and config version.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not provide an interactive review UI.
- Does not enforce portfolio sizing or cash checks.
- Does not place or route orders.
- Does not connect to brokers.
- Review decisions are manual audit records, not trading instructions.
