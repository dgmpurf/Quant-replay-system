# Reviewed LOCAL_CSV Market Fallback Workflow v0.1

This guide documents a local-only fallback workflow for market data when optional real-data adapters are unstable.

It is not live trading. It does not connect to broker APIs, place orders, automate execution, print secrets, or modify `.env`.

## Purpose

Use this workflow when AKShare market history fails but you still have usable local inputs:

- a manually reviewed market `raw_data.csv`,
- an AKShare or other reviewed universe `raw_data.csv`,
- an AKShare or other reviewed trading-calendar `raw_data.csv`.

The intended path is:

```text
reviewed market LOCAL_CSV
plus universe LOCAL_CSV
plus trading_calendar LOCAL_CSV
to data-pipeline
to data-quality
to snapshot-quality
to current-candidates
```

The minimum dataset set for `current-candidates` is:

- `market`
- `universe`
- `trading_calendar`

If your universe file is stock-only and the reviewed market file contains ETF symbols such as `510300`, add a reviewed ETF universe overlay before running `data-pipeline`.

## Required Market CSV Columns

The market fallback CSV should use the canonical market schema:

```text
symbol,trade_date,open,high,low,close,volume,amount,pre_close,adj_factor,is_suspended,limit_up,limit_down,event_time,publish_time,ingest_time,available_time,revision_id,source
```

Column expectations:

- `symbol`: local instrument code, for example `000001` or `510300`.
- `trade_date`: trading date, preferably `YYYY-MM-DD`.
- `open`, `high`, `low`, `close`, `pre_close`, `adj_factor`, `limit_up`, `limit_down`: numeric price/factor fields.
- `volume`, `amount`: numeric turnover fields; they must not be negative.
- `is_suspended`: boolean-like value such as `false`, `true`, `0`, or `1`.
- `event_time`, `publish_time`, `ingest_time`, `available_time`: parseable timestamps.
- `available_time`: earliest time the row may be used by replay/current candidates. For daily market data, `trade_date 15:30` is the usual MVP default when exact publication time is unavailable.
- `revision_id`: local revision label, for example `reviewed_v1`.
- `source`: source label, for example `LOCAL_REVIEWED_CSV`.

The ingestion layer can add default `source`, `revision_id`, and `available_time` only when configured to do so, but this fallback workflow is intentionally reviewed. Prefer filling those fields explicitly before using the file.

## Local File Convention

Keep manually reviewed files local and out of Git:

```text
data\local\reviewed_market\market_raw_data.csv
data\raw\AKSHARE_OPTIONAL\universe\<universe_run_id>\raw_data.csv
data\raw\AKSHARE_OPTIONAL\trading_calendar\<calendar_run_id>\raw_data.csv
data\local\local_csv_market_fallback_manifest.json
```

Do not commit `data/raw/`, `data/processed/`, `outputs/`, or large vendor files.

## Validate The Market CSV Before Pipeline

Run these checks from Windows CMD:

```cmd
cd /d "G:\AICODING\Quantitative Trading\quant-replay-system"
.venv\Scripts\activate.bat
```

Check that the file is readable and has the required columns:

```cmd
python -c "import pandas as pd; p=r'<MARKET_RAW_DATA_CSV>'; required='symbol,trade_date,open,high,low,close,volume,amount,pre_close,adj_factor,is_suspended,limit_up,limit_down,event_time,publish_time,ingest_time,available_time,revision_id,source'.split(','); df=pd.read_csv(p); missing=[c for c in required if c not in df.columns]; print('rows', len(df)); print('missing', missing); print(df.head().to_string(index=False))"
```

Check duplicate `symbol`/`trade_date` keys and common market sanity conditions:

```cmd
python -c "import pandas as pd; p=r'<MARKET_RAW_DATA_CSV>'; df=pd.read_csv(p); prices=['open','high','low','close']; n=df[prices].apply(pd.to_numeric, errors='coerce'); print('duplicate_symbol_trade_date', int(df.duplicated(['symbol','trade_date']).sum())); print('non_positive_prices', int((n<=0).any(axis=1).sum())); print('ohlc_inconsistent', int(((n['high']<n['low'])|(n['high']<n['open'])|(n['high']<n['close'])|(n['low']>n['open'])|(n['low']>n['close'])).sum())); print('negative_volume_or_amount', int((df[['volume','amount']].apply(pd.to_numeric, errors='coerce')<0).any(axis=1).sum()))"
```

Check timestamp parseability:

```cmd
python -c "import pandas as pd; p=r'<MARKET_RAW_DATA_CSV>'; df=pd.read_csv(p); cols=['event_time','publish_time','ingest_time','available_time']; print({c:int(pd.to_datetime(df[c], errors='coerce').isna().sum()) for c in cols if c in df.columns})"
```

