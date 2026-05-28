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

## Index, Health, And Status

Use `advisory-profile-calibration-index` to discover local calibration runs:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration-index
```

The index scans `outputs/reports/advisory_profile_calibration/` and writes:

```text
outputs/reports/advisory_profile_calibration/index/
  advisory_profile_calibration_index.csv
  advisory_profile_calibration_index_report.md
  metadata.json
```

Index rows include the calibration run id, status, profile, input type, action counts, quality status fields, safety flags, and artifact paths.

Use `advisory-profile-calibration-health` to check artifact completeness and safety boundaries:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration-health
```

Health checks verify:

- `metadata.json` is readable,
- `advisory_profile_calibration.csv` exists and has the required columns,
- `advisory_profile_calibration_summary.csv` exists and is readable,
- `advisory_profile_calibration_report.md` exists,
- leading-zero symbols such as `000001` remain six-character strings,
- demo calibration does not contain `REVIEW_BUY_CANDIDATE` or `REVIEW_SELL_CANDIDATE`,
- review labels retain `requires_manual_confirmation=true`,
- `auto_order_allowed=false`,
- `no_live_trading=true`,
- `no_broker_api=true`,
- `no_message_sent=true`,
- no message delivery, broker, live-trading, or `APPROVED_FOR_PAPER` metadata is present,
- `BLOCKED` rows include reason or issue context where possible.

Health artifacts are written under:

```text
outputs/reports/advisory_profile_calibration/health/<health_id>/
  advisory_profile_calibration_health_report.md
  advisory_profile_calibration_health_issues.csv
  advisory_profile_calibration_health_summary.csv
  metadata.json
```

Use `advisory-profile-calibration-status` to summarize the latest calibration run:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration-status
```

Expected stages include:

- `NO_ADVISORY_PROFILE_CALIBRATION_ARTIFACTS`
- `DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED`
- `ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW`
- `ADVISORY_PROFILE_CALIBRATION_HEALTH_WARN`
- `ADVISORY_PROFILE_CALIBRATION_FAILED`

For demo-only calibration, the status reminds the user not to treat `DEMO_ONLY` labels as strategy recommendations. For non-demo structural calibration, the status may be ready for review, but `REVIEW_BUY_CANDIDATE` remains a human-review-only label and auto-order remains disabled.

## Research Status Integration

`research-status` includes the latest `advisory-profile-calibration-status` as calibration/design context. The unified summary, metadata, markdown report, and CLI output expose the latest calibration run id, profile, health status, simulated action counts, issue count, report path, and next manual action.

Calibration context does not approve trades. `REVIEW_BUY_CANDIDATE` remains a human-review-only threshold-analysis label, demo calibration remains `DEMO_ONLY`, and later workflow stages such as signal semantics, signal advisory, market-update handoff, or paper workflow keep priority for the final dashboard stage.

## Calibration-to-Semantics Proposal

Use `calibration-to-signal-semantics` after calibration runs to compare local calibration outputs against the current `signal_semantics` defaults:

```cmd
python -m quant_replay_system.cli calibration-to-signal-semantics
```

The proposal report is read-only. It recommends keeping current defaults when evidence is insufficient, highlights mandatory gates such as risk, data-quality, and snapshot-quality failures, and points future work toward `WATCH` semantics or evidence collection before non-demo buy-review expansion. See [calibration_to_signal_semantics.md](calibration_to_signal_semantics.md).

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
