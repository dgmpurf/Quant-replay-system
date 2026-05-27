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
