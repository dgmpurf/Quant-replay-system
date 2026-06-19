from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.training_result_planning import (
    EXACT_TRAINING_RESULT_PLANNING_APPROVAL_TEXT,
    NO_TRAINING_RESULT_PLANNING_INPUT,
    READY_FOR_TRAINING_RESULT_PLANNING,
    TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED,
    TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED,
    TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED,
    TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED,
    TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_HEALTH_BLOCKED,
    TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED,
    TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED,
    TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED,
    TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED,
    TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED,
    TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED,
    TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED,
    TrainingResultPlanningSettings,
    run_training_result_planning,
)
from quant_replay_system.training_result_planning_health import check_training_result_planning_health
from quant_replay_system.training_result_planning_index import build_training_result_planning_index
from quant_replay_system.training_result_planning_status import run_training_result_planning_status


DOWNSTREAM_FALSE_FIELDS = [
    "training_result_created",
    "weights_trained",
    "model_version_created",
    "parameter_version_created",
    "thresholds_optimized",
    "predictions_created",
    "calibrated_probabilities_created",
    "feature_importance_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]


def test_no_input_writes_safe_diagnostics_only(tmp_path: Path) -> None:
    result = run_training_result_planning(TrainingResultPlanningSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_TRAINING_RESULT_PLANNING_INPUT
    assert result.workflow_stage == "TRAINING_RESULT_PLANNING_NO_INPUT"
    assert result.ready_for_training_result_planning is False
    assert result.training_result_planning_executed is False
    assert result.training_result_planning_artifacts_created is False
    assert result.metric_evidence_row_count == 0
    assert result.planning_input_row_count == 0
    assert result.eligible_planning_input_count == 0
    assert result.quarantined_planning_input_count == 0
    _assert_downstream_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    for key in _safe_diagnostic_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    assert not result.artifact_paths["input_index"].exists()
    metadata = _read_json(result.artifact_paths["metadata"])
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert metadata["execution_status"] == NO_TRAINING_RESULT_PLANNING_INPUT
    assert safety["training_result_created"] is False


@pytest.mark.parametrize("approval_text", ["", "continue", "go ahead", "plan training", "make training_result", "train it", "build model"])
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_training_result_planning(settings)

    assert result.status == TRAINING_RESULT_PLANNING_APPROVAL_BLOCKED
    assert result.ready_for_training_result_planning is False
    assert result.training_result_planning_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    "request_patch",
    [
        {"actual_training_result_requested": True},
        {"training_result_requested": True},
        {"weights_requested": True},
        {"model_version_requested": True},
        {"parameter_version_requested": True},
        {"thresholds_requested": True},
        {"predictions_requested": True},
        {"calibrated_probabilities_requested": True},
        {"feature_importance_requested": True},
        {"stock_profile_requested": True},
        {"buy_review_requested": True},
        {"paper_approval_requested": True},
        {"performance_validation_requested": True},
    ],
)
def test_overclaim_requests_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.training_result_planning_request_manifest_path, request_patch)

    result = run_training_result_planning(settings)

    assert result.status == TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED
    assert result.training_result_planning_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize("request_patch", [{"trading_requested": True}, {"broker_api_called": True}, {"order_placed": True}, {"message_sent": True}])
