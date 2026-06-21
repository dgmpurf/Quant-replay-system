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
from test_stock_profile import _happy_settings as _stock_profile_happy_settings

from quant_replay_system.paper_workflow_phase1 import (
    EXACT_PAPER_WORKFLOW_PHASE1_APPROVAL_TEXT,
    NO_PAPER_WORKFLOW_PHASE1_INPUT,
    PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED,
    PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED,
    PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED,
    PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED,
    PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED,
    PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED,
    PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED,
    PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED,
    PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED,
    PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED,
    READY_FOR_PAPER_WORKFLOW_PHASE1,
    PaperWorkflowPhase1Settings,
    run_paper_workflow_phase1,
)
from quant_replay_system.stock_profile import run_stock_profile


DOWNSTREAM_FALSE_FIELDS = [
    "approved_for_paper",
    "approved_for_paper_created",
    "paper_approval_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
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
    result = run_paper_workflow_phase1(PaperWorkflowPhase1Settings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_PAPER_WORKFLOW_PHASE1_INPUT
    assert result.workflow_stage == "PAPER_WORKFLOW_PHASE1_NO_INPUT"
    assert result.ready_for_paper_workflow_phase1 is False
    assert result.paper_workflow_phase1_executed is False
    assert result.paper_workflow_phase1_report_only_artifacts_created is False
    assert result.paper_workflow_metadata_created is False
    assert result.paper_candidate_review_context_created is False
    assert result.paper_decision_draft_created is False
    assert result.paper_review_queue_created is False
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
        "approve paper",
        "paper approve",
        "make it eligible",
        "show buy candidates",
        "use it in candidates",
        "validate performance",
        "make it trade",
    ],
)
def test_missing_or_vague_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_paper_workflow_phase1(settings)

    assert result.status == PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED
    assert result.paper_workflow_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"approved_for_paper_requested": True}, PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED),
        ({"paper_approval_requested": True}, PAPER_WORKFLOW_PHASE1_APPROVAL_BLOCKED),
        ({"real_buy_review_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"current_candidates_integration_requested": True}, PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ({"snapshot_build_requested": True}, PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ({"signal_semantics_mutation_requested": True}, PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ({"active_stock_profile_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"promoted_model_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"production_model_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"active_thresholds_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"advisory_predictions_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"active_probabilities_requested": True}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ({"broker_api_called": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"order_placed": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"message_sent": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"external_api_called": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"trading_requested": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_scope_and_side_effect_requests_block(
    tmp_path: Path, patch: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.paper_workflow_request_manifest_path, patch)

    result = run_paper_workflow_phase1(settings)

    assert result.status == expected_status
    assert result.paper_workflow_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("stock_profile_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("stock_profile_input_index_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_ARTIFACT_BLOCKED),
        ("stock_profile_lineage_matrix_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("stock_profile_limitations_path", PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED := "PAPER_WORKFLOW_PHASE1_LIMITATIONS_BLOCKED"),
        ("stock_profile_overfit_warnings_path", PAPER_WORKFLOW_PHASE1_OVERFIT_WARNING_BLOCKED),
        ("stock_profile_safety_flags_path", PAPER_WORKFLOW_PHASE1_SAFETY_FLAG_BLOCKED),
        ("stock_profile_status_artifact_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("stock_profile_health_artifact_path", PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED),
        ("active_model_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("model_weight_versioning_metadata_path", PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("training_result_metadata_path", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_rows_path", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED),
        ("metric_computation_result_rows_path", PAPER_WORKFLOW_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("forward_return_label_rows_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("replay_decision_freeze_rows_path", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("existing_paper_workflow_status_path", PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED),
        ("leakage_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_paper_workflow_phase1(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.paper_workflow_phase1_report_only_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("stock_profile_metadata_path", {"status": "NO_STOCK_PROFILE_INPUT"}, PAPER_WORKFLOW_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("stock_profile_health_artifact_path", {"status": "FAIL"}, PAPER_WORKFLOW_PHASE1_HEALTH_BLOCKED),
        ("existing_paper_workflow_status_path", {"approved_count": 1}, PAPER_WORKFLOW_PHASE1_PAPER_CONTEXT_BLOCKED),
        ("leakage_evidence_bundle_path", {"current_candidates_integration_requested": True}, PAPER_WORKFLOW_PHASE1_LEAKAGE_BLOCKED),
        ("side_effect_evidence_bundle_path", {"trading_allowed": True}, PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"paper_workflow_not_performance_validation": False}, PAPER_WORKFLOW_PHASE1_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_paper_workflow_phase1(settings)

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("training_result_rows_path", "training_result_row_id", PAPER_WORKFLOW_PHASE1_TRAINING_RESULT_ROWS_BLOCKED),
        ("training_result_rows_path", "replay_decision_id", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "forward_return_label_id", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "source_hash", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "revision_id", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "available_time", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "quality_status", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
        ("stock_profile_lineage_matrix_path", "lineage_item", PAPER_WORKFLOW_PHASE1_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_paper_workflow_phase1(settings)

    assert result.status == expected_status


def test_forbidden_artifact_and_output_path_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    forbidden = Path(settings.output_dir) / "active_stock_profile_pointer.json"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("{}", encoding="utf-8")

    result = run_paper_workflow_phase1(settings)

    assert result.status == PAPER_WORKFLOW_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED

    outside = run_paper_workflow_phase1(replace(_happy_settings(tmp_path / "outside"), output_dir=tmp_path / "not_manual"))
    assert outside.status == PAPER_WORKFLOW_PHASE1_SIDE_EFFECT_BLOCKED


def test_happy_path_without_allow_reaches_ready_without_substantive_artifacts(tmp_path: Path) -> None:
    result = run_paper_workflow_phase1(_happy_settings(tmp_path))

    assert result.status == READY_FOR_PAPER_WORKFLOW_PHASE1
    assert result.ready_for_paper_workflow_phase1 is True
    assert result.paper_workflow_phase1_executed is False
    assert result.paper_workflow_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_happy_path_with_allow_creates_report_only_artifacts(tmp_path: Path) -> None:
    result = run_paper_workflow_phase1(replace(_happy_settings(tmp_path), allow_paper_workflow_phase1=True))

    assert result.status == PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.workflow_stage == PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.ready_for_paper_workflow_phase1 is True
    assert result.paper_workflow_phase1_executed is True
    assert result.paper_workflow_phase1_report_only_artifacts_created is True
    assert result.source_stock_profile_run_id
    assert result.source_active_model_run_id
    assert result.source_model_workflow_run_id
    assert result.model_weight_reference_id
    assert result.model_version_id
    assert result.parameter_version_id
    for key in [*_safe_artifact_keys(), *_substantive_artifact_keys()]:
        assert result.artifact_paths[key].exists(), key
    _assert_downstream_false(result)

    context = pd.read_csv(result.artifact_paths["paper_candidate_review_context"], dtype=str)
    draft = pd.read_csv(result.artifact_paths["paper_decision_draft"], dtype=str)
    queue = pd.read_csv(result.artifact_paths["paper_review_queue"], dtype=str)
    assert "human_review_context" in context.columns
    assert not _frame_contains_any(context, ["BUY", "SELL", "ORDER", "TRADE", "APPROVED_FOR_PAPER"])
    assert set(draft["draft_review_label"]) <= {
        "PAPER_REVIEW_DRAFT",
        "WATCH_ONLY_REVIEW",
        "BLOCKED_REVIEW",
        "NEEDS_HUMAN_REVIEW",
    }
    assert not _frame_contains_any(draft, ["APPROVED_FOR_PAPER", "REAL_BUY_REVIEW_CANDIDATE", "BUY", "SELL", "ORDER", "TRADE"])
    assert "broker" not in " ".join(queue.columns).lower()
    assert "message" not in " ".join(queue.columns).lower()

    limitations = result.artifact_paths["paper_workflow_limitations"].read_text(encoding="utf-8").lower()
    for phrase in [
        "does not create `approved_for_paper`",
        "no real buy-review eligibility",
        "no strategy performance validation",
        "no current-candidates integration",
        "no snapshot integration",
        "no signal_semantics mutation",
        "no active stock_profile",
        "no promoted model",
        "no production model",
        "no active thresholds",
        "no advisory predictions",
        "no active probabilities",
        "no broker/order/message/api/trading",
    ]:
        assert phrase in limitations

    warnings = set(pd.read_csv(result.artifact_paths["paper_workflow_overfit_warnings"], dtype=str)["warning_item"])
    for warning in ["small sample", "class imbalance", "single-stock overfit", "paper-decision overfit", "lookahead leakage"]:
        assert warning in warnings

    safety = _read_json(result.artifact_paths["paper_workflow_safety_flags"])
    assert safety["paper_workflow_phase1_report_only_artifacts_created"] is True
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False, field


def test_cli_runs_no_input_and_happy_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["paper-workflow-phase1", "--output-dir", _output_dir(tmp_path / "cli_no_input")])
    assert no_input.returncode == 0
    assert "status: NO_PAPER_WORKFLOW_PHASE1_INPUT" in no_input.stdout
    assert "approved_for_paper: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "cli_ready")
    ready = _run_cli(["paper-workflow-phase1", *_cli_args(settings)])
    assert ready.returncode == 0
    assert "status: READY_FOR_PAPER_WORKFLOW_PHASE1" in ready.stdout
    assert "paper_workflow_phase1_report_only_artifacts_created: False" in ready.stdout

    allowed_settings = _happy_settings(tmp_path / "cli_allowed")
    allowed = _run_cli(["paper-workflow-phase1", *_cli_args(allowed_settings), "--allow-paper-workflow-phase1"])
    assert allowed.returncode == 0
    assert "status: PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED" in allowed.stdout
    assert "approved_for_paper: False" in allowed.stdout


def test_no_forbidden_commands_docs_or_research_status_integration() -> None:
    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")
    assert "paper-workflow-phase1-index" not in cli_text
    assert "paper-workflow-phase1-health" not in cli_text
    assert "paper-workflow-phase1-status" not in cli_text
    assert "paper_workflow_phase1" not in Path("src/quant_replay_system/local_research_dashboard.py").read_text(encoding="utf-8")
    assert not Path("docs/project_sources").exists()
    assert not Path("docs/paper_workflow_phase1.md").exists()


def _happy_settings(tmp_path: Path) -> PaperWorkflowPhase1Settings:
    stock_settings = _stock_profile_happy_settings(tmp_path / "stock_profile_source")
    stock_result = run_stock_profile(replace(stock_settings, allow_stock_profile=True))
    root = tmp_path / "paper_workflow_fixtures"
    root.mkdir(parents=True, exist_ok=True)

    return PaperWorkflowPhase1Settings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_PAPER_WORKFLOW_PHASE1_APPROVAL_TEXT}),
        paper_workflow_request_manifest_path=_write_json(root / "request.json", _safe_request()),
        stock_profile_metadata_path=stock_result.artifact_paths["stock_profile_metadata"],
        stock_profile_input_index_path=stock_result.artifact_paths["stock_profile_input_index"],
        stock_profile_lineage_matrix_path=stock_result.artifact_paths["stock_profile_lineage_matrix"],
        stock_profile_factor_coverage_summary_path=stock_result.artifact_paths["stock_profile_factor_coverage_summary"],
        stock_profile_symbol_coverage_path=stock_result.artifact_paths["stock_profile_symbol_coverage"],
        stock_profile_market_regime_coverage_path=stock_result.artifact_paths["stock_profile_market_regime_coverage"],
        stock_profile_metric_summary_path=stock_result.artifact_paths["stock_profile_metric_summary"],
        stock_profile_limitations_path=stock_result.artifact_paths["stock_profile_limitations"],
        stock_profile_overfit_warnings_path=stock_result.artifact_paths["stock_profile_overfit_warnings"],
        stock_profile_safety_flags_path=stock_result.artifact_paths["stock_profile_safety_flags"],
        stock_profile_status_artifact_path=_write_json(root / "stock_profile_status.json", {"status": "STOCK_PROFILE_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED"}),
        stock_profile_health_artifact_path=_write_json(root / "stock_profile_health.json", {"status": "PASS"}),
        active_model_metadata_path=stock_settings.active_model_metadata_path,
        active_model_pointer_path=stock_settings.active_model_pointer_path,
        active_model_lineage_matrix_path=stock_settings.active_model_lineage_matrix_path,
        active_model_limitations_path=stock_settings.active_model_limitations_path,
        active_model_overfit_warnings_path=stock_settings.active_model_overfit_warnings_path,
        active_model_safety_flags_path=stock_settings.active_model_safety_flags_path,
        active_model_status_artifact_path=stock_settings.active_model_status_artifact_path,
        active_model_health_artifact_path=stock_settings.active_model_health_artifact_path,
        model_weight_versioning_metadata_path=stock_settings.model_weight_versioning_metadata_path,
        model_weights_reference_path=stock_settings.model_weights_reference_path,
        model_version_metadata_path=stock_settings.model_version_metadata_path,
        parameter_version_metadata_path=stock_settings.parameter_version_metadata_path,
        model_weight_versioning_status_artifact_path=stock_settings.model_weight_versioning_status_artifact_path,
        model_weight_versioning_health_artifact_path=stock_settings.model_weight_versioning_health_artifact_path,
        training_result_metadata_path=stock_settings.training_result_metadata_path,
        training_result_rows_path=stock_settings.training_result_rows_path,
        training_result_status_artifact_path=stock_settings.training_result_status_artifact_path,
        training_result_health_artifact_path=stock_settings.training_result_health_artifact_path,
        training_result_planning_metadata_path=stock_settings.training_result_planning_metadata_path,
        training_result_planning_health_artifact_path=stock_settings.training_result_planning_health_artifact_path,
        metric_extension_metadata_path=stock_settings.metric_extension_metadata_path,
        metric_extension_result_rows_path=stock_settings.metric_extension_result_rows_path,
        metric_extension_health_artifact_path=stock_settings.metric_extension_health_artifact_path,
        metric_computation_metadata_path=stock_settings.metric_computation_metadata_path,
        metric_computation_result_rows_path=stock_settings.metric_computation_result_rows_path,
        metric_computation_health_artifact_path=stock_settings.metric_computation_health_artifact_path,
        metric_evaluation_metadata_path=stock_settings.metric_evaluation_metadata_path,
        metric_evaluation_health_artifact_path=stock_settings.metric_evaluation_health_artifact_path,
        training_evaluation_metadata_path=stock_settings.training_evaluation_metadata_path,
        training_evaluation_sample_rows_path=stock_settings.training_evaluation_sample_rows_path,
        training_evaluation_health_artifact_path=stock_settings.training_evaluation_health_artifact_path,
        forward_return_label_metadata_path=stock_settings.forward_return_label_metadata_path,
        forward_return_label_rows_path=stock_settings.forward_return_label_rows_path,
        forward_return_label_health_artifact_path=stock_settings.forward_return_label_health_artifact_path,
        replay_decision_freeze_metadata_path=stock_settings.replay_decision_freeze_metadata_path,
        replay_decision_freeze_rows_path=stock_settings.replay_decision_freeze_rows_path,
        replay_decision_freeze_health_artifact_path=stock_settings.replay_decision_freeze_health_artifact_path,
        existing_paper_workflow_status_path=_write_json(root / "paper_status.json", _safe_existing_paper_context()),
        existing_paper_context_manifest_path=_write_json(root / "paper_context.json", _safe_existing_paper_context()),
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", _safe_leakage_bundle()),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _safe_overclaim_bundle()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_side_effects()),
        output_dir=_output_dir(tmp_path),
    )


def _safe_request() -> dict[str, object]:
    return {
        "paper_workflow_phase_1_only": True,
        "approved_for_paper_requested": False,
        "paper_approval_requested": False,
        "real_buy_review_requested": False,
        "performance_validation_requested": False,
        "current_candidates_integration_requested": False,
        "snapshot_build_requested": False,
        "signal_semantics_mutation_requested": False,
        "active_stock_profile_requested": False,
        "promoted_model_requested": False,
        "production_model_requested": False,
        "active_thresholds_requested": False,
        "advisory_predictions_requested": False,
        "active_probabilities_requested": False,
        "trading_requested": False,
    }


def _safe_existing_paper_context() -> dict[str, object]:
    return {
        "workflow_stage": "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
        "status": "WARN",
        "approved_count": 0,
        "watch_only_count": 9,
        "open_position_count": 0,
        "closed_trade_count": 0,
        "broker_api_invoked": False,
        "live_trading_enabled": False,
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
        "paper_workflow_phase1_report_only": True,
        "paper_workflow_not_approved_for_paper": True,
        "paper_workflow_not_real_buy_review": True,
        "paper_workflow_not_performance_validation": True,
        "paper_workflow_not_current_candidates": True,
        "paper_workflow_not_snapshot": True,
        "paper_workflow_not_signal_semantics": True,
        "paper_workflow_not_active_stock_profile": True,
        "paper_workflow_not_promoted_model": True,
        "paper_workflow_not_production_model": True,
        "paper_workflow_not_active_thresholds": True,
        "paper_workflow_not_advisory_predictions": True,
        "paper_workflow_not_active_probabilities": True,
        "paper_workflow_not_trading": True,
    }


def _safe_side_effects() -> dict[str, object]:
    return {**{field: False for field in DOWNSTREAM_FALSE_FIELDS}, "report_only": True, "diagnostic_output": True}


def _safe_artifact_keys() -> list[str]:
    return [
        "paper_workflow_metadata",
        "paper_workflow_safety_flags",
        "paper_workflow_precondition_results",
        "paper_workflow_approval_results",
        "paper_workflow_upstream_lineage_results",
        "paper_workflow_stock_profile_input_results",
        "paper_workflow_existing_paper_context_results",
        "paper_workflow_leakage_guard_results",
        "paper_workflow_side_effect_guard_results",
        "paper_workflow_overclaim_guard_results",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "paper_workflow_input_index",
        "paper_workflow_lineage_matrix",
        "paper_candidate_review_context",
        "paper_decision_draft",
        "paper_review_queue",
        "paper_workflow_limitations",
        "paper_workflow_overfit_warnings",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "paper_workflow_phase1_v0_1"


def _assert_downstream_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _frame_contains_any(frame: pd.DataFrame, needles: list[str]) -> bool:
    text = " ".join(frame.fillna("").astype(str).to_numpy().ravel()).upper()
    return any(needle.upper() in text for needle in needles)


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


def _cli_args(settings: PaperWorkflowPhase1Settings) -> list[object]:
    args: list[object] = []
    for field in PaperWorkflowPhase1Settings.__dataclass_fields__:
        if field in {"allow_paper_workflow_phase1", "write_artifacts", "research_governed", "diagnostic_output"}:
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
        check=False,
    )
