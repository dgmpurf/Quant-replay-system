# AKShare Universe + Market Real-Data Dry-Run Checklist v0.1

This checklist is a manual Windows CMD dry run for moving guarded AKShare data through the local research workflow.

It is not live trading. It does not connect to broker APIs, place orders, automate execution, print secrets, or modify `.env`.

## Purpose

Use this checklist when you want to manually test the local real-data path:

```text
AKShare market/universe/calendar fetch
-> raw_data.csv
-> data-pipeline
-> data-quality
-> snapshot-quality
-> current-candidates
-> research-status
```

The minimum dataset set for `current-candidates` is:

- `market`
- `universe`
- `trading_calendar`

Optional `benchmark` data can be added later, but it is not required for the first dry run.

## 1. Activate The Local Environment

```cmd
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
.venv\Scripts\activate.bat
```

## 2. Install AKShare Manually If Needed

Only install AKShare in your local virtual environment when you are intentionally doing a manual real-data dry run:

```cmd
python -m pip install akshare
```

Automated tests must not install AKShare, call AKShare, or use network APIs.

## 3. Fetch AKShare Market Data

Example ETF market fetch:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type market --symbol 510300 --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Copy the printed `raw_data` path. It should look like:

```text
data\raw\AKSHARE_OPTIONAL\market\<market_run_id>\raw_data.csv
```

## 4. Fetch AKShare Universe Snapshot

Example combined stock/ETF universe snapshot:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type universe --as-of-date 2024-05-20 --market-type all --allow-real-data
```

Copy the printed `raw_data` path. It should look like:

```text
data\raw\AKSHARE_OPTIONAL\universe\<universe_run_id>\raw_data.csv
```

Universe fields can be incomplete depending on AKShare source coverage. The adapter fills conservative MVP defaults, but you should still review data-quality results before using the snapshot.

## 5. Fetch AKShare Trading Calendar

If the AKShare trading-calendar path is supported in your environment, fetch it manually:

```cmd
python -m quant_replay_system.cli data-source-fetch --source AKSHARE_OPTIONAL --dataset-type trading_calendar --start-date 2024-01-01 --end-date 2024-05-20 --allow-real-data
```

Copy the printed `raw_data` path. It should look like:

```text
data\raw\AKSHARE_OPTIONAL\trading_calendar\<calendar_run_id>\raw_data.csv
```

If this path fails because the AKShare endpoint changed, use a reviewed local trading-calendar CSV through `LOCAL_CSV`.

## 6. Create A Local Data-Pipeline Manifest

Create a local manifest by copying the example template:

```text
docs\examples\akshare_real_data_pipeline_manifest_example.json
```

Replace these placeholder values with the printed raw paths:

- `<MARKET_RAW_DATA_CSV>`
- `<UNIVERSE_RAW_DATA_CSV>`
- `<TRADING_CALENDAR_RAW_DATA_CSV>`

Keep the edited manifest local. A typical local path is:

```text
data\local\akshare_real_data_pipeline_manifest.json
```

## 7. Run Data Pipeline

Run the raw AKShare files through canonical ingestion, data-quality checks, and snapshot manifest generation:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest "data\local\akshare_real_data_pipeline_manifest.json"
```

The command prints processed paths and, when all three datasets are present, a snapshot manifest path similar to:

```text
outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

You can also process one dataset at a time with `LOCAL_CSV`:

```cmd
python -m quant_replay_system.cli data-pipeline --dataset-type market --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\market\<market_run_id>\raw_data.csv"
python -m quant_replay_system.cli data-pipeline --dataset-type universe --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\universe\<universe_run_id>\raw_data.csv"
python -m quant_replay_system.cli data-pipeline --dataset-type trading_calendar --source LOCAL_CSV --input "data\raw\AKSHARE_OPTIONAL\trading_calendar\<calendar_run_id>\raw_data.csv"
```

Manifest mode is preferred for a full current-candidate snapshot because it creates one combined `snapshot_manifest.json`.

## 8. Review Data Quality

`data-pipeline` runs data-quality by default. Open its report path from the CLI output.

You can rerun standalone data-quality checks on processed files if needed:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type market --input "data\processed\market\<pipeline_id>\raw_data_cleaned.csv"
python -m quant_replay_system.cli data-quality --dataset-type universe --input "data\processed\universe\<pipeline_id>\raw_data_cleaned.csv"
python -m quant_replay_system.cli data-quality --dataset-type trading_calendar --input "data\processed\trading_calendar\<pipeline_id>\raw_data_cleaned.csv"
```

