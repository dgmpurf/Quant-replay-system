from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_package_candidate_contract_fixture import (
    ARTIFACT_FILENAMES,
    DEFAULT_OUTPUT_ROOT,
    FIELD_FAMILY_CONTRACT,
    FORBIDDEN_STATUS_WORDING,
    REQUIRED_CASE_IDS,
    SAFETY_FALSE_FLAGS,
    REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
    TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY,
    build_real_reviewed_package_candidate_contract_fixture_artifacts,
    default_real_reviewed_package_candidate_contract_fixture_cases,
    real_reviewed_package_candidate_contract_fixture_safety_flags,
    real_reviewed_package_candidate_contract_fixture_statuses,
    validate_real_reviewed_package_candidate_contract_fixture_case,
)


def _case(case_id: str) -> dict[str, object]:
    return next(
        case
        for case in default_real_reviewed_package_candidate_contract_fixture_cases()
        if case["case_id"] == case_id
    )


def _validate(case_id: str) -> dict[str, object]:
    return validate_real_reviewed_package_candidate_contract_fixture_case(_case(case_id))


def _output_root(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_real_reviewed_package_candidate_contract_fixture_v0_1"
    )


def test_default_contract_fixture_cases_include_required_cases() -> None:
    cases = default_real_reviewed_package_candidate_contract_fixture_cases()

    assert {case["case_id"] for case in cases} == set(REQUIRED_CASE_IDS)
    assert len(cases) >= 60


def test_minimal_schema_designed_case_is_report_only() -> None:
    result = _validate("minimal_schema_designed_report_only")

    assert result["status"] == REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["blocker_count"] == 0
    assert result["warning_count"] == 0
    assert result["pass_candidate"] is False
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["synthetic_only"] is True


def test_report_only_pass_candidate_has_zero_blockers_and_no_active_flags() -> None:
    result = _validate("report_only_pass_candidate_for_human_review")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW"
    assert result["health_status"] == "PASS"
    assert result["blocker_count"] == 0
    assert result["warning_count"] == 0
    assert result["pass_candidate"] is True
    for flag in SAFETY_FALSE_FLAGS:
        assert result[flag] is False


def test_missing_required_sections_block() -> None:
    for case_id in [
        "missing_package_manifest",
        "missing_source_registry_snapshot",
        "missing_raw_document_reference_manifest",
        "missing_reviewed_file_manifest",
        "missing_table_schema_manifest",
        "missing_row_lineage_manifest",
        "missing_available_time_manifest",
        "missing_source_hash_revision_manifest",
        "missing_reviewer_attestation_manifest",
        "missing_quality_review_manifest",
        "missing_forbidden_downstream_flags",
    ]:
        result = _validate(case_id)
        assert result["health_status"] == "FAIL"
        assert result["blocker_count"] >= 1
        assert result["pass_candidate"] is False


def test_available_time_missing_blocks() -> None:
    result = _validate("missing_available_time")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING"
    assert "pit_timing" in result["blocker_categories"]


def test_available_time_after_decision_blocks() -> None:
    result = _validate("available_time_after_replay_decision_time")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING"
    assert result["health_status"] == "FAIL"


def test_conflicting_available_time_blocks() -> None:
    result = _validate("conflicting_available_time")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING"
    assert "pit_timing" in result["blocker_categories"]


def test_future_revision_risk_warns_or_blocks() -> None:
    for case_id in ["future_revision_risk", "future_revision_risk_warns_or_blocks"]:
        result = _validate(case_id)
        assert result["health_status"] in {"WARN", "FAIL"}
        assert "future_revision_risk" in result["warning_categories"] or "revision_conflict" in result["blocker_categories"]


def test_missing_source_hash_blocks() -> None:
    result = _validate("missing_source_hash")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "source_hash" in result["blocker_categories"]


def test_missing_local_file_hash_blocks() -> None:
    result = _validate("missing_local_file_hash")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "local_file_hash" in result["blocker_categories"]


def test_missing_revision_id_blocks_or_needs_pro_review() -> None:
    result = _validate("missing_revision_id")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "revision_id" in result["blocker_categories"]
    assert "needs_pro_review" in result["warning_categories"]


def test_revision_conflict_blocks() -> None:
    result = _validate("revision_conflict")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "revision_conflict" in result["blocker_categories"]


def test_filename_as_revision_id_blocks() -> None:
    result = _validate("filename_as_revision_id_blocks")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "revision_id" in result["blocker_categories"]


def test_missing_reviewer_authority_blocks() -> None:
    result = _validate("missing_reviewer_authority")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY"
    assert "reviewer_authority" in result["blocker_categories"]


def test_reviewer_approval_does_not_override_pit_failure() -> None:
    for case_id in [
        "reviewer_approval_attempts_to_override_pit_failure",
        "reviewer_approval_cannot_override_timing_failure",
        "reviewer_approval_cannot_override_source_hash_failure",
        "reviewer_approval_cannot_override_available_time_failure",
        "reviewer_approval_cannot_override_revision_conflict",
        "reviewer_approval_cannot_override_quality_failed",
    ]:
        result = _validate(case_id)
        assert result["blocker_count"] >= 1
        assert "reviewer_non_override" in result["blocker_categories"]
        assert "does not override" in result["why_report_only"]


