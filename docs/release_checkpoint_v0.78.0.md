# Release Checkpoint v0.78.0

## Milestone

Signal Advisory Contract and Alert Preview.

Recommended tag: `v0.78.0`

## Completed Capabilities

- Added the `signal-advisory` module and CLI command.
- Defined a signal advisory contract between current-candidates and any human or execution-like action.
- Added advisory signal schema fields for identity, source candidate linkage, actionability, score context, timing, invalidation, risk notes, data-source notes, and safety flags.
- Generated local `signals.csv`, `signal_advisory_report.md`, `signal_alert_preview.md`, and `metadata.json` artifacts.
- Classified demo current-candidate inputs as `DEMO_ONLY`, not buy or sell recommendations.
- Preserved leading-zero symbols such as `000001`.
- Required manual confirmation on every signal.
- Recorded safety fields including `no_live_trading=true`, `no_broker_api=true`, and `auto_order_allowed=false`.
- Rendered local alert preview markdown without sending messages.

Latest local dry-run:

- source current-candidates run: `f484cd4648`
- signal_run_id: `2921a18906bf`
- signal_count: `9`
- advisory action counts: `DEMO_ONLY=9`
- `000001` preserved as `000001`

## Product Vision Alignment

This milestone shifts the project beyond pure replay and paper workflow plumbing toward the near-term product goal: a reliable quantitative research, signal advisory, and human-confirmed execution assistant.

The system should be able to tell the user:

- what to watch,
- what may be buyable or sellable after review,
- why a signal exists,
- when the signal is valid,
- when it is invalidated,
- what risk or data-quality caveats apply,
- whether manual confirmation is required.

Full automation remains later-stage work. International market expansion also remains later-stage work. The near-term default is human-in-the-loop advisory review.

## Workflow Impact

The completed workflow chain is:

```text
current-candidates
-> signal-advisory
-> signals.csv
-> alert preview markdown
-> manual review / human confirmation
-> future paper workflow or alert delivery
```

`signal-advisory` creates a formal artifact boundary before future delivery or execution-assistant work. It gives downstream components a local, reproducible signal contract without changing paper review status, sending messages, or creating orders.

## Validation Baseline

- Backend tests: `1018 passed, 2 warnings`
- Quick tests: `909 passed, 109 deselected, 2 warnings`

The warnings are the existing pandas date-format inference warnings in data ingestion/factor dataset tests.

## Safety Guarantees

- A signal is not an order.
- Demo signals are not strategy recommendations.
- No automatic buy or sell execution is implemented.
- No broker API is implemented or invoked.
- No live trading is implemented or invoked.
- No real SMS, email, Telegram, WeChat, webhook, or broker message delivery is implemented.
- Manual confirmation is required.
- `auto_order_allowed=false` by default.
- `no_live_trading=true` and `no_broker_api=true` are recorded in signal artifacts.
- Generated `data/cache`, `data/raw`, `data/processed`, and `outputs` artifacts are ignored and must not be committed.

## Known Limitations

- Current advisory output is local artifact only.
- Alert preview is markdown only.
- No delivery channel is implemented.
- No single-symbol advisory review exists yet.
- Demo candidates produce `DEMO_ONLY` only.
- Non-demo advisory semantics still require future strategy validation.
- No automated execution exists.
- No international market support exists yet.

## Recommended Next Engineering Tasks

1. Add `signal-advisory-index`, `signal-advisory-health`, and `signal-advisory-status` artifact views.
2. Integrate signal advisory context into `research-status`.
3. Add a single-symbol advisory review command that reads existing local snapshots/signals and returns watch/buy/sell/hold review context with risks and invalidation.
4. Add explicit alert-delivery design documentation before implementing any real channel.
5. Keep future delivery work local-preview-first, with no message sending until reviewed and explicitly enabled.
