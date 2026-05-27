# Release Checkpoint v0.88.0: Signal Advisory Semantics Policy

## Milestone Name

Signal Advisory Semantics Policy v0.1.

Recommended tag: `v0.88.0`

## Completed Capabilities

- Added a deterministic signal semantics layer for local candidate/scored rows.
- Added explicit advisory action labels:
  - `DEMO_ONLY`
  - `WATCH`
  - `REVIEW_BUY_CANDIDATE`
  - `REVIEW_SELL_CANDIDATE`
  - `HOLD_REVIEW`
  - `NO_ACTION`
  - `BLOCKED`
- Forced demo rows to `DEMO_ONLY`.
- Prevented demo rows from becoming `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE`.
- Preserved conservative `NO_TRADE` behavior.
- Preserved leading-zero symbols such as `000001`.
- Blocked risk-blocked rows.
- Blocked missing-symbol rows or recorded explicit issues.
- Blocked `data_quality_status=FAIL`.
- Blocked `snapshot_quality_status=FAIL`.
- Allowed a synthetic non-demo high-score row to become `REVIEW_BUY_CANDIDATE`.
- Allowed a synthetic moderate non-demo row to become `WATCH`.
- Preserved safety fields:
  - `requires_manual_confirmation=true`
  - `auto_order_allowed=false`
  - `no_live_trading=true`
  - `no_broker_api=true`
  - `no_message_sent=true`

## Workflow Impact

The semantics policy gives the advisory product layer a deterministic, auditable bridge from quantitative artifacts to user-facing advisory labels:

```text
current-candidates / scored dataset
-> signal-semantics
-> advisory action labels
-> signal-advisory / single-symbol advisory / human review
```

`REVIEW_BUY_CANDIDATE` is a human-review candidate label. It is not an order, a buy instruction, a paper approval, a broker instruction, or automated execution guidance.

Demo rows must never produce real buy/sell guidance. A demo row can validate local workflow behavior, but it remains `DEMO_ONLY` and not a strategy recommendation.

Data-quality, snapshot-quality, and risk precheck remain gates. A high score does not override failed data quality, failed snapshot quality, missing symbols, or risk blocks.

## Validation Baseline

- Backend tests: `1130 passed, 2 warnings`
- Quick tests: `1021 passed, 109 deselected, 2 warnings`

Latest dry-run:

- Demo candidates run: `79fb4e67da29`
  - rows: `9`
  - `DEMO_ONLY=9`
  - `REVIEW_BUY_CANDIDATE=0`
  - `REVIEW_SELL_CANDIDATE=0`
- Synthetic non-demo run: `2a81d8a065bd`
  - rows: `4`
  - `REVIEW_BUY_CANDIDATE=1`
  - `WATCH=1`
  - `BLOCKED=2`
  - issues: `RISK_BLOCKED`, `MISSING_SYMBOL`

## Safety Guarantees

- No live trading was implemented.
- No broker integration was implemented.
- No automated order placement was implemented.
- No `APPROVED_FOR_PAPER` was applied.
- No real message sending was implemented.
- No LLM/API calls were added.
- No scheduler, cron, or GitHub Actions automation was added.
- Demo artifacts are not strategy recommendations.
- Advisory labels are not orders.
- Manual confirmation remains required.
- Auto-order remains disabled.
- Generated outputs remain local ignored artifacts and must not be committed.

## Known Limitations

- Non-demo labels are structural semantics only, not validated trading recommendations.
- `REVIEW_BUY_CANDIDATE` and `REVIEW_SELL_CANDIDATE` still require future strategy validation before any stronger meaning is attached.
- Sell and hold semantics are explicit-source labels only in v0.1; they are not inferred from market behavior.
- The semantics command consumes quality statuses when present or supplied, but does not run `data-quality` or `snapshot-quality` itself.
- Artifact index, health, and status views for `signal_semantics` are not yet implemented.
- `research-status` integration for semantics artifacts is not yet implemented.
- No alert delivery, broker integration, automation, or international market support is included.

## Recommended Next Engineering Tasks

1. Add Signal Semantics Artifact Index / Health / Status v0.1.
2. Integrate signal semantics status into unified `research-status` as advisory-policy context.
3. Wire signal semantics into `signal-advisory` and `single-symbol-advisory` as the shared classification policy.
4. Add explicit non-demo strategy validation gates before expanding reviewed buy/sell semantics.
5. Keep checkpoint documentation before any future delivery channel, LLM integration, broker integration, or automation work.
