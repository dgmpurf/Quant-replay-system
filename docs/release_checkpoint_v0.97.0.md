# Release Checkpoint v0.97.0: Multi-date Current-Candidates Backfill Plan And Dashboard Context

## Milestone Name

Multi-date Current-Candidates Backfill Plan, Artifact Views, Warmup Hardening, and Research-Status Integration.

Recommended tag: `v0.97.0`

## Completed Capabilities

- Added a local plan-only command: `current-candidates-backfill-plan`.
- Reads existing local market cache coverage without mutating the cache.
- Preserves symbol values as strings, including leading-zero symbols such as `000001`.
- Selects candidate signal dates inside a requested date range.
- Requires distinct symbol coverage without inflating counts from duplicate source/upstream rows.
- Enforces explicit indicator warmup feasibility with `--warmup-trading-days`, defaulting to `60`.
- Requires enough future trading dates for requested forward horizons before selecting a signal date.
- Marks forward-horizon feasibility for 1, 3, 5, and 10 trading-day horizons.
- Records reviewed local source/upstream guidance for later candidate generation.
- Added `current-candidates-backfill-plan-index`, `current-candidates-backfill-plan-health`, and `current-candidates-backfill-plan-status`.
- Integrated latest backfill plan status into unified `research-status` as planning context only.
- Hardened legacy/stale plan actionability: pre-warmup artifacts remain visible, while active status follows the latest warmup-aware plan.
- Preserves later paper workflow priority; a plan does not imply candidates were generated.

## Workflow Impact

The multi-date evidence workflow now has a reviewed planning step:

```text
local market cache
-> current-candidates-backfill-plan
-> current-candidates-backfill-plan-index / health / status
-> research-status planning context
-> future reviewed current-candidates generation
-> future forward-return label dataset
-> advisory profile calibration evidence
-> calibration-to-signal-semantics proposal review
```

Latest local plan status:

- latest_plan_id: `aadd86db24a1`
- status: `PASS`
- workflow_stage: `CURRENT_CANDIDATES_BACKFILL_PLAN_READY`
- health_status: `PASS`
- overall_health_status: `WARN`
- selected_date_count: `8`
- first_signal_date: `2024-04-02`
- last_signal_date: `2024-05-06`
- warmup_trading_days: `60`
- warmup_feasible_count: `8`
- forward_1d_available_count: `8`
- forward_3d_available_count: `8`
- forward_5d_available_count: `8`
- forward_10d_available_count: `8`
- legacy_plan_count: `1`
- legacy_missing_warmup_count: `1`
- active_plan_issue_count: `0`
- active_plan_error_count: `0`
- latest_plan_is_warmup_aware: `True`

The standalone health view still reports overall `WARN` because an older legacy plan artifact predates explicit warmup columns. The active status view distinguishes that stale context from the latest warmup-hardened plan, which is selected as the active plan and reports `PASS`.

Latest `research-status` dry-run:

- status: `WARN`
- final workflow_stage: `PAPER_WORKFLOW_READY`
- latest_current_candidates_backfill_plan_id: `aadd86db24a1`
- current_candidates_backfill_plan_stage: `CURRENT_CANDIDATES_BACKFILL_PLAN_READY`
- current_candidates_backfill_plan_health_status: `PASS`
- current_candidates_backfill_plan_selected_date_count: `8`
- current_candidates_backfill_plan_legacy_plan_count: `1`
- current_candidates_backfill_plan_active_plan_issue_count: `0`
- current_candidates_backfill_plan_latest_plan_is_warmup_aware: `True`
- later paper workflow priority preserved
- next_manual_action stayed on the WATCH_ONLY paper workflow path

## Validation Baseline

Full backend tests:

```text
1237 passed, 2 warnings
```

Quick tests:

```text
1128 passed, 109 deselected, 2 warnings
```

Focused dashboard tests include research-status visibility, non-blocking ready state, actionable health failure, paper workflow priority preservation, CSV/metadata export, and CLI field printing for current-candidates backfill plan status.

## Safety Guarantees

- Plan output is not strategy validation.
- Plan output is not a trading recommendation.
- Plan output does not generate current-candidates artifacts.
- Plan output does not build snapshot manifests.
- Plan output does not compute forward returns.
- Plan output does not run `data-pipeline`.
- Plan output does not mutate market cache.
- `research-status` reads plan status as planning context only.
- No external data fetch was implemented.
- No LLM/API calls were implemented.
- No real SMS/email/Telegram/WeChat delivery was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No automatic BUY/SELL execution was implemented.
- No order placement was implemented.
- No `APPROVED_FOR_PAPER` behavior was applied.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- The planner does not build snapshot manifests.
- The planner does not run snapshot-quality or data-quality gates.
- The planner does not generate current-candidates artifacts.
- The planner does not compute forward-return labels.
- Source/upstream guidance is recorded for manual review but is not applied as a cache rewrite.
- Current local cache coverage is limited to 9 symbols and one historical range.
- Older plan artifacts may remain as legacy health warnings until regenerated, but they no longer drive active warmup-aware plan status.
- The plan does not validate strategy performance or market edge.
- A separate reviewed implementation is still needed for multi-date candidate generation.
- A separate reviewed implementation is still needed for forward-return outcome labeling.

## Recommended Next Engineering Tasks

1. Design a reviewed multi-date current-candidates execution workflow that consumes the latest warmup-aware plan, still without cache mutation or execution behavior.
2. Optionally regenerate older legacy backfill plan artifacts if a clean overall health report is desired.
3. Add a forward-return label dataset after multi-date candidate artifacts exist.
4. Add source-policy enforcement for future plan execution so duplicate source/upstream rows do not leak into candidate generation.
5. Keep non-demo `signal_semantics` thresholds unchanged until multi-date, multi-symbol, backtest, and paper evidence are available.
6. Create release tag `v0.97.0` only after user review, git safety checks, and the normal checkpoint process.
