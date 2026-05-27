# Signal Advisory Semantics Policy v0.1

Signal Advisory Semantics maps local candidate, scored, or signal rows into advisory action labels.

It is a deterministic policy layer. It is not live trading, broker integration, order placement, paper approval, message delivery, or a strategy recommendation.

## Purpose

The semantics policy sits between quantitative artifacts and advisory-facing reports:

```text
current-candidates / scored dataset
-> signal-semantics
-> advisory labels
-> signal-advisory / single-symbol advisory / human review
```

It answers:

- whether a row is blocked by risk or quality context,
- whether a demo row must remain workflow validation only,
- whether a non-demo row can be labeled as a structural review candidate,
- what risks and caveats should remain visible,
- whether manual confirmation and no-auto-order safety fields are preserved.

## Advisory Labels

Supported labels:

- `DEMO_ONLY`
- `WATCH`
- `REVIEW_BUY_CANDIDATE`
- `REVIEW_SELL_CANDIDATE`
- `HOLD_REVIEW`
- `NO_ACTION`
- `BLOCKED`

These labels are advisory states, not orders.

`REVIEW_BUY_CANDIDATE` means "review this candidate manually." It does not mean buy now, approve for paper, send an order, or connect to a broker.

## Policy Rules

The v0.1 policy is intentionally conservative:

1. Rows are `BLOCKED` when risk, score, missing symbol, unavailable data, `data_quality_status=FAIL`, or `snapshot_quality_status=FAIL` makes the row unsafe for review.
2. Demo or not-strategy rows become `DEMO_ONLY` after block checks. They never become buy-review or sell-review guidance.
3. Non-demo high-score rows can become `REVIEW_BUY_CANDIDATE` only as a structural human-review label.
4. Explicit non-demo sell or hold labels can become `REVIEW_SELL_CANDIDATE` or `HOLD_REVIEW`.
5. `NO_TRADE` becomes `NO_ACTION`.
6. Moderate non-demo rows can become `WATCH`.
7. Missing fields do not crash the run. The policy records issues and falls back conservatively.

Every output row keeps:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_message_sent=true`

## Configuration

Default settings live in `config/default.yaml`:

```yaml
signal_semantics:
  output_dir: outputs/reports/signal_semantics
  reviewed_buy_min_score: 70
  watch_min_score: 55
  require_snapshot_quality_pass: true
  require_data_quality_pass: true
  allow_review_buy_for_demo: false
  allow_auto_order: false
```

`allow_review_buy_for_demo` and `allow_auto_order` must remain disabled. The implementation raises if those safety boundaries are enabled.

## CLI Usage

Run semantics on a current-candidates artifact:

```cmd
python -m quant_replay_system.cli signal-semantics --input outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --input-type candidates --profile demo
```

Run with explicit quality status overrides:

```cmd
python -m quant_replay_system.cli signal-semantics --input outputs\reports\manual_diagnostics\signal_semantics_synthetic_reviewed_fixture.csv --input-type candidates --profile reviewed_local_v0 --snapshot-quality-status PASS --data-quality-status PASS
```

The CLI prints the semantics run id, status, row count, advisory action counts, artifact paths, and safety flags.

## Index, Health, And Status

Use `signal-semantics-index` to discover local semantics runs:

```cmd
python -m quant_replay_system.cli signal-semantics-index
```

The index scans `outputs/reports/signal_semantics/` and writes:

```text
outputs/reports/signal_semantics/index/
  signal_semantics_index.csv
  signal_semantics_index_report.md
  metadata.json
```

Index rows include the semantics run id, status, row count, advisory action counts, issue count, input path, profile, quality status fields, safety flags, and artifact paths.

Use `signal-semantics-health` to check artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli signal-semantics-health
```

Health checks verify:

