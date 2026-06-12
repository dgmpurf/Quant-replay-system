# Minimal Replay Input Package Fixture Smoke

`minimal-replay-input-package-fixture-smoke` creates a tiny report-only replay input package fixture and runs the report-only historical replay input gate validator against it.

The smoke result may show `REPLAY_INPUT_GATE_PASS_CANDIDATE` and `SMOKE_PASS_CANDIDATE_READY`. That means the fixture package can exercise the validator contract. It is not active replay input, not `ACTIVE_REPLAY_INPUT_READY`, and not a permission to run replay.

## Commands

```powershell
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-index
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-health
python -m quant_replay_system.cli minimal-replay-input-package-fixture-smoke-status
python -m quant_replay_system.cli research-status
```

## Research Status

`research-status` exposes the latest smoke through `minimal_replay_input_package_fixture_smoke_*` fields, including the smoke run id, smoke status, health status, workflow stage, input package path, linked validator run id, validator status, pass-candidate flag, active-ready flag, report path, and safety booleans.

The current expected smoke status is:

- `latest_smoke_status=REPLAY_INPUT_GATE_PASS_CANDIDATE`
- `latest_smoke_workflow_stage=SMOKE_PASS_CANDIDATE_READY`
- `smoke_pass_candidate=true`
- `smoke_active_replay_input_ready=false`
- `smoke_active_replay_input=false`
- `smoke_forward_labels_exist=false`
- `smoke_weights_trained=false`
- `smoke_active_stock_profile_exists=false`
- `smoke_real_buy_review_eligible=false`

If later paper workflow artifacts exist, the final `workflow_stage` remains `PAPER_WORKFLOW_READY`; the smoke fields remain visible as replay-input context.

## Safety Boundary

The smoke does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, and does not create real buy-review eligibility.

It also does not run current-candidates, build snapshots, mutate cache, write `data/raw`, write `data/processed`, write `data/cache`, call LLM/API or external APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.
