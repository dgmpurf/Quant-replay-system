# Release Checkpoint v0.94.0: Advisory Profile Calibration Artifact Views and Research Status Integration

## Milestone Name

Advisory Profile Calibration Artifact Views and Research Status Integration v0.1.

Recommended tag: `v0.94.0`

## Completed Capabilities

- Added advisory profile calibration artifact views:
  - `advisory-profile-calibration-index`
  - `advisory-profile-calibration-health`
  - `advisory-profile-calibration-status`
- Added local artifact discovery for calibration runs under `outputs/reports/advisory_profile_calibration/`.
- Added health checks for calibration artifact completeness and safety boundaries.
- Added latest calibration status summary with profile, action counts, health status, issue counts, report path, and next manual action.
- Integrated `advisory-profile-calibration-status` into unified `research-status`.
- Exposed calibration fields in research-status summary CSV, metadata, markdown report, and CLI output.
- Preserved later paper workflow priority when calibration artifacts are present.
- Preserved demo safety: demo calibration remains `DEMO_ONLY`.
- Preserved human-review semantics: `REVIEW_BUY_CANDIDATE` is not an order.
- Confirmed no auto-order, broker API, live trading, or real message delivery.

## Workflow Impact

The calibration observability path is now:

```text
current-candidates / scored rows
-> advisory-profile-calibration
-> advisory-profile-calibration-index / health / status
-> research-status
-> human threshold review
-> future signal_semantics profile refinement
```

This milestone makes calibration artifacts dashboard-ready. It does not change `signal_semantics`, signal advisory, single-symbol advisory, paper workflow, or execution behavior. Calibration remains design context for future non-demo advisory profile refinement.

## Validation Baseline

Full backend tests:

```text
1194 passed, 2 warnings
```

Quick tests:

```text
1085 passed, 109 deselected, 2 warnings
```

CLI verification:

- `advisory-profile-calibration-index`
  - artifact_count: `9`
  - detected demo and synthetic calibration runs
- `advisory-profile-calibration-health`
  - status: `PASS`
  - checked_artifact_count: `9`
  - issue_count: `0`
  - error_count: `0`
  - warning_count: `0`
- `advisory-profile-calibration-status`
  - status: `WARN`
  - workflow_stage: `ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW`
  - latest_calibration_run_id: `d305d565dd51`
  - row_count: `6`
  - health_status: `PASS`
- `research-status`
  - status: `WARN`
  - final workflow_stage: `PAPER_WORKFLOW_READY`
  - latest_advisory_profile_calibration_run_id: `d305d565dd51`
  - calibration fields visible
  - later paper workflow priority preserved

## Safety Guarantees

- Calibration output is threshold-design context only.
- `REVIEW_BUY_CANDIDATE` is not an order.
- `WATCH` is not an order.
- `BLOCKED` remains visible and cannot be overridden by score.
- Demo rows remain `DEMO_ONLY`.
- No automatic BUY/SELL execution was implemented.
- No broker API was implemented.
- No live trading was implemented.
- No real SMS/email/Telegram/WeChat delivery was implemented.
- No LLM/API calls were implemented.
- Manual confirmation remains required.
- `auto_order_allowed=false` remains required.
- Generated outputs are ignored local artifacts and must not be committed.

## Known Limitations

- Calibration does not validate strategy quality, profitability, drawdown, or false-positive behavior.
- Calibration does not run data-quality or snapshot-quality itself; it consumes provided or row-level quality status.
- Non-demo review labels remain structural threshold-analysis labels until calibrated and validated.
- Current profiles are fixed local threshold candidates in v0.1.
- Research-status integration is observability only, not trading approval.
- No delivery channel, automation, broker integration, live trading, or international market support is implemented.

## Recommended Next Engineering Tasks

1. Review v0.94.0 artifacts and checkpoint before expanding non-demo semantics.
2. Add read-only audit for how advisory-profile-calibration results should inform future `signal_semantics` profile settings.
3. Add multi-date calibration analysis before changing non-demo advisory thresholds.
4. Keep `REVIEW_BUY_CANDIDATE` human-review-only until strategy validation and risk controls are separately checkpointed.
5. Keep delivery channels, automation, broker integration, and live trading out of scope until separately reviewed and checkpointed.
6. Create release tag `v0.94.0` only after user review, git safety checks, and normal checkpoint process.
