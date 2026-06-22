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
from test_paper_workflow_phase1 import _happy_settings as _paper_workflow_happy_settings

from quant_replay_system.approved_for_paper_phase1 import (
    APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED,
    APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED,
    EXACT_APPROVED_FOR_PAPER_PHASE1_APPROVAL_TEXT,
    NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
    READY_FOR_APPROVED_FOR_PAPER_PHASE1,
    ApprovedForPaperPhase1Settings,
    run_approved_for_paper_phase1,
)
from quant_replay_system.paper_workflow_phase1 import run_paper_workflow_phase1


DOWNSTREAM_FALSE_FIELDS = [
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
    result = run_approved_for_paper_phase1(ApprovedForPaperPhase1Settings(output_dir=_output_dir(tmp_path)))

    assert result.status == NO_APPROVED_FOR_PAPER_PHASE1_INPUT
    assert result.workflow_stage == "APPROVED_FOR_PAPER_PHASE1_NO_INPUT"
    assert result.ready_for_approved_for_paper_phase1 is False
    assert result.approved_for_paper_phase1_executed is False
    assert result.approved_for_paper_phase1_report_only_artifacts_created is False
    assert result.scoped_approved_for_paper is False
    assert result.scoped_approved_for_paper_phase1 is False
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
        "make it approved",
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

    result = run_approved_for_paper_phase1(settings)

    assert result.status == APPROVED_FOR_PAPER_PHASE1_APPROVAL_BLOCKED
    assert result.approved_for_paper_phase1_report_only_artifacts_created is False
    assert result.scoped_approved_for_paper is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("patch", "expected_status"),
    [
        ({"real_buy_review_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"performance_validation_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"current_candidates_integration_requested": True}, APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED),
        ({"snapshot_build_requested": True}, APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED),
        ({"signal_semantics_mutation_requested": True}, APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED),
        ({"active_stock_profile_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"promoted_model_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"production_model_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"active_thresholds_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"advisory_predictions_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"active_probabilities_requested": True}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ({"broker_api_called": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"order_placed": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"message_sent": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"external_api_called": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
        ({"trading_requested": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
    ],
)
def test_unsafe_scope_and_side_effect_requests_block(
    tmp_path: Path, patch: dict[str, object], expected_status: str
) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(settings.approved_for_paper_request_manifest_path, patch)

    result = run_approved_for_paper_phase1(settings)

    assert result.status == expected_status
    assert result.approved_for_paper_phase1_report_only_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    ("setting_name", "expected_status"),
    [
        ("paper_workflow_metadata_path", APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED),
        ("paper_workflow_input_index_path", APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED),
        ("paper_workflow_lineage_matrix_path", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("paper_workflow_limitations_path", APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_ARTIFACT_BLOCKED),
        ("paper_workflow_overfit_warnings_path", APPROVED_FOR_PAPER_PHASE1_OVERFIT_WARNING_BLOCKED),
        ("paper_workflow_safety_flags_path", APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED),
        ("paper_workflow_status_artifact_path", APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED),
        ("paper_workflow_health_artifact_path", APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED),
        ("stock_profile_metadata_path", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("active_model_metadata_path", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("model_weight_versioning_metadata_path", APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("training_result_metadata_path", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_rows_path", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        ("training_result_planning_metadata_path", APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_PLANNING_INPUT_BLOCKED),
        ("metric_extension_result_rows_path", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("metric_computation_result_rows_path", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("metric_evaluation_metadata_path", APPROVED_FOR_PAPER_PHASE1_METRIC_EVIDENCE_BLOCKED),
        ("training_evaluation_metadata_path", APPROVED_FOR_PAPER_PHASE1_TRAINING_EVALUATION_INPUT_BLOCKED),
        ("forward_return_label_rows_path", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("replay_decision_freeze_rows_path", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("leakage_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_LEAKAGE_BLOCKED),
        ("overclaim_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
        ("side_effect_evidence_bundle_path", APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
    ],
)
def test_missing_required_inputs_block_by_gate(tmp_path: Path, setting_name: str, expected_status: str) -> None:
    result = run_approved_for_paper_phase1(replace(_happy_settings(tmp_path), **{setting_name: None}))

    assert result.status == expected_status
    assert result.approved_for_paper_phase1_report_only_artifacts_created is False


@pytest.mark.parametrize(
    ("path_name", "patch", "expected_status"),
    [
        ("paper_workflow_metadata_path", {"status": "NO_PAPER_WORKFLOW_PHASE1_INPUT"}, APPROVED_FOR_PAPER_PHASE1_PAPER_WORKFLOW_INPUT_BLOCKED),
        ("paper_workflow_health_artifact_path", {"status": "FAIL"}, APPROVED_FOR_PAPER_PHASE1_HEALTH_BLOCKED),
        ("paper_workflow_safety_flags_path", {"paper_workflow_phase1_report_only_artifacts_created": False}, APPROVED_FOR_PAPER_PHASE1_SAFETY_FLAG_BLOCKED),
        ("stock_profile_metadata_path", {"status": "NO_STOCK_PROFILE_INPUT"}, APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("active_model_metadata_path", {"status": "NO_ACTIVE_MODEL_INPUT"}, APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("model_weight_versioning_metadata_path", {"status": "NO_MODEL_WEIGHT_VERSIONING_INPUT"}, APPROVED_FOR_PAPER_PHASE1_STOCK_PROFILE_INPUT_BLOCKED),
        ("training_result_metadata_path", {"status": "NO_TRAINING_RESULT_INPUT"}, APPROVED_FOR_PAPER_PHASE1_TRAINING_RESULT_INPUT_BLOCKED),
        ("side_effect_evidence_bundle_path", {"trading_allowed": True}, APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED),
        ("overclaim_evidence_bundle_path", {"approved_for_paper_not_performance_validation": False}, APPROVED_FOR_PAPER_PHASE1_OVERCLAIM_BLOCKED),
    ],
)
def test_gate_failures_block(tmp_path: Path, path_name: str, patch: dict[str, object], expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    _patch_json(getattr(settings, path_name), patch)

    result = run_approved_for_paper_phase1(settings)

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("path_name", "column", "expected_status"),
    [
        ("paper_workflow_lineage_matrix_path", "paper_workflow_run_id", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "training_result_row_id", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "source_hash", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "revision_id", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "available_time", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
        ("training_result_rows_path", "quality_status", APPROVED_FOR_PAPER_PHASE1_LINEAGE_BLOCKED),
    ],
)
def test_missing_required_columns_block(tmp_path: Path, path_name: str, column: str, expected_status: str) -> None:
    settings = _happy_settings(tmp_path)
    frame = pd.read_csv(getattr(settings, path_name), dtype=str)
    frame = frame.drop(columns=[column])
    frame.to_csv(getattr(settings, path_name), index=False)

    result = run_approved_for_paper_phase1(settings)

    assert result.status == expected_status


def test_forbidden_artifact_and_output_path_block(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    forbidden = Path(settings.output_dir) / "real_buy_review_candidate.csv"
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("{}", encoding="utf-8")

    result = run_approved_for_paper_phase1(settings)

    assert result.status == APPROVED_FOR_PAPER_PHASE1_FORBIDDEN_ARTIFACT_BLOCKED

    outside = run_approved_for_paper_phase1(replace(_happy_settings(tmp_path / "outside"), output_dir=tmp_path / "not_manual"))
    assert outside.status == APPROVED_FOR_PAPER_PHASE1_SIDE_EFFECT_BLOCKED


def test_happy_path_without_allow_reaches_ready_without_substantive_artifacts(tmp_path: Path) -> None:
    result = run_approved_for_paper_phase1(_happy_settings(tmp_path))

    assert result.status == READY_FOR_APPROVED_FOR_PAPER_PHASE1
    assert result.ready_for_approved_for_paper_phase1 is True
    assert result.approved_for_paper_phase1_executed is False
    assert result.approved_for_paper_phase1_report_only_artifacts_created is False
    assert result.scoped_approved_for_paper_phase1 is False
    assert result.scoped_approved_for_paper is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_happy_path_with_allow_creates_report_only_artifacts_and_preserves_lineage(tmp_path: Path) -> None:
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), allow_approved_for_paper_phase1=True)
    )

    assert result.status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.workflow_stage == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert result.ready_for_approved_for_paper_phase1 is True
    assert result.approved_for_paper_phase1_executed is True
    assert result.approved_for_paper_phase1_report_only_artifacts_created is True
    assert result.scoped_approved_for_paper_phase1 is True
    assert result.scoped_approved_for_paper is True
    _assert_downstream_false(result)
    for key in [*_safe_artifact_keys(), *_substantive_artifact_keys()]:
        assert result.artifact_paths[key].exists(), key

    metadata = _read_json(result.artifact_paths["approved_for_paper_metadata"])
    assert metadata["approved_for_paper_run_id"] == result.approved_for_paper_run_id
    assert metadata["approved_for_paper_scope"] == "report_only_phase1_artifact_state_only"
    assert metadata["source_paper_workflow_phase1_run_id"]
    assert metadata["source_stock_profile_run_id"]
    assert metadata["source_active_model_run_id"]
    assert metadata["source_model_workflow_run_id"]
    assert metadata["model_weight_reference_id"]
    assert metadata["model_version_id"]
    assert metadata["parameter_version_id"]
    assert metadata["source_training_result_run_id"]
    assert metadata["source_metric_computation_run_id"]
    assert metadata["source_metric_extension_run_id"]
    assert metadata["source_metric_evaluation_planning_run_id"]
    assert metadata["source_forward_return_label_run_id"]
    assert metadata["source_replay_decision_freeze_run_id"]

    lineage = pd.read_csv(result.artifact_paths["approved_for_paper_lineage_matrix"], dtype=str)
    assert lineage.loc[0, "paper_workflow_phase1_run_id"] == result.source_paper_workflow_phase1_run_id
    assert lineage.loc[0, "stock_profile_run_id"] == result.source_stock_profile_run_id
    assert lineage.loc[0, "active_model_run_id"] == result.source_active_model_run_id
    assert lineage.loc[0, "model_workflow_run_id"] == result.source_model_workflow_run_id
    assert lineage.loc[0, "training_result_run_id"] == result.source_training_result_run_id


def test_created_artifacts_are_human_review_only_and_report_limitations(tmp_path: Path) -> None:
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), allow_approved_for_paper_phase1=True)
    )

    review_context = pd.read_csv(result.artifact_paths["approved_for_paper_review_context"], dtype=str)
    assert "human" in " ".join(review_context.fillna("").astype(str).to_numpy().ravel()).lower()
    assert not _frame_contains_any(
        review_context,
        ["REAL_BUY_REVIEW_CANDIDATE", "BUY", "SELL", "ORDER", "TRADE", "LIVE_TRADING_READY"],
    )

    decision = pd.read_csv(result.artifact_paths["approved_for_paper_decision_draft"], dtype=str)
    assert set(decision["draft_label"]) <= {
        "APPROVED_FOR_PAPER_PHASE1",
        "PAPER_APPROVAL_REVIEW_DRAFT",
        "PAPER_BLOCKED_REVIEW",
        "NEEDS_HUMAN_REVIEW",
    }
    assert not _frame_contains_any(decision, ["REAL_BUY_REVIEW_CANDIDATE", "BUY", "SELL", "ORDER", "TRADE"])

    limitations = result.artifact_paths["approved_for_paper_limitations"].read_text(encoding="utf-8").lower()
    for phrase in [
        "phase 1 is report-only",
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
        "metrics are evidence only, not profitability proof",
        "fill/slippage assumptions remain future separate validation",
    ]:
        assert phrase in limitations


def test_overfit_warnings_and_safety_flags_cover_required_boundaries(tmp_path: Path) -> None:
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), allow_approved_for_paper_phase1=True)
    )

    warnings = pd.read_csv(result.artifact_paths["approved_for_paper_overfit_warnings"], dtype=str)
    warning_items = set(warnings["warning_item"])
    for expected in [
        "small sample",
        "class imbalance",
        "single-stock overfit",
        "approved-for-paper overfit",
        "lookahead leakage",
        "paper-overfit risk",
    ]:
        assert expected in warning_items

    safety = _read_json(result.artifact_paths["approved_for_paper_safety_flags"])
    assert safety["approved_for_paper_phase1_report_only_artifacts_created"] is True
    assert safety["scoped_approved_for_paper_phase1"] is True
    assert safety["scoped_approved_for_paper"] is True
    assert safety["approved_for_paper_scope"] == "report_only_phase1_artifact_state_only"
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert safety[field] is False, field

    output_names = " ".join(path.name.lower() for path in Path(result.artifact_path).rglob("*"))
    for forbidden in [
        "real_buy_review",
        "performance_validation",
        "current_candidates",
        "snapshot",
        "signal_semantics",
        "broker",
        "order",
        "message",
        "api",
        "trading",
    ]:
        assert forbidden not in output_names


def test_cli_no_input_and_happy_paths(tmp_path: Path) -> None:
    no_input = _run_cli(["approved-for-paper-phase1", "--output-dir", _output_dir(tmp_path / "cli_no_input")])
    assert no_input.returncode == 0
    assert "status: NO_APPROVED_FOR_PAPER_PHASE1_INPUT" in no_input.stdout
    assert "ready_for_approved_for_paper_phase1: False" in no_input.stdout
    assert "real_buy_review_eligible: False" in no_input.stdout

    settings = _happy_settings(tmp_path / "cli_ready")
    ready = _run_cli(["approved-for-paper-phase1", *_cli_args(settings)])
    assert ready.returncode == 0
    assert "status: READY_FOR_APPROVED_FOR_PAPER_PHASE1" in ready.stdout
    assert "approved_for_paper_phase1_report_only_artifacts_created: False" in ready.stdout

    allowed_settings = replace(settings, output_dir=_output_dir(tmp_path / "cli_allowed"))
    allowed = _run_cli(
        ["approved-for-paper-phase1", *_cli_args(allowed_settings), "--allow-approved-for-paper-phase1"]
    )
    assert allowed.returncode == 0
    assert "status: APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED" in allowed.stdout
    assert "scoped_approved_for_paper: True" in allowed.stdout
    assert "trading_allowed: False" in allowed.stdout


def test_approved_for_paper_phase1_research_status_docs_do_not_create_project_source() -> None:
    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")
    assert "approved-for-paper-phase1" in cli_text
    assert "approved_for_paper_phase1" in Path("src/quant_replay_system/local_research_dashboard.py").read_text(
        encoding="utf-8"
    )
    assert Path("docs/release_checkpoint_v1.55.0.md").exists()
    assert not Path("docs/project_sources").exists()


def _happy_settings(tmp_path: Path) -> ApprovedForPaperPhase1Settings:
    paper_settings = _paper_workflow_happy_settings(tmp_path / "paper_source")
    paper_result = run_paper_workflow_phase1(replace(paper_settings, allow_paper_workflow_phase1=True))
    root = tmp_path / "approved_for_paper_fixtures"
    root.mkdir(parents=True, exist_ok=True)

    return ApprovedForPaperPhase1Settings(
        approval_manifest_path=_write_json(root / "approval.json", {"approval_text": EXACT_APPROVED_FOR_PAPER_PHASE1_APPROVAL_TEXT}),
        approved_for_paper_request_manifest_path=_write_json(root / "request.json", _safe_request()),
        paper_workflow_metadata_path=paper_result.artifact_paths["paper_workflow_metadata"],
        paper_workflow_input_index_path=paper_result.artifact_paths["paper_workflow_input_index"],
        paper_workflow_lineage_matrix_path=paper_result.artifact_paths["paper_workflow_lineage_matrix"],
        paper_workflow_review_context_path=paper_result.artifact_paths["paper_candidate_review_context"],
        paper_workflow_decision_draft_path=paper_result.artifact_paths["paper_decision_draft"],
        paper_workflow_limitations_path=paper_result.artifact_paths["paper_workflow_limitations"],
        paper_workflow_overfit_warnings_path=paper_result.artifact_paths["paper_workflow_overfit_warnings"],
        paper_workflow_safety_flags_path=paper_result.artifact_paths["paper_workflow_safety_flags"],
        paper_workflow_status_artifact_path=_write_json(
            root / "paper_status.json",
            {"status": "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED", "health_status": "PASS"},
        ),
        paper_workflow_health_artifact_path=_write_json(root / "paper_health.json", {"status": "PASS"}),
        stock_profile_metadata_path=paper_settings.stock_profile_metadata_path,
        stock_profile_status_artifact_path=paper_settings.stock_profile_status_artifact_path,
        stock_profile_health_artifact_path=paper_settings.stock_profile_health_artifact_path,
        active_model_metadata_path=paper_settings.active_model_metadata_path,
        active_model_status_artifact_path=paper_settings.active_model_status_artifact_path,
        active_model_health_artifact_path=paper_settings.active_model_health_artifact_path,
        model_weight_versioning_metadata_path=paper_settings.model_weight_versioning_metadata_path,
        model_weights_reference_path=paper_settings.model_weights_reference_path,
        model_version_metadata_path=paper_settings.model_version_metadata_path,
        parameter_version_metadata_path=paper_settings.parameter_version_metadata_path,
        model_weight_versioning_status_artifact_path=paper_settings.model_weight_versioning_status_artifact_path,
        model_weight_versioning_health_artifact_path=paper_settings.model_weight_versioning_health_artifact_path,
        training_result_metadata_path=paper_settings.training_result_metadata_path,
        training_result_rows_path=paper_settings.training_result_rows_path,
        training_result_status_artifact_path=paper_settings.training_result_status_artifact_path,
        training_result_health_artifact_path=paper_settings.training_result_health_artifact_path,
        training_result_planning_metadata_path=paper_settings.training_result_planning_metadata_path,
        training_result_planning_health_artifact_path=paper_settings.training_result_planning_health_artifact_path,
        metric_extension_metadata_path=paper_settings.metric_extension_metadata_path,
        metric_extension_result_rows_path=paper_settings.metric_extension_result_rows_path,
        metric_extension_health_artifact_path=paper_settings.metric_extension_health_artifact_path,
        metric_computation_metadata_path=paper_settings.metric_computation_metadata_path,
        metric_computation_result_rows_path=paper_settings.metric_computation_result_rows_path,
        metric_computation_health_artifact_path=paper_settings.metric_computation_health_artifact_path,
        metric_evaluation_metadata_path=paper_settings.metric_evaluation_metadata_path,
        metric_evaluation_health_artifact_path=paper_settings.metric_evaluation_health_artifact_path,
        training_evaluation_metadata_path=paper_settings.training_evaluation_metadata_path,
        training_evaluation_sample_rows_path=paper_settings.training_evaluation_sample_rows_path,
        training_evaluation_health_artifact_path=paper_settings.training_evaluation_health_artifact_path,
        forward_return_label_metadata_path=paper_settings.forward_return_label_metadata_path,
        forward_return_label_rows_path=paper_settings.forward_return_label_rows_path,
        forward_return_label_health_artifact_path=paper_settings.forward_return_label_health_artifact_path,
        replay_decision_freeze_metadata_path=paper_settings.replay_decision_freeze_metadata_path,
        replay_decision_freeze_rows_path=paper_settings.replay_decision_freeze_rows_path,
        replay_decision_freeze_health_artifact_path=paper_settings.replay_decision_freeze_health_artifact_path,
        leakage_evidence_bundle_path=_write_json(root / "leakage.json", _safe_leakage_bundle()),
        overclaim_evidence_bundle_path=_write_json(root / "overclaim.json", _safe_overclaim_bundle()),
        side_effect_evidence_bundle_path=_write_json(root / "side_effect.json", _safe_side_effects()),
        output_dir=_output_dir(tmp_path),
    )


def _safe_request() -> dict[str, object]:
    return {
        "approved_for_paper_phase1_only": True,
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
        "approved_for_paper_phase1_report_only": True,
        "approved_for_paper_not_real_buy_review": True,
        "approved_for_paper_not_performance_validation": True,
        "approved_for_paper_not_current_candidates": True,
        "approved_for_paper_not_snapshot": True,
        "approved_for_paper_not_signal_semantics": True,
        "approved_for_paper_not_active_stock_profile": True,
        "approved_for_paper_not_promoted_model": True,
        "approved_for_paper_not_production_model": True,
        "approved_for_paper_not_active_thresholds": True,
        "approved_for_paper_not_advisory_predictions": True,
        "approved_for_paper_not_active_probabilities": True,
        "approved_for_paper_not_trading": True,
    }


def _safe_side_effects() -> dict[str, object]:
    return {**{field: False for field in DOWNSTREAM_FALSE_FIELDS}, "report_only": True, "diagnostic_output": True}


def _safe_artifact_keys() -> list[str]:
    return [
        "approved_for_paper_metadata",
        "approved_for_paper_safety_flags",
        "approved_for_paper_precondition_results",
        "approved_for_paper_approval_results",
        "approved_for_paper_upstream_lineage_results",
        "approved_for_paper_paper_workflow_input_results",
        "approved_for_paper_leakage_guard_results",
        "approved_for_paper_side_effect_guard_results",
        "approved_for_paper_overclaim_guard_results",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "approved_for_paper_input_index",
        "approved_for_paper_lineage_matrix",
        "approved_for_paper_review_context",
        "approved_for_paper_decision_draft",
        "approved_for_paper_limitations",
        "approved_for_paper_overfit_warnings",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "approved_for_paper_phase1_v0_1"


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


def _cli_args(settings: ApprovedForPaperPhase1Settings) -> list[object]:
    args: list[object] = []
    for field in ApprovedForPaperPhase1Settings.__dataclass_fields__:
        if field in {"allow_approved_for_paper_phase1", "write_artifacts", "research_governed", "diagnostic_output"}:
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
