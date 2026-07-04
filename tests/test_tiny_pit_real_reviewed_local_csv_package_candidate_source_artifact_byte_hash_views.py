from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash as core,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_health import (
    check_source_artifact_byte_hash_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_index import (
    build_source_artifact_byte_hash_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_status import (
    run_source_artifact_byte_hash_status,
)


FULL_HASH = "4727a3ec842bd0e9a28dcdd64f298c2e9872b022d10f5a960bfe1d80460a76f8"
MISMATCH_HASH = "b" * 64
SECRET_SENTINEL = "SECRET_SENTINEL_SHOULD_NOT_APPEAR"
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SENTINEL_SHOULD_NOT_APPEAR"
TARGET_CSV_SENTINEL = "TARGET_CSV_SENTINEL_SHOULD_NOT_APPEAR"
CSV_HEADER_SENTINEL = "CSV_HEADER_SENTINEL_SHOULD_NOT_APPEAR"
CSV_ROW_SENTINEL = "CSV_ROW_SENTINEL_SHOULD_NOT_APPEAR"
PRIVATE_PATH = "C:/Users/msjpurf/private/source-artifact.bin"
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash "
    "Research-Status Planning Report-Only v0.1"
)
UNSAFE_WORDING = [
    "SOURCE_RELIABILITY_VALIDATED",
    "SOURCE_HASH_VALIDATED",
    "PIT_ADMISSIBLE_PACKAGE",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]


def test_index_discovers_no_input_artifact_and_exposes_safe_no_input_fields(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    core.run_source_artifact_byte_hash(output_root=root, run_id="001_no_input")

    result = build_source_artifact_byte_hash_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "001_no_input"
    assert row["runtime_status"] == core.STATUS_NO_INPUT
    assert row["health_status"] == "PASS"
    assert row["source_artifact_byte_read_level"] == core.SOURCE_ARTIFACT_BYTE_READ_NONE
    assert row["source_hash_recompute_level"] == core.SOURCE_HASH_RECOMPUTE_NONE
    assert row["source_content_read_level"] == core.SOURCE_CONTENT_READ_NONE
    assert row["csv_read_level"] == core.CSV_READ_NONE
    assert row["source_artifact_opened_for_hash"] is False
    assert row["source_artifact_bytes_streamed_for_hash"] is False
    assert row["source_hash_validated"] is False
    _assert_downstream_false(row)


def test_index_discovers_matched_artifact_and_exposes_preview_identity_context(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    _write_hash_fixture(tmp_path, root, "002_matched", declared_hash=FULL_HASH)
    (tmp_path / "source" / "synthetic-source.bin").unlink()

    result = build_source_artifact_byte_hash_index(root=root, output_dir=root / "index")

    row = result.rows[0]
    assert row["runtime_status"] == core.STATUS_MATCHED
    assert row["health_status"] == "PASS"
    assert row["source_id"] == "source-001"
    assert row["source_artifact_id"] == "artifact-001"
    assert row["source_artifact_name_preview"] == "synthetic source"
    assert row["source_artifact_path_preview"] == "synthetic-source.bin"
    assert row["source_hash_algorithm"] == core.HASH_ALGORITHM
    assert row["source_artifact_file_size_bytes"] == len(b"synthetic source artifact bytes\n")
    assert row["computed_source_hash_preview"] == FULL_HASH[: core.HASH_PREVIEW_LENGTH]
    assert row["declared_source_hash_preview"] == FULL_HASH[: core.HASH_PREVIEW_LENGTH]
    assert row["computed_source_hash_full_recorded_in_metadata"] is True
    assert row["source_artifact_byte_identity_matched"] is True
    assert row["source_artifact_byte_identity_mismatch"] is False
    assert row["source_artifact_byte_identity_actionable_mismatch"] is False
    assert row["source_hash_validated"] is False
    assert row["source_reliability_scored"] is False
    assert row["target_csv_opened"] is False
    assert row["source_content_read"] is False
    assert row["source_content_semantically_read"] is False
    _assert_downstream_false(row)
    public_text = _artifact_text(result.artifact_paths.values())
    assert FULL_HASH not in public_text
    assert PRIVATE_PATH not in public_text
    assert SECRET_SENTINEL not in public_text


def test_health_pass_warn_and_fail_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    core.run_source_artifact_byte_hash(output_root=root, run_id="001_no_input")
    _write_hash_fixture(tmp_path, root, "002_matched", declared_hash=FULL_HASH)
    _write_hash_fixture(tmp_path, root, "003_mismatch", declared_hash=MISMATCH_HASH)
    _write_hash_fixture(tmp_path, root, "004_missing_hash", declared_hash="", compare=False)

    result = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")

    assert result.status == "WARN"
    assert result.checked_artifact_count == 4
    codes = {row["issue_code"] for row in result.rows}
    assert "BYTE_IDENTITY_MISMATCH_ACTIONABLE" in codes
    assert "DECLARED_SOURCE_HASH_MISSING" in codes
    assert result.error_count == 0


def test_health_pass_for_safe_no_input_and_safe_matched_artifacts(tmp_path: Path) -> None:
    no_input_root = tmp_path / "no_input" / "workflow"
    matched_root = tmp_path / "matched" / "workflow"
    core.run_source_artifact_byte_hash(output_root=no_input_root, run_id="001_no_input")
    _write_hash_fixture(tmp_path / "matched", matched_root, "001_matched", declared_hash=FULL_HASH)

    no_input_health = check_source_artifact_byte_hash_health(
        root=no_input_root,
        output_dir=no_input_root / "health",
    )
    matched_health = check_source_artifact_byte_hash_health(
        root=matched_root,
        output_dir=matched_root / "health",
    )

    assert no_input_health.status == "PASS"
    assert matched_health.status == "PASS"


def test_health_fails_for_forbidden_true_metadata_flags(tmp_path: Path) -> None:
    forbidden_fields = [
        "source_content_read",
        "source_content_semantically_read",
        "target_csv_opened",
        "csv_header_read",
        "csv_values_read",
        "csv_full_content_read",
        "source_hash_validated",
        "source_reliability_scored",
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]
    for field in forbidden_fields:
        root = tmp_path / field / "workflow"
        result = _write_hash_fixture(tmp_path / field, root, "unsafe", declared_hash=FULL_HASH)
        _mutate_metadata(result, **{field: True})

        health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")

        assert health.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in health.rows}


def test_health_fails_for_leakage_without_echoing_leaked_values(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    result = _write_hash_fixture(tmp_path, root, "leak", declared_hash=FULL_HASH)
    _write_text(Path(result["artifact_paths"]["report"]), f"{FULL_HASH}\n{PRIVATE_PATH}\n{SECRET_SENTINEL}")

    health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")
    text = _artifact_text(health.artifact_paths.values())

    assert health.status == "FAIL"
    codes = {row["issue_code"] for row in health.rows}
    assert "FULL_HASH_DISCLOSURE_LEAK" in codes
    assert "PRIVATE_OR_SECRET_DISCLOSURE_LEAK" in codes
    assert FULL_HASH not in text
    assert PRIVATE_PATH not in text
    assert SECRET_SENTINEL not in text


def test_health_fails_for_public_hash_and_content_leakage_without_echoing_values(tmp_path: Path) -> None:
    leak_cases = [
        ("full_declared_hash", FULL_HASH, "FULL_HASH_DISCLOSURE_LEAK"),
        ("source_content", SOURCE_CONTENT_SENTINEL, "SOURCE_CONTENT_DISCLOSURE_LEAK"),
        ("target_csv", TARGET_CSV_SENTINEL, "TARGET_CSV_DISCLOSURE_LEAK"),
        ("csv_header", CSV_HEADER_SENTINEL, "TARGET_CSV_DISCLOSURE_LEAK"),
        ("csv_row", CSV_ROW_SENTINEL, "TARGET_CSV_DISCLOSURE_LEAK"),
    ]
    for run_id, leaked_value, expected_code in leak_cases:
        root = tmp_path / run_id / "workflow"
        result = _write_hash_fixture(tmp_path / run_id, root, run_id, declared_hash=FULL_HASH)
        _write_text(Path(result["artifact_paths"]["summary"]), leaked_value)

        health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")
        text = _artifact_text(health.artifact_paths.values())

        assert health.status == "FAIL", run_id
        assert expected_code in {row["issue_code"] for row in health.rows}
        assert leaked_value not in text


def test_health_fails_for_unsafe_live_status_stage_and_next_task_wording(tmp_path: Path) -> None:
    cases = [
        ("runtime_status", "SOURCE_RELIABILITY_VALIDATED"),
        ("workflow_stage", "ACTIVE_REPLAY_INPUT_READY"),
        ("recommended_next_task", "READY_FOR_REPLAY"),
    ]
    for field, unsafe_value in cases:
        root = tmp_path / field / "workflow"
        result = _write_hash_fixture(tmp_path / field, root, "unsafe_wording", declared_hash=FULL_HASH)
        _mutate_metadata(result, **{field: unsafe_value})

        health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")

        assert health.status == "FAIL", field
        assert "FORBIDDEN_LIVE_WORDING" in {row["issue_code"] for row in health.rows}


def test_health_malformed_metadata_schema_is_fail_not_exception(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    result = _write_hash_fixture(tmp_path, root, "malformed", declared_hash=FULL_HASH)
    _write_text(Path(result["artifact_paths"]["metadata"]), "{not-json")

    health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "METADATA_UNREADABLE" in {row["issue_code"] for row in health.rows}


def test_status_summarizes_latest_artifact_and_recommends_cli_next_task(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    _write_hash_fixture(tmp_path, root, "001_mismatch", declared_hash=MISMATCH_HASH)
    _write_hash_fixture(tmp_path, root, "002_matched", declared_hash=FULL_HASH)

    result = run_source_artifact_byte_hash_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "002_matched"
    assert result.latest_runtime_status == core.STATUS_MATCHED
    assert result.latest_health_status == "WARN"
    assert result.summary["latest_source_artifact_byte_identity_matched"] is True
    assert result.summary["latest_computed_source_hash_preview"] == FULL_HASH[: core.HASH_PREVIEW_LENGTH]
    assert result.summary["latest_source_hash_validated"] is False
    assert result.summary["latest_source_reliability_scored"] is False
    assert result.summary["latest_target_csv_opened"] is False
    assert result.summary["latest_csv_read_level"] == core.CSV_READ_NONE
    assert result.recommended_next_task == NEXT_TASK
    text = _artifact_text(result.artifact_paths.values())
    assert FULL_HASH not in text
    assert PRIVATE_PATH not in text
    for phrase in UNSAFE_WORDING:
        assert phrase not in text


def test_status_summarizes_safe_no_input_artifact(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    core.run_source_artifact_byte_hash(output_root=root, run_id="001_no_input")

    result = run_source_artifact_byte_hash_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "001_no_input"
    assert result.latest_runtime_status == core.STATUS_NO_INPUT
    assert result.latest_health_status == "PASS"
    assert result.summary["latest_source_artifact_opened_for_hash"] is False
    assert result.summary["latest_source_hash_validated"] is False
    assert result.recommended_next_task == NEXT_TASK


def test_views_do_not_reopen_source_artifact_after_core_generation(tmp_path: Path) -> None:
    root = tmp_path / "workflow"
    _write_hash_fixture(tmp_path, root, "001_matched", declared_hash=FULL_HASH)
    (tmp_path / "source" / "synthetic-source.bin").unlink()

    index = build_source_artifact_byte_hash_index(root=root, output_dir=root / "index")
    health = check_source_artifact_byte_hash_health(root=root, output_dir=root / "health")
    status = run_source_artifact_byte_hash_status(root=root, output_dir=root / "status")

    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_runtime_status == core.STATUS_MATCHED


def test_views_modules_and_tests_do_not_import_hash_library_or_create_project_sources() -> None:
    module_names = [
        "quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_index",
        "quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_health",
        "quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_status",
        "tests.test_tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_views",
    ]
    for module_name in module_names:
        module = importlib.import_module(module_name)
        module_path = Path(module.__file__)
        with module_path.open("r", encoding="utf-8") as handle:
            text = handle.read()
        assert ("hash" + "lib") not in text
        assert ("sha" + "256") not in text
    assert not Path("docs/project_sources").exists()


def _write_hash_fixture(
    tmp_path: Path,
    root: Path,
    run_id: str,
    *,
    declared_hash: str,
    compare: bool = True,
) -> dict:
    source_root = tmp_path / "source"
    manifest_root = tmp_path / "manifest"
    source_root.mkdir(parents=True, exist_ok=True)
    manifest_root.mkdir(parents=True, exist_ok=True)
    source_artifact = source_root / "synthetic-source.bin"
    _write_bytes(source_artifact, b"synthetic source artifact bytes\n")
    metadata_path = manifest_root / f"{run_id}_metadata.json"
    manifest_path = manifest_root / f"{run_id}_manifest.json"
    _write_json(metadata_path, {"source_hash_value": declared_hash})
    _write_json(
        manifest_path,
        {
            "source_artifact_hash_request_id": f"request-{run_id}",
            "source_id": "source-001",
            "source_artifact_id": "artifact-001",
            "source_artifact_declared_name": "synthetic source",
            "source_artifact_path_ref": str(source_artifact),
            "report_only": True,
            "diagnostic_only": True,
            "requested_source_artifact_byte_read_level": core.SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
            "requested_source_hash_recompute_level": core.SOURCE_HASH_RECOMPUTE_SHA256_ONLY,
            "requested_source_content_read_level": core.SOURCE_CONTENT_READ_NONE,
            "requested_csv_read_level": core.CSV_READ_NONE,
            "requested_local_file_hash_level": core.LOCAL_FILE_HASH_NONE,
            "requested_expected_hash_verification_level": core.EXPECTED_HASH_VERIFICATION_NONE,
            "requested_source_hash_validation_level": core.SOURCE_HASH_VALIDATION_NONE,
            "requested_revision_id_validation_level": core.REVISION_ID_VALIDATION_NONE,
            "requested_available_time_validation_level": core.AVAILABLE_TIME_VALIDATION_NONE,
            "requested_pit_admissibility_level": core.PIT_ADMISSIBILITY_NONE,
            "requested_source_reliability_level": core.SOURCE_RELIABILITY_NONE,
            "requested_reviewer_authority_level": core.REVIEWER_AUTHORITY_NONE,
            "requested_package_creation_level": core.PACKAGE_CREATION_NONE,
            "requested_active_input_level": core.ACTIVE_INPUT_NONE,
            "requested_replay_readiness_level": core.REPLAY_READINESS_NONE,
            "source_hash_algorithm": core.HASH_ALGORITHM,
            "declared_source_hash": declared_hash,
            "source_lineage_metadata_ref": str(metadata_path),
            "revision_id_metadata_ref": "report-only",
            "available_time_metadata_ref": "report-only",
            "compare_to_declared_source_hash": compare,
            "full_hash_recording_policy": core.FULL_HASH_RECORDING_LOCAL_METADATA_ONLY,
            "disclosure_policy": core.DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES,
            "forbidden_downstream_flags": core.source_artifact_byte_hash_safety_flags(),
            "limitations": ["Report-only byte hash fixture."],
        },
    )
    result = core.run_source_artifact_byte_hash(
        output_root=root,
        run_id=run_id,
        source_artifact_hash_manifest_path=manifest_path,
        source_lineage_metadata_path=metadata_path,
        source_artifact_path=source_artifact,
        allowed_manifest_roots=[manifest_root],
        allowed_source_artifact_roots=[source_root],
        allow_source_artifact_byte_hash=True,
        source_artifact_byte_read_level=core.SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
        source_hash_recompute_level=core.SOURCE_HASH_RECOMPUTE_SHA256_ONLY,
        compare_to_declared_source_hash=compare,
    )
    return result


def _mutate_metadata(result: dict, **updates: object) -> None:
    metadata_path = Path(result["artifact_paths"]["metadata"])
    metadata = _read_json(metadata_path)
    metadata.update(updates)
    _write_json(metadata_path, metadata)


def _assert_downstream_false(row: dict) -> None:
    for field in core.REQUIRED_FALSE_FLAGS:
        assert row[field] is False


def _artifact_text(paths) -> str:
    chunks: list[str] = []
    for path in paths:
        path = Path(path)
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                chunks.append(handle.read())
    return "\n".join(chunks)


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(payload)
