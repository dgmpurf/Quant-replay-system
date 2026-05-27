# Release Checkpoint v0.89.0: Signal Semantics Research Status Integration

## Milestone Name

Signal Semantics Research Status Integration v0.1.

Recommended tag: `v0.89.0`

## Completed Capabilities

- Added deterministic Signal Advisory Semantics Policy in v0.1.
- Added `signal-semantics-index`, `signal-semantics-health`, and `signal-semantics-status`.
- Integrated `signal-semantics-status` into unified `research-status`.
- Exposed latest signal semantics run id in `research-status`.
- Exposed signal semantics action counts in `research-status`:
  - `DEMO_ONLY`
  - `WATCH`
  - `REVIEW_BUY_CANDIDATE`
  - `REVIEW_SELL_CANDIDATE`
  - `HOLD_REVIEW`
  - `NO_ACTION`
  - `BLOCKED`
- Exposed signal semantics health status, workflow stage, profile, input path, report path, and next action.
- Kept `REVIEW_BUY_CANDIDATE` as a human-review-only label.
- Preserved demo rows as `DEMO_ONLY`; demo rows do not become real buy/sell guidance.
- Kept `BLOCKED` rows visible for review and audit.
- Preserved later paper workflow priority in the final `research-status` stage.
- Preserved no-auto-order, no-broker, and no-live-trading boundaries.

## Workflow Impact

Signal semantics is now observable in the unified dashboard as advisory-policy context:

```text
current-candidates / scored rows
-> signal-semantics
-> signal-semantics-index / health / status
-> research-status
-> signal-advisory / single-symbol advisory / paper workflow as later stages
```

The dashboard can now show whether scored rows were mapped into advisory labels safely, whether health checks passed, and whether any review labels need manual attention before downstream advisory use.

If `signal-semantics-status` reports `DEMO_SIGNAL_SEMANTICS_VALIDATED`, `research-status` treats demo semantics as expected demo context. If it reports `SIGNAL_SEMANTICS_READY_FOR_REVIEW`, `research-status` treats `REVIEW_BUY_CANDIDATE`, `WATCH`, and `BLOCKED` counts as manual review context.

Later workflow artifacts still take priority. A valid paper workflow can remain the final `workflow_stage` while signal semantics fields stay visible as audit context.

## Validation Baseline

- Backend tests: `1148 passed, 2 warnings`
- Quick tests: `1039 passed, 109 deselected, 2 warnings`

Latest local dry-run:

- `signal-semantics-status`
  - status: `WARN`
  - stage: `SIGNAL_SEMANTICS_READY_FOR_REVIEW`
  - latest_semantics_run_id: `2a81d8a065bd`
  - health_status: `PASS`
  - row_count: `4`
  - `REVIEW_BUY_CANDIDATE=1`
  - `WATCH=1`
  - `BLOCKED=2`
  - next action: review labels manually; `REVIEW_BUY_CANDIDATE` is not an order and auto-order remains disabled.
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - latest_signal_semantics_run_id: `2a81d8a065bd`
  - `REVIEW_BUY_CANDIDATE=1`
  - `WATCH=1`
  - `BLOCKED=2`
  - health_status: `PASS`
  - later paper workflow priority preserved
  - next_manual_action stayed on the WATCH_ONLY paper workflow path.

## Safety Guarantees

- `REVIEW_BUY_CANDIDATE` is not an order.
- `WATCH` is not an order.
- `BLOCKED` remains visible and does not get hidden by scores.
- Demo rows must remain `DEMO_ONLY`.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real message delivery was implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains the default and required safety posture.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- Non-demo review labels are structural only.
- Strategy quality is not validated by this milestone.
- Sell and hold labels are explicit-source only in v0.1.
- `signal-semantics` consumes quality status when present or provided, but it does not run `data-quality` or `snapshot-quality` itself.
- `research-status` integration is observability, not trading approval.
- Broader semantics calibration and backtesting remain future work.

## Recommended Next Engineering Tasks

1. Wire signal semantics into `signal-advisory` and `single-symbol-advisory` as the shared classification policy.
2. Add regression coverage for semantics-fed advisory artifacts once the shared policy is wired downstream.
3. Expand non-demo semantics only behind explicit strategy validation, quality gates, and manual-confirmation rules.
4. Add calibration/backtesting evidence before strengthening any reviewed buy/sell semantics.
5. Keep checkpoint documentation before any delivery channel, automation, broker integration, or live-trading work.
