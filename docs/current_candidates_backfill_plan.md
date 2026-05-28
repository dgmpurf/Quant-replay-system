# Multi-date Current-Candidates Backfill Plan v0.1

`current-candidates-backfill-plan` creates a local plan for earlier-date current-candidates generation from existing market-cache coverage.

It is a planning artifact only. It does not run `current-candidates`, run `data-pipeline`, fetch data, mutate cache files, send messages, connect to brokers, or place orders.

## Purpose

The planner answers:

```text
Given the local market cache, which signal dates are feasible for later current-candidates generation and future forward-return labels?
```

The intended workflow is:

```text
local market cache
-> current-candidates-backfill-plan
-> reviewed signal-date plan
-> current-candidates-backfill-execution-manifest
-> later current-candidates generation
-> later forward-return label dataset
-> calibration evidence
```

The command deliberately stops at the plan. Candidate generation and outcome labeling remain separate reviewed steps.

## CLI Usage

```cmd
python -m quant_replay_system.cli current-candidates-backfill-plan --cache-path data\cache\market\daily_bars.csv --start-date 2024-01-02 --end-date 2024-05-20 --universe etf_core --selection-profile demo --horizons 1,3,5,10 --warmup-trading-days 60 --max-dates 8
```

Optional controls:

- `--min-symbol-coverage`: minimum distinct symbol count required on a signal date.
- `--warmup-trading-days`: required trading-day indicator warmup coverage through each planned signal date. The default is `60`.
- `--source-policy`: source-policy label to record in the plan.
- `--output-dir`: destination root for plan artifacts.

## Selection Logic

The planner reads the local market cache with symbols preserved as strings. Leading-zero symbols such as `000001` remain intact.

Candidate signal dates are selected only when:

- the date is inside the requested cache range,
- the date has at least the requested minimum distinct symbol coverage,
- enough historical trading dates exist through the signal date for indicator warmup,
- enough future trading dates exist for the maximum requested horizon,
- duplicate `symbol` + `trade_date` source rows do not inflate the symbol coverage count.

For example, with `--warmup-trading-days 60` and a 10-trading-day forward horizon, a cache covering `2024-01-02` through `2024-05-20` cannot use early January 2024 dates for candidate generation. Those dates have future labels available, but they do not have enough historical bars for indicator warmup. The first feasible date moves to the first date with the requested warmup window, while the latest feasible date remains constrained by the maximum forward horizon.

The plan marks horizon feasibility for:

- `forward_1d_available`
- `forward_3d_available`
- `forward_5d_available`
- `forward_10d_available`

`latest_required_forward_date` records the latest cache trading date needed for the requested maximum horizon.

## Source Guidance

Market cache rows can contain duplicate `symbol` + `trade_date` entries from multiple source/upstream routes. The plan records reviewed guidance for later execution, but does not filter or rewrite cache rows.

The v0.1 default guidance is:

- `source_policy=reviewed_local_v0`
- `recommended_source_filter=AKSHARE_OPTIONAL`
- `recommended_upstream_filter=TENCENT_FOR_STOCKS;SINA_FOR_ETFS`

BaoStock-style rows can remain useful for comparison, but later generation should use an explicit reviewed source policy before producing calibration evidence.

## Artifacts

Artifacts are written under:

```text
outputs/reports/current_candidates_backfill_plan/<plan_id>/
```

Files:

- `current_candidates_backfill_plan.csv`
- `current_candidates_backfill_plan_report.md`
- `metadata.json`

The CSV includes:

- `plan_id`
- `signal_date`
- `universe`
- `selection_profile`
- `eligible_symbol_count`
- `total_symbol_count`
- `min_required_symbol_count`
- `max_forward_horizon`
- `warmup_trading_days`
- `warmup_available`
- `earliest_required_warmup_date`
- `first_available_market_date`
- `warmup_start_date`
- `warmup_reason`
- `forward_1d_available`
- `forward_3d_available`
- `forward_5d_available`
- `forward_10d_available`
- `latest_required_forward_date`
- `cache_start_date`
- `cache_end_date`
- `source_policy`
- `recommended_source_filter`
- `recommended_upstream_filter`
- `status`
- `reason`
- `candidate_generation_feasible`
- `candidate_generation_blocker`
- `no_live_trading`
- `no_broker_api`
- `no_order_placement`
- `no_message_sent`

## Index, Health, And Status

