from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    CSV_READ_NONE,
    FILE_TOUCH_NONE,
    HASH_PREVIEW_HEX_CHARS,
    LOCAL_FILE_BYTE_HASH_ONLY,
    LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
    LOCAL_FILE_HASH_NONE,
    MAX_HASH_INPUT_BYTES,
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_SIZE_LIMIT,
    STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL,
    STATUS_HASH_ONLY_REPORT_ONLY,
    STATUS_NO_INPUT,
    local_file_byte_hash_only_statuses,
    run_local_file_byte_hash_only,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only "
    "Artifact Views Report-Only v0.1"
)
SENTINEL_ROW_VALUE = "SENTINEL_HASH_ONLY_ROW_VALUE_DO_NOT_RECORD"
FORBIDDEN_WORDING = [
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
]


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "local_file_byte_hash_only"


def _write_csv(path: Path, payload: bytes | None = None) -> tuple[Path, bytes]:
    data = payload if payload is not None else (
        b"symbol,signal_date,review_note\n"
        + b"000001,2024-04-02,"
        + SENTINEL_ROW_VALUE.encode("utf-8")
        + b"\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path, data


def _manifest(csv_path: Path | str, **overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "package_id": "tiny-pit-real-reviewed-local-csv-byte-hash-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-07-01T00:00:00Z",
        "prepared_by": "synthetic-reviewer",
        "report_only": True,
        "diagnostic_only": True,
        "requested_file_touch_level": LOCAL_FILE_BYTE_HASH_ONLY,
        "requested_csv_read_level": CSV_READ_NONE,
        "requested_local_file_hash_level": LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        "local_file_references": [
            {
                "reference_type": "reviewed_local_csv_file_ref",
                "reference_name": "reviewed-local-csv-fixture",
                "path": str(csv_path),
                "required": True,
                "intended_touch_level": LOCAL_FILE_BYTE_HASH_ONLY,
                "declared_only": False,
                "notes": "synthetic tmp_path CSV byte-hash fixture",
            }
        ],
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
        "limitations": ["Byte-hash-only local fixture; no CSV parsing or PIT admissibility."],
    }
    manifest.update(overrides)
    return manifest


def _write_manifest(path: Path, manifest: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run_hash_only(tmp_path: Path, manifest: dict[str, object] | None = None, **kwargs: object):
    csv_path, csv_bytes = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(
        tmp_path / "allowed" / "manifest.json",
        manifest or _manifest(csv_path),
    )
    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
        **kwargs,
    )
    return result, csv_bytes


def _artifact_texts(result: dict[str, object]) -> dict[str, str]:
    return {
        name: Path(path).read_text(encoding="utf-8")
        for name, path in result["artifact_paths"].items()
        if Path(path).is_file()
    }


def _all_artifact_text(result: dict[str, object]) -> str:
    return "\n".join(_artifact_texts(result).values())


def test_no_input_writes_safe_artifact_set_and_no_hash(tmp_path: Path) -> None:
    result = run_local_file_byte_hash_only(output_root=_output_root(tmp_path))

    assert result["runtime_status"] == STATUS_NO_INPUT
    assert result["health_status"] == "PASS"
    assert result["file_touch_level"] == FILE_TOUCH_NONE
    assert result["csv_read_level"] == CSV_READ_NONE
    assert result["local_file_hash_level"] == LOCAL_FILE_HASH_NONE
    assert result["local_file_byte_hash_computed"] is False
    assert result["local_file_byte_hash_algorithm"] == ""
    assert result["local_file_byte_hash_value"] == ""
    assert result["local_file_byte_hash_preview"] == ""
    assert result["local_file_byte_hash_full_recorded_in_metadata"] is False
    assert result["local_file_byte_hash_disclosure_level"] == ""
    assert result["local_file_bytes_read_for_hash"] is False
    assert result["local_file_size_bytes"] == ""
    assert result["local_file_size_limit_bytes"] == MAX_HASH_INPUT_BYTES
    assert result["csv_file_opened_structurally"] is False
    assert result["csv_header_read"] is False
    assert result["csv_header_column_count"] == 0
    assert result["csv_row_count_computed"] is False
    assert result["csv_row_count"] == ""
    assert result["csv_values_read"] is False
    assert result["csv_full_content_read"] is False
    assert result["real_csv_consumed"] is False
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert all(result[flag] is False for flag in REQUIRED_FALSE_FLAGS)
    for path in result["artifact_paths"].values():
        assert Path(path).is_file()


def test_missing_allow_flag_blocks_before_hash_computation(tmp_path: Path) -> None:
    csv_path, _ = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG
    assert result["local_file_byte_hash_computed"] is False
    assert result["local_file_bytes_read_for_hash"] is False


@pytest.mark.parametrize(
    "manifest_override",
    [
        {"package_id": None},
        {"report_only": False},
        {"diagnostic_only": False},
        {"requested_file_touch_level": FILE_TOUCH_NONE},
        {"requested_csv_read_level": "CSV_HEADER_ONLY"},
        {"requested_local_file_hash_level": LOCAL_FILE_HASH_NONE},
        {"local_file_references": []},
        {"limitations": []},
    ],
)
def test_manifest_schema_failure_blocks(tmp_path: Path, manifest_override: dict[str, object]) -> None:
    csv_path, _ = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest = _manifest(csv_path)
    for key, value in manifest_override.items():
        if value is None:
            manifest.pop(key)
        else:
            manifest[key] = value
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", manifest)

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert result["local_file_byte_hash_computed"] is False


@pytest.mark.parametrize(
    "bad_path",
    [
        "https://example.invalid/reviewed.csv",
        "../reviewed.csv",
        "data/raw/reviewed.csv",
        "data/processed/reviewed.csv",
        "data/cache/reviewed.csv",
        "docs/project_sources/reviewed.csv",
        "outputs/reports/manual_diagnostics/reviewed.csv",
        "secrets/reviewed.csv",
        "auth/reviewed.csv",
        "token/reviewed.csv",
        "credential/reviewed.csv",
        "key/reviewed.csv",
        ".env/reviewed.csv",
        "reviewed.txt",
    ],
)
def test_path_guard_rejects_unsafe_references(tmp_path: Path, bad_path: str) -> None:
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(bad_path))

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["local_file_byte_hash_computed"] is False


