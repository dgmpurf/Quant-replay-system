from __future__ import annotations

import csv
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_preflight as core,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Artifact Views "
    "Report-Only v0.1"
)
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CORE_CREATED_REPORT_ONLY"
)
FORBIDDEN_WORDING = {
    "REAL_PACKAGE_CANDIDATE_CREATED",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
}
FORBIDDEN_API_NAMES = {
    "direct_csv_path",
    "target_csv_path",
    "source_artifact_path",
    "source_bytes_path",
    "source_content_path",
    "package_root",
    "source_hash_recompute",
    "local_file_hash_recompute",
    "expected_hash_reverify",
    "available_time_pit_gate",
    "pit_admissibility_validation",
    "reviewer_authority_validation",
    "source_reliability_scoring",
    "quality_to_package_promotion",
    "limitation_override",
    "real_package_candidate_creation",
    "active_input",
    "replay",
    "trading",
}
NEGATIVE_FALSE_FIELDS = [
    "target_csv_opened",
    "source_artifact_opened",
    "source_content_read",
    "csv_header_read_by_preflight",
    "csv_physical_data_line_count_computed_by_preflight",
    "source_hash_recomputed",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "available_time_compared_to_decision_time",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
REQUIRED_REFERENCE_NAMES = [
    "csv_structural_header_metadata",
    "local_file_byte_hash_metadata",
    "expected_hash_verification_metadata",
    "csv_physical_data_line_count_metadata",
    "source_revision_time_metadata",
    "reviewer_quality_limitation_metadata",
]


def test_no_input_safe_artifact_set_and_does_not_read_metadata_paths(tmp_path: Path) -> None:
    result = core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=_output_root(tmp_path),
        run_id="no_input",
        preflight_metadata_path=tmp_path / "missing_preflight_metadata.json",
        csv_structural_header_metadata_path=tmp_path / "missing_header.json",
    )

    assert result["runtime_status"] == core.STATUS_NO_INPUT
    assert result["health_status"] == "PASS"
    assert result["workflow_stage"] == WORKFLOW_STAGE
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["preflight_level"] == core.PREFLIGHT_NONE
    assert result["package_creation_level"] == core.PACKAGE_CREATION_NONE
    assert result["csv_read_level"] == core.CSV_READ_NONE
    assert result["preflight_manifest_read"] is False
    assert result["preflight_metadata_read"] is False
    assert result["references_declared"] is False
    assert result["references_followed_metadata_only"] is False
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert result["evidence_reference_count"] == 0
    _assert_negative_fields_false(result)
    _assert_artifacts_exist(result)
    _assert_no_forbidden_wording(result)


def test_missing_allow_flag_blocks_without_reading_manifest(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)

    result = _run_preflight(tmp_path, manifest_path, refs, allow=False)

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG
    assert result["health_status"] == "FAIL"
    assert result["preflight_manifest_read"] is False
    assert result["references_followed_metadata_only"] is False
    _assert_negative_fields_false(result)


def test_malformed_manifest_and_missing_required_field_block(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    malformed_path = allowed / "malformed_manifest.json"
    malformed_path.write_text("{not-json", encoding="utf-8")

    malformed = _run_preflight(tmp_path, malformed_path, {}, run_id="malformed")

    assert malformed["runtime_status"] == core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert malformed["health_status"] == "FAIL"

    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        manifest_mutation=lambda manifest: manifest.pop("blocker_policy"),
    )

    missing_field = _run_preflight(tmp_path, manifest_path, refs, run_id="missing_field")

    assert missing_field["runtime_status"] == core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert missing_field["health_status"] == "FAIL"
    assert any("blocker_policy" in issue for issue in missing_field["issues"])


def test_path_guard_blocks_url_traversal_and_protected_paths(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)

    url_result = _run_preflight(
        tmp_path,
        "https://example.invalid/preflight.json",
        refs,
        run_id="url",
    )
    traversal_result = _run_preflight(
        tmp_path,
        manifest_path,
        {**refs, "csv_structural_header_metadata_path": tmp_path / ".." / "header.json"},
        run_id="traversal",
    )
    protected_result = _run_preflight(
        tmp_path,
        Path("data/raw/preflight.json"),
        refs,
        run_id="protected",
    )

    for result in [url_result, traversal_result, protected_result]:
        assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD
        assert result["health_status"] == "FAIL"
        _assert_negative_fields_false(result)


