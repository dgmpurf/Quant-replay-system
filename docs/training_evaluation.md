# Training / Evaluation Phase 1

Training / Evaluation Phase 1 is a report-only dataset/planning workflow. It prepares bounded diagnostic artifacts from frozen replay decisions and forward-return labels so the next governance step can review whether training/evaluation should proceed. It does not compute metrics, does not create training_result, does not train weights, does not create model_version, does not optimize thresholds, does not create predictions, does not create calibrated probabilities, does not create feature importance, does not create active stock profiles, does not create real buy-review eligibility, does not apply paper approval, does not claim strategy performance validation, and does not authorize trading.

## Commands

- `training-evaluation`
- `training-evaluation-index`
- `training-evaluation-health`
- `training-evaluation-status`

The core command writes artifacts under `outputs/reports/manual_diagnostics/training_evaluation_v0_1/<training_evaluation_run_id>/` by default. The index, health, and status commands summarize those report-only artifacts for local review and `research-status` integration.

## Artifact Layout

Each run writes:

- `training_evaluation_metadata.json`
- `training_evaluation_report.md`
- `training_evaluation_dataset_index.csv`
- `training_evaluation_sample_rows.csv`
- `training_evaluation_label_coverage_report.csv`
- `training_evaluation_split_plan.csv`
- `training_evaluation_feature_plan.csv`
- `training_evaluation_label_plan.csv`
- `training_evaluation_gate_results.csv`
- `training_evaluation_blocker_matrix.csv`
- `training_evaluation_safety_flags.json`
- `recommended_next_task.md`

These artifacts are diagnostics and planning context only. They are not model outputs and not performance evidence.

## Status Semantics

`NO_TRAINING_EVALUATION_INPUT` means the required frozen replay decision, forward-label, governance, approval, leakage, or overclaim inputs were not provided or were incomplete.

`READY_FOR_TRAINING_EVALUATION_DATASET` means the gates appear ready for a report-only dataset/planning run, but the explicit allow flag was not supplied. No dataset/planning artifacts are created beyond diagnostics.

`TRAINING_EVALUATION_DATASET_CREATED` means report-only dataset/planning artifacts were created after explicit allow. It does not mean metrics were computed. It does not create training_result, train weights, create model_version, optimize thresholds, create predictions, create calibrated probabilities, create feature importance, create active stock profiles, create real buy-review eligibility, apply paper approval, claim strategy performance validation, or authorize trading.

## Required Contracts

The metadata records lineage to source forward-return labels and replay decision freeze artifacts. It includes source run ids, source status and health fields where available, label row counts, symbol counts, label name sets, dataset sample row counts, and safety flags.

The dataset index lists the bounded sample rows, label coverage report, split plan, feature plan, and label plan. The bounded sample is capped for inspection and is not a training matrix. The label coverage report summarizes label names and horizon coverage. The split, feature, and label plans are planning artifacts only.

The safety flags must keep these values false:

- `metrics_computed`
- `training_allowed`
- `weights_trained`
- `training_result_created`
- `model_version_created`
- `thresholds_optimized`
- `predictions_created`
- `calibrated_probabilities_created`
- `feature_importance_created`
- `stock_profile_allowed`
- `active_stock_profile_exists`
- `stock_profile_created`
- `buy_review_allowed`
- `real_buy_review_eligible`
- `approved_for_paper`
- `strategy_performance_validated`
- `trading_allowed`
- `order_placed`
- `broker_api_called`
- `message_sent`
- `llm_api_called`
- `external_api_called`
- `cache_mutated`
- `data_raw_written`
- `data_processed_written`
- `data_cache_written`
- `current_candidates_run`
- `snapshot_built`
- `signal_semantics_changed`

`report_only=true` and `diagnostic_only=true` remain true.

## Artifact Views

`training-evaluation-index` discovers training/evaluation run folders and exports one row per artifact. It preserves source lineage, counts, safety flags, and artifact paths.

`training-evaluation-health` checks that required files are present and that the safety boundary is intact. It fails if a dataset-created artifact claims metrics, training_result, weights, model_version, thresholds, predictions, probabilities, feature importance, stock profiles, buy-review eligibility, paper approval, performance validation, trading, broker/order/message/API/cache side effects, data writes, current-candidates generation, snapshot builds, or signal-semantics changes.

`training-evaluation-status` summarizes the latest artifact and reports the current stage, health, counts, next action, and safety statement.

## Research-Status Integration

`research-status` exposes the latest training/evaluation fields, including source forward-label lineage, label counts, planning artifact booleans, report paths, and all safety flags. Later paper workflow priority is preserved: if paper artifacts already indicate `PAPER_WORKFLOW_READY`, the final workflow stage remains `PAPER_WORKFLOW_READY` while training/evaluation context stays visible.

Training / Evaluation Phase 1 is intentionally separated from any future metrics, training_result, model_version, stock_profile, buy-review, paper approval, strategy performance validation, or trading workflow.
