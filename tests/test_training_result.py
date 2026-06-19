from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.training_result import (
    EXACT_TRAINING_RESULT_APPROVAL_TEXT,
    NO_TRAINING_RESULT_INPUT,
    READY_FOR_TRAINING_RESULT,
    TRAINING_RESULT_APPROVAL_BLOCKED,
    TRAINING_RESULT_CREATED,
    TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED,
    TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED,
    TRAINING_RESULT_HEALTH_BLOCKED,
    TRAINING_RESULT_LEAKAGE_BLOCKED,
    TRAINING_RESULT_LINEAGE_BLOCKED,
    TRAINING_RESULT_LIMITATIONS_BLOCKED,
    TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED,
    TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED,
    TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED,
    TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED,
    TRAINING_RESULT_OVERCLAIM_BLOCKED,
    TRAINING_RESULT_OVERFIT_WARNING_BLOCKED,
    TRAINING_RESULT_PLANNING_INPUT_BLOCKED,
    TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED,
    TRAINING_RESULT_REPORT_ONLY_BLOCKED,
    TRAINING_RESULT_SIDE_EFFECT_BLOCKED,
    TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED,
    TrainingResultSettings,
    run_training_result,
)


DOWNSTREAM_FALSE_FIELDS = [
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

REQUIRED_METRICS = {
    "sample_count",
    "label_coverage",
    "average_return",
    "median_return",
    "hit_rate",
    "benchmark_relative_return",
    "industry_relative_return",
}

FORBIDDEN_ROW_TOKENS = [
    "weight",
    "model_version",
    "parameter_version",
    "threshold",
    "prediction",
    "probability",
    "feature_importance",
    "stock_profile",
    "buy_review",
    "paper_approval",
    "performance_validation",
    "order",
    "broker",
    "trade",
]


def test_no_input_writes_safe_diagnostics_only(tmp_path: Path) -> None:
    result = run_training_result(TrainingResultSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_TRAINING_RESULT_INPUT
    assert result.workflow_stage == "TRAINING_RESULT_NO_INPUT"
    assert result.ready_for_training_result is False
    assert result.training_result_executed is False
    assert result.training_result_created is False
    assert result.training_result_row_count == 0
    assert result.eligible_training_result_row_count == 0
    assert result.quarantined_training_result_row_count == 0
    assert result.metric_evidence_reference_count == 0
    assert result.limitations_created is False
    assert result.overfit_warnings_created is False
    _assert_downstream_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    assert not result.artifact_paths["rows"].exists()
    safety = _read_json(result.artifact_paths["safety_flags"])
    assert safety["training_result_created"] is False
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False, field


@pytest.mark.parametrize(
    "approval_text",
    ["", "continue", "go ahead", "train it", "make training_result", "build model", "optimize thresholds", "make it better"],
)
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_APPROVAL_BLOCKED
    assert result.training_result_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    "request_patch",
    [
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
def test_forbidden_scope_requests_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.training_result_request_manifest_path, request_patch)

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_OVERCLAIM_BLOCKED
    assert result.training_result_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize("request_patch", [{"trading_requested": True}, {"broker_api_called": True}, {"order_placed": True}, {"message_sent": True}])
def test_side_effect_requests_block(tmp_path: Path, request_patch: dict[str, object]) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.training_result_request_manifest_path, request_patch)

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_SIDE_EFFECT_BLOCKED
    assert result.training_result_created is False


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("training_result_planning_metadata_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_input_index_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_metric_evidence_index_path", TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_limitations_path", TRAINING_RESULT_LIMITATIONS_BLOCKED),
        ("training_result_planning_overfit_warnings_path", TRAINING_RESULT_OVERFIT_WARNING_BLOCKED),
        ("training_result_planning_status_artifact_path", TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_summary_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_status_artifact_path", TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_summary_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_status_artifact_path", TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_input_index_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_sample_scope_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_denominator_rules_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_status_artifact_path", TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_status_artifact_path", TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_status_artifact_path", TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_status_artifact_path", TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", TRAINING_RESULT_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", TRAINING_RESULT_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", TRAINING_RESULT_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", TRAINING_RESULT_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_training_result(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.training_result_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("training_result_planning_metadata_path", {"status": "NO_TRAINING_RESULT_PLANNING_INPUT"}, TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", {"status": "NO_METRIC_EXTENSION_INPUT"}, TRAINING_RESULT_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", {"status": "NO_METRIC_COMPUTATION_INPUT"}, TRAINING_RESULT_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", {"status": "NO_METRIC_EVALUATION_INPUT"}, TRAINING_RESULT_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, TRAINING_RESULT_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", {"status": "NO_FORWARD_RETURN_LABEL_INPUT"}, TRAINING_RESULT_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", {"status": "NO_REPLAY_DECISION_FREEZE_INPUT"}, TRAINING_RESULT_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", {"status": "FAIL"}, TRAINING_RESULT_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_label_leakage": True}, TRAINING_RESULT_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, TRAINING_RESULT_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"actual_training_result_not_performance_validation": False}, TRAINING_RESULT_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_training_result(settings)

    assert result.status == expected_status
    assert result.training_result_created is False


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_result_planning_lineage_matrix_path", "training_result_planning_run_id", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "replay_decision_id", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "forward_return_label_id", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "available_time", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "source_hash", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "revision_id", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "quality_status", TRAINING_RESULT_LINEAGE_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "report_only", TRAINING_RESULT_REPORT_ONLY_BLOCKED),
        ("training_result_planning_lineage_matrix_path", "diagnostic_only", TRAINING_RESULT_REPORT_ONLY_BLOCKED),
        ("training_result_planning_metric_evidence_index_path", "metric_name", TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED),
        ("training_evaluation_sample_rows_path", "split_role", TRAINING_RESULT_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_row_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_training_result(settings)

    assert result.status == expected_status
    assert result.training_result_created is False


def test_missing_metric_evidence_references_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    _drop_csv_rows(settings.training_result_planning_metric_evidence_index_path, "metric_name", "hit_rate")

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_METRIC_EVIDENCE_BLOCKED


def test_missing_limitations_and_overfit_warnings_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    settings.training_result_planning_limitations_path.write_text("too short\n", encoding="utf-8")
    assert run_training_result(settings).status == TRAINING_RESULT_LIMITATIONS_BLOCKED

    settings = _happy_settings(tmp_path / "warnings")
    _drop_csv_rows(settings.training_result_planning_overfit_warnings_path, "risk_item", "lookahead leakage")
    assert run_training_result(settings).status == TRAINING_RESULT_OVERFIT_WARNING_BLOCKED


def test_duplicate_sample_rows_without_quarantine_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame["quarantine_count"] = "0"
    frame.to_csv(settings.training_evaluation_sample_rows_path, index=False)

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_LINEAGE_BLOCKED


def test_forbidden_artifacts_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    forbidden = Path(settings.metric_extension_metadata_path).parent / "model_weights.json"
    forbidden.write_text("{}", encoding="utf-8")

    result = run_training_result(settings)

    assert result.status == TRAINING_RESULT_FORBIDDEN_ARTIFACT_BLOCKED
    assert result.training_result_created is False


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_training_result(replace(_happy_settings(tmp_path), output_dir=tmp_path / "outputs" / "reports" / "training_result_v0_1"))


def test_happy_path_without_allow_is_ready_and_creates_no_actual_training_result_artifacts(tmp_path: Path) -> None:
    result = run_training_result(_happy_settings(tmp_path))

    assert result.status == READY_FOR_TRAINING_RESULT
    assert result.workflow_stage == READY_FOR_TRAINING_RESULT
    assert result.ready_for_training_result is True
    assert result.training_result_executed is False
    assert result.training_result_created is False
    assert result.training_result_row_count == 0
    assert result.metric_evidence_reference_count == 7
    assert not result.artifact_paths["rows"].exists()
    assert not result.artifact_paths["input_index"].exists()
    _assert_downstream_false(result)


def test_happy_path_with_allow_creates_report_only_training_result_artifacts(tmp_path: Path) -> None:
    result = run_training_result(replace(_happy_settings(tmp_path), allow_training_result=True))

    assert result.status == TRAINING_RESULT_CREATED
    assert result.workflow_stage == TRAINING_RESULT_CREATED
    assert result.ready_for_training_result is True
    assert result.training_result_executed is True
    assert result.training_result_created is True
    assert result.training_result_row_count == 1
    assert result.eligible_training_result_row_count == 1
    assert result.quarantined_training_result_row_count == 0
    assert result.metric_evidence_reference_count == 7
    assert result.limitations_created is True
    assert result.overfit_warnings_created is True
    assert result.source_training_result_planning_run_id == "trp_plan"
    assert result.source_metric_extension_run_id == "metric_ext_plan"
    assert result.source_metric_computation_run_id == "metric_comp_plan"
    assert result.source_metric_evaluation_planning_run_id == "metric_eval_plan"
    assert result.source_training_evaluation_run_id == "train_eval_plan"
    assert result.source_forward_return_label_run_id == "label_plan"
    assert result.source_replay_decision_freeze_run_id == "freeze_plan"
    _assert_downstream_false(result)
    for key in _created_artifact_keys():
        assert result.artifact_paths[key].exists(), key

    rows = pd.read_csv(result.artifact_paths["rows"], dtype=str)
    assert rows.loc[0, "symbol"] == "000001"
    assert rows.loc[0, "training_result_run_id"] == result.training_result_run_id
    assert not any(token in column for token in FORBIDDEN_ROW_TOKENS for column in rows.columns)

    evidence = pd.read_csv(result.artifact_paths["metric_evidence_reference"], dtype=str)
    assert set(evidence["metric_name"]) == REQUIRED_METRICS
    assert evidence["permitted_interpretation"].str.contains("evidence only", regex=False).all()
    assert evidence["forbidden_interpretation"].str.contains("not strategy performance validation", regex=False).all()
    assert evidence["forbidden_interpretation"].str.contains("not profitability proof", regex=False).all()

    lineage = pd.read_csv(result.artifact_paths["lineage_matrix"], dtype=str)
    assert {"training_result_planning_run_id", "metric_extension_run_id", "metric_computation_run_id"}.issubset(set(lineage["lineage_item"]))

    limitations = result.artifact_paths["limitations"].read_text(encoding="utf-8")
    for phrase in [
        "report-only actual training_result artifacts",
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
        assert phrase in limitations

    warnings = pd.read_csv(result.artifact_paths["overfit_warnings"], dtype=str)
    assert {"small sample", "class imbalance", "single-stock overfit", "metric selection bias", "lookahead leakage"}.issubset(set(warnings["risk_item"]))

    safety = _read_json(result.artifact_paths["safety_flags"])
    assert safety["training_result_created"] is True
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False, field

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in [
        "report-only actual training_result artifacts",
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
        assert phrase in report

    produced_names = {path.name for path in result.artifact_paths["artifact_dir"].iterdir()}
    forbidden_names = {
        "model_weights.json",
        "weights.csv",
        "model_version.json",
        "parameter_version.json",
        "thresholds.csv",
        "predictions.csv",
        "probabilities.csv",
        "calibrated_probabilities.csv",
        "feature_importance.csv",
        "stock_profile.csv",
        "buy_review.csv",
        "paper_approval.json",
        "performance_validation_report.md",
        "broker_orders.csv",
    }
    assert produced_names.isdisjoint(forbidden_names)
    assert result.artifact_paths["recommended_next_task"].read_text(encoding="utf-8") == "Actual Training Result Artifact Views Report-Only v0.1\n"


def test_cli_no_input_ready_and_allow_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["training-result", "--output-dir", _output_dir(tmp_path)])
    assert "status: NO_TRAINING_RESULT_INPUT" in no_input.stdout
    assert "training_result_created: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "cli")
    args = _cli_args(settings)
    ready = _run_cli(["training-result", *args])
    assert "status: READY_FOR_TRAINING_RESULT" in ready.stdout
    assert "training_result_created: False" in ready.stdout

    created = _run_cli(["training-result", *args, "--allow-training-result"])
    assert "status: TRAINING_RESULT_CREATED" in created.stdout
    assert "training_result_created: True" in created.stdout
    assert "weights_trained: False" in created.stdout

    help_text = _run_cli(["--help"]).stdout
    assert "training-result" in help_text
    assert "training-result-index" not in help_text
    assert "training-result-health" not in help_text
    assert "training-result-status" not in help_text
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> TrainingResultSettings:
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_TRAINING_RESULT_APPROVAL_TEXT})
    request = _write_json(root / "request.json", {})

    planning_dir = root / "training_result_planning"
    planning_dir.mkdir()
    planning_metadata = _write_json(planning_dir / "training_result_planning_metadata.json", _metadata("training_result_planning_run_id", "trp_plan", "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED"))
    planning_input_index = _write_csv(planning_dir / "training_result_planning_input_index.csv", _input_index_rows())
    planning_metric_evidence = _write_csv(planning_dir / "training_result_planning_metric_evidence_index.csv", _metric_evidence_rows())
    planning_lineage = _write_csv(planning_dir / "training_result_planning_lineage_matrix.csv", _training_result_lineage_rows())
    planning_limitations = planning_dir / "training_result_planning_limitations.md"
    planning_limitations.write_text(_limitations_text(), encoding="utf-8")
    planning_overfit = _write_csv(planning_dir / "training_result_planning_overfit_warnings.csv", _overfit_warning_rows())
    planning_status = _write_json(planning_dir / "training_result_planning_status.json", {"status": "TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED"})
    planning_health = _write_json(planning_dir / "training_result_planning_health.json", {"status": "PASS"})

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
    metric_eval_index = _write_csv(metric_eval_dir / "metric_evaluation_input_index.csv", [{"input_component": "sample_rows", "source_hash_coverage": "PASS", "revision_id_coverage": "PASS", "available_time_coverage": "PASS", "quality_status_coverage": "PASS", "report_only": True, "diagnostic_only": True}])
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

    return TrainingResultSettings(
        approval_manifest_path=approval,
        training_result_request_manifest_path=request,
        training_result_planning_metadata_path=planning_metadata,
        training_result_planning_input_index_path=planning_input_index,
        training_result_planning_metric_evidence_index_path=planning_metric_evidence,
        training_result_planning_lineage_matrix_path=planning_lineage,
        training_result_planning_limitations_path=planning_limitations,
        training_result_planning_overfit_warnings_path=planning_overfit,
        training_result_planning_status_artifact_path=planning_status,
        training_result_planning_health_artifact_path=planning_health,
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


def _base_lineage() -> dict[str, object]:
    return {
        "training_result_planning_run_id": "trp_plan",
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
        "benchmark_id": "CSI300",
        "benchmark_name": "CSI 300",
        "industry_id": "bank",
        "industry_name": "Bank",
        "metric_name": "average_return",
        "metric_value": 0.08,
        "numerator_count": 1,
        "denominator_count": 1,
        "source_hash": "hash_lineage",
        "revision_id": "rev_lineage",
        "available_time": "2024-04-02T15:30:00",
        "quality_status": "PASS",
        "quarantine_count": 0,
        "report_only": True,
        "diagnostic_only": True,
    }


def _training_result_lineage_rows() -> list[dict[str, object]]:
    return [_base_lineage()]


def _input_index_rows() -> list[dict[str, object]]:
    return [
        {
            "input_component": family,
            "artifact_name": f"{family}.json",
            "artifact_path": f"fixtures/{family}.json",
            "source_stage": family,
            "source_run_id": run_id,
            "row_count": 1,
            "required_for_training_result": True,
            "immutable_required": True,
            "source_hash_coverage": "PASS",
            "revision_id_coverage": "PASS",
            "available_time_coverage": "PASS",
            "quality_status_coverage": "PASS",
            "health_status": "PASS",
            "report_only": True,
            "diagnostic_only": True,
        }
        for family, run_id in [
            ("training_result_planning", "trp_plan"),
            ("metric_extension", "metric_ext_plan"),
            ("metric_computation", "metric_comp_plan"),
            ("metric_evaluation", "metric_eval_plan"),
            ("training_evaluation", "train_eval_plan"),
            ("forward_return_label", "label_plan"),
            ("replay_decision_freeze", "freeze_plan"),
        ]
    ]


def _metric_evidence_rows() -> list[dict[str, object]]:
    return [
        {
            "metric_name": metric,
            "metric_value": 1 if metric in {"sample_count", "label_coverage", "hit_rate"} else 0.08,
            "source_artifact_family": "metric_computation" if metric not in {"benchmark_relative_return", "industry_relative_return"} else "metric_extension",
            "accepted_interpretation": "training_result evidence only",
            "forbidden_interpretation": "not strategy performance validation; not profitability proof",
            "numerator_count": 1,
            "denominator_count": 1,
            "report_only": True,
            "diagnostic_only": True,
        }
        for metric in sorted(REQUIRED_METRICS)
    ]


def _metric_extension_rows() -> list[dict[str, object]]:
    base = _base_lineage() | {"source_hash": "hash_ext", "revision_id": "rev_ext"}
    return [
        base | {"metric_name": "benchmark_relative_return", "metric_value": 0.04},
        base | {"metric_name": "industry_relative_return", "metric_value": 0.03},
    ]


def _metric_extension_summary() -> list[dict[str, object]]:
    return [
        {"metric_name": "benchmark_relative_return", "metric_value": 0.04, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "industry_relative_return", "metric_value": 0.03, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
    ]


def _metric_computation_rows() -> list[dict[str, object]]:
    return [_base_lineage() | {"source_hash": "hash_metric", "revision_id": "rev_metric"}]


def _metric_computation_summary() -> list[dict[str, object]]:
    return [
        {"metric_name": "sample_count", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "label_coverage", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "average_return", "metric_value": 0.08, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "median_return", "metric_value": 0.08, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
        {"metric_name": "hit_rate", "metric_value": 1, "numerator_count": 1, "denominator_count": 1, "report_only": True, "diagnostic_only": True},
    ]


def _sample_rows() -> list[dict[str, object]]:
    return [_base_lineage() | {"training_evaluation_sample_id": "sample_001", "source_hash": "hash_sample", "revision_id": "rev_sample"}]


def _limitations_text() -> str:
    return (
        "report-only actual training_result artifacts only\n"
        "not weights\nnot model_version\nnot parameter_version\nnot thresholds\n"
        "not predictions/probabilities/feature importance\nnot stock_profile\nnot buy-review\n"
        "not paper approval\nnot performance validation\nnot trading\n"
        "metric evidence is bounded and descriptive\npositive relative return is not profitability proof\n"
    )


def _overfit_warning_rows() -> list[dict[str, object]]:
    return [
        {"warning_id": f"w{i}", "risk_item": risk, "applies_to_training_result": True, "guard_required": True, "severity": "WARN", "notes": "report-only warning"}
        for i, risk in enumerate(
            [
                "small sample",
                "class imbalance",
                "duplicate sample rows",
                "non-numeric labels",
                "single-stock overfit",
                "single-industry overfit",
                "single-regime overfit",
                "metric selection bias",
                "multiple comparisons",
                "threshold overfit",
                "benchmark mismatch",
                "industry classification drift",
                "survivorship bias",
                "lookahead leakage",
                "paper-overfit risk",
            ],
            start=1,
        )
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
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "diagnostic_only": True,
    }


def _overclaim_bundle() -> dict[str, object]:
    return {
        "actual_training_result_report_only": True,
        "actual_training_result_not_weights": True,
        "actual_training_result_not_model_version": True,
        "actual_training_result_not_parameter_version": True,
        "actual_training_result_not_thresholds": True,
        "actual_training_result_not_predictions": True,
        "actual_training_result_not_probabilities": True,
        "actual_training_result_not_feature_importance": True,
        "actual_training_result_not_stock_profile": True,
        "actual_training_result_not_buy_review": True,
        "actual_training_result_not_paper_approval": True,
        "actual_training_result_not_performance_validation": True,
        "actual_training_result_not_trading": True,
    }


def _assert_downstream_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _safe_artifact_keys() -> list[str]:
    return [
        "metadata",
        "report",
        "status_json",
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


def _created_artifact_keys() -> list[str]:
    return _safe_artifact_keys() + [
        "rows",
        "input_index",
        "metric_evidence_reference",
        "lineage_matrix",
        "limitations",
        "overfit_warnings",
    ]


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


def _drop_csv_rows(path: Path, column: str, value: str) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame = frame[frame[column].astype(str) != value]
    frame.to_csv(path, index=False)


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "training_result_v0_1"


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


def _cli_args(settings: TrainingResultSettings) -> list[object]:
    fields = [
        "approval_manifest_path",
        "training_result_request_manifest_path",
        "training_result_planning_metadata_path",
        "training_result_planning_input_index_path",
        "training_result_planning_metric_evidence_index_path",
        "training_result_planning_lineage_matrix_path",
        "training_result_planning_limitations_path",
        "training_result_planning_overfit_warnings_path",
        "training_result_planning_status_artifact_path",
        "training_result_planning_health_artifact_path",
        "metric_extension_metadata_path",
        "metric_extension_result_rows_path",
        "metric_extension_summary_path",
        "metric_extension_safety_flags_path",
        "metric_extension_status_artifact_path",
        "metric_extension_health_artifact_path",
        "metric_computation_metadata_path",
        "metric_computation_result_rows_path",
        "metric_computation_summary_path",
        "metric_computation_safety_flags_path",
        "metric_computation_status_artifact_path",
        "metric_computation_health_artifact_path",
        "metric_evaluation_metadata_path",
        "metric_evaluation_input_index_path",
        "metric_evaluation_sample_scope_path",
        "metric_evaluation_denominator_rules_path",
        "metric_evaluation_safety_flags_path",
        "metric_evaluation_status_artifact_path",
        "metric_evaluation_health_artifact_path",
        "training_evaluation_metadata_path",
        "training_evaluation_sample_rows_path",
        "training_evaluation_safety_flags_path",
        "training_evaluation_status_artifact_path",
        "training_evaluation_health_artifact_path",
        "forward_return_label_metadata_path",
        "forward_return_label_rows_path",
        "forward_return_label_status_artifact_path",
        "forward_return_label_health_artifact_path",
        "replay_decision_freeze_metadata_path",
        "replay_decision_freeze_rows_path",
        "replay_decision_freeze_status_artifact_path",
        "replay_decision_freeze_health_artifact_path",
        "leakage_evidence_bundle_path",
        "overclaim_evidence_bundle_path",
        "side_effect_evidence_bundle_path",
        "output_dir",
    ]
    args: list[object] = []
    for field in fields:
        args.extend([f"--{field.replace('_', '-')}", getattr(settings, field)])
    return args
