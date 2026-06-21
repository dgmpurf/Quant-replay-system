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
from test_active_model import _happy_settings as _active_model_happy_settings

from quant_replay_system.active_model import run_active_model
from quant_replay_system.stock_profile import (
    EXACT_STOCK_PROFILE_APPROVAL_TEXT,
    NO_STOCK_PROFILE_INPUT,
    READY_FOR_STOCK_PROFILE_PHASE1,
    STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED,
    STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED,
    STOCK_PROFILE_APPROVAL_BLOCKED,
    STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED,
    STOCK_PROFILE_HEALTH_BLOCKED,
    STOCK_PROFILE_LEAKAGE_BLOCKED,
    STOCK_PROFILE_LINEAGE_BLOCKED,
    STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED,
    STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED,
    STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED,
    STOCK_PROFILE_OVERCLAIM_BLOCKED,
    STOCK_PROFILE_OVERFIT_WARNING_BLOCKED,
    STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    STOCK_PROFILE_SAFETY_FLAG_BLOCKED,
    STOCK_PROFILE_SIDE_EFFECT_BLOCKED,
    STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED,
    StockProfileSettings,
    run_stock_profile,
)
from quant_replay_system.stock_profile_health import check_stock_profile_health
from quant_replay_system.stock_profile_index import build_stock_profile_index
from quant_replay_system.stock_profile_status import run_stock_profile_status


DOWNSTREAM_FALSE_FIELDS = [
    "active_stock_profile_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "approved_for_paper",
    "strategy_performance_validated",
    "trading_allowed",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "promoted_model_created",
    "production_model_created",
    "active_thresholds_created",
    "advisory_predictions_created",
    "active_probabilities_created",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]


