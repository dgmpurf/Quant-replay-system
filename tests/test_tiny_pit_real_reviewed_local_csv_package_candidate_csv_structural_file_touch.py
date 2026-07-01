from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch import (
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL,
    STATUS_HEADER_ONLY_REPORT_ONLY,
    STATUS_NO_INPUT,
    csv_structural_file_touch_statuses,
    run_csv_structural_file_touch,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only "
    "Post-v1.75 Next Boundary Design Planning Report-Only v0.1"
)
COMPLETED_PHASE_NEXT_ACTIONS = [
    "Artifact Views Report-Only v0.1",
    "CLI Report-Only v0.1",
    "Research-Status Planning Report-Only v0.1",
]
UNSAFE_NEXT_ACTION_PHRASES = [
    "row-count implementation",
    "file-hash implementation",
    "full-content reading",
    "real package candidate",
    "PIT validator",
    "active replay",
    "replay implementation",
    "labels",
    "training",
    "model",
    "stock_profile",
    "paper validation",
    "buy-review",
    "trading",
]
FORBIDDEN_WORDING = [
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "PERFORMANCE_VALIDATED",
]


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "csv_structural_file_touch"


def _write_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "symbol,signal_date,review_note\n"
        "000001,2024-04-02,SENTINEL_SECRET_ROW_VALUE_DO_NOT_RECORD\n",
        encoding="utf-8",
        newline="",
    )
    return path


def _manifest(root: Path, csv_path: Path | str, **overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "package_id": "tiny-pit-real-reviewed-local-csv-structural-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-07-01T00:00:00Z",
        "prepared_by": "synthetic-reviewer",
        "report_only": True,
        "diagnostic_only": True,
        "requested_file_touch_level": "CSV_STRUCTURAL_HEADER_ONLY",
        "requested_csv_read_level": "CSV_HEADER_ONLY",
        "requested_local_file_hash_level": "LOCAL_FILE_HASH_NONE",
        "csv_file_references": [
            {
                "reference_type": "reviewed_local_csv_file_ref",
                "reference_name": "reviewed-local-csv-fixture",
                "path": str(csv_path),
                "required": True,
                "intended_touch_level": "CSV_HEADER_ONLY",
                "declared_only": False,
                "notes": "synthetic tmp_path CSV structural fixture",
            }
        ],
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
        "limitations": ["Header-only structural read; no CSV values consumed."],
    }
    manifest.update(overrides)
    return manifest


def _write_manifest(path: Path, manifest: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run_header_only(tmp_path: Path, manifest: dict[str, object] | None = None):
    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(
        tmp_path / "allowed" / "manifest.json",
        manifest or _manifest(tmp_path / "allowed", csv_path),
    )
    return run_csv_structural_file_touch(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        local_file_hash_level="LOCAL_FILE_HASH_NONE",
        allow_csv_header_only=True,
    )


def _artifact_text(result: dict[str, object]) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in result["artifact_paths"].values()
        if Path(path).is_file()
    )


def test_no_input_writes_safe_artifact_set(tmp_path: Path) -> None:
    result = run_csv_structural_file_touch(output_root=_output_root(tmp_path))

    assert result["runtime_status"] == STATUS_NO_INPUT
    assert result["health_status"] == "PASS"
    assert result["file_touch_level"] == "FILE_TOUCH_NONE"
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["local_file_hash_level"] == "LOCAL_FILE_HASH_NONE"
    assert result["csv_file_opened_structurally"] is False
    assert result["csv_header_read"] is False
    assert result["csv_header_column_count"] == 0
    assert result["csv_row_count_computed"] is False
    assert result["csv_row_count"] == ""
    assert result["csv_values_read"] is False
    assert result["csv_full_content_read"] is False
    assert result["local_file_byte_hash_computed"] is False
    assert result["real_csv_consumed"] is False
    assert all(result[flag] is False for flag in REQUIRED_FALSE_FLAGS)
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    for completed in COMPLETED_PHASE_NEXT_ACTIONS:
        assert completed not in result["recommended_next_task"]
    for unsafe in UNSAFE_NEXT_ACTION_PHRASES:
        assert unsafe not in result["recommended_next_task"]
    for path in result["artifact_paths"].values():
        assert Path(path).is_file()


def test_header_only_reads_header_names_and_count_but_not_rows(tmp_path: Path) -> None:
    result = _run_header_only(tmp_path)

    assert result["runtime_status"] == STATUS_HEADER_ONLY_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["file_touch_level"] == "CSV_STRUCTURAL_HEADER_ONLY"
    assert result["csv_read_level"] == "CSV_HEADER_ONLY"
    assert result["local_file_hash_level"] == "LOCAL_FILE_HASH_NONE"
    assert result["csv_file_opened_structurally"] is True
    assert result["csv_header_read"] is True
    assert result["csv_header_column_count"] == 3
    assert result["csv_header_columns"] == ["symbol", "signal_date", "review_note"]
    assert result["csv_row_count_computed"] is False
    assert result["csv_row_count"] == ""
    assert result["csv_values_read"] is False
    assert result["csv_full_content_read"] is False
    assert result["local_file_byte_hash_computed"] is False
    assert result["local_file_byte_hash_algorithm"] == ""
    assert result["real_csv_consumed"] is False
    assert all(result[flag] is False for flag in REQUIRED_FALSE_FLAGS)
    assert result["recommended_next_task"] == EXPECTED_NEXT_TASK
    for completed in COMPLETED_PHASE_NEXT_ACTIONS:
        assert completed not in result["recommended_next_task"]
    for unsafe in UNSAFE_NEXT_ACTION_PHRASES:
        assert unsafe not in result["recommended_next_task"]
    assert "SENTINEL_SECRET_ROW_VALUE_DO_NOT_RECORD" not in _artifact_text(result)


