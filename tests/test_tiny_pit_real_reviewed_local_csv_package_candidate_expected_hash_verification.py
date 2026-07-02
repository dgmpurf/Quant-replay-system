from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system import tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification as expected_hash


EXPECTED_FULL_HASH = "a" * 64
ACTUAL_FULL_HASH = "b" * 64
MATCHING_FULL_HASH = "c" * 64
PREVIEW_CHARS = 16

FORBIDDEN_API_NAMES = {
    "target_csv_path",
    "direct_csv_path",
    "file_path",
    "package_root",
    "reviewed_csv_path",
    "raw_csv_path",
    "recompute_hash",
    "allow_recompute_hash",
    "header_read",
    "allow_header_read",
    "row_count",
    "allow_row_count",
    "full_content",
    "allow_full_content",
    "source_hash_validation",
    "revision_id_validation",
    "available_time_validation",
    "pit_validator",
    "reviewer_authority",
    "active_input",
    "replay",
    "package_candidate",
    "trading",
    "automatic_discovery",
}

UNSAFE_WORDING = {
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

NEGATIVE_FLAG_FIELDS = [
    "expected_hash_verified_against_source_hash",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "source_reliability_scored",
    "reviewer_authority_validated",
    "local_file_byte_hash_recomputed",
    "target_file_opened_for_expected_hash_verification",
    "csv_file_opened_structurally",
    "csv_header_read",
    "csv_row_count_computed",
    "csv_values_read",
    "csv_full_content_read",
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


def test_no_input_writes_safe_artifact_set_without_reading_metadata(tmp_path: Path) -> None:
    missing_metadata = tmp_path / "allowed" / "missing_metadata.json"
    result = expected_hash.run_expected_hash_verification(
        output_root=_output_root(tmp_path),
        run_id="no_input",
        local_file_byte_hash_metadata_path=missing_metadata,
    )

    assert result["runtime_status"] == "NO_EXPECTED_HASH_VERIFICATION_INPUT"
    assert result["health_status"] == "PASS"
    assert result["workflow_stage"] == expected_hash.WORKFLOW_STAGE
    assert result["file_touch_level"] == "FILE_TOUCH_NONE"
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["local_file_hash_level"] == "LOCAL_FILE_HASH_NONE"
    assert result["expected_hash_verification_level"] == "EXPECTED_HASH_VERIFICATION_NONE"
    assert result["expected_hash_verification_performed"] is False
    assert result["expected_hash_present"] is False
    assert result["expected_hash_preview"] == ""
    assert result["actual_local_file_byte_hash_preview"] == ""
    assert result["expected_hash_matched"] is False
    assert result["expected_hash_mismatch"] is False
    assert result["expected_hash_verified_against_local_metadata"] is False
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    assert result["actionable_mismatch"] is False
    _assert_all_negative_flags_false(result)
    _assert_artifact_set(result, "no_input")


def test_missing_allow_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH)

    result = _run(
        tmp_path,
        run_id="missing_allow",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        allow=False,
    )

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_ALLOW_FLAG"
    assert result["health_status"] == "FAIL"
    assert result["expected_hash_verification_performed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda manifest, _metadata: manifest.pop("verification_id"),
        lambda manifest, _metadata: manifest.__setitem__("report_only", False),
        lambda manifest, _metadata: manifest.__setitem__(
            "requested_csv_read_level", "CSV_HEADER_READ_ONLY"
        ),
        lambda manifest, _metadata: manifest.__setitem__(
            "requested_expected_hash_verification_level", "EXPECTED_HASH_VERIFICATION_NONE"
        ),
        lambda manifest, _metadata: manifest.__setitem__(
            "requested_local_file_hash_level", "LOCAL_FILE_HASH_SHA256_ONLY"
        ),
    ],
)
def test_manifest_schema_failure_blocks(tmp_path: Path, mutation) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH, mutation)

    result = _run(tmp_path, run_id="manifest_schema", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_disclosure_policy_failure_blocks_with_disclosure_status(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        EXPECTED_FULL_HASH,
        EXPECTED_FULL_HASH,
        lambda manifest, _metadata: manifest.__setitem__("expected_hash_disclosure_level", "FULL_HASH"),
    )

    result = _run(tmp_path, run_id="disclosure", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_DISCLOSURE_POLICY"
    assert result["health_status"] == "FAIL"


def test_missing_expected_hash_value_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        EXPECTED_FULL_HASH,
        EXPECTED_FULL_HASH,
        lambda manifest, _metadata: manifest.pop("expected_hash_value"),
    )

    result = _run(tmp_path, run_id="missing_hash", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["expected_hash_present"] is False


@pytest.mark.parametrize("bad_hash", ["a" * 63, "a" * 65, "z" * 64, "abcd"])
def test_malformed_or_non_hex_expected_hash_blocks(tmp_path: Path, bad_hash: str) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, bad_hash, EXPECTED_FULL_HASH)

    result = _run(tmp_path, run_id="bad_hash", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


@pytest.mark.parametrize("algorithm", ["MD5", "SHA1", "CRC32", "SHA-1"])
def test_unsupported_algorithm_blocks(tmp_path: Path, algorithm: str) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        EXPECTED_FULL_HASH,
        EXPECTED_FULL_HASH,
        lambda manifest, _metadata: manifest.__setitem__("expected_hash_algorithm", algorithm),
    )

    result = _run(tmp_path, run_id="bad_algorithm", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_UNSUPPORTED_ALGORITHM"
    assert result["health_status"] == "FAIL"


def test_missing_local_byte_hash_metadata_path_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH)

    result = expected_hash.run_expected_hash_verification(
        output_root=_output_root(tmp_path),
        run_id="missing_metadata_arg",
        expected_hash_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        verification_level="EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        allow_expected_hash_verification=True,
    )

    assert metadata_path.is_file()
    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA"
    assert result["health_status"] == "FAIL"


def test_manifest_metadata_path_and_api_metadata_path_mismatch_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH)
    other_metadata = tmp_path / "allowed" / "other_metadata.json"
    other_metadata.write_text(_json_text(_valid_local_metadata(EXPECTED_FULL_HASH)), encoding="utf-8")

    result = _run(tmp_path, run_id="metadata_mismatch", manifest_path=manifest_path, metadata_path=other_metadata)

    assert metadata_path != other_metadata
    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_missing_local_byte_hash_metadata_file_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH)
    metadata_path.unlink()

    result = _run(tmp_path, run_id="missing_metadata_file", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_LOCAL_HASH_METADATA"
    assert result["health_status"] == "FAIL"


@pytest.mark.parametrize(
    "field",
    [
        "local_file_byte_hash_computed",
        "csv_header_read",
        "csv_row_count_computed",
        "csv_values_read",
        "csv_full_content_read",
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
    ],
)
def test_unsafe_local_byte_hash_metadata_flags_block(tmp_path: Path, field: str) -> None:
    def mutate(_manifest: dict, metadata: dict) -> None:
        metadata[field] = False if field == "local_file_byte_hash_computed" else True

    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH, mutate)

    result = _run(tmp_path, run_id=f"unsafe_{field}", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA"
    assert result["health_status"] == "FAIL"
    assert result["expected_hash_verification_performed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda _manifest, metadata: metadata.__setitem__("local_file_byte_hash_algorithm", "MD5"),
        lambda _manifest, metadata: metadata.__setitem__("local_file_byte_hash_value", ""),
        lambda _manifest, metadata: metadata.__setitem__("local_file_byte_hash_value", "g" * 64),
        lambda _manifest, metadata: metadata.__setitem__("csv_read_level", "CSV_HEADER_READ_ONLY"),
    ],
)
def test_unsafe_local_byte_hash_metadata_shape_blocks(tmp_path: Path, mutation) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, EXPECTED_FULL_HASH, mutation)

    result = _run(tmp_path, run_id="unsafe_shape", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_UNSAFE_LOCAL_HASH_METADATA"
    assert result["health_status"] == "FAIL"


def test_forbidden_downstream_manifest_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        EXPECTED_FULL_HASH,
        EXPECTED_FULL_HASH,
        lambda manifest, _metadata: manifest["forbidden_downstream_flags"].__setitem__("trading_allowed", True),
    )

    result = _run(tmp_path, run_id="forbidden_downstream", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
    assert result["health_status"] == "FAIL"


def test_path_guard_blocks_protected_and_secret_paths(tmp_path: Path) -> None:
    secret_dir = tmp_path / "allowed" / "secret"
    manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        EXPECTED_FULL_HASH,
        EXPECTED_FULL_HASH,
        manifest_dir=secret_dir,
        metadata_dir=secret_dir,
    )

    result = _run(tmp_path, run_id="secret_path", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_BLOCKED_BY_PATH_GUARD"
    assert result["health_status"] == "FAIL"


def test_matched_expected_hash_produces_pass_preview_only_artifacts(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, MATCHING_FULL_HASH.upper(), MATCHING_FULL_HASH)

    result = _run(tmp_path, run_id="matched", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["expected_hash_verification_performed"] is True
    assert result["expected_hash_matched"] is True
    assert result["expected_hash_mismatch"] is False
    assert result["expected_hash_verified_against_local_metadata"] is True
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    assert result["actionable_mismatch"] is False
    assert result["expected_hash_preview"] == MATCHING_FULL_HASH[:PREVIEW_CHARS]
    assert result["actual_local_file_byte_hash_preview"] == MATCHING_FULL_HASH[:PREVIEW_CHARS]
    _assert_all_negative_flags_false(result)
    _assert_artifacts_preview_only(result, MATCHING_FULL_HASH, MATCHING_FULL_HASH)


def test_mismatched_expected_hash_produces_warn_actionable_mismatch(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = _run(tmp_path, run_id="mismatched", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY"
    assert result["health_status"] == "WARN"
    assert result["expected_hash_verification_performed"] is True
    assert result["expected_hash_matched"] is False
    assert result["expected_hash_mismatch"] is True
    assert result["issue_count"] == 1
    assert result["warning_count"] == 1
    assert result["actionable_mismatch"] is True
    _assert_artifacts_preview_only(result, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)


def test_source_target_csv_can_be_absent_for_metadata_only_verification(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    target_csv = tmp_path / "allowed" / "reviewed.csv"
    assert not target_csv.exists()

    result = _run(tmp_path, run_id="no_csv", manifest_path=manifest_path, metadata_path=metadata_path)

    assert result["runtime_status"] == "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"
    assert result["target_file_opened_for_expected_hash_verification"] is False
    assert result["real_csv_consumed"] is False


def test_module_does_not_import_hashlib_or_byte_csv_reading_dependencies() -> None:
    source = Path(expected_hash.__file__).read_text(encoding="utf-8")

    assert "hashlib" not in source
    assert "read_bytes" not in source
    assert "pandas" not in source
    assert "import csv" not in source


def test_public_api_signature_has_no_direct_csv_or_downstream_arguments() -> None:
    parameters = set(inspect.signature(expected_hash.run_expected_hash_verification).parameters)

    assert FORBIDDEN_API_NAMES.isdisjoint(parameters)
    assert {
        "output_root",
        "run_id",
        "expected_hash_manifest_path",
        "local_file_byte_hash_metadata_path",
        "allowed_manifest_roots",
        "verification_level",
        "allow_expected_hash_verification",
        "max_manifest_size_bytes",
    }.issubset(parameters)


def test_artifacts_never_contain_full_hashes_and_contain_only_previews(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = _run(tmp_path, run_id="preview_only", manifest_path=manifest_path, metadata_path=metadata_path)

    _assert_artifacts_preview_only(result, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)
    assert result["expected_hash_preview"] == EXPECTED_FULL_HASH[:PREVIEW_CHARS]
    assert result["actual_local_file_byte_hash_preview"] == ACTUAL_FULL_HASH[:PREVIEW_CHARS]
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["target_file_opened_for_expected_hash_verification"] is False
    assert result["local_file_byte_hash_recomputed"] is False


def test_unsafe_wording_does_not_appear_positively(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    result = _run(tmp_path, run_id="wording", manifest_path=manifest_path, metadata_path=metadata_path)
    text = _artifact_text(result)
    status_text = " ".join(
        [
            result["runtime_status"],
            result["workflow_stage"],
            result["recommended_next_task"],
            text,
        ]
    )

    for wording in UNSAFE_WORDING:
        assert wording not in status_text


def test_docs_project_sources_is_not_created_and_artifacts_stay_under_tmp_output_root(tmp_path: Path) -> None:
    manifest_path, metadata_path = _write_valid_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    root = _output_root(tmp_path)

    result = _run(tmp_path, run_id="path_scope", manifest_path=manifest_path, metadata_path=metadata_path)

    assert not Path("docs/project_sources").exists()
    for path in result["artifact_paths"].values():
        assert Path(path).resolve().is_relative_to(root.resolve())
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _run(
    tmp_path: Path,
    *,
    run_id: str,
    manifest_path: Path,
    metadata_path: Path,
    allow: bool = True,
) -> dict:
    return expected_hash.run_expected_hash_verification(
        output_root=_output_root(tmp_path),
        run_id=run_id,
        expected_hash_manifest_path=manifest_path,
        local_file_byte_hash_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        verification_level="EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        allow_expected_hash_verification=allow,
    )


def _write_valid_inputs(
    tmp_path: Path,
    expected_full_hash: str,
    actual_full_hash: str,
    mutation=None,
    *,
    manifest_dir: Path | None = None,
    metadata_dir: Path | None = None,
) -> tuple[Path, Path]:
    manifest_dir = manifest_dir or tmp_path / "allowed" / "manifest"
    metadata_dir = metadata_dir or tmp_path / "allowed" / "byte_hash_artifact"
    metadata_path = metadata_dir / "metadata.json"
    manifest_path = manifest_dir / "expected_hash_manifest.json"
    metadata = _valid_local_metadata(actual_full_hash)
    manifest = _valid_manifest(expected_full_hash, metadata_path)
    if mutation is not None:
        mutation(manifest, metadata)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(_json_text(metadata), encoding="utf-8")
    manifest_path.write_text(_json_text(manifest), encoding="utf-8")
    return manifest_path, metadata_path


def _valid_manifest(expected_full_hash: str, metadata_path: Path) -> dict:
    return {
        "verification_id": "verify_fixture",
        "package_id": "package_fixture",
        "package_schema_version": "tiny-pit-expected-hash-v0.1",
        "created_at": "2026-07-02T00:00:00Z",
        "prepared_by": "pytest",
        "report_only": True,
        "diagnostic_only": True,
        "requested_expected_hash_verification_level": "EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        "requested_csv_read_level": "CSV_READ_NONE",
        "requested_local_file_hash_level": "LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY",
        "source_local_file_byte_hash_artifact_metadata_path": str(metadata_path),
        "expected_hash_algorithm": "SHA-256",
        "expected_hash_value": expected_full_hash,
        "expected_hash_disclosure_level": "PREVIEW_ONLY_STATUS",
        "forbidden_downstream_flags": {field: False for field in expected_hash.REQUIRED_FALSE_FLAGS},
        "limitations": ["Synthetic expected-hash verification fixture."],
    }


def _valid_local_metadata(actual_full_hash: str) -> dict:
    metadata = {
        "local_file_byte_hash_computed": True,
        "local_file_byte_hash_algorithm": "SHA-256",
        "local_file_byte_hash_value": actual_full_hash,
        "csv_read_level": "CSV_READ_NONE",
        "csv_header_read": False,
        "csv_row_count_computed": False,
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
    }
    metadata.update({field: False for field in expected_hash.REQUIRED_FALSE_FLAGS})
    return metadata


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "expected_hash_verification"


def _artifact_set(result: dict) -> list[Path]:
    return [Path(path) for path in result["artifact_paths"].values()]


def _assert_artifact_set(result: dict, run_id: str) -> None:
    for path in _artifact_set(result):
        assert path.is_file()
        assert run_id in str(path)


def _assert_artifacts_preview_only(result: dict, expected_full_hash: str, actual_full_hash: str) -> None:
    text = _artifact_text(result)
    assert expected_full_hash.lower() not in text.lower()
    assert actual_full_hash.lower() not in text.lower()
    assert expected_full_hash[:PREVIEW_CHARS].lower() in text.lower()
    assert actual_full_hash[:PREVIEW_CHARS].lower() in text.lower()


def _artifact_text(result: dict) -> str:
    chunks = []
    for path in _artifact_set(result):
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _assert_all_negative_flags_false(result: dict) -> None:
    for field in NEGATIVE_FLAG_FIELDS:
        assert result[field] is False


def _json_text(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