def test_allowed_root_escape_blocks(tmp_path: Path) -> None:
    csv_path, _ = _write_csv(tmp_path / "outside" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD


def test_empty_and_size_limit_files_block(tmp_path: Path) -> None:
    empty_path, _ = _write_csv(tmp_path / "allowed" / "empty.csv", b"")
    empty_manifest = _write_manifest(tmp_path / "allowed" / "empty_manifest.json", _manifest(empty_path))
    empty_result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path / "empty"),
        package_manifest_path=empty_manifest,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )
    assert empty_result["runtime_status"] == STATUS_BLOCKED_BY_SIZE_LIMIT
    assert empty_result["local_file_byte_hash_computed"] is False

    large_path, _ = _write_csv(tmp_path / "allowed" / "large.csv", b"abcdef")
    large_manifest = _write_manifest(tmp_path / "allowed" / "large_manifest.json", _manifest(large_path))
    large_result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path / "large"),
        package_manifest_path=large_manifest,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
        max_hash_input_bytes=3,
    )
    assert large_result["runtime_status"] == STATUS_BLOCKED_BY_SIZE_LIMIT
    assert large_result["local_file_byte_hash_computed"] is False


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside, _ = _write_csv(tmp_path / "outside" / "reviewed.csv")
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    link = allowed / "linked.csv"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    manifest_path = _write_manifest(allowed / "manifest.json", _manifest(link))

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[allowed],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["local_file_byte_hash_computed"] is False


