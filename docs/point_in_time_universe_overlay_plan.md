# Point-in-Time Universe Overlay Plan v0.1

`pit-universe-overlay-plan` creates a local manual-review template for point-in-time universe overlays from blocked multi-date current-candidates execution manifest rows.

It is plan/template-only. It does not run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward returns, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The current-candidates backfill execution manifest can identify signal dates blocked because the available universe artifact is too late for the signal date, for example:

```text
BLOCKED_UNIVERSE_AS_OF
```

This command turns those blocked rows into a reviewed overlay template:

```text
current-candidates-backfill-execution-manifest
-> pit-universe-overlay-plan
-> manual point-in-time universe review
-> later snapshot preparation
```

A generated row is not point-in-time valid by default. It remains `NEEDS_MANUAL_REVIEW` until a human reviewer supplies evidence and approves the row in a later workflow.

## CLI Usage

```cmd
python -m quant_replay_system.cli pit-universe-overlay-plan --execution-manifest outputs\reports\current_candidates_backfill_execution_manifest\f98279630ce6\current_candidates_backfill_execution_manifest.csv --universe-name etf_core
```

Optional controls:

- `--base-universe`: use a specific local universe CSV as the template source. If omitted, the command first looks for the latest local `data/raw/LOCAL_CSV/universe_overlay/**/raw_data.csv`, then falls back to the universe dataset path recorded in each blocked manifest row.
- `--allow-template-include`: prefill `include_flag=true` in the template. This still does not make rows valid for execution.
- `--output-dir`: destination root for plan artifacts.

## Template Behavior

The planner reads execution manifest rows with `readiness_status=BLOCKED_UNIVERSE_AS_OF`.

For each blocked signal date, it builds symbol/date template rows from the base universe. When the execution manifest sits beside metadata that links back to the source backfill plan, the template is scoped to the plan's `symbols` for each signal date. Otherwise, when the execution manifest has a readable market dataset, the template is scoped to market symbols present on that signal date; if neither source is available, it falls back to the base universe symbols.

Every generated row defaults to:

- `review_status=NEEDS_MANUAL_REVIEW`
- `manual_review_required=true`
- `include_flag` empty unless `--allow-template-include` is used
- `valid_for_signal_date=false`
- `survivorship_bias_warning=true` when the base universe `as_of_date` or `available_time` is later than the signal date decision time
- `plan_only=true`

The command proposes `proposed_as_of_date=<signal_date>` and `proposed_available_time=<signal_date> 08:00:00` as editable template values only. They are not evidence and do not approve the row.

## Artifacts

Artifacts are written under:

```text
outputs/reports/point_in_time_universe_overlay_plan/<overlay_plan_id>/
```

Files:

- `point_in_time_universe_overlay_plan.csv`
- `point_in_time_universe_overlay_template.csv`
- `point_in_time_universe_overlay_plan_report.md`
- `metadata.json`

The CSV includes:

- `overlay_plan_id`
- `signal_date`
- `symbol`
- `universe_name`
- `proposed_as_of_date`
- `proposed_available_time`
- `base_universe_path`
- `base_universe_as_of_date`
- `base_universe_available_time`
- `include_flag`
- `review_status`
- `review_reason`
- `source`
- `upstream_source`
- `survivorship_bias_warning`
- `manual_review_required`
- `valid_for_signal_date`
- `blocker_reason`
- local-only safety flags

## Index, Health, And Status

Use `pit-universe-overlay-plan-index` to discover local PIT universe overlay plan artifacts:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-plan-index
```

The index scans `outputs/reports/point_in_time_universe_overlay_plan/` and writes:

```text
outputs/reports/point_in_time_universe_overlay_plan/index/
  point_in_time_universe_overlay_plan_index.csv
  point_in_time_universe_overlay_plan_index_report.md
  metadata.json
```

Index rows include overlay plan id, row count, signal date count, symbol count, manual-review count, valid-for-signal-date count, survivorship-warning count, safety flags, report path, plan CSV path, template CSV path, and metadata path.

Use `pit-universe-overlay-plan-health` to verify artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-plan-health
```

Health checks verify:

- `metadata.json` is readable,
- plan CSV and template CSV exist and have required columns,
- report exists,
- `review_status` is present,
- `manual_review_required=true`,
- `include_flag=true` is not used before reviewed PIT-valid approval,
- future-universe-derived rows carry `survivorship_bias_warning=true`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_order_placement=true`,
- `no_message_sent=true`,
- `plan_only=true`,
- metadata does not indicate current-candidates generation, snapshot building, forward-return computation, cache mutation, network/API calls, LLM calls, message delivery, broker access, or order placement.

Use `pit-universe-overlay-plan-status` to summarize the latest plan:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-plan-status
```

Expected stages include:

- `NO_PIT_UNIVERSE_OVERLAY_PLAN`
- `PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW`
- `PIT_UNIVERSE_OVERLAY_PLAN_READY_FOR_REVIEW`
- `PIT_UNIVERSE_OVERLAY_PLAN_HEALTH_WARN`
- `PIT_UNIVERSE_OVERLAY_PLAN_FAILED`

`PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW` is expected for generated templates. It means the artifact is safe and discoverable, but rows are not valid for execution until manual point-in-time universe review is completed.

## Reviewed Approval Workflow

Use `pit-universe-overlay-review` to apply a reviewer-supplied local CSV to a PIT overlay plan/template:

```cmd
python -m quant_replay_system.cli pit-universe-overlay-review --overlay-plan outputs\reports\point_in_time_universe_overlay_plan\38a254c54024\point_in_time_universe_overlay_plan.csv --write-review-template-only
```

The review workflow merges updates by `signal_date`, `symbol`, and `universe_name`. `APPROVED_FOR_PIT_UNIVERSE` rows require reviewer identity, review time, review reason, evidence source/path or reference, listed-date evidence, active-status evidence, and explicit survivorship-bias resolution. Failed approval checks are downgraded to `NEEDS_MORE_EVIDENCE` with blocker reasons.

It writes reviewed evidence artifacts only. It does not write usable universe inputs under `data/raw` or `data/processed`, build snapshots, run `current-candidates`, compute labels, or place orders. Use `pit-universe-overlay-review-index`, `pit-universe-overlay-review-health`, and `pit-universe-overlay-review-status` to discover, safety-check, and summarize review artifacts. See [point_in_time_universe_overlay_review.md](point_in_time_universe_overlay_review.md).

## Research-Status Integration

`research-status` includes the latest `pit-universe-overlay-plan-status` as PIT universe preparation context.

The unified dashboard exposes:

- latest overlay plan id,
- status and workflow stage,
- health status,
- row, signal-date, and symbol counts,
- `NEEDS_MANUAL_REVIEW` count,
- valid-for-signal-date count,
- survivorship-bias warning count,
- report path,
- next manual action.

`PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW` is visible and reviewable, but it does not imply readiness for candidate generation. Rows with `NEEDS_MANUAL_REVIEW` are not valid PIT universe rows yet. Survivorship-bias warnings remain visible until a later reviewed approval workflow supplies explicit evidence.

If a later paper workflow is already active, unified `research-status` preserves that later workflow priority while keeping PIT universe overlay fields visible for audit.

## Safety Boundaries

The planner always records:

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

## Known Limitations

- It creates review templates only; it does not produce a valid PIT universe.
- It does not verify listing/delisting evidence.
- It does not create per-date snapshot manifests.
- It does not decide whether a future-universe-derived row should be included.
- It does not validate strategy performance.