Use `current-candidates-backfill-plan-index` to discover local plan artifacts:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-plan-index
```

The index scans `outputs/reports/current_candidates_backfill_plan/` and writes:

```text
outputs/reports/current_candidates_backfill_plan/index/
  current_candidates_backfill_plan_index.csv
  current_candidates_backfill_plan_index_report.md
  metadata.json
```

Index rows include plan id, status, universe, selection profile, selected date count, first/last signal dates, cache range, whether the artifact is `warmup_aware`, warmup and forward-horizon availability counts, source/upstream guidance, safety flags, and artifact paths.

Use `current-candidates-backfill-plan-health` to check plan artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-plan-health
```

Health checks verify:

- `metadata.json` is readable,
- `current_candidates_backfill_plan.csv` exists and has the required columns,
- `current_candidates_backfill_plan_report.md` exists,
- selected rows have `warmup_available=true`,
- selected rows have the requested forward horizons available,
- leading-zero symbols remain six-digit strings when symbol-level fields are present,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_order_placement=true`,
- `no_message_sent=true`,
- metadata remains plan-only and does not indicate candidate generation, data-pipeline execution, cache mutation, messages, broker access, or live trading.

Older plan artifacts that predate explicit warmup columns remain visible as audit context and can be reported as `STALE_OR_PARTIAL_PLAN` warnings. Health summaries distinguish active warmup-aware plan issues from legacy context with fields such as `legacy_plan_count`, `stale_plan_warning_count`, `active_plan_issue_count`, `active_plan_error_count`, `legacy_missing_warmup_count`, and `latest_plan_is_warmup_aware`.

Use `current-candidates-backfill-plan-status` to summarize the latest plan:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-plan-status
```

Expected stages include:

- `NO_CURRENT_CANDIDATES_BACKFILL_PLAN`
- `CURRENT_CANDIDATES_BACKFILL_PLAN_READY`
- `CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH_WARN`
- `CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED`

Status output is planning context only. The active status is based on the latest warmup-aware plan when one exists, so older pre-warmup legacy warnings do not by themselves turn the active plan into `CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH_WARN`. It does not run `current-candidates`, compute forward labels, mutate cache, send messages, connect to brokers, or place orders.

## Research-Status Integration

`research-status` includes the latest `current-candidates-backfill-plan-status` as planning context only.

The unified dashboard exports:

- latest plan id,
- status and workflow stage,
- health status,
- selected date count,
- first and last selected signal dates,
- warmup trading-day requirement,
- forward-horizon availability summary,
- active versus legacy plan issue counts,
- whether the latest active plan is warmup-aware,
- report path,
- next manual action.

`CURRENT_CANDIDATES_BACKFILL_PLAN_READY` is visible but non-blocking. Legacy pre-warmup warnings remain reviewable audit context, but the active plan status follows the latest warmup-aware plan. Active health failures are actionable only when the backfill plan is the active stage. Later generated current-candidates, advisory artifacts, market-update handoff, and paper workflow stages take priority, while the plan stays visible as audit context.

The dashboard does not execute the plan. It does not generate candidates, build snapshot manifests, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

## Execution Manifest

After a warmup-aware plan is reviewed, use `current-candidates-backfill-execution-manifest` to check which planned signal dates already have the local snapshot inputs needed for a future execution step:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest --plan outputs\reports\current_candidates_backfill_plan\aadd86db24a1\current_candidates_backfill_plan.csv
```

The execution manifest checks existing snapshot manifests, snapshot-quality status, market/universe/trading-calendar paths, and whether the universe `as_of_date` is point-in-time valid for each signal date. It is still manifest-only: it does not run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward returns, mutate cache, send messages, connect to brokers, or place orders.

Use `current-candidates-backfill-execution-manifest-index`, `current-candidates-backfill-execution-manifest-health`, and `current-candidates-backfill-execution-manifest-status` to discover, safety-check, and summarize execution readiness artifacts before any reviewed generation step.

See [current_candidates_backfill_execution_manifest.md](current_candidates_backfill_execution_manifest.md).

## Safety Boundaries

The planner always records:

- `current_candidates_executed=false`
- `data_pipeline_executed=false`
- `cache_mutated=false`
- `network_api_called=false`
- `external_api_called=false`
- `llm_api_called=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`

The output is not a trading recommendation, not a paper approval, and not strategy-performance validation.

## Known Limitations

- The planner does not build snapshot manifests.
- The planner does not run snapshot-quality or data-quality gates.
- The planner does not generate current-candidates artifacts.
- The planner does not compute forward returns.
- Source/upstream guidance is recorded for review but not applied as a cache rewrite.
- The current cache may be too small for robust calibration evidence.
