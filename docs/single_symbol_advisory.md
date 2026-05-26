# Single-Symbol Advisory Review v0.1

Single-Symbol Advisory Review answers a focused local question about one symbol using existing candidate, scored, or signal advisory artifacts.

It is advisory only. It is not an order, paper approval, broker instruction, alert delivery workflow, or automated execution step.

## Purpose

The workflow supports a local human-in-the-loop review question:

```text
symbol + local artifacts -> single-symbol-advisory -> report / CSV / JSON / optional alert preview -> manual review
```

It can help explain:

- whether the symbol appears in the provided local artifact,
- what the source candidate or score action was,
- what the advisory action label is,
- why that label was assigned,
- when the artifact is valid,
- what invalidates it,
- what risk and data-quality caveats apply,
- whether manual confirmation is required.

The answer is constrained by the provided artifact. If the symbol is absent, the workflow returns `NOT_FOUND` and does not invent a recommendation.

## Inputs

For v0.1, provide at least one of:

- `--candidates <candidates.csv>`
- `--scored-dataset <scored_dataset.csv>`
- `--signals <signals.csv>`

Optional context:

- `--factor-dataset <factor_dataset.csv>`
- `--metadata <metadata.json>`
- `--snapshot-manifest <snapshot_manifest.json>`
- `--date <YYYY-MM-DD>`
- `--alert-preview`

Symbol values are treated as text. A symbol such as `000001` remains `000001`.

## Advisory Actions

Supported advisory labels:

- `DEMO_ONLY`
- `WATCH`
- `REVIEW_BUY_CANDIDATE`
- `REVIEW_SELL_CANDIDATE`
- `HOLD_REVIEW`
- `NO_ACTION`
- `BLOCKED`

These labels are not orders.

Demo inputs keep conservative behavior:

- `selection_profile=demo`, `demo_mode=true`, or `not_strategy_recommendation=true` produces `DEMO_ONLY` unless the row is blocked.
- Demo output is workflow validation only.
- Demo output is not strategy advice.
- Manual confirmation is still required.
- `auto_order_allowed=false`.

If the source row is blocked by `risk_precheck_status`, `score_action`, or candidate action, the advisory action is `BLOCKED`.

If the source action is `NO_TRADE`, the advisory action is `NO_ACTION`.

Non-demo structural labels such as `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE` are allowed only when the source artifact already supports that action. They still require manual confirmation and do not allow auto-order placement.

## Artifacts

Artifacts are written under:

```text
outputs/reports/single_symbol_advisory/<advisory_run_id>/
```

Files:

- `single_symbol_advisory_report.md`
- `single_symbol_advisory.json`
- `single_symbol_advisory.csv`
- `metadata.json`
- `alert_preview.md` when `--alert-preview` is supplied

The alert preview is markdown only. It is not sent to SMS, email, Telegram, WeChat, webhooks, or any broker.

## CLI Usage

Review one symbol from current candidates:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --alert-preview
```

Use explicit metadata and scored dataset context:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\example\candidates.csv --scored-dataset outputs\reports\current_candidates\example\scored_dataset.csv --metadata outputs\reports\current_candidates\example\metadata.json --alert-preview
```

The CLI prints the advisory run id, status, symbol, advisory action, artifact paths, and safety flags.

## Safety Contract

Every output records:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_message_sent=true`

The workflow does not:

- place orders,
- approve paper trades,
- apply `APPROVED_FOR_PAPER`,
- connect to brokers,
- mutate market cache,
- send messages,
- call network APIs.

## Known MVP Limitations

- Uses local artifacts only.
- Does not fetch market data.
- Does not validate strategy profitability.
- Does not provide natural-language conversation yet.
- Does not provide real alert delivery.
- Demo artifacts produce review-only output and are not strategy recommendations.
- International market semantics are not implemented.