Fix unexplained missing columns, duplicate rows, non-positive prices, negative volume/amount, OHLC inconsistencies, or invalid timestamps before continuing.

## Add ETF Universe Coverage When Needed

Copy and review the example ETF overlay:

```cmd
copy docs\examples\etf_universe_overlay_example.csv data\raw\manual_overlays\etf_universe_overlay.csv
```

Edit the local overlay as needed, then merge it into the base universe:

```cmd
python -m quant_replay_system.cli universe-overlay --base-universe "<UNIVERSE_RAW_DATA_CSV>" --overlay data\raw\manual_overlays\etf_universe_overlay.csv
```

Use the printed `merged_universe_path` as `<UNIVERSE_RAW_DATA_CSV>` in the local manifest. See [universe_overlay.md](universe_overlay.md) for validation rules and artifact details.

## Create A Local Manifest

Copy this template:

```text
docs\examples\local_csv_market_fallback_manifest_example.json
```

Replace the placeholders:

- `<MARKET_RAW_DATA_CSV>`
- `<UNIVERSE_RAW_DATA_CSV>`
- `<TRADING_CALENDAR_RAW_DATA_CSV>`

Recommended local copy:

```text
data\local\local_csv_market_fallback_manifest.json
```

## Run Data Pipeline

Run all three reviewed files through one local pipeline:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest "data\local\local_csv_market_fallback_manifest.json"
```

The pipeline writes processed canonical files and, when the three required datasets are present, a snapshot manifest:

```text
outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

## Review Data Quality

`data-pipeline` runs data-quality by default. Open the data-quality report paths printed by the command.

You can also rerun standalone data-quality on processed outputs:

```cmd
python -m quant_replay_system.cli data-quality --dataset-type market --input "data\processed\market\<pipeline_id>\raw_data_cleaned.csv"
python -m quant_replay_system.cli data-quality --dataset-type universe --input "data\processed\universe\<pipeline_id>\raw_data_cleaned.csv"
python -m quant_replay_system.cli data-quality --dataset-type trading_calendar --input "data\processed\trading_calendar\<pipeline_id>\raw_data_cleaned.csv"
```

Do not continue if required data quality failures are unexplained.

## Run Snapshot Quality

Run the snapshot quality gate:

```cmd
python -m quant_replay_system.cli snapshot-quality --manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

Interpretation:

- `PASS`: continue to current candidates.
- `WARN`: review the warning before continuing.
- `FAIL`: fix the required dataset issue before using the snapshot.

## Generate Current Candidates

After snapshot quality is acceptable:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest "outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json"
```

The output includes:

```text
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\candidates.csv
outputs\reports\current_candidates\<decision_date>_<universe_name>_<run_id>\current_candidates_report.md
```

These are paper-trading research candidates only. They do not trigger live orders.

## Optional Status Dashboard

After the run, summarize the local workflow:

```cmd
python -m quant_replay_system.cli research-status --root outputs\reports --decision-date 2024-05-20 --universe etf_core
```

Review the printed next manual action.

## Guardrails

- This workflow uses reviewed local CSV files.
- No real network calls are needed after the local CSV files exist.
- Automated tests must not call AKShare, Tushare, or network APIs.
- Do not commit generated `data/raw/`, `data/processed/`, `outputs/`, `.env`, `.venv`, or secrets.
- Always run `data-quality` and `snapshot-quality` before current-candidate generation.
- Current candidates are paper-trading research candidates only.
- No broker API is involved.
- No order automation is implemented.

## Troubleshooting

### Market CSV is missing required columns

Add the missing canonical columns or export the data again. Prefer explicit `available_time`, `revision_id`, and `source` values for reviewed fallback files.

### Data-quality reports duplicate market rows

Deduplicate by `symbol` and `trade_date`, keeping the reviewed row for the intended revision.

### OHLC checks fail

Verify vendor-adjusted data and split/adjustment conventions. The project expects `high >= low`, `high >= open`, `high >= close`, `low <= open`, and `low <= close`.

### Snapshot-quality fails

Check whether the failure is in a required dataset: `market`, `universe`, or `trading_calendar`. Required dataset failures should be fixed before current candidates.

### Current-candidates returns zero candidates

Confirm the `decision_date` exists in the market and calendar files, the universe includes active instruments for that date, and the configured score/candidate thresholds are not too restrictive for the tiny dataset.

## Known MVP Limitations

- This workflow does not fetch, repair, or certify market data.
- Reviewed local CSV quality depends on the user's upstream source and manual review.
- The project still uses local/mock/manual data only for automated tests.
- This is not live trading and does not connect to a broker.
