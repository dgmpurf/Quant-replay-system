# Reviewed Offline Update Batch To Snapshot Handoff v0.1

`market-update-handoff` converts reviewed offline `market-daily-update` rows into a local snapshot validation dry run.

It is local-only. It does not fetch real data, mutate the market cache, schedule jobs, call broker APIs, place orders, or automate execution.

## Purpose

The offline reviewed symbol manifest proves that each raw market file can pass `market-cache-preflight`. The handoff proves that the accepted rows can feed the research snapshot chain:

```text
market-daily-update
-> market-update-handoff
-> data-pipeline
-> snapshot-quality
-> current-candidates --selection-profile demo
```

This keeps cache writes separate from research snapshot dry-runs. Accepted raw files can be tested end to end before any later explicit cache write.

## CLI

Run from a reviewed offline symbol manifest:

```cmd
python -m quant_replay_system.cli market-update-handoff --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --selection-profile demo --dry-run
```

Use an existing `market-daily-update` artifact directory instead of rerunning the manifest:

```cmd
python -m quant_replay_system.cli market-update-handoff --market-daily-update-dir outputs\reports\market_daily_update\<update_id> --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --selection-profile demo
```

By default, `WARN_ACCEPT` rows are included. This lets provisional reviewed sources, such as AKShare/Sina ETF rows, participate in local workflow validation. To include only strict `ACCEPT` rows:

```cmd
python -m quant_replay_system.cli market-update-handoff --symbol-manifest data\raw\manual_manifests\daily_market_symbols_offline_example.csv --universe data\raw\LOCAL_CSV\universe_overlay\<overlay_id>\raw_data.csv --trading-calendar data\raw\AKSHARE_OPTIONAL\trading_calendar\<run_id>\raw_data.csv --decision-date 2024-05-20 --universe-name etf_core --strict-accept-only
```

Use `--skip-validation` to only generate the batch market CSV and data-pipeline manifest.

## Included Rows

Rows are included when:

- `preflight_status=ACCEPT`, or
- `preflight_status=WARN_ACCEPT` and `--strict-accept-only` is not set.

Rejected, blocked, disabled, or failed rows are excluded and reported in `market_update_handoff_rows.csv`.

## Generated Local Inputs

The handoff writes a merged market CSV under:

```text
data/raw/manual_update_batches/<handoff_id>/market_raw_data.csv
```

It also writes a data-pipeline manifest under:

```text
data/raw/manual_manifests/market_update_handoff_<handoff_id>.json
```

The manifest uses `LOCAL_CSV` entries for:

- `market`: the merged batch market CSV,
- `universe`: the reviewed universe path supplied to the command,
- `trading_calendar`: the reviewed trading calendar path supplied to the command.

## Validation Chain

When validation is enabled, the command runs:

```text
data-pipeline -> snapshot-quality -> current-candidates
```

`current-candidates` uses the supplied `--decision-date`, `--universe-name`, and `--selection-profile`. The `demo` profile remains only for local artifact/workflow validation and is not a strategy recommendation.

## Artifacts

Artifacts are written under:

```text
outputs/reports/market_update_handoff/<handoff_id>/
```

Files:

- `market_update_handoff_report.md`
- `market_update_handoff_rows.csv`
- `generated_pipeline_manifest.json`
- `metadata.json`

The metadata records the batch CSV path, local pipeline manifest path, pipeline id, snapshot quality status, current-candidate run id, factor/scored/candidate shapes, warnings, and no-live-trading/no-broker audit fields.

## Index, Health, And Status

Recent handoff artifacts can be discovered and checked before running paper workflow smoke tests.

Build a local handoff artifact index:

```cmd
python -m quant_replay_system.cli market-update-handoff-index --root outputs\reports\market_update_handoff
```

The index records each `handoff_id`, batch market CSV path, generated pipeline manifest path, pipeline id, snapshot-quality status, current-candidate run id, factor/scored/candidate row counts, and report paths.

Check indexed artifacts:

```cmd
python -m quant_replay_system.cli market-update-handoff-health --index outputs\reports\market_update_handoff\index\market_update_handoff_index.csv
```

The health check verifies metadata, batch market CSVs, generated manifests, linked data-pipeline reports, snapshot-quality reports, current-candidate artifacts when paths are available, and no-live-trading statements where expected.

Summarize the latest handoff:

```cmd
python -m quant_replay_system.cli market-update-handoff-status --root outputs\reports\market_update_handoff
```

The status view reports the latest handoff, `PASS`/`WARN`/`FAIL`, workflow stage, next manual action, and warnings/errors. It does not regenerate artifacts, mutate the cache, fetch data, or run paper trading.

## Safety

- No cache write occurs.
- No real data fetch occurs.
- No live trading or broker API is invoked.
- No order placement is possible.
- This is not a scheduler or automation service.
- The generated snapshot still must pass the normal quality gates before research use.

## Known MVP Limitations

- v0.1 consumes offline raw files or an existing local update artifact; it does not decide source preference.
- `WARN_ACCEPT` inclusion is useful for local smoke tests but should be reviewed before normal research use.
- ETF rows may remain provisional until another reliable ETF reference source is available.
- The handoff does not repair failed rows or generate missing universe coverage.
