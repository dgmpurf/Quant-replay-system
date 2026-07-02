from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only as core,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_health import (
    check_csv_physical_data_line_count_only_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_index import (
    build_csv_physical_data_line_count_only_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_status import (
    run_csv_physical_data_line_count_only_status,
)


HEADER_SENTINEL = "HEADER_SENTINEL_SHOULD_NOT_APPEAR"
ROW_SENTINEL = "ROW_SENTINEL_SHOULD_NOT_APPEAR"
FULL_CONTENT_SENTINEL = "FULL_CONTENT_SAMPLE_SHOULD_NOT_APPEAR"
HASH_SENTINEL = "SOURCE_HASH_EXPECTED_HASH_LOCAL_BYTE_HASH_SHOULD_NOT_APPEAR"
CLI_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line "
    "Count-Only Research-Status Planning Report-Only v0.1"
)
UNSAFE_WORDING = [
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
NEGATIVE_FIELDS = [
    "csv_header_read",
    "csv_header_values_recorded",
    "csv_values_read",
    "csv_value_fields_parsed",
    "csv_row_values_stored",
    "csv_full_content_semantically_read",
    "csv_full_content_read",
    "real_csv_consumed",
    "local_file_byte_hash_computed",
    "local_file_byte_hash_recomputed",
    "expected_hash_verification_performed",
    "expected_hash_verified_against_local_metadata",
    "expected_hash_verified_against_source_hash",
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
UNSAFE_FLAG_FIELDS = [
    "csv_values_read",
    "csv_value_fields_parsed",
    "csv_row_values_stored",
    "csv_full_content_read",
    "csv_full_content_semantically_read",
    "csv_header_values_recorded",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "reviewer_authority_validated",
    "local_file_byte_hash_computed",
    "local_file_byte_hash_recomputed",
    "expected_hash_verification_performed",
    "real_package_candidate_created",
    "active_replay_input",
    "replay_execution_allowed",
    "trading_allowed",
    "buy_review_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]


def test_index_discovers_no_input_artifact_and_exposes_safe_fields(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_csv_physical_data_line_count_only(output_root=root, run_id="001_no_input")

    result = build_csv_physical_data_line_count_only_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "001_no_input"
    assert row["runtime_status"] == "NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT"
    assert row["health_status"] == "PASS"
    assert row["file_touch_level"] == "FILE_TOUCH_NONE"
    assert row["csv_read_level"] == "CSV_READ_NONE"
    assert row["csv_physical_data_line_count_computed"] is False
    assert row["csv_physical_data_line_count"] == ""
    assert row["target_csv_opened_for_physical_data_line_count"] is False
    _assert_negative_fields_false(row)


def test_index_discovers_positive_count_artifact_and_exposes_policy(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core_count(tmp_path, root, "002_count", f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n{ROW_SENTINEL}2,r4\n")

    result = build_csv_physical_data_line_count_only_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY"
    assert row["csv_physical_data_line_count_computed"] is True
    assert row["csv_physical_data_line_count"] == 2
    assert row["csv_physical_line_count_total"] == 3
    assert row["csv_physical_data_line_count_policy"] == "PHYSICAL_NON_HEADER_LINE_COUNT"
    assert row["csv_header_dependency_policy"] == "REQUIRE_PRIOR_HEADER_ONLY_METADATA"
    assert row["header_metadata_reused"] is True
    assert row["csv_header_line_skipped_by_policy"] is True
    assert row["target_csv_opened_for_physical_data_line_count"] is True


def test_index_output_excludes_header_row_full_content_and_hash_sentinels(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core_count(tmp_path, root, "index_no_leak", f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n")

    result = build_csv_physical_data_line_count_only_index(root=root, output_dir=root / "index")
    text = _artifact_text(result.artifact_paths.values())

    for sentinel in [HEADER_SENTINEL, ROW_SENTINEL, FULL_CONTENT_SENTINEL, HASH_SENTINEL]:
        assert sentinel not in text
    for token in ["row_snippet", "parsed_field", "full_content_sample"]:
        assert token not in text


def test_health_pass_for_safe_no_input_and_positive_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_csv_physical_data_line_count_only(output_root=root, run_id="001_no_input")
    _run_core_count(tmp_path, root, "002_count", "h1,h2\nr1,r2\n")

    result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 2
    assert result.error_count == 0
    assert result.warning_count == 0


def test_health_warn_for_zero_data_lines(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core_count(tmp_path, root, "zero", "h1,h2\n")

    result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert result.warning_count >= 1
    assert "ZERO_PHYSICAL_DATA_LINES" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_ambiguous_count_policy(tmp_path: Path) -> None:
    root = _root(tmp_path)
    artifact = _run_core_count(tmp_path, root, "bad_policy", "h1,h2\nr1,r2\n")
    _mutate_metadata(artifact, csv_physical_data_line_count_policy="CSV_RECORD_COUNT_ONLY")

    result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "COUNT_POLICY_INVALID" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_leakage_in_artifact_text_without_echoing_values(tmp_path: Path) -> None:
    root = _root(tmp_path)
    artifact = _run_core_count(tmp_path, root, "leak", "h1,h2\nr1,r2\n")
    _write_text(Path(artifact["artifact_paths"]["report"]), f"{HEADER_SENTINEL} {ROW_SENTINEL} {HASH_SENTINEL}")

    result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")
    text = _artifact_text(result.artifact_paths.values())

    assert result.status == "FAIL"
    assert "ARTIFACT_DISCLOSURE_LEAK" in {row["issue_code"] for row in result.rows}
    assert HEADER_SENTINEL not in text
    assert ROW_SENTINEL not in text
    assert HASH_SENTINEL not in text


def test_health_fails_for_each_forbidden_metadata_flag(tmp_path: Path) -> None:
    for field in UNSAFE_FLAG_FIELDS:
        root = _root(tmp_path / field)
        artifact = _run_core_count(tmp_path / field, root, "unsafe", "h1,h2\nr1,r2\n")
        _mutate_metadata(artifact, **{field: True})

        result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_unsafe_live_status_stage_or_next_task_wording(tmp_path: Path) -> None:
    for field in ["runtime_status", "workflow_stage", "recommended_next_task"]:
        root = _root(tmp_path / field)
        artifact = _run_core_count(tmp_path / field, root, "unsafe_wording", "h1,h2\nr1,r2\n")
        _mutate_metadata(artifact, **{field: "ACTIVE_REPLAY_INPUT_READY"})

        result = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_STATUS_WORDING" in {row["issue_code"] for row in result.rows}


def test_status_summarizes_latest_safe_artifact_and_recommends_cli_phase(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_csv_physical_data_line_count_only(output_root=root, run_id="001_no_input")
    _run_core_count(tmp_path, root, "002_count", "h1,h2\nr1,r2\nr3,r4\n")

    result = run_csv_physical_data_line_count_only_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "002_count"
    assert result.latest_runtime_status == "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY"
    assert result.latest_health_status == "PASS"
    assert result.latest_csv_physical_data_line_count == 2
    assert result.latest_csv_physical_data_line_count_policy == "PHYSICAL_NON_HEADER_LINE_COUNT"
    assert result.recommended_next_task == CLI_NEXT_TASK
    assert "Research-Status Planning" in result.recommended_next_task
    assert "Checkpoint" not in result.recommended_next_task
    _assert_negative_fields_false(result.summary)


def test_status_preserves_warn_health_for_zero_data_lines(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core_count(tmp_path, root, "zero", "")

    result = run_csv_physical_data_line_count_only_status(root=root, output_dir=root / "status")

    assert result.latest_health_status == "WARN"
    assert result.latest_runtime_status == "CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES"
    assert result.latest_csv_physical_data_line_count == 0


def test_status_does_not_expose_sentinels_or_imply_downstream_readiness(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core_count(tmp_path, root, "status_no_leak", f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n")

    result = run_csv_physical_data_line_count_only_status(root=root, output_dir=root / "status")
    text = _artifact_text(result.artifact_paths.values())

    for sentinel in [HEADER_SENTINEL, ROW_SENTINEL, FULL_CONTENT_SENTINEL, HASH_SENTINEL]:
        assert sentinel not in text
    for wording in UNSAFE_WORDING:
        assert wording not in result.latest_runtime_status
        assert wording not in result.latest_workflow_stage
        assert wording not in result.recommended_next_task
        assert wording not in text
    assert result.summary["real_package_candidate_created"] is False
    assert result.summary["active_replay_input"] is False
    assert result.summary["pit_admissibility_validated"] is False
    assert result.summary["buy_review_allowed"] is False
    assert result.summary["trading_allowed"] is False


def test_views_do_not_reopen_target_csv_or_recount_after_source_files_deleted(tmp_path: Path) -> None:
    root = _root(tmp_path)
    artifact = _run_core_count(tmp_path, root, "source_deleted", "h1,h2\nr1,r2\nr3,r4\n")
    for path in [tmp_path / "allowed" / "sample.csv", tmp_path / "allowed" / "header_metadata.json"]:
        path.unlink()

    index = build_csv_physical_data_line_count_only_index(root=root, output_dir=root / "index")
    health = check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")
    status = run_csv_physical_data_line_count_only_status(root=root, output_dir=root / "status")

    assert index.rows[0]["csv_physical_data_line_count"] == artifact["csv_physical_data_line_count"]
    assert health.status == "PASS"
    assert status.latest_csv_physical_data_line_count == artifact["csv_physical_data_line_count"]


def test_views_modules_exclude_forbidden_dependencies_and_path_bulk_reads() -> None:
    for module_path in [
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_index.py"),
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_health.py"),
        Path("src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only_status.py"),
    ]:
        text = _read_file(module_path)
        assert "import pandas" not in text
        assert "from pandas" not in text
        assert "import csv" not in text
        assert "from csv" not in text
        assert "hashlib" not in text
        assert ".read_text(" not in text
        assert ".read_bytes(" not in text
        assert "DictReader" not in text
        assert "csv.reader" not in text


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_csv_physical_data_line_count_only(output_root=root, run_id="no_input")
    build_csv_physical_data_line_count_only_index(root=root, output_dir=root / "index")
    check_csv_physical_data_line_count_only_health(root=root, output_dir=root / "health")
    run_csv_physical_data_line_count_only_status(root=root, output_dir=root / "status")

    assert not Path("docs/project_sources").exists()


def _run_core_count(tmp_path: Path, root: Path, run_id: str, csv_text: str) -> dict:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, csv_text)
    return core.run_csv_physical_data_line_count_only(
        output_root=root,
        run_id=run_id,
        package_manifest_path=manifest_path,
        header_metadata_path=header_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_read_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_physical_data_line_count_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        allow_csv_physical_data_line_count_only=True,
    )


def _write_valid_inputs(tmp_path: Path, csv_text: str) -> tuple[Path, Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(parents=True, exist_ok=True)
    csv_path = allowed / "sample.csv"
    header_path = allowed / "header_metadata.json"
    manifest_path = allowed / "package_manifest.json"
    _write_text(csv_path, csv_text)
    _write_json(header_path, _header_metadata(csv_path))
    _write_json(manifest_path, _manifest(csv_path, header_path))
    return manifest_path, header_path, csv_path


def _manifest(csv_path: Path, header_path: Path) -> dict:
    return {
        "package_id": "synthetic-package",
        "package_schema_version": "tiny-pit-local-csv-v0.1",
        "created_at": "2026-07-02T00:00:00Z",
        "prepared_by": "pytest",
        "report_only": True,
        "diagnostic_only": True,
        "requested_file_touch_level": "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        "requested_csv_read_level": "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        "requested_csv_physical_data_line_count_level": "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        "requested_local_file_hash_level": "LOCAL_FILE_HASH_NONE",
        "requested_expected_hash_verification_level": "EXPECTED_HASH_VERIFICATION_NONE",
        "csv_file_references": [
            {
                "reference_type": "reviewed_local_csv_file_ref",
                "reference_name": "synthetic_csv",
                "path": str(csv_path),
                "required": True,
                "intended_touch_level": "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
                "declared_only": False,
                "notes": "Synthetic pytest file only.",
            }
        ],
        "header_metadata_reference": str(header_path),
        "row_count_policy": "PHYSICAL_NON_HEADER_LINE_COUNT",
        "forbidden_downstream_flags": core.csv_physical_data_line_count_safety_flags(),
        "limitations": ["Physical non-header line count only."],
    }


def _header_metadata(csv_path: Path) -> dict:
    return {
        "report_only": True,
        "diagnostic_only": True,
        "target_csv_path": str(csv_path),
        "csv_header_read": True,
        "csv_header_column_count": 2,
        "csv_row_count_computed": False,
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "local_file_byte_hash_computed": False,
        "expected_hash_verification_performed": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
        **core.csv_physical_data_line_count_safety_flags(),
    }


def _mutate_metadata(artifact: dict, **updates) -> None:
    path = Path(artifact["artifact_paths"]["metadata"])
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload.update(updates)
    _write_json(path, payload)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _read_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _artifact_text(paths) -> str:
    chunks = []
    for path in paths:
        path = Path(path)
        if path.is_file():
            chunks.append(_read_file(path))
    return "\n".join(chunks)


def _assert_negative_fields_false(row: dict) -> None:
    for field in NEGATIVE_FIELDS:
        assert row[field] is False, field


def _root(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"
