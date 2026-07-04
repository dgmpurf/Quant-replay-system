from __future__ import annotations

import csv
import json
from pathlib import Path
from shutil import rmtree

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_preflight as core,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_health import (
    check_real_reviewed_local_csv_package_candidate_preflight_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_index import (
    build_real_reviewed_local_csv_package_candidate_preflight_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_preflight_status import (
    run_real_reviewed_local_csv_package_candidate_preflight_status,
)


NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Research-Status "
    "Planning Report-Only v0.1"
)
FULL_HASH_SENTINEL = "0123456789abcdef" * 4
REVIEWER_SENTINEL = "private-reviewer-identity-should-not-appear"
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/source.csv"
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SHOULD_NOT_APPEAR"
TARGET_CSV_SENTINEL = "TARGET_CSV_SHOULD_NOT_APPEAR"
HEADER_VALUE_SENTINEL = "HEADER_VALUE_SHOULD_NOT_APPEAR"
ROW_VALUE_SENTINEL = "ROW_VALUE_SHOULD_NOT_APPEAR"
FORBIDDEN_WORDING = [
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
]
NEGATIVE_FALSE_FIELDS = [
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "target_csv_opened",
    "source_artifact_opened",
    "source_content_read",
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


def test_index_discovers_no_input_artifact_and_exposes_safe_fields(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=root,
        run_id="001_no_input",
    )

    result = build_real_reviewed_local_csv_package_candidate_preflight_index(
        root=root,
        output_dir=root / "index",
    )

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "001_no_input"
    assert row["runtime_status"] == core.STATUS_NO_INPUT
    assert row["health_status"] == "PASS"
    assert row["preflight_id"] == ""
    assert row["declared_package_id"] == ""
    assert row["preflight_level"] == core.PREFLIGHT_NONE
    assert row["package_creation_level"] == core.PACKAGE_CREATION_NONE
    assert row["csv_read_level"] == core.CSV_READ_NONE
    assert row["evidence_reference_count"] == 0
    assert row["real_package_candidate_created"] is False
    _assert_negative_fields_false(row)


def test_index_discovers_metadata_context_and_exposes_counts_capabilities_and_presence(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_complete_preflight(tmp_path, root, "002_metadata_context")

    result = build_real_reviewed_local_csv_package_candidate_preflight_index(
        root=root,
        output_dir=root / "index",
    )

    row = result.rows[0]
    assert row["runtime_status"] == core.STATUS_METADATA_CONTEXT_REPORT_ONLY
    assert row["health_status"] == "PASS"
    assert row["preflight_id"] == "preflight-001"
    assert row["declared_package_id"] == "declared-package-001"
    assert row["real_package_candidate_created"] is False
    assert row["preflight_level"] == core.PREFLIGHT_METADATA_REFERENCES_ONLY
    assert row["package_creation_level"] == core.PACKAGE_CREATION_NONE
    assert row["csv_read_level"] == core.CSV_READ_NONE
    assert row["source_hash_validation_level"] == core.SOURCE_HASH_VALIDATION_NONE
    assert row["revision_id_validation_level"] == core.REVISION_ID_VALIDATION_NONE
    assert row["available_time_validation_level"] == core.AVAILABLE_TIME_VALIDATION_NONE
    assert row["pit_admissibility_level"] == core.PIT_ADMISSIBILITY_NONE
    assert row["reviewer_authority_level"] == core.REVIEWER_AUTHORITY_NONE
    assert row["quality_status_level"] == core.QUALITY_STATUS_NONE
    assert row["permission_review_level"] == core.PERMISSION_REVIEW_NONE
    assert row["active_input_level"] == core.ACTIVE_INPUT_NONE
    assert row["replay_readiness_level"] == core.REPLAY_READINESS_NONE
    assert row["evidence_reference_count"] == 6
    assert row["required_reference_count"] == 6
    assert row["required_reference_present_count"] == 6
    assert row["missing_required_reference_count"] == 0
    assert row["missing_optional_reference_count"] == 0
    for reference_name in REQUIRED_REFERENCE_NAMES:
        assert row[f"{reference_name}_present"] is True
    _assert_negative_fields_false(row)


def test_index_artifacts_do_not_expose_sensitive_or_csv_sentinels(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_complete_preflight(
        tmp_path,
        root,
        "003_sensitive",
        metadata_overrides={
            "source_revision_time_metadata": {
                "source_hash_preview": FULL_HASH_SENTINEL[:12],
                "full_source_hash": FULL_HASH_SENTINEL,
                "private_path": PRIVATE_PATH_SENTINEL,
                "source_content_sample": SOURCE_CONTENT_SENTINEL,
            },
            "reviewer_quality_limitation_metadata": {
                "reviewer_id_preview": REVIEWER_SENTINEL[:12],
                "reviewer_id": REVIEWER_SENTINEL,
            },
            "csv_structural_header_metadata": {
                "target_csv_sample": TARGET_CSV_SENTINEL,
                "header_value_sample": HEADER_VALUE_SENTINEL,
            },
            "csv_physical_data_line_count_metadata": {
                "row_value_sample": ROW_VALUE_SENTINEL,
            },
        },
    )

    result = build_real_reviewed_local_csv_package_candidate_preflight_index(
        root=root,
        output_dir=root / "index",
    )
    text = _artifact_text(result.artifact_paths.values())

    _assert_no_sensitive_sentinels(text)
    _assert_no_positive_forbidden_wording(text)


def test_health_pass_warn_and_blocked_core_artifacts(tmp_path: Path) -> None:
    pass_root = _output_root(tmp_path / "pass")
    core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=pass_root,
        run_id="001_no_input",
    )
    _run_complete_preflight(tmp_path / "pass", pass_root, "002_pass")

    pass_health = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=pass_root,
        output_dir=pass_root / "health",
    )
    assert pass_health.status == "PASS"
    assert pass_health.checked_artifact_count == 2
    assert pass_health.error_count == 0

    optional_root = _output_root(tmp_path / "optional")
    _run_complete_preflight(
        tmp_path / "optional",
        optional_root,
        "003_missing_optional",
        optional_missing=True,
    )
    optional_health = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=optional_root,
        output_dir=optional_root / "health",
    )
    assert optional_health.status == "WARN"
    assert "MISSING_OPTIONAL_EVIDENCE" in {row["issue_code"] for row in optional_health.rows}

    required_root = _output_root(tmp_path / "required")
    _run_complete_preflight(
        tmp_path / "required",
        required_root,
        "004_missing_required",
        missing_required="source_revision_time_metadata",
    )
    required_health = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=required_root,
        output_dir=required_root / "health",
    )
    assert required_health.status == "FAIL"
    assert "MISSING_REQUIRED_EVIDENCE" in {row["issue_code"] for row in required_health.rows}


