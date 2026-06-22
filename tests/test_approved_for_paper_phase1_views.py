from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).parent))
from test_approved_for_paper_phase1 import _happy_settings, _output_dir, _patch_json, _run_cli

from quant_replay_system.approved_for_paper_phase1 import (
    APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED,
    DOWNSTREAM_FALSE_FIELDS,
    NO_APPROVED_FOR_PAPER_PHASE1_INPUT,
    READY_FOR_APPROVED_FOR_PAPER_PHASE1,
    ApprovedForPaperPhase1Settings,
    run_approved_for_paper_phase1,
)
from quant_replay_system.approved_for_paper_phase1_health import check_approved_for_paper_phase1_health
from quant_replay_system.approved_for_paper_phase1_index import build_approved_for_paper_phase1_index
from quant_replay_system.approved_for_paper_phase1_status import run_approved_for_paper_phase1_status


def test_approved_for_paper_phase1_index_health_and_status_cover_no_input_ready_and_created(
    tmp_path: Path,
) -> None:
    root = _output_dir(tmp_path)
    no_input = run_approved_for_paper_phase1(ApprovedForPaperPhase1Settings(output_dir=root))
    ready = run_approved_for_paper_phase1(replace(_happy_settings(tmp_path / "ready"), output_dir=root))
    created = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path / "created"), output_dir=root, allow_approved_for_paper_phase1=True)
    )

    index = build_approved_for_paper_phase1_index(root=root, output_dir=root / "index")

    assert index.artifact_count == 3
    frame = index.index_frame.set_index("approved_for_paper_run_id")
    assert frame.loc[no_input.approved_for_paper_run_id, "status"] == NO_APPROVED_FOR_PAPER_PHASE1_INPUT
    assert frame.loc[ready.approved_for_paper_run_id, "status"] == READY_FOR_APPROVED_FOR_PAPER_PHASE1
    created_row = frame.loc[created.approved_for_paper_run_id]
    assert created_row["status"] == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert created_row["approved_for_paper_input_index_created"] is True
    assert created_row["approved_for_paper_lineage_matrix_created"] is True
    assert created_row["approved_for_paper_review_context_created"] is True
    assert created_row["approved_for_paper_decision_draft_created"] is True
    assert created_row["approved_for_paper_limitations_created"] is True
    assert created_row["approved_for_paper_overfit_warnings_created"] is True
    assert created_row["review_context_row_count"] == 1
    assert created_row["decision_draft_row_count"] == 1
    assert created_row["overfit_warning_row_count"] >= 5
    assert created_row["source_paper_workflow_phase1_run_id"]
    assert created_row["source_stock_profile_run_id"]
    assert created_row["source_active_model_run_id"]
    assert created_row["source_model_workflow_run_id"]
    assert created_row["source_training_result_run_id"]
    assert created_row["source_metric_computation_run_id"]
    assert created_row["source_forward_return_label_run_id"]
    assert created_row["source_replay_decision_freeze_run_id"]
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert created_row[field] is False, field

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")
    assert health.status == "PASS"
    assert health.checked_artifact_count == 3
    assert health.error_count == 0

    status = run_approved_for_paper_phase1_status(root=root, output_dir=root / "status")
    assert status.latest_approved_for_paper_run_id == created.approved_for_paper_run_id
    assert status.health_status == "PASS"
    assert status.status == APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED
    assert status.approved_for_paper_phase1_report_only_artifacts_created is True
    assert status.scoped_approved_for_paper is True
    assert status.real_buy_review_eligible is False
    assert status.strategy_performance_validated is False
    assert "report-only approved_for_paper phase 1" in status.safety_statement.lower()
    assert "does not create real buy-review eligibility" in status.safety_statement
    assert "does not validate strategy performance" in status.safety_statement
    assert "does not integrate current-candidates" in status.safety_statement
    assert "does not build snapshots" in status.safety_statement
    assert "does not mutate signal_semantics" in status.safety_statement
    assert "does not authorize broker/order/message/API/trading" in status.safety_statement


