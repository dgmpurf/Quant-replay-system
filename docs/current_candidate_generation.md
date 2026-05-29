# Current Candidate Generation v0.1

Current Candidate Generation creates a local, auditable `candidates.csv` for an as-of date using the same point-in-time-safe factor dataset, score engine, and candidate selector used by replay.

It is a paper-trading input workflow. It does not connect to brokers, place orders, automate execution, call market data APIs, or require API tokens.

## Purpose

Historical replay answers what would have happened on an old decision date.

Current candidate generation answers:

```text
Given a local snapshot and an as-of date, which symbols pass the current research candidate rules?
```

The output is designed to feed the manual paper trading workflow:

```text
local snapshot -> current-candidates -> candidates.csv -> signal-advisory -> human review / paper workflow
```

## Relationship To Replay

The current-candidate workflow reuses the same core modules as replay:

- `build_factor_dataset(...)` for point-in-time features,
- `score_factor_dataset(...)` for explainable component scores,
- `select_candidates(...)` for ranking and thresholds,
- optional Snapshot Quality Preflight before data is consumed.

Unlike `run_replay(...)`, it does not simulate T+1 buys, exits, or future returns. It only produces candidate artifacts for review.

Universe eligibility follows the factor dataset and replay data contract. `listed_date` and `delisted_date` may be missing in vendor universe snapshots. A missing `listed_date` is treated as an unknown listing date and does not reject an otherwise active symbol by itself. Present parseable dates remain active filters: future `listed_date` values and `delisted_date` values on or before the decision date make the symbol ineligible. `available_time`, `as_of_date`, source revisions, `is_active`, ST, and suspension rules remain point-in-time safe.

Current-candidate generation requires market and universe symbols to overlap after normalization. Symbol values are treated as strings because leading zeros are significant: `000001` is not the same as `1` in source files, and ETF symbols such as `510300` / `159915` must be present in the universe snapshot when the market data is for those ETFs. If the factor dataset is empty, metadata includes coverage diagnostics such as market symbol count, universe symbol count, market/universe intersection count, a sample of missing market symbols, and universe instrument-type counts.

When a vendor universe is stock-only, use the reviewed [universe overlay workflow](universe_overlay.md) to merge ETF rows before running `data-pipeline` and `current-candidates`.

## Selection Profiles

`current-candidates` supports explicit selection profiles:

- `default`: the normal research behavior. It uses configured `min_action`, `min_final_score`, risk blocks, and candidate selection thresholds.
- `demo`: a local dry-run profile for artifact and workflow validation with tiny datasets. If no default candidates pass, it can select top scored non-blocked rows so downstream paper workflow artifacts can be tested.

The default profile remains unchanged and is the only profile intended for normal research review.

The demo profile is not a strategy recommendation. Demo candidates are marked in `candidates.csv`, report output, and metadata with:

- `selection_profile=demo`
- `demo_mode=true`
- `not_strategy_recommendation=true`
- `selection_reason=DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION` when the row did not pass default thresholds

Demo selection does not change score calculation and does not select `BLOCKED` rows.

## Multi-date Backfill Planning

Use `current-candidates-backfill-plan` when you need to review feasible historical signal dates before generating a multi-date set of current-candidates artifacts:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-plan --cache-path data\cache\market\daily_bars.csv --start-date 2024-01-02 --end-date 2024-05-20 --universe etf_core --selection-profile demo --horizons 1,3,5,10 --warmup-trading-days 60 --max-dates 8
```

The planner reads the local market cache, preserves leading-zero symbols, checks distinct symbol coverage by signal date, verifies indicator warmup coverage, and marks whether future trading dates exist for requested forward-return horizons. It records source/upstream guidance so later candidate generation can avoid duplicate `symbol` + `trade_date` rows through an explicit reviewed source policy.

This command writes plan artifacts only. It does not run `current-candidates`, run `data-pipeline`, mutate cache files, fetch data, compute forward returns, send messages, connect to brokers, or place orders. See [current_candidates_backfill_plan.md](current_candidates_backfill_plan.md).

Use `current-candidates-backfill-plan-index`, `current-candidates-backfill-plan-health`, and `current-candidates-backfill-plan-status` to discover, safety-check, and summarize those plan artifacts before any reviewed execution step.

Before executing a reviewed multi-date plan, use `current-candidates-backfill-execution-manifest` to check whether the required local snapshot manifest, snapshot-quality PASS, market dataset, universe dataset, and trading calendar already exist for each planned signal date:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest --plan outputs\reports\current_candidates_backfill_plan\aadd86db24a1\current_candidates_backfill_plan.csv
```

