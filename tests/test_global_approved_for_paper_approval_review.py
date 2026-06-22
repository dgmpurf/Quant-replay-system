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
from test_approved_for_paper_phase1 import _happy_settings as _approved_for_paper_phase1_happy_settings

from quant_replay_system.approved_for_paper_phase1 import run_approved_for_paper_phase1
from quant_replay_system.global_approved_for_paper_approval_review import (
    EXACT_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_TEXT,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED,
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED,
    GlobalApprovedForPaperApprovalReviewSettings,
    NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT,
    READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW,
    run_global_approved_for_paper_approval_review,
)


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
    "broker_api_called",
    "order_placed",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]


def test_no_input_path_is_safe_and_creates_no_substantive_artifacts(tmp_path: Path) -> None:
    result = run_global_approved_for_paper_approval_review(
        GlobalApprovedForPaperApprovalReviewSettings(output_dir=_output_dir(tmp_path))
    )

    assert result.status == NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT
    assert result.workflow_stage == "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_NO_INPUT"
    assert result.ready_for_global_approved_for_paper_approval_review is False
    assert result.global_approved_for_paper_approval_review_executed is False
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False
    assert result.scoped_global_approved_for_paper_approval_review is False
    assert result.global_approved_for_paper is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


@pytest.mark.parametrize("approval_text", ["", "approve", "global approved", "allow trading", "create buy review"])
def test_missing_wrong_or_ambiguous_approval_blocks(tmp_path: Path, approval_text: str) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approval_manifest_path, {"approval_text": approval_text})

    result = run_global_approved_for_paper_approval_review(settings)

    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_APPROVAL_BLOCKED
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False
    assert result.global_approved_for_paper is False
    _assert_downstream_false(result)


def test_ready_without_allow_creates_no_substantive_artifacts(tmp_path: Path) -> None:
    result = run_global_approved_for_paper_approval_review(_happy_settings(tmp_path))

    assert result.status == READY_FOR_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW
    assert result.ready_for_global_approved_for_paper_approval_review is True
    assert result.global_approved_for_paper_approval_review_executed is False
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False
    assert result.scoped_global_approved_for_paper_approval_review is False
    assert result.global_approved_for_paper is False
    _assert_downstream_false(result)
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_explicit_allow_creates_only_report_only_artifacts(tmp_path: Path) -> None:
    result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )

    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    assert result.workflow_stage == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    assert result.ready_for_global_approved_for_paper_approval_review is True
    assert result.global_approved_for_paper_approval_review_executed is True
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is True
    assert result.scoped_global_approved_for_paper_approval_review is True
    assert result.global_approved_for_paper is False
    _assert_downstream_false(result)
    for key in [*_safe_artifact_keys(), *_substantive_artifact_keys()]:
        assert result.artifact_paths[key].exists(), key

    metadata = _read_json(result.artifact_paths["global_approved_for_paper_approval_review_metadata"])
    assert metadata["global_approved_for_paper_approval_review_id"] == result.global_approved_for_paper_approval_review_id
    assert metadata["global_approved_for_paper"] is False
    assert metadata["global_approved_for_paper_scope"] == "report_only_global_approval_review_only"
    assert metadata["source_approved_for_paper_phase1_run_id"] == result.source_approved_for_paper_phase1_run_id

    lineage = pd.read_csv(result.artifact_paths["global_approved_for_paper_lineage_matrix"], dtype=str)
    assert lineage.loc[0, "source_approved_for_paper_phase1_run_id"] == result.source_approved_for_paper_phase1_run_id
    assert lineage.loc[0, "source_paper_workflow_phase1_run_id"]
    assert lineage.loc[0, "source_model_workflow_run_id"]
    assert lineage.loc[0, "report_only"] == "True"

    limitations = result.artifact_paths["global_approved_for_paper_limitations"].read_text(encoding="utf-8").lower()
    for phrase in [
        "report-only approval-review",
        "not global approved_for_paper as operational state",
        "no real buy-review eligibility",
        "no buy_review_allowed",
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

    output_names = " ".join(path.name.lower() for path in Path(result.artifact_path).rglob("*"))
    for forbidden in ["current_candidates", "snapshot", "signal_semantics", "broker", "order_placed", "trading"]:
        assert forbidden not in output_names


def test_missing_upstream_lineage_blocks(tmp_path: Path) -> None:
    result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), approved_for_paper_phase1_metadata_path=None)
    )

    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_LINEAGE_BLOCKED
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False