def test_side_effect_requests_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.training_result_planning_request_manifest_path, request_patch)

    result = run_training_result_planning(settings)

    assert result.status == TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED
    assert result.training_result_planning_artifacts_created is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("metric_extension_metadata_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_summary_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_summary_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED),
        ("metric_evaluation_denominator_rules_path", TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED),
        ("metric_evaluation_status_artifact_path", TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_status_artifact_path", TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_status_artifact_path", TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_training_result_planning(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.training_result_planning_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("metric_extension_metadata_path", {"status": "NO_METRIC_EXTENSION_INPUT"}, TRAINING_RESULT_PLANNING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", {"status": "NO_METRIC_COMPUTATION_INPUT"}, TRAINING_RESULT_PLANNING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", {"status": "NO_METRIC_EVALUATION_INPUT"}, TRAINING_RESULT_PLANNING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, TRAINING_RESULT_PLANNING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", {"status": "NO_FORWARD_RETURN_LABEL_INPUT"}, TRAINING_RESULT_PLANNING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", {"status": "NO_REPLAY_DECISION_FREEZE_INPUT"}, TRAINING_RESULT_PLANNING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_PLANNING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_label_leakage": True}, TRAINING_RESULT_PLANNING_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, TRAINING_RESULT_PLANNING_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"training_result_planning_not_performance_validation": False}, TRAINING_RESULT_PLANNING_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_training_result_planning(settings)

    assert result.status == expected_status
    assert result.training_result_planning_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("metric_extension_result_rows_path", "metric_extension_run_id", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "replay_decision_id", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "forward_return_label_id", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "available_time", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "source_hash", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "revision_id", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "quality_status", TRAINING_RESULT_PLANNING_LINEAGE_BLOCKED),
        ("metric_extension_result_rows_path", "denominator_count", TRAINING_RESULT_PLANNING_DENOMINATOR_BLOCKED),
        ("metric_extension_result_rows_path", "report_only", TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED),
        ("metric_extension_result_rows_path", "diagnostic_only", TRAINING_RESULT_PLANNING_REPORT_ONLY_BLOCKED),
        ("metric_computation_summary_path", "metric_name", TRAINING_RESULT_PLANNING_METRIC_EVIDENCE_BLOCKED),
        ("training_evaluation_sample_rows_path", "split_role", TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED),
    ],
)
def test_missing_required_row_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_training_result_planning(settings)

    assert result.status == expected_status
    assert result.training_result_planning_artifacts_created is False


def test_duplicate_sample_rows_without_quarantine_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame["quarantine_count"] = "0"
    frame.to_csv(settings.training_evaluation_sample_rows_path, index=False)

    result = run_training_result_planning(settings)

    assert result.status == TRAINING_RESULT_PLANNING_SAMPLE_SCOPE_BLOCKED


def test_forbidden_actual_artifacts_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    forbidden = Path(settings.metric_extension_metadata_path).parent / "training_result_rows.csv"
    forbidden.write_text("training_result_id,value\nactual,1\n", encoding="utf-8")

    result = run_training_result_planning(settings)

    assert result.status == TRAINING_RESULT_PLANNING_FORBIDDEN_ARTIFACT_BLOCKED
    assert result.training_result_created is False


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_training_result_planning(replace(_happy_settings(tmp_path), output_dir=tmp_path / "outputs" / "reports" / "training_result_planning"))


def test_happy_path_without_allow_is_ready_and_creates_no_substantive_planning_artifacts(tmp_path: Path) -> None:
    result = run_training_result_planning(_happy_settings(tmp_path))

    assert result.status == READY_FOR_TRAINING_RESULT_PLANNING
    assert result.workflow_stage == READY_FOR_TRAINING_RESULT_PLANNING
    assert result.ready_for_training_result_planning is True
    assert result.training_result_planning_executed is False
    assert result.training_result_planning_artifacts_created is False
    assert result.metric_evidence_row_count == 7
    assert not result.artifact_paths["input_index"].exists()
    _assert_downstream_false(result)


def test_happy_path_with_allow_creates_report_only_planning_artifacts(tmp_path: Path) -> None:
    result = run_training_result_planning(replace(_happy_settings(tmp_path), allow_training_result_planning=True))

    assert result.status == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED
    assert result.ready_for_training_result_planning is True
    assert result.training_result_planning_executed is True
    assert result.training_result_planning_artifacts_created is True
    assert result.model_scope_rows_created is True
    assert result.limitations_created is True
    assert result.overfit_warnings_created is True
    assert result.health_plan_created is True
    assert result.status_plan_created is True
    assert result.source_metric_extension_run_id == "metric_ext_plan"
    assert result.source_metric_computation_run_id == "metric_comp_plan"
    assert result.source_metric_evaluation_planning_run_id == "metric_eval_plan"
    assert result.source_training_evaluation_run_id == "train_eval_plan"
    assert result.source_forward_return_label_run_id == "label_plan"
    assert result.source_replay_decision_freeze_run_id == "freeze_plan"
    _assert_downstream_false(result)
    for key in _required_created_artifact_keys():
        assert result.artifact_paths[key].exists(), key

    evidence = pd.read_csv(result.artifact_paths["metric_evidence_index"])
    assert set(evidence["metric_name"]) == {
        "sample_count",
        "label_coverage",
        "average_return",
        "median_return",
        "hit_rate",
        "benchmark_relative_return",
        "industry_relative_return",
    }
    assert set(evidence["accepted_interpretation"]) == {"planning evidence only"}
    assert evidence["forbidden_interpretation"].str.contains("not training_result", regex=False).all()
    assert evidence["forbidden_interpretation"].str.contains("not strategy performance validation", regex=False).all()

    model_scope = pd.read_csv(result.artifact_paths["model_scope"])
    forbidden_items = set(model_scope.loc[model_scope["allowed_in_phase_1"] == False, "scope_item"])  # noqa: E712
    assert {"model_weights", "model_version", "thresholds", "predictions", "calibrated_probabilities", "feature_importance"}.issubset(forbidden_items)

    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")
    for phrase in [
        "report-only planning artifacts",
        "not actual training_result",
        "not weights",
        "not model_version",
        "not thresholds",
        "not predictions/probabilities/feature importance",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in limitations

    warnings = pd.read_csv(result.artifact_paths["overfit_warnings"])
    assert {"small sample", "class imbalance", "single-stock overfit", "metric selection bias", "lookahead leakage"}.issubset(set(warnings["risk_item"]))

    health_plan = pd.read_csv(result.artifact_paths["health_plan"])
    assert {"upstream health PASS", "lineage complete", "report-only flags"}.issubset(set(health_plan["future_gate"]))

    status_plan = pd.read_csv(result.artifact_paths["status_plan"])
    status_values = dict(zip(status_plan["status_field"], status_plan["expected_value"]))
    for key in [
        "training_result_created",
        "weights_trained",
        "model_version_created",
        "thresholds_optimized",
        "predictions_created",
        "stock_profile_created",
        "approved_for_paper",
        "strategy_performance_validated",
        "trading_allowed",
    ]:
        assert status_values[key] == "False"

    produced_names = {path.name for path in result.artifact_paths["artifact_dir"].iterdir()}
    forbidden_names = {
        "training_result_metadata.json",
        "training_result_rows.csv",
        "training_result_status.json",
        "model_weights.json",
        "model_version.json",
        "parameter_version.json",
        "thresholds.csv",
        "predictions.csv",
        "probabilities.csv",
        "feature_importance.csv",
        "stock_profile.csv",
        "buy_review.csv",
        "paper_approval.json",
        "performance_validation_report.md",
        "broker_orders.csv",
    }
    assert produced_names.isdisjoint(forbidden_names)

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "report-only planning artifacts",
        "not actual training_result",
        "not weights",
        "not model_version",
        "not thresholds",
        "not predictions/probabilities/feature importance",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in report


def test_cli_no_input_runs_and_no_artifact_view_commands_are_added(tmp_path: Path) -> None:
    no_input = _run_cli(["training-result-planning", "--output-dir", _output_dir(tmp_path)])
    assert "status: NO_TRAINING_RESULT_PLANNING_INPUT" in no_input.stdout
    help_text = _run_cli(["--help"]).stdout
    assert "training-result-planning" in help_text
    assert "training-result-planning-index" in help_text
    assert "training-result-planning-health" in help_text
    assert "training-result-planning-status" in help_text
    assert not Path("docs/project_sources").exists()


def test_cli_happy_paths_without_and_with_allow(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    args = _cli_args(settings)

    ready = _run_cli(["training-result-planning", *args])
    assert "status: READY_FOR_TRAINING_RESULT_PLANNING" in ready.stdout
    assert "training_result_planning_artifacts_created: False" in ready.stdout

    created = _run_cli(["training-result-planning", *args, "--allow-training-result-planning"])
    assert "status: TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED" in created.stdout
    assert "training_result_planning_artifacts_created: True" in created.stdout
    assert "training_result_created: False" in created.stdout
    assert "weights_trained: False" in created.stdout


def test_training_result_planning_index_discovers_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    _create_view_fixture_artifacts(tmp_path)

    index = build_training_result_planning_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert index.artifact_count == 3
    assert index.artifact_paths["index_csv"].exists()
    frame = index.index_frame
    assert set(frame["status"]) == {
        NO_TRAINING_RESULT_PLANNING_INPUT,
        READY_FOR_TRAINING_RESULT_PLANNING,
        TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED,
    }
    created = frame[frame["status"] == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED].iloc[0]
    assert created["training_result_planning_artifacts_created"] is True
    assert created["input_index_row_count"] == 6
    assert created["metric_evidence_row_count"] == 7
    assert created["lineage_matrix_row_count"] >= 1
    assert created["model_scope_row_count"] >= 10
    assert created["overfit_warning_row_count"] >= 5
    assert created["health_plan_row_count"] >= 3
    assert created["status_plan_row_count"] >= 10
    assert created["source_metric_extension_run_id"] == "metric_ext_plan"
    assert created["source_metric_computation_run_id"] == "metric_comp_plan"
    assert created["source_metric_evaluation_planning_run_id"] == "metric_eval_plan"
    assert created["source_training_evaluation_run_id"] == "train_eval_plan"
    assert created["source_forward_return_label_run_id"] == "label_plan"
    assert created["source_replay_decision_freeze_run_id"] == "freeze_plan"
    assert created["report_only"] is True
    assert created["diagnostic_only"] is True
    assert created["training_result_created"] is False
    assert created["weights_trained"] is False
    assert created["model_version_created"] is False
    assert created["parameter_version_created"] is False
    assert created["thresholds_optimized"] is False
    assert created["predictions_created"] is False
    assert created["calibrated_probabilities_created"] is False
    assert created["feature_importance_created"] is False
    assert created["stock_profile_created"] is False
    assert created["approved_for_paper"] is False
    assert created["strategy_performance_validated"] is False
    assert created["trading_allowed"] is False


def test_training_result_planning_health_passes_for_valid_artifact_states(tmp_path: Path) -> None:
    _create_view_fixture_artifacts(tmp_path)

    health = check_training_result_planning_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 3
    assert health.error_count == 0
    assert health.health_frame.empty
    assert health.artifact_paths["health_csv"].exists()


@pytest.mark.parametrize(
    ("mutator", "issue_code"),
    [
        (lambda path: (path / "training_result_planning_metadata.json").unlink(), "MISSING_METADATA"),
        (lambda path: (path / "training_result_planning_input_index.csv").unlink(), "MISSING_INPUT_INDEX"),
        (lambda path: (path / "training_result_planning_metric_evidence_index.csv").unlink(), "MISSING_METRIC_EVIDENCE_INDEX"),
        (lambda path: (path / "training_result_planning_lineage_matrix.csv").unlink(), "MISSING_LINEAGE_MATRIX"),
        (lambda path: (path / "training_result_planning_model_scope.csv").unlink(), "MISSING_MODEL_SCOPE"),
        (lambda path: (path / "training_result_planning_limitations.md").unlink(), "MISSING_LIMITATIONS"),
        (lambda path: (path / "training_result_planning_overfit_warnings.csv").unlink(), "MISSING_OVERFIT_WARNINGS"),
        (lambda path: (path / "training_result_planning_health_plan.csv").unlink(), "MISSING_HEALTH_PLAN"),
        (lambda path: (path / "training_result_planning_status_plan.csv").unlink(), "MISSING_STATUS_PLAN"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"training_result_planning_artifacts_created": False}), "ARTIFACTS_CREATED_FLAG_FALSE"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"model_scope_rows_created": False}), "MODEL_SCOPE_FLAG_FALSE"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"limitations_created": False}), "LIMITATIONS_FLAG_FALSE"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"overfit_warnings_created": False}), "OVERFIT_WARNINGS_FLAG_FALSE"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"health_plan_created": False}), "HEALTH_PLAN_FLAG_FALSE"),
        (lambda path: _patch_json(path / "training_result_planning_metadata.json", {"status_plan_created": False}), "STATUS_PLAN_FLAG_FALSE"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "sample_count"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "label_coverage"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "average_return"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "median_return"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "hit_rate"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "benchmark_relative_return"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_metric_evidence_index.csv", "metric_name", "industry_relative_return"), "METRIC_EVIDENCE_REQUIRED_METRIC_MISSING"),
        (lambda path: _patch_csv_cell(path / "training_result_planning_metric_evidence_index.csv", "forbidden_interpretation", "actual training_result"), "METRIC_EVIDENCE_OVERCLAIM"),
        (lambda path: _patch_csv_cell(path / "training_result_planning_metric_evidence_index.csv", "forbidden_interpretation", "strategy validation passed"), "METRIC_EVIDENCE_OVERCLAIM"),
        (lambda path: _drop_csv_column(path / "training_result_planning_input_index.csv", "source_run_id"), "INPUT_INDEX_LINEAGE_MISSING"),
        (lambda path: _drop_csv_column(path / "training_result_planning_lineage_matrix.csv", "source_hash"), "LINEAGE_COVERAGE_MISSING"),
        (lambda path: _patch_model_scope(path, "model_weights", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "model_version", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "parameter_version", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "thresholds", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "predictions", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "calibrated_probabilities", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: _patch_model_scope(path, "feature_importance", True), "MODEL_SCOPE_FORBIDDEN_ALLOWED"),
        (lambda path: (path / "training_result_planning_limitations.md").write_text("report-only planning artifacts\n", encoding="utf-8"), "LIMITATIONS_WORDING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_overfit_warnings.csv", "risk_item", "small sample"), "OVERFIT_WARNING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_overfit_warnings.csv", "risk_item", "class imbalance"), "OVERFIT_WARNING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_overfit_warnings.csv", "risk_item", "single-stock overfit"), "OVERFIT_WARNING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_overfit_warnings.csv", "risk_item", "metric selection bias"), "OVERFIT_WARNING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_overfit_warnings.csv", "risk_item", "lookahead leakage"), "OVERFIT_WARNING_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_health_plan.csv", "future_gate", "upstream health PASS"), "HEALTH_PLAN_GATE_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_health_plan.csv", "future_gate", "lineage complete"), "HEALTH_PLAN_GATE_MISSING"),
        (lambda path: _drop_csv_rows(path / "training_result_planning_health_plan.csv", "future_gate", "report-only flags"), "HEALTH_PLAN_GATE_MISSING"),
        (lambda path: _patch_status_plan(path, "training_result_created", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "weights_trained", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "model_version_created", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "parameter_version_created", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "thresholds_optimized", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "predictions_created", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "stock_profile_created", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "approved_for_paper", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "strategy_performance_validated", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: _patch_status_plan(path, "trading_allowed", "True"), "STATUS_PLAN_FALSE_FIELD_ALLOWED"),
        (lambda path: (path / "training_result_metadata.json").write_text("{}", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "model_weights.json").write_text("{}", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "model_version.json").write_text("{}", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "parameter_version.json").write_text("{}", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "thresholds.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "predictions.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "probabilities.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "feature_importance.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "stock_profile.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "buy_review.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "paper_approval.json").write_text("{}", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "performance_validation_report.md").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: (path / "broker_orders.csv").write_text("", encoding="utf-8"), "FORBIDDEN_ARTIFACT_PRESENT"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"training_result_created": True}), "TRAINING_RESULT_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"weights_trained": True}), "WEIGHTS_TRAINED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"model_version_created": True}), "MODEL_VERSION_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"parameter_version_created": True}), "PARAMETER_VERSION_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"thresholds_optimized": True}), "THRESHOLDS_OPTIMIZED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"predictions_created": True}), "PREDICTIONS_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"calibrated_probabilities_created": True}), "CALIBRATED_PROBABILITIES_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"feature_importance_created": True}), "FEATURE_IMPORTANCE_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"stock_profile_allowed": True}), "STOCK_PROFILE_ALLOWED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"active_stock_profile_exists": True}), "ACTIVE_STOCK_PROFILE_EXISTS_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"stock_profile_created": True}), "STOCK_PROFILE_CREATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"buy_review_allowed": True}), "BUY_REVIEW_ALLOWED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"real_buy_review_eligible": True}), "REAL_BUY_REVIEW_ELIGIBLE_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"approved_for_paper": True}), "APPROVED_FOR_PAPER_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"strategy_performance_validated": True}), "STRATEGY_PERFORMANCE_VALIDATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"trading_allowed": True}), "TRADING_ALLOWED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"order_placed": True}), "ORDER_PLACED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"broker_api_called": True}), "BROKER_API_CALLED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"message_sent": True}), "MESSAGE_SENT_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"llm_api_called": True}), "LLM_API_CALLED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"external_api_called": True}), "EXTERNAL_API_CALLED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"cache_mutated": True}), "CACHE_MUTATED_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"data_raw_written": True}), "DATA_RAW_WRITTEN_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"data_processed_written": True}), "DATA_PROCESSED_WRITTEN_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"data_cache_written": True}), "DATA_CACHE_WRITTEN_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"current_candidates_run": True}), "CURRENT_CANDIDATES_RUN_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"snapshot_built": True}), "SNAPSHOT_BUILT_UNEXPECTED"),
        (lambda path: _patch_json(path / "training_result_planning_safety_flags.json", {"signal_semantics_changed": True}), "SIGNAL_SEMANTICS_CHANGED_UNEXPECTED"),
    ],
)
def test_training_result_planning_health_fails_on_invalid_artifact_boundaries(
    tmp_path: Path,
    mutator: object,
    issue_code: str,
) -> None:
    created = run_training_result_planning(replace(_happy_settings(tmp_path), allow_training_result_planning=True))
    mutator(Path(created.artifact_path))

    health = check_training_result_planning_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


