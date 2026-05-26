# Signal Advisory Contract and Alert Preview v0.1

Signal Advisory turns a local `current-candidates` artifact into auditable advisory signal artifacts and local alert preview text.

It is not live trading, broker integration, order placement, or message delivery. It does not send SMS, email, Telegram, WeChat, webhooks, or broker messages.

## Purpose

The advisory layer sits between candidate generation and any human or execution action:

```text
current-candidates -> signal-advisory -> local alert preview -> human review
```

The output answers:

- what to watch,
- why it appeared in the candidate artifact,
- when the advisory artifact is valid,
- what would invalidate it,
- which safety flags apply,
- whether manual confirmation is required.

Every signal requires manual confirmation. `auto_order_allowed` is always `false`.

## Contract

Each signal includes:

- `signal_id`
- `signal_run_id`
- `signal_date`
- `decision_date`
- `symbol`
- `name`
- `instrument_type`
- `source_candidate_run_id`
- `selection_profile`
- `demo_mode`
- `not_strategy_recommendation`
- `advisory_action`
- `original_score_action`
- `original_candidate_action`
- `final_score`
- `confidence_level`
- `reason_summary`
- `score_breakdown`
- `entry_condition`
- `exit_condition`
- `invalidation_condition`
- `valid_until`
- `risk_notes`
- `data_source_notes`
- `snapshot_manifest_path`
- `candidates_path`
- `requires_manual_confirmation`
- `auto_order_allowed`
- `no_live_trading`
- `no_broker_api`
- `alert_title`
- `alert_body`

Supported advisory actions:

- `WATCH`
- `REVIEW_BUY_CANDIDATE`
- `REVIEW_SELL_CANDIDATE`
- `HOLD_REVIEW`
- `NO_ACTION`
- `BLOCKED`
- `DEMO_ONLY`

These are advisory labels, not orders.

## Demo Inputs

If the source candidate artifact has `selection_profile=demo`, `demo_mode=true`, or `not_strategy_recommendation=true`, generated signals are marked `DEMO_ONLY`.

Demo signals are workflow validation artifacts only:

- they are not strategy recommendations,
- they do not become buy or sell recommendations,
- they require manual confirmation,
- they cannot be auto-ordered,
- they do not change paper review status,
- they do not apply `APPROVED_FOR_PAPER`.

## Artifacts

By default, artifacts are written under:

```text
outputs/reports/signals/<signal_run_id>/
```

Files:

- `signals.csv`
- `signal_alert_preview.md`
- `signal_advisory_report.md`
- `metadata.json`

The alert preview is local text only. No message is sent.

## CLI Usage

Build advisory signals from an explicit current-candidates CSV:

```cmd
python -m quant_replay_system.cli signal-advisory --candidates outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --alert-preview
```

Optional source artifact paths can be supplied explicitly:

```cmd
python -m quant_replay_system.cli signal-advisory --candidates outputs\reports\current_candidates\example\candidates.csv --candidate-report outputs\reports\current_candidates\example\current_candidates_report.md --metadata outputs\reports\current_candidates\example\metadata.json --alert-preview
```

The CLI prints the signal run id, signal count, advisory action counts, artifact paths, and local-only safety statements.

## Future Alert Delivery

Future SMS, email, Telegram, WeChat, or webhook delivery should consume the generated signal artifacts. Delivery must not change trading state, approve paper trades, create orders, or bypass manual confirmation.

Any future delivery workflow should keep a separate audit trail for:

- which local signal artifact was used,
- who approved delivery,
- what message was previewed,
- whether a message was actually sent,
- whether manual confirmation remained required.

## Known MVP Limitations

- Uses existing current-candidates artifacts only.
- Does not validate strategy profitability or recommendation quality.
- Does not provide an interactive alert UI.
- Does not send messages.
- Does not integrate with brokers.
- Does not create positions, fills, or paper approvals.
- Non-demo advisory labels are structure for future review workflows and still require manual confirmation.