def test_strict_metadata_complete_pass_builds_matrix_and_preserves_none_levels(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="strict_pass")

    assert result["runtime_status"] == core.STATUS_METADATA_CONTEXT_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["preflight_level"] == core.PREFLIGHT_METADATA_REFERENCES_ONLY
    assert result["package_creation_level"] == core.PACKAGE_CREATION_NONE
    assert result["csv_read_level"] == core.CSV_READ_NONE
    assert result["declared_package_id"] == "declared-package-001"
    assert result["real_package_candidate_created"] is False
    assert result["required_reference_count"] == 6
    assert result["required_reference_present_count"] == 6
    assert result["missing_required_reference_count"] == 0
    assert result["evidence_reference_matrix_created"] is True
    assert result["source_hash_recompute_not_performed"] is True
    assert result["available_time_pit_gate_not_performed"] is True
    assert result["reviewer_authority_validation_not_performed"] is True
    assert result["package_creation_not_performed"] is True
    assert result["unvalidated_capability_count"] >= 4
    _assert_matrix(result, expected_decision="PASS", expected_rows=6)
    _assert_negative_fields_false(result)
    _assert_no_forbidden_wording(result)


def test_missing_required_evidence_blocks_and_missing_optional_evidence_warns(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        manifest_mutation=lambda manifest: manifest.__setitem__(
            "evidence_references",
            [
                ref
                for ref in manifest["evidence_references"]
                if ref["reference_name"] != "source_revision_time_metadata"
            ],
        ),
    )

    missing_required = _run_preflight(
        tmp_path,
        manifest_path,
        {key: value for key, value in refs.items() if key != "source_revision_time_metadata_path"},
        run_id="missing_required",
    )

    assert missing_required["runtime_status"] == core.STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA
    assert missing_required["health_status"] == "FAIL"
    assert missing_required["missing_required_reference_count"] == 1

    optional_path = tmp_path / "allowed" / "optional" / "missing_optional.json"
    optional_warn = _run_preflight(
        tmp_path,
        manifest_path,
        {**refs, "metadata_reference_following_metadata_path": optional_path},
        run_id="missing_optional",
    )

    assert optional_warn["runtime_status"] == core.STATUS_WARN_MISSING_OPTIONAL_EVIDENCE
    assert optional_warn["health_status"] == "WARN"
    assert optional_warn["missing_optional_reference_count"] == 1
    _assert_negative_fields_false(optional_warn)


def test_expected_hash_warn_can_warn_without_promoting_validation(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "expected_hash_verification_metadata": {
                "runtime_status": "EXPECTED_HASH_VERIFICATION_WARN_HASH_MISMATCH",
                "health_status": "WARN",
                "warning_count": 1,
                "blocker_count": 0,
            }
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="expected_hash_warn")

    assert result["runtime_status"] == core.STATUS_WARN_MISSING_OPTIONAL_EVIDENCE
    assert result["health_status"] == "WARN"
    assert result["warning_count"] >= 1
    assert result["expected_hash_reverified"] is False
    _assert_negative_fields_false(result)


def test_expected_hash_blocker_blocks_without_reverification(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "expected_hash_verification_metadata": {
                "runtime_status": "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_HASH_MISMATCH",
                "health_status": "FAIL",
                "warning_count": 0,
                "blocker_count": 1,
            }
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="expected_hash_block")

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
    assert result["health_status"] == "FAIL"
    assert result["expected_hash_reverified"] is False
    _assert_negative_fields_false(result)


def test_source_and_reviewer_metadata_do_not_become_validations_or_readiness(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="no_validation")

    for field in [
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "reviewer_authority_validated",
        "quality_status_validated",
        "permission_class_validated",
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
    ]:
        assert result[field] is False


