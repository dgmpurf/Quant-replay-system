from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture import (
    ARTIFACT_FILENAMES,
    FIELD_FAMILY_CONTRACT,
    FORBIDDEN_STATUS_WORDING,
    REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
    REQUIRED_CASE_IDS,
    SAFETY_FALSE_FLAGS,
    TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY,
    build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
    default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases,
    real_reviewed_local_csv_package_candidate_preflight_safety_flags,
    real_reviewed_local_csv_package_candidate_preflight_statuses,
    validate_real_reviewed_local_csv_package_candidate_preflight_contract_case,
    write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
)


def _case(case_id: str) -> dict[str, object]:
    return next(
        case
        for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases()
        if case["case_id"] == case_id
    )


def _validate(case_id: str) -> dict[str, object]:
    return validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(_case(case_id))


def _output_root(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_v0_1"
    )


def test_default_preflight_contract_fixture_cases_include_required_cases() -> None:
    cases = default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases()

    assert {case["case_id"] for case in cases} == set(REQUIRED_CASE_IDS)
    assert len(cases) >= 55


def test_schema_designed_case_is_report_only() -> None:
    result = _validate("schema_designed_report_only")

    assert result["status"] == REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["blocker_count"] == 0
    assert result["warning_count"] == 0
    assert result["pass_candidate"] is False
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["synthetic_only"] is True


def test_declared_candidate_is_report_only_and_not_real_package_created() -> None:
    result = _validate("declared_report_only_candidate")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_DECLARED_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["real_package_candidate_created"] is False
    assert result["real_reviewed_csv_package_created"] is False
    assert result["real_csv_required"] is False
    assert result["real_csv_consumed"] is False


def test_complete_pass_candidate_for_human_review_has_no_blockers_and_no_active_flags() -> None:
    result = _validate("complete_report_only_pass_candidate_for_human_review")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW"
    assert result["health_status"] == "PASS"
    assert result["blocker_count"] == 0
    assert result["warning_count"] == 0
    assert result["pass_candidate"] is True
    for flag in SAFETY_FALSE_FLAGS:
        assert result[flag] is False


def test_allowed_status_vocabulary_excludes_forbidden_terms() -> None:
    statuses = real_reviewed_local_csv_package_candidate_preflight_statuses()

    for forbidden in FORBIDDEN_STATUS_WORDING:
        assert forbidden not in statuses
    assert "ACTIVE_REPLAY_INPUT_READY" not in statuses


def test_report_only_flags_true_for_all_cases() -> None:
    for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases():
        result = validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case)
        assert result["report_only"] is True
        assert result["diagnostic_only"] is True
        assert result["synthetic_only"] is True


def test_no_real_csv_required_or_consumed_for_all_cases() -> None:
    for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases():
        result = validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case)
        assert result["real_csv_required"] is False
        assert result["real_csv_consumed"] is False


def test_no_real_package_candidate_created_for_all_cases() -> None:
    for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases():
        result = validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case)
        assert result["real_package_candidate_created"] is False
        assert result["real_reviewed_csv_package_created"] is False


def test_no_active_reviewed_input_candidate_created_for_all_cases() -> None:
    for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases():
        result = validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case)
        assert result["active_reviewed_input_candidate_created"] is False


def test_no_active_replay_input_or_active_ready_emitted() -> None:
    for case in default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases():
        result = validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case)
        assert result["active_replay_input"] is False
        assert result["active_replay_ready"] is False
        assert result["active_replay_input_ready_emitted"] is False


def test_missing_required_sections_block() -> None:
    for case_id in [
        "missing_package_manifest",
        "missing_source_registry_snapshot",
        "missing_raw_document_or_dataset_reference_manifest",
        "missing_reviewed_file_manifest",
        "missing_table_schema_manifest",
        "missing_row_lineage_manifest",
        "missing_available_time_manifest",
        "missing_source_hash_revision_manifest",
        "missing_reviewer_attestation_manifest",
        "missing_quality_review_manifest",
        "missing_limitation_manifest",
        "missing_forbidden_downstream_flags",
    ]:
        result = _validate(case_id)
        assert result["health_status"] == "FAIL"
        assert result["blocker_count"] >= 1
        assert "missing_section" in result["blocker_categories"] or result["status"].endswith("FORBIDDEN_DOWNSTREAM")
        assert result["pass_candidate"] is False