def test_training_result_planning_health_fails_if_ready_artifact_has_substantive_planning_outputs(tmp_path: Path) -> None:
    ready = run_training_result_planning(_happy_settings(tmp_path))
    artifact_path = Path(ready.artifact_path)
    _write_csv(artifact_path / "training_result_planning_input_index.csv", [{"source_run_id": "unsafe"}])

    health = check_training_result_planning_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "SUBSTANTIVE_PLANNING_ARTIFACT_WITHOUT_CREATED_STATUS" in set(health.health_frame["issue_code"])


def test_training_result_planning_status_summarizes_no_input_ready_and_created_states(tmp_path: Path) -> None:
    no_input, ready, created = _create_view_fixture_artifacts(tmp_path)

    no_input_status = run_training_result_planning_status(root=_single_artifact_root(tmp_path, no_input), output_dir=_output_dir(tmp_path) / "status_no_input")
    assert no_input_status.latest_training_result_planning_run_id == no_input.training_result_planning_run_id
    assert no_input_status.status == NO_TRAINING_RESULT_PLANNING_INPUT
    assert no_input_status.training_result_planning_artifacts_created is False

    ready_status = run_training_result_planning_status(root=_single_artifact_root(tmp_path, ready), output_dir=_output_dir(tmp_path) / "status_ready")
    assert ready_status.latest_training_result_planning_run_id == ready.training_result_planning_run_id
    assert ready_status.status == READY_FOR_TRAINING_RESULT_PLANNING
    assert ready_status.ready_for_training_result_planning is True
    assert ready_status.training_result_planning_artifacts_created is False

    created_status = run_training_result_planning_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status_created")
    assert created_status.latest_training_result_planning_run_id == created.training_result_planning_run_id
    assert created_status.status == TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED
    assert created_status.health_status == "PASS"
    assert created_status.training_result_planning_artifacts_created is True
    assert created_status.metric_evidence_row_count == 7
    assert created_status.input_index_row_count == 6
    assert created_status.training_result_created is False
    assert created_status.weights_trained is False
    assert created_status.model_version_created is False
    assert created_status.parameter_version_created is False
    assert created_status.thresholds_optimized is False
    assert created_status.predictions_created is False
    assert created_status.stock_profile_created is False
    assert created_status.approved_for_paper is False
    assert created_status.strategy_performance_validated is False
    assert created_status.trading_allowed is False
    for phrase in [
        "report-only planning only",
        "only planning artifacts",
        "not actual training_result",
        "not weights",
        "not model_version",
        "not parameter_version",
        "not thresholds",
        "not predictions/probabilities/feature importance",
        "not stock_profile",
        "not buy-review",
        "not paper approval",
        "not performance validation",
        "not trading",
    ]:
        assert phrase in created_status.safety_statement