def test_non_pass_upstream_health_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    _write_json(settings.approved_for_paper_phase1_health_artifact_path, {"status": "FAIL"})

    result = run_global_approved_for_paper_approval_review(settings)

    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_HEALTH_BLOCKED
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False


@pytest.mark.parametrize("field", DOWNSTREAM_FALSE_FIELDS)
def test_forbidden_downstream_flags_true_in_input_block(tmp_path: Path, field: str) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _read_json(settings.approval_manifest_path)
    manifest[field] = True
    _write_json(settings.approval_manifest_path, manifest)

    result = run_global_approved_for_paper_approval_review(settings)

    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_SIDE_EFFECT_BLOCKED
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False
    _assert_downstream_false(result)


def test_cli_no_input_and_only_core_command_registered(tmp_path: Path) -> None:
    completed = _run_cli(
        ["global-approved-for-paper-approval-review", "--output-dir", _output_dir(tmp_path / "cli")]
    )

    assert completed.returncode == 0
    assert "status: NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_INPUT" in completed.stdout
    assert "global_approved_for_paper_approval_review_report_only_artifacts_created: False" in completed.stdout
    assert "global_approved_for_paper: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout

    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")
    assert "global-approved-for-paper-approval-review" in cli_text
    assert "global-approved-for-paper-approval-review-index" not in cli_text
    assert "global-approved-for-paper-approval-review-health" not in cli_text
    assert "global-approved-for-paper-approval-review-status" not in cli_text


def _happy_settings(tmp_path: Path) -> GlobalApprovedForPaperApprovalReviewSettings:
    phase1_result = run_approved_for_paper_phase1(
        replace(_approved_for_paper_phase1_happy_settings(tmp_path / "phase1"), allow_approved_for_paper_phase1=True)
    )
    root = tmp_path / "global_approval_review_fixtures"
    root.mkdir(parents=True, exist_ok=True)
    return GlobalApprovedForPaperApprovalReviewSettings(
        approval_manifest_path=_write_json(
            root / "approval.json",
            {
                "approval_text": EXACT_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_TEXT,
                "approved_by": "local_reviewer",
                "approved_at": "2026-06-22T00:00:00Z",
                "approval_scope": "GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY",
            },
        ),
        approved_for_paper_phase1_metadata_path=phase1_result.artifact_paths["approved_for_paper_metadata"],
        approved_for_paper_phase1_status_artifact_path=_write_json(
            root / "approved_for_paper_phase1_status.json",
            {"status": "APPROVED_FOR_PAPER_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED", "health_status": "PASS"},
        ),
        approved_for_paper_phase1_health_artifact_path=_write_json(root / "approved_for_paper_phase1_health.json", {"status": "PASS"}),
        approved_for_paper_phase1_lineage_matrix_path=phase1_result.artifact_paths["approved_for_paper_lineage_matrix"],
        approved_for_paper_phase1_limitations_path=phase1_result.artifact_paths["approved_for_paper_limitations"],
        approved_for_paper_phase1_safety_flags_path=phase1_result.artifact_paths["approved_for_paper_safety_flags"],
        output_dir=_output_dir(tmp_path),
    )


def _safe_artifact_keys() -> list[str]:
    return [
        "global_approved_for_paper_approval_review_metadata",
        "global_approved_for_paper_precondition_results",
        "global_approved_for_paper_forbidden_output_guard",
        "global_approved_for_paper_overclaim_guard",
        "global_approved_for_paper_side_effect_guard",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "global_approved_for_paper_approval_manifest_review",
        "global_approved_for_paper_lineage_matrix",
        "global_approved_for_paper_research_status_preview",
        "global_approved_for_paper_limitations",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "global_approved_for_paper_approval_review_v0_1"


def _assert_downstream_false(result: object) -> None:
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
