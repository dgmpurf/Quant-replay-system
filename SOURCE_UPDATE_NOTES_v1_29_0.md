# Source Update Notes v1.29.0

v1.29.0 adds `research-status` integration for the report-only real historical replay input gate validator.

## Source Update Guidance

- Add the v1.29.0 checkpoint to project context.
- Record that `historical-replay-input-gate-validator` and its index/health/status views exist.
- Record that `research-status` exposes `historical_replay_input_gate_validator_*` fields.
- Record that the current dry-run is `NO_INPUT`, not active replay input.
- Preserve the distinction between `REPLAY_INPUT_GATE_PASS_CANDIDATE` and `ACTIVE_REPLAY_INPUT_READY`.

## Safety

No source pack was duplicated into Git. Do not recreate `docs/project_sources/`.

This update does not run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, run current-candidates, build snapshots, mutate cache, write data inputs, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or validate strategy performance.