def test_missing_allow_flag_blocks_header_touch(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(tmp_path / "allowed", csv_path))

    result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG
    assert result["csv_header_read"] is False
    assert result["real_csv_consumed"] is False


@pytest.mark.parametrize(
    ("file_touch_level", "csv_read_level", "local_file_hash_level"),
    [
        ("CSV_STRUCTURAL_ROW_COUNT_ONLY", "CSV_ROW_COUNT_ONLY", "LOCAL_FILE_HASH_NONE"),
        ("LOCAL_FILE_BYTE_HASH_ONLY", "CSV_READ_NONE", "LOCAL_FILE_BYTE_HASH_ONLY"),
        ("CSV_STRUCTURAL_AND_BYTE_HASH_ONLY", "CSV_HEADER_ONLY", "LOCAL_FILE_BYTE_HASH_ONLY"),
    ],
)
def test_unsupported_row_count_and_hash_levels_block(
    tmp_path: Path, file_touch_level: str, csv_read_level: str, local_file_hash_level: str
) -> None:
    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(tmp_path / "allowed", csv_path))

    result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=file_touch_level,
        csv_read_level=csv_read_level,
        local_file_hash_level=local_file_hash_level,
        allow_csv_header_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_UNSUPPORTED_TOUCH_LEVEL
    assert result["csv_row_count_computed"] is False
    assert result["local_file_byte_hash_computed"] is False


def test_public_api_excludes_direct_csv_package_root_and_replay_args() -> None:
    parameters = inspect.signature(run_csv_structural_file_touch).parameters

    for forbidden in [
        "csv_path",
        "direct_csv_path",
        "package_root",
        "reviewed_csv_path",
        "data_target_path",
        "replay_input_path",
        "active_input_path",
    ]:
        assert forbidden not in parameters
    assert "package_manifest_path" in parameters
    assert "allowed_manifest_roots" in parameters


@pytest.mark.parametrize(
    "bad_path",
    [
        "https://example.invalid/reviewed.csv",
        "../reviewed.csv",
        "data/raw/reviewed.csv",
        "data/processed/reviewed.csv",
        "data/cache/reviewed.csv",
        "docs/project_sources/reviewed.csv",
        "secrets/reviewed.csv",
        "auth/reviewed.csv",
        "token/reviewed.csv",
        "credential/reviewed.csv",
        "key/reviewed.csv",
        ".env/reviewed.csv",
        "reviewed.txt",
    ],
)
def test_path_guard_rejects_unsafe_csv_references(tmp_path: Path, bad_path: str) -> None:
    manifest_path = _write_manifest(
        tmp_path / "allowed" / "manifest.json",
        _manifest(tmp_path / "allowed", bad_path),
    )

    result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        allow_csv_header_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["csv_header_read"] is False


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside = _write_csv(tmp_path / "outside" / "reviewed.csv")
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    link = allowed / "linked.csv"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    manifest_path = _write_manifest(allowed / "manifest.json", _manifest(allowed, link))

    result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[allowed],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        allow_csv_header_only=True,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["csv_header_read"] is False


def test_manifest_schema_and_forbidden_downstream_flags_block(tmp_path: Path) -> None:
    missing_required = _manifest(tmp_path / "allowed", "reviewed.csv")
    missing_required.pop("csv_file_references")
    missing_manifest = _write_manifest(tmp_path / "allowed" / "missing.json", missing_required)
    missing_result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path / "missing"),
        package_manifest_path=missing_manifest,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        allow_csv_header_only=True,
    )
    assert missing_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA

    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    unsafe = _manifest(
        tmp_path / "allowed",
        csv_path,
        forbidden_downstream_flags={**{flag: False for flag in REQUIRED_FALSE_FLAGS}, "trading_allowed": True},
    )
    unsafe_manifest = _write_manifest(tmp_path / "allowed" / "unsafe.json", unsafe)
    unsafe_result = run_csv_structural_file_touch(
        output_root=_output_root(tmp_path / "unsafe"),
        package_manifest_path=unsafe_manifest,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        allow_csv_header_only=True,
    )

    assert unsafe_result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert unsafe_result["trading_allowed"] is False


def test_status_vocabulary_and_artifacts_exclude_unsafe_wording(tmp_path: Path) -> None:
    result = _run_header_only(tmp_path)
    status_blob = json.dumps(csv_structural_file_touch_statuses())
    artifact_blob = _artifact_text(result)

    for forbidden in FORBIDDEN_WORDING:
        assert forbidden not in status_blob
        assert forbidden not in artifact_blob
        assert forbidden not in result["runtime_status"]
        assert forbidden not in result["recommended_next_task"]
    for completed in COMPLETED_PHASE_NEXT_ACTIONS:
        assert completed not in result["recommended_next_task"]
    for unsafe in UNSAFE_NEXT_ACTION_PHRASES:
        assert unsafe not in result["recommended_next_task"]
    assert not Path("docs/project_sources").exists()


def test_artifact_writes_stay_under_tmp_output_root(tmp_path: Path) -> None:
    output_root = _output_root(tmp_path)
    result = _run_header_only(tmp_path)

    for path in result["artifact_paths"].values():
        resolved = Path(path).resolve()
        assert output_root.resolve() in [resolved, *resolved.parents]
    assert not (Path("data") / "raw").joinpath("reviewed.csv").exists()
