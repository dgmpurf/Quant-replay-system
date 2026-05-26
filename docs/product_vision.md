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
- manual review identity and reason,
- paper or execution-state transition,
- safety flags and no-auto-order status.

## Later-Stage Automation

Full automation is a later-stage optional capability. It should not be added until the advisory, review, risk, fill reconciliation, and audit layers are mature and separately reviewed.

Any future automation must remain gated by explicit configuration, safety tests, and a clear operational review process.

## Later-Stage Market Expansion

International market expansion is also later-stage work. The current data contracts, cache policy, and quality gates are built around the local China A-share research workflow. New markets should be added through explicit source policy, schema, calendar, symbol, and quality-gate reviews.

## Future Single-Symbol Review

A future advisory feature may let the user input a single symbol and ask whether to buy, sell, hold, watch, or ignore it.

That feature should return:

- advisory action,
- reasons and score context,
- data-quality and source caveats,
- timing and validity,
- invalidation conditions,
- risk notes,
- manual confirmation requirement.

It should still avoid automatic orders and should not present demo or unvalidated signals as strategy recommendations.
