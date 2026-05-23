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
local snapshot -> current-candidates -> candidates.csv -> paper-review-decisions -> paper-daily
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
- Candidate scoring remains explainable MVP scoring, not machine learning.
