# Parameter Calibration v0.1

Parameter Calibration compares explicit, explainable parameter sets by running Batch Replay for each set.

It does not change point-in-time filtering, trading calendar logic, T+1 execution rules, indicator formulas, or the score formula. It only changes configuration values such as score weights, candidate thresholds, `top_n`, and holding horizon.

## Purpose

Calibration helps answer:

- Which score-weight mix is more stable?
- Which candidate threshold produces enough trades without over-trading?
- Which holding horizon behaves more consistently?
- Which configuration deserves deeper manual review?

The MVP goal is not to maximize historical return at all costs. The goal is stable, explainable comparison.

## Avoiding Overfitting

Historical replay can tempt a system into choosing the best-looking backtest. This project treats calibration as a research aid, not a profit guarantee.

Good calibration practice:

- use small parameter grids,
- compare stability and risk penalties, not only average return,
- keep point-in-time data rules unchanged,
- record skipped and failed dates,
- preserve train, validation, and test split metadata,
- review the selected configuration manually before using it in later workflows.

## Parameter Grid Design

A parameter set can include:

- scoring weights for reality, technical, expectation, liquidity, sentiment, and risk penalty,
- `min_final_score`,
- `min_action`,
- `top_n`,
- `holding_horizon`,
- `skip_non_trading_days`,
- `fail_fast`.

Example small grid:

```python
top_n = [3, 5, 10]
holding_horizon = [3, 5, 10]
min_final_score = [60, 70, 80]
weights = ["baseline", "technical_heavy", "risk_heavy", "liquidity_heavy"]
```

For MVP, keep the active grid smaller than the full Cartesian product unless there is a clear reason to run more combinations.

## Objective Score

The MVP objective score is explainable:

```text
objective_score =
  0.35 * normalized_average_return
+ 0.20 * normalized_win_rate
+ 0.15 * normalized_average_excess_return
- 0.15 * normalized_worst_return_penalty
- 0.10 * normalized_variance_penalty
- 0.05 * low_trade_count_penalty
```

If benchmark or excess return is unavailable, the missing component is treated neutrally so calibration can still rank results.

Penalties are included because stable candidate behavior matters more than a lucky high-return sample.

## Train, Validation, Test Metadata

Calibration v0.1 records:

- `split_name`
- `train_dates`
- `validation_dates`
- `test_dates`

MVP does not yet enforce walk-forward training. These fields prepare the system for stricter validation later.

## Relationship To Batch Replay

Calibration calls `run_batch_replay(...)` once per parameter set.

Batch Replay still calls the single-date replay orchestrator, so the existing replay contracts remain in force:

- point-in-time data filtering,
- universe eligibility,
- scoring,
- candidate selection,
- T+1 execution simulation,
- report generation.

## Artifact Outputs

Default calibration output path:

```text
outputs/reports/calibrations/<calibration_id>/
  calibration_report.md
  ranked_results.csv
  parameter_sets.csv
  batch_runs.csv
  aggregate_metrics.csv
  metadata.json
```

`ranked_results.csv` contains objective scores and ranking metrics.

`parameter_sets.csv` records each parameter configuration.

`batch_runs.csv` links each parameter set to its batch replay artifacts.

`aggregate_metrics.csv` contains the metrics used for ranking.

`metadata.json` records the calibration ID, split metadata, best parameter set, output files, warnings, and known limitations.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not implement machine learning.
- Does not optimize large search spaces.
- Does not enforce walk-forward validation yet.
- Does not include portfolio cash accounting or position sizing.
- Objective score is a review aid, not a direct trading instruction.
- No live trading or broker API integration is implemented.