def test_quality_failed_blocks() -> None:
    result = _validate("quality_failed")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
    assert result["health_status"] == "FAIL"


def test_warning_requires_limitation_note() -> None:
    result = _validate("warning_without_limitation_note")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
    assert "limitation_missing" in result["blocker_categories"]


def test_forbidden_downstream_flag_true_blocks() -> None:
    result = _validate("forbidden_downstream_flag_true")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"
    assert "forbidden_downstream" in result["blocker_categories"]
    for flag in SAFETY_FALSE_FLAGS:
        assert result[flag] is False


def test_unsafe_status_wording_blocks() -> None:
    for case_id in [
        "unsafe_status_wording_ready_for_replay",
        "unsafe_status_wording_active_replay_input_ready",
    ]:
        result = _validate(case_id)
        assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
        assert "unsafe_wording" in result["blocker_categories"]


def test_future_label_leakage_blocks() -> None:
    result = _validate("future_label_leakage")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert "future_label_leakage" in result["blocker_categories"]


def test_protected_data_write_claim_blocks() -> None:
    result = _validate("protected_data_write_claimed")

    assert result["status"] == "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert "protected_write" in result["blocker_categories"]
    assert result["data_raw_written"] is False
    assert result["data_processed_written"] is False
    assert result["data_cache_written"] is False


def test_artifacts_write_only_under_manual_diagnostics_or_tmp_path(tmp_path: Path) -> None:
    result = build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=_output_root(tmp_path))

    assert result.artifact_path.is_relative_to(_output_root(tmp_path))
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == set(ARTIFACT_FILENAMES.values())
    assert "manual_diagnostics" in DEFAULT_OUTPUT_ROOT


def test_rejects_data_raw_processed_cache_output_roots(tmp_path: Path) -> None:
    for unsafe in [
        tmp_path / "data" / "raw",
        tmp_path / "data" / "processed",
        tmp_path / "data" / "cache",
    ]:
        with pytest.raises(ValueError):
            build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=unsafe)


def test_rejects_docs_project_sources_output_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=tmp_path / "docs" / "project_sources")


def test_no_docs_project_sources_created(tmp_path: Path) -> None:
    build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=_output_root(tmp_path))

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not Path("docs/project_sources").exists()


def test_no_real_csv_required() -> None:
    signature = inspect.signature(build_real_reviewed_package_candidate_contract_fixture_artifacts)

    assert "csv" not in " ".join(signature.parameters)
    assert "path" not in " ".join(parameter for parameter in signature.parameters if parameter != "output_root")


def test_no_data_raw_processed_cache_writes(tmp_path: Path) -> None:
    build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=_output_root(tmp_path))

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_no_active_replay_input_ready_status() -> None:
    statuses = real_reviewed_package_candidate_contract_fixture_statuses()

    assert "ACTIVE_REPLAY_INPUT_READY" not in statuses
    assert all("ACTIVE_REPLAY_INPUT_READY" not in case["status"] for case in default_real_reviewed_package_candidate_contract_fixture_cases())


def test_status_vocabulary_excludes_forbidden_terms() -> None:
    statuses = real_reviewed_package_candidate_contract_fixture_statuses()

    for forbidden in FORBIDDEN_STATUS_WORDING:
        assert forbidden not in statuses


def test_public_api_has_no_real_csv_path_argument() -> None:
    for function in [
        default_real_reviewed_package_candidate_contract_fixture_cases,
        real_reviewed_package_candidate_contract_fixture_statuses,
        real_reviewed_package_candidate_contract_fixture_safety_flags,
        validate_real_reviewed_package_candidate_contract_fixture_case,
        build_real_reviewed_package_candidate_contract_fixture_artifacts,
    ]:
        parameters = inspect.signature(function).parameters
        assert not any("csv" in name.lower() for name in parameters)
        assert not any("real" in name.lower() and "path" in name.lower() for name in parameters)


def test_metadata_aggregate_health_pass_despite_expected_negative_cases(tmp_path: Path) -> None:
    result = build_real_reviewed_package_candidate_contract_fixture_artifacts(output_root=_output_root(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.workflow_stage == TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY
    assert result.status == REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    assert result.health_status == "PASS"
    assert result.fail_count > 0
    assert metadata["health_status"] == "PASS"
    assert metadata["status"] == REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["synthetic_only"] is True
    for flag in SAFETY_FALSE_FLAGS:
        assert metadata[flag] is False


def test_field_family_contract_records_required_groups() -> None:
    families = {row["field_family"] for row in FIELD_FAMILY_CONTRACT}

    assert families == {
        "package_identity",
        "source_lineage",
        "hash_revision",
        "timing",
        "reviewer",
        "quality",
        "limitation",
        "forbidden_downstream_flags",
    }