def test_no_input_writes_safe_diagnostics_only(tmp_path: Path) -> None:
    result = run_stock_profile(StockProfileSettings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_STOCK_PROFILE_INPUT
    assert result.workflow_stage == "STOCK_PROFILE_NO_INPUT"
    assert result.ready_for_stock_profile_phase1 is False
    assert result.stock_profile_phase1_executed is False
    assert result.stock_profile_phase1_report_only_artifacts_created is False
    assert result.stock_profile_metadata_created is False
    assert result.stock_profile_input_index_created is False
    assert result.stock_profile_lineage_matrix_created is False
    assert result.stock_profile_factor_coverage_summary_created is False
    assert result.stock_profile_symbol_coverage_created is False
    assert result.stock_profile_market_regime_coverage_created is False
    assert result.stock_profile_metric_summary_created is False
    assert result.stock_profile_limitations_created is False
    assert result.stock_profile_overfit_warnings_created is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


@pytest.mark.parametrize(
    "approval_text",
    [
        "",
        "continue",
        "go ahead",
        "create stock profile",
        "activate stock profile",
        "make it usable",
        "show buy candidates",
        "use it in candidates",
        "approve paper",
        "validate performance",
        "make it trade",
    ],
)
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_stock_profile(settings)

    assert result.status == STOCK_PROFILE_APPROVAL_BLOCKED
    assert result.stock_profile_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"real_buy_review_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"buy_review_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"paper_approval_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"promoted_model_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"production_model_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"active_thresholds_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"advisory_predictions_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"active_probabilities_requested": True}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ({"current_candidates_integration_requested": True}, STOCK_PROFILE_LEAKAGE_BLOCKED),
        ({"snapshot_build_requested": True}, STOCK_PROFILE_LEAKAGE_BLOCKED),
        ({"signal_semantics_mutation_requested": True}, STOCK_PROFILE_LEAKAGE_BLOCKED),
        ({"trading_requested": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
        ({"broker_api_called": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
        ({"order_placed": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
        ({"message_sent": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
        ({"external_api_called": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_approval_scope_and_side_effect_requests_block(
    tmp_path: Path, patch: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.stock_profile_request_manifest_path, patch)

    result = run_stock_profile(settings)

    assert result.status == expected_status
    assert result.stock_profile_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("active_model_metadata_path", STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED),
        ("active_model_pointer_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_registry_entry_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_parameter_pointer_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_activation_status_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_input_index_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_lineage_matrix_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_limitations_path", STOCK_PROFILE_ACTIVE_MODEL_ARTIFACT_BLOCKED),
        ("active_model_overfit_warnings_path", STOCK_PROFILE_OVERFIT_WARNING_BLOCKED),
        ("active_model_safety_flags_path", STOCK_PROFILE_SAFETY_FLAG_BLOCKED),
        ("active_model_status_artifact_path", STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED),
        ("active_model_health_artifact_path", STOCK_PROFILE_HEALTH_BLOCKED),
        ("model_weight_versioning_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weights_reference_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_version_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("parameter_version_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_input_index_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_lineage_matrix_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_limitations_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_ARTIFACT_BLOCKED),
        ("model_overfit_warnings_path", STOCK_PROFILE_OVERFIT_WARNING_BLOCKED),
        ("model_safety_flags_path", STOCK_PROFILE_SAFETY_FLAG_BLOCKED),
        ("training_result_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_result_rows_path", STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_planning_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED),
        ("metric_computation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("metric_computation_result_rows_path", STOCK_PROFILE_METRIC_EVIDENCE_BLOCKED),
        ("metric_evaluation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("training_evaluation_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("forward_return_label_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("replay_decision_freeze_metadata_path", STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("leakage_evidence_bundle_path", STOCK_PROFILE_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", STOCK_PROFILE_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.stock_profile_phase1_report_only_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("active_model_metadata_path", {"status": "NO_ACTIVE_MODEL_INPUT"}, STOCK_PROFILE_ACTIVE_MODEL_INPUT_BLOCKED),
        ("active_model_health_artifact_path", {"status": "FAIL"}, STOCK_PROFILE_HEALTH_BLOCKED),
        ("model_weight_versioning_metadata_path", {"status": "READY_FOR_MODEL_WEIGHT_VERSIONING"}, STOCK_PROFILE_MODEL_WEIGHT_VERSIONING_INPUT_BLOCKED),
        ("model_weight_versioning_health_artifact_path", {"status": "FAIL"}, STOCK_PROFILE_HEALTH_BLOCKED),
        ("training_result_metadata_path", {"status": "NO_TRAINING_RESULT_INPUT"}, "STOCK_PROFILE_TRAINING_RESULT_INPUT_BLOCKED"),
        ("training_result_health_artifact_path", {"status": "FAIL"}, STOCK_PROFILE_HEALTH_BLOCKED),
        ("leakage_evidence_bundle_path", {"current_candidates_integration_requested": True}, STOCK_PROFILE_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"trading_allowed": True}, STOCK_PROFILE_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"stock_profile_not_performance_validation": False}, STOCK_PROFILE_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_stock_profile(settings)

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_result_rows_path", "training_result_row_id", STOCK_PROFILE_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_rows_path", "replay_decision_id", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "forward_return_label_id", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "source_hash", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "revision_id", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "available_time", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "quality_status", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "report_only", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "diagnostic_only", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("training_result_rows_path", "research_governed", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("active_model_lineage_matrix_path", "lineage_item", STOCK_PROFILE_LINEAGE_BLOCKED),
        ("model_lineage_matrix_path", "lineage_item", STOCK_PROFILE_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_stock_profile(settings)

    assert result.status == expected_status


def test_duplicate_sample_rows_and_forbidden_artifacts_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(settings.training_evaluation_sample_rows_path, dtype=str)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame["quarantine_count"] = "0"
    frame.to_csv(settings.training_evaluation_sample_rows_path, index=False)
    assert run_stock_profile(settings).status == STOCK_PROFILE_LINEAGE_BLOCKED

    settings = _happy_settings(tmp_path / "forbidden")
    (Path(settings.active_model_metadata_path).parent / "buy_review_candidate.csv").write_text("", encoding="utf-8")
    assert run_stock_profile(settings).status == STOCK_PROFILE_FORBIDDEN_ARTIFACT_BLOCKED


def test_output_path_outside_manual_diagnostics_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manual_diagnostics"):
        run_stock_profile(replace(_happy_settings(tmp_path), output_dir=tmp_path / "outputs" / "reports" / "stock_profile_v0_1"))


def test_happy_path_without_allow_is_ready_and_creates_no_substantive_artifacts(tmp_path: Path) -> None:
    result = run_stock_profile(_happy_settings(tmp_path))

    assert result.status == READY_FOR_STOCK_PROFILE_PHASE1
    assert result.workflow_stage == READY_FOR_STOCK_PROFILE_PHASE1
    assert result.ready_for_stock_profile_phase1 is True
    assert result.stock_profile_phase1_executed is False
    assert result.stock_profile_phase1_report_only_artifacts_created is False
    assert result.training_result_row_count == 1
    assert result.metric_evidence_reference_count == 7
    _assert_downstream_false(result)
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_happy_path_with_allow_creates_report_only_research_governed_stock_profile_artifacts(tmp_path: Path) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), allow_stock_profile=True))

    assert result.status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.workflow_stage == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.ready_for_stock_profile_phase1 is True
    assert result.stock_profile_phase1_executed is True
    assert result.stock_profile_phase1_report_only_artifacts_created is True
    assert result.stock_profile_metadata_created is True
    assert result.stock_profile_input_index_created is True
    assert result.stock_profile_lineage_matrix_created is True
    assert result.stock_profile_factor_coverage_summary_created is True
    assert result.stock_profile_symbol_coverage_created is True
    assert result.stock_profile_market_regime_coverage_created is True
    assert result.stock_profile_metric_summary_created is True
    assert result.stock_profile_limitations_created is True
    assert result.stock_profile_overfit_warnings_created is True
    assert result.stock_profile_safety_flags_created is True
    _assert_downstream_false(result)
    for key in _safe_artifact_keys() + _substantive_artifact_keys():
        assert result.artifact_paths[key].exists(), key

    metadata = _read_json(result.artifact_paths["stock_profile_metadata"])
    assert metadata["source_active_model_run_id"] == result.source_active_model_run_id
    assert metadata["source_model_workflow_run_id"] == result.source_model_workflow_run_id
    assert metadata["model_weight_reference_id"] == result.model_weight_reference_id
    assert metadata["model_version_id"] == result.model_version_id
    assert metadata["parameter_version_id"] == result.parameter_version_id
    assert metadata["source_training_result_run_id"] == result.source_training_result_run_id
    assert metadata["source_metric_extension_run_id"] == "metric_ext_plan"
    assert metadata["source_metric_computation_run_id"] == "metric_comp_plan"
    assert metadata["source_metric_evaluation_planning_run_id"] == "metric_eval_plan"
    assert metadata["source_forward_return_label_run_id"] == "label_plan"
    assert metadata["source_replay_decision_freeze_run_id"] == "freeze_plan"

    lineage = pd.read_csv(result.artifact_paths["stock_profile_lineage_matrix"], dtype=str)
    for item in [
        "stock_profile_run_id",
        "active_model_run_id",
        "model_workflow_run_id",
        "model_weight_reference_id",
        "model_version_id",
        "parameter_version_id",
        "training_result_run_id",
        "training_result_row_id",
        "metric_extension_run_id",
        "metric_computation_run_id",
        "metric_evaluation_run_id",
        "forward_return_label_run_id",
        "replay_decision_freeze_run_id",
        "symbol",
        "factor_layer",
        "metric_name",
        "source_hash",
        "revision_id",
        "available_time",
        "quality_status",
    ]:
        assert item in set(lineage["lineage_item"])

    factor = pd.read_csv(result.artifact_paths["stock_profile_factor_coverage_summary"], dtype=str)
    assert len(factor) == 8
    assert "not fixed 12-factor final coverage" in " ".join(factor["notes"].str.lower())

    metrics = pd.read_csv(result.artifact_paths["stock_profile_metric_summary"], dtype=str)
    assert set(metrics["metric_name"]) == {
        "sample_count",
        "label_coverage",
        "average_return",
        "median_return",
        "hit_rate",
        "benchmark_relative_return",
        "industry_relative_return",
    }
    joined_metric_interpretation = " ".join(metrics["interpretation"].str.lower())
    assert "not profitability proof" in joined_metric_interpretation
    assert "not strategy validation" in joined_metric_interpretation

    symbol = pd.read_csv(result.artifact_paths["stock_profile_symbol_coverage"], dtype=str)
    assert not bool(symbol["real_buy_review_eligible"].map(_truthy).any())

    regime = pd.read_csv(result.artifact_paths["stock_profile_market_regime_coverage"], dtype=str)
    assert not regime["interpretation"].str.contains("robustness validation", case=False, regex=False).any()

    limitations = result.artifact_paths["stock_profile_limitations"].read_text(encoding="utf-8").lower()
    for phrase in [
        "report-only and research-governed",
        "not trading instruction",
        "no real buy-review eligibility",
        "no paper approval",
        "no strategy performance validation",
        "no current-candidates integration",
        "no snapshot integration",
        "no signal_semantics mutation",
        "no broker/order/message/api/trading",
        "no promoted model",
        "no production model",
        "no active thresholds",
        "no advisory predictions",
        "no active probabilities",
        "not profitability proof",
    ]:
        assert phrase in limitations

    warnings = pd.read_csv(result.artifact_paths["stock_profile_overfit_warnings"], dtype=str)
    for warning in [
        "small sample",
        "class imbalance",
        "single-stock overfit",
        "single-industry overfit",
        "metric selection bias",
        "lookahead leakage",
        "stock-profile overfit",
    ]:
        assert warning in set(warnings["risk_item"])

    safety = _read_json(result.artifact_paths["stock_profile_safety_flags"])
    assert safety["stock_profile_phase1_report_only_artifacts_created"] is True
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False

    forbidden_names = [path.name for path in result.artifact_paths["artifact_dir"].iterdir()]
    assert not any(
        name.startswith(
            (
                "buy_review",
                "paper_approval",
                "performance_validation",
                "current_candidates",
                "snapshot",
                "signal_semantics",
                "broker",
                "order",
                "trade",
                "promoted_model",
                "production_model",
                "active_threshold",
                "advisory_prediction",
                "active_probability",
            )
        )
        for name in forbidden_names
    )


def test_cli_stock_profile_no_input_ready_and_allow_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["stock-profile", "--output-dir", _output_dir(tmp_path / "no_input")])
    assert "status: NO_STOCK_PROFILE_INPUT" in no_input.stdout
    assert "stock_profile_phase1_report_only_artifacts_created: False" in no_input.stdout
    assert "active_stock_profile_created: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "ready")
    ready = _run_cli(["stock-profile", *_cli_args(settings)])
    assert "status: READY_FOR_STOCK_PROFILE_PHASE1" in ready.stdout
    assert "stock_profile_phase1_report_only_artifacts_created: False" in ready.stdout

    allowed = _run_cli(["stock-profile", *_cli_args(settings), "--allow-stock-profile"])
    assert "status: STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED" in allowed.stdout
    assert "stock_profile_phase1_report_only_artifacts_created: True" in allowed.stdout
    assert "active_stock_profile_created: False" in allowed.stdout
    assert "trading_allowed: False" in allowed.stdout

    help_result = _run_cli(["--help"])
    assert "stock-profile" in help_result.stdout
    assert "stock-profile-index" in help_result.stdout
    assert "stock-profile-health" in help_result.stdout
    assert "stock-profile-status" in help_result.stdout
    assert not Path("docs/project_sources").exists()
    assert not Path("docs/release_checkpoint_v1.53.0.md").exists()


def test_stock_profile_index_discovers_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    no_input = run_stock_profile(StockProfileSettings(output_dir=_output_dir(tmp_path)))
    ready_settings = replace(_happy_settings(tmp_path / "ready"), output_dir=_output_dir(tmp_path))
    ready = run_stock_profile(ready_settings)
    created = run_stock_profile(replace(ready_settings, allow_stock_profile=True))

    result = build_stock_profile_index(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "index")

    assert result.artifact_count == 3
    frame = result.index_frame.set_index("stock_profile_run_id")
    assert frame.loc[no_input.stock_profile_run_id, "status"] == NO_STOCK_PROFILE_INPUT
    assert frame.loc[ready.stock_profile_run_id, "status"] == READY_FOR_STOCK_PROFILE_PHASE1
    assert frame.loc[created.stock_profile_run_id, "status"] == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    created_row = frame.loc[created.stock_profile_run_id]
    assert created_row["stock_profile_input_index_created"] is True
    assert created_row["stock_profile_lineage_matrix_created"] is True
    assert created_row["stock_profile_factor_coverage_summary_created"] is True
    assert created_row["stock_profile_symbol_coverage_created"] is True
    assert created_row["stock_profile_market_regime_coverage_created"] is True
    assert created_row["stock_profile_metric_summary_created"] is True
    assert created_row["stock_profile_limitations_created"] is True
    assert created_row["stock_profile_overfit_warnings_created"] is True
    assert created_row["stock_profile_safety_flags_created"] is True
    assert created_row["source_active_model_run_id"]
    assert created_row["source_model_workflow_run_id"]
    assert created_row["model_weight_reference_id"]
    assert created_row["factor_layer_count"] == 8
    assert created_row["factor_coverage_row_count"] == 8
    assert created_row["symbol_coverage_row_count"] == 1
    assert created_row["market_regime_coverage_row_count"] == 1
    assert created_row["metric_summary_row_count"] == 7
    assert created_row["overfit_warning_row_count"] >= 18
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert created_row[field] is False
    assert result.artifact_paths["index_csv"].exists()
    assert result.artifact_paths["index_report"].exists()


@pytest.mark.parametrize(
    "artifact_key",
    [
        "stock_profile_metadata",
        "stock_profile_input_index",
        "stock_profile_lineage_matrix",
        "stock_profile_factor_coverage_summary",
        "stock_profile_symbol_coverage",
        "stock_profile_market_regime_coverage",
        "stock_profile_metric_summary",
        "stock_profile_limitations",
        "stock_profile_overfit_warnings",
        "stock_profile_safety_flags",
    ],
)
def test_stock_profile_health_fails_if_created_artifact_is_missing(tmp_path: Path, artifact_key: str) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), allow_stock_profile=True))
    result.artifact_paths[artifact_key].unlink()

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert health.error_count >= 1


@pytest.mark.parametrize("status_name", [NO_STOCK_PROFILE_INPUT, READY_FOR_STOCK_PROFILE_PHASE1])
def test_stock_profile_health_fails_if_report_only_created_flag_is_true_before_created_state(
    tmp_path: Path, status_name: str
) -> None:
    if status_name == NO_STOCK_PROFILE_INPUT:
        result = run_stock_profile(StockProfileSettings(output_dir=_output_dir(tmp_path)))
    else:
        result = run_stock_profile(_happy_settings(tmp_path))
    _patch_json(result.artifact_paths["stock_profile_metadata"], {"stock_profile_phase1_report_only_artifacts_created": True})
    _patch_json(result.artifact_paths["stock_profile_safety_flags"], {"stock_profile_phase1_report_only_artifacts_created": True})

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "STOCK_PROFILE_REPORT_ONLY_ARTIFACTS_CREATED_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_stock_profile_health_fails_if_created_state_flag_is_false(tmp_path: Path) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), allow_stock_profile=True))
    _patch_json(result.artifact_paths["stock_profile_metadata"], {"stock_profile_phase1_report_only_artifacts_created": False})
    _patch_json(result.artifact_paths["stock_profile_safety_flags"], {"stock_profile_phase1_report_only_artifacts_created": False})

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert "STOCK_PROFILE_REPORT_ONLY_ARTIFACTS_CREATED_FLAG_FALSE" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("field", DOWNSTREAM_FALSE_FIELDS)
def test_stock_profile_health_fails_if_downstream_or_side_effect_flag_is_true(tmp_path: Path, field: str) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), allow_stock_profile=True))
    _patch_json(result.artifact_paths["stock_profile_safety_flags"], {field: True})

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "FAIL"
    assert f"{field.upper()}_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_stock_profile_health_fails_for_lineage_factor_metric_limitation_warning_and_forbidden_artifact_issues(
    tmp_path: Path,
) -> None:
    result = run_stock_profile(replace(_happy_settings(tmp_path), allow_stock_profile=True))
    pd.read_csv(result.artifact_paths["stock_profile_factor_coverage_summary"], dtype=str).query(
        "factor_layer != 'market_structure'"
    ).to_csv(result.artifact_paths["stock_profile_factor_coverage_summary"], index=False)
    pd.DataFrame([{"metric_name": "profitability_proof", "interpretation": "strategy performance validation"}]).to_csv(
        result.artifact_paths["stock_profile_metric_summary"], index=False
    )
    result.artifact_paths["stock_profile_limitations"].write_text(
        "# Missing limits\nThis is report-only.\n", encoding="utf-8"
    )
    pd.DataFrame([{"risk_item": "small sample"}]).to_csv(result.artifact_paths["stock_profile_overfit_warnings"], index=False)
    (result.artifact_paths["artifact_dir"] / "buy_review_candidate.csv").write_text("", encoding="utf-8")
    lineage = pd.read_csv(result.artifact_paths["stock_profile_input_index"], dtype=str)
    lineage.loc[0, "source_run_id"] = ""
    lineage.to_csv(result.artifact_paths["stock_profile_input_index"], index=False)

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    issue_codes = set(health.health_frame["issue_code"])
    assert health.status == "FAIL"
    assert "STOCK_PROFILE_FACTOR_LAYER_TAXONOMY_INCOMPLETE" in issue_codes
    assert "STOCK_PROFILE_METRIC_SUMMARY_UNAPPROVED_METRIC" in issue_codes
    assert "STOCK_PROFILE_METRIC_SUMMARY_OVERCLAIM" in issue_codes
    assert "STOCK_PROFILE_LIMITATIONS_WORDING_MISSING" in issue_codes
    assert "STOCK_PROFILE_OVERFIT_WARNING_MISSING" in issue_codes
    assert "FORBIDDEN_STOCK_PROFILE_DOWNSTREAM_ARTIFACT_PRESENT" in issue_codes
    assert "STOCK_PROFILE_INPUT_INDEX_LINEAGE_MISSING" in issue_codes


def test_stock_profile_health_passes_for_valid_no_input_ready_and_created_artifacts(tmp_path: Path) -> None:
    run_stock_profile(StockProfileSettings(output_dir=_output_dir(tmp_path)))
    ready_settings = replace(_happy_settings(tmp_path / "ready"), output_dir=_output_dir(tmp_path))
    run_stock_profile(ready_settings)
    run_stock_profile(replace(ready_settings, allow_stock_profile=True))

    health = check_stock_profile_health(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "health")

    assert health.status == "PASS"
    assert health.error_count == 0
    assert health.checked_artifact_count == 3
    assert health.artifact_paths["health_csv"].exists()
    assert health.artifact_paths["health_report"].exists()


def test_stock_profile_status_reports_latest_state_and_safety_wording(tmp_path: Path) -> None:
    ready_settings = replace(_happy_settings(tmp_path), output_dir=_output_dir(tmp_path))
    created = run_stock_profile(replace(ready_settings, allow_stock_profile=True))

    status = run_stock_profile_status(root=_output_dir(tmp_path), output_dir=_output_dir(tmp_path) / "status")

    assert status.latest_stock_profile_run_id == created.stock_profile_run_id
    assert status.status == STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert status.health_status == "PASS"
    assert status.stock_profile_phase1_report_only_artifacts_created is True
    assert status.active_stock_profile_created is False
    assert status.real_buy_review_eligible is False
    assert status.buy_review_allowed is False
    assert status.approved_for_paper is False
    assert status.strategy_performance_validated is False
    assert status.current_candidates_run is False
    assert status.snapshot_built is False
    assert status.signal_semantics_changed is False
    assert status.promoted_model_created is False
    assert status.production_model_created is False
    assert status.active_thresholds_created is False
    assert status.advisory_predictions_created is False
    assert status.active_probabilities_created is False
    wording = status.safety_statement.lower()
    for phrase in [
        "report-only",
        "research-governed",
        "does not create active stock_profile",
        "does not create real buy-review eligibility",
        "does not apply paper approval",
        "does not validate strategy performance",
        "does not integrate current-candidates",
        "does not build snapshots",
        "does not mutate signal_semantics",
        "does not create promoted model",
        "does not create production model",
        "does not create active thresholds",
        "does not create advisory predictions",
        "does not create active probabilities",
        "does not authorize broker/order/message/api/trading",
    ]:
        assert phrase in wording
    assert status.artifact_paths["status_csv"].exists()
    assert status.artifact_paths["status_report"].exists()


def test_cli_stock_profile_view_commands_run_without_research_status_or_checkpoint(tmp_path: Path) -> None:
    run_stock_profile(StockProfileSettings(output_dir=_output_dir(tmp_path)))

    index = _run_cli(["stock-profile-index", "--root", _output_dir(tmp_path), "--output-dir", _output_dir(tmp_path) / "cli_index"])
    health = _run_cli(["stock-profile-health", "--root", _output_dir(tmp_path), "--output-dir", _output_dir(tmp_path) / "cli_health"])
    status = _run_cli(["stock-profile-status", "--root", _output_dir(tmp_path), "--output-dir", _output_dir(tmp_path) / "cli_status"])

    assert "stock_profile_index:" in index.stdout
    assert "artifact_count: 1" in index.stdout
    assert "stock_profile_health:" in health.stdout
    assert "status: PASS" in health.stdout
    assert "stock_profile_status:" in status.stdout
    assert "status: NO_STOCK_PROFILE_INPUT" in status.stdout
    assert not Path("docs/project_sources").exists()
    assert not Path("docs/release_checkpoint_v1.53.0.md").exists()


def _happy_settings(tmp_path: Path) -> StockProfileSettings:
    active_settings = _active_model_happy_settings(tmp_path / "active_model_source")
    active_result = run_active_model(replace(active_settings, allow_active_model=True))
    artifact_paths = active_result.artifact_paths
    root = tmp_path / "stock_profile_fixtures"
    root.mkdir(parents=True, exist_ok=True)
    _ensure_research_governed_training_rows(active_settings.training_result_rows_path)

    return StockProfileSettings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_STOCK_PROFILE_APPROVAL_TEXT}),
        stock_profile_request_manifest_path=_write_json(root / "request.json", _safe_stock_profile_request()),
        active_model_metadata_path=artifact_paths["active_model_metadata"],
        active_model_pointer_path=artifact_paths["active_model_pointer"],
        active_model_registry_entry_path=artifact_paths["active_model_registry_entry"],
        active_parameter_pointer_path=artifact_paths["active_parameter_pointer"],
        active_model_activation_status_path=artifact_paths["active_model_activation_status"],
        active_model_input_index_path=artifact_paths["active_model_input_index"],
        active_model_lineage_matrix_path=artifact_paths["active_model_lineage_matrix"],
        active_model_limitations_path=artifact_paths["active_model_limitations"],
        active_model_overfit_warnings_path=artifact_paths["active_model_overfit_warnings"],
        active_model_safety_flags_path=artifact_paths["active_model_safety_flags"],
        active_model_status_artifact_path=_write_json(root / "active_model_status.json", {"status": "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED"}),
        active_model_health_artifact_path=_write_json(root / "active_model_health.json", {"status": "PASS"}),
        model_weight_versioning_metadata_path=active_settings.model_weight_versioning_metadata_path,
        model_weights_reference_path=active_settings.model_weights_reference_path,
        model_version_metadata_path=active_settings.model_version_metadata_path,
        parameter_version_metadata_path=active_settings.parameter_version_metadata_path,
        model_input_index_path=active_settings.model_input_index_path,
        model_lineage_matrix_path=active_settings.model_lineage_matrix_path,
        model_limitations_path=active_settings.model_limitations_path,
        model_overfit_warnings_path=active_settings.model_overfit_warnings_path,
        model_safety_flags_path=active_settings.model_safety_flags_path,
        model_weight_versioning_status_artifact_path=active_settings.model_weight_versioning_status_artifact_path,
        model_weight_versioning_health_artifact_path=active_settings.model_weight_versioning_health_artifact_path,
        training_result_metadata_path=active_settings.training_result_metadata_path,
        training_result_rows_path=active_settings.training_result_rows_path,
        training_result_status_artifact_path=active_settings.training_result_status_artifact_path,
        training_result_health_artifact_path=active_settings.training_result_health_artifact_path,
        training_result_planning_metadata_path=active_settings.training_result_planning_metadata_path,
        training_result_planning_health_artifact_path=active_settings.training_result_planning_health_artifact_path,
        metric_extension_metadata_path=active_settings.metric_extension_metadata_path,
        metric_extension_result_rows_path=active_settings.metric_extension_result_rows_path,
        metric_extension_health_artifact_path=active_settings.metric_extension_health_artifact_path,
        metric_computation_metadata_path=active_settings.metric_computation_metadata_path,
        metric_computation_result_rows_path=active_settings.metric_computation_result_rows_path,
        metric_computation_health_artifact_path=active_settings.metric_computation_health_artifact_path,
        metric_evaluation_metadata_path=active_settings.metric_evaluation_metadata_path,
        metric_evaluation_health_artifact_path=active_settings.metric_evaluation_health_artifact_path,
        training_evaluation_metadata_path=active_settings.training_evaluation_metadata_path,
        training_evaluation_sample_rows_path=active_settings.training_evaluation_sample_rows_path,
        training_evaluation_health_artifact_path=active_settings.training_evaluation_health_artifact_path,
        forward_return_label_metadata_path=active_settings.forward_return_label_metadata_path,
        forward_return_label_rows_path=active_settings.forward_return_label_rows_path,
        forward_return_label_health_artifact_path=active_settings.forward_return_label_health_artifact_path,
        replay_decision_freeze_metadata_path=active_settings.replay_decision_freeze_metadata_path,
        replay_decision_freeze_rows_path=active_settings.replay_decision_freeze_rows_path,
        replay_decision_freeze_health_artifact_path=active_settings.replay_decision_freeze_health_artifact_path,
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", _safe_leakage_bundle()),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _safe_overclaim_bundle()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_side_effects()),
        output_dir=_output_dir(tmp_path),
    )


def _safe_stock_profile_request() -> dict[str, object]:
    return {
        "stock_profile_phase_1_only": True,
        "real_buy_review_requested": False,
        "buy_review_requested": False,
        "paper_approval_requested": False,
        "performance_validation_requested": False,
        "current_candidates_integration_requested": False,
        "snapshot_build_requested": False,
        "signal_semantics_mutation_requested": False,
        "promoted_model_requested": False,
        "production_model_requested": False,
        "active_thresholds_requested": False,
        "advisory_predictions_requested": False,
        "active_probabilities_requested": False,
        "trading_requested": False,
    }


def _ensure_research_governed_training_rows(path: Path) -> None:
    frame = pd.read_csv(path, dtype=str)
    frame["research_governed"] = "true"
    if "factor_layer" not in frame.columns:
        frame["factor_layer"] = "market_structure"
    if "instrument_type" not in frame.columns:
        frame["instrument_type"] = "STOCK"
    if "market_regime_id" not in frame.columns:
        frame["market_regime_id"] = "baseline"
    frame.to_csv(path, index=False)


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
        "stock_profile_research_governed_only": True,
        "stock_profile_not_active_stock_profile": True,
        "stock_profile_not_buy_review": True,
        "stock_profile_not_paper_approval": True,
        "stock_profile_not_performance_validation": True,
        "stock_profile_not_current_candidates": True,
        "stock_profile_not_snapshot": True,
        "stock_profile_not_signal_semantics": True,
        "stock_profile_not_promoted_model": True,
        "stock_profile_not_production_model": True,
        "stock_profile_not_active_thresholds": True,
        "stock_profile_not_advisory_predictions": True,
        "stock_profile_not_active_probabilities": True,
        "stock_profile_not_trading": True,
    }