def test_training_result_planning_view_cli_commands_run(tmp_path: Path) -> None:
    _create_view_fixture_artifacts(tmp_path)
    root = _output_dir(tmp_path)

    index = _run_cli(["training-result-planning-index", "--root", root, "--output-dir", root / "index"])
    assert "artifact_count: 3" in index.stdout

    health = _run_cli(["training-result-planning-health", "--root", root, "--output-dir", root / "health"])
    assert "status: PASS" in health.stdout

    status = _run_cli(["training-result-planning-status", "--root", root, "--output-dir", root / "status"])
    assert "status: TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED" in status.stdout
    assert "training_result_created: False" in status.stdout
    assert "weights_trained: False" in status.stdout

    help_text = _run_cli(["--help"]).stdout
    assert "training-result-planning-index" in help_text
    assert "training-result-planning-health" in help_text
    assert "training-result-planning-status" in help_text
    assert not Path("docs/project_sources").exists()
    assert Path("docs/release_checkpoint_v1.49.0.md").exists()


def test_training_result_planning_docs_checkpoint_and_source_note_are_safety_explicit() -> None:
    required_paths = [
        Path("docs/training_result_planning.md"),
        Path("docs/release_checkpoint_v1.49.0.md"),
        Path("SOURCE_UPDATE_NOTES_v1_49_0.md"),
    ]
    for path in required_paths:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in [
            "report-only planning",
            "not actual training_result",
            "does not train weights",
            "does not create model_version",
            "does not create parameter_version",
            "does not optimize thresholds",
            "does not create predictions",
            "does not create calibrated probabilities",
            "does not create feature importance",
            "does not create active stock profiles",
            "does not create real buy-review eligibility",
            "does not apply paper approval",
            "does not claim strategy performance validation",
            "does not authorize trading",
        ]:
            assert phrase in text, f"{path}: {phrase}"
    source_text = Path("SOURCE_UPDATE_NOTES_v1_49_0.md").read_text(encoding="utf-8")
    assert "docs/project_sources/ is intentionally absent from Git" in source_text
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> TrainingResultPlanningSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_TRAINING_RESULT_PLANNING_APPROVAL_TEXT})
    request = _write_json(root / "request.json", {})
    metric_ext_dir = root / "metric_extension"
    metric_ext_dir.mkdir()
    metric_ext_metadata = _write_json(metric_ext_dir / "metric_extension_metadata.json", _metadata("metric_extension_run_id", "metric_ext_plan", "METRIC_EXTENSION_REPORT_CREATED"))
    metric_ext_rows = _write_csv(metric_ext_dir / "metric_extension_result_rows.csv", _metric_extension_rows())
    metric_ext_summary = _write_csv(metric_ext_dir / "metric_extension_summary.csv", _metric_extension_summary())
    metric_ext_safety = _write_json(metric_ext_dir / "metric_extension_safety_flags.json", _safe_flags())
    metric_ext_status = _write_json(metric_ext_dir / "metric_extension_status.json", {"status": "METRIC_EXTENSION_REPORT_CREATED"})
    metric_ext_health = _write_json(metric_ext_dir / "metric_extension_health.json", {"status": "PASS"})

    metric_dir = root / "metric_computation"
    metric_dir.mkdir()
    metric_metadata = _write_json(metric_dir / "metric_computation_metadata.json", _metadata("metric_computation_run_id", "metric_comp_plan", "METRIC_COMPUTATION_REPORT_CREATED"))
    metric_rows = _write_csv(metric_dir / "metric_computation_result_rows.csv", _metric_computation_rows())
    metric_summary = _write_csv(metric_dir / "metric_computation_summary.csv", _metric_computation_summary())
    metric_safety = _write_json(metric_dir / "metric_computation_safety_flags.json", _safe_flags())
    metric_status = _write_json(metric_dir / "metric_computation_status.json", {"status": "METRIC_COMPUTATION_REPORT_CREATED"})
    metric_health = _write_json(metric_dir / "metric_computation_health.json", {"status": "PASS"})

    metric_eval_dir = root / "metric_evaluation"
    metric_eval_dir.mkdir()
    metric_eval_metadata = _write_json(metric_eval_dir / "metric_evaluation_metadata.json", _metadata("metric_evaluation_run_id", "metric_eval_plan", "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED"))
    metric_eval_index = _write_csv(metric_eval_dir / "metric_evaluation_input_index.csv", [{"input_component": "sample_rows", "source_hash_coverage": "PASS", "revision_id_coverage": "PASS", "available_time_coverage": "PASS", "quality_status_coverage": "PASS"}])
    sample_scope = _write_csv(metric_eval_dir / "metric_evaluation_sample_scope.csv", [{"valid_sample_scope": True, "report_only": True, "diagnostic_only": True}])
    denominator_rules = _write_csv(metric_eval_dir / "metric_evaluation_denominator_rules.csv", [{"metric_name": "average_return", "denominator_count": 1, "report_only": True, "diagnostic_only": True}])
    metric_eval_safety = _write_json(metric_eval_dir / "metric_evaluation_safety_flags.json", _safe_flags())
    metric_eval_status = _write_json(metric_eval_dir / "metric_evaluation_status.json", {"status": "METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED"})
    metric_eval_health = _write_json(metric_eval_dir / "metric_evaluation_health.json", {"status": "PASS"})

    train_dir = root / "training_evaluation"
    train_dir.mkdir()
    training_metadata = _write_json(train_dir / "training_evaluation_metadata.json", _metadata("training_evaluation_run_id", "train_eval_plan", "TRAINING_EVALUATION_DATASET_CREATED"))
    sample_rows = _write_csv(train_dir / "training_evaluation_sample_rows.csv", _sample_rows())
    training_safety = _write_json(train_dir / "training_evaluation_safety_flags.json", _safe_flags())
    training_status = _write_json(train_dir / "training_evaluation_status.json", {"status": "TRAINING_EVALUATION_DATASET_CREATED"})
    training_health = _write_json(train_dir / "training_evaluation_health.json", {"status": "PASS"})

    label_dir = root / "forward_label"
    label_dir.mkdir()
    label_metadata = _write_json(label_dir / "forward_return_label_metadata.json", _metadata("forward_return_label_run_id", "label_plan", "FORWARD_RETURN_LABELS_CREATED"))
    label_rows = _write_csv(label_dir / "forward_return_label_rows.csv", [{"forward_return_label_id": "label_001", "replay_decision_id": "decision_001", "symbol": "000001", "report_only": True, "diagnostic_only": True}])
    label_status = _write_json(label_dir / "forward_return_label_status.json", {"status": "FORWARD_RETURN_LABELS_CREATED"})
    label_health = _write_json(label_dir / "forward_return_label_health.json", {"status": "PASS"})

    freeze_dir = root / "replay_freeze"
    freeze_dir.mkdir()
    freeze_metadata = _write_json(freeze_dir / "replay_decision_freeze_metadata.json", _metadata("replay_decision_freeze_run_id", "freeze_plan", "REPLAY_DECISION_FROZEN"))
    freeze_rows = _write_csv(freeze_dir / "replay_decision_freeze_rows.csv", [{"replay_decision_id": "decision_001", "symbol": "000001", "report_only": True, "diagnostic_only": True}])
    freeze_status = _write_json(freeze_dir / "replay_decision_freeze_status.json", {"status": "REPLAY_DECISION_FROZEN"})
    freeze_health = _write_json(freeze_dir / "replay_decision_freeze_health.json", {"status": "PASS"})

    leakage = _write_json(root / "leakage.json", {"future_label_leakage": False, "metric_extension_leakage": False})
    overclaim = _write_json(root / "overclaim.json", _overclaim_bundle())
    side_effect = _write_json(root / "side_effect.json", _safe_flags())

    return TrainingResultPlanningSettings(
        approval_manifest_path=approval,
        training_result_planning_request_manifest_path=request,
        metric_extension_metadata_path=metric_ext_metadata,
        metric_extension_result_rows_path=metric_ext_rows,
        metric_extension_summary_path=metric_ext_summary,
        metric_extension_safety_flags_path=metric_ext_safety,
        metric_extension_status_artifact_path=metric_ext_status,
        metric_extension_health_artifact_path=metric_ext_health,
        metric_computation_metadata_path=metric_metadata,
        metric_computation_result_rows_path=metric_rows,
        metric_computation_summary_path=metric_summary,
        metric_computation_safety_flags_path=metric_safety,
        metric_computation_status_artifact_path=metric_status,
        metric_computation_health_artifact_path=metric_health,
        metric_evaluation_metadata_path=metric_eval_metadata,
        metric_evaluation_input_index_path=metric_eval_index,
        metric_evaluation_sample_scope_path=sample_scope,
        metric_evaluation_denominator_rules_path=denominator_rules,
        metric_evaluation_safety_flags_path=metric_eval_safety,
        metric_evaluation_status_artifact_path=metric_eval_status,
        metric_evaluation_health_artifact_path=metric_eval_health,
        training_evaluation_metadata_path=training_metadata,
        training_evaluation_sample_rows_path=sample_rows,
        training_evaluation_safety_flags_path=training_safety,
        training_evaluation_status_artifact_path=training_status,
        training_evaluation_health_artifact_path=training_health,
        forward_return_label_metadata_path=label_metadata,
        forward_return_label_rows_path=label_rows,
        forward_return_label_status_artifact_path=label_status,
        forward_return_label_health_artifact_path=label_health,
        replay_decision_freeze_metadata_path=freeze_metadata,
        replay_decision_freeze_rows_path=freeze_rows,
        replay_decision_freeze_status_artifact_path=freeze_status,
        replay_decision_freeze_health_artifact_path=freeze_health,
        leakage_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        side_effect_evidence_bundle_path=side_effect,
        output_dir=_output_dir(tmp_path),
    )


