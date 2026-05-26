# Release Checkpoint v0.81.0

## Milestone

Single-Symbol Advisory Review.

Recommended tag: `v0.81.0`

## Completed Capabilities

- Added the `single-symbol-advisory` module and CLI command.
- Enabled a user to input one symbol and review it against local candidate, scored, factor, or signal artifacts.
- Preserved leading-zero symbols such as `000001`.
- Returned `NOT_FOUND` for missing symbols without inventing recommendations.
- Kept demo candidate output as `DEMO_ONLY`, not real buy or sell guidance.
- Preserved blocked source rows as `BLOCKED`.
- Preserved `NO_TRADE` source rows as `NO_ACTION` or watch-style review behavior.
- Generated local single-symbol advisory artifacts:
  - `single_symbol_advisory.csv`
  - `single_symbol_advisory.json`
  - `single_symbol_advisory_report.md`
  - `metadata.json`
  - `alert_preview.md` when requested
- Rendered local alert preview markdown only.
- Recorded safety flags:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`

Latest local dry-run:

- Source artifact: `outputs/reports/current_candidates/2024-05-20_etf_core_f484cd4648/candidates.csv`
- `000001`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
  - final_score: `55.600644074275095`
- `510300`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
  - final_score: `52.960111927644135`
- `999999`
  - status: `NOT_FOUND`
  - advisory_action: `NO_ACTION`
  - no recommendation was invented

## Product Vision Alignment

This milestone is the first local implementation of the user's desired single-symbol advisory question:

```text
I input a stock, and the system tells me whether to watch, buy-review, sell-review, hold, or avoid, with reasons, risk notes, validity, and manual confirmation.
```

For v0.1, the workflow uses existing local artifacts only. When the source artifacts are demo candidates, the answer remains `DEMO_ONLY` and is not a strategy recommendation.

This moves the project closer to the near-term product goal: quantitative research plus signal advisory plus human-confirmed execution assistance. Full automation, real alert delivery, and international market expansion remain later-stage goals.

## Workflow Impact

The completed workflow chain is:

```text
local candidates / scored dataset
-> single-symbol-advisory
-> single_symbol_advisory.csv / json / report
-> local alert preview
-> human review / manual confirmation
```

The command creates a focused artifact boundary for one-symbol review without changing trading state, applying paper approvals, sending alerts, or creating orders.

## Validation Baseline

- Backend tests: `1043 passed, 2 warnings`
- Quick tests: `934 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- Advisory output is not an order.
- Demo advisory output is not a strategy recommendation.
- No automatic buy or sell execution is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery is implemented.
- Manual confirmation is required.
- `auto_order_allowed=false`.
- `APPROVED_FOR_PAPER` is not applied.
- Market cache is not mutated.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Uses local artifacts only.
- No conversational natural-language review exists yet.
- No real alert delivery channel exists.
- Demo outputs remain `DEMO_ONLY`.
- Non-demo advisory labels still require future strategy validation.
- No automatic execution exists.
- No international market support exists yet.

## Recommended Next Engineering Tasks

1. Add single-symbol advisory index, health, and status views so repeated symbol reviews are discoverable and dashboard-ready.
2. Integrate single-symbol advisory status into `research-status` as context without overriding later paper workflow priority.
3. Add richer non-demo advisory validation before any `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE` label is treated as research-review evidence.
4. Design local-only alert delivery dry-run metadata before implementing any real message channel.
5. Preserve human confirmation and no-auto-order safety boundaries before any future execution-assistant work.
