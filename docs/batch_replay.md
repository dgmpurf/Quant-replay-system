# Batch Replay v0.1

Batch Replay runs the existing single-date `run_replay(...)` workflow across a list of historical decision dates and writes a batch-level audit trail.

It does not change point-in-time filtering, trading calendar rules, T+1 execution, technical indicator formulas, or scoring formulas. It only coordinates repeated replay runs and aggregates their outputs.

## Purpose

Single replay runs answer: "What would the system have selected on this one decision date?"

Batch replay answers: "How did the same rules behave across many decision dates?"

This is the bridge between one-off research checks and future parameter calibration.

## Input Decision Dates

The caller supplies a list of decision dates. Each date is normalized to a daily decision date.

Default behavior:

- Trading days are executed.
- Non-trading days are skipped with reason `NON_TRADING_DAY`.
- A failed date is recorded with reason `RUN_FAILED`.
- Remaining dates continue unless `fail_fast` is enabled.

Batch replay uses the existing trading calendar. It does not infer exchange holidays without calendar data.

## Relationship To `run_replay`

For each executable decision date, batch replay calls `run_replay(...)`.

Each single replay still:

- builds the point-in-time factor dataset,
- scores candidates,
- selects candidates,
- simulates T+1 buy execution,
- simulates planned exit by trading-day holding horizon,
- writes replay-level artifacts.

Batch replay then collects those `ReplayRunResult` objects and writes batch-level artifacts.

## Artifact Directory Structure

Default batch output path:

```text
outputs/reports/batch_replays/<batch_id>/
  batch_report.md
  batch_index.csv
  aggregate_performance.csv
  replay_runs.csv
  skipped_dates.csv
  metadata.json
```

The `batch_id` is deterministic for the same:

- decision dates,
- universe name,
- top N,
- holding horizon,
- config version.

## Batch Files

`batch_report.md` is the human-readable batch summary.

`batch_index.csv` has one row per successful replay run, including report paths, candidate paths, trade paths, candidate counts, buy counts, return fields, status, and warning count.

`aggregate_performance.csv` contains one row of batch-level performance statistics.

`replay_runs.csv` contains flattened replay metadata such as decision date, run ID, row counts, report path, and warning count.

`skipped_dates.csv` records skipped and failed dates with:

- `decision_date`
- `reason`
- `detail`

`metadata.json` records the batch ID, config summary, requested/executed/skipped dates, output files, warnings, and known limitations.

## Aggregate Performance Fields

Batch replay reports:

- number of requested dates,
- number of executed dates,
- number of skipped dates,
- number of failed dates,
- total candidates,
- total simulated trades,
- total skipped trades,
- average return,
- median return,
- win rate,
- best return,
- worst return,
- average equal-weight return by run,
- average benchmark return when available,
- average excess return when available.

Trade-level return statistics are computed from simulated trades that have valid `trade_return` values.

## Preparation For Calibration

Batch Replay v0.1 gives later calibration modules a stable set of inputs:

- repeatable per-date replay outputs,
- batch-level summary files,
- deterministic artifact naming,
- skipped-date accounting,
- auditable metadata.

Parameter calibration can later compare many batch runs without changing the underlying replay contract.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not place live orders or call broker APIs.
- Does not do portfolio cash accounting or position sizing.
- Does not optimize or calibrate parameters yet.
- Failed replay dates are recorded, but automatic repair is not attempted.
- Results depend on the completeness of the supplied trading calendar and market data.
