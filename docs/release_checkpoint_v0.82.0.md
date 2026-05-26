# Release Checkpoint v0.82.0

## Milestone

Single-Symbol Advisory Artifact Views and Research Status Integration.

Recommended tag: `v0.82.0`

## Completed Capabilities

- Added local artifact views for repeated single-symbol advisory reviews:
  - `single-symbol-advisory-index`
  - `single-symbol-advisory-health`
  - `single-symbol-advisory-status`
- Integrated `single-symbol-advisory-status` into unified `research-status`.
- Exported latest single-symbol advisory context in `research-status` summary CSV, metadata, markdown report, and CLI output.
- Surfaced latest advisory run id, latest symbol, advisory status/stage/action, health status, final score, demo flags, alert preview path, and next manual action.
- Preserved `NOT_FOUND` handling without invented recommendations.
- Kept `DEMO_ONLY` advisory context visible without turning it into buy or sell guidance.
- Preserved leading-zero symbol safety for symbols such as `000001`.
- Preserved local alert preview context without sending real messages.
- Preserved manual confirmation and safety flags:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - no broker API
  - no live trading
  - no message sending
- Preserved later paper workflow priority: a valid paper workflow remains the final active stage while the latest one-symbol review remains visible as context.

Latest local dry-run:

- `single-symbol-advisory-status`
  - status: `WARN`
  - stage: `SINGLE_SYMBOL_ADVISORY_NOT_FOUND`
  - latest advisory run: `715962f35e1f`
  - latest symbol: `999999`
  - advisory action: `NO_ACTION`
  - health: `PASS`
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - latest single-symbol advisory run: `715962f35e1f`
  - latest symbol: `999999`
  - single-symbol stage: `SINGLE_SYMBOL_ADVISORY_NOT_FOUND`
  - single-symbol health: `PASS`
  - later paper workflow priority preserved

`999999` did not produce fake advice. `NOT_FOUND` remains safe review context when no recommendation is invented.

## Product Vision Alignment

This milestone strengthens the project's near-term direction as a quantitative research, signal advisory, and human-confirmed execution assistant.

The user-facing product goal includes asking about one symbol and receiving watch, buy-review, sell-review, hold, avoid, or missing-context feedback with reasons and risk notes. This checkpoint makes repeated single-symbol reviews discoverable and visible in the unified research dashboard before any delivery channel, non-demo semantics, or execution-assistant work.

Single-symbol advisory remains advisory only. It is not an order, not paper approval, not broker instruction, and not a strategy recommendation when sourced from demo artifacts.

Full automation and international market expansion remain later-stage goals.

## Workflow Impact

The completed workflow chain is:

```text
local candidates / scored dataset
-> single-symbol-advisory
-> single-symbol-advisory-index / health / status
-> research-status
-> human review / future alert preview / future paper workflow
```

`research-status` now treats single-symbol advisory as contextual evidence. If the one-symbol review is the active stage, health failures remain actionable. If a broader signal advisory, reviewed export, current-candidates run, market-update handoff, or paper workflow already exists, that later workflow keeps final-stage priority and the one-symbol review remains visible for audit.

## Validation Baseline

- Backend tests: `1061 passed, 2 warnings`
- Quick tests: `952 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- Advisory output is not an order.
- `NOT_FOUND` is not a recommendation.
- Demo advisory output is not a strategy recommendation.
- No automatic buy or sell execution is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery is implemented.
- Manual confirmation is required.
- `auto_order_allowed=false`.
- `APPROVED_FOR_PAPER` is not applied.
- Market cache is not mutated by advisory status views.
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

1. Add a local-only conversational single-symbol review facade that consumes existing single-symbol advisory artifacts without fetching data or sending messages.
2. Add a non-demo advisory validation plan before enabling any `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE` semantics beyond structural labels.
3. Design alert-delivery dry-run metadata for SMS/email/Telegram/WeChat-style channels before implementing any real delivery.
4. Add richer data-quality and source-caveat explanations to single-symbol advisory reports.
5. Preserve manual confirmation, `auto_order_allowed=false`, and no-broker/no-live-trading boundaries before any future execution-assistant workflow.
