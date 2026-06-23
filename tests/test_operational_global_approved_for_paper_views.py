from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent))
from test_operational_global_approved_for_paper import DOWNSTREAM_FALSE_FIELDS
from test_operational_global_approved_for_paper import _happy_settings
from test_operational_global_approved_for_paper import _output_dir
from test_operational_global_approved_for_paper import _read_json

from quant_replay_system.operational_global_approved_for_paper import (
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED,
    run_operational_global_approved_for_paper,
)
from quant_replay_system.operational_global_approved_for_paper_health import (
    check_operational_global_approved_for_paper_health,
)
from quant_replay_system.operational_global_approved_for_paper_index import (
    build_operational_global_approved_for_paper_index,
)
from quant_replay_system.operational_global_approved_for_paper_status import (
    NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND,
    OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED,
    run_operational_global_approved_for_paper_status,
)


def test_index_safe_empty_when_no_artifacts_exist(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)

    result = build_operational_global_approved_for_paper_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 0
    assert result.latest_run_id == ""
    assert result.latest_status == ""
    assert result.index_frame.empty
    assert result.artifact_paths["index_csv"].exists()
    metadata = _read_json(result.artifact_paths["metadata"])
    assert metadata["artifact_count"] == 0
    assert metadata["diagnostic_only"] is True


def test_index_ignores_view_directories_and_preserves_numeric_run_id_as_string(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    for view_dir in ["index", "health", "status"]:
        (root / view_dir).mkdir(parents=True)
    run_dir = root / "000123456789"
    run_dir.mkdir(parents=True)
    metadata = _safe_metadata("000123456789", NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT)
    _write_json(run_dir / "operational_global_approved_for_paper_metadata.json", metadata)

    result = build_operational_global_approved_for_paper_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert isinstance(row["operational_global_approved_for_paper_id"], str)
    assert row["operational_global_approved_for_paper_id"] == "000123456789"
    assert result.latest_run_id == "000123456789"


def test_index_discovers_valid_no_input_and_planning_created_runs(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    no_input = run_operational_global_approved_for_paper(_happy_settings(tmp_path / "no_input_fixture"))
    created = run_operational_global_approved_for_paper(
        replace(
            _happy_settings(tmp_path / "created_fixture"),
            output_dir=root,
            allow_operational_global_approved_for_paper_planning=True,
        )
    )

    result = build_operational_global_approved_for_paper_index(root=root, output_dir=root / "index")

    assert no_input.artifact_path != created.artifact_path
    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["operational_global_approved_for_paper_id"] == created.operational_global_approved_for_paper_id
    assert row["status"] == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
    assert row["operational_global_approved_for_paper_planning_artifacts_created"] is True
    assert row["operational_global_approved_for_paper_granted"] is False
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert row[field] is False, field


def test_health_passes_for_safe_no_input_and_valid_planning_created_runs(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    run_operational_global_approved_for_paper(_happy_settings(tmp_path / "ready"))
    run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path / "created"), output_dir=root, allow_operational_global_approved_for_paper_planning=True)
    )

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.checked_artifact_count == 1
    assert result.artifact_paths["health_csv"].exists()


def test_health_fails_when_created_state_artifact_missing(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )
    core.artifact_paths["operational_global_approved_for_paper_lineage_matrix"].unlink()

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "MISSING_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_LINEAGE_MATRIX" in set(result.health_frame["issue_code"])


def test_health_fails_when_metadata_unreadable(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )
    core.artifact_paths["operational_global_approved_for_paper_metadata"].write_text("{", encoding="utf-8")

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "UNREADABLE_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_METADATA" in set(result.health_frame["issue_code"])


def test_health_fails_for_unknown_status(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(_happy_settings(tmp_path))
    _patch_metadata(core, {"status": "OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_GRANTED"})

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "UNKNOWN_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_STATUS" in set(result.health_frame["issue_code"])


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_health_fails_when_forbidden_flag_is_true(tmp_path: Path, field: str) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )
    _patch_metadata(core, {field: True})

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert f"{field.upper()}_UNEXPECTED" in set(result.health_frame["issue_code"])


def test_health_fails_when_artifact_path_implies_forbidden_operational_output(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )
    _patch_metadata(core, {"artifact_paths": {"unsafe": "outputs/reports/current_candidates/run/report.csv"}})

    result = check_operational_global_approved_for_paper_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_OPERATIONAL_ARTIFACT_PATH" in set(result.health_frame["issue_code"])


