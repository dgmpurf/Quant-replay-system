from __future__ import annotations

import inspect
import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time as core,
)


FULL_SOURCE_HASH = "a" * 64
SOURCE_HASH_PREVIEW = "a" * 16
EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Checkpoint Planning Report-Only v0.1"
)
STALE_NEXT_TASKS = {
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Artifact Views Report-Only v0.1",
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time CLI Report-Only v0.1",
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Research-Status Planning Report-Only v0.1",
}
FORBIDDEN_WORDING = {
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
    "package_root",
    "recompute_source_hash",
    "recompute_local_file_hash",
    "reverify_expected_hash",
    "pit_gate",
    "available_time_decision_gate",
    "reviewer_authority",
    "source_reliability",
    "real_package_candidate",
    "active_input",
    "replay",
    "trading",
    "automatic_discovery",
}
NEGATIVE_FALSE_FIELDS = [
    "source_hash_recomputed",
    "source_artifact_opened",
    "source_content_read",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "target_csv_opened",
    "real_csv_consumed",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
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


def test_no_input_safe_artifact_set_without_reading_source_metadata(tmp_path: Path) -> None:
    missing_metadata = tmp_path / "allowed" / "missing_source_metadata.json"

    result = core.run_source_hash_revision_available_time(
        output_root=_output_root(tmp_path),
        run_id="no_input",
        source_lineage_metadata_path=missing_metadata,
    )

    assert result["runtime_status"] == "NO_SOURCE_REVISION_TIME_INPUT"
    assert result["health_status"] == "PASS"
    assert result["workflow_stage"] == core.WORKFLOW_STAGE
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["source_hash_validation_level"] == "SOURCE_HASH_VALIDATION_NONE"
    assert result["revision_id_validation_level"] == "REVISION_ID_VALIDATION_NONE"
    assert result["available_time_validation_level"] == "AVAILABLE_TIME_VALIDATION_NONE"
    assert result["pit_admissibility_level"] == "PIT_ADMISSIBILITY_NONE"
    assert result["source_hash_metadata_present"] is False
    assert result["source_hash_format_checked"] is False
    assert result["source_hash_algorithm_supported"] is False
    assert result["source_hash_preview"] == ""
    assert result["revision_id_metadata_present"] is False
    assert result["revision_id_value_recorded"] is False
    assert result["available_time_metadata_present"] is False
    assert result["available_time_parseable"] is False
    assert result["available_time_timezone_present"] is False
    assert result["available_time_compared_to_decision_time"] is False
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    for stale_next_task in STALE_NEXT_TASKS:
        assert result["recommended_next_task"] != stale_next_task
    _assert_negative_fields_false(result)
    _assert_artifacts_exist(result, "no_input")


def test_missing_allow_flag_blocks_before_metadata_read(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(
        tmp_path,
        run_id="missing_allow",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        allow=False,
    )

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_ALLOW_FLAG"
    assert result["health_status"] == "FAIL"
    assert result["source_hash_metadata_present"] is False
    assert result["source_artifact_opened"] is False


def test_malformed_manifest_blocks(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    manifest_path = allowed / "manifest.json"
    metadata_path = allowed / "source_metadata.json"
    manifest_path.write_text("{malformed", encoding="utf-8")
    _write_json(metadata_path, _source_metadata())

    result = _run_metadata(
        tmp_path,
        run_id="malformed_manifest",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_missing_required_manifest_field_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        manifest_mutation=lambda manifest: manifest.pop("source_hash_policy"),
    )

    result = _run_metadata(
        tmp_path,
        run_id="missing_manifest_field",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_path_guard_blocks_url_traversal_and_protected_paths(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    cases = [
        "https://example.invalid/manifest.json",
        tmp_path / "outside" / "manifest.json",
        tmp_path / "allowed" / "secrets" / "manifest.json",
        Path("docs") / "project_sources" / "manifest.json",
        Path("data") / "raw" / "manifest.json",
    ]

    for index, bad_path in enumerate(cases):
        result = _run_metadata(
            tmp_path,
            run_id=f"path_guard_{index}",
            manifest_path=bad_path,
            metadata_path=metadata_path if index == 0 else manifest_path,
        )
        assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_PATH_GUARD"
        assert result["health_status"] == "FAIL"


def test_unsupported_hash_algorithm_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__("source_hash_algorithm", "MD5"),
    )

    result = _run_metadata(tmp_path, run_id="unsupported_algorithm", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM"
    assert result["health_status"] == "FAIL"


def test_malformed_source_hash_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__("source_hash_value", "z" * 64),
    )

    result = _run_metadata(tmp_path, run_id="bad_source_hash", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_SOURCE_HASH"
    assert result["health_status"] == "FAIL"


def test_missing_source_hash_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.pop("source_hash_value"),
    )

    result = _run_metadata(tmp_path, run_id="missing_hash", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_SOURCE_HASH"
    assert result["health_status"] == "FAIL"


def test_missing_revision_id_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.pop("revision_id"),
    )

    result = _run_metadata(tmp_path, run_id="missing_revision", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_REVISION_ID"
    assert result["health_status"] == "FAIL"


def test_filename_as_revision_and_unsupported_revision_type_block(tmp_path: Path) -> None:
    for run_id, revision_type in [
        ("filename_revision", "filename_as_revision"),
        ("unsupported_revision", "spreadsheet_tab_name"),
    ]:
        manifest_path, metadata_path = _write_valid_inputs(
            tmp_path,
            metadata_mutation=lambda metadata, value=revision_type: metadata.__setitem__(
                "revision_id_type", value
            ),
            suffix=run_id,
        )

        result = _run_metadata(tmp_path, run_id=run_id, manifest_path=manifest_path, metadata_path=metadata_path)

        assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_REVISION_ID"
        assert result["health_status"] == "FAIL"


def test_revision_id_path_like_value_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__(
            "revision_id", "C:/Users/msjpurf/secret/revision.json"
        ),
    )

    result = _run_metadata(tmp_path, run_id="path_revision", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_REVISION_ID"
    assert result["health_status"] == "FAIL"


def test_malformed_available_time_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__("available_time", "not-a-date"),
    )

    result = _run_metadata(tmp_path, run_id="bad_available_time", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_AVAILABLE_TIME"
    assert result["health_status"] == "FAIL"


def test_available_time_without_timezone_warns_not_pass(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {"available_time": "2024-04-02T09:30:00", "available_time_timezone": ""}
        ),
    )

    result = _run_metadata(tmp_path, run_id="timezone_warning", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED"
    assert result["health_status"] == "WARN"
    assert result["available_time_metadata_present"] is True
    assert result["available_time_parseable"] is True
    assert result["available_time_timezone_present"] is False
    assert result["available_time_validated"] is False


def test_metadata_present_pass_sets_only_metadata_present_fields(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(tmp_path, run_id="metadata_present", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["source_hash_validation_level"] == "SOURCE_HASH_METADATA_PRESENT_ONLY"
    assert result["revision_id_validation_level"] == "REVISION_ID_METADATA_PRESENT_ONLY"
    assert result["available_time_validation_level"] == "AVAILABLE_TIME_METADATA_PRESENT_ONLY"
    assert result["pit_admissibility_level"] == "PIT_ADMISSIBILITY_NONE"
    assert result["source_hash_metadata_present"] is True
    assert result["source_hash_format_checked"] is True
    assert result["source_hash_algorithm_supported"] is True
    assert result["source_hash_algorithm"] == "SHA-256"
    assert result["source_hash_preview"] == SOURCE_HASH_PREVIEW
    assert len(result["source_hash_preview"]) == 16
    assert result["revision_id_metadata_present"] is True
    assert result["revision_id_type"] == "provider_revision_id"
    assert result["revision_id_type_supported"] is True
    assert result["revision_id_value_recorded"] is True
    assert result["available_time_metadata_present"] is True
    assert result["available_time_parseable"] is True
    assert result["available_time_timezone_present"] is True
    assert result["available_time_compared_to_decision_time"] is False
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    _assert_negative_fields_false(result)


def test_no_source_artifact_opened_even_when_reference_present(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.__setitem__(
            "source_artifact_reference", str(tmp_path / "allowed" / "missing_source_artifact.pdf")
        ),
    )

    result = _run_metadata(tmp_path, run_id="artifact_ref", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["health_status"] == "PASS"
    assert result["source_artifact_opened"] is False
    assert result["source_content_read"] is False


def test_no_source_hash_recompute_expected_hash_reverify_or_pit_comparison(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(tmp_path, run_id="negative_proof", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["source_hash_recomputed"] is False
    assert result["local_file_hash_recomputed"] is False
    assert result["expected_hash_reverified"] is False
    assert result["available_time_compared_to_decision_time"] is False
    assert result["pit_admissibility_validated"] is False


def test_forbidden_downstream_flag_true_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata["forbidden_downstream_flags"].__setitem__(
            "active_replay_input", True
        ),
    )

    result = _run_metadata(tmp_path, run_id="forbidden_flag", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"
    assert result["active_replay_input"] is False


def test_unsafe_source_metadata_claims_block(tmp_path: Path) -> None:
    for field in ["source_hash_validated", "pit_admissibility_validated", "reviewer_authority_validated"]:
        manifest_path, metadata_path = _write_valid_inputs(
            tmp_path,
            metadata_mutation=lambda metadata, flag=field: metadata.__setitem__(flag, True),
            suffix=field,
        )

        result = _run_metadata(tmp_path, run_id=field, manifest_path=manifest_path, metadata_path=metadata_path)

        assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
        assert result["health_status"] == "FAIL"
        assert result[field] is False


def test_generated_artifacts_do_not_expose_full_source_hash(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(tmp_path, run_id="disclosure", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["source_hash_preview"] == SOURCE_HASH_PREVIEW
    assert result["source_hash_preview"] in _artifact_text(result)
    assert FULL_SOURCE_HASH not in _artifact_text(result)


def test_source_id_and_source_name_secret_like_values_block(tmp_path: Path) -> None:
    for field in ["source_id", "source_name"]:
        manifest_path, metadata_path = _write_valid_inputs(
            tmp_path,
            metadata_mutation=lambda metadata, name=field: metadata.__setitem__(
                name, "secret/token/source"
            ),
            suffix=field,
        )

        result = _run_metadata(tmp_path, run_id=f"bad_{field}", manifest_path=manifest_path, metadata_path=metadata_path)

        assert result["runtime_status"] == "SOURCE_REVISION_TIME_BLOCKED_BY_UNSAFE_REFERENCE_METADATA"
        assert result["health_status"] == "FAIL"


def test_module_does_not_import_hashlib() -> None:
    module_path = Path(core.__file__)
    assert "hashlib" not in module_path.read_text(encoding="utf-8")


def test_public_api_signature_has_no_forbidden_arguments() -> None:
    parameter_names = set(inspect.signature(core.run_source_hash_revision_available_time).parameters)

    assert not (parameter_names & FORBIDDEN_API_NAMES)


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    _run_metadata(tmp_path, run_id="docs_guard", manifest_path=manifest_path, metadata_path=metadata_path)

    assert not Path("docs/project_sources").exists()


def test_artifact_writes_stay_under_tmp_output_root(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    output_root = _output_root(tmp_path)

    result = core.run_source_hash_revision_available_time(
        output_root=output_root,
        run_id="artifact_root",
        source_lineage_manifest_path=manifest_path,
        source_lineage_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        source_hash_validation_level="SOURCE_HASH_METADATA_PRESENT_ONLY",
        revision_id_validation_level="REVISION_ID_METADATA_PRESENT_ONLY",
        available_time_validation_level="AVAILABLE_TIME_METADATA_PRESENT_ONLY",
        allow_source_revision_time_metadata=True,
    )

    for artifact_path in result["artifact_paths"].values():
        assert Path(artifact_path).resolve().is_relative_to(output_root.resolve())


def test_unsafe_wording_does_not_appear_positively_in_outputs(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    result = _run_metadata(tmp_path, run_id="wording", manifest_path=manifest_path, metadata_path=metadata_path)
    output_text = "\n".join(
        [
            result["runtime_status"],
            result["workflow_stage"],
            result["recommended_next_task"],
            _artifact_text(result),
        ]
    )

    for phrase in FORBIDDEN_WORDING:
        assert phrase not in output_text


def test_metadata_present_result_recommends_checkpoint_planning(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    result = _run_metadata(
        tmp_path,
        run_id="checkpoint_next_task",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )

    assert result["runtime_status"] == "SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY"
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    for stale_next_task in STALE_NEXT_TASKS:
        assert result["recommended_next_task"] != stale_next_task


def _run_metadata(
    tmp_path: Path,
    *,
    run_id: str,
    manifest_path: str | Path,
    metadata_path: str | Path,
    allow: bool = True,
) -> dict:
    return core.run_source_hash_revision_available_time(
        output_root=_output_root(tmp_path),
        run_id=run_id,
        source_lineage_manifest_path=manifest_path,
        source_lineage_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        source_hash_validation_level="SOURCE_HASH_METADATA_PRESENT_ONLY",
        revision_id_validation_level="REVISION_ID_METADATA_PRESENT_ONLY",
        available_time_validation_level="AVAILABLE_TIME_METADATA_PRESENT_ONLY",
        pit_admissibility_level="PIT_ADMISSIBILITY_NONE",
        allow_source_revision_time_metadata=allow,
    )


def _write_valid_inputs(
    tmp_path: Path,
    *,
    manifest_mutation=None,
    metadata_mutation=None,
    suffix: str = "valid",
) -> tuple[Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(exist_ok=True)
    metadata_path = allowed / f"source_metadata_{suffix}.json"
    manifest_path = allowed / f"manifest_{suffix}.json"
    metadata = _source_metadata()
    if metadata_mutation:
        metadata_mutation(metadata)
    manifest = _manifest(metadata_path)
    if manifest_mutation:
        manifest_mutation(manifest)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, manifest)
    return manifest_path, metadata_path


def _manifest(metadata_path: Path) -> dict:
    return {
        "package_id": "pkg-source-revision-time",
        "package_schema_version": "source_revision_time_v0_1",
        "created_at": "2026-07-03T00:00:00Z",
        "prepared_by": "codex-test",
        "report_only": True,
        "diagnostic_only": True,
        "requested_source_hash_validation_level": "SOURCE_HASH_METADATA_PRESENT_ONLY",
        "requested_revision_id_validation_level": "REVISION_ID_METADATA_PRESENT_ONLY",
        "requested_available_time_validation_level": "AVAILABLE_TIME_METADATA_PRESENT_ONLY",
        "requested_pit_admissibility_level": "PIT_ADMISSIBILITY_NONE",
        "source_lineage_metadata_reference": {
            "path": str(metadata_path),
            "required": True,
            "reference_type": "source_lineage_metadata_ref",
            "intended_touch_level": "SOURCE_REVISION_TIME_METADATA_PRESENT_ONLY",
            "declared_only": False,
        },
        "source_hash_policy": "SOURCE_HASH_METADATA_PRESENT_ONLY",
        "revision_id_policy": "REVISION_ID_REQUIRED_METADATA_ONLY",
        "available_time_policy": "AVAILABLE_TIME_PARSEABILITY_ONLY",
        "timezone_policy": "TIMEZONE_REQUIRED_FOR_PASS",
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata shape only; no PIT admissibility validation."],
    }


def _source_metadata() -> dict:
    return {
        "source_id": "official_test_source",
        "source_name": "Official Test Source",
        "source_type": "official_public",
        "permission_class": "reviewed_local_metadata_only",
        "source_hash_algorithm": "SHA-256",
        "source_hash_value": FULL_SOURCE_HASH,
        "source_hash_disclosure_level": "PREVIEW_ONLY_STATUS",
        "revision_id": "provider-2024-04-02-v1",
        "revision_id_type": "provider_revision_id",
        "available_time": "2024-04-02T09:30:00+08:00",
        "available_time_timezone": "Asia/Shanghai",
        "available_time_policy": "available_time_metadata_present_only",
        "quality_status": "review_context_only",
        "manual_review_status": "review_context_only",
        "report_only": True,
        "diagnostic_only": True,
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata only."],
    }


def _false_flags() -> dict[str, bool]:
    return {field: False for field in NEGATIVE_FALSE_FIELDS}


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "source_revision_time"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _assert_negative_fields_false(result: dict) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert result[field] is False, field


def _assert_artifacts_exist(result: dict, run_id: str) -> None:
    assert Path(result["artifact_root"]).name == run_id
    for path in result["artifact_paths"].values():
        assert Path(path).is_file()


def _artifact_text(result: dict) -> str:
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in result["artifact_paths"].values())
