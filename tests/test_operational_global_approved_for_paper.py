from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.operational_global_approved_for_paper import (
    BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER,
    INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW,
    OperationalGlobalApprovedForPaperSettings,
    run_operational_global_approved_for_paper,
)


DOWNSTREAM_FALSE_FIELDS = [
    "operational_global_approved_for_paper_granted",
    "global_approved_for_paper",
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
    result = run_operational_global_approved_for_paper(
        OperationalGlobalApprovedForPaperSettings(output_dir=_output_dir(tmp_path))
    )

    assert result.status == NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT
    assert result.workflow_stage == "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_NO_INPUT"
    assert result.ready_for_operational_global_approved_for_paper_review is False
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_valid_manifest_without_allow_is_ready_and_creates_no_substantive_artifacts(tmp_path: Path) -> None:
    result = run_operational_global_approved_for_paper(_happy_settings(tmp_path))

    assert result.status == READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW
    assert result.ready_for_operational_global_approved_for_paper_review is True
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)
    for key in _safe_artifact_keys():
        assert result.artifact_paths[key].exists(), key
    for key in _substantive_artifact_keys():
        assert not result.artifact_paths[key].exists(), key


def test_explicit_report_only_allow_creates_only_planning_artifacts(tmp_path: Path) -> None:
    result = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
    assert result.workflow_stage == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
    assert result.ready_for_operational_global_approved_for_paper_review is True
    assert result.operational_global_approved_for_paper_planning_artifacts_created is True
    _assert_downstream_false(result)
    for key in [*_safe_artifact_keys(), *_substantive_artifact_keys()]:
        assert result.artifact_paths[key].exists(), key

    metadata = _read_json(result.artifact_paths["operational_global_approved_for_paper_metadata"])
    assert isinstance(metadata["operational_global_approved_for_paper_id"], str)
    assert metadata["approval_manifest_exact_user_approval_id"] == "000123456789"
    assert metadata["operational_global_approved_for_paper_granted"] is False
    assert metadata["global_approved_for_paper"] is False
    assert metadata["buy_review_allowed"] is False

    lineage = pd.read_csv(result.artifact_paths["operational_global_approved_for_paper_lineage_matrix"], dtype=str)
    assert lineage.loc[0, "operational_global_approved_for_paper_id"] == result.operational_global_approved_for_paper_id
    assert lineage.loc[0, "upstream_artifact_id"] == "paper_phase1_001"
    assert lineage.loc[0, "upstream_health_status"] == "PASS"

    limitations = result.artifact_paths["operational_global_approved_for_paper_limitations"].read_text(
        encoding="utf-8"
    ).lower()
    for phrase in [
        "report-only planning",
        "does not grant operational global approved_for_paper",
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


def test_missing_required_manifest_field_invalidates(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _valid_manifest(tmp_path)
    manifest.pop("exact_user_approval_id")
    _write_json(settings.manifest_path, manifest)

    result = run_operational_global_approved_for_paper(
        replace(settings, allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == INVALID_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)


def test_upstream_health_non_pass_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _valid_manifest(tmp_path)
    manifest["upstream_health_statuses"] = ["PASS", "FAIL"]
    _write_json(settings.manifest_path, manifest)

    result = run_operational_global_approved_for_paper(
        replace(settings, allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)


@pytest.mark.parametrize(
    "field",
    [
        "real_buy_review_requested",
        "trading_requested",
        "buy_review_allowed_requested",
        "strategy_performance_validation_requested",
    ],
)
def test_forbidden_request_fields_block(tmp_path: Path, field: str) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _valid_manifest(tmp_path)
    manifest[field] = True
    _write_json(settings.manifest_path, manifest)

    result = run_operational_global_approved_for_paper(
        replace(settings, allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)


def test_report_only_until_promoted_false_blocks(tmp_path: Path) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _valid_manifest(tmp_path)
    manifest["report_only_until_promoted"] = False
    _write_json(settings.manifest_path, manifest)

    result = run_operational_global_approved_for_paper(
        replace(settings, allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "data/raw/input.csv",
        "data/processed/input.csv",
        "data/cache/input.csv",
        "outputs/reports/current_candidates/run/report.csv",
        "outputs/reports/snapshots/run/report.csv",
        "outputs/reports/signal_semantics_mutation/run/report.csv",
        "outputs/reports/broker/orders.csv",
        "outputs/reports/trading/orders.csv",
    ],
)
def test_forbidden_upstream_artifact_path_blocks(tmp_path: Path, unsafe_path: str) -> None:
    settings = _happy_settings(tmp_path)
    manifest = _valid_manifest(tmp_path)
    manifest["upstream_artifact_paths"] = [unsafe_path]
    _write_json(settings.manifest_path, manifest)

    result = run_operational_global_approved_for_paper(
        replace(settings, allow_operational_global_approved_for_paper_planning=True)
    )

    assert result.status == BLOCKED_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    _assert_downstream_false(result)


def test_output_stays_under_manual_diagnostics_and_no_protected_data_or_project_source_writes(tmp_path: Path) -> None:
    result = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )

    artifact_path = Path(result.artifact_path)
    assert "manual_diagnostics" in artifact_path.as_posix()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_cli_no_input_path_is_safe(tmp_path: Path) -> None:
    completed = _run_cli(["operational-global-approved-for-paper", "--output-dir", _output_dir(tmp_path / "cli")])

    assert completed.returncode == 0
    assert "status: NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT" in completed.stdout
    assert "operational_global_approved_for_paper_planning_artifacts_created: False" in completed.stdout
    assert "operational_global_approved_for_paper_granted: False" in completed.stdout
    assert "global_approved_for_paper: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "buy_review_allowed: False" in completed.stdout
    assert "strategy_performance_validated: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout


def test_cli_valid_manifest_without_allow_path_is_safe(tmp_path: Path) -> None:
    manifest_path = _write_json(tmp_path / "manifest.json", _valid_manifest(tmp_path))

    completed = _run_cli(
        [
            "operational-global-approved-for-paper",
            "--manifest-path",
            manifest_path,
            "--output-dir",
            _output_dir(tmp_path / "cli_ready"),
        ]
    )

    assert completed.returncode == 0
    assert "status: READY_FOR_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REVIEW" in completed.stdout
    assert "ready_for_operational_global_approved_for_paper_review: True" in completed.stdout
    assert "operational_global_approved_for_paper_planning_artifacts_created: False" in completed.stdout
    assert "operational_global_approved_for_paper_granted: False" in completed.stdout


def test_cli_explicit_allow_creates_only_report_only_planning_artifacts(tmp_path: Path) -> None:
    manifest_path = _write_json(tmp_path / "manifest.json", _valid_manifest(tmp_path))
    output_dir = _output_dir(tmp_path / "cli_created")

    completed = _run_cli(
        [
            "operational-global-approved-for-paper",
            "--manifest-path",
            manifest_path,
            "--output-dir",
            output_dir,
            "--allow-operational-global-approved-for-paper-planning",
        ]
    )

    assert completed.returncode == 0
    assert "status: OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED" in completed.stdout
    assert "operational_global_approved_for_paper_planning_artifacts_created: True" in completed.stdout
    assert "operational_global_approved_for_paper_granted: False" in completed.stdout
    assert "real_buy_review_eligible: False" in completed.stdout
    assert "buy_review_allowed: False" in completed.stdout
    assert "strategy_performance_validated: False" in completed.stdout
    assert "trading_allowed: False" in completed.stdout
    assert list(output_dir.rglob("operational_global_approved_for_paper_metadata.json"))
    assert list(output_dir.rglob("operational_global_approved_for_paper_manifest_review.csv"))


def _happy_settings(tmp_path: Path) -> OperationalGlobalApprovedForPaperSettings:
    return OperationalGlobalApprovedForPaperSettings(
        manifest_path=_write_json(tmp_path / "manifest.json", _valid_manifest(tmp_path)),
        output_dir=_output_dir(tmp_path),
    )


def _valid_manifest(tmp_path: Path) -> dict[str, object]:
    safe_report = tmp_path / "reports" / "approved_for_paper_phase1" / "paper_phase1_001" / "report.md"
    return {
        "exact_user_approval_id": "000123456789",
        "approval_scope": "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_REPORT_ONLY_PLANNING",
        "approval_timestamp": "2026-06-23T00:00:00Z",
        "approver_placeholder_id": "placeholder_approver_001",
        "reviewer_placeholder_id": "placeholder_reviewer_001",
        "upstream_artifact_ids": ["paper_phase1_001"],
        "upstream_artifact_paths": [safe_report.as_posix()],
        "upstream_health_statuses": ["PASS"],
        "immutable_lineage_hashes": ["hash_lineage_001"],
        "source_hashes": ["hash_source_001"],
        "revision_ids": ["revision_001"],
        "available_time_summary": "all inputs available before the planning decision time",
        "limitations_acknowledged": True,
        "overfit_warnings_acknowledged": True,
        "metric_limitations_acknowledged": True,
        "paper_workflow_limitations_acknowledged": True,
        "stock_profile_limitations_acknowledged": True,
        "forbidden_outputs_checked": True,
        "side_effects_checked": True,
        "operational_global_approved_for_paper_requested": True,
        "real_buy_review_requested": False,
        "trading_requested": False,
        "buy_review_allowed_requested": False,
        "strategy_performance_validation_requested": False,
        "approval_expiry": "2026-07-23T00:00:00Z",
        "review_cadence": "manual_review_before_any_future_promotion",
        "revocation_path": "manual_revocation_report_only_path",
        "audit_report_path": "outputs/reports/manual_diagnostics/operational_global_approved_for_paper_implementation_planning_v0_1/operational_global_approved_for_paper_implementation_planning.md",
        "created_by_workflow": "operational-global-approved-for-paper report-only planning fixture",
        "report_only_until_promoted": True,
    }


def _safe_artifact_keys() -> list[str]:
    return [
        "operational_global_approved_for_paper_metadata",
        "operational_global_approved_for_paper_health_gate_results",
        "operational_global_approved_for_paper_forbidden_output_guard",
        "operational_global_approved_for_paper_side_effect_guard",
        "operational_global_approved_for_paper_overclaim_guard",
        "recommended_next_task",
    ]


def _substantive_artifact_keys() -> list[str]:
    return [
        "operational_global_approved_for_paper_manifest_review",
        "operational_global_approved_for_paper_lineage_matrix",
        "operational_global_approved_for_paper_limitations",
        "operational_global_approved_for_paper_revocation_plan",
    ]


def _output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "operational_global_approved_for_paper_v0_1"


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
