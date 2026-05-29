# Reviewed PIT Universe Overlay Approval Workflow v0.1

`pit-universe-overlay-review` applies local reviewer updates to a point-in-time universe overlay plan/template.

It is review-only. It does not write usable universe input files under `data/raw` or `data/processed`, run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

`pit-universe-overlay-plan` creates rows that are intentionally not valid for execution:

```text
PIT overlay plan/template
-> reviewer-supplied local update CSV
-> pit-universe-overlay-review
-> reviewed approval artifacts
-> later snapshot preparation planning
```

The review workflow validates whether a row has enough point-in-time evidence to be marked `APPROVED_FOR_PIT_UNIVERSE`. Approval remains evidence metadata only; it does not create a snapshot-ready universe dataset by itself.

## CLI Usage

Template-only mode:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review --overlay-plan outputs\reports\point_in_time_universe_overlay_plan\38a254c54024\point_in_time_universe_overlay_plan.csv --write-review-template-only
```

Apply local review updates:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review --overlay-plan outputs\reports\point_in_time_universe_overlay_plan\38a254c54024\point_in_time_universe_overlay_plan.csv --review-updates outputs\reports\manual_diagnostics\pit_universe_overlay_review_updates.csv
```

Optional:

- `--output-dir`: destination root for review artifacts.

## Review Keys

Review updates merge onto the overlay plan by:

- `signal_date`
- `symbol`
- `universe_name`

Symbols are preserved as strings, so `000001` remains `000001`.

## Status Values

Allowed review statuses:

- `NEEDS_MANUAL_REVIEW`
- `APPROVED_FOR_PIT_UNIVERSE`
- `REJECTED`
- `NEEDS_MORE_EVIDENCE`

Invalid statuses are rejected.

## Approval Requirements

`APPROVED_FOR_PIT_UNIVERSE` requires:

- `include_flag=true`
- `reviewer`
- `reviewed_at`
- `review_reason`
- `evidence_source`
- `evidence_path` or `evidence_reference`
- `listed_date_evidence`
- `is_active_evidence=true`
- `survivorship_bias_resolved=true`
- `proposed_as_of_date <= signal_date`
- `proposed_available_time <= signal_date` decision time
- `listed_date_evidence <= signal_date`
- `delisted_date_evidence` blank or on/after `signal_date`

Rows that fail approval checks are not silently approved. They are downgraded to `NEEDS_MORE_EVIDENCE` with a `blocker_reason`.

## Artifacts

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_overlay_review/<review_id>/
```

Files:

- `reviewed_pit_universe_overlay.csv`
- `pit_universe_overlay_review_template.csv`
- `pit_universe_overlay_review_report.md`
- `metadata.json`

The reviewed CSV includes:

- review id and source overlay plan id
- signal date, symbol, and universe name
- review status and validity fields
- reviewer and evidence fields
- listed/delisted/active evidence fields
- survivorship-bias warning and resolution fields
- local-only safety flags

## Index, Health, And Status

Use `pit-universe-overlay-review-index` to discover local reviewed PIT universe overlay artifacts:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review-index
```

The index writes:

```text
outputs/reports/point_in_time_universe_overlay_review/index/
  pit_universe_overlay_review_index.csv
  pit_universe_overlay_review_index_report.md
  metadata.json
```

Index rows include review id, source overlay plan id, row counts, approved/rejected/needs-more-evidence counts, valid-for-signal-date count, unresolved survivorship-warning count, missing-evidence count, local-only safety flags, report path, reviewed CSV path, template path, metadata path, and creation time.

Use `pit-universe-overlay-review-health` to verify artifact completeness and approval safety:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review-health
```

Health checks verify approved rows have reviewer identity, review time, evidence source, evidence path or reference, resolved survivorship-bias status, and `valid_for_signal_date=true`. Health also verifies `no_live_trading=true`, `no_broker_api=true`, `no_order_placement=true`, `no_message_sent=true`, `review_only=true`, and metadata does not indicate current-candidates generation, snapshot building, forward-return computation, cache mutation, network/API calls, LLM calls, message delivery, broker access, or order placement.

Use `pit-universe-overlay-review-status` to summarize the latest review:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review-status
```

Expected stages include:

- `NO_PIT_UNIVERSE_OVERLAY_REVIEWS`
- `PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE`
- `PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS`
- `PIT_UNIVERSE_OVERLAY_REVIEW_ALL_APPROVED`
- `PIT_UNIVERSE_OVERLAY_REVIEW_HEALTH_WARN`
- `PIT_UNIVERSE_OVERLAY_REVIEW_FAILED`

Approved rows are evidence context only. They do not mean current-candidates were generated, snapshots were built, forward labels were computed, or trading actions were approved.

## Research-Status Integration

`research-status` includes the latest `pit-universe-overlay-review-status` as PIT universe preparation context.

The unified dashboard exposes latest review id, status/stage, health status, approved count, valid-for-signal-date count, needs-more-evidence count, unresolved survivorship-warning count, report path, and next manual action.

`PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE` is visible and reviewable, but it is not a strategy failure or candidate-generation failure. `PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS` means some rows have reviewed PIT evidence; it still does not export usable universe files or start snapshot preparation.

If a later paper workflow is already active, unified `research-status` preserves that later workflow priority while keeping review fields visible for audit.

## Safety Boundaries

The workflow always records:

- `current_candidates_executed=false`
- `data_pipeline_executed=false`
- `snapshot_manifest_built=false`
- `forward_returns_computed=false`
- `cache_mutated=false`
- `network_api_called=false`
- `external_api_called=false`
- `llm_api_called=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`
- `review_only=true`

Approved rows are not trading recommendations and do not authorize candidate generation, snapshot construction, paper approval, live trading, broker use, order placement, or message delivery.

## Known Limitations

- The workflow does not export approved rows into `data/raw`.
- It does not build per-date snapshot manifests.
- It does not prove strategy performance or market edge.
- Approval artifacts do not yet feed a snapshot-preparation workflow.