@pytest.mark.parametrize(
    ("artifact_key", "issue_code"),
    [
        ("approved_for_paper_metadata", "MISSING_APPROVED_FOR_PAPER_METADATA"),
        ("approved_for_paper_input_index", "MISSING_APPROVED_FOR_PAPER_INPUT_INDEX"),
        ("approved_for_paper_lineage_matrix", "MISSING_APPROVED_FOR_PAPER_LINEAGE_MATRIX"),
        ("approved_for_paper_review_context", "MISSING_APPROVED_FOR_PAPER_REVIEW_CONTEXT"),
        ("approved_for_paper_decision_draft", "MISSING_APPROVED_FOR_PAPER_DECISION_DRAFT"),
        ("approved_for_paper_limitations", "MISSING_APPROVED_FOR_PAPER_LIMITATIONS"),
        ("approved_for_paper_overfit_warnings", "MISSING_APPROVED_FOR_PAPER_OVERFIT_WARNINGS"),
        ("approved_for_paper_safety_flags", "MISSING_APPROVED_FOR_PAPER_SAFETY_FLAGS"),
    ],
)
def test_approved_for_paper_phase1_health_fails_if_created_artifact_missing(
    tmp_path: Path, artifact_key: str, issue_code: str
) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    result.artifact_paths[artifact_key].unlink()

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("status_name", [NO_APPROVED_FOR_PAPER_PHASE1_INPUT, READY_FOR_APPROVED_FOR_PAPER_PHASE1])
def test_approved_for_paper_phase1_health_fails_if_created_flag_true_before_created_state(
    tmp_path: Path, status_name: str
) -> None:
    root = _output_dir(tmp_path)
    if status_name == NO_APPROVED_FOR_PAPER_PHASE1_INPUT:
        result = run_approved_for_paper_phase1(ApprovedForPaperPhase1Settings(output_dir=root))
    else:
        result = run_approved_for_paper_phase1(replace(_happy_settings(tmp_path), output_dir=root))
    _patch_json(result.artifact_paths["approved_for_paper_metadata"], {"approved_for_paper_phase1_report_only_artifacts_created": True})
    _patch_json(result.artifact_paths["approved_for_paper_safety_flags"], {"approved_for_paper_phase1_report_only_artifacts_created": True})

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_REPORT_ONLY_ARTIFACTS_CREATED_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_approved_for_paper_phase1_health_fails_if_ready_or_no_input_has_substantive_artifact(
    tmp_path: Path,
) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(ApprovedForPaperPhase1Settings(output_dir=root))
    result.artifact_paths["approved_for_paper_decision_draft"].write_text(
        "draft_label\nAPPROVED_FOR_PAPER_PHASE1\n", encoding="utf-8"
    )

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_SUBSTANTIVE_ARTIFACT_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_approved_for_paper_phase1_health_fails_if_created_flag_false_for_created_status(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    _patch_json(result.artifact_paths["approved_for_paper_metadata"], {"approved_for_paper_phase1_report_only_artifacts_created": False})
    _patch_json(result.artifact_paths["approved_for_paper_safety_flags"], {"approved_for_paper_phase1_report_only_artifacts_created": False})

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_REPORT_ONLY_ARTIFACTS_CREATED_FLAG_FALSE" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    "field",
    [
        "source_paper_workflow_phase1_run_id",
        "source_stock_profile_run_id",
        "source_active_model_run_id",
        "source_model_workflow_run_id",
        "source_training_result_run_id",
        "source_metric_extension_run_id",
        "source_metric_computation_run_id",
        "source_metric_evaluation_planning_run_id",
        "source_training_evaluation_run_id",
        "source_forward_return_label_run_id",
        "source_replay_decision_freeze_run_id",
    ],
)
def test_approved_for_paper_phase1_health_fails_if_source_lineage_missing(tmp_path: Path, field: str) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    _patch_json(result.artifact_paths["approved_for_paper_metadata"], {field: ""})

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_SOURCE_LINEAGE_MISSING" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    ("artifact_key", "mutator", "issue_code"),
    [
        (
            "approved_for_paper_review_context",
            lambda path: pd.DataFrame([{"human_review_context": "BUY now"}]).to_csv(path, index=False),
            "APPROVED_FOR_PAPER_REVIEW_CONTEXT_FORBIDDEN_INSTRUCTION",
        ),
        (
            "approved_for_paper_decision_draft",
            lambda path: pd.DataFrame([{"draft_label": "REAL_BUY_REVIEW_CANDIDATE"}]).to_csv(path, index=False),
            "APPROVED_FOR_PAPER_DECISION_DRAFT_FORBIDDEN_LABEL",
        ),
    ],
)
def test_approved_for_paper_phase1_health_fails_for_review_artifact_leakage(
    tmp_path: Path, artifact_key: str, mutator, issue_code: str
) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    mutator(result.artifact_paths[artifact_key])

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert issue_code in set(health.health_frame["issue_code"])


