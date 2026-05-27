# Release Checkpoint v0.90.0: Shared Signal Semantics Wiring Across Advisory Layers

## Milestone Name

Shared Signal Semantics Wiring Across Advisory Layers v0.1.

Recommended tag: `v0.90.0`

## Completed Capabilities

- Completed the read-only audit of existing advisory classification points.
- Wired `signal-advisory` to the shared `signal_semantics` classification policy.
- Wired `single-symbol-advisory` to the shared `signal_semantics` classification policy.
- Confirmed question-style single-symbol answers inherit the shared single-symbol advisory semantics result.
- Confirmed `advisory-conversation` remains deterministic parser/routing only and does not perform independent trading classification.
- Preserved `DEMO_ONLY` safety for demo rows and high-score demo rows.
- Preserved `REVIEW_BUY_CANDIDATE` as a human-review-only label, not an order.
- Preserved `BLOCKED` propagation for risk `FAIL` and blocked rows.
- Preserved `NO_TRADE` as `NO_ACTION`.
- Preserved safe `NOT_FOUND` behavior: `NO_ACTION` with no invented recommendation.
- Preserved safe `PARSE_FAILED` behavior: no invented symbol and no invented recommendation.
- Preserved local-only safety flags:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`

## Workflow Impact

Shared semantics are now the classification path for product-facing advisory layers:

```text
current-candidates / scored rows
-> signal_semantics
-> signal-advisory
-> single-symbol-advisory
-> question-style answer
-> advisory-conversation
-> research-status / paper workflow as later stages
```

`signal-advisory` and `single-symbol-advisory` no longer maintain separate advisory-action mapping logic. They call the shared policy internally, so users do not need to run `signal-semantics` separately before generating advisory artifacts.

Question-style answers and advisory-conversation outputs continue to consume the single-symbol advisory result. This keeps the user-facing answer layer deterministic and prevents conversational routing from becoming a separate trading classifier.

Later `research-status` and paper workflow states remain later workflow stages. This milestone changes advisory classification consistency, not trading approval or workflow priority.

## Validation Baseline

- Focused tests: passed.
- Backend tests: `1154 passed, 2 warnings`.
- Quick tests: `1045 passed, 109 deselected, 2 warnings`.

Latest local dry-runs:

- `single-symbol-advisory --symbol 000001 --question-style`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
  - final_score: `55.600644074275095`
  - `requires_manual_confirmation=True`
  - `auto_order_allowed=False`
  - `no_live_trading=True`
  - `no_broker_api=True`
  - `no_message_sent=True`
- `advisory-conversation --question "000001 now buy?"`
  - parsed_symbol: `000001`
  - parsed_intent: `BUY_REVIEW`
  - status: `READY`
  - advisory_action: `DEMO_ONLY`
  - `llm_api_called=False`
  - `external_api_called=False`
  - `no_message_sent=True`
- `advisory-conversation` with no six-digit symbol
  - status: `PARSE_FAILED`
  - parsed_symbol: empty
  - advisory_action: `NO_ACTION`
  - no symbol or recommendation invented

## Safety Guarantees

- `REVIEW_BUY_CANDIDATE` is not an order.
- Demo rows must stay `DEMO_ONLY`; high-score demo rows do not become buy/sell review guidance.
- `NOT_FOUND` does not invent recommendations.
- `PARSE_FAILED` does not invent symbols or recommendations.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real message delivery was implemented.
- No LLM/API calls were implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains required.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- Non-demo review labels remain structural only.
- Strategy quality is not validated by this milestone.
- Quality gates only apply when quality status is present in row/metadata.
- `signal-advisory` and `single-symbol-advisory` use semantics in-process, but they do not automatically emit standalone `signal-semantics` artifacts as side effects.
- No real alert delivery channel exists.
- No automation exists.
- No international market support exists.

## Recommended Next Engineering Tasks

1. Add advisory artifact health checks that explicitly verify generated signal and single-symbol artifacts declare the shared semantics-policy source.
2. Add release/status observability for semantics-policy version in downstream advisory metadata if useful.
3. Expand non-demo semantics only after strategy validation, calibration/backtesting evidence, and quality-gate hardening.
4. Keep delivery channels, automation, broker integration, and live trading out of scope until separately reviewed and checkpointed.
5. Create a release tag `v0.90.0` only after user review, git safety checks, and the normal checkpoint process.