def _metric_extension_rows() -> list[dict[str, object]]:
    base = {
        "metric_extension_run_id": "metric_ext_plan",
        "metric_computation_run_id": "metric_comp_plan",
        "metric_evaluation_run_id": "metric_eval_plan",
        "training_evaluation_run_id": "train_eval_plan",
        "forward_return_label_run_id": "label_plan",
        "replay_decision_freeze_run_id": "freeze_plan",
        "replay_decision_id": "decision_001",
        "forward_return_label_id": "label_001",
        "symbol": "000001",
        "replay_as_of_date": "2024-04-02",
        "split_role": "test",
        "label_name": "forward_return_5d",
        "horizon_trading_days": 5,
        "metric_value": 0.04,
        "numerator_count": 1,
        "denominator_count": 1,
        "source_hash": "hash_ext",
        "revision_id": "rev_ext",
        "available_time": "2024-04-02T15:30:00",
        "quality_status": "PASS",
        "exclusion_count": 0,
        "quarantine_count": 0,
        "report_only": True,
        "diagnostic_only": True,
    }
    return [
        base | {"metric_name": "benchmark_relative_return", "benchmark_id": "CSI300", "benchmark_name": "CSI 300", "industry_id": "", "industry_name": ""},
        base | {"metric_name": "industry_relative_return", "benchmark_id": "", "benchmark_name": "", "industry_id": "bank", "industry_name": "Bank"},
    ]


