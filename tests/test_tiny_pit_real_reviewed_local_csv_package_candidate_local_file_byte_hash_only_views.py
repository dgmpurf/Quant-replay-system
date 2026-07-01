from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    CSV_READ_NONE,
    HASH_PREVIEW_HEX_CHARS,
    LOCAL_FILE_BYTE_HASH_ONLY,
    LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
    LOCAL_FILE_HASH_NONE,
    REQUIRED_FALSE_FLAGS,
    run_local_file_byte_hash_only,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_health import (
    check_local_file_byte_hash_only_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_index import (
    build_local_file_byte_hash_only_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only_status import (
    run_local_file_byte_hash_only_status,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only "
    "CLI Report-Only v0.1"
)
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


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "byte_hash_only"


def _write_csv(path: Path) -> tuple[Path, bytes]:
    payload = b"symbol,signal_date,review_note\n000001,2024-04-02,SENTINEL_VIEW_VALUE_DO_NOT_RECORD\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path, payload


def _manifest(csv_path: Path) -> dict[str, object]:
    return {
        "package_id": "tiny-pit-real-reviewed-local-csv-byte-hash-views-001",
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
            }
        ],
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
        "limitations": ["Byte-hash-only view fixture; no CSV parsing."],
    }


def _write_manifest(path: Path, manifest: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_no_input(root: Path, run_id: str = "000-no-input") -> dict[str, object]:
    return run_local_file_byte_hash_only(output_root=root, run_id=run_id)


def _build_hash(root: Path, tmp_path: Path, run_id: str = "999-hash") -> tuple[dict[str, object], str, Path]:
    csv_path, payload = _write_csv(tmp_path / "allowed" / f"{run_id}.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / f"{run_id}.json", _manifest(csv_path))
    result = run_local_file_byte_hash_only(
        output_root=root,
        run_id=run_id,
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level=LOCAL_FILE_BYTE_HASH_ONLY,
        csv_read_level=CSV_READ_NONE,
        local_file_hash_level=LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
        allow_local_file_byte_hash_only=True,
    )
    return result, hashlib.sha256(payload).hexdigest(), csv_path


def _all_view_text(result) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.artifact_paths.values()
        if Path(path).is_file()
    )


def _metadata_path(run_result: dict[str, object]) -> Path:
    return Path(run_result["artifact_paths"]["metadata"])


def _mutate_metadata(run_result: dict[str, object], **updates: object) -> None:
    path = _metadata_path(run_result)
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata.update(updates)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_index_discovers_no_input_and_hash_artifacts_without_full_hash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(root)
    hash_result, full_hash, _ = _build_hash(root, tmp_path)
    preview = full_hash[:HASH_PREVIEW_HEX_CHARS]

    index = build_local_file_byte_hash_only_index(root=root, output_dir=root / "index")

    assert index.artifact_count == 2
    assert set(index.index_frame["run_id"]) == {"000-no-input", "999-hash"}
    hash_row = index.index_frame[index.index_frame["run_id"] == "999-hash"].iloc[0].to_dict()
    assert hash_row["file_touch_level"] == LOCAL_FILE_BYTE_HASH_ONLY
    assert hash_row["csv_read_level"] == CSV_READ_NONE
    assert hash_row["local_file_hash_level"] == LOCAL_FILE_BYTE_HASH_SHA256_ONLY
    assert hash_row["local_file_byte_hash_preview"] == preview
    assert hash_row["local_file_byte_hash_disclosure_level"] == "FULL_METADATA_PREVIEW_STATUS"
    assert hash_row["local_file_byte_hash_computed"] is True
    assert hash_row["active_replay_input"] is False
    assert hash_row["trading_allowed"] is False
    assert full_hash not in _all_view_text(index)
    assert full_hash in _metadata_path(hash_result).read_text(encoding="utf-8")


def test_health_passes_safe_no_input_and_hash_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(root)
    _build_hash(root, tmp_path)

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "PASS"
    assert health.checked_artifact_count == 2
    assert health.error_count == 0


@pytest.mark.parametrize(
    "field",
    [
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
        "active_replay_input",
        "active_replay_input_ready_emitted",
        "buy_review_allowed",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ],
)
def test_health_fails_for_unsafe_true_metadata_flags(tmp_path: Path, field: str) -> None:
    root = _root(tmp_path)
    run_result, _, _ = _build_hash(root, tmp_path)
    _mutate_metadata(run_result, **{field: True})

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert health.error_count >= 1


@pytest.mark.parametrize("algorithm", ["MD5", "SHA1", ""])
def test_health_fails_for_unsupported_hash_algorithm_when_computed(tmp_path: Path, algorithm: str) -> None:
    root = _root(tmp_path)
    run_result, _, _ = _build_hash(root, tmp_path)
    _mutate_metadata(run_result, local_file_byte_hash_algorithm=algorithm)

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"


def test_health_fails_when_preview_missing_for_computed_hash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run_result, _, _ = _build_hash(root, tmp_path)
    _mutate_metadata(run_result, local_file_byte_hash_preview="")

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"


def test_health_fails_when_full_hash_leaks_outside_metadata(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run_result, full_hash, _ = _build_hash(root, tmp_path)
    report_path = Path(run_result["artifact_paths"]["report"])
    report_path.write_text(report_path.read_text(encoding="utf-8") + f"\nleaked={full_hash}\n", encoding="utf-8")

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert full_hash not in _all_view_text(health)


def test_health_fails_for_unsafe_wording_without_repeating_phrase_in_output(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run_result, _, _ = _build_hash(root, tmp_path)
    _mutate_metadata(run_result, runtime_status="ACTIVE_REPLAY_INPUT_READY")

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "ACTIVE_REPLAY_INPUT_READY" not in _all_view_text(health)


def test_status_summarizes_latest_hash_artifact_with_preview_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(root, run_id="000-no-input")
    _, full_hash, _ = _build_hash(root, tmp_path, run_id="999-hash")

    status = run_local_file_byte_hash_only_status(root=root, output_dir=root / "status")

    assert status.latest_run_id == "999-hash"
    assert status.latest_runtime_status == "LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY"
    assert status.latest_health_status == "PASS"
    assert status.latest_file_touch_level == LOCAL_FILE_BYTE_HASH_ONLY
    assert status.latest_csv_read_level == CSV_READ_NONE
    assert status.latest_local_file_hash_level == LOCAL_FILE_BYTE_HASH_SHA256_ONLY
    assert status.latest_local_file_byte_hash_preview == full_hash[:HASH_PREVIEW_HEX_CHARS]
    assert status.latest_csv_header_read is False
    assert status.latest_csv_row_count_computed is False
    assert status.latest_csv_values_read is False
    assert status.latest_csv_full_content_read is False
    assert status.latest_real_csv_consumed is False
    assert status.latest_source_hash_validated is False
    assert status.latest_revision_id_validated is False
    assert status.latest_available_time_validated is False
    assert status.latest_pit_admissibility_validated is False
    assert status.latest_active_replay_input is False
    assert status.latest_trading_allowed is False
    assert status.latest_buy_review_allowed is False
    assert status.recommended_next_task == EXPECTED_NEXT_TASK
    status_text = _all_view_text(status)
    assert full_hash not in status_text
    for forbidden in FORBIDDEN_WORDING:
        assert forbidden not in status_text
    for forbidden_next in ["row-count", "full-content", "PIT validator", "active replay", "trading"]:
        assert forbidden_next not in status.recommended_next_task


def test_status_summarizes_no_input_artifact(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(root, run_id="000-no-input")

    status = run_local_file_byte_hash_only_status(root=root, output_dir=root / "status")

    assert status.latest_run_id == "000-no-input"
    assert status.latest_runtime_status == "NO_LOCAL_FILE_BYTE_HASH_INPUT"
    assert status.latest_csv_read_level == CSV_READ_NONE
    assert status.latest_local_file_hash_level == LOCAL_FILE_HASH_NONE
    assert status.latest_local_file_byte_hash_computed is False
    assert status.recommended_next_task == EXPECTED_NEXT_TASK


def test_views_do_not_need_target_csv_after_core_artifact_creation(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(root, run_id="000-no-input")
    _, _, csv_path = _build_hash(root, tmp_path, run_id="999-hash")
    csv_path.unlink()

    index = build_local_file_byte_hash_only_index(root=root, output_dir=root / "index")
    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")
    status = run_local_file_byte_hash_only_status(root=root, output_dir=root / "status")

    assert index.artifact_count == 2
    assert health.status == "PASS"
    assert status.latest_run_id == "999-hash"


def test_missing_required_artifact_fails_health(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run_result, _, _ = _build_hash(root, tmp_path)
    Path(run_result["artifact_paths"]["summary"]).unlink()

    health = check_local_file_byte_hash_only_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"


def test_views_write_only_under_tmp_path_and_docs_project_sources_absent(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_hash(root, tmp_path)

    results = [
        build_local_file_byte_hash_only_index(root=root, output_dir=root / "index"),
        check_local_file_byte_hash_only_health(root=root, output_dir=root / "health"),
        run_local_file_byte_hash_only_status(root=root, output_dir=root / "status"),
    ]

    for result in results:
        for path in result.artifact_paths.values():
            resolved = Path(path).resolve()
            assert root.resolve() in [resolved, *resolved.parents]
    assert not Path("docs/project_sources").exists()
    assert not (Path("data") / "raw").joinpath("reviewed.csv").exists()
