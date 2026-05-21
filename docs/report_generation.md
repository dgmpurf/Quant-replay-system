# Report Generation v0.1

Report Generation v0.1 hardens replay artifacts so a single replay run leaves behind stable, auditable files that can later support batch replay and parameter calibration.

## Artifact Directory Structure

By default, each replay run writes to:

```text
outputs/reports/replay_runs/<decision_date>_<universe_name>_<run_id>/
```

Inside the folder:

```text
report.md
factor_dataset.csv
scored_dataset.csv
candidates.csv
simulated_trades.csv
performance_summary.csv
metadata.json
```

If a legacy explicit markdown path is passed to `run_replay(..., report_output_path="...md")`, artifacts are written next to that markdown file for backward compatibility.

## Stable Naming Rules

If `run_id` is not supplied, the system generates a deterministic short hash from:

- `decision_date`
- `universe_name`
- `top_n`
- `holding_horizon`
- `config_version`

This keeps artifact naming stable for the same replay parameters.

## Markdown Report Contents

`report.md` includes:

- Replay metadata
- Config summary
- Data audit summary
- Universe/factor/scored/candidate/trade row counts
- Candidate table
- Score breakdown
- Simulated trade table
- Skipped and blocked trades
- Performance summary
- Warnings
- Known MVP limitations

## CSV Export Purpose

CSV exports make replay runs inspectable outside Python:

- `factor_dataset.csv`: point-in-time factor table
- `scored_dataset.csv`: factor table plus component scores and actions
- `candidates.csv`: selected candidates with rank and explanation fields
- `simulated_trades.csv`: simulated buy/sell/skip outcomes
- `performance_summary.csv`: one-row summary of replay performance

Structured columns such as score breakdowns and sell attempts are JSON-encoded rather than exported as Python object repr strings.

## metadata.json Fields

`metadata.json` includes:

- `decision_date`
- `decision_time`
- `universe_name`
- `top_n`
- `holding_horizon`
- `run_id`
- `created_at`
- `config_summary`
- `row_counts`
- `output_files`
- `warnings`
- `known_limitations`
- `audit_metadata`

## How This Prepares for Batch Replay

Batch replay can later run many decision dates and collect each run folder. The deterministic folder structure and CSV exports make it easier to aggregate:

- candidate history,
- trade outcomes,
- score distributions,
- parameter versions,
- skipped trade reasons,
- benchmark/excess returns.

## Known MVP Limitations

- Reports are markdown and CSV only.
- No HTML dashboard yet.
- No batch aggregation index yet.
- No portfolio ledger, cash accounting, or sizing report yet.
- `created_at` changes each time artifacts are regenerated, even when `run_id` is deterministic.