def _metric_extension_summary() -> list[dict[str, object]]:
    return [
        {"metric_name": "benchmark_relative_return", "metric_value": 0.04, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "industry_relative_return", "metric_value": 0.03, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
    ]


def _metric_computation_rows() -> list[dict[str, object]]:
    return [
        {
            "metric_computation_run_id": "metric_comp_plan",
            "metric_evaluation_run_id": "metric_eval_plan",
            "training_evaluation_run_id": "train_eval_plan",
            "forward_return_label_run_id": "label_plan",
            "replay_decision_freeze_run_id": "freeze_plan",
            "replay_decision_id": "decision_001",
            "forward_return_label_id": "label_001",
            "symbol": "000001",
            "replay_as_of_date": "2024-04-02",
            "split_role": "test",
            "label_name": "forward_return_5d",
            "horizon_trading_days": 5,
            "metric_name": "average_return",
            "metric_value": 0.08,
            "numerator_count": 1,
            "denominator_count": 1,
            "source_hash": "hash_metric",
            "revision_id": "rev_metric",
            "available_time": "2024-04-02T15:30:00",
            "quality_status": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        }
    ]


def _metric_computation_summary() -> list[dict[str, object]]:
    return [
        {"metric_name": "sample_count", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "label_coverage", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "average_return", "metric_value": 0.08, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "median_return", "metric_value": 0.08, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "hit_rate", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
    ]


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "training_evaluation_sample_id": "sample_001",
            "metric_evaluation_run_id": "metric_eval_plan",
            "training_evaluation_run_id": "train_eval_plan",
            "forward_return_label_run_id": "label_plan",
            "replay_decision_freeze_run_id": "freeze_plan",
            "replay_decision_id": "decision_001",
            "forward_return_label_id": "label_001",
            "symbol": "000001",
            "replay_as_of_date": "2024-04-02",
            "split_role": "test",
            "label_name": "forward_return_5d",
            "horizon_trading_days": 5,
            "source_hash": "hash_sample",
            "revision_id": "rev_sample",
            "available_time": "2024-04-02T15:30:00",
            "quality_status": "PASS",
            "quarantine_count": 0,
            "report_only": True,
            "diagnostic_only": True,
        }
    ]