def _safe_side_effects() -> dict[str, object]:
    return {
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS},
        "research_governed": True,
        "diagnostic_output": True,
    }


def _safe_artifact_keys() -> list[str]:
    return [
        "stock_profile_metadata",
        "stock_profile_safety_flags",
        "stock_profile_precondition_results",
        "stock_profile_approval_results",
        "stock_profile_upstream_lineage_results",
        "stock_profile_active_model_input_results",
        "stock_profile_model_weight_versioning_input_results",
        "stock_profile_training_result_input_results",
        "stock_profile_metric_evidence_results",
        "stock_profile_leakage_guard_results",
        "stock_profile_side_effect_guard_results",
        "stock_profile_overclaim_guard_results",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "stock_profile_input_index",
        "stock_profile_lineage_matrix",
        "stock_profile_factor_coverage_summary",
        "stock_profile_symbol_coverage",
        "stock_profile_market_regime_coverage",
        "stock_profile_metric_summary",
        "stock_profile_limitations",
        "stock_profile_overfit_warnings",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "stock_profile_v0_1"


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


def _cli_args(settings: StockProfileSettings) -> list[object]:
    args: list[object] = []
    for field in StockProfileSettings.__dataclass_fields__:
        if field in {"allow_stock_profile", "write_artifacts", "research_governed", "diagnostic_output"}:
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


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
