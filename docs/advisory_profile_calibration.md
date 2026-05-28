# Advisory Profile Calibration Analyzer v0.1

Advisory Profile Calibration Analyzer evaluates local candidate or scored rows against proposed non-demo advisory profile thresholds.

It is local and deterministic. It is not live trading, broker integration, order placement, paper approval, message delivery, an LLM feature, or a strategy recommendation.

## Purpose

The analyzer helps design future non-demo advisory profiles before those thresholds are wired into production-facing advisory semantics:

```text
candidates / scored_dataset
-> advisory-profile-calibration
-> simulated threshold labels
-> local calibration report
-> human review of profile settings
```

The output labels are simulated calibration labels only:

- `REVIEW_BUY_CANDIDATE`
- `WATCH`
- `NO_ACTION`
- `BLOCKED`
- `DEMO_ONLY`

`REVIEW_BUY_CANDIDATE` means "this row would meet the proposed human-review threshold." It does not mean buy, approve paper trading, send a message, place an order, or connect to a broker.

## Profiles

Built-in v0.1 profiles:

| Profile | Buy-review threshold | Watch threshold | Quality gates |
| --- | ---: | ---: | --- |
| `conservative` | `75` | `60` | data quality PASS, snapshot quality PASS |
| `balanced` | `70` | `55` | data quality PASS, snapshot quality PASS |
| `experimental` | `65` | `50` | data quality PASS, snapshot quality PASS |

The profiles are threshold-analysis candidates, not strategy validation results.

## Gates

Rows become `BLOCKED` when any of these apply:

- missing symbol
- invalid local six-digit symbol
- `risk_precheck_status` is `BLOCK`, `BLOCKED`, `FAIL`, `REJECT`, or `REJECTED`
- `score_action=BLOCKED`
- `action=BLOCKED`
- `data_quality_status=FAIL`
- `snapshot_quality_status=FAIL`
- `market_data_available=false` when present
- `execution_data_available=false` when present

Rows with demo or not-strategy markers are `DEMO_ONLY`, even when their score is high.

## CLI Usage

Run against local candidates:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration --input outputs\reports\current_candidates\2024-05-20_etf_core_f484cd4648\candidates.csv --input-type candidates --profile balanced --data-quality-status PASS --snapshot-quality-status PASS
```

Run against a scored dataset:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration --input outputs\reports\current_candidates\example\scored_dataset.csv --input-type scored_dataset --profile conservative --data-quality-status PASS --snapshot-quality-status PASS
```

The CLI prints the calibration run id, row counts, simulated label counts, artifact paths, and safety flags.

## Artifacts

Artifacts are written under:

```text
outputs/reports/advisory_profile_calibration/<calibration_run_id>/
```

Files:

- `advisory_profile_calibration.csv`
- `advisory_profile_calibration_summary.csv`
- `advisory_profile_calibration_issues.csv`
- `advisory_profile_calibration_report.md`
- `metadata.json`

The summary includes score distribution, row count, symbol count, risk/action counts, simulated label counts, and safety flags.

## Safety Boundaries

Every row and metadata artifact keeps:

- `requires_manual_confirmation=true`
- `auto_order_allowed=false`
- `no_live_trading=true`
- `no_broker_api=true`
- `no_message_sent=true`

The analyzer does not:

- place orders,
- approve paper trades,
- connect to brokers,
- send SMS, email, Telegram, WeChat, or webhook messages,
- call LLM APIs,
- call external APIs,
- mutate market cache.

Generated outputs are local diagnostics and are ignored by git. They should not be committed.

## Known MVP Limitations

- The analyzer evaluates current local artifact fields only.
- Profiles are fixed built-in threshold candidates in v0.1.
- It does not run data-quality or snapshot-quality itself; it consumes supplied status values or row fields.
- It does not validate strategy quality, profitability, drawdown, or false-positive behavior.
- It does not perform multi-date calibration or backtesting.
- Non-demo labels remain structural human-review labels until future strategy validation.