def test_available_time_missing_blocks() -> None:
    result = _validate("missing_available_time_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME"
    assert "available_time" in result["blocker_categories"]


def test_available_time_after_decision_blocks() -> None:
    result = _validate("available_time_after_replay_decision_time_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME"
    assert result["health_status"] == "FAIL"


def test_conflicting_available_time_blocks() -> None:
    result = _validate("conflicting_available_time_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME"
    assert "available_time_conflict" in result["blocker_categories"]


def test_document_publish_time_without_source_evidence_blocks() -> None:
    result = _validate("document_publish_time_without_source_evidence_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME"
    assert "source_evidence_missing" in result["blocker_categories"]


def test_missing_source_hash_blocks() -> None:
    result = _validate("missing_source_hash_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "source_hash" in result["blocker_categories"]


def test_missing_local_file_hash_blocks() -> None:
    result = _validate("missing_local_file_hash_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
    assert "local_file_hash" in result["blocker_categories"]


def test_missing_revision_id_blocks() -> None:
    result = _validate("missing_revision_id_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION"
    assert "revision_id" in result["blocker_categories"]


def test_filename_as_revision_id_blocks() -> None:
    result = _validate("filename_as_revision_id_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION"
    assert "filename_as_revision_id" in result["blocker_categories"]


def test_revision_conflict_blocks() -> None:
    result = _validate("revision_conflict_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION"
    assert "revision_conflict" in result["blocker_categories"]


def test_changed_local_hash_requires_new_package_version() -> None:
    result = _validate("changed_local_file_hash_requires_new_package_version")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION"
    assert "new_package_version_required" in result["blocker_categories"]


def test_missing_reviewer_authority_blocks() -> None:
    result = _validate("missing_reviewer_authority_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY"
    assert "reviewer_authority" in result["blocker_categories"]


def test_reviewer_approval_does_not_override_timing_failure() -> None:
    result = _validate("reviewer_approval_cannot_override_timing_failure")

    assert "reviewer_non_override" in result["blocker_categories"]
    assert "does not override" in result["why_report_only"]


def test_reviewer_approval_does_not_override_source_hash_failure() -> None:
    result = _validate("reviewer_approval_cannot_override_source_hash_failure")

    assert "reviewer_non_override" in result["blocker_categories"]
    assert "source_hash" in result["blocker_categories"]


def test_reviewer_approval_does_not_override_revision_conflict() -> None:
    result = _validate("reviewer_approval_cannot_override_revision_conflict")

    assert "reviewer_non_override" in result["blocker_categories"]
    assert "revision_conflict" in result["blocker_categories"]


def test_reviewer_approval_does_not_override_quality_failed() -> None:
    result = _validate("reviewer_approval_cannot_override_quality_failed")

    assert "reviewer_non_override" in result["blocker_categories"]
    assert "quality" in result["blocker_categories"]


def test_quality_failed_blocks() -> None:
    result = _validate("quality_failed_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
    assert result["health_status"] == "FAIL"


def test_warning_without_limitation_blocks() -> None:
    result = _validate("warning_without_limitation_note_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
    assert "limitation_missing" in result["blocker_categories"]


def test_blocker_count_positive_blocks_pass_candidate() -> None:
    result = _validate("blocker_count_positive_blocks_pass_candidate")

    assert result["blocker_count"] > 0
    assert result["pass_candidate"] is False


def test_warning_count_positive_allows_needs_review_only() -> None:
    result = _validate("warning_count_positive_allows_needs_review_only")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW"
    assert result["health_status"] == "WARN"
    assert result["warning_count"] > 0
    assert result["blocker_count"] == 0
    assert result["pass_candidate"] is False


def test_forbidden_downstream_flag_true_blocks() -> None:
    result = _validate("forbidden_downstream_flag_true_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert "forbidden_downstream" in result["blocker_categories"]
    for flag in SAFETY_FALSE_FLAGS:
        assert result[flag] is False


def test_future_label_leakage_blocks() -> None:
    result = _validate("future_label_leakage_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert "future_label_leakage" in result["blocker_categories"]


def test_protected_data_write_claim_blocks() -> None:
    result = _validate("protected_data_write_claim_blocks")

    assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert "protected_write" in result["blocker_categories"]
    assert result["data_raw_written"] is False
    assert result["data_processed_written"] is False
    assert result["data_cache_written"] is False


def test_unsafe_ready_wording_blocks() -> None:
    for case_id in [
        "unsafe_status_wording_ready_for_replay_blocks",
        "unsafe_status_wording_active_replay_input_ready_blocks",
    ]:
        result = _validate(case_id)
        assert result["status"] == "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
        assert "unsafe_wording" in result["blocker_categories"]


def test_real_csv_path_argument_rejected_by_public_api() -> None:
    for function in [
        default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases,
        real_reviewed_local_csv_package_candidate_preflight_statuses,
        real_reviewed_local_csv_package_candidate_preflight_safety_flags,
        validate_real_reviewed_local_csv_package_candidate_preflight_contract_case,
        build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
        write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
    ]:
        parameters = inspect.signature(function).parameters
        assert not any("csv" in name.lower() for name in parameters)
        assert not any("package_path" in name.lower() for name in parameters)
        assert not any("real" in name.lower() and "path" in name.lower() for name in parameters)


def test_output_root_guard_rejects_data_raw_processed_cache(tmp_path: Path) -> None:
    for unsafe in [
        tmp_path / "data" / "raw",
        tmp_path / "data" / "processed",
        tmp_path / "data" / "cache",
    ]:
        with pytest.raises(ValueError):
            build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(output_root=unsafe)


def test_output_root_guard_rejects_docs_project_sources(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
            output_root=tmp_path / "docs" / "project_sources"
        )


def test_output_root_guard_rejects_secret_auth_token_credential_paths(tmp_path: Path) -> None:
    for unsafe_part in [".env", "secrets", "auth", "token", "credential"]:
        with pytest.raises(ValueError):
            build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
                output_root=tmp_path / unsafe_part / "out"
            )


def test_artifacts_write_only_under_manual_diagnostics_or_tmp_path(tmp_path: Path) -> None:
    result = build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
        output_root=_output_root(tmp_path)
    )
    write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(result)

    assert result.artifact_path.is_relative_to(_output_root(tmp_path))
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == set(ARTIFACT_FILENAMES.values())


def test_no_docs_project_sources_created(tmp_path: Path) -> None:
    result = build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
        output_root=_output_root(tmp_path)
    )
    write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(result)

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not Path("docs/project_sources").exists()


def test_artifact_file_set_is_exact(tmp_path: Path) -> None:
    result = build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
        output_root=_output_root(tmp_path)
    )
    write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(result)

    assert set(result.artifact_paths) == {
        "artifact_dir",
        "metadata",
        "report",
        "package_candidate_manifest_contract",
        "package_section_contract",
        "field_family_contract",
        "available_time_preflight_case_matrix",
        "source_hash_revision_preflight_case_matrix",
        "reviewer_authority_preflight_case_matrix",
        "quality_limitation_preflight_case_matrix",
        "safe_status_vocabulary",
        "forbidden_downstream_flags",
        "limitations",
    }
    assert {path.name for path in result.artifact_paths["artifact_dir"].iterdir()} == set(ARTIFACT_FILENAMES.values())


def test_metadata_aggregate_health_pass_despite_expected_negative_cases(tmp_path: Path) -> None:
    result = build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
        output_root=_output_root(tmp_path)
    )
    write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(result)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.workflow_stage == TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY
    assert result.status == REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    assert result.health_status == "PASS"
    assert result.fail_count > 0
    assert metadata["health_status"] == "PASS"
    assert metadata["status"] == REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY
    for flag in SAFETY_FALSE_FLAGS:
        assert metadata[flag] is False


def test_public_api_has_no_real_csv_or_package_path_argument() -> None:
    for function in [
        default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases,
        real_reviewed_local_csv_package_candidate_preflight_statuses,
        real_reviewed_local_csv_package_candidate_preflight_safety_flags,
        validate_real_reviewed_local_csv_package_candidate_preflight_contract_case,
        build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
        write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts,
    ]:
        parameters = inspect.signature(function).parameters
        assert not any("csv" in name.lower() for name in parameters)
        assert not any("package_path" in name.lower() for name in parameters)
        assert not any("real" in name.lower() and "path" in name.lower() for name in parameters)


def test_field_family_contract_records_required_groups() -> None:
    families = {row["field_family"] for row in FIELD_FAMILY_CONTRACT}

    assert families == {
        "package_identity",
        "package_section_presence",
        "source_registry_snapshot",
        "raw_document_dataset_reference",
        "reviewed_file_manifest",
        "table_schema_manifest",
        "row_lineage",
        "available_time",
        "source_hash_local_file_hash_revision_id",
        "reviewer_authority",
        "quality",
        "limitations",
        "forbidden_downstream_flags",
        "output_root_guard_fields",
    }