The manifest can mark rows as `READY_FOR_REVIEW` or blocked by missing snapshot inputs, snapshot-quality status, plan infeasibility, missing datasets, or universe `as_of_date` being later than the signal date. It does not run `current-candidates`, build snapshots, compute forward returns, mutate cache, send messages, connect to brokers, or place orders. See [current_candidates_backfill_execution_manifest.md](current_candidates_backfill_execution_manifest.md).

If execution is blocked by `BLOCKED_UNIVERSE_AS_OF`, use `pit-universe-overlay-plan` to produce a manual review template for point-in-time universe overlays:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-plan --execution-manifest outputs\reports\current_candidates_backfill_execution_manifest\f98279630ce6\current_candidates_backfill_execution_manifest.csv --universe-name etf_core
```

Generated rows default to `NEEDS_MANUAL_REVIEW`, `valid_for_signal_date=false`, and survivorship-bias warnings when derived from a later universe artifact. The command is template-only and does not approve the universe, build snapshots, run current-candidates, or compute labels. See [point_in_time_universe_overlay_plan.md](point_in_time_universe_overlay_plan.md).

## Signal Semantics Policy

Use `signal-semantics` when a current-candidates or scored artifact needs an explicit advisory label mapping before signal or one-symbol review:

```cmd
python -m quant_replay_system.cli signal-semantics --input outputs\reports\current_candidates\example\candidates.csv --input-type candidates --profile demo
```

The policy is deterministic and conservative. It blocks failed risk/data/snapshot rows, preserves leading-zero symbols, and forces demo/not-strategy rows to `DEMO_ONLY`. Non-demo labels such as `REVIEW_BUY_CANDIDATE` are human-review labels only; they do not approve paper trades, send messages, or place orders.

Use `advisory-profile-calibration` when testing proposed non-demo threshold profiles against local candidates or scored rows:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration --input outputs\reports\current_candidates\example\candidates.csv --input-type candidates --profile balanced --data-quality-status PASS --snapshot-quality-status PASS
```

The calibration analyzer writes simulated labels for threshold review only. It does not alter current-candidates artifacts, approve paper trades, send messages, or place orders.

## Signal Advisory Handoff

Use `signal-advisory` when a current-candidates artifact should be converted into local advisory signals and alert preview text before any human action:

```cmd
python -m quant_replay_system.cli signal-advisory --candidates outputs\reports\current_candidates\example\candidates.csv --alert-preview
```

The advisory output is local-only. It writes `signals.csv`, `signal_alert_preview.md`, `signal_advisory_report.md`, and `metadata.json` under `outputs/reports/signals/<signal_run_id>/`.

Signals are not orders and do not approve paper trades. Demo candidates remain `DEMO_ONLY` workflow validation artifacts, keep `not_strategy_recommendation=true`, require manual confirmation, and set `auto_order_allowed=false`.

For a focused review of one symbol from a generated `candidates.csv`, use `single-symbol-advisory`:

```cmd
python -m quant_replay_system.cli single-symbol-advisory --symbol 000001 --candidates outputs\reports\current_candidates\example\candidates.csv --alert-preview
```

The single-symbol advisory report uses local artifacts only, preserves leading-zero symbols, returns `NOT_FOUND` instead of inventing recommendations, and keeps demo output as workflow validation rather than strategy advice.

## Snapshot Quality Preflight

If `snapshot_manifest_path` is supplied, snapshot preflight runs by default according to current-candidate settings:

```yaml
current_candidates:
  enable_snapshot_quality_preflight: true
```

