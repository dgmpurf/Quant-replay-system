from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).parent))
from test_training_result import _happy_settings as _training_result_happy_settings

from quant_replay_system.model_weight_versioning import (
    EXACT_MODEL_WEIGHT_VERSIONING_APPROVAL_TEXT,
    MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED,
    MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED,
    MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED,
    MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED,
    MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED,
    MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED,
    MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED,
    MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED,
    MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED,
    MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED,
    MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED,
    MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED,
    NO_MODEL_WEIGHT_VERSIONING_INPUT,
    READY_FOR_MODEL_WEIGHT_VERSIONING,
    ModelWeightVersioningSettings,
    run_model_weight_versioning,
)
from quant_replay_system.training_result import run_training_result


DOWNSTREAM_FALSE_FIELDS = [
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


def test_no_input_writes_safe_diagnostics_only(tmp_path: Path) -> None:
    result = run_model_weight_versioning(ModelWeightVersioningSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_MODEL_WEIGHT_VERSIONING_INPUT
    assert result.workflow_stage == "MODEL_WEIGHT_VERSIONING_NO_INPUT"
    assert result.ready_for_model_weight_versioning is False
    assert result.model_weight_versioning_executed is False
    assert result.model_weight_versioning_research_artifacts_created is False
    assert result.model_weights_reference_created is False
    assert result.model_version_metadata_created is False
    assert result.parameter_version_metadata_created is False
    assert result.threshold_plan_created is False
    assert result.prediction_rows_created is False
    assert result.probability_calibration_report_created is False
    assert result.feature_importance_report_created is False
    _assert_downstream_false(result)
    assert result.report_only is True
    assert result.diagnostic_only is True
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


@pytest.mark.parametrize("approval_text", ["", "continue", "go ahead", "train it", "build model", "optimize thresholds", "make predictions"])
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_model_weight_versioning(settings)

    assert result.status == MODEL_WEIGHT_VERSIONING_APPROVAL_BLOCKED
    assert result.model_weight_versioning_research_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"stock_profile_requested": True}, MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ({"buy_review_requested": True}, MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ({"paper_approval_requested": True}, MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ({"trading_requested": True}, MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
        ({"broker_api_called": True}, MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
        ({"order_placed": True}, MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
        ({"message_sent": True}, MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_approval_scope_and_side_effect_requests_block(tmp_path: Path, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.model_request_manifest_path, patch)

    result = run_model_weight_versioning(settings)

    assert result.status == expected_status
    assert result.model_weight_versioning_research_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("training_result_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_rows_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_result_input_index_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_metric_evidence_reference_path", MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED),
        ("training_result_lineage_matrix_path", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_limitations_path", MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED),
        ("training_result_overfit_warnings_path", MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED),
        ("training_result_safety_flags_path", MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED),
        ("training_result_planning_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_sample_rows_path", MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_rows_path", MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_rows_path", MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_model_weight_versioning(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.model_weight_versioning_research_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("training_result_metadata_path", {"status": "NO_TRAINING_RESULT_INPUT"}, MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_result_planning_metadata_path", {"status": "NO_TRAINING_RESULT_PLANNING_INPUT"}, MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("training_result_planning_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_extension_metadata_path", {"status": "NO_METRIC_EXTENSION_INPUT"}, MODEL_WEIGHT_VERSIONING_METRIC_EXTENSION_INPUT_BLOCKED),
        ("metric_extension_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_computation_metadata_path", {"status": "NO_METRIC_COMPUTATION_INPUT"}, MODEL_WEIGHT_VERSIONING_METRIC_COMPUTATION_INPUT_BLOCKED),
        ("metric_computation_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("metric_evaluation_metadata_path", {"status": "NO_METRIC_EVALUATION_INPUT"}, MODEL_WEIGHT_VERSIONING_METRIC_EVALUATION_INPUT_BLOCKED),
        ("metric_evaluation_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("training_evaluation_metadata_path", {"status": "NO_TRAINING_EVALUATION_INPUT"}, MODEL_WEIGHT_VERSIONING_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("training_evaluation_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("forward_return_label_metadata_path", {"status": "NO_FORWARD_RETURN_LABEL_INPUT"}, MODEL_WEIGHT_VERSIONING_FORWARD_LABEL_INPUT_BLOCKED),
        ("forward_return_label_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("replay_decision_freeze_metadata_path", {"status": "NO_REPLAY_DECISION_FREEZE_INPUT"}, MODEL_WEIGHT_VERSIONING_REPLAY_FREEZE_INPUT_BLOCKED),
        ("replay_decision_freeze_health_artifact_path", {"status": "FAIL"}, MODEL_WEIGHT_VERSIONING_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"future_label_leakage": True}, MODEL_WEIGHT_VERSIONING_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"broker_api_called": True}, MODEL_WEIGHT_VERSIONING_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"model_artifacts_not_performance_validation": False}, MODEL_WEIGHT_VERSIONING_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_model_weight_versioning(settings)

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_result_rows_path", "training_result_row_id", MODEL_WEIGHT_VERSIONING_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_rows_path", "replay_decision_id", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "forward_return_label_id", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "available_time", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "source_hash", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "revision_id", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "quality_status", MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED),
        ("training_result_rows_path", "report_only", MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED),
        ("training_result_rows_path", "diagnostic_only", MODEL_WEIGHT_VERSIONING_REPORT_ONLY_BLOCKED),
        ("training_result_metric_evidence_reference_path", "metric_name", MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_model_weight_versioning(settings)

    assert result.status == expected_status


def test_missing_metric_evidence_limitations_and_overfit_warnings_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    _drop_csv_rows(settings.training_result_metric_evidence_reference_path, "metric_name", "hit_rate")
    assert run_model_weight_versioning(settings).status == MODEL_WEIGHT_VERSIONING_METRIC_EVIDENCE_BLOCKED

    settings = _happy_settings(tmp_path / "limitations")
    settings.training_result_limitations_path.write_text("too short\n", encoding="utf-8")
    assert run_model_weight_versioning(settings).status == MODEL_WEIGHT_VERSIONING_LIMITATIONS_BLOCKED

    settings = _happy_settings(tmp_path / "warnings")
    _drop_csv_rows(settings.training_result_overfit_warnings_path, "risk_item", "lookahead leakage")
    assert run_model_weight_versioning(settings).status == MODEL_WEIGHT_VERSIONING_OVERFIT_WARNING_BLOCKED


def test_duplicate_sample_rows_without_quarantine_block_and_forbidden_artifacts_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame["quarantine_count"] = "0"
    frame.to_csv(settings.training_evaluation_sample_rows_path, index=False)
    assert run_model_weight_versioning(settings).status == MODEL_WEIGHT_VERSIONING_LINEAGE_BLOCKED

    settings = _happy_settings(tmp_path / "forbidden")
    (Path(settings.training_result_metadata_path).parent / "active_stock_profile.json").write_text("{}", encoding="utf-8")
    assert run_model_weight_versioning(settings).status == MODEL_WEIGHT_VERSIONING_FORBIDDEN_ARTIFACT_BLOCKED


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_model_weight_versioning(replace(_happy_settings(tmp_path), output_dir=tmp_path / "outputs" / "reports" / "model_weight_versioning_v0_1"))


def test_happy_path_without_allow_is_ready_and_creates_no_research_artifacts(tmp_path: Path) -> None:
    result = run_model_weight_versioning(_happy_settings(tmp_path))

    assert result.status == READY_FOR_MODEL_WEIGHT_VERSIONING
    assert result.workflow_stage == READY_FOR_MODEL_WEIGHT_VERSIONING
    assert result.ready_for_model_weight_versioning is True
    assert result.model_weight_versioning_executed is False
    assert result.model_weight_versioning_research_artifacts_created is False
    assert result.training_result_row_count == 1
    assert result.metric_evidence_reference_count == 7
    _assert_downstream_false(result)
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_happy_path_with_allow_creates_report_only_model_research_artifacts(tmp_path: Path) -> None:
    result = run_model_weight_versioning(replace(_happy_settings(tmp_path), allow_model_weight_versioning=True))

    assert result.status == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED
    assert result.workflow_stage == MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED
    assert result.ready_for_model_weight_versioning is True
    assert result.model_weight_versioning_executed is True
    assert result.model_weight_versioning_research_artifacts_created is True
    assert result.model_weights_reference_created is True
    assert result.model_version_metadata_created is True
    assert result.parameter_version_metadata_created is True
    assert result.threshold_plan_created is True
    assert result.prediction_rows_created is True
    assert result.probability_calibration_report_created is True
    assert result.feature_importance_report_created is True
    assert result.source_training_result_run_id
    assert result.source_training_result_planning_run_id == "trp_plan"
    assert result.source_metric_extension_run_id == "metric_ext_plan"
    assert result.source_metric_computation_run_id == "metric_comp_plan"
    assert result.source_metric_evaluation_planning_run_id == "metric_eval_plan"
    assert result.source_training_evaluation_run_id == "train_eval_plan"
    assert result.source_forward_return_label_run_id == "label_plan"
    assert result.source_replay_decision_freeze_run_id == "freeze_plan"
    _assert_downstream_false(result)
    for key in _safe_artifact_keys() + _substantive_artifact_keys():
        assert result.artifact_paths[key].exists(), key

    weights = _read_json(result.artifact_paths["model_weights_reference"])
    assert weights["reference_type"] == "report_only_reference"
    assert "executable trading model" in weights["forbidden_interpretation"]

    model_version = _read_json(result.artifact_paths["model_version_metadata"])
    assert model_version["active_model"] is False
    assert model_version["promoted_model"] is False

    parameter_version = _read_json(result.artifact_paths["parameter_version_metadata"])
    assert parameter_version["active_parameters"] is False

    threshold_plan = pd.read_csv(result.artifact_paths["threshold_plan"], dtype=str)
    assert threshold_plan["forbidden_interpretation"].str.contains("signal_semantics", regex=False).any()

    prediction_rows = pd.read_csv(result.artifact_paths["prediction_rows"], dtype=str)
    assert prediction_rows.loc[0, "symbol"] == "000001"
    assert prediction_rows["prediction_role"].eq("report_only_research").all()
    assert prediction_rows["forbidden_interpretation"].str.contains("advisory signals", regex=False).all()

    probability_report = result.artifact_paths["probability_calibration_report"].read_text(encoding="utf-8")
    assert "no active probabilities" in probability_report

    feature_importance = pd.read_csv(result.artifact_paths["feature_importance_report"], dtype=str)
    assert feature_importance["forbidden_interpretation"].str.contains("active stock_profile", regex=False).all()

    limitations = result.artifact_paths["model_limitations"].read_text(encoding="utf-8")
    for phrase in ["report-only research artifacts", "no stock_profile", "no buy-review", "no paper approval", "no performance validation", "no trading"]:
        assert phrase in limitations

    warnings = pd.read_csv(result.artifact_paths["model_overfit_warnings"], dtype=str)
    for risk in ["small sample", "class imbalance", "single-stock overfit", "metric selection bias", "lookahead leakage"]:
        assert risk in set(warnings["risk_item"])

    safety = _read_json(result.artifact_paths["model_safety_flags"])
    assert safety["model_weight_versioning_research_artifacts_created"] is True
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False, field

    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    for phrase in ["report-only research artifacts", "no stock_profile", "no buy-review", "no paper approval", "no performance validation", "no trading"]:
        assert phrase in report

    filenames = [path.name for path in Path(result.artifact_path).iterdir()]
    assert not any(name.startswith(("active_stock_profile", "stock_profile", "buy_review", "paper_approval", "approved_for_paper", "performance_validation", "strategy_performance", "broker", "order", "trade", "message")) for name in filenames)


def test_metric_evidence_reference_and_lineage_are_preserved(tmp_path: Path) -> None:
    result = run_model_weight_versioning(replace(_happy_settings(tmp_path), allow_model_weight_versioning=True))

    input_index = pd.read_csv(result.artifact_paths["model_input_index"], dtype=str)
    assert input_index["source_run_id"].str.contains(result.source_training_result_run_id).any()

    lineage = pd.read_csv(result.artifact_paths["model_lineage_matrix"], dtype=str)
    assert {"training_result_run_id", "training_result_planning_run_id", "metric_extension_run_id", "metric_computation_run_id", "metric_evaluation_run_id", "training_evaluation_run_id", "forward_return_label_run_id", "replay_decision_freeze_run_id"}.issubset(set(lineage["lineage_item"]))

    metadata = _read_json(result.artifact_paths["model_training_metadata"])
    assert metadata["source_training_result_run_id"] == result.source_training_result_run_id
    assert metadata["metric_evidence_reference_count"] == 7


def test_cli_no_input_ready_and_allow_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["model-weight-versioning", "--output-dir", _output_dir(tmp_path / "no_input")])
    assert "status: NO_MODEL_WEIGHT_VERSIONING_INPUT" in no_input.stdout
    assert "model_weight_versioning_research_artifacts_created: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "ready")
    ready = _run_cli(["model-weight-versioning", *_cli_args(settings)])
    assert "status: READY_FOR_MODEL_WEIGHT_VERSIONING" in ready.stdout
    assert "model_weight_versioning_research_artifacts_created: False" in ready.stdout

    settings = _happy_settings(tmp_path / "allow")
    allowed = _run_cli(["model-weight-versioning", *_cli_args(settings), "--allow-model-weight-versioning"])
    assert "status: MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED" in allowed.stdout
    assert "model_weights_reference_created: True" in allowed.stdout


def test_no_extra_commands_research_status_checkpoint_or_project_source_are_added() -> None:
    help_result = _run_cli(["--help"])
    assert "model-weight-versioning" in help_result.stdout
    assert "model-weight-versioning-index" not in help_result.stdout
    assert "model-weight-versioning-health" not in help_result.stdout
    assert "model-weight-versioning-status" not in help_result.stdout
    assert not Path("docs/project_sources").exists()
    assert not list(Path("docs").glob("release_checkpoint_v1.51.0.md"))


def _happy_settings(tmp_path: Path) -> ModelWeightVersioningSettings:
    training_settings = _training_result_happy_settings(tmp_path / "training_result_source")
    training_result = run_training_result(replace(training_settings, allow_training_result=True))
    artifact_paths = training_result.artifact_paths
    root = tmp_path / "model_fixtures"
    root.mkdir(parents=True, exist_ok=True)
    approval = _write_json(root / "approval.json", {"approval_text": EXACT_MODEL_WEIGHT_VERSIONING_APPROVAL_TEXT})
    request = _write_json(root / "request.json", _safe_model_request())
    leakage = _write_json(root / "leakage.json", {"future_label_leakage": False, "training_result_leakage": False})
    overclaim = _write_json(root / "overclaim.json", _overclaim_bundle())
    side_effect = _write_json(root / "side_effect.json", _safe_side_effects())

    return ModelWeightVersioningSettings(
        approval_manifest_path=approval,
        model_request_manifest_path=request,
        training_result_metadata_path=artifact_paths["metadata"],
        training_result_rows_path=artifact_paths["rows"],
        training_result_status_artifact_path=artifact_paths["status_json"],
        training_result_health_artifact_path=_write_json(root / "training_result_health.json", {"status": "PASS"}),
        training_result_input_index_path=artifact_paths["input_index"],
        training_result_metric_evidence_reference_path=artifact_paths["metric_evidence_reference"],
        training_result_lineage_matrix_path=artifact_paths["lineage_matrix"],
        training_result_limitations_path=artifact_paths["limitations"],
        training_result_overfit_warnings_path=artifact_paths["overfit_warnings"],
        training_result_safety_flags_path=artifact_paths["safety_flags"],
        training_result_planning_metadata_path=training_settings.training_result_planning_metadata_path,
        training_result_planning_health_artifact_path=training_settings.training_result_planning_health_artifact_path,
        metric_extension_metadata_path=training_settings.metric_extension_metadata_path,
        metric_extension_result_rows_path=training_settings.metric_extension_result_rows_path,
        metric_extension_health_artifact_path=training_settings.metric_extension_health_artifact_path,
        metric_computation_metadata_path=training_settings.metric_computation_metadata_path,
        metric_computation_result_rows_path=training_settings.metric_computation_result_rows_path,
        metric_computation_health_artifact_path=training_settings.metric_computation_health_artifact_path,
        metric_evaluation_metadata_path=training_settings.metric_evaluation_metadata_path,
        metric_evaluation_health_artifact_path=training_settings.metric_evaluation_health_artifact_path,
        training_evaluation_metadata_path=training_settings.training_evaluation_metadata_path,
        training_evaluation_sample_rows_path=training_settings.training_evaluation_sample_rows_path,
        training_evaluation_health_artifact_path=training_settings.training_evaluation_health_artifact_path,
        forward_return_label_metadata_path=training_settings.forward_return_label_metadata_path,
        forward_return_label_rows_path=training_settings.forward_return_label_rows_path,
        forward_return_label_health_artifact_path=training_settings.forward_return_label_health_artifact_path,
        replay_decision_freeze_metadata_path=training_settings.replay_decision_freeze_metadata_path,
        replay_decision_freeze_rows_path=training_settings.replay_decision_freeze_rows_path,
        replay_decision_freeze_health_artifact_path=training_settings.replay_decision_freeze_health_artifact_path,
        leakage_evidence_bundle_path=leakage,
        overclaim_evidence_bundle_path=overclaim,
        side_effect_evidence_bundle_path=side_effect,
        output_dir=_output_dir(tmp_path),
    )


def _safe_model_request() -> dict[str, object]:
    return {
        "model_weight_versioning_report_only": True,
        "stock_profile_requested": False,
        "buy_review_requested": False,
        "paper_approval_requested": False,
        "performance_validation_requested": False,
        "trading_requested": False,
    }


def _overclaim_bundle() -> dict[str, object]:
    return {
        "model_artifacts_report_only": True,
        "model_artifacts_not_stock_profile": True,
        "model_artifacts_not_buy_review": True,
        "model_artifacts_not_paper_approval": True,
        "model_artifacts_not_performance_validation": True,
        "model_artifacts_not_trading": True,
    }


def _safe_side_effects() -> dict[str, object]:
    return {
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": True,
        "diagnostic_only": True,
    }


def _safe_artifact_keys() -> list[str]:
    return [
        "model_training_metadata",
        "report",
        "model_safety_flags",
        "model_precondition_results",
        "model_approval_results",
        "model_input_lineage_results",
        "model_training_result_input_results",
        "model_metric_evidence_results",
        "model_leakage_guard_results",
        "model_side_effect_guard_results",
        "model_overclaim_guard_results",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "model_weights_reference",
        "model_version_metadata",
        "parameter_version_metadata",
        "threshold_plan",
        "prediction_rows",
        "probability_calibration_report",
        "feature_importance_report",
        "model_input_index",
        "model_lineage_matrix",
        "model_limitations",
        "model_overfit_warnings",
    ]


def _assert_downstream_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path, patch: dict[str, object]) -> None:
    payload = _read_json(path)
    payload.update(patch)
    _write_json(path, payload)


def _drop_csv_rows(path: Path, column: str, value: str) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame = frame[frame[column].astype(str) != value]
    frame.to_csv(path, index=False)


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "model_weight_versioning_v0_1"


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


def _cli_args(settings: ModelWeightVersioningSettings) -> list[object]:
    args: list[object] = []
    for field in ModelWeightVersioningSettings.__dataclass_fields__:
        if field in {"allow_model_weight_versioning", "write_artifacts", "report_only", "diagnostic_only"}:
            continue
        value = getattr(settings, field)
        if value is None:
            continue
        args.extend([f"--{field.replace('_', '-')}", value])
    return args
