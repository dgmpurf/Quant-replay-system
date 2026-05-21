# Replay Run Orchestrator v0.1

Replay Run Orchestrator v0.1 connects the existing modules into one auditable historical replay workflow for a single decision date.

It does not implement live trading, broker integration, machine learning, or real market data ingestion.

## Purpose

The orchestrator answers one research question:

```text
Given a decision date, what candidates would the system have selected using only data available at that decision time, and how would the planned T+1 replay have performed?
```

## Full Replay Flow

For a decision date `T`, `run_replay(...)`:

1. Loads or receives local market data, universe snapshot data, benchmark data, and a trading calendar.
2. Builds a point-in-time factor dataset.
3. Scores every factor row with Score Engine v0.1.
4. Selects candidates with Candidate Selection v0.1.
5. Simulates T+1 buy execution through the existing execution module.
6. Simulates planned exit after the holding horizon in trading days.
7. Evaluates simple trade returns and benchmark/excess return when benchmark data is supplied.
8. Writes a markdown replay report.

## Inputs

Main function:

```python
run_replay(
    decision_date,
    universe_name="default",
    top_n=None,
    holding_horizon=None,
    config=None,
    market_data=None,
    universe_snapshot=None,
    benchmark_data=None,
    corporate_actions=None,
    trading_calendar=None,
    report_output_path=None,
)
```

If data frames are not supplied, the orchestrator uses the mock paths from `config/default.yaml`.

## Output

`run_replay(...)` returns `ReplayRunResult` with:

- `decision_date`
- `decision_time`
- `universe_name`
- `factor_dataset_row_count`
- `scored_dataset_row_count`
- `selected_candidates`
- `simulated_trades`
- `performance_summary`
- `report_path`
- `warnings`
- `audit_metadata`
- `factor_dataset`
- `scored_dataset`

## Point-in-Time Safety

The orchestrator does not implement its own data eligibility shortcut. It reuses:

- `build_factor_dataset(...)`
- `build_replay_dataset(...)`
- `filter_available_records(...)`
- `compute_technical_indicators(..., decision_time=...)`

Feature data follows:

```text
available_time <= decision_time
```

Future market rows after the decision date are used only for execution and performance measurement.

## Scoring and Candidate Selection

The orchestrator uses:

- `score_factor_dataset(...)`
- `select_candidates(...)`

Candidate outputs preserve:

- `symbol`
- `final_score`
- `action`
- component scores
- `score_reason`
- `score_breakdown`
- `risk_precheck_status`
- `risk_precheck_reason`

## T+1 Simulation

The orchestrator uses the existing `simulate_t_plus_1_execution(...)` implementation.

Rules:

- signal date is `decision_date`,
- buy date is `next_trading_day(decision_date)`,
- sell date uses the configured holding horizon in trading days,
- blocked buys are recorded as skipped trades,
- blocked sells use the existing delayed-exit behavior.

No live order behavior is created.

## Report Format

Default path:

```text
outputs/reports/replay_<decision_date>_<universe_name>.md
```

The markdown report includes:

1. Replay metadata
2. Data audit summary
3. Candidate table
4. Score breakdown
5. Simulated trade table
6. Performance summary
7. Warnings and skipped trades
8. Known limitations

## Known MVP Limitations

- Uses local CSV/mock data only.
- No portfolio cash ledger or position sizing.
- Equal-weight return is a simple mean of filled trade returns.
- Benchmark return is a simple average over filled trade buy/sell periods.
- Reports are markdown only.
- No batch replay, parameter calibration, or paper trading execution layer yet.