def test_manifest_and_api_validation_claims_block_without_performing_validation(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        manifest_mutation=lambda manifest: manifest.__setitem__(
            "requested_available_time_validation_level",
            "AVAILABLE_TIME_VALIDATION_ATTEMPTED",
        ),
    )

    manifest_claim = _run_preflight(tmp_path, manifest_path, refs, run_id="manifest_claim")

    assert manifest_claim["runtime_status"] == core.STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM
    assert manifest_claim["health_status"] == "FAIL"
    assert manifest_claim["available_time_compared_to_decision_time"] is False

    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)

    api_claim = core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=_output_root(tmp_path),
        run_id="api_claim",
        preflight_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        allow_real_reviewed_local_csv_package_candidate_preflight=True,
        source_hash_validation_level="SOURCE_HASH_VALIDATION_ATTEMPTED",
        **refs,
    )

    assert api_claim["runtime_status"] == core.STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM
    assert api_claim["health_status"] == "FAIL"
    assert api_claim["source_hash_recomputed"] is False
    assert api_claim["source_hash_validated"] is False


def test_reviewer_quality_limitation_and_permission_blockers_block(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "reviewer_quality_limitation_metadata": {
                "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION",
                "health_status": "FAIL",
                "limitation_severity_max": "BLOCKER",
                "blocking_limitation_count": 1,
            }
        },
    )

    limitation = _run_preflight(tmp_path, manifest_path, refs, run_id="limitation_block")

    assert limitation["runtime_status"] == core.STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION
    assert limitation["health_status"] == "FAIL"

    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "reviewer_quality_limitation_metadata": {
                "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION",
                "health_status": "FAIL",
                "permission_class": "restricted",
            }
        },
    )

    permission = _run_preflight(tmp_path, manifest_path, refs, run_id="permission_block")

    assert permission["runtime_status"] == core.STATUS_BLOCKED_BY_PERMISSION
    assert permission["health_status"] == "FAIL"


def test_unsafe_validation_claims_and_forbidden_downstream_flags_block(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "source_revision_time_metadata": {"source_hash_validated": True},
        },
    )

    unsafe = _run_preflight(tmp_path, manifest_path, refs, run_id="unsafe_validation")

    assert unsafe["runtime_status"] == core.STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM
    assert unsafe["health_status"] == "FAIL"

    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        manifest_mutation=lambda manifest: manifest["forbidden_downstream_flags"].update(
            {"active_replay_input": True}
        ),
    )

    forbidden = _run_preflight(tmp_path, manifest_path, refs, run_id="forbidden_downstream")

    assert forbidden["runtime_status"] == core.STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert forbidden["health_status"] == "FAIL"


@pytest.mark.parametrize(
    "unsafe_field",
    [
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
    ],
)
def test_unsafe_reference_metadata_claims_block(tmp_path: Path, unsafe_field: str) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "csv_structural_header_metadata": {unsafe_field: True},
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id=f"unsafe_{unsafe_field}")

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
    assert result["health_status"] == "FAIL"


def test_forbidden_status_wording_in_reference_blocks_and_is_sanitized(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "source_revision_time_metadata": {
                "runtime_status": "ACTIVE_REPLAY_INPUT_READY",
                "health_status": "PASS",
            },
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="forbidden_status")

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_UNSAFE_REFERENCE_METADATA
    assert result["health_status"] == "FAIL"
    _assert_no_forbidden_wording(result)
    _assert_negative_fields_false(result)


def test_generated_artifacts_do_not_leak_sensitive_sentinels(tmp_path: Path) -> None:
    full_hash = "0123456789abcdef" * 4
    full_reviewer = "private-reviewer-identity-very-secret"
    private_path = "C:/Users/msjpurf/.env.secret"
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "source_revision_time_metadata": {
                "source_hash_preview": full_hash[:12],
                "full_source_hash": full_hash,
                "private_path": private_path,
            },
            "reviewer_quality_limitation_metadata": {
                "reviewer_id_preview": full_reviewer[:12],
                "reviewer_id": full_reviewer,
                "limitation_note": "safe category only",
            },
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="disclosure")
    artifact_text = _artifact_text(result)

    assert full_hash not in artifact_text
    assert full_reviewer not in artifact_text
    assert private_path not in artifact_text
    assert "source_hash_preview" in artifact_text
    assert "reviewer_id_preview" in artifact_text


