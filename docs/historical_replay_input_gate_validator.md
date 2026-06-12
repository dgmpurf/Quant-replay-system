# Historical Replay Input Gate Validator v0.1

The historical replay input gate validator is a report-only validator for candidate replay input packages.

It checks whether a local package can be considered a replay input gate pass candidate. It does not run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, place orders, call brokers, send messages, call LLM/API services, mutate cache, or write `data/raw`, `data/processed`, or `data/cache`.

## Commands

```powershell
python -m quant_replay_system.cli historical-replay-input-gate-validator
python -m quant_replay_system.cli historical-replay-input-gate-validator-index
python -m quant_replay_system.cli historical-replay-input-gate-validator-health
python -m quant_replay_system.cli historical-replay-input-gate-validator-status
python -m quant_replay_system.cli research-status
```

## Research Status

`research-status` surfaces the latest real validator status under `historical_replay_input_gate_validator_*` fields. The current no-input dry-run reports:

- `historical_replay_input_gate_validator_status=NO_INPUT`
- `historical_replay_input_gate_validator_stage=INPUT_GATE_VALIDATOR_NO_INPUT`
- `historical_replay_input_gate_validator_health_status=PASS`
- `historical_replay_input_gate_validator_active_replay_input_ready=false`
- `historical_replay_input_gate_validator_active_replay_input=false`
- `historical_replay_input_gate_validator_forward_labels_exist=false`
- `historical_replay_input_gate_validator_weights_trained=false`
- `historical_replay_input_gate_validator_active_stock_profile_exists=false`
- `historical_replay_input_gate_validator_real_buy_review_eligible=false`

The validator can expose `REPLAY_INPUT_GATE_PASS_CANDIDATE` in the future, but that remains review context only. It is not `ACTIVE_REPLAY_INPUT_READY`.

## Priority

The unified dashboard preserves later workflow priority. If paper workflow artifacts are already ready, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; validator fields remain visible as replay-input context.

## Safety Boundary

This command and its artifact views are not current-candidates generation, snapshot building, forward-label computation, training, stock-profile creation, or trading authorization. They do not validate strategy performance.

