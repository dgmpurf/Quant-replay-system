from __future__ import annotations

import os
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent))
from test_global_approved_for_paper_approval_review import DOWNSTREAM_FALSE_FIELDS
from test_global_approved_for_paper_approval_review import _happy_settings
from test_global_approved_for_paper_approval_review import _output_dir
from test_global_approved_for_paper_approval_review import _read_json

from quant_replay_system.global_approved_for_paper_approval_review import (
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED,
    GlobalApprovedForPaperApprovalReviewSettings,
    run_global_approved_for_paper_approval_review,
)
from quant_replay_system.global_approved_for_paper_approval_review_health import (
    check_global_approved_for_paper_approval_review_health,
)
from quant_replay_system.global_approved_for_paper_approval_review_index import (
    build_global_approved_for_paper_approval_review_index,
)
from quant_replay_system.global_approved_for_paper_approval_review_status import (
    GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED,
    NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND,
    run_global_approved_for_paper_approval_review_status,
)


def test_index_safe_empty_when_no_artifacts_exist(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)

    result = build_global_approved_for_paper_approval_review_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()
    metadata = _read_json(result.artifact_paths["metadata"])
    assert metadata["artifact_count"] == 0
    assert metadata["diagnostic_only"] is True


def test_index_discovers_report_only_artifact_and_preserves_safety_flags(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core_result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )

    result = build_global_approved_for_paper_approval_review_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["global_approved_for_paper_approval_review_id"] == core_result.global_approved_for_paper_approval_review_id
    assert row["status"] == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    assert row["global_approved_for_paper_approval_review_report_only_artifacts_created"] is True
    assert row["global_approved_for_paper"] is False
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert row[field] is False, field


def test_health_passes_for_valid_report_only_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )

    result = check_global_approved_for_paper_approval_review_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.checked_artifact_count == 1
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_substantive_artifact_is_missing(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core_result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )
    core_result.artifact_paths["global_approved_for_paper_lineage_matrix"].unlink()

    result = check_global_approved_for_paper_approval_review_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "MISSING_GLOBAL_APPROVED_FOR_PAPER_LINEAGE_MATRIX" in set(result.health_frame["issue_code"])


def test_health_fails_when_forbidden_downstream_flag_is_true(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core_result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )
    metadata_path = core_result.artifact_paths["global_approved_for_paper_approval_review_metadata"]
    metadata = _read_json(metadata_path)
    metadata["trading_allowed"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    result = check_global_approved_for_paper_approval_review_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "TRADING_ALLOWED_UNEXPECTED" in set(result.health_frame["issue_code"])


def test_status_safe_empty_when_no_artifacts_exist(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)

    result = run_global_approved_for_paper_approval_review_status(root=root, output_dir=root / "status")

    assert result.workflow_stage == NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND
    assert result.health_status == "FAIL"
    assert result.global_approved_for_paper is False
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is False
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def test_status_summarizes_latest_valid_report_only_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core_result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )

    result = run_global_approved_for_paper_approval_review_status(root=root, output_dir=root / "status")

    assert result.latest_global_approved_for_paper_approval_review_id == core_result.global_approved_for_paper_approval_review_id
    assert result.status == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_REPORT_ONLY_APPROVED
    assert result.health_status == "PASS"
    assert result.global_approved_for_paper_approval_review_report_only_artifacts_created is True
    assert result.global_approved_for_paper is False
    assert "report-only" in result.safety_statement
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def test_status_reports_health_failed_for_unsafe_latest_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core_result = run_global_approved_for_paper_approval_review(
        replace(_happy_settings(tmp_path), allow_global_approved_for_paper_approval_review=True)
    )
    metadata_path = core_result.artifact_paths["global_approved_for_paper_approval_review_metadata"]
    metadata = _read_json(metadata_path)
    metadata["real_buy_review_eligible"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    result = run_global_approved_for_paper_approval_review_status(root=root, output_dir=root / "status")

    assert result.health_status == "FAIL"
    assert result.workflow_stage == GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_HEALTH_FAILED
    assert result.real_buy_review_eligible is True
    assert result.global_approved_for_paper is False


def test_cli_view_commands_default_safe_no_input(tmp_path: Path) -> None:
    root = _output_dir(tmp_path / "cli")

    index = _run_cli(["global-approved-for-paper-approval-review-index", "--root", root, "--output-dir", root / "index"])
    health = _run_cli(["global-approved-for-paper-approval-review-health", "--root", root, "--output-dir", root / "health"])
    status = _run_cli(["global-approved-for-paper-approval-review-status", "--root", root, "--output-dir", root / "status"])

    assert index.returncode == 0
    assert "artifact_count: 0" in index.stdout
    assert health.returncode == 0
    assert "status: FAIL" in health.stdout
    assert status.returncode == 0
    assert f"workflow_stage: {NO_GLOBAL_APPROVED_FOR_PAPER_APPROVAL_REVIEW_ARTIFACT_FOUND}" in status.stdout
    assert "global_approved_for_paper: False" in status.stdout
    assert "trading_allowed: False" in status.stdout


def test_only_expected_global_approval_review_view_commands_are_registered() -> None:
    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")

    for command in [
        "global-approved-for-paper-approval-review",
        "global-approved-for-paper-approval-review-index",
        "global-approved-for-paper-approval-review-health",
        "global-approved-for-paper-approval-review-status",
    ]:
        assert command in cli_text
    assert "global-approved-for-paper-approval-review-research-status" not in cli_text


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