Do not continue to current candidates if required data quality issues are unexplained.

## 9. Run Snapshot Quality

Run the snapshot gate against the generated manifest:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

Review `PASS`, `WARN`, or `FAIL`.

- `PASS`: suitable for the next dry-run step.
- `WARN`: review the warning before continuing.
- `FAIL`: fix required dataset issues before using the snapshot.

## 10. Generate Current Candidates

Generate paper-trading candidates from the quality-checked snapshot:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

The output includes:

```text
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\candidates.csv
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\current_candidates_report.md
```

Current candidates are paper-trading candidates only. They are not live trading signals and do not trigger orders.

## 11. Run Research Status

Build the top-level local workflow status report:

```cmd
python -m quant_replay_system.cli research-status --root outputs\reports --decision-date 2024-05-20 --universe etf_core
```

Review the printed `next_manual_action` and the generated dashboard report.

## Recommended Local Folder Convention

```text
data\raw\AKSHARE_OPTIONAL\market\<market_run_id>\raw_data.csv
data\raw\AKSHARE_OPTIONAL\universe\<universe_run_id>\raw_data.csv
data\raw\AKSHARE_OPTIONAL\trading_calendar\<calendar_run_id>\raw_data.csv
data\local\akshare_real_data_pipeline_manifest.json
data\processed\market\<pipeline_id>\raw_data_cleaned.csv
data\processed\universe\<pipeline_id>\raw_data_cleaned.csv
data\processed\trading_calendar\<pipeline_id>\raw_data_cleaned.csv
outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
outputs\reports\snapshot_quality\<snapshot_id>_<quality_gate_id>\snapshot_quality_gate_report.md
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\candidates.csv
```

## Guardrails

- Real data fetch is manual only.
- `--allow-real-data` is required for `AKSHARE_OPTIONAL`.
- Automated tests must not call AKShare or network APIs.
- Do not commit `data/raw/`, `data/processed/`, or large market data files.
- Always run `data-quality` and `snapshot-quality` before `current-candidates`.
- Current candidates are paper-trading candidates only, not live trading signals.
- No broker API is involved.
- No order automation is implemented.
- No secrets, API keys, account values, or tokens should be printed or stored.

## Troubleshooting

### AKShare is not installed

Install it manually in the active virtual environment:

```cmd
python -m pip install akshare
```

### AKShare endpoint changed

AKShare function names and columns can change. If a fetch fails, check the command output, confirm the AKShare function still exists, and use a reviewed local CSV through `LOCAL_CSV` until the adapter mapping is updated.

### Symbol format issues

For market data, ETF-like symbols such as `510300` use the default ETF history path. Other A-share symbols may require a different AKShare function or symbol format.

### Empty raw_data.csv

Check the symbol, date range, instrument existence, `--market-type`, and whether AKShare returned rows for the requested endpoint.

### data-quality FAIL

Open the generated data-quality report, fix the source file or mapping issue, and rerun `data-pipeline`.

### snapshot-quality FAIL

Required datasets are `market`, `universe`, and `trading_calendar`. A failure in any required dataset should block current-candidate generation until fixed.

### current-candidates returns zero candidates

Review market/universe overlap, decision-date coverage, `available_time`, score thresholds, and risk precheck reasons in `scored_dataset.csv`.

### research-status shows WARN

Open the linked report and inspect the component with warnings. A WARN can be acceptable for exploratory dry runs, but it should be understood before paper-trading handoff.

## Known MVP Limitations

- AKShare real-data usage is manual-only and disabled by default.
- Universe snapshot fields may rely on conservative defaults when AKShare does not provide them.
- Trading-calendar endpoint availability can vary by AKShare version.
- The workflow does not repair vendor data.
- The dry run is not strategy-quality validation.
- This workflow does not implement live trading, broker integration, or automated order placement.
