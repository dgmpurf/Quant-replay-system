# Personal MVP Daily Advisory Review

Personal MVP Daily Advisory Review is a local, report-only surface for personal/family daily advisory review. It aggregates existing local advisory context into a compact human review packet without creating new recommendations, approvals, broker actions, replay inputs, labels, training data, model artifacts, stock profiles, paper approvals, performance validation, or trading authority.

## Commands

Create a daily review packet:

```cmd
python -m quant_replay_system.cli personal-mvp-daily-advisory-review --root outputs\reports --review-date 2024-05-20
```

Discover, safety-check, and summarize generated packets:

```cmd
python -m quant_replay_system.cli personal-mvp-daily-advisory-review-index --root outputs\reports\personal_mvp_daily_advisory_review
python -m quant_replay_system.cli personal-mvp-daily-advisory-review-health --root outputs\reports\personal_mvp_daily_advisory_review
python -m quant_replay_system.cli personal-mvp-daily-advisory-review-status --root outputs\reports\personal_mvp_daily_advisory_review
```

`research-status` exposes the latest daily advisory review context when status artifacts exist, while preserving later `PAPER_WORKFLOW_READY` priority.

## Artifact Roots

Default core output root:

```text
outputs/reports/personal_mvp_daily_advisory_review/<daily_review_run_id>/
```

Default status output root:

```text
outputs/reports/personal_mvp_daily_advisory_review/status/
```

Generated daily review artifacts include:

- `metadata.json`
- `daily_advisory_review_report.md`
- `daily_advisory_review_rows.csv`
- `daily_advisory_review_summary.csv`
- `single_symbol_drilldown_index.csv`
- `manual_review_checklist.csv`
- `safety_flags.json`

Artifact views generate index, health, and status files under sibling `index/`, `health/`, and `status/` folders.

## Status Semantics

Expected core statuses include:

- `DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW`
- `DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT`
- `DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED`
- `DAILY_ADVISORY_REVIEW_BLOCKED_CONTEXT_REVIEW_REQUIRED`
- `DAILY_ADVISORY_REVIEW_DEMO_ONLY_CONTEXT`
- `DAILY_ADVISORY_REVIEW_FAILED_SAFETY_CHECK`

The status command may emit `DAILY_ADVISORY_REVIEW_NO_ARTIFACT` when no daily review artifact has been generated.

These statuses are local review-context statuses only. They are not global paper approval, real buy-review eligibility, replay readiness, strategy-performance validation, or trading permission.

## Report-Only Boundary

This workflow is:

- report-only;
- diagnostic-only;
- local-only;
- manual-confirmation-required.

It can read existing local report artifacts for review context. It must not run upstream workflows or create downstream authority.

The workflow does not:

- create real buy-review eligibility;
- set `buy_review_allowed=true`;
- authorize trading;
- call brokers, place orders, or send messages;
- create active replay input;
- run replay execution;
- create replay decisions or replay evidence bundles;
- create forward labels;
- join future labels to decision-time inputs;
- create training or evaluation datasets;
- compute metrics;
- train models;
- create active weights or active thresholds;
- create stock_profile validation;
- expand paper workflow authority;
- validate strategy performance;
- run current-candidates;
- build snapshots;
- mutate `signal_semantics`;
- write `data/raw`, `data/processed`, or `data/cache`.

## Safety Fields

The daily review artifacts carry negative proof fields that must remain false:

- `real_buy_review_approved`
- `buy_review_allowed`
- `trading_allowed`
- `broker_api_called`
- `broker_api_approved`
- `order_placed`
- `order_placement_approved`
- `message_sent`
- `message_delivery_approved`
- `external_api_called`
- `llm_api_called`
- `active_replay_input_created`
- `active_replay_input_approved`
- `real_replay_execution_approved`
- `current_candidates_run`
- `snapshot_built`
- `signal_semantics_mutated`
- `labels_created`
- `training_dataset_created`
- `model_training_performed`
- `stock_profile_created`
- `strategy_performance_validated`
- `data_raw_written`
- `data_processed_written`
- `data_cache_written`

The required positive context fields are:

- `report_only=true`
- `diagnostic_only=true`
- `local_only=true`
- `manual_confirmation_required=true`

## Research-Status Integration

`research-status` may expose:

- latest daily review run id;
- latest daily review status, health status, and workflow stage;
- report path;
- row count and review-bucket counts;
- manual-confirmation flag;
- report-only, diagnostic-only, and local-only flags;
- safety fields;
- recommended next task.

`research-status` must not present the daily review as a paper approval, buy-review approval, strategy-performance validation, active replay input, current-candidates integration, snapshot integration, broker integration, order placement, message delivery, or trading readiness.

When later paper workflow context exists, the final top-level workflow stage must remain `PAPER_WORKFLOW_READY`; daily advisory review fields remain visible as context only.

## Human Review Policy

The daily review packet is meant to reduce artifact sprawl for a human reviewer. Labels such as `WATCH`, `REVIEW_BUY_CANDIDATE`, `REVIEW_SELL_CANDIDATE`, `HOLD_REVIEW`, `NO_ACTION`, `BLOCKED`, and `NOT_FOUND` are review buckets only. They must not be rendered as commands to buy, sell, hold, place orders, send messages, or connect to brokers.

## Known Limitations

- It depends on existing local artifacts.
- It does not create source evidence or validate PIT admissibility.
- It does not solve stale or blocked upstream artifacts.
- It does not replace single-symbol drill-down, paper workflow review, or human confirmation.
- It does not create Project Source files, checkpoint tags, or runtime authority.
