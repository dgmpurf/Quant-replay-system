from __future__ import annotations

import inspect
import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation as core,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation Checkpoint Planning Report-Only v0.1"
)
WORKFLOW_STAGE = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_REVIEWER_AUTHORITY_"
    "QUALITY_LIMITATION_CORE_CREATED_REPORT_ONLY"
)
FULL_REVIEWER_ID = "private-reviewer-identity-000001"
REVIEWER_ID_PREVIEW = FULL_REVIEWER_ID[:12]
LONG_LIMITATION_TEXT = "sensitive limitation detail " * 20
FORBIDDEN_WORDING = {
    "REVIEWER_APPROVED_PACKAGE",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "PERFORMANCE_VALIDATED",
}
FORBIDDEN_API_NAMES = {
    "direct_csv_path",
    "target_csv_path",
    "source_artifact_path",
    "source_bytes_path",
    "source_content_path",
    "package_root",
    "reviewer_authority_validation",
    "source_reliability_score",
    "quality_to_package_promotion",
    "limitation_override",
    "source_hash_recompute",
    "available_time_pit_gate",
    "real_package_candidate",
    "active_input",
    "replay",
    "trading",
    "automatic_discovery",
}
NEGATIVE_FALSE_FIELDS = [
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "real_csv_consumed",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "trading_allowed",
    "buy_review_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]


def test_no_input_safe_artifact_set_and_does_not_read_reviewer_metadata(tmp_path: Path) -> None:
    missing_metadata = tmp_path / "allowed" / "missing_reviewer_quality_metadata.json"

    result = core.run_reviewer_authority_quality_limitation(
        output_root=_output_root(tmp_path),
        run_id="no_input",
        reviewer_quality_metadata_path=missing_metadata,
    )

    assert result["runtime_status"] == "NO_REVIEWER_QUALITY_LIMITATION_INPUT"
    assert result["health_status"] == "PASS"
    assert result["workflow_stage"] == WORKFLOW_STAGE
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["reviewer_authority_level"] == "REVIEWER_AUTHORITY_NONE"
    assert result["quality_status_level"] == "QUALITY_STATUS_NONE"
    assert result["limitation_review_level"] == "LIMITATION_REVIEW_NONE"
    assert result["permission_review_level"] == "PERMISSION_REVIEW_NONE"
    assert result["package_promotion_level"] == "PACKAGE_PROMOTION_NONE"
    assert result["reviewer_metadata_present"] is False
    assert result["reviewer_id_recorded"] is False
    assert result["reviewer_id_preview"] == ""
    assert result["reviewer_role_supported"] is False
    assert result["quality_status_present"] is False
    assert result["limitations_present"] is False
    assert result["permission_class_present"] is False
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    _assert_negative_fields_false(result)
    _assert_artifacts_exist(result, "no_input")


def test_missing_allow_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(
        tmp_path,
        run_id="missing_allow",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        allow=False,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_ALLOW_FLAG"
    assert result["health_status"] == "FAIL"
    assert result["reviewer_metadata_present"] is False


def test_malformed_manifest_blocks(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    manifest_path = allowed / "manifest.json"
    metadata_path = allowed / "metadata.json"
    manifest_path.write_text("{malformed", encoding="utf-8")
    _write_json(metadata_path, _reviewer_quality_metadata())

    result = _run_metadata(
        tmp_path,
        run_id="malformed_manifest",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_missing_required_manifest_field_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        manifest_mutation=lambda manifest: manifest.pop("reviewer_policy"),
    )

    result = _run_metadata(
        tmp_path,
        run_id="missing_manifest_field",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert "reviewer_policy" in result["issues"][0]


def test_path_guard_blocks_url_traversal_and_protected_paths(tmp_path: Path) -> None:
    _, metadata_path = _write_valid_inputs(tmp_path)

    url_result = _run_metadata(
        tmp_path,
        run_id="url",
        manifest_path="https://example.invalid/manifest.json",
        metadata_path=metadata_path,
    )
    traversal_result = _run_metadata(
        tmp_path,
        run_id="traversal",
        manifest_path=tmp_path / "allowed" / ".." / "manifest.json",
        metadata_path=metadata_path,
    )
    protected_result = _run_metadata(
        tmp_path,
        run_id="protected",
        manifest_path=Path("data/raw/manifest.json"),
        metadata_path=metadata_path,
    )

    for result in [url_result, traversal_result, protected_result]:
        assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_PATH_GUARD"
        assert result["health_status"] == "FAIL"


def test_metadata_present_pass_sets_context_fields_and_no_validation_flags(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(
        tmp_path,
        run_id="metadata_pass",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["reviewer_authority_level"] == "REVIEWER_METADATA_PRESENT_ONLY"
    assert result["quality_status_level"] == "QUALITY_METADATA_PRESENT_ONLY"
    assert result["limitation_review_level"] == "LIMITATION_METADATA_PRESENT_ONLY"
    assert result["permission_review_level"] == "PERMISSION_CLASS_METADATA_PRESENT_ONLY"
    assert result["package_promotion_level"] == "PACKAGE_PROMOTION_NONE"
    assert result["reviewer_metadata_present"] is True
    assert result["reviewer_id_recorded"] is True
    assert result["reviewer_id_preview"] == REVIEWER_ID_PREVIEW
    assert result["reviewer_role"] == "reviewer"
    assert result["reviewer_role_supported"] is True
    assert result["reviewer_type"] == "human_declared_only"
    assert result["reviewer_attestation_present"] is True
    assert result["reviewer_authority_scope_declared"] is True
    assert result["quality_status_present"] is True
    assert result["quality_status_declared"] is True
    assert result["quality_issue_count"] == 0
    assert result["quality_warning_count"] == 0
    assert result["quality_blocker_count"] == 0
    assert result["limitations_present"] is True
    assert result["limitation_count"] == 1
    assert result["limitation_severity_max"] == "INFO"
    assert result["limitation_categories"] == ["schema_assumption"]
    assert result["permission_class_present"] is True
    assert result["permission_class"] == "public"
    assert result["legality_flag"] == "public_confirmed"
    _assert_negative_fields_false(result)


def test_reviewer_authority_declared_does_not_create_package_readiness(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {
                "reviewer_role": "approver_declared_only",
                "reviewer_authority_scope_declared": True,
            }
        ),
    )

    result = _run_metadata(
        tmp_path,
        run_id="declared_authority",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY"
    assert result["reviewer_authority_scope_declared"] is True
    assert result["reviewer_authority_validated"] is False
    assert result["real_package_candidate_created"] is False
    assert result["active_replay_input"] is False
    assert result["buy_review_allowed"] is False
    assert result["trading_allowed"] is False


def test_missing_reviewer_metadata_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.pop("reviewer_id_recorded"),
    )

    result = _run_metadata(
        tmp_path,
        run_id="missing_reviewer",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_REVIEWER_METADATA"
    assert result["health_status"] == "FAIL"


def test_unsupported_reviewer_role_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__("reviewer_role", "chief_approver"),
    )

    result = _run_metadata(
        tmp_path,
        run_id="bad_role",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE"
    assert result["health_status"] == "FAIL"


def test_missing_quality_status_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.pop("quality_status"),
    )

    result = _run_metadata(
        tmp_path,
        run_id="missing_quality",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_QUALITY_STATUS"
    assert result["health_status"] == "FAIL"


def test_warn_limitation_creates_warn_health_and_status(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {
                "quality_status": "QUALITY_STATUS_WARN_LIMITATIONS",
                "quality_warning_count": 1,
                "limitation_severity_max": "WARN",
                "limitation_categories": ["timezone_assumption"],
                "limitations": ["Timezone assumption requires human review."],
            }
        ),
    )

    result = _run_metadata(
        tmp_path,
        run_id="warn_limitation",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_WARN_LIMITATIONS_PRESENT"
    assert result["health_status"] == "WARN"
    assert result["warning_count"] >= 1


def test_blocker_limitation_creates_fail_block_status(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {
                "quality_status": "QUALITY_STATUS_BLOCKED_BY_LIMITATIONS",
                "quality_blocker_count": 1,
                "limitation_severity_max": "BLOCKER",
                "blocking_limitation_count": 1,
                "limitation_categories": ["missing_available_time"],
                "limitations": ["Missing available time blocks package promotion."],
            }
        ),
    )

    result = _run_metadata(
        tmp_path,
        run_id="blocker_limitation",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION"
    assert result["health_status"] == "FAIL"


def test_reviewer_or_quality_limitation_override_blocks(tmp_path: Path) -> None:
    reviewer_manifest, reviewer_metadata = _write_valid_inputs(
        tmp_path / "reviewer",
        metadata_mutation=lambda metadata: metadata.__setitem__(
            "limitations_overridden_by_reviewer", True
        ),
    )
    quality_manifest, quality_metadata = _write_valid_inputs(
        tmp_path / "quality",
        metadata_mutation=lambda metadata: metadata.__setitem__(
            "limitations_overridden_by_quality", True
        ),
    )

    reviewer_result = _run_metadata(
        tmp_path,
        run_id="reviewer_override",
        manifest_path=reviewer_manifest,
        metadata_path=reviewer_metadata,
        allowed_root=tmp_path / "reviewer" / "allowed",
    )
    quality_result = _run_metadata(
        tmp_path,
        run_id="quality_override",
        manifest_path=quality_manifest,
        metadata_path=quality_metadata,
        allowed_root=tmp_path / "quality" / "allowed",
    )

    for result in [reviewer_result, quality_result]:
        assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION"
        assert result["health_status"] == "FAIL"


def test_forbidden_or_unknown_permission_class_blocks(tmp_path: Path) -> None:
    restricted_manifest, restricted_metadata = _write_valid_inputs(
        tmp_path / "restricted",
        metadata_mutation=lambda metadata: metadata.update(
            {"permission_class": "restricted", "legality_flag": "restricted_use"}
        ),
    )
    unknown_manifest, unknown_metadata = _write_valid_inputs(
        tmp_path / "unknown",
        metadata_mutation=lambda metadata: metadata.update(
            {"permission_class": "unknown", "legality_flag": "unknown"}
        ),
    )

    restricted_result = _run_metadata(
        tmp_path,
        run_id="restricted",
        manifest_path=restricted_manifest,
        metadata_path=restricted_metadata,
        allowed_root=tmp_path / "restricted" / "allowed",
    )
    unknown_result = _run_metadata(
        tmp_path,
        run_id="unknown",
        manifest_path=unknown_manifest,
        metadata_path=unknown_metadata,
        allowed_root=tmp_path / "unknown" / "allowed",
    )

    for result in [restricted_result, unknown_result]:
        assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION"
        assert result["health_status"] == "FAIL"


def test_forbidden_downstream_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata["forbidden_downstream_flags"].__setitem__(
            "buy_review_allowed", True
        ),
    )

    result = _run_metadata(
        tmp_path,
        run_id="forbidden_downstream",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"


def test_unsafe_validation_and_downstream_claims_block(tmp_path: Path) -> None:
    unsafe_fields = [
        "reviewer_authority_validated",
        "source_reliability_scored",
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
    ]

    for field in unsafe_fields:
        manifest_path, metadata_path = _write_valid_inputs(
            tmp_path / field,
            metadata_mutation=lambda metadata, field=field: metadata.__setitem__(field, True),
        )

        result = _run_metadata(
            tmp_path,
            run_id=field,
            manifest_path=manifest_path,
            metadata_path=metadata_path,
            allowed_root=tmp_path / field / "allowed",
        )

        assert result["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
        assert result["health_status"] == "FAIL"


def test_public_artifacts_do_not_leak_full_reviewer_identity_or_long_limitation_text(
    tmp_path: Path,
) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {
                "full_reviewer_id": FULL_REVIEWER_ID,
                "reviewer_attestation_text": "declared local attestation",
                "detailed_limitation_text": LONG_LIMITATION_TEXT,
            }
        ),
    )

    result = _run_metadata(
        tmp_path,
        run_id="disclosure",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["reviewer_id_preview"] == REVIEWER_ID_PREVIEW
    assert len(result["reviewer_id_preview"]) <= core.REVIEWER_ID_PREVIEW_CHARS
    assert _artifact_text(result, "metadata").find(FULL_REVIEWER_ID) == -1
    for artifact in ["report", "summary", "issues", "forbidden_downstream_flags", "limitations"]:
        text = _artifact_text(result, artifact)
        assert FULL_REVIEWER_ID not in text
        assert LONG_LIMITATION_TEXT not in text


def test_status_and_artifacts_do_not_use_forbidden_positive_wording(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(
        tmp_path,
        run_id="wording",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    text = json.dumps(result, sort_keys=True) + "\n" + _artifact_text(result, "report")
    text += "\n" + _artifact_text(result, "summary")
    text += "\n" + _artifact_text(result, "metadata")
    for forbidden in FORBIDDEN_WORDING:
        assert forbidden not in text


def test_module_and_tests_do_not_import_hash_library() -> None:
    module_text = Path(core.__file__).read_text(encoding="utf-8")
    test_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_import_name = "hash" + "lib"

    assert forbidden_import_name not in module_text
    assert forbidden_import_name not in test_text


def test_public_api_signature_has_no_forbidden_arguments() -> None:
    parameters = set(inspect.signature(core.run_reviewer_authority_quality_limitation).parameters)

    assert not (parameters & FORBIDDEN_API_NAMES)


def test_docs_project_sources_not_created() -> None:
    assert not Path("docs/project_sources").exists()


def test_output_root_rejects_protected_paths(tmp_path: Path) -> None:
    for protected in [
        tmp_path / "data" / "raw" / "out",
        tmp_path / "data" / "processed" / "out",
        tmp_path / "data" / "cache" / "out",
        tmp_path / "docs" / "project_sources" / "out",
    ]:
        try:
            core.run_reviewer_authority_quality_limitation(output_root=protected, run_id="blocked")
        except ValueError as exc:
            assert "protected" in str(exc)
        else:  # pragma: no cover
            raise AssertionError(f"protected output root was not rejected: {protected}")


def _run_metadata(
    tmp_path: Path,
    *,
    run_id: str,
    manifest_path: str | Path,
    metadata_path: str | Path,
    allow: bool = True,
    allowed_root: Path | None = None,
) -> dict:
    return core.run_reviewer_authority_quality_limitation(
        output_root=_output_root(tmp_path),
        run_id=run_id,
        reviewer_quality_manifest_path=manifest_path,
        reviewer_quality_metadata_path=metadata_path,
        allowed_manifest_roots=[allowed_root or tmp_path / "allowed"],
        reviewer_authority_level="REVIEWER_METADATA_PRESENT_ONLY",
        quality_status_level="QUALITY_METADATA_PRESENT_ONLY",
        limitation_review_level="LIMITATION_METADATA_PRESENT_ONLY",
        permission_review_level="PERMISSION_CLASS_METADATA_PRESENT_ONLY",
        package_promotion_level="PACKAGE_PROMOTION_NONE",
        allow_reviewer_quality_limitation_metadata=allow,
    )


def _write_valid_inputs(
    tmp_path: Path,
    *,
    manifest_mutation=None,
    metadata_mutation=None,
) -> tuple[Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(parents=True, exist_ok=True)
    metadata_path = allowed / "reviewer_quality_metadata.json"
    manifest_path = allowed / "manifest.json"
    metadata = _reviewer_quality_metadata()
    if metadata_mutation is not None:
        metadata_mutation(metadata)
    manifest = _manifest(metadata_path)
    if manifest_mutation is not None:
        manifest_mutation(manifest)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, manifest)
    return manifest_path, metadata_path


def _manifest(metadata_path: Path) -> dict:
    return {
        "package_id": "pkg-reviewer-quality-fixture",
        "package_schema_version": "reviewer_quality_limitation_v0_1",
        "created_at": "2026-07-03T00:00:00Z",
        "prepared_by": "synthetic-test",
        "report_only": True,
        "diagnostic_only": True,
        "requested_reviewer_authority_level": "REVIEWER_METADATA_PRESENT_ONLY",
        "requested_quality_status_level": "QUALITY_METADATA_PRESENT_ONLY",
        "requested_limitation_review_level": "LIMITATION_METADATA_PRESENT_ONLY",
        "requested_permission_review_level": "PERMISSION_CLASS_METADATA_PRESENT_ONLY",
        "requested_package_promotion_level": "PACKAGE_PROMOTION_NONE",
        "reviewer_quality_metadata_reference": {
            "path": str(metadata_path),
            "required": True,
            "reference_type": "reviewer_quality_limitation_metadata_ref",
            "intended_touch_level": "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_ONLY",
            "declared_only": False,
        },
        "reviewer_policy": "metadata-present-only",
        "quality_policy": "declared-only",
        "limitation_policy": "visible-non-override",
        "permission_policy": "declared-permission-class-only",
        "disclosure_policy": "preview-only",
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Synthetic manifest limitation context."],
    }


def _reviewer_quality_metadata() -> dict:
    return {
        "reviewer_id_recorded": True,
        "reviewer_id_preview": REVIEWER_ID_PREVIEW,
        "reviewer_role": "reviewer",
        "reviewer_type": "human_declared_only",
        "reviewer_attestation_present": True,
        "reviewer_authority_scope_declared": True,
        "reviewer_authority_validated": False,
        "manual_review_status": "declared_context_only",
        "quality_status": "QUALITY_METADATA_PRESENT_ONLY",
        "quality_status_validated": False,
        "quality_issue_count": 0,
        "quality_warning_count": 0,
        "quality_blocker_count": 0,
        "limitations_present": True,
        "limitation_count": 1,
        "limitation_severity_max": "INFO",
        "limitation_categories": ["schema_assumption"],
        "unresolved_limitation_count": 0,
        "blocking_limitation_count": 0,
        "limitation_policy": "visible-non-override",
        "limitations_overridden_by_reviewer": False,
        "limitations_overridden_by_quality": False,
        "assumptions_present": True,
        "assumption_count": 1,
        "permission_class": "public",
        "legality_flag": "public_confirmed",
        "permission_class_validated": False,
        "report_only": True,
        "diagnostic_only": True,
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Synthetic INFO limitation context."],
    }


def _false_flags() -> dict:
    return {field: False for field in NEGATIVE_FALSE_FIELDS}


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "reviewer_quality_limitation"


def _assert_artifacts_exist(result: dict, run_id: str) -> None:
    assert Path(result["artifact_root"]).name == run_id
    for key in [
        "metadata",
        "report",
        "limitations",
        "issues",
        "summary",
        "forbidden_downstream_flags",
    ]:
        assert Path(result["artifact_paths"][key]).is_file()


def _assert_negative_fields_false(result: dict) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert result[field] is False


def _artifact_text(result: dict, key: str) -> str:
    return Path(result["artifact_paths"][key]).read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