def test_hash_only_computes_sha256_without_csv_semantics(tmp_path: Path) -> None:
    result, csv_bytes = _run_hash_only(tmp_path)
    expected_hash = hashlib.sha256(csv_bytes).hexdigest()

    assert result["runtime_status"] == STATUS_HASH_ONLY_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["file_touch_level"] == LOCAL_FILE_BYTE_HASH_ONLY
    assert result["csv_read_level"] == CSV_READ_NONE
    assert result["local_file_hash_level"] == LOCAL_FILE_BYTE_HASH_SHA256_ONLY
    assert result["local_file_byte_hash_computed"] is True
    assert result["local_file_byte_hash_algorithm"] == "SHA-256"
    assert result["local_file_byte_hash_value"] == expected_hash
    assert result["local_file_byte_hash_preview"] == expected_hash[:HASH_PREVIEW_HEX_CHARS]
    assert result["local_file_byte_hash_full_recorded_in_metadata"] is True
    assert result["local_file_byte_hash_disclosure_level"] == "FULL_METADATA_PREVIEW_STATUS"
    assert result["local_file_bytes_read_for_hash"] is True
    assert result["local_file_size_bytes"] == len(csv_bytes)
    assert result["local_file_size_limit_bytes"] == MAX_HASH_INPUT_BYTES
    assert result["local_file_byte_hash_verified_against_manifest"] is False
    assert result["local_file_byte_hash_expected_present"] is False
    assert result["csv_file_opened_structurally"] is False
    assert result["csv_header_read"] is False
    assert result["csv_header_column_count"] == 0
    assert result["csv_row_count_computed"] is False
    assert result["csv_row_count"] == ""
    assert result["csv_values_read"] is False
    assert result["csv_full_content_read"] is False
    assert result["real_csv_consumed"] is False
    for field in [
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "source_reliability_scored",
        "reviewer_authority_validated",
    ]:
        assert result[field] is False
    assert all(result[flag] is False for flag in REQUIRED_FALSE_FLAGS)


def test_hash_disclosure_full_hash_only_in_metadata_and_no_row_values(tmp_path: Path) -> None:
    result, csv_bytes = _run_hash_only(tmp_path)
    full_hash = hashlib.sha256(csv_bytes).hexdigest()
    preview = full_hash[:HASH_PREVIEW_HEX_CHARS]
    texts = _artifact_texts(result)

    assert full_hash in texts["metadata"]
    for name, text in texts.items():
        if name == "metadata":
            continue
        assert full_hash not in text
        assert SENTINEL_ROW_VALUE not in text
    assert preview in texts["report"]
    assert preview in texts["summary"]
    assert "upload-safe Project Source" not in _all_artifact_text(result)


def test_forbidden_downstream_flag_true_blocks(tmp_path: Path) -> None:
    csv_path, _ = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    flags = {flag: False for flag in REQUIRED_FALSE_FLAGS}
    flags["trading_allowed"] = True
    manifest_path = _write_manifest(
        tmp_path / "allowed" / "manifest.json",
        _manifest(csv_path, forbidden_downstream_flags=flags),
    )

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert result["trading_allowed"] is False
    assert result["local_file_byte_hash_computed"] is False


def test_unsupported_levels_block(tmp_path: Path) -> None:
    csv_path, _ = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))

    result = run_local_file_byte_hash_only(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level="CSV_HEADER_ONLY",
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_UNSUPPORTED_LEVEL
    assert result["local_file_byte_hash_computed"] is False


def test_public_api_excludes_direct_csv_package_replay_and_content_args() -> None:
    parameters = inspect.signature(run_local_file_byte_hash_only).parameters

    for forbidden in [
        "csv_path",
        "direct_csv_path",
        "file_path",
        "direct_file_path",
        "package_root",
        "reviewed_csv_path",
        "data_target_path",
        "row_count",
        "allow_row_count",
        "allow_header_read",
        "allow_full_content",
        "replay_input_path",
        "active_input_path",
        "source_reliability",
        "reviewer_authority",
        "trading_allowed",
    ]:
        assert forbidden not in parameters
    assert "package_manifest_path" in parameters
    assert "allowed_manifest_roots" in parameters
    assert "allow_local_file_byte_hash_only" in parameters


def test_status_vocabulary_artifacts_and_result_exclude_unsafe_wording(tmp_path: Path) -> None:
    result, _ = _run_hash_only(tmp_path)
    status_blob = json.dumps(local_file_byte_hash_only_statuses())
    artifact_blob = _all_artifact_text(result)

    for forbidden in FORBIDDEN_WORDING:
        assert forbidden not in status_blob
        assert forbidden not in artifact_blob
        assert forbidden not in result["runtime_status"]
        assert forbidden not in result["workflow_stage"]
        assert forbidden not in result["recommended_next_task"]
    assert not Path("docs/project_sources").exists()


def test_artifact_writes_stay_under_tmp_output_root(tmp_path: Path) -> None:
    output_root = _output_root(tmp_path)
    result, _ = _run_hash_only(tmp_path)

    for path in result["artifact_paths"].values():
        resolved = Path(path).resolve()
        assert output_root.resolve() in [resolved, *resolved.parents]
    assert not (Path("data") / "raw").joinpath("reviewed.csv").exists()