def test_health_warn_for_core_unvalidated_future_capability_warnings(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    artifact = _run_complete_preflight(tmp_path, root, "future_warning")
    _mutate_metadata(
        artifact,
        {
            "runtime_status": core.STATUS_WARN_UNVALIDATED_SOURCE_HASH,
            "health_status": "WARN",
            "warning_count": 1,
        },
    )

    result = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "WARN"
    assert "UNVALIDATED_FUTURE_CAPABILITY_WARNING" in {row["issue_code"] for row in result.rows}


def test_health_warn_for_expected_hash_reference_warning(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_complete_preflight(
        tmp_path,
        root,
        "expected_hash_warn",
        metadata_overrides={
            "expected_hash_verification_metadata": {
                "runtime_status": "EXPECTED_HASH_VERIFICATION_WARN_HASH_MISMATCH",
                "health_status": "WARN",
                "warning_count": 1,
            }
        },
    )

    result = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "WARN"
    assert "EXPECTED_HASH_REFERENCE_WARN" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_unsafe_claims_downstream_review_quality_and_permission(tmp_path: Path) -> None:
    cases = [
        (
            "unsafe_validation",
            {"source_revision_time_metadata": {"source_hash_validated": True}},
            None,
            "UNSUPPORTED_VALIDATION_CLAIM",
        ),
        (
            "forbidden_downstream",
            {},
            lambda manifest: manifest["forbidden_downstream_flags"].update({"active_replay_input": True}),
            "FORBIDDEN_DOWNSTREAM",
        ),
        (
            "reviewer_block",
            {
                "reviewer_quality_limitation_metadata": {
                    "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION",
                    "health_status": "FAIL",
                    "limitation_severity_max": "BLOCKER",
                }
            },
            None,
            "REVIEWER_QUALITY_BLOCKER",
        ),
        (
            "permission_block",
            {
                "reviewer_quality_limitation_metadata": {
                    "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION",
                    "health_status": "FAIL",
                    "permission_class": "restricted",
                }
            },
            None,
            "FORBIDDEN_PERMISSION",
        ),
    ]
    for run_id, overrides, mutation, expected_code in cases:
        root = _output_root(tmp_path / run_id)
        _run_complete_preflight(
            tmp_path / run_id,
            root,
            run_id,
            metadata_overrides=overrides,
            manifest_mutation=mutation,
        )

        result = check_real_reviewed_local_csv_package_candidate_preflight_health(
            root=root,
            output_dir=root / "health",
        )

        assert result.status == "FAIL", run_id
        assert expected_code in {row["issue_code"] for row in result.rows}


def test_health_fails_for_package_active_buy_trading_and_data_write_flags(tmp_path: Path) -> None:
    unsafe_fields = [
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]
    for field in unsafe_fields:
        root = _output_root(tmp_path / field)
        artifact = _run_complete_preflight(tmp_path / field, root, field)
        _mutate_metadata(artifact, {field: True})

        result = check_real_reviewed_local_csv_package_candidate_preflight_health(
            root=root,
            output_dir=root / "health",
        )

        assert result.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_leakage_without_echoing_leaked_values(tmp_path: Path) -> None:
    cases = [
        ("hash_leak", "report", FULL_HASH_SENTINEL, "FULL_HASH_DISCLOSURE_LEAK"),
        ("reviewer_leak", "report", REVIEWER_SENTINEL, "REVIEWER_ID_DISCLOSURE_LEAK"),
        ("private_path_leak", "report", PRIVATE_PATH_SENTINEL, "PRIVATE_PATH_DISCLOSURE_LEAK"),
        ("source_content_leak", "report", SOURCE_CONTENT_SENTINEL, "SOURCE_OR_CSV_CONTENT_LEAK"),
        ("target_csv_leak", "report", TARGET_CSV_SENTINEL, "SOURCE_OR_CSV_CONTENT_LEAK"),
        ("header_leak", "report", HEADER_VALUE_SENTINEL, "SOURCE_OR_CSV_CONTENT_LEAK"),
        ("row_leak", "report", ROW_VALUE_SENTINEL, "SOURCE_OR_CSV_CONTENT_LEAK"),
    ]
    for run_id, artifact_key, leaked_text, expected_code in cases:
        root = _output_root(tmp_path / run_id)
        artifact = _run_complete_preflight(tmp_path / run_id, root, run_id)
        Path(artifact["artifact_paths"][artifact_key]).write_text(leaked_text, encoding="utf-8")

        result = check_real_reviewed_local_csv_package_candidate_preflight_health(
            root=root,
            output_dir=root / "health",
        )
        output_text = _artifact_text(result.artifact_paths.values())

        assert result.status == "FAIL", run_id
        assert expected_code in {row["issue_code"] for row in result.rows}
        assert leaked_text not in output_text


def test_health_fails_for_unsafe_live_status_stage_or_next_task_wording(tmp_path: Path) -> None:
    for field in ["runtime_status", "workflow_stage", "recommended_next_task"]:
        root = _output_root(tmp_path / field)
        artifact = _run_complete_preflight(tmp_path / field, root, field)
        _mutate_metadata(artifact, {field: "ACTIVE_REPLAY_INPUT_READY"})

        result = check_real_reviewed_local_csv_package_candidate_preflight_health(
            root=root,
            output_dir=root / "health",
        )

        assert result.status == "FAIL", field
        assert "FORBIDDEN_LIVE_WORDING" in {row["issue_code"] for row in result.rows}


def test_status_summarizes_latest_artifact_and_points_to_cli_phase(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_complete_preflight(tmp_path, root, "001_first")
    _run_complete_preflight(tmp_path, root, "002_latest")

    result = run_real_reviewed_local_csv_package_candidate_preflight_status(
        root=root,
        output_dir=root / "status",
    )

    assert result.latest_run_id == "002_latest"
    assert result.latest_runtime_status == core.STATUS_METADATA_CONTEXT_REPORT_ONLY
    assert result.latest_health_status == "PASS"
    assert result.latest_preflight_id == "preflight-001"
    assert result.latest_declared_package_id == "declared-package-001"
    assert result.latest_required_reference_present_count == 6
    assert result.latest_missing_required_reference_count == 0
    assert result.latest_real_package_candidate_created is False
    assert result.latest_active_replay_input is False
    assert result.latest_buy_review_allowed is False
    assert result.latest_trading_allowed is False
    assert result.recommended_next_task == NEXT_TASK
    text = _artifact_text(result.artifact_paths.values())
    _assert_no_positive_forbidden_wording(text)
    _assert_no_sensitive_sentinels(text)


def test_views_do_not_reread_prior_metadata_references_after_core_artifact_exists(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    refs_root = tmp_path / "allowed" / "metadata"
    _run_complete_preflight(tmp_path, root, "references_deleted")
    rmtree(refs_root)

    index = build_real_reviewed_local_csv_package_candidate_preflight_index(
        root=root,
        output_dir=root / "index",
    )
    health = check_real_reviewed_local_csv_package_candidate_preflight_health(
        root=root,
        output_dir=root / "health",
    )
    status = run_real_reviewed_local_csv_package_candidate_preflight_status(
        root=root,
        output_dir=root / "status",
    )

    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_run_id == "references_deleted"


def test_view_modules_and_tests_do_not_import_hash_library_and_do_not_create_project_sources() -> None:
    forbidden_import_name = "hash" + "lib"
    view_paths = [
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_index.py"),
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_health.py"),
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_preflight_status.py"),
        Path(__file__),
    ]

    for path in view_paths:
        assert forbidden_import_name not in path.read_text(encoding="utf-8")
    assert not Path("docs/project_sources").exists()


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "preflight_views"


def _run_complete_preflight(
    tmp_path: Path,
    root: Path,
    run_id: str,
    *,
    metadata_overrides: dict[str, dict[str, object]] | None = None,
    manifest_mutation=None,
    missing_required: str | None = None,
    optional_missing: bool = False,
) -> dict[str, object]:
    manifest_path, refs = _write_manifest_and_references(
        tmp_path,
        metadata_overrides=metadata_overrides,
        manifest_mutation=manifest_mutation,
        missing_required=missing_required,
    )
    if missing_required:
        refs.pop(f"{missing_required}_path", None)
    if optional_missing:
        refs["metadata_reference_following_metadata_path"] = (
            tmp_path / "allowed" / "metadata" / "missing_optional.json"
        )
    return core.run_real_reviewed_local_csv_package_candidate_preflight(
        output_root=root,
        run_id=run_id,
        preflight_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        allow_real_reviewed_local_csv_package_candidate_preflight=True,
        **refs,
    )


def _write_manifest_and_references(
    tmp_path: Path,
    *,
    metadata_overrides: dict[str, dict[str, object]] | None = None,
    manifest_mutation=None,
    missing_required: str | None = None,
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
        if reference_name != missing_required:
            entries.append(_reference_entry(reference_name, path))
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


def _reference_entry(reference_name: str, path: Path) -> dict[str, object]:
    return {
        "reference_name": reference_name,
        "reference_type": reference_name,
        "path": str(path),
        "required": True,
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


def _mutate_metadata(artifact: dict[str, object], updates: dict[str, object]) -> None:
    metadata_path = Path(artifact["artifact_paths"]["metadata"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(updates)
    _write_json(metadata_path, metadata)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact_text(paths) -> str:
    return "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in paths
        if Path(path).exists() and Path(path).suffix in {".json", ".md", ".csv"}
    )


def _assert_negative_fields_false(row: dict[str, object]) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert row[field] is False, field


def _assert_no_sensitive_sentinels(text: str) -> None:
    for sentinel in [
        FULL_HASH_SENTINEL,
        REVIEWER_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        HEADER_VALUE_SENTINEL,
        ROW_VALUE_SENTINEL,
    ]:
        assert sentinel not in text


def _assert_no_positive_forbidden_wording(text: str) -> None:
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in text