def _metadata(id_key: str, run_id: str, status: str) -> dict[str, object]:
    return {
        id_key: run_id,
        "status": status,
        "execution_status": status,
        "workflow_stage": status,
        "report_only": True,
        "diagnostic_only": True,
    }


def _safe_flags() -> dict[str, object]:
    return {
        "training_result_created": False,
        "weights_trained": False,
        "model_version_created": False,
        "parameter_version_created": False,
        "thresholds_optimized": False,
        "predictions_created": False,
        "calibrated_probabilities_created": False,
        "feature_importance_created": False,
        "stock_profile_allowed": False,
        "active_stock_profile_exists": False,
        "stock_profile_created": False,
        "buy_review_allowed": False,
        "real_buy_review_eligible": False,
        "approved_for_paper": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        "order_placed": False,
        "broker_api_called": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
    }


def _overclaim_bundle() -> dict[str, object]:
    return {
        "training_result_planning_not_actual_training_result": True,
        "training_result_planning_not_weights": True,
        "training_result_planning_not_model_version": True,
        "training_result_planning_not_parameter_version": True,
        "training_result_planning_not_thresholds": True,
        "training_result_planning_not_predictions": True,
        "training_result_planning_not_probabilities": True,
        "training_result_planning_not_feature_importance": True,
        "training_result_planning_not_stock_profile": True,
        "training_result_planning_not_buy_review": True,
        "training_result_planning_not_paper_approval": True,
        "training_result_planning_not_performance_validation": True,
        "training_result_planning_not_trading": True,
    }


def _assert_downstream_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _safe_diagnostic_artifact_keys() -> list[str]:
    return ["metadata", "report", "safety_flags", "precondition_results", "approval_results", "recommended_next_task"]


def _required_created_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "input_index",
        "metric_evidence_index",
        "lineage_matrix",
        "model_scope",
        "limitations",
        "overfit_warnings",
        "health_plan",
        "status_plan",
        "safety_flags",
        "precondition_results",
        "approval_results",
        "input_lineage_results",
        "metric_evidence_results",
        "leakage_guard_results",
        "side_effect_guard_results",
        "overclaim_guard_results",
        "recommended_next_task",
    ]


