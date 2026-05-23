# Reviewed ETF Universe Overlay Workflow v0.1

Universe overlay is a local-only helper for merging reviewed ETF universe rows into a base universe snapshot before `data-pipeline`.

It does not fetch market data, call AKShare or Tushare, connect to broker APIs, place orders, or automate execution.

## Purpose

Some real-data universe sources can be stock-only. If market data contains ETF `510300` but the universe snapshot has only `STOCK` rows, point-in-time factor dataset construction has no joinable universe row and current-candidates can legitimately produce an empty factor dataset.

The overlay workflow lets you review a small ETF universe CSV manually and merge it into the base universe:

```text
base universe raw_data.csv
+ reviewed ETF overlay CSV
-> universe-overlay
-> merged universe raw_data.csv
-> data-pipeline
-> snapshot-quality
-> current-candidates
```

## Overlay Schema

The overlay CSV uses the canonical universe schema:

```text
as_of_date,symbol,name,instrument_type,exchange,listed_date,delisted_date,is_active,is_st,is_suspended,industry,min_lot,t_plus_rule,available_time,revision_id,source
```

Required fields for every overlay row:

- `symbol`
- `instrument_type`
- `as_of_date`
- `available_time`
- `is_active`
- `min_lot`
- `t_plus_rule`

Symbols are read as strings and leading zeros are significant. `000001`, `510300`, and `159915` are preserved exactly.

## Validation Rules

`universe-overlay` validates the reviewed overlay before merging:

- missing canonical columns fail,
- blank `symbol` fails,
- duplicate overlay symbols fail by default,
- blank required overlay fields fail,
- invalid `as_of_date` or `available_time` fails,
- invalid `is_active` values fail,
- non-positive `min_lot` fails,
- overlay rows that already exist in the base universe fail unless `--allow-override-existing` is supplied.

`--allow-override-existing` should be used only after manual review because it replaces base rows for matching symbols.

## CLI Usage

Copy the docs-only example overlay and edit it locally:

```cmd
copy docs\examples\etf_universe_overlay_example.csv data\raw\manual_overlays\etf_universe_overlay.csv
```

Merge the reviewed ETF rows into the base universe:

```cmd
python -m quant_replay_system.cli universe-overlay --base-universe data\raw\AKSHARE_OPTIONAL\universe\<run_id>\raw_data.csv --overlay data\raw\manual_overlays\etf_universe_overlay.csv
```

The command prints:

- merged universe path,
- added symbol count,
- overridden symbol count,
- report path,
- `No live trading or broker API was invoked.`

The merged universe is written under:

```text
data/raw/LOCAL_CSV/universe_overlay/<overlay_run_id>/raw_data.csv
```

## Data Pipeline Handoff

Use the merged universe path in your local data-pipeline manifest:

```json
{
  "datasets": [
    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": "<MARKET_RAW_DATA_CSV>"},
    {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": "<MERGED_UNIVERSE_RAW_DATA_CSV>"},
    {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": "<TRADING_CALENDAR_RAW_DATA_CSV>"}
  ]
}
```

Then run:

```cmd
python -m quant_replay_system.cli data-pipeline --manifest data\local\local_csv_market_fallback_manifest.json
python -m quant_replay_system.cli snapshot-quality --manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json
```

For a tiny local dry-run where a single scored ETF row does not pass default candidate thresholds, use the explicit demo selection profile:

```cmd
python -m quant_replay_system.cli current-candidates --date 2024-05-20 --universe etf_core --top 5 --snapshot-manifest outputs\reports\data_pipeline\<pipeline_id>\snapshot_manifest.json --selection-profile demo
```

Demo candidates are for artifact and paper workflow validation only. They are marked as `selection_profile=demo` and `not_strategy_recommendation=true`.

## Artifact Outputs

`universe-overlay` writes:

- `raw_data.csv`
- `universe_overlay_report.md`
- `overlay_metadata.json`

The report includes row counts, added symbols, overridden symbols, output paths, and the no-live-trading statement.

## Guardrails

- Use reviewed local CSV files only.
- Do not commit `data/raw/`, `data/processed/`, or `outputs/`.
- Run `data-quality` and `snapshot-quality` before using merged data.
- Current candidates are paper-trading research inputs only.
- The current-candidate demo profile can validate downstream artifacts with tiny datasets, but demo rows are not strategy recommendations.
- No broker API or live trading integration is involved.
- Automated tests use local fake CSV data only and do not call real network APIs.

## Known MVP Limitations

- The overlay tool does not infer missing ETF rows from market data.
- The user is responsible for reviewing ETF names, exchanges, activity status, and available times.
- It does not reconcile vendor symbol master history.
- Override behavior is intentionally manual and off by default.
