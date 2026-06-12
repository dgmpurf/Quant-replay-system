# Historical Replay Input Gate Validator Fixture

`historical-replay-input-gate-validator-fixture` creates a report-only contract fixture for a future historical replay input gate validator.

It is not the real validator. It is not real replay. It does not create active replay input, compute forward labels, train weights, create active stock profiles, or make any row eligible for real buy-review.

## Commands

```powershell
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-index
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-health
python -m quant_replay_system.cli historical-replay-input-gate-validator-fixture-status
python -m quant_replay_system.cli research-status
```

## Research-Status Context

`research-status` exposes the latest fixture through `input_gate_validator_fixture_*` fields:

- `latest_input_gate_validator_fixture_run_id`
- `input_gate_validator_fixture_status`
- `input_gate_validator_fixture_stage`
- `input_gate_validator_fixture_health_status`
- `input_gate_validator_fixture_case_count`
- `input_gate_validator_fixture_blocked_case_count`
- `input_gate_validator_fixture_pass_candidate_case_count`
- `input_gate_validator_fixture_active_ready_case_count`
- `input_gate_validator_fixture_validation_issue_count`
- `input_gate_validator_fixture_overclaim_guard_pass_count`
- `input_gate_validator_fixture_overclaim_guard_total_count`
- `input_gate_validator_fixture_active_replay_input`
- `input_gate_validator_fixture_forward_labels_exist`
- `input_gate_validator_fixture_weights_trained`
- `input_gate_validator_fixture_active_stock_profile_exists`
- `input_gate_validator_fixture_real_buy_review_eligible`
- `input_gate_validator_fixture_validator_implemented`
- `input_gate_validator_fixture_report_only`
- `input_gate_validator_fixture_diagnostic_only`
- `input_gate_validator_fixture_no_live_trading`
- `input_gate_validator_fixture_no_broker_api`
- `input_gate_validator_fixture_no_order_placement`
- `input_gate_validator_fixture_no_message_sent`
- `input_gate_validator_fixture_llm_api_called`
- `input_gate_validator_fixture_external_api_called`
- `input_gate_validator_fixture_cache_mutated`
- `input_gate_validator_fixture_current_candidates_run`
- `input_gate_validator_fixture_snapshot_built`
- `input_gate_validator_fixture_signal_semantics_changed`
- `input_gate_validator_fixture_report_path`
- `input_gate_validator_fixture_next_action`

When healthy, the status stage is `INPUT_GATE_VALIDATOR_FIXTURE_READY`. That stage means the fixture contracts are visible and reviewable only. It must not be read as `ACTIVE_REPLAY_INPUT_READY`, `REAL_REPLAY_READY`, `FORWARD_LABEL_READY`, `TRAINING_READY`, `STOCK_PROFILE_READY`, or `REAL_BUY_REVIEW_READY`.

If later replay substrate, advisory, current-candidates, or paper workflow artifacts exist, their workflow priority remains preserved. The input-gate fixture remains visible as context.

## Safety

The fixture keeps:

- `active_replay_input: false`
- `forward_labels_exist: false`
- `weights_trained: false`
- `active_stock_profile_exists: false`
- `real_buy_review_eligible: false`
- `validator_implemented: false`
- `report_only: true`
- `diagnostic_only: true`

It also records no live trading, no broker API, no order placement, no messages, no LLM/API calls, no external API calls, no cache mutation, no current-candidates generation, no snapshot build, and no signal semantics change.
