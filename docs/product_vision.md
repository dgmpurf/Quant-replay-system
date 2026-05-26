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

## Human Confirmation

Manual confirmation remains the default boundary before any execution-like action. The current project supports local research, reviewed cache export, current-candidates, signal advisory, WATCH_ONLY paper workflow, and diagnostic paper reconciliation without live trading or broker integration.

Future human-confirmed execution assistance should preserve auditability:

- source data and snapshot paths,
- scoring and candidate context,
- signal contract fields,
- signal index, health, and status evidence,
- unified `research-status` context for signal advisory, alert-preview, and later paper workflow priority,
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

Future versions may add conversational natural-language review, richer risk context, and human-approved alert delivery while preserving the same safety boundary.
