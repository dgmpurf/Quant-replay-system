# Release Checkpoint v0.83.0

## Milestone

Question-style Single-Symbol Advisory Response.

Recommended tag: `v0.83.0`

## Completed Capabilities

- Extended `single-symbol-advisory` with deterministic question-style answer rendering.
- Added CLI options:
  - `--question-style`
  - `--question`
  - `--answer-style concise|detailed`
  - `--answer-output-dir`
- Generated local answer artifacts under:

```text
outputs/reports/single_symbol_advisory_answer/<answer_run_id>/
```

- Wrote deterministic local answer files:
  - `single_symbol_advisory_answer.md`
  - `single_symbol_advisory_answer.json`
  - `metadata.json`
- Rendered answer sections for:
  - symbol
  - advisory action
  - short answer
  - why
  - score, current action, and score action
  - risk notes
  - data/source caveats
  - entry consideration
  - exit consideration
  - invalidation condition
  - valid-until date
  - manual confirmation and no-auto-order safety fields
- Preserved demo-only answer safety: demo artifacts remain workflow validation only, not real strategy recommendations.
- Preserved `NOT_FOUND` behavior without invented recommendations.
- Preserved leading-zero symbol safety for symbols such as `000001`.
- Recorded safety metadata:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`
  - `llm_api_called=false`
- Added no broker, no live trading, no real message delivery, and no automated-order behavior.

Latest local dry-run:

- `000001`
  - advisory_run_id: `45d8d039dd45`
  - answer_run_id: `bf19072dd3a4`
  - advisory action: `DEMO_ONLY`
  - answer: demo-only workflow validation, not a real trading recommendation
- `999999`
  - advisory_run_id: `715962f35e1f`
  - answer_run_id: `6e51b09f1425`
  - status: `NOT_FOUND`
  - advisory action: `NO_ACTION`
  - answer: cannot review from the provided artifact; no recommendation was invented

## Product Vision Alignment

This milestone adds the first local question-style response layer for the product direction:

```text
User asks: Should I buy, sell, or wait?
System answers from local advisory artifacts with reasons, risks, validity, invalidation, and safety boundaries.
```

The implementation is intentionally deterministic and local. It does not call an LLM, parse the question semantically, fetch new data, send alerts, approve trades, or place orders.

This keeps the near-term product path focused on quantitative research, signal advisory, and human-confirmed execution assistance. Conversational natural-language review, real delivery channels, automation, and international market support remain later-stage goals.

## Workflow Impact

The completed workflow chain is:

```text
local candidates / scored dataset
-> single-symbol-advisory
-> question-style answer
-> local markdown answer
-> local alert preview
-> human review / manual confirmation
```

The question-style layer consumes the existing single-symbol advisory result. It does not change advisory classification, risk gates, source data, paper workflow state, or trading state.

## Validation Baseline

- Backend tests: `1065 passed, 2 warnings`
- Quick tests: `956 passed, 109 deselected, 2 warnings`

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
- Market cache is not mutated by question-style answer rendering.
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

1. Add artifact index, health, and status views for question-style answer artifacts if repeated answer runs need dashboard observability.
2. Design a local-only conversational facade that routes questions to existing deterministic advisory artifacts before any LLM integration.
3. Draft safety requirements for future LLM-assisted review, including no-order, no-broker, no-secret, and no-message-send boundaries.
4. Add richer risk/data-quality explanation fields to the underlying single-symbol advisory result before expanding non-demo semantics.
5. Preserve manual confirmation and `auto_order_allowed=false` before any future alert-delivery or execution-assistant workflow.
