# Guarded PIT Universe Export Staging v0.1

`pit-universe-export-staging` creates guarded, outputs-only staging previews from PIT universe export-readiness artifacts.

It does not write usable universe files under `data/raw` or `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The staging workflow sits after export readiness and before any future explicit accept/export workflow:

```text
pit-universe-overlay-review
-> pit-universe-overlay-export-readiness
-> pit-universe-export-staging
-> future explicit accepted local universe export
-> future snapshot preparation
```

It answers:

```text
Which export-ready PIT universe rows can be staged as reviewable preview files under outputs/reports?
```

Staging previews are not accepted universe inputs.

## CLI Usage

Run against the active export-readiness artifact:

```cmd
python -m quant_replay_system.cli pit-universe-export-staging --export-readiness outputs\reports\point_in_time_universe_overlay_export_readiness\75c6975e93e4\pit_universe_overlay_export_readiness.csv
```

Optional:

- `--output-dir`: staging artifact root.
- `--allow-diagnostic-source`: allow `manual_diagnostics` sources for isolated diagnostics only.

Diagnostic sources are blocked by default so synthetic export-ready rows cannot become active staging inputs.

## Required Universe Columns

Staged preview rows use the current-candidates universe snapshot schema:

- `as_of_date`
- `symbol`
- `name`
- `instrument_type`
- `exchange`
- `listed_date`
- `delisted_date`
- `is_active`
- `is_st`
- `is_suspended`
- `industry`
- `min_lot`
- `t_plus_rule`
- `available_time`
- `revision_id`
- `source`

Symbols are preserved as strings so leading zeros remain intact.

## Status Values

Expected staging statuses include:

- `EXPORT_STAGING_BLOCKED_NO_READY_ROWS`
- `EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE`
- `EXPORT_STAGING_BLOCKED_READINESS_HEALTH`
- `EXPORT_STAGING_BLOCKED_DUPLICATES`
- `EXPORT_STAGING_BLOCKED_MISSING_COLUMNS`
- `EXPORT_STAGING_READY_FOR_REVIEW`
- `EXPORT_STAGING_DRY_RUN_CREATED`
- `EXPORT_STAGING_FAILED`

For the current active export-readiness artifact, `EXPORT_STAGING_BLOCKED_NO_READY_ROWS` is expected because `export_ready_count=0`.

## Artifacts

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_export_staging/<staging_id>/
```

Files:

- `pit_universe_export_staging.csv`
- `pit_universe_export_staging_report.md`
- `metadata.json`
- `staged_universe_combined_preview.csv`
- `staged_universe_<signal_date>_preview.csv` when staged rows exist

Preview CSVs are review artifacts only. They are not accepted local universe files and must not be passed to production-like workflows without a later explicit accept/export step.

## Index, Health, And Status

Use the artifact views to discover, check, and summarize staging artifacts:

```cmd
python -m quant_replay_system.cli pit-universe-export-staging-index
python -m quant_replay_system.cli pit-universe-export-staging-health
python -m quant_replay_system.cli pit-universe-export-staging-status
```

The index records staging id, linked export-readiness/review ids, row counts, staged row counts, blocked counts, diagnostic-source flags, no-ready-row flags, duplicate and missing-column counts, safety flags, and artifact paths.

The health view checks that metadata, staging CSV, and report files are readable; required columns exist; no `data/raw` or `data/processed` write is claimed; no current-candidates generation, snapshot build, forward labels, cache mutation, API call, broker call, order placement, or message delivery is claimed; and staged rows contain complete universe snapshot columns.

The status view summarizes the latest staging artifact into stages such as:

- `NO_PIT_UNIVERSE_EXPORT_STAGING`
- `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS`
- `PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE`
- `PIT_UNIVERSE_EXPORT_STAGING_READY_FOR_REVIEW`
- `PIT_UNIVERSE_EXPORT_STAGING_HEALTH_WARN`
- `PIT_UNIVERSE_EXPORT_STAGING_FAILED`

`PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS` is expected when the active export-readiness artifact has no export-ready rows. It is planning context, not a failed export.

## Research Status

`research-status` includes the latest `pit-universe-export-staging-status` as PIT universe export-preparation context.

The unified summary records:

- latest staging id
- staging status and stage
- health status
- linked export-readiness id
- linked review id
- export-ready input count
- staged row count
- blocked count
- diagnostic-source flag
- no-ready-row flag
- report path
- next manual action

Staging context does not mean a universe export happened. Later current-candidates, advisory, market-update handoff, or paper workflow artifacts keep final workflow priority, while staging fields remain visible for audit.

## Blockers

Staging is blocked when:

- the source is under `manual_diagnostics` and `--allow-diagnostic-source` is not set
- no rows have `export_ready=true`
- duplicate `signal_date + symbol + universe_name` keys exist among staged rows
- required universe columns are missing
- PIT dates are invalid
- export-readiness metadata indicates unsafe writes or workflow execution

## Safety Boundaries

The workflow records:

- `would_write_data_raw=false`
- `would_write_data_processed=false`
- `no_data_raw_write=true`
- `no_data_processed_write=true`
- `no_current_candidates_generated=true`
- `no_snapshot_built=true`
- `no_forward_labels=true`
- `cache_mutated=false`
- `network_api_called=false`
- `external_api_called=false`
- `llm_api_called=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`
- `staging_only=true`

Staging does not validate strategy performance and does not authorize trading, broker use, message delivery, candidate generation, snapshot construction, or data writes outside `outputs/reports`.

## Known Limitations

- It does not accept or export staged previews into `data/raw`.
- It does not build snapshot manifests from staged previews.
- It does not repair missing PIT evidence.
