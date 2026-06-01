# PIT Universe Overlay Export Readiness v0.1

`pit-universe-overlay-export-readiness` checks whether reviewed PIT universe overlay rows are ready for a later explicit universe export workflow.

It is readiness-only. It does not write usable universe files under `data/raw` or `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The reviewed PIT universe overlay workflow can approve rows as evidence artifacts. Export readiness is the next safety gate:

```text
pit-universe-overlay-review
-> pit-universe-overlay-export-readiness
-> later explicit universe export workflow
-> later snapshot preparation planning
```

This command answers:

```text
Are any reviewed PIT universe rows complete enough to be considered for a later reviewed export?
```

It does not perform that export.

## CLI Usage

```cmd
python -m quant_replay_system.cli pit-universe-overlay-export-readiness --review outputs\reports\point_in_time_universe_overlay_review\7bc8ba08bf5a\reviewed_pit_universe_overlay.csv
```

Optional:

- `--output-dir`: destination root for readiness artifacts.

## Export Readiness Rules

A row can be `export_ready=true` only when all of these are true:

- `review_status=APPROVED_FOR_PIT_UNIVERSE`
- `valid_for_signal_date=true`
- `include_flag=true`
- `survivorship_bias_resolved=true`
- reviewer and `reviewed_at` are present
- `evidence_source` is present
- `evidence_path` or `evidence_reference` is present
- unresolved survivorship warning is absent
- `listed_date <= signal_date` when `listed_date` is present
- `delisted_date` is blank or on/after `signal_date`
- all required current-candidates universe output fields are present or already mapped in the reviewed artifact

Required current-candidates universe fields:

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

These fields are expected to come from reviewer-provided metadata in reviewed PIT overlay rows. Non-authoritative helper hints are ignored for completeness checks.

Duplicate `signal_date + symbol + universe_name` keys among otherwise export-ready rows are blocked.

## Status Values

Aggregate readiness statuses:

- `EXPORT_BLOCKED_NO_APPROVED_ROWS`
- `EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE`
- `EXPORT_BLOCKED_UNRESOLVED_SURVIVORSHIP`
- `EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS`
- `EXPORT_BLOCKED_INVALID_PIT_DATES`
- `EXPORT_READY_FOR_DRY_RUN`
- `EXPORT_READY_REVIEW_ONLY`

For the current template-only review, `EXPORT_BLOCKED_NO_APPROVED_ROWS` is expected and safe.

If at least one row is `export_ready=true` but some rows are still blocked, the aggregate status is `EXPORT_READY_REVIEW_ONLY`.
This is treated as passable readiness-check context (reviewable), not a hard process failure, and appears in status as `PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN`.

## Artifacts

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_overlay_export_readiness/<export_readiness_id>/
```

Files:

- `pit_universe_overlay_export_readiness.csv`
- `pit_universe_overlay_export_readiness_report.md`
- `metadata.json`

The readiness CSV includes:

- review id, signal date, symbol, and universe name
- review status and `valid_for_signal_date`
- `export_ready`
- readiness status and blocker reason
- missing required universe-column counts
- reviewer/evidence fields
- survivorship warning/resolution fields
- local-only safety flags

## Index, Health, And Status

Use `pit-universe-overlay-export-readiness-index` to discover local readiness artifacts:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-export-readiness-index
```

The index writes:

```text
outputs/reports/point_in_time_universe_overlay_export_readiness/index/
  pit_universe_overlay_export_readiness_index.csv
  pit_universe_overlay_export_readiness_index_report.md
  metadata.json
```

Index rows include export-readiness id, source review id, row counts, approved/export-ready/blocked counts, no-approved-rows state, unresolved survivorship-warning count, missing required-column count, duplicate-key count, report path, readiness CSV path, metadata path, and local-only safety flags.

Use `pit-universe-overlay-export-readiness-health` to verify readiness artifact completeness and safety:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-export-readiness-health
```

Health verifies metadata, readiness CSV, report path, required columns, no `data/raw` or `data/processed` write, no current-candidates generation, no snapshot build, no forward labels, and no live trading, broker API, order placement, or message delivery. `no_approved_rows=true` is valid blocked-readiness context and does not fail health by itself.

Use `pit-universe-overlay-export-readiness-status` to summarize the latest readiness run:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-export-readiness-status
```

Expected stages include:

- `NO_PIT_UNIVERSE_EXPORT_READINESS`
- `PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS`
- `PIT_UNIVERSE_EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE`
- `PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN`
- `PIT_UNIVERSE_EXPORT_READINESS_HEALTH_WARN`
- `PIT_UNIVERSE_EXPORT_READINESS_FAILED`

## Research-Status Integration

`research-status` includes the latest `pit-universe-overlay-export-readiness-status` as PIT universe preparation context.

The unified dashboard exposes latest export-readiness id, status/stage, health status, linked review id, approved count, export-ready count, blocked count, no-approved-rows flag, missing required-column count, unresolved survivorship-warning count, report path, and next manual action.

Blocked readiness, including `PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS`, is visible and reviewable. It is not a candidate-generation failure and does not mean a universe export was attempted. If a later paper workflow is already active, unified `research-status` preserves that later workflow priority while keeping export-readiness fields visible for audit.

## Safety Boundaries

The workflow always records:

- `universe_exported=false`
- `would_write_data_raw=false`
- `would_write_data_processed=false`
 - `no_current_candidates_generated=true`
 - `universe_exported=false`
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
- `export_readiness_only=true`

Export readiness is not strategy validation and does not authorize candidate generation, snapshot construction, paper approval, live trading, broker use, order placement, or message delivery.

## Known Limitations

- It does not export approved rows into `data/raw` or `data/processed`.
- It does not build per-date snapshot manifests.
- It does not fill missing universe fields from a base universe automatically.
- It does not prove strategy performance or market edge.
- A later explicit reviewed export workflow is still required before snapshot preparation can consume approved rows.

If readiness is blocked because rows are not approved or evidence fields are missing, use [point_in_time_universe_evidence_completion_helper.md](point_in_time_universe_evidence_completion_helper.md) to generate a report-only completion template. That helper may prefill non-authoritative `suggested_*` hints from a local base universe, but it does not approve rows or export usable universe files.
