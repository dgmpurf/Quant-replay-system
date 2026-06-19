# Training Result Planning Phase 1

`training-result-planning` creates report-only planning artifacts for a future training result workflow. It consumes approved report-only metric extension, metric computation, metric evaluation, training evaluation, forward return label, and replay decision freeze context. It does not train weights or create any executable model artifact.

This workflow is deliberately conservative:

- report-only planning artifacts only.
- not actual training_result.
- does not train weights.
- does not create model_version.
- does not create parameter_version.
- does not optimize thresholds.
- does not create predictions.
- does not create calibrated probabilities.
- does not create feature importance.
- does not create active stock profiles.
- does not create real buy-review eligibility.
- does not apply paper approval.
- does not claim strategy performance validation.
- does not authorize trading.

## Commands

Use:

```bash
python -m quant_replay_system.cli training-result-planning
python -m quant_replay_system.cli training-result-planning-index
python -m quant_replay_system.cli training-result-planning-health
python -m quant_replay_system.cli training-result-planning-status
```

`training-result-planning` can reach `READY_FOR_TRAINING_RESULT_PLANNING` without explicit allow. It creates substantive planning artifacts only when the exact local approval text is supplied and upstream lineage, health, safety, metric evidence, denominator, and sample-scope gates pass.

## Research Status

`research-status` includes the latest training result planning context when artifacts exist. The dashboard exposes the latest run id, status/stage, health status, source lineage, metric evidence names, planning input counts, model scope and limitation flags, report path, next action, and downstream safety flags.

Later paper workflow priority is preserved. A training result planning artifact does not override `PAPER_WORKFLOW_READY`.

## Safety Boundary

The workflow must fail closed if any output claims to be a real training result, weights, model_version, parameter_version, thresholds, predictions, calibrated probabilities, feature importance, active stock profile, real buy-review eligibility, paper approval, strategy performance validation, broker/order/message/API side effect, cache mutation, data write, current-candidates run, snapshot build, or signal-semantics change.

`docs/project_sources/` is intentionally absent from Git. Project Source refresh is an external ChatGPT project maintenance action after a commit/tag, not a repository output of this workflow.
