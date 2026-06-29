from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_admissibility_validator import (
    REQUIRED_SYNTHETIC_CASE_STATUS_MAP,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED,
    build_synthetic_validator_artifacts,
    default_synthetic_package_cases,
    tiny_pit_admissibility_validator_safety_flags,
    tiny_pit_admissibility_validator_statuses,
    validate_synthetic_package_case,
)


EXPECTED_ARTIFACTS = {
    "metadata.json",
    "tiny_pit_admissibility_validator_report.md",
    "package_gate_matrix.csv",
    "timing_admissibility_matrix.csv",
    "source_lineage_matrix.csv",
    "reviewer_authority_matrix.csv",
    "quality_gate_matrix.csv",
    "output_status_contract.csv",
    "forbidden_interpretation_matrix.csv",
    "safety_flags.json",
}

EXPECTED_CASES = {
    "no_input",
    "valid_diagnostic_only_package",
    "missing_package_manifest",
    "missing_required_section",
    "missing_source_hash",
    "missing_revision_id",
    "available_time_after_replay_decision_time",
    "unknown_available_time",
    "conflicting_available_time",
    "missing_reviewer_authority",
    "reviewer_approval_with_pit_failure",
    "quality_failed",
    "warning_only_package",
    "forbidden_downstream_flag_leakage",
}

EXPECTED_CASE_COLUMNS = {
    "case_id",
    "case_name",
    "expected_status",
    "actual_status",
    "blocker_count",
    "warning_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "active_replay_input",
    "active_replay_ready",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "forbidden_interpretation",
    "limitation_note",
}


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "tiny_pit_admissibility_validator_v0_1"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _artifact_text(result) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths["artifact_dir"].iterdir()
        if path.suffix in {".csv", ".json", ".md"}
    )


def test_default_synthetic_cases_include_all_required_cases_and_statuses() -> None:
    cases = default_synthetic_package_cases()

    assert {case["case_name"] for case in cases} == EXPECTED_CASES
    assert set(REQUIRED_SYNTHETIC_CASE_STATUS_MAP) == EXPECTED_CASES
    assert set(tiny_pit_admissibility_validator_statuses()) == {
        "NO_INPUT",
        "PACKAGE_SCHEMA_INVALID",
        "PACKAGE_BLOCKED_MISSING_REQUIRED_SECTION",
        "PACKAGE_BLOCKED_PIT_TIMING",
        "PACKAGE_BLOCKED_SOURCE_LINEAGE",
        "PACKAGE_BLOCKED_REVIEWER_AUTHORITY",
        "PACKAGE_BLOCKED_QUALITY",
        "PACKAGE_WARN_REVIEW_REQUIRED",
        "PACKAGE_PASS_CANDIDATE_FOR_HUMAN_REVIEW",
        "PACKAGE_DIAGNOSTIC_ONLY_PASS",
    }


@pytest.mark.parametrize("case", default_synthetic_package_cases(), ids=lambda case: case["case_name"])
def test_each_required_case_maps_to_expected_status_and_safe_counts(case: dict[str, object]) -> None:
    result = validate_synthetic_package_case(case)

    assert result["actual_status"] == REQUIRED_SYNTHETIC_CASE_STATUS_MAP[result["case_name"]]
    assert result["expected_status"] == result["actual_status"]
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["synthetic_only"] is True
    assert result["active_replay_input"] is False
    assert result["active_replay_ready"] is False
    assert result["trading_allowed"] is False
    assert result["data_raw_written"] is False
    assert result["data_processed_written"] is False
    assert result["data_cache_written"] is False
    assert result["actual_status"] != "ACTIVE_REPLAY_INPUT_READY"

    if result["case_name"] == "valid_diagnostic_only_package":
        assert result["blocker_count"] == 0
        assert result["warning_count"] == 0
    elif result["case_name"] == "warning_only_package":
        assert result["blocker_count"] == 0
        assert result["warning_count"] > 0
    elif result["case_name"] != "no_input":
        assert result["blocker_count"] > 0