def _create_view_fixture_artifacts(tmp_path: Path) -> tuple[object, object, object]:
    no_input = run_training_result_planning(TrainingResultPlanningSettings(output_dir=_output_dir(tmp_path)))
    settings = _happy_settings(tmp_path)
    ready = run_training_result_planning(settings)
    created = run_training_result_planning(replace(settings, allow_training_result_planning=True))
    return no_input, ready, created


def _single_artifact_root(tmp_path: Path, result: object) -> Path:
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / f"single_{result.training_result_planning_run_id}"
    target = root / result.training_result_planning_run_id
    target.mkdir(parents=True, exist_ok=True)
    for item in Path(result.artifact_path).iterdir():
        if item.is_file():
            (target / item.name).write_bytes(item.read_bytes())
    return root


def _drop_csv_rows(path: Path, column: str, value: str) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame = frame[frame[column].astype(str) != value]
    frame.to_csv(path, index=False)


def _drop_csv_column(path: Path, column: str) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(path, index=False)


def _patch_csv_cell(path: Path, column: str, value: str) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame.loc[0, column] = value
    frame.to_csv(path, index=False)


def _patch_model_scope(artifact_path: Path, scope_item: str, allowed: bool) -> None:
    path = artifact_path / "training_result_planning_model_scope.csv"
    frame = pd.read_csv(path, dtype=str)
    frame.loc[frame["scope_item"].astype(str) == scope_item, "allowed_in_phase_1"] = str(allowed)
    frame.to_csv(path, index=False)


def _patch_status_plan(artifact_path: Path, status_field: str, expected_value: str) -> None:
    path = artifact_path / "training_result_planning_status_plan.csv"
    frame = pd.read_csv(path, dtype=str)
    frame.loc[frame["status_field"].astype(str) == status_field, "expected_value"] = expected_value
    frame.to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path, patch: dict[str, object]) -> None:
    payload = _read_json(path)
    payload.update(patch)
    _write_json(path, payload)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "training_result_planning_v0_1"


def _run_cli(args: list[object]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    return subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", *[str(arg) for arg in args]],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def _cli_args(settings: TrainingResultPlanningSettings) -> list[object]:
    return [
        "--approval-manifest-path",
        settings.approval_manifest_path,
        "--training-result-planning-request-manifest-path",
        settings.training_result_planning_request_manifest_path,
        "--metric-extension-metadata-path",
        settings.metric_extension_metadata_path,
        "--metric-extension-result-rows-path",
        settings.metric_extension_result_rows_path,
        "--metric-extension-summary-path",
        settings.metric_extension_summary_path,
        "--metric-extension-safety-flags-path",
        settings.metric_extension_safety_flags_path,
        "--metric-extension-status-artifact-path",
        settings.metric_extension_status_artifact_path,
        "--metric-extension-health-artifact-path",
        settings.metric_extension_health_artifact_path,
        "--metric-computation-metadata-path",
        settings.metric_computation_metadata_path,
        "--metric-computation-result-rows-path",
        settings.metric_computation_result_rows_path,
        "--metric-computation-summary-path",
        settings.metric_computation_summary_path,
        "--metric-computation-safety-flags-path",
        settings.metric_computation_safety_flags_path,
        "--metric-computation-status-artifact-path",
        settings.metric_computation_status_artifact_path,
        "--metric-computation-health-artifact-path",
        settings.metric_computation_health_artifact_path,
        "--metric-evaluation-metadata-path",
        settings.metric_evaluation_metadata_path,
        "--metric-evaluation-input-index-path",
        settings.metric_evaluation_input_index_path,
        "--metric-evaluation-sample-scope-path",
        settings.metric_evaluation_sample_scope_path,
        "--metric-evaluation-denominator-rules-path",
        settings.metric_evaluation_denominator_rules_path,
        "--metric-evaluation-safety-flags-path",
        settings.metric_evaluation_safety_flags_path,
        "--metric-evaluation-status-artifact-path",
        settings.metric_evaluation_status_artifact_path,
        "--metric-evaluation-health-artifact-path",
        settings.metric_evaluation_health_artifact_path,
        "--training-evaluation-metadata-path",
        settings.training_evaluation_metadata_path,
        "--training-evaluation-sample-rows-path",
        settings.training_evaluation_sample_rows_path,
        "--training-evaluation-safety-flags-path",
        settings.training_evaluation_safety_flags_path,
        "--training-evaluation-status-artifact-path",
        settings.training_evaluation_status_artifact_path,
        "--training-evaluation-health-artifact-path",
        settings.training_evaluation_health_artifact_path,
        "--forward-return-label-metadata-path",
        settings.forward_return_label_metadata_path,
        "--forward-return-label-rows-path",
        settings.forward_return_label_rows_path,
        "--forward-return-label-status-artifact-path",
        settings.forward_return_label_status_artifact_path,
        "--forward-return-label-health-artifact-path",
        settings.forward_return_label_health_artifact_path,
        "--replay-decision-freeze-metadata-path",
        settings.replay_decision_freeze_metadata_path,
        "--replay-decision-freeze-rows-path",
        settings.replay_decision_freeze_rows_path,
        "--replay-decision-freeze-status-artifact-path",
        settings.replay_decision_freeze_status_artifact_path,
        "--replay-decision-freeze-health-artifact-path",
        settings.replay_decision_freeze_health_artifact_path,
        "--leakage-evidence-bundle-path",
        settings.leakage_evidence_bundle_path,
        "--overclaim-evidence-bundle-path",
        settings.overclaim_evidence_bundle_path,
        "--side-effect-evidence-bundle-path",
        settings.side_effect_evidence_bundle_path,
        "--output-dir",
        settings.output_dir,
    ]
