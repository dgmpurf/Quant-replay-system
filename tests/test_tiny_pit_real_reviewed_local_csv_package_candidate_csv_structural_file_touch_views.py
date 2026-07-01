from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch import (
    REQUIRED_FALSE_FLAGS,
    run_csv_structural_file_touch,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_health import (
    check_csv_structural_file_touch_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_index import (
    build_csv_structural_file_touch_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch_status import (
    run_csv_structural_file_touch_status,
)


EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only "
    "CLI Report-Only v0.1"
)
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


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "csv_structural_file_touch"


def _write_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "symbol,signal_date,review_note\n"
        "000001,2024-04-02,SENTINEL_VIEW_TEST_ROW_VALUE_DO_NOT_READ\n",
        encoding="utf-8",
        newline="",
    )
    return path


def _manifest(csv_path: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "package_id": "tiny-pit-real-reviewed-local-csv-views-001",
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
    payload.update(overrides)
    return payload


def _write_manifest(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _create_no_input_and_header_artifacts(tmp_path: Path) -> tuple[dict[str, object], dict[str, object], Path]:
    output_root = _root(tmp_path)
    no_input = run_csv_structural_file_touch(output_root=output_root, run_id="001_no_input")
    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))
    header = run_csv_structural_file_touch(
        output_root=output_root,
        run_id="002_header",
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_HEADER_ONLY",
        local_file_hash_level="LOCAL_FILE_HASH_NONE",
        allow_csv_header_only=True,
    )
    return no_input, header, csv_path


def _mutate_metadata(artifact_dir: Path, **updates: object) -> None:
    metadata_path = artifact_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(updates)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_index_discovers_no_input_and_header_only_artifacts(tmp_path: Path) -> None:
    _create_no_input_and_header_artifacts(tmp_path)

    result = build_csv_structural_file_touch_index(root=_root(tmp_path), output_dir=_root(tmp_path) / "index")

    assert result.artifact_count == 2
    assert result.artifact_paths["index_csv"].is_file()
    rows = result.index_frame.sort_values("run_id").to_dict("records")
    assert rows[0]["run_id"] == "001_no_input"
    assert rows[0]["file_touch_level"] == "FILE_TOUCH_NONE"
    assert rows[0]["csv_read_level"] == "CSV_READ_NONE"
    assert rows[0]["real_csv_consumed"] is False
    assert rows[1]["run_id"] == "002_header"
    assert rows[1]["file_touch_level"] == "CSV_STRUCTURAL_HEADER_ONLY"
    assert rows[1]["csv_read_level"] == "CSV_HEADER_ONLY"
    assert rows[1]["local_file_hash_level"] == "LOCAL_FILE_HASH_NONE"
    assert rows[1]["csv_header_read"] is True
    assert rows[1]["csv_header_column_count"] == 3
    assert rows[1]["csv_row_count_computed"] is False
    assert rows[1]["local_file_byte_hash_computed"] is False
    assert rows[1]["real_csv_consumed"] is False
    assert rows[1]["active_replay_input"] is False
    assert rows[1]["trading_allowed"] is False


def test_health_passes_for_safe_no_input_and_header_only_artifacts(tmp_path: Path) -> None:
    _create_no_input_and_header_artifacts(tmp_path)

    result = check_csv_structural_file_touch_health(root=_root(tmp_path), output_dir=_root(tmp_path) / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.artifact_paths["health_csv"].is_file()


@pytest.mark.parametrize(
    "field",
    [
        "real_csv_consumed",
        "csv_values_read",
        "csv_full_content_read",
        "csv_row_count_computed",
        "local_file_byte_hash_computed",
        "active_replay_input",
        "active_replay_input_ready_emitted",
        "buy_review_allowed",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ],
)
def test_health_fails_for_unsafe_metadata_flags(tmp_path: Path, field: str) -> None:
    _, header, _ = _create_no_input_and_header_artifacts(tmp_path)
    _mutate_metadata(Path(header["artifact_paths"]["metadata"]).parent, **{field: True})

    result = check_csv_structural_file_touch_health(root=_root(tmp_path), output_dir=_root(tmp_path) / "health")

    assert result.status == "FAIL"
    assert result.error_count >= 1
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in set(result.health_frame["issue_code"])


def test_health_fails_for_unsafe_status_wording(tmp_path: Path) -> None:
    _, header, _ = _create_no_input_and_header_artifacts(tmp_path)
    report_path = Path(header["artifact_paths"]["report"])
    report_path.write_text(report_path.read_text(encoding="utf-8") + "\nACTIVE_REPLAY_INPUT_READY\n", encoding="utf-8")

    result = check_csv_structural_file_touch_health(root=_root(tmp_path), output_dir=_root(tmp_path) / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_STATUS_WORDING" in set(result.health_frame["issue_code"])


def test_status_summarizes_latest_context_and_safe_next_task(tmp_path: Path) -> None:
    _create_no_input_and_header_artifacts(tmp_path)

    result = run_csv_structural_file_touch_status(root=_root(tmp_path), output_dir=_root(tmp_path) / "status")

    assert result.latest_run_id == "002_header"
    assert result.latest_runtime_status == "CSV_STRUCTURAL_HEADER_ONLY_REPORT_ONLY"
    assert result.latest_health_status == "PASS"
    assert result.file_touch_level == "CSV_STRUCTURAL_HEADER_ONLY"
    assert result.csv_read_level == "CSV_HEADER_ONLY"
    assert result.local_file_hash_level == "LOCAL_FILE_HASH_NONE"
    assert result.csv_header_read is True
    assert result.csv_header_column_count == 3
    assert result.csv_row_count_computed is False
    assert result.csv_row_count == ""
    assert result.csv_values_read is False
    assert result.csv_full_content_read is False
    assert result.local_file_byte_hash_computed is False
    assert result.local_file_byte_hash_algorithm == ""
    assert result.real_csv_consumed is False
    assert result.active_replay_input is False
    assert result.buy_review_allowed is False
    assert result.trading_allowed is False
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert result.artifact_paths["status_csv"].is_file()
    status_blob = json.dumps(result.summary_frame.to_dict("records"))
    for forbidden in FORBIDDEN_WORDING:
        assert forbidden not in status_blob
        assert forbidden not in result.recommended_next_task


def test_views_read_artifact_metadata_only_after_source_csv_removed(tmp_path: Path) -> None:
    _no_input, _header, csv_path = _create_no_input_and_header_artifacts(tmp_path)
    csv_path.unlink()

    index = build_csv_structural_file_touch_index(root=_root(tmp_path), output_dir=_root(tmp_path) / "index")
    health = check_csv_structural_file_touch_health(root=_root(tmp_path), output_dir=_root(tmp_path) / "health")
    status = run_csv_structural_file_touch_status(root=_root(tmp_path), output_dir=_root(tmp_path) / "status")

    assert index.artifact_count == 2
    assert health.status == "PASS"
    assert status.latest_run_id == "002_header"
    assert "SENTINEL_VIEW_TEST_ROW_VALUE_DO_NOT_READ" not in index.index_frame.to_csv(index=False)
    assert not Path("docs/project_sources").exists()
