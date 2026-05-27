# Product Vision

`quant-replay-system` is a quantitative research and signal advisory system first.

The near-term product goal is not a fully automated trading bot. The default path is human-in-the-loop:

```text
local data -> research artifacts -> advisory signals -> human confirmation -> reviewed paper workflow
```

## Near-Term Goal

The system should help a user understand:

- what to watch,
- what may be buyable or sellable after review,
- why a signal exists,
- when the signal is valid,
- when the signal is invalidated,
- what risk, source, and data-quality caveats apply,
- whether manual confirmation is required.

Signals are advisory artifacts. They are not orders, approvals, or broker instructions.

The signal advisory semantics policy is the deterministic bridge between quantitative rows and user-facing advisory labels. It defines when a row is `DEMO_ONLY`, `WATCH`, `REVIEW_BUY_CANDIDATE`, `REVIEW_SELL_CANDIDATE`, `HOLD_REVIEW`, `NO_ACTION`, or `BLOCKED`. Those labels remain human-review states, not trading instructions, and demo artifacts must stay workflow validation only.

## Human Confirmation

Manual confirmation remains the default boundary before any execution-like action. The current project supports local research, reviewed cache export, current-candidates, signal advisory, WATCH_ONLY paper workflow, and diagnostic paper reconciliation without live trading or broker integration.

Future human-confirmed execution assistance should preserve auditability:

- source data and snapshot paths,
- scoring and candidate context,
- signal contract fields,
- signal index, health, and status evidence,
- unified `research-status` context for signal advisory, single-symbol review, alert-preview, and later paper workflow priority,
- manual review identity and reason,
- paper or execution-state transition,
- safety flags and no-auto-order status.

## Later-Stage Automation

Full automation is a later-stage optional capability. It should not be added until the advisory, review, risk, fill reconciliation, and audit layers are mature and separately reviewed.

Any future automation must remain gated by explicit configuration, safety tests, and a clear operational review process.

## Later-Stage Market Expansion

International market expansion is also later-stage work. The current data contracts, cache policy, and quality gates are built around the local China A-share research workflow. New markets should be added through explicit source policy, schema, calendar, symbol, and quality-gate reviews.

## Single-Symbol Review

The single-symbol advisory workflow lets the user input one symbol and ask whether to buy, sell, hold, watch, or ignore it using existing local artifacts.

That feature should return:

- advisory action,
- reasons and score context,
- data-quality and source caveats,
- timing and validity,
- invalidation conditions,
- risk notes,
- manual confirmation requirement.

The v0.1 implementation is local artifact only. It does not fetch data, send messages, approve paper trades, or connect to brokers. Demo or unvalidated signals are not presented as strategy recommendations, and every output keeps manual confirmation and no-auto-order safety fields.

Single-symbol advisory index, health, and status views make repeated one-symbol reviews discoverable and safety-checkable before any future delivery or automation layer. Unified `research-status` includes the latest one-symbol context while preserving later paper workflow priority. This helps preserve the distinction between a review artifact, a missing-symbol result, and executable guidance.

Question-style single-symbol answers provide an intermediate local rendering layer: they turn existing advisory artifacts into a plain answer with reasons, risk notes, timing, invalidation, and safety boundaries. The v0.1 implementation is deterministic and does not call an LLM, send messages, or create execution instructions.

Question-style answer index, health, and status views make repeated local answers discoverable and safety-checkable. Unified `research-status` includes the latest answer context, including safe `NOT_FOUND` outcomes and demo-only disclaimers, while preserving later paper workflow priority.

The local-only conversational advisory facade adds a deterministic routing layer for simple Chinese/English questions. It extracts a symbol and intent, then calls the existing single-symbol advisory answer workflow. This is not an LLM system, does not fetch data, does not send messages, and does not change trading state.

Advisory conversation index, health, and status views make repeated user-style questions discoverable and safety-checkable. They verify deterministic parser outputs, safe `PARSE_FAILED` and `NOT_FOUND` behavior, linked answer artifacts, no LLM/API calls, no message sending, no broker access, and no auto-order. Unified `research-status` includes the latest conversation context while preserving later paper workflow priority, so a parse failure remains audit evidence rather than a trading recommendation or workflow regression.

Question-style answer index, health, and status views make repeated answer artifacts discoverable and safety-checkable. They verify local-only boundaries such as no LLM/API calls, no message sending, no auto-order, and safe `NOT_FOUND` behavior before any future conversational or delivery layer is considered.

Future versions may add conversational natural-language review, richer risk context, and human-approved alert delivery while preserving the same safety boundary.
