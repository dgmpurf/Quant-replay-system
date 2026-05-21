# Walk-Forward Validation v0.1

Walk-forward validation enforces explicit train, validation, and optional test date splits around Parameter Calibration.

It does not change point-in-time filtering, trading calendar logic, T+1 execution rules, technical indicators, scoring formulas, batch replay behavior, or portfolio simulation math. It only controls which dates are used to select parameters and which dates are used to evaluate the selected parameter set out of sample.

## Why Walk-Forward Validation Matters

Calibration can make a parameter set look strong on the same dates used to choose it.

Walk-forward validation reduces that risk by separating:

- train dates used to compare candidate parameter sets,
- validation dates used to test the selected parameter set out of sample,
- optional test dates used for a final holdout check.

The MVP goal is not to prove future performance. The goal is to make overfitting easier to see before a parameter set is promoted to later replay, reporting, or paper-trading workflows.

## Train, Validation, And Test Split

MVP v0.1 supports explicit split mode:

```python
run_walk_forward_validation(
    train_dates=["2024-03-01", "2024-03-04", "2024-03-05"],
    validation_dates=["2024-03-07"],
    test_dates=["2024-03-08"],
    universe_name="etf_core",
    parameter_sets=parameter_sets,
)
```

The split dates must be disjoint. Minimum split sizes are controlled by config:

```yaml
walk_forward:
  require_validation: true
  require_test: false
  min_train_dates: 3
  min_validation_dates: 1
  min_test_dates: 0
```

Rolling windows are not implemented yet.

## Relationship To Parameter Calibration

Walk-forward validation calls `run_parameter_calibration(...)` on train dates first.

Then it:

1. selects the best parameter set from train calibration,
2. evaluates only that parameter set on validation dates,
3. evaluates the same selected parameter set on test dates when provided,
4. compares in-sample and out-of-sample metrics.

Calibration still calls Batch Replay, and Batch Replay still calls the single-date replay orchestrator. Existing point-in-time and replay contracts remain in force.

## In-Sample Vs Out-Of-Sample Comparison

The report compares selected-parameter performance across train and validation splits:

- objective score,
- average return,
- portfolio total return when available,
- max drawdown when available,
- trade count.

If portfolio-aware calibration is enabled, the selected parameter set is still evaluated through the portfolio-aware ranking fields produced by calibration.

## Overfitting Risk Diagnostics

The MVP diagnostic formula is simple and explainable:

```text
overfit_risk_score =
  0.40 * normalized_objective_decay
+ 0.25 * normalized_return_decay
+ 0.20 * normalized_drawdown_worsening
+ 0.15 * low_trade_count_penalty
```

The output also includes:

- `objective_decay`,
- `return_decay`,
- `drawdown_worsening`,
- `low_trade_count_penalty`,
- `overfit_risk_label`.

Risk labels are:

- `LOW`
- `MEDIUM`
- `HIGH`
- `SEVERE`

Thresholds are configurable:

```yaml
walk_forward:
  overfit_warning_threshold: 0.50
  severe_overfit_threshold: 0.75
```

These diagnostics are heuristics. They are not statistical proof that a strategy is robust.

## Artifact Outputs

Default output path:

```text
outputs/reports/walk_forward/<walk_forward_id>/
  walk_forward_report.md
  diagnostics.csv
  selected_parameter_set.json
  train_summary.csv
  validation_summary.csv
  test_summary.csv
  metadata.json
```

`walk_forward_report.md` contains the split summary, selected parameter set, train performance, validation performance, optional test performance, diagnostics, warnings, and limitations.

`diagnostics.csv` contains one row of overfitting diagnostics.

`selected_parameter_set.json` records the selected parameter configuration.

`train_summary.csv`, `validation_summary.csv`, and optional `test_summary.csv` contain the selected parameter set's ranked calibration row for each split.

`metadata.json` records artifact paths, split dates, diagnostics, warnings, and live-trading safety metadata.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Supports explicit split mode only.
- Does not implement rolling or expanding windows yet.
- Diagnostics are heuristic and should be manually reviewed.
- Small validation sets can produce noisy risk labels.
- Objective scores depend on the existing calibration outputs.
- No live trading or broker API integration is implemented.
