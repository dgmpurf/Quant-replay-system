# AKShare Manual Real-Data Workflow v0.1

This document shows a guarded Windows CMD workflow for using the optional AKShare data source adapter manually.

The AKShare adapter is optional and manual-only. It is not enabled by default, automated tests never call AKShare or the network, and the project still does not connect to brokers, place orders, automate execution, or implement live trading.

## Purpose

`AKSHARE_OPTIONAL` can fetch raw market-style data into local artifacts when the user explicitly opts in with `--allow-real-data`.

The raw output is only the first step. Before replay, current-candidate generation, or paper-trading review, AKShare output should go through the existing local preparation path:

```text
AKShare manual fetch
-> raw_data.csv
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates
```

Do not treat raw AKShare data as complete, clean, or replay-ready until data quality and snapshot quality have been reviewed.

For a concise universe + market dry-run checklist with a local manifest template, see [akshare_real_data_dry_run.md](akshare_real_data_dry_run.md).

## Safety Guarantees

- `AKSHARE_OPTIONAL` requires explicit `--allow-real-data`.
- Real-data fetches are disabled by default in `config/default.yaml`.
- Automated tests must not use `--allow-real-data`.
- Automated tests must not call AKShare or network APIs.
- No API keys or tokens are required by this adapter.
- `.env` is not modified.
- No broker API is invoked.
- No live trading or automated order placement is implemented.

## Setup

From Windows CMD:

```cmd
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
.venv\Scripts\activate.bat
```

If AKShare is not installed in the local virtual environment, install it manually:

```cmd
python -m pip install akshare
```

Do not add real-data dependencies, tokens, or generated vendor data to automated tests.

## Step 1: Fetch Raw AKShare Market Data

Example ETF market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

The command prints a `raw_data` path similar to:

```text
data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv
```

It also prints:

```text
No live trading or broker API was invoked.
```

For v0.1, AKShare support is intentionally limited:

- `market` supports ETF-like symbols such as `510300` through the default ETF daily-history path.
- `benchmark` uses the default AKShare index daily-history path.
- `trading_calendar` uses the default AKShare trading-calendar path.
- `universe` supports guarded stock/ETF symbol snapshot fetches with conservative default fields.
- `corporate_actions` are not implemented for AKShare yet.

## Step 2: Run The Raw File Through Data Pipeline

Use the printed `raw_data.csv` path as a local CSV input:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv"
```

The pipeline writes processed data and report artifacts similar to:

```text
data\processed\market\<pipeline_id>\raw_data_cleaned.csv
outputs\reports\data_pipeline\<pipeline_id>\data_pipeline_report.md
outputs\reports\data_pipeline\<pipeline_id>\data_quality_summary.csv
```

`data-pipeline` runs data quality by default. You can also rerun the standalone quality report against the processed file:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type market --input "data\processed\market\<pipeline_id>\raw_data_cleaned.csv"
```

Market data alone is not enough for a full current-candidates run. A complete snapshot normally needs at least:

- `market`
- `universe`
- `trading_calendar`

The current AKShare adapter can help with market, universe, and trading-calendar data. Universe fields may be incomplete depending on AKShare source coverage, so always review the data-quality output before using it for current candidates.

## Step 3: Prepare Required Snapshot Inputs

Fetch or prepare the other required datasets locally.

Example trading-calendar fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Then run the printed raw calendar file through the pipeline:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type trading_calendar --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv"
```

For universe data, run the guarded AKShare universe snapshot command:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

Then run the printed raw universe file through the pipeline:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type universe --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv"
```

If AKShare universe coverage is not sufficient for your research universe, use a reviewed local universe CSV instead:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type universe --source LOCAL_CSV --input "data\local\universe_snapshot.csv"
```

## Step 4: Build A Multi-Dataset Snapshot Manifest

When you have local files for market, universe, and trading calendar, use data-pipeline manifest mode.

Create a local JSON manifest outside generated raw-data folders, for example:

```json
{
  "datasets": [
    {
      "dataset_type": "market",
      "source": "LOCAL_CSV",
      "input_path": "data/raw/AKSHARE_OPTIONAL/market/<market_run_id>/raw_data.csv"
    },
    {
      "dataset_type": "universe",
      "source": "LOCAL_CSV",
      "input_path": "data/raw/AKSHARE_OPTIONAL/universe/<universe_run_id>/raw_data.csv"
    },
    {
      "dataset_type": "trading_calendar",
      "source": "LOCAL_CSV",
      "input_path": "data/raw/AKSHARE_OPTIONAL/trading_calendar/<calendar_run_id>/raw_data.csv"
    }
  ]
}
```

Run:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest "data\local\akshare_snapshot_manifest.json"
```