def test_source_artifact_and_target_csv_paths_remain_unopened_metadata_only(tmp_path: Path) -> None:
    target_csv_path = tmp_path / "unopened_target.csv"
    source_artifact_path = tmp_path / "unopened_source_artifact.pdf"
    source_content_path = tmp_path / "unopened_source_content.txt"
    manifest_path, refs = _write_valid_manifest_and_references(
        tmp_path,
        metadata_overrides={
            "csv_structural_header_metadata": {
                "target_csv_path": str(target_csv_path),
            },
            "source_revision_time_metadata": {
                "source_artifact_path": str(source_artifact_path),
                "source_content_path": str(source_content_path),
            },
        },
    )

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="metadata_only_paths")

    assert result["runtime_status"] == core.STATUS_METADATA_CONTEXT_REPORT_ONLY
    assert target_csv_path.exists() is False
    assert source_artifact_path.exists() is False
    assert source_content_path.exists() is False
    assert result["target_csv_opened"] is False
    assert result["source_artifact_opened"] is False
    assert result["source_content_read"] is False
    artifact_text = _artifact_text(result)
    assert str(target_csv_path) not in artifact_text
    assert str(source_artifact_path) not in artifact_text
    assert str(source_content_path) not in artifact_text
    _assert_negative_fields_false(result)


def test_module_and_tests_do_not_import_hash_library() -> None:
    forbidden_import_name = "hash" + "lib"
    assert forbidden_import_name not in inspect.getsource(core)
    assert forbidden_import_name not in Path(__file__).read_text(encoding="utf-8")


def test_public_api_signature_excludes_forbidden_arguments() -> None:
    parameters = set(
        inspect.signature(core.run_real_reviewed_local_csv_package_candidate_preflight).parameters
    )

    assert not (parameters & FORBIDDEN_API_NAMES)
    assert {
        "output_root",
        "preflight_manifest_path",
        "allowed_manifest_roots",
        "allow_real_reviewed_local_csv_package_candidate_preflight",
    } <= parameters


def test_docs_project_sources_not_created_and_artifacts_stay_under_tmp_output(tmp_path: Path) -> None:
    manifest_path, refs = _write_valid_manifest_and_references(tmp_path)
    output_root = _output_root(tmp_path)

    result = _run_preflight(tmp_path, manifest_path, refs, run_id="artifact_root")

    assert not Path("docs/project_sources").exists()
    for artifact_path in result["artifact_paths"].values():
        path = Path(artifact_path).resolve()
        assert output_root.resolve() in [path, *path.parents]


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "preflight"


