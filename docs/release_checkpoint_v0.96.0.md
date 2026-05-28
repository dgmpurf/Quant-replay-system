# Release Checkpoint v0.96.0: Calibration-to-Signal-Semantics Research Status Integration

## Milestone Name

Calibration-to-Signal-Semantics Research Status Integration v0.1.

Recommended tag: `v0.96.0`

Note: local tag check showed `v0.95.0` already exists, so this checkpoint uses the next available version.

## Completed Capabilities

- Added the local `calibration-to-signal-semantics` proposal report workflow.
- Added calibration-to-signal-semantics artifact observability:
  - `calibration-to-signal-semantics-index`
  - `calibration-to-signal-semantics-health`
  - `calibration-to-signal-semantics-status`
- Integrated `calibration-to-signal-semantics-status` into unified `research-status`.
- Exposed latest proposal context in research-status summary CSV, metadata, markdown report, and CLI output.
- Exposed `defaults_changed=False` so the dashboard can confirm proposal artifacts did not mutate executable defaults.
- Exposed proposal categories including:
  - `KEEP_CURRENT_DEFAULTS`
  - `CONSIDER_WATCH_EXPANSION`
  - `DO_NOT_EXPAND_BUY_REVIEW_YET`
  - `REQUIRE_MORE_EVIDENCE`
  - `NEED_MULTI_DATE_VALIDATION`
  - `NEED_MORE_SYMBOLS`
  - `NEED_BACKTEST_OR_PAPER_EVIDENCE`
- Preserved `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE` as reviewable design context, not a blocker.
- Preserved later paper workflow priority when proposal artifacts are present.
- Confirmed no `signal_semantics` defaults or config thresholds were changed.

## Workflow Impact

The proposal observability path is now:

```text
advisory-profile-calibration artifacts
-> calibration-to-signal-semantics proposal report
-> calibration-to-signal-semantics-index / health / status
-> research-status
-> human review of future signal_semantics refinement
```

`research-status` now shows whether proposal artifacts exist, whether they passed health checks, whether defaults were changed, and what conservative proposal categories are active. This helps track the bridge from calibration analysis to future `signal_semantics` refinement without changing current classification behavior.

Latest verified local proposal context:

- proposal_run_id: `ae1cfb395915`
- status: `WARN`
- stage: `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE`
- health: `PASS`
- defaults_changed: `False`
- calibration_run_count: `10`
- observed_review_buy_candidate_count: `7`
- observed_watch_count: `8`
- observed_blocked_count: `24`

Latest verified `research-status` context:

- status: `WARN`
- final workflow_stage: `PAPER_WORKFLOW_READY`
- proposal fields visible
- health: `PASS`
- defaults_changed: `False`
- next manual action stayed on the WATCH_ONLY paper workflow path
- later paper workflow priority preserved

## Validation Baseline

Full backend tests:

```text
1217 passed, 2 warnings
```

Quick tests:

```text
1108 passed, 109 deselected, 2 warnings
```

Focused verification:

```text
126 passed
```

CLI verification:

- `calibration-to-signal-semantics-status`
  - status: `WARN`
  - workflow_stage: `CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE`
  - latest_proposal_run_id: `ae1cfb395915`
  - health_status: `PASS`
  - defaults_changed: `False`
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - calibration-to-signal-semantics proposal fields visible
  - later paper workflow priority preserved

## Safety Guarantees

- Proposal output is design evidence only.
- Proposal output is not strategy validation.
- Proposal output does not approve non-demo trading.
- `defaults_changed=False` is visible and expected.
- `signal_semantics` behavior was not changed.
- Config/default thresholds were not mutated.
- `REVIEW_BUY_CANDIDATE` remains a human-review label, not an order.
- `WATCH` remains a human-review label, not an order.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real SMS/email/Telegram/WeChat delivery was implemented.
- No LLM/API calls were implemented.
- No scheduler, cron, or GitHub Actions workflow was added.
- No strategy performance claim was made.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- The proposal does not validate strategy performance.
- The proposal does not prove market edge.
- Demo artifacts remain workflow and safety validation only.
- Synthetic fixtures prove rule behavior, not profitability or robustness.
- More symbols and multi-date evidence are still needed.
- Backtest or paper evidence is still required before non-demo buy-review expansion.
- `WATCH` expansion remains a future consideration only.
- Non-demo buy-review expansion remains out of scope.
- No real alert delivery channel is implemented.
- No automation, broker integration, live trading, or international market support is implemented.

## Recommended Next Engineering Tasks

1. Review v0.96.0 artifacts and checkpoint before changing any `signal_semantics` thresholds.
2. Add a read-only multi-date calibration evidence collector before considering non-demo semantics changes.
3. Explore WATCH-only semantics refinement before expanding `REVIEW_BUY_CANDIDATE`.
4. Keep `DO_NOT_EXPAND_BUY_REVIEW_YET` as the default stance until broader symbol, multi-date, backtest, and paper evidence exist.
5. Keep delivery channels, automation, broker integration, and live trading out of scope until separately designed, reviewed, and checkpointed.
6. Create release tag `v0.96.0` only after user review, git safety checks, and normal checkpoint process.