The pipeline writes:

```text
outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

## Step 5: Run Snapshot Quality

Run the snapshot gate before current candidates:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

Review `PASS`, `WARN`, or `FAIL` before continuing.

If the gate is `FAIL`, do not use the snapshot for current candidates until the required dataset issue is fixed.

## Step 6: Generate Current Candidates

When snapshot quality is acceptable, generate current candidates:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

The command writes:

```text
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\candidates.csv
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\current_candidates_report.md
```

From there, continue into the local manual paper workflow:

```cmd
python -m quant_replay_system.cli current-to-paper --candidates "outputs\reports\current_candidates\<run_folder>\candidates.csv" --paper-date 2024-05-20
python -m quant_replay_system.cli current-to-paper-review --handoff-dir "outputs\reports\current_to_paper_handoff\<handoff_id>"
```

Manual review and fills remain separate, human-controlled steps.

## Recommended Local Folder Convention

Raw and processed data should stay local and untracked:

```text
data\raw\AKSHARE_OPTIONAL\market\<run_id>\raw_data.csv
data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv
data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv
data\processed\market\<pipeline_id>\raw_data_cleaned.csv
data\processed\universe\<pipeline_id>\raw_data_cleaned.csv
data\processed\trading_calendar\<pipeline_id>\raw_data_cleaned.csv
outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
outputs\reports\snapshot_quality\<snapshot_id>_<quality_gate_id>\snapshot_quality_gate_report.md
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\candidates.csv
```

Do not commit:

- `data/raw/`
- `data/processed/`
- large market data files
- generated vendor data
- local credentials or `.env`

## Troubleshooting

### AKShare is not installed

Install it manually in the active local virtual environment:

```cmd
python -m pip install akshare
```

Then rerun the `data-source-fetch` command.

### Network or API failure

AKShare is an external data source and can fail due to network, service, or upstream schema changes. Rerun later, narrow the date range, or use an already downloaded local CSV through `LOCAL_CSV`.

Automated tests should never depend on this path.

### Empty dataset

Check:

- symbol format,
- `--market-type` for universe snapshots,
- date range,
- whether the instrument existed during the requested period,
- whether AKShare changed the underlying function or returned columns.

Then run `data-quality` before using the file.

### Symbol format uncertainty

For v0.1, ETF-like symbols such as `510300` use the default ETF daily-history path. Other market symbols use the default A-share daily-history path. If a symbol does not work, verify the symbol format directly with AKShare documentation before relying on the output.

### `current-candidates` returns zero candidates

Review:

- `snapshot-quality` status,
- market/universe overlap,
- decision date coverage,
- `available_time` values,
- candidate score thresholds,
- risk precheck reasons in `scored_dataset.csv`.

Zero candidates can be a valid research result, but it should be explainable from the artifacts.

### `snapshot-quality` returns WARN or FAIL

Open the generated snapshot quality report. Required dataset failures should block downstream use until fixed. Warnings can be acceptable for exploratory local work, but they should be reviewed before paper-trading handoff.

## Known MVP Limitations

- AKShare is manual-only and disabled by default.
- The adapter does not provide a full production data downloader.
- Universe snapshot support is MVP-level and may rely on defaulted fields such as `industry=UNKNOWN`, `min_lot=100`, and `t_plus_rule=T+1`.
- Corporate action AKShare fetches are not implemented yet.
- Function selection for market data is simple and may need manual refinement later.
- Data quality checks summarize issues; they do not repair data.
- Mock data and small examples are not strategy-quality validation.
- This workflow is not live trading and never invokes broker APIs.