def test_status_safe_empty_when_no_artifacts_exist(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)

    result = run_operational_global_approved_for_paper_status(root=root, output_dir=root / "status")

    assert result.workflow_stage == NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND
    assert result.status == "MISSING"
    assert result.health_status == "PASS"
    assert result.operational_global_approved_for_paper_granted is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_status_summarizes_latest_no_input_run_safely(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(OperationalGlobalNoInputSettings(root))

    result = run_operational_global_approved_for_paper_status(root=root, output_dir=root / "status")

    assert result.latest_operational_global_approved_for_paper_id == core.operational_global_approved_for_paper_id
    assert result.status == NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_INPUT
    assert result.health_status == "PASS"
    assert result.operational_global_approved_for_paper_planning_artifacts_created is False
    assert result.operational_global_approved_for_paper_granted is False
    for field in DOWNSTREAM_FALSE_FIELDS:
        assert getattr(result, field) is False, field


def test_status_summarizes_planning_created_run_safely(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )

    result = run_operational_global_approved_for_paper_status(root=root, output_dir=root / "status")

    assert result.latest_operational_global_approved_for_paper_id == core.operational_global_approved_for_paper_id
    assert result.status == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_PLANNING_ARTIFACTS_CREATED
    assert result.health_status == "PASS"
    assert result.operational_global_approved_for_paper_planning_artifacts_created is True
    assert result.operational_global_approved_for_paper_granted is False
    assert result.global_approved_for_paper is False
    assert result.real_buy_review_eligible is False
    assert result.buy_review_allowed is False
    assert result.strategy_performance_validated is False
    assert result.trading_allowed is False


def test_status_reports_health_failed_for_unsafe_latest_artifact(tmp_path: Path) -> None:
    root = _output_dir(tmp_path)
    core = run_operational_global_approved_for_paper(
        replace(_happy_settings(tmp_path), allow_operational_global_approved_for_paper_planning=True)
    )
    _patch_metadata(core, {"buy_review_allowed": True})

    result = run_operational_global_approved_for_paper_status(root=root, output_dir=root / "status")

    assert result.health_status == "FAIL"
    assert result.workflow_stage == OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_HEALTH_FAILED
    assert result.buy_review_allowed is True
    assert result.operational_global_approved_for_paper_granted is False


def test_cli_view_commands_run_successfully(tmp_path: Path) -> None:
    root = _output_dir(tmp_path / "cli")

    index = _run_cli(["operational-global-approved-for-paper-index", "--root", root, "--output-dir", root / "index"])
    health = _run_cli(["operational-global-approved-for-paper-health", "--root", root, "--output-dir", root / "health"])
    status = _run_cli(["operational-global-approved-for-paper-status", "--root", root, "--output-dir", root / "status"])

    assert index.returncode == 0
    assert "artifact_count: 0" in index.stdout
    assert health.returncode == 0
    assert "status: PASS" in health.stdout
    assert status.returncode == 0
    assert f"workflow_stage: {NO_OPERATIONAL_GLOBAL_APPROVED_FOR_PAPER_ARTIFACT_FOUND}" in status.stdout
    assert "operational_global_approved_for_paper_granted: False" in status.stdout
    assert "buy_review_allowed: False" in status.stdout
    assert "trading_allowed: False" in status.stdout


def test_only_core_and_view_commands_are_registered() -> None:
    cli_text = Path("src/quant_replay_system/cli.py").read_text(encoding="utf-8")

    for command in [
        "operational-global-approved-for-paper",
        "operational-global-approved-for-paper-index",
        "operational-global-approved-for-paper-health",
        "operational-global-approved-for-paper-status",
    ]:
        assert command in cli_text
    assert "operational-global-approved-for-paper-research-status" not in cli_text


def OperationalGlobalNoInputSettings(root: Path):
    from quant_replay_system.operational_global_approved_for_paper import OperationalGlobalApprovedForPaperSettings

    return OperationalGlobalApprovedForPaperSettings(output_dir=root)


def _safe_metadata(run_id: str, status: str) -> dict[str, object]:
    return {
        "operational_global_approved_for_paper_id": run_id,
        "status": status,
        "workflow_stage": status,
        "ready_for_operational_global_approved_for_paper_review": False,
        "operational_global_approved_for_paper_planning_artifacts_created": False,
        "operational_global_approved_for_paper_granted": False,
        "global_approved_for_paper": False,
        "real_buy_review_eligible": False,
        "buy_review_allowed": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        **{field: False for field in DOWNSTREAM_FALSE_FIELDS if field not in {"real_buy_review_eligible", "buy_review_allowed", "strategy_performance_validated", "trading_allowed"}},
        "report_only": True,
        "research_governed": True,
        "diagnostic_output": True,
    }


def _patch_metadata(core_result: object, patch: dict[str, object]) -> None:
    path = core_result.artifact_paths["operational_global_approved_for_paper_metadata"]
    metadata = _read_json(path)
    metadata.update(patch)
    _write_json(path, metadata)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


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
