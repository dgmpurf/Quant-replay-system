# Release Checkpoint v0.93.0: Non-Demo Advisory Profile Calibration Analyzer

## Milestone Name

Non-Demo Advisory Profile Calibration Analyzer v0.1.

Recommended tag: `v0.93.0`

## Completed Capabilities

- Completed a read-only audit of available scoring, candidate, and signal semantics fields for non-demo advisory calibration.
- Added a local deterministic Advisory Profile Calibration Analyzer.
- Added CLI command:

```cmd
python -m quant_replay_system.cli advisory-profile-calibration
```

- Added built-in calibration profiles:
  - `conservative`
  - `balanced`
  - `experimental`
- Added local calibration artifacts:
  - `advisory_profile_calibration.csv`
  - `advisory_profile_calibration_summary.csv`
  - `advisory_profile_calibration_issues.csv`
  - `advisory_profile_calibration_report.md`
  - `metadata.json`
- Preserved leading-zero symbols.
- Preserved demo-only safety: demo inputs remain `DEMO_ONLY` and do not become non-demo review labels.
- Synthetic non-demo fixtures can produce calibration-only `REVIEW_BUY_CANDIDATE`, `WATCH`, `NO_ACTION`, and `BLOCKED` labels.
- Data-quality FAIL and snapshot-quality FAIL block rows.
- Risk-blocked and missing-symbol rows remain `BLOCKED`.
- All labels remain human-review or calibration context only.

## Workflow Impact

The calibration analyzer adds a profile-design step before future non-demo semantics expansion:

```text
current-candidates / scored rows
-> advisory-profile-calibration
-> simulated profile labels
-> local calibration report
-> human review of thresholds
-> future signal_semantics profile refinement
```

The analyzer does not change `signal_semantics`, signal advisory, single-symbol advisory, paper workflow, or execution behavior. It gives the project a safe place to compare threshold candidates before any future policy wiring.

## Validation Baseline

Full backend tests:

```text
1176 passed, 2 warnings
```

Quick tests:

```text
1067 passed, 109 deselected, 2 warnings
```

CLI dry-run summary:

- 9-symbol demo candidates, balanced profile:
  - calibration_run_id: `6b5bc0d5c005`
  - `DEMO_ONLY=9`
  - `REVIEW_BUY_CANDIDATE=0`
- Synthetic conservative profile:
  - calibration_run_id: `acd40a062bad`
  - `REVIEW_BUY_CANDIDATE=1`
  - `WATCH=2`
  - `NO_ACTION=1`
  - `BLOCKED=2`
- Synthetic balanced profile:
  - calibration_run_id: `d19fb602a5bf`
  - `REVIEW_BUY_CANDIDATE=1`
  - `WATCH=2`
  - `NO_ACTION=1`
  - `BLOCKED=2`
- Synthetic experimental profile:
  - calibration_run_id: `ed2a04fcfc7b`
  - `REVIEW_BUY_CANDIDATE=2`
  - `WATCH=1`
  - `NO_ACTION=1`
  - `BLOCKED=2`
- Data-quality FAIL gate:
  - calibration_run_id: `2a5d061be01c`
  - `BLOCKED=6`
- Snapshot-quality FAIL gate:
  - calibration_run_id: `d305d565dd51`
  - `BLOCKED=6`

## Safety Guarantees

- Calibration output is not a strategy recommendation.
- `REVIEW_BUY_CANDIDATE` remains human-review-only.
- `WATCH` is not an order.
- `BLOCKED` remains visible and cannot be overridden by score.
- Demo rows remain `DEMO_ONLY`.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real message delivery was implemented.
- No LLM/API calls were implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains required.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- The analyzer does not validate strategy quality, profitability, drawdown, or false-positive behavior.
- It does not perform multi-date replay/backtest calibration.
- It consumes data-quality and snapshot-quality statuses but does not run those gates itself.
- Profiles are built-in threshold candidates in v0.1.
- Calibration artifacts do not yet have index, health, or status views.
- Calibration status is not yet integrated into `research-status`.
- No delivery channel, automation, broker integration, or international market support is implemented.

## Recommended Next Engineering Tasks

1. Add Advisory Profile Calibration Artifact Index / Health / Status v0.1.
2. Integrate calibration status into `research-status` as profile-design context only.
3. Add multi-date calibration analysis before changing non-demo `signal_semantics` behavior.
4. Keep non-demo review labels structural until strategy validation, data-quality gating, and backtesting evidence exist.
5. Keep delivery channels, automation, broker integration, and live trading out of scope until separately reviewed and checkpointed.
6. Create release tag `v0.93.0` only after user review, git safety checks, and normal checkpoint process.