Preflight behavior follows the shared snapshot preflight rules:

- `PASS`: continue.
- `WARN`: continue by default and record warnings unless configured to block.
- `FAIL`: block by default when `block_on_fail: true`.

The result metadata records:

- `snapshot_quality_preflight_enabled`
- `snapshot_quality_status`
- `snapshot_quality_report_path`
- `snapshot_quality_gate_id`
- `snapshot_quality_warnings`

## Artifacts

Artifacts are written under:

```text
outputs/reports/current_candidates/<decision_date>_<universe_name>_<run_id>/
```

Files:

- `current_candidates_report.md`
- `factor_dataset.csv`
- `scored_dataset.csv`
- `candidates.csv`
- `metadata.json`

The `run_id` is deterministic from:

- decision date,
- universe name,
- `top_n`,
- config version,
- snapshot manifest path when provided.

## candidates.csv Schema

The candidate export includes:

- `rank`
- `symbol`
- `name`
- `final_score`
- `action`
- `technical_score`
- `liquidity_score`
- `expectation_score`
- `reality_score`
- `sentiment_score`
- `risk_penalty`
- `risk_precheck_status`
- `risk_precheck_reason`
- `score_reason`
- `score_breakdown`
- `selection_profile`
- `demo_mode`
- `not_strategy_recommendation`
- `selection_reason`
- `current_candidate_run_id`
- `source_run_id`
- `source_report_path`

`source_run_id` and `source_report_path` make the file compatible with the paper trading review and daily paper runner workflows.

## CLI Usage

Generate current candidates from configured mock/local data:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5
```

Generate current candidates from a snapshot manifest and run preflight:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data\snapshots\example_snapshot_manifest.json
```

Allow snapshot warnings:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data\snapshots\example_snapshot_manifest.json --allow-warn
```

Disable snapshot preflight explicitly:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --snapshot-manifest data\snapshots\example_snapshot_manifest.json --disable-snapshot-preflight
```

Run a local demo profile for tiny workflow smoke tests:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest data\snapshots\example_snapshot_manifest.json --selection-profile demo
```

For reviewed offline market update batches, `market-update-handoff` can generate the snapshot manifest and invoke the same demo validation chain:

```cmd
python -m quant_replay_system.cli market-update-handoff --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --selection-profile demo --dry-run
```

The CLI prints the candidate count, `candidates.csv` path, report path, snapshot quality status when applicable, and:

```text
No live trading or broker API was invoked.
```

## Paper Trading Workflow

Use the generated `candidates.csv` to start the manual workflow:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --candidates outputs\reports\current_candidates\...\candidates.csv
```

Then apply manual review decisions:

```cmd
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\...\decisions.csv --updates data\paper\review_updates.csv --reviewer-id msj
```

Then run daily paper reporting with reviewed decisions and manual fills:

```cmd
python -m quant_replay_system.cli paper-daily --date 2024-05-20 --reviewed-decisions outputs\reports\paper_trading\reviews\...\reviewed_decisions.csv --fills data\paper\fills.csv
```

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not download or refresh data.
- Does not place orders or call broker APIs.
- Does not simulate future returns; replay remains the workflow for execution/performance simulation.
- Snapshot preflight checks file quality, but it does not repair data.
- Missing universe `listed_date` values are supported as unknown listing dates, but incomplete vendor universe coverage should still be reviewed before paper-trading research use.
- If a market symbol is absent from the universe snapshot, the point-in-time factor dataset will be empty for that symbol. ETF workflows need ETF universe coverage, not stock-only universe coverage.
- A reviewed ETF overlay can add ETF universe coverage, but the project does not infer or auto-approve ETF rows.
- The `demo` selection profile is only for local artifact/workflow validation with tiny datasets; it is not a strategy recommendation and does not change scoring formulas.
- `signal-advisory` can render alert previews from demo candidates, but those previews are workflow validation only and are not sent as messages.
- `market-update-handoff` can include `WARN_ACCEPT` provisional rows for local validation, but those rows remain provisional and should not be treated as strategy recommendations.
- Candidate scoring remains explainable MVP scoring, not machine learning.