def _write_valid_manifest_and_references(
    tmp_path: Path,
    *,
    manifest_mutation=None,
    metadata_overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[Path, dict[str, Path]]:
    allowed = tmp_path / "allowed"
    metadata_root = allowed / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    overrides = metadata_overrides or {}
    refs: dict[str, Path] = {}
    entries = []
    for reference_name in REQUIRED_REFERENCE_NAMES:
        path = metadata_root / f"{reference_name}.json"
        refs[f"{reference_name}_path"] = path
        _write_json(path, _reference_metadata(reference_name, **overrides.get(reference_name, {})))
        entries.append(_reference_entry(reference_name, path, required=True))

    manifest: dict[str, object] = {
        "preflight_id": "preflight-001",
        "declared_package_id": "declared-package-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-07-04T00:00:00Z",
        "prepared_by": "synthetic-preparer",
        "report_only": True,
        "diagnostic_only": True,
        "requested_preflight_level": core.PREFLIGHT_METADATA_REFERENCES_ONLY,
        "requested_package_creation_level": core.PACKAGE_CREATION_NONE,
        "requested_csv_read_level": core.CSV_READ_NONE,
        "requested_source_hash_validation_level": core.SOURCE_HASH_VALIDATION_NONE,
        "requested_revision_id_validation_level": core.REVISION_ID_VALIDATION_NONE,
        "requested_available_time_validation_level": core.AVAILABLE_TIME_VALIDATION_NONE,
        "requested_pit_admissibility_level": core.PIT_ADMISSIBILITY_NONE,
        "requested_reviewer_authority_level": core.REVIEWER_AUTHORITY_NONE,
        "requested_quality_status_level": core.QUALITY_STATUS_NONE,
        "requested_limitation_review_level": core.LIMITATION_REVIEW_NONE,
        "requested_permission_review_level": core.PERMISSION_REVIEW_NONE,
        "requested_source_reliability_level": core.SOURCE_RELIABILITY_NONE,
        "requested_active_input_level": core.ACTIVE_INPUT_NONE,
        "requested_replay_readiness_level": core.REPLAY_READINESS_NONE,
        "evidence_references": entries,
        "required_evidence_policy": "strict_metadata_complete",
        "warning_policy": {"missing_optional_evidence": "WARN"},
        "blocker_policy": {"missing_required_evidence": "FAIL"},
        "disclosure_policy": {"hashes": "preview_only", "reviewer": "preview_only"},
        "forbidden_downstream_flags": {field: False for field in NEGATIVE_FALSE_FIELDS},
        "limitations": ["preflight is metadata-reference context only"],
    }
    if manifest_mutation:
        manifest_mutation(manifest)
    manifest_path = allowed / "preflight_manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path, refs


def _reference_entry(reference_name: str, path: Path, *, required: bool) -> dict[str, object]:
    return {
        "reference_name": reference_name,
        "reference_type": reference_name,
        "path": str(path),
        "required": required,
        "expected_workflow_area": reference_name,
        "expected_report_only": True,
        "expected_diagnostic_only": True,
        "expected_metadata_only": True,
        "expected_negative_flags": NEGATIVE_FALSE_FIELDS,
        "allow_statuses": ["PASS", "WARN", "METADATA_PRESENT_REPORT_ONLY"],
        "warn_statuses": ["WARN", "EXPECTED_HASH_VERIFICATION_WARN_HASH_MISMATCH"],
        "block_statuses": ["FAIL"],
        "disclosure_level": "preview_only",
    }


def _reference_metadata(reference_name: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "reference_name": reference_name,
        "runtime_status": "METADATA_PRESENT_REPORT_ONLY",
        "health_status": "PASS",
        "workflow_stage": f"{reference_name.upper()}_REPORT_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "metadata_only": True,
        "issue_count": 0,
        "warning_count": 0,
        "blocker_count": 0,
        "source_hash_preview": "abcdef123456",
        "reviewer_id_preview": "reviewer-001",
        "forbidden_downstream_flags": {field: False for field in NEGATIVE_FALSE_FIELDS},
        "limitations": ["synthetic metadata reference"],
    }
    for field in NEGATIVE_FALSE_FIELDS:
        payload[field] = False
    payload.update(overrides)
    return payload


def _run_preflight(
    tmp_path: Path,
    manifest_path: Path | str,
    refs: dict[str, Path],
    *,
    run_id: str = "run",
    allow: bool = True,
) -> dict[str, object]:
    return core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=_output_root(tmp_path),
        run_id=run_id,
        preflight_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        allow_real_reviewed_local_csv_package_candidate_preflight=allow,
        **refs,
    )


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _assert_negative_fields_false(result: dict[str, object]) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert result[field] is False, field


def _assert_artifacts_exist(result: dict[str, object]) -> None:
    for artifact_path in result["artifact_paths"].values():
        assert Path(artifact_path).exists(), artifact_path


def _assert_matrix(result: dict[str, object], *, expected_decision: str, expected_rows: int) -> None:
    matrix_path = Path(result["artifact_paths"]["evidence_reference_matrix"])
    rows = list(csv.DictReader(matrix_path.open(encoding="utf-8", newline="")))
    assert len(rows) == expected_rows
    assert {row["reference_decision"] for row in rows} == {expected_decision}
    assert all(row["reference_path_preview"] for row in rows)
    assert all(row["reference_read_as_json"] == "True" for row in rows)


def _assert_no_forbidden_wording(result: dict[str, object]) -> None:
    live_text = "\n".join(
        str(result.get(field, ""))
        for field in ["runtime_status", "workflow_stage", "recommended_next_task"]
    )
    artifact_text = _artifact_text(result)
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in live_text
        assert phrase not in artifact_text


def _artifact_text(result: dict[str, object]) -> str:
    return "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in result["artifact_paths"].values()
        if Path(path).suffix in {".json", ".md", ".csv"}
    )
