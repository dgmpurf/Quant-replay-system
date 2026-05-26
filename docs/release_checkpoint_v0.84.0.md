# Release Checkpoint v0.84.0

## Milestone

Question-style Single-Symbol Advisory Answer Artifact Views and Research Status Integration.

Recommended tag: `v0.84.0`

## Completed Capabilities

- Added local observability for deterministic question-style single-symbol advisory answer artifacts.
- Added answer artifact view commands:
  - `single-symbol-advisory-answer-index`
  - `single-symbol-advisory-answer-health`
  - `single-symbol-advisory-answer-status`
- Indexed answer artifacts under:

```text
outputs/reports/single_symbol_advisory_answer/
```

- Added health checks for answer artifact completeness and safety boundaries:
  - metadata, markdown answer, and JSON answer readability
  - required answer fields
  - leading-zero symbol preservation, such as `000001`
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`
  - `llm_api_called=false`
  - demo answers do not contain real buy/sell instructions
  - `NOT_FOUND` answers do not invent recommendations
  - no message-delivery metadata
- Added answer status summary for latest local question-style answer runs.
- Integrated `single-symbol-advisory-answer-status` into unified `research-status`.
- Exposed latest answer context in `research-status`, including:
  - latest answer run id
  - latest symbol
  - answer status and stage
  - advisory action
  - health status
  - question and answer style
  - demo and `not_strategy_recommendation` flags
  - markdown answer path
  - answer-layer next manual action
- Preserved later paper workflow priority in unified `research-status`.
- Kept `DEMO_ONLY` answer context visible without turning it into strategy advice.
- Kept safe `NOT_FOUND` answer behavior visible without inventing a recommendation.
- Preserved no LLM/API call, no message delivery, no broker, no live trading, and no auto-order safety boundaries.

Latest local status evidence:

- `single-symbol-advisory-answer-status`
  - status: `WARN`
  - stage: `DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED`
  - latest answer run: `bf19072dd3a4`
  - symbol: `000001`
  - action: `DEMO_ONLY`
  - health: `PASS`
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - question-style answer context visible
  - later paper workflow priority preserved
  - next action remains on the WATCH_ONLY paper workflow path

## Product Vision Alignment

This checkpoint strengthens the product direction of a quantitative research, signal advisory, and human-confirmed execution assistant.

Question-style answers help move toward the user-facing workflow:

```text
User asks about one stock
-> system answers from local advisory artifacts
-> system explains action label, reasons, risks, validity, and invalidation
-> human reviews before any future action
```

The v0.1 answer layer remains deterministic and local. It is not an LLM product, message-delivery workflow, broker integration, or automatic trading system.

## Workflow Impact

The completed workflow chain is:

```text
local candidates / scored dataset
-> single-symbol-advisory
-> question-style answer
-> single-symbol-advisory-answer-index / health / status
-> research-status
-> human review / future alert preview / future delivery channel
```

The artifact views make repeated local answers discoverable and safety-checkable. The unified dashboard now shows latest answer context while preserving priority for later paper workflow states such as `PAPER_WORKFLOW_READY`.

## Validation Baseline

- Backend tests: `1086 passed, 2 warnings`
- Quick tests: `977 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- The answer is not an order.
- Demo answers are not strategy recommendations.
- `NOT_FOUND` does not invent recommendations.
- No automatic buy or sell execution is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery is implemented.
- No LLM API call is implemented or invoked in v0.1.
- Manual confirmation is required.
- `auto_order_allowed=false`.
- `APPROVED_FOR_PAPER` is not applied.
- Market cache is not mutated by answer artifact views or dashboard integration.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Deterministic rendering only.
- No conversational natural-language parsing exists yet.
- `--question` is stored and echoed but not semantically parsed.
- No real alert delivery channel exists.
- Demo outputs remain `DEMO_ONLY`.
- Non-demo advisory labels still require future strategy validation.
- No automatic execution exists.
- No international market support exists yet.

## Recommended Next Engineering Tasks

1. Add a local-only conversational facade that routes user questions to existing deterministic single-symbol answer artifacts before any LLM integration.
2. Draft explicit safety requirements for future LLM-assisted advisory review, including no-order, no-broker, no-secret, and no-message-send boundaries.
3. Add richer risk, data-quality, and invalidation explanations to the underlying single-symbol advisory record.
4. Design a local delivery-preview abstraction that can format alerts without sending them.
5. Preserve manual confirmation and `auto_order_allowed=false` before any delivery-channel, non-demo advisory, or execution-assistant work.
