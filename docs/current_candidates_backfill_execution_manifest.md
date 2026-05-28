# Current-Candidates Backfill Execution Manifest v0.1

`current-candidates-backfill-execution-manifest` turns a warmup-aware backfill plan into a reviewed execution-readiness manifest.

It is manifest-only. It does not run `current-candidates`, build snapshot manifests, run `data-pipeline`, compute forward returns, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The manifest answers:

```text
For each planned signal date, do the reviewed local inputs already exist and look point-in-time valid enough for a future human-reviewed current-candidates execution step?
```

The intended workflow is:

```text
current-candidates-backfill-plan
-> current-candidates-backfill-execution-manifest
-> human review of blocked/ready dates
-> later snapshot planning or candidate generation
```

The command deliberately stops before execution. A `READY_FOR_REVIEW` row is not generated candidates, not a paper approval, and not a trading recommendation.

## CLI Usage

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest --plan outputs\reports\current_candidates_backfill_plan\aadd86db24a1\current_candidates_backfill_plan.csv
```

Optional controls:

- `--snapshot-root`: existing data-pipeline artifact root containing `snapshot_manifest.json` files.
- `--snapshot-quality-root`: existing snapshot-quality artifact root.
- `--universe-root`: reviewed universe overlay root recorded for audit context.
- `--selection-profile`: optional manifest-level profile label.
- `--output-dir`: destination root for manifest artifacts.

## Readiness Checks

Each plan row is evaluated without executing downstream workflows.

Rows are blocked when:

- the plan row is not feasible (`BLOCKED_PLAN_INFEASIBLE`),
- no existing snapshot manifest is found (`BLOCKED_MISSING_SNAPSHOT`),
- snapshot quality is missing or not `PASS` (`BLOCKED_SNAPSHOT_QUALITY`),
- required market, universe, or trading-calendar datasets are missing (`BLOCKED_MISSING_INPUT`),
- the universe `as_of_date` or `available_time` is later than the signal date decision time (`BLOCKED_UNIVERSE_AS_OF`).

Rows become `READY_FOR_REVIEW` only when the plan is feasible, an existing snapshot is found, snapshot quality is `PASS`, required datasets are readable, the trading calendar contains the signal date, market rows exist for planned symbols, and the universe is point-in-time valid for the signal date.

## Artifacts

Artifacts are written under:

```text
outputs/reports/current_candidates_backfill_execution_manifest/<execution_manifest_id>/
```

Files:

- `current_candidates_backfill_execution_manifest.csv`
- `current_candidates_backfill_execution_manifest_report.md`
- `metadata.json`

The CSV includes:

- `execution_manifest_id`
- `plan_id`
- `signal_date`
- `universe`
- `selection_profile`
- plan feasibility and forward-horizon flags
- snapshot manifest and snapshot-quality status
- market, universe, and trading-calendar paths
- universe point-in-time validity fields
- source/upstream guidance
- `readiness_status`
- `blocker_reason`
- safety flags

## Index, Health, And Status

Use `current-candidates-backfill-execution-manifest-index` to discover local execution manifest artifacts:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest-index
```

The index scans `outputs/reports/current_candidates_backfill_execution_manifest/` and writes:

```text
outputs/reports/current_candidates_backfill_execution_manifest/index/
  current_candidates_backfill_execution_manifest_index.csv
  current_candidates_backfill_execution_manifest_index_report.md
  metadata.json
```

Index rows include execution manifest id, linked plan id, row counts, readiness/blocker counts, safety flags, report path, manifest CSV path, metadata path, and created time when available.

Use `current-candidates-backfill-execution-manifest-health` to verify artifact completeness and safety:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest-health
```

Health checks verify:

- `metadata.json` is readable,
- `current_candidates_backfill_execution_manifest.csv` exists and has the required columns,
- `current_candidates_backfill_execution_manifest_report.md` exists,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_order_placement=true`,
- `no_message_sent=true`,
- `plan_only=true`,
- metadata does not indicate current-candidates generation, snapshot building, data-pipeline execution, forward-return computation, cache mutation, network/API calls, LLM calls, message delivery, broker access, or order placement,
- blocked rows include `blocker_reason`.

Use `current-candidates-backfill-execution-manifest-status` to summarize the latest manifest:

```cmd
python -m quant_replay_system.cli current-candidates-backfill-execution-manifest-status
```

Expected stages include:

- `NO_CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST`
- `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW`
- `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED`
- `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_HEALTH_WARN`
- `CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_FAILED`

`CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED` is expected when reviewed inputs are not ready, such as missing per-date snapshot manifests or a universe `as_of_date` later than the signal date. It is a planning/readiness blocker only; no candidate generation has run.

## Research Status Integration

`research-status` includes the latest `current-candidates-backfill-execution-manifest-status` as multi-date candidate execution-readiness context.

The unified dashboard exports fields for the latest execution manifest id, linked plan id, status/stage, health status, row count, ready count, blocked count, blocker counts, report path, and next manual action. A blocked manifest remains visible as a planning blocker, not as a strategy failure, paper workflow failure, or failed current-candidates run.

If later workflow artifacts already exist, especially paper workflow status, those later stages keep priority for the final `workflow_stage`. Execution manifest fields remain visible for audit while the next manual action can stay on the later paper workflow path.

## Safety Boundaries

The manifest always records:

- `current_candidates_executed=false`
- `data_pipeline_executed=false`
- `snapshot_manifest_built=false`
- `forward_returns_computed=false`
- `cache_mutated=false`
- `network_api_called=false`
- `external_api_called=false`
- `llm_api_called=false`
- `reviewed_execution_required=true`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_order_placement=true`
- `no_message_sent=true`
- `plan_only=true`

## Known Limitations

- It checks existing snapshot artifacts only; it does not create missing per-date snapshots.
- It uses snapshot quality metadata that already exists; it does not run snapshot-quality.
- It does not decide which blocked rows should be fixed first.
- It does not compute forward-return labels or validate strategy performance.
- A ready row still requires human review and a separate later execution step.
