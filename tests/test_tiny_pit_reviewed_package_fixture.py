from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_reviewed_package_fixture import (
    REQUIRED_REVIEWED_PACKAGE_FIXTURE_CASE_STATUS_MAP,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
    build_tiny_pit_reviewed_package_fixture_artifacts,
    default_tiny_pit_reviewed_package_fixture_cases,
    tiny_pit_reviewed_package_fixture_safety_flags,
    tiny_pit_reviewed_package_fixture_statuses,
    validate_tiny_pit_reviewed_package_fixture_case,
)


EXPECTED_CASES = {
    "minimal_valid_synthetic_package",
    "missing_package_manifest",
    "missing_reviewed_source_manifest",
    "missing_source_hash",
    "missing_revision_id",
    "available_time_after_replay_decision_time",
    "future_revision_risk",
    "reviewer_missing",
    "reviewer_authority_missing",
    "reviewer_approval_with_pit_failure",
    "quality_failed",
    "required_section_missing",
    "forbidden_downstream_flag_true",
    "unsafe_active_ready_wording",
    "malformed_metadata",
}

EXPECTED_STATUSES = {
    "NO_PACKAGE_FIXTURE",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_WARN_REVIEW_REQUIRED",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_REVIEWER",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_QUALITY",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM",
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_HEALTH_FAILED",
}

EXPECTED_ARTIFACTS = {
    "metadata.json",
    "tiny_pit_reviewed_package_fixture_report.md",
    "package_manifest.json",
    "reviewed_source_manifest.csv",
    "reviewed_file_manifest.csv",
    "package_section_manifest.csv",
    "evidence_lineage_manifest.csv",
    "timing_manifest.csv",
    "reviewer_attestation_manifest.csv",
    "quality_review_manifest.csv",
    "forbidden_downstream_flags.json",
    "package_limitations.md",
}


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "tiny_pit_reviewed_package_fixture_v0_1"


def _case(name: str) -> dict[str, object]:
    return next(case for case in default_tiny_pit_reviewed_package_fixture_cases() if case["case_name"] == name)


def _validate(name: str) -> dict[str, object]:
    return validate_tiny_pit_reviewed_package_fixture_case(_case(name))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _all_artifact_text(artifact_dir: Path) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in artifact_dir.iterdir()
        if path.suffix in {".csv", ".json", ".md"}
    )


def test_default_tiny_pit_reviewed_package_fixture_cases_include_required_cases() -> None:
    cases = default_tiny_pit_reviewed_package_fixture_cases()

    assert {case["case_name"] for case in cases} == EXPECTED_CASES
    assert set(REQUIRED_REVIEWED_PACKAGE_FIXTURE_CASE_STATUS_MAP) == EXPECTED_CASES


def test_status_vocabulary_is_non_active() -> None:
    statuses = tiny_pit_reviewed_package_fixture_statuses()

    assert set(statuses) == EXPECTED_STATUSES
    assert "ACTIVE_REPLAY_INPUT_READY" not in statuses
    assert all("TRADING" not in status for status in statuses)


def test_safety_flags_default_false() -> None:
    flags = tiny_pit_reviewed_package_fixture_safety_flags()

    assert set(flags) == set(SAFETY_FALSE_FLAGS)
    assert all(value is False for value in flags.values())