- `metadata.json` is readable,
- `signal_semantics.csv` exists and has the required columns,
- `signal_semantics_report.md` exists,
- `signal_semantics_issues.csv` is readable when present,
- leading-zero symbols such as `000001` remain six-character strings,
- demo semantics do not contain `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE`,
- `auto_order_allowed=false`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- no message delivery metadata is present,
- no `APPROVED_FOR_PAPER` metadata is present,
- `BLOCKED` rows include reason or issue context where possible.

Health artifacts are written under:

```text
outputs/reports/signal_semantics/health/<health_id>/
  signal_semantics_health_report.md
  signal_semantics_health_issues.csv
  signal_semantics_health_summary.csv
  metadata.json
```

Use `signal-semantics-status` to summarize the latest semantics run:

```cmd
python -m quant_replay_system.cli signal-semantics-status
```

The status view reports the latest semantics run id, health status, action counts, issue count, workflow stage, report path, and next manual action.

Expected stages include:

- `NO_SIGNAL_SEMANTICS_ARTIFACTS`
- `DEMO_SIGNAL_SEMANTICS_VALIDATED`
- `SIGNAL_SEMANTICS_READY_FOR_REVIEW`
- `SIGNAL_SEMANTICS_HEALTH_WARN`
- `SIGNAL_SEMANTICS_FAILED`

For a demo-only run, the expected stage is `DEMO_SIGNAL_SEMANTICS_VALIDATED`, and the next action reminds the user not to treat `DEMO_ONLY` labels as strategy recommendations. For non-demo structural runs, the status may be ready for review, but labels still require manual confirmation and do not permit auto-order.

## Research Status Integration

`research-status` includes the latest `signal-semantics-status` as advisory-policy context. The unified dashboard exports:

- `latest_signal_semantics_run_id`
- `signal_semantics_status`
- `signal_semantics_stage`
- `signal_semantics_health_status`
- action counts for `DEMO_ONLY`, `WATCH`, `REVIEW_BUY_CANDIDATE`, `REVIEW_SELL_CANDIDATE`, `HOLD_REVIEW`, `NO_ACTION`, and `BLOCKED`
- `signal_semantics_issue_count`
- `signal_semantics_profile`
- `signal_semantics_input_path`
- `signal_semantics_report_path`
- `signal_semantics_next_action`

When the latest run is `SIGNAL_SEMANTICS_READY_FOR_REVIEW`, the dashboard treats review labels as manual review context. `REVIEW_BUY_CANDIDATE` remains a human-review candidate, not an order, and auto-order remains disabled. When the latest run is `DEMO_SIGNAL_SEMANTICS_VALIDATED`, the dashboard keeps demo rows as `DEMO_ONLY` workflow validation, not strategy recommendations.

Later workflow stages such as signal advisory, single-symbol advisory, advisory conversation, market-update handoff, and paper workflow take priority for the final `workflow_stage`. Signal semantics fields remain visible for audit. Active semantics health failures remain actionable when no later valid workflow supersedes them.

## Artifacts

Artifacts are written under:

```text
outputs/reports/signal_semantics/<semantics_run_id>/
```

Files:

- `signal_semantics.csv`
- `signal_semantics_report.md`
- `signal_semantics_issues.csv`
- `metadata.json`

Generated outputs are local diagnostics and are ignored by git. They should not be committed.

## Safety Boundaries

- Advisory labels are not orders.
- Demo rows are not strategy recommendations.
- `REVIEW_BUY_CANDIDATE` is human-review-only language.
- No automatic BUY/SELL execution is implemented.
- No broker API or live trading is implemented.
- No message delivery is implemented.
- `APPROVED_FOR_PAPER` is not applied.
- Data-quality and snapshot-quality failures remain blocking.
- Manual confirmation remains required.

## Known MVP Limitations

- The policy uses local artifact fields only.
- Non-demo thresholds are structural defaults, not validated strategy semantics.
- Sell and hold labels are not inferred from market behavior in v0.1; they require explicit source labels.
- Quality status is consumed when present or supplied by CLI, but the command does not run data-quality or snapshot-quality itself.
- No alert delivery, broker integration, automation, or international market support is included.