def test_reviewer_approval_with_pit_failure_and_forbidden_flag_leakage_are_rejected() -> None:
    reviewer_case = next(
        case
        for case in default_synthetic_package_cases()
        if case["case_name"] == "reviewer_approval_with_pit_failure"
    )
    forbidden_case = next(
        case
        for case in default_synthetic_package_cases()
        if case["case_name"] == "forbidden_downstream_flag_leakage"
    )

    reviewer_result = validate_synthetic_package_case(reviewer_case)
    forbidden_result = validate_synthetic_package_case(forbidden_case)

    assert reviewer_result["actual_status"] == "PACKAGE_BLOCKED_PIT_TIMING"
    assert "does not override PIT failure" in reviewer_result["limitation_note"]
    assert reviewer_result["blocker_count"] > 0
    assert forbidden_result["actual_status"] == "PACKAGE_SCHEMA_INVALID"
    assert forbidden_result["blocker_count"] > 0
    assert "forbidden downstream flag" in forbidden_result["limitation_note"]


def test_build_synthetic_validator_artifacts_writes_expected_tmp_path_artifacts(tmp_path: Path) -> None:
    result = build_synthetic_validator_artifacts(output_dir=_output_root(tmp_path))

    assert result.workflow_stage == TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED
    assert result.status == "PASS"
    assert result.health_status == "PASS"
    assert result.case_count == len(EXPECTED_CASES)
    assert result.pass_candidate_count == 1
    assert result.blocker_count > 0
    assert result.warning_count > 0
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.synthetic_only is True
    assert result.artifact_paths["artifact_dir"].is_relative_to(_output_root(tmp_path))
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_metadata_safety_flags_and_report_preserve_boundaries(tmp_path: Path) -> None:
    result = build_synthetic_validator_artifacts(output_dir=_output_root(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    all_text = _artifact_text(result)

    assert metadata["workflow_stage"] == TINY_PIT_ADMISSIBILITY_VALIDATOR_SYNTHETIC_CORE_CREATED
    assert metadata["workflow_stage"] != "ACTIVE_REPLAY_INPUT_READY"
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["synthetic_only"] is True
    assert metadata["real_data_allowed"] is False
    assert metadata["active_replay_input"] is False
    assert metadata["active_replay_ready"] is False
    assert metadata["trading_allowed"] is False
    assert metadata["data_raw_written"] is False
    assert metadata["data_processed_written"] is False
    assert metadata["data_cache_written"] is False
    assert metadata["artifact_path"] == str(result.artifact_paths["artifact_dir"])
    assert metadata["report_path"] == str(result.artifact_paths["report"])

    assert safety == tiny_pit_admissibility_validator_safety_flags()
    for flag in SAFETY_FALSE_FLAGS:
        assert safety[flag] is False
        assert metadata[flag] is False

    assert "synthetic-only" in report
    assert "report-only" in report
    assert "diagnostic-only" in report
    assert "no real PIT validator" in report
    assert "no real reviewed CSV package" in report
    assert "no active replay input" in report
    assert "no replay execution" in report
    assert "no labels" in report
    assert "no training" in report
    assert "no metrics" in report
    assert "no signal_score" in report
    assert "no model" in report
    assert "no stock_profile" in report
    assert "no paper validation" in report
    assert "no buy-review" in report
    assert "no trading" in report
    assert "no data/raw, data/processed, or data/cache writes" in report
    assert "ACTIVE_REPLAY_INPUT_READY" not in all_text
    assert "trading_allowed,true" not in all_text.lower()
    assert not re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower())


def test_csv_artifacts_have_expected_columns_and_status_contract_is_safe(tmp_path: Path) -> None:
    result = build_synthetic_validator_artifacts(output_dir=_output_root(tmp_path))
    package_rows = _csv_rows(result.artifact_paths["package_gate_matrix"])
    statuses = _csv_rows(result.artifact_paths["output_status_contract"])
    forbidden = _csv_rows(result.artifact_paths["forbidden_interpretation_matrix"])

    assert set(package_rows[0]) == EXPECTED_CASE_COLUMNS
    assert {row["case_name"] for row in package_rows} == EXPECTED_CASES
    assert all(row["actual_status"] != "ACTIVE_REPLAY_INPUT_READY" for row in package_rows)
    assert {row["status_name"] for row in statuses} == set(tiny_pit_admissibility_validator_statuses())
    assert all(row["active_replay_input_allowed"] == "False" for row in statuses)
    assert all(row["trading_allowed"] == "False" for row in statuses)
    assert "active_replay_input" in {row["forbidden_interpretation"] for row in forbidden}
    assert "trading_allowed" in {row["forbidden_interpretation"] for row in forbidden}


def test_core_cli_command_is_report_only_after_views_task() -> None:
    help_output = subprocess.run(
        [sys.executable, "-m", "quant_replay_system.cli", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    ).stdout

    assert re.search(r"^\s*tiny-pit-admissibility-validator\s", help_output, re.MULTILINE)