@pytest.mark.parametrize(
    "phrase",
    [
        "no real buy-review eligibility",
        "no strategy performance validation",
        "no current-candidates",
        "no snapshot",
        "no signal_semantics mutation",
        "no active stock_profile",
        "no broker/order/message/api/trading",
        "no promoted model",
        "no production model",
        "no active thresholds",
        "no advisory predictions",
        "no active probabilities",
    ],
)
def test_approved_for_paper_phase1_health_fails_if_limitations_omit_required_wording(
    tmp_path: Path, phrase: str
) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    text = result.artifact_paths["approved_for_paper_limitations"].read_text(encoding="utf-8")
    result.artifact_paths["approved_for_paper_limitations"].write_text(text.replace(phrase, ""), encoding="utf-8")

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_LIMITATIONS_WORDING_MISSING" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("warning", ["small sample", "class imbalance", "single-stock overfit", "approved-for-paper overfit", "lookahead leakage"])
def test_approved_for_paper_phase1_health_fails_if_overfit_warning_missing(tmp_path: Path, warning: str) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    frame = pd.read_csv(result.artifact_paths["approved_for_paper_overfit_warnings"], dtype=str)
    frame.query("warning_item != @warning").to_csv(result.artifact_paths["approved_for_paper_overfit_warnings"], index=False)

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "APPROVED_FOR_PAPER_OVERFIT_WARNING_MISSING" in set(health.health_frame["issue_code"])


@pytest.mark.parametrize("field", DOWNSTREAM_FALSE_FIELDS)
def test_approved_for_paper_phase1_health_fails_if_safety_or_side_effect_flag_true(tmp_path: Path, field: str) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    _patch_json(result.artifact_paths["approved_for_paper_safety_flags"], {field: True})

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert f"{field.upper()}_UNEXPECTED" in set(health.health_frame["issue_code"])


def test_approved_for_paper_phase1_health_fails_for_forbidden_artifacts(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    result = run_approved_for_paper_phase1(
        replace(_happy_settings(tmp_path), output_dir=root, allow_approved_for_paper_phase1=True)
    )
    (Path(result.artifact_path) / "real_buy_review_candidate.csv").write_text("", encoding="utf-8")

    health = check_approved_for_paper_phase1_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "FORBIDDEN_APPROVED_FOR_PAPER_DOWNSTREAM_ARTIFACT_PRESENT" in set(health.health_frame["issue_code"])


def test_approved_for_paper_phase1_view_cli_commands_run(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_approved_for_paper_phase1(ApprovedForPaperPhase1Settings(output_dir=root))

    index = _run_cli(["approved-for-paper-phase1-index", "--root", root, "--output-dir", root / "cli_index"])
    health = _run_cli(["approved-for-paper-phase1-health", "--root", root, "--output-dir", root / "cli_health"])
    status = _run_cli(["approved-for-paper-phase1-status", "--root", root, "--output-dir", root / "cli_status"])

    assert index.returncode == 0
    assert "artifact_count: 1" in index.stdout
    assert health.returncode == 0
    assert "status: PASS" in health.stdout
    assert status.returncode == 0
    assert "workflow_stage: APPROVED_FOR_PAPER_PHASE1_NO_INPUT" in status.stdout
    assert "does not create real buy-review eligibility" in status.stdout


def test_views_have_research_status_docs_without_project_source() -> None:
    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")
    assert "approved-for-paper-phase1-index" in cli_text
    assert "approved-for-paper-phase1-health" in cli_text
    assert "approved-for-paper-phase1-status" in cli_text
    dashboard_text = Path("src/quant_replay_system/local_research_dashboard.py").read_text(encoding="utf-8")
    assert "approved_for_paper_phase1" in dashboard_text
    assert Path("docs/approved_for_paper_phase1.md").exists()
    assert not Path("docs/project_sources").exists()
