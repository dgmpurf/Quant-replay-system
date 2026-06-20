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
from test_model_weight_versioning import _happy_settings as _model_weight_versioning_happy_settings

from quant_replay_system.active_model import (
    ACTIVE_MODEL_APPROVAL_BLOCKED,
    ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED,
    ACTIVE_MODEL_HEALTH_BLOCKED,
    ACTIVE_MODEL_LEAKAGE_BLOCKED,
    ACTIVE_MODEL_LINEAGE_BLOCKED,
    ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED,
    ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED,
    ACTIVE_MODEL_OVERCLAIM_BLOCKED,
    ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED,
    ACTIVE_MODEL_SAFETY_FLAG_BLOCKED,
    ACTIVE_MODEL_SIDE_EFFECT_BLOCKED,
    ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED,
    EXACT_ACTIVE_MODEL_APPROVAL_TEXT,
    NO_ACTIVE_MODEL_INPUT,
    READY_FOR_ACTIVE_MODEL,
    ActiveModelSettings,
    run_active_model,
)
from quant_replay_system.model_weight_versioning import run_model_weight_versioning


DOWNSTREAM_FALSE_FIELDS = [
    "promoted_model_created",
    "production_model_created",
    "active_thresholds_created",
    "advisory_predictions_created",
    "active_probabilities_created",
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
    result = run_active_model(ActiveModelSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_ACTIVE_MODEL_INPUT
    assert result.workflow_stage == "ACTIVE_MODEL_NO_INPUT"
    assert result.ready_for_active_model is False
    assert result.active_model_executed is False
    assert result.active_model_artifacts_created is False
    assert result.active_model_pointer_created is False
    assert result.active_model_registry_entry_created is False
    assert result.active_parameter_pointer_created is False
    _assert_downstream_false(result)
    assert result.research_governed is True
    assert result.diagnostic_output is True
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


@pytest.mark.parametrize(
    "approval_text",
    ["", "continue", "go ahead", "activate it", "promote it", "use model", "make it live", "use predictions", "make it trade"],
)
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_active_model(settings)

    assert result.status == ACTIVE_MODEL_APPROVAL_BLOCKED
    assert result.active_model_artifacts_created is False
    assert result.active_model_pointer_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"promoted_model_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"production_model_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"active_thresholds_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"advisory_predictions_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"active_probabilities_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"stock_profile_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"buy_review_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"paper_approval_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ({"current_candidates_integration_requested": True}, ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ({"snapshot_build_requested": True}, ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ({"signal_semantics_mutation_requested": True}, ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ({"trading_requested": True}, ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
        ({"broker_api_called": True}, ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
        ({"order_placed": True}, ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
        ({"message_sent": True}, ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_approval_scope_and_side_effect_requests_block(
    tmp_path: Path, patch: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.active_model_request_manifest_path, patch)

    result = run_active_model(settings)

    assert result.status == expected_status
    assert result.active_model_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("model_weight_versioning_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weights_reference_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_version_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("parameter_version_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_input_index_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_lineage_matrix_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_limitations_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_overfit_warnings_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_safety_flags_path", ACTIVE_MODEL_SAFETY_FLAG_BLOCKED),
        ("model_weight_versioning_status_artifact_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weight_versioning_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_result_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_rows_path", ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_health_artifact_path", ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_result_planning_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_computation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_evaluation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_metadata_path", ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("leakage_evidence_bundle_path", ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", ACTIVE_MODEL_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_active_model(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.active_model_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("model_weight_versioning_metadata_path", {"status": "READY_FOR_MODEL_WEIGHT_VERSIONING"}, ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weight_versioning_health_artifact_path", {"status": "FAIL"}, ACTIVE_MODEL_HEALTH_BLOCKED),
        ("training_result_metadata_path", {"status": "NO_TRAINING_RESULT_INPUT"}, ACTIVE_MODEL_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_health_artifact_path", {"status": "FAIL"}, ACTIVE_MODEL_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"current_candidates_integration_requested": True}, ACTIVE_MODEL_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"trading_allowed": True}, ACTIVE_MODEL_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"active_model_not_performance_validation": False}, ACTIVE_MODEL_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_active_model(settings)

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_result_rows_path", "training_result_row_id", ACTIVE_MODEL_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_rows_path", "replay_decision_id", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "forward_return_label_id", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "available_time", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "source_hash", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "revision_id", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "quality_status", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "report_only", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("training_result_rows_path", "diagnostic_only", ACTIVE_MODEL_LINEAGE_BLOCKED),
        ("model_lineage_matrix_path", "lineage_item", ACTIVE_MODEL_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_active_model(settings)

    assert result.status == expected_status


def test_duplicate_sample_rows_without_quarantine_and_forbidden_artifacts_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame["quarantine_count"] = "0"
    frame.to_csv(settings.training_evaluation_sample_rows_path, index=False)
    assert run_active_model(settings).status == ACTIVE_MODEL_LINEAGE_BLOCKED

    settings = _happy_settings(tmp_path / "forbidden")
    (Path(settings.model_weight_versioning_metadata_path).parent / "stock_profile.json").write_text("{}", encoding="utf-8")
    assert run_active_model(settings).status == ACTIVE_MODEL_FORBIDDEN_ARTIFACT_BLOCKED


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_active_model(replace(_happy_settings(tmp_path), output_dir=tmp_path / "outputs" / "reports" / "active_model_v0_1"))


def test_happy_path_without_allow_is_ready_and_creates_no_active_model_artifacts(tmp_path: Path) -> None:
    result = run_active_model(_happy_settings(tmp_path))

    assert result.status == READY_FOR_ACTIVE_MODEL
    assert result.workflow_stage == READY_FOR_ACTIVE_MODEL
    assert result.ready_for_active_model is True
    assert result.active_model_executed is False
    assert result.active_model_artifacts_created is False
    assert result.active_model_pointer_created is False
    assert result.active_model_registry_entry_created is False
    assert result.active_parameter_pointer_created is False
    assert result.training_result_row_count == 1
    assert result.metric_evidence_reference_count == 7
    _assert_downstream_false(result)
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_happy_path_with_allow_creates_research_governed_active_model_artifacts(tmp_path: Path) -> None:
    result = run_active_model(replace(_happy_settings(tmp_path), allow_active_model=True))

    assert result.status == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED
    assert result.workflow_stage == ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED
    assert result.ready_for_active_model is True
    assert result.active_model_executed is True
    assert result.active_model_artifacts_created is True
    assert result.active_model_pointer_created is True
    assert result.active_model_registry_entry_created is True
    assert result.active_parameter_pointer_created is True
    assert result.active_model_activation_status_created is True
    assert result.active_model_rollback_plan_created is True
    assert result.active_model_input_index_created is True
    assert result.active_model_lineage_matrix_created is True
    assert result.active_model_limitations_created is True
    assert result.active_model_overfit_warnings_created is True
    assert result.active_model_safety_flags_created is True
    _assert_downstream_false(result)
    for key in _safe_artifact_keys() + _substantive_artifact_keys():
        assert result.artifact_paths[key].exists(), key

    metadata = _read_json(result.artifact_paths["active_model_metadata"])
    assert metadata["source_model_workflow_run_id"] == result.source_model_workflow_run_id
    assert metadata["model_weight_reference_id"] == result.model_weight_reference_id
    assert metadata["model_version_id"] == result.model_version_id
    assert metadata["parameter_version_id"] == result.parameter_version_id
    assert metadata["source_training_result_run_id"] == result.source_training_result_run_id
    assert metadata["source_training_result_planning_run_id"] == "trp_plan"
    assert metadata["source_metric_extension_run_id"] == "metric_ext_plan"
    assert metadata["source_metric_computation_run_id"] == "metric_comp_plan"
    assert metadata["source_metric_evaluation_planning_run_id"] == "metric_eval_plan"
    assert metadata["source_training_evaluation_run_id"] == "train_eval_plan"
    assert metadata["source_forward_return_label_run_id"] == "label_plan"
    assert metadata["source_replay_decision_freeze_run_id"] == "freeze_plan"

    pointer = _read_json(result.artifact_paths["active_model_pointer"])
    assert pointer["pointer_role"] == "research_governed_active_model"
    for phrase in ["promoted model", "production model", "active thresholds", "advisory predictions", "stock_profile", "paper approval", "trading permission"]:
        assert phrase in pointer["forbidden_interpretation"]
    assert pointer["serving_enabled"] is False
    assert pointer["current_candidates_integration"] is False
    assert pointer["snapshot_integration"] is False
    assert pointer["signal_semantics_mutated"] is False

    registry = _read_json(result.artifact_paths["active_model_registry_entry"])
    assert registry["promoted_model"] is False
    assert registry["production_model"] is False
    assert registry["serving_enabled"] is False

    parameter_pointer = _read_json(result.artifact_paths["active_parameter_pointer"])
    assert parameter_pointer["active_thresholds_created"] is False
    assert parameter_pointer["signal_semantics_mutated"] is False

    activation = _read_json(result.artifact_paths["active_model_activation_status"])
    assert activation["promoted_model_created"] is False
    assert activation["production_model_created"] is False
    assert activation["active_thresholds_created"] is False
    assert activation["advisory_predictions_created"] is False
    assert activation["active_probabilities_created"] is False
    assert activation["stock_profile_created"] is False
    assert activation["trading_allowed"] is False

    rollback = result.artifact_paths["active_model_rollback_plan"].read_text(encoding="utf-8").lower()
    assert "no production serving exists" in rollback
    assert "no broker/order/trading path exists" in rollback

    limitations = result.artifact_paths["active_model_limitations"].read_text(encoding="utf-8").lower()
    for phrase in [
        "no promoted model",
        "no production model",
        "no active thresholds",
        "no advisory predictions",
        "no active probabilities",
        "no stock_profile",
        "no buy-review",
        "no paper approval",
        "no performance validation",
        "no trading",
    ]:
        assert phrase in limitations

    warnings = pd.read_csv(result.artifact_paths["active_model_overfit_warnings"], dtype=str)
    assert {"small sample", "class imbalance", "single-stock overfit", "metric selection bias", "lookahead leakage"}.issubset(
        set(warnings["risk_item"])
    )

    safety = _read_json(result.artifact_paths["active_model_safety_flags"])
    assert safety["active_model_artifacts_created"] is True
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False

    report = result.artifact_paths["report"].read_text(encoding="utf-8").lower()
    for phrase in [
        "research-governed active model",
        "no promoted model",
        "no production model",
        "no active thresholds",
        "no advisory predictions",
        "no active probabilities",
        "no stock_profile",
        "no buy-review",
        "no paper approval",
        "no performance validation",
        "no trading",
    ]:
        assert phrase in report

    forbidden_names = [path.name for path in result.artifact_paths["artifact_dir"].iterdir()]
    assert not any(name.startswith(("promoted_model", "production_model", "active_threshold", "advisory_prediction", "active_probability", "stock_profile", "buy_review", "paper_approval", "performance_validation", "broker", "order", "trade")) for name in forbidden_names)


def test_cli_active_model_no_input_ready_and_allow_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["active-model", "--output-dir", _output_dir(tmp_path / "no_input")])
    assert "status: NO_ACTIVE_MODEL_INPUT" in no_input.stdout
    assert "active_model_artifacts_created: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "ready")
    ready = _run_cli(["active-model", *_cli_args(settings)])
    assert "status: READY_FOR_ACTIVE_MODEL" in ready.stdout
    assert "active_model_artifacts_created: False" in ready.stdout

    allowed = _run_cli(["active-model", *_cli_args(settings), "--allow-active-model"])
    assert "status: ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED" in allowed.stdout
    assert "active_model_artifacts_created: True" in allowed.stdout
    assert "stock_profile_created: False" in allowed.stdout
    assert "trading_allowed: False" in allowed.stdout

    help_result = _run_cli(["--help"])
    assert "active-model" in help_result.stdout
    assert "active-model-index" not in help_result.stdout
    assert "active-model-health" not in help_result.stdout
    assert "active-model-status" not in help_result.stdout
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> ActiveModelSettings:
    model_settings = _model_weight_versioning_happy_settings(tmp_path / "model_weight_source")
    model_result = run_model_weight_versioning(replace(model_settings, allow_model_weight_versioning=True))
    artifact_paths = model_result.artifact_paths
    root = tmp_path / "active_model_fixtures"
    root.mkdir(parents=True, exist_ok=True)

    return ActiveModelSettings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_ACTIVE_MODEL_APPROVAL_TEXT}),
        active_model_request_manifest_path=_write_json(root / "request.json", _safe_active_model_request()),
        model_weight_versioning_metadata_path=artifact_paths["model_training_metadata"],
        model_weights_reference_path=artifact_paths["model_weights_reference"],
        model_version_metadata_path=artifact_paths["model_version_metadata"],
        parameter_version_metadata_path=artifact_paths["parameter_version_metadata"],
        threshold_plan_path=artifact_paths["threshold_plan"],
        prediction_rows_path=artifact_paths["prediction_rows"],
        probability_calibration_report_path=artifact_paths["probability_calibration_report"],
        feature_importance_report_path=artifact_paths["feature_importance_report"],
        model_input_index_path=artifact_paths["model_input_index"],
        model_lineage_matrix_path=artifact_paths["model_lineage_matrix"],
        model_limitations_path=artifact_paths["model_limitations"],
        model_overfit_warnings_path=artifact_paths["model_overfit_warnings"],
        model_safety_flags_path=artifact_paths["model_safety_flags"],
        model_weight_versioning_status_artifact_path=_write_json(root / "model_weight_versioning_status.json", {"status": "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED"}),
        model_weight_versioning_health_artifact_path=_write_json(root / "model_weight_versioning_health.json", {"status": "PASS"}),
        training_result_metadata_path=model_settings.training_result_metadata_path,
        training_result_rows_path=model_settings.training_result_rows_path,
        training_result_status_artifact_path=model_settings.training_result_status_artifact_path,
        training_result_health_artifact_path=model_settings.training_result_health_artifact_path,
        training_result_planning_metadata_path=model_settings.training_result_planning_metadata_path,
        training_result_planning_health_artifact_path=model_settings.training_result_planning_health_artifact_path,
        metric_extension_metadata_path=model_settings.metric_extension_metadata_path,
        metric_extension_result_rows_path=model_settings.metric_extension_result_rows_path,
        metric_extension_health_artifact_path=model_settings.metric_extension_health_artifact_path,
        metric_computation_metadata_path=model_settings.metric_computation_metadata_path,
        metric_computation_result_rows_path=model_settings.metric_computation_result_rows_path,
        metric_computation_health_artifact_path=model_settings.metric_computation_health_artifact_path,
        metric_evaluation_metadata_path=model_settings.metric_evaluation_metadata_path,
        metric_evaluation_health_artifact_path=model_settings.metric_evaluation_health_artifact_path,
        training_evaluation_metadata_path=model_settings.training_evaluation_metadata_path,
        training_evaluation_sample_rows_path=model_settings.training_evaluation_sample_rows_path,
        training_evaluation_health_artifact_path=model_settings.training_evaluation_health_artifact_path,
        forward_return_label_metadata_path=model_settings.forward_return_label_metadata_path,
        forward_return_label_rows_path=model_settings.forward_return_label_rows_path,
        forward_return_label_health_artifact_path=model_settings.forward_return_label_health_artifact_path,
        replay_decision_freeze_metadata_path=model_settings.replay_decision_freeze_metadata_path,
        replay_decision_freeze_rows_path=model_settings.replay_decision_freeze_rows_path,
        replay_decision_freeze_health_artifact_path=model_settings.replay_decision_freeze_health_artifact_path,
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", _safe_leakage_bundle()),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _safe_overclaim_bundle()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_side_effects()),
        output_dir=_output_dir(tmp_path),
    )


def _safe_active_model_request() -> dict[str, object]:
    return {
        "active_model_phase_1_only": True,
        "promoted_model_requested": False,
        "production_model_requested": False,
        "active_thresholds_requested": False,
        "advisory_predictions_requested": False,
        "active_probabilities_requested": False,
        "stock_profile_requested": False,
        "buy_review_requested": False,
        "paper_approval_requested": False,
        "performance_validation_requested": False,
        "trading_requested": False,
        "current_candidates_integration_requested": False,
        "snapshot_build_requested": False,
        "signal_semantics_mutation_requested": False,
    }


def _safe_leakage_bundle() -> dict[str, object]:
    return {
        "current_candidates_integration_requested": False,
        "snapshot_build_requested": False,
        "signal_semantics_mutation_requested": False,
        "threshold_to_signal_binding_requested": False,
        "advisory_prediction_display_requested": False,
    }


def _safe_overclaim_bundle() -> dict[str, object]:
    return {
        "active_model_research_governed_only": True,
        "active_model_not_promoted_model": True,
        "active_model_not_production_model": True,
        "active_model_not_active_thresholds": True,
        "active_model_not_advisory_predictions": True,
        "active_model_not_active_probabilities": True,
        "active_model_not_stock_profile": True,
        "active_model_not_buy_review": True,
        "active_model_not_paper_approval": True,
        "active_model_not_performance_validation": True,
        "active_model_not_trading": True,
    }


def _safe_side_effects() -> dict[str, object]:
    return {
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "research_governed": True,
        "diagnostic_output": True,
    }


def _safe_artifact_keys() -> list[str]:
    return [
        "active_model_metadata",
        "report",
        "active_model_safety_flags",
        "active_model_precondition_results",
        "active_model_approval_results",
        "active_model_input_lineage_results",
        "active_model_model_weight_versioning_input_results",
        "active_model_metric_evidence_results",
        "active_model_leakage_guard_results",
        "active_model_side_effect_guard_results",
        "active_model_overclaim_guard_results",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "active_model_pointer",
        "active_model_registry_entry",
        "active_parameter_pointer",
        "active_model_activation_status",
        "active_model_rollback_plan",
        "active_model_input_index",
        "active_model_lineage_matrix",
        "active_model_limitations",
        "active_model_overfit_warnings",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "active_model_v0_1"


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


def _cli_args(settings: ActiveModelSettings) -> list[object]:
    args: list[object] = []
    for field in ActiveModelSettings.__dataclass_fields__:
        if field in {"allow_active_model", "write_artifacts", "research_governed", "diagnostic_output"}:
            continue
        value = getattr(settings, field)
        if value is None:
            continue
        args.extend([f"--{field.replace('_', '-')}", value])
    return args


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