def test_minimal_valid_synthetic_package_creates_required_sections(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    assert result.workflow_stage == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.status == TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY
    assert result.health_status == "PASS"
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.synthetic_only is True
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == EXPECTED_ARTIFACTS
    assert result.artifact_paths["artifact_dir"].is_relative_to(_output_root(tmp_path))


def test_minimal_valid_synthetic_package_has_zero_blockers() -> None:
    result = _validate("minimal_valid_synthetic_package")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["blocker_count"] == 0
    assert result["warning_count"] == 0


def test_warning_case_has_warning_and_zero_blockers() -> None:
    result = _validate("future_revision_risk")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_WARN_REVIEW_REQUIRED"
    assert result["health_status"] == "WARN"
    assert result["blocker_count"] == 0
    assert result["warning_count"] >= 1


@pytest.mark.parametrize(
    ("case_name", "expected_status"),
    [
        ("missing_package_manifest", "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"),
        ("missing_reviewed_source_manifest", "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"),
        ("required_section_missing", "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"),
    ],
)
def test_missing_section_cases_block(case_name: str, expected_status: str) -> None:
    result = _validate(case_name)

    assert result["actual_status"] == expected_status
    assert result["blocker_count"] >= 1


def test_missing_package_manifest_blocks() -> None:
    assert _validate("missing_package_manifest")["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"


def test_missing_reviewed_source_manifest_blocks() -> None:
    assert _validate("missing_reviewed_source_manifest")["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"


def test_missing_source_hash_blocks_source_lineage() -> None:
    result = _validate("missing_source_hash")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE"
    assert result["blocker_count"] >= 1


def test_missing_revision_id_blocks_source_lineage() -> None:
    result = _validate("missing_revision_id")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE"
    assert result["blocker_count"] >= 1


def test_available_time_after_replay_decision_time_blocks_timing() -> None:
    result = _validate("available_time_after_replay_decision_time")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING"
    assert result["blocker_count"] >= 1


def test_reviewer_approval_does_not_override_pit_failure() -> None:
    result = _validate("reviewer_approval_with_pit_failure")

    assert result["actual_status"] in {
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE",
    }
    assert result["blocker_count"] >= 1
    assert result["warning_count"] >= 1
    assert "does not override" in str(result["limitation_note"])


def test_quality_failed_blocks() -> None:
    result = _validate("quality_failed")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_QUALITY"
    assert result["health_status"] == "FAIL"
    assert result["blocker_count"] >= 1


def test_required_section_missing_blocks() -> None:
    assert _validate("required_section_missing")["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION"


def test_forbidden_downstream_flag_true_blocks() -> None:
    result = _validate("forbidden_downstream_flag_true")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"
    assert result["blocker_count"] >= 1
    assert result["active_replay_input"] is False
    assert result["trading_allowed"] is False


def test_unsafe_active_ready_wording_blocks() -> None:
    result = _validate("unsafe_active_ready_wording")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"
    assert result["blocker_count"] >= 1


def test_malformed_metadata_health_fails() -> None:
    result = _validate("malformed_metadata")

    assert result["actual_status"] == "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_HEALTH_FAILED"
    assert result["health_status"] == "FAIL"
    assert result["blocker_count"] >= 1


def test_artifacts_write_only_under_tmp_path_or_manual_diagnostics_root(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    for path in result.artifact_paths.values():
        if path.name != "artifact_dir":
            assert path.is_relative_to(result.artifact_paths["artifact_dir"])
    with pytest.raises(ValueError):
        build_tiny_pit_reviewed_package_fixture_artifacts(output_root=tmp_path / "data" / "raw")
    with pytest.raises(ValueError):
        build_tiny_pit_reviewed_package_fixture_artifacts(output_root=tmp_path / "docs" / "project_sources")


def test_no_data_raw_processed_cache_writes(tmp_path: Path) -> None:
    build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_no_real_file_path_required() -> None:
    result = _validate("minimal_valid_synthetic_package")

    assert result["real_file_path_required"] is False
    assert result["synthetic_only"] is True


def test_no_real_csv_consumed(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["real_reviewed_csv_package_created"] is False
    assert metadata["real_csv_consumed"] is False


def test_no_cli_or_views_created_in_core_task(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    assert not (result.artifact_paths["artifact_dir"] / "index").exists()
    assert not (result.artifact_paths["artifact_dir"] / "health").exists()
    assert not (result.artifact_paths["artifact_dir"] / "status").exists()
    assert not any(path.name.endswith(("_index.csv", "_health.csv", "_status.csv")) for path in result.artifact_paths["artifact_dir"].iterdir())


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not Path("docs/project_sources").exists()


def test_ids_remain_strings(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert isinstance(result.fixture_id, str)
    assert isinstance(metadata["fixture_id"], str)
    assert isinstance(metadata["package_id"], str)
    assert metadata["package_id"] == "000001"


def test_report_text_never_emits_active_ready_permission(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    safety = json.loads(result.artifact_paths["forbidden_downstream_flags"].read_text(encoding="utf-8"))
    report = result.artifact_paths["report"].read_text(encoding="utf-8")
    all_text = _all_artifact_text(result.artifact_paths["artifact_dir"])

    assert "synthetic-only" in report
    assert "report-only" in report
    assert "diagnostic-only" in report
    assert "reviewed means simulated metadata only" in report
    assert "not real reviewed CSV package" in report
    assert "not active reviewed input candidate" in report
    assert "not real replay input" in report
    assert "not active replay input" in report
    assert "not ACTIVE_REPLAY_INPUT_READY" in report
    assert "no replay execution" in report
    assert "no labels/training/metrics/signal_score/model/stock_profile/paper/buy-review/performance/trading" in report
    assert "no data/raw, data/processed, or data/cache writes" in report
    assert metadata["active_replay_input_ready_emitted"] is False
    assert all(value is False for value in safety.values())
    assert "ACTIVE_REPLAY_INPUT_READY,true" not in all_text
    assert "active_replay_input_ready_emitted,true" not in all_text


def test_written_csv_manifests_are_synthetic_and_report_only(tmp_path: Path) -> None:
    result = build_tiny_pit_reviewed_package_fixture_artifacts(output_root=_output_root(tmp_path))

    for key in [
        "reviewed_source_manifest",
        "reviewed_file_manifest",
        "package_section_manifest",
        "evidence_lineage_manifest",
        "timing_manifest",
        "reviewer_attestation_manifest",
        "quality_review_manifest",
    ]:
        rows = _csv_rows(result.artifact_paths[key])
        assert rows
        assert all(row["report_only"] == "True" for row in rows)
        assert all(row["diagnostic_only"] == "True" for row in rows)
        assert all(row["synthetic_only"] == "True" for row in rows)
