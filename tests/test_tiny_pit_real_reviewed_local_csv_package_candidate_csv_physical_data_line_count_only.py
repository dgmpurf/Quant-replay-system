from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only as core,
)


HEADER_SENTINEL = "HEADER_SENTINEL_SHOULD_NOT_APPEAR"
ROW_SENTINEL = "ROW_SENTINEL_SHOULD_NOT_APPEAR"

FORBIDDEN_OUTPUT_WORDING = {
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
    "target_csv_path",
    "direct_csv_path",
    "file_path",
    "package_root",
    "reviewed_csv_path",
    "raw_csv_path",
    "csv_parser",
    "true_record_count",
    "value_read",
    "full_content",
    "local_file_hash",
    "expected_hash",
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

NEGATIVE_FALSE_FIELDS = [
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


def test_no_input_safe_artifact_set_and_does_not_read_inputs(tmp_path: Path) -> None:
    missing_header = tmp_path / "allowed" / "missing_header.json"

    result = core.run_csv_physical_data_line_count_only(
        output_root=_output_root(tmp_path),
        run_id="no_input",
        header_metadata_path=missing_header,
    )

    assert result["runtime_status"] == "NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT"
    assert result["health_status"] == "PASS"
    assert result["workflow_stage"] == core.WORKFLOW_STAGE
    assert result["file_touch_level"] == "FILE_TOUCH_NONE"
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["local_file_hash_level"] == "LOCAL_FILE_HASH_NONE"
    assert result["expected_hash_verification_level"] == "EXPECTED_HASH_VERIFICATION_NONE"
    assert result["csv_physical_data_line_count_level"] == "CSV_PHYSICAL_DATA_LINE_COUNT_NONE"
    assert result["csv_physical_data_line_count_computed"] is False
    assert result["csv_physical_data_line_count"] == ""
    assert result["csv_physical_data_line_count_policy"] == ""
    assert result["csv_header_dependency_policy"] == ""
    assert result["header_metadata_reused"] is False
    assert result["target_csv_opened_for_physical_data_line_count"] is False
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    _assert_negative_fields_false(result)
    _assert_artifacts_exist(result, "no_input")


def test_missing_allow_flag_blocks_before_count(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    result = _run_count(
        tmp_path,
        run_id="missing_allow",
        manifest_path=manifest_path,
        header_path=header_path,
        allow=False,
    )

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MISSING_ALLOW_FLAG"
    assert result["health_status"] == "FAIL"
    assert result["target_csv_opened_for_physical_data_line_count"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda manifest, _header: manifest.pop("package_id"),
        lambda manifest, _header: manifest.__setitem__("report_only", False),
        lambda manifest, _header: manifest.__setitem__("diagnostic_only", False),
        lambda manifest, _header: manifest.__setitem__(
            "requested_file_touch_level", "CSV_STRUCTURAL_HEADER_ONLY"
        ),
        lambda manifest, _header: manifest.__setitem__(
            "requested_csv_read_level", "CSV_RECORD_COUNT_ONLY"
        ),
        lambda manifest, _header: manifest.__setitem__(
            "requested_csv_physical_data_line_count_level", "CSV_PHYSICAL_DATA_LINE_COUNT_NONE"
        ),
        lambda manifest, _header: manifest.__setitem__(
            "requested_local_file_hash_level", "LOCAL_FILE_HASH_SHA256_ONLY"
        ),
        lambda manifest, _header: manifest.__setitem__(
            "requested_expected_hash_verification_level", "EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY"
        ),
        lambda manifest, _header: manifest.__setitem__("row_count_policy", "CSV_RECORD_COUNT"),
        lambda manifest, _header: manifest.__setitem__("csv_file_references", []),
        lambda manifest, _header: manifest["csv_file_references"][0].__setitem__(
            "reference_type", "direct_csv_path"
        ),
        lambda manifest, _header: manifest["csv_file_references"][0].__setitem__("required", False),
        lambda manifest, _header: manifest["csv_file_references"][0].__setitem__(
            "declared_only", True
        ),
        lambda manifest, _header: manifest["csv_file_references"][0].__setitem__(
            "intended_touch_level", "CSV_HEADER_ONLY"
        ),
    ],
)
def test_malformed_or_missing_manifest_fields_block(tmp_path: Path, mutation) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n", mutation)

    result = _run_count(tmp_path, run_id="bad_manifest", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"
    assert result["target_csv_opened_for_physical_data_line_count"] is False


def test_malformed_json_manifest_blocks(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    manifest_path = allowed / "manifest.json"
    header_path = allowed / "header.json"
    _write_raw_text(manifest_path, "{malformed")
    _write_json(header_path, _header_metadata(allowed / "sample.csv"))

    result = _run_count(tmp_path, run_id="malformed_json", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA"
    assert result["health_status"] == "FAIL"


def test_unsupported_requested_levels_block(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    result = core.run_csv_physical_data_line_count_only(
        output_root=_output_root(tmp_path),
        run_id="bad_level",
        package_manifest_path=manifest_path,
        header_metadata_path=header_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_STRUCTURAL_HEADER_ONLY",
        csv_read_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_physical_data_line_count_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        allow_csv_physical_data_line_count_only=True,
    )

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_LEVEL"
    assert result["health_status"] == "FAIL"


@pytest.mark.parametrize(
    "manifest_path_factory",
    [
        lambda tmp_path: "https://example.invalid/manifest.json",
        lambda tmp_path: tmp_path / "outside" / "manifest.json",
        lambda tmp_path: tmp_path / ".env" / "manifest.json",
        lambda tmp_path: tmp_path / "allowed" / "secrets" / "manifest.json",
    ],
)
def test_path_guard_blocks_url_traversal_secret_and_env_paths(tmp_path: Path, manifest_path_factory) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")
    bad_manifest_path = manifest_path_factory(tmp_path)
    if isinstance(bad_manifest_path, Path) and not str(bad_manifest_path).startswith("https://"):
        bad_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(bad_manifest_path, _manifest(_csv_path, header_path))

    result = _run_count(
        tmp_path,
        run_id="path_guard",
        manifest_path=bad_manifest_path,
        header_path=header_path,
    )

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD"
    assert result["health_status"] == "FAIL"


def test_allowed_root_escape_and_protected_paths_block(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    csv_path = tmp_path / "data" / "raw" / "sample.csv"
    header_path = allowed / "header.json"
    manifest_path = allowed / "manifest.json"
    _write_json(header_path, _header_metadata(csv_path))
    _write_json(manifest_path, _manifest(csv_path, header_path))

    result = _run_count(tmp_path, run_id="protected_path", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD"
    assert result["health_status"] == "FAIL"


def test_non_csv_target_blocks(tmp_path: Path) -> None:
    manifest_path, header_path, csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")
    txt_path = csv_path.with_suffix(".txt")
    _write_file(txt_path, "h1,h2\nr1,r2\n")
    _write_json(manifest_path, _manifest(txt_path, header_path))
    _write_json(header_path, _header_metadata(txt_path))

    result = _run_count(tmp_path, run_id="non_csv", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_UNSUPPORTED_FILE_TYPE"
    assert result["health_status"] == "FAIL"


def test_size_limit_blocks_before_scan(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    result = _run_count(
        tmp_path,
        run_id="size_limit",
        manifest_path=manifest_path,
        header_path=header_path,
        max_count_input_bytes=1,
    )

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_SIZE_LIMIT"
    assert result["health_status"] == "FAIL"
    assert result["target_csv_opened_for_physical_data_line_count"] is False


def test_header_metadata_path_required_and_must_match_manifest(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    missing_header_arg = core.run_csv_physical_data_line_count_only(
        output_root=_output_root(tmp_path),
        run_id="missing_header_arg",
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_read_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_physical_data_line_count_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        allow_csv_physical_data_line_count_only=True,
    )
    assert missing_header_arg["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY"

    other_header = header_path.with_name("other_header.json")
    _write_json(other_header, _header_metadata(_csv_path))
    mismatch = _run_count(tmp_path, run_id="header_mismatch", manifest_path=manifest_path, header_path=other_header)
    assert mismatch["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA"

    missing_file = _run_count(
        tmp_path,
        run_id="missing_header_file",
        manifest_path=manifest_path,
        header_path=header_path.with_name("missing_header.json"),
    )
    assert missing_file["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD"


@pytest.mark.parametrize(
    "header_mutation",
    [
        lambda header: header.__setitem__("report_only", False),
        lambda header: header.__setitem__("diagnostic_only", False),
        lambda header: header.__setitem__("csv_header_read", False),
        lambda header: header.__setitem__("csv_header_column_count", 0),
        lambda header: header.__setitem__("csv_row_count_computed", True),
        lambda header: header.__setitem__("csv_values_read", True),
        lambda header: header.__setitem__("csv_full_content_read", True),
        lambda header: header.__setitem__("real_csv_consumed", True),
        lambda header: header.__setitem__("local_file_byte_hash_computed", True),
        lambda header: header.__setitem__("expected_hash_verification_performed", True),
        lambda header: header.__setitem__("source_hash_validated", True),
        lambda header: header.__setitem__("revision_id_validated", True),
        lambda header: header.__setitem__("available_time_validated", True),
        lambda header: header.__setitem__("pit_admissibility_validated", True),
        lambda header: header.__setitem__("reviewer_authority_validated", True),
        lambda header: header.__setitem__("real_package_candidate_created", True),
        lambda header: header.__setitem__("active_replay_input_ready_emitted", True),
        lambda header: header.__setitem__("trading_allowed", True),
        lambda header: header.__setitem__("data_raw_written", True),
    ],
)
def test_unsafe_header_metadata_blocks(tmp_path: Path, header_mutation) -> None:
    manifest_path, header_path, csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")
    header = _header_metadata(csv_path)
    header_mutation(header)
    _write_json(header_path, header)

    result = _run_count(tmp_path, run_id="unsafe_header", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY"
    assert result["health_status"] == "FAIL"
    assert result["target_csv_opened_for_physical_data_line_count"] is False


def test_header_metadata_target_path_mismatch_blocks(tmp_path: Path) -> None:
    manifest_path, header_path, csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")
    mismatch_target = csv_path.with_name("other.csv")
    _write_file(mismatch_target, "h1,h2\nr1,r2\n")
    _write_json(header_path, _header_metadata(mismatch_target))

    result = _run_count(tmp_path, run_id="header_target_mismatch", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY"
    assert result["health_status"] == "FAIL"


def test_safe_physical_data_line_count_excludes_header(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(
        tmp_path, f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n{ROW_SENTINEL}2,r4\n"
    )

    result = _run_count(tmp_path, run_id="count_two", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY"
    assert result["health_status"] == "PASS"
    assert result["csv_physical_data_line_count_computed"] is True
    assert result["csv_physical_data_line_count"] == 2
    assert result["csv_physical_line_count_total"] == 3
    assert result["csv_physical_data_line_count_policy"] == "PHYSICAL_NON_HEADER_LINE_COUNT"
    assert result["csv_header_dependency_policy"] == "REQUIRE_PRIOR_HEADER_ONLY_METADATA"
    assert result["header_metadata_reused"] is True
    assert result["csv_header_line_skipped_by_policy"] is True
    assert result["target_csv_opened_for_physical_data_line_count"] is True
    assert result["issue_count"] == 0
    assert result["warning_count"] == 0
    _assert_negative_fields_false(result)
    _assert_artifacts_do_not_contain(result, {HEADER_SENTINEL, ROW_SENTINEL, "row_snippet", "parsed_field"})


@pytest.mark.parametrize(
    ("csv_text", "expected_total", "header_skipped"),
    [
        ("h1,h2\n", 1, True),
        ("", 0, False),
    ],
)
def test_zero_data_lines_warn_without_crash(
    tmp_path: Path, csv_text: str, expected_total: int, header_skipped: bool
) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, csv_text)

    result = _run_count(tmp_path, run_id="zero_data_lines", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES"
    assert result["health_status"] == "WARN"
    assert result["csv_physical_data_line_count"] == 0
    assert result["csv_physical_line_count_total"] == expected_total
    assert result["csv_header_line_skipped_by_policy"] is header_skipped
    assert result["warning_count"] >= 1
    _assert_negative_fields_false(result)


def test_quoted_multiline_like_fixture_is_physical_line_count_not_record_count(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(
        tmp_path,
        "h1,h2\n"
        '"semantic value starts\n'
        'semantic value continues",r2\n'
        "plain,r4\n",
    )

    result = _run_count(tmp_path, run_id="quoted_multiline_like", manifest_path=manifest_path, header_path=header_path)

    assert result["runtime_status"] == "CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY"
    assert result["csv_physical_data_line_count"] == 3
    artifact_text = _all_artifact_text(result)
    assert "physical non-header lines" in artifact_text
    assert "quoted multiline" in artifact_text.lower()
    assert "semantic CSV record" in artifact_text


def test_module_source_excludes_forbidden_dependencies_and_path_bulk_reads() -> None:
    source = _read_text(Path(core.__file__))

    assert "import pandas" not in source
    assert "from pandas" not in source
    assert "import csv" not in source
    assert "from csv" not in source
    assert "hashlib" not in source
    assert ".read_text(" not in source
    assert ".read_bytes(" not in source
    assert "DictReader" not in source
    assert "csv.reader" not in source


def test_public_api_signature_has_no_direct_csv_or_downstream_arguments() -> None:
    parameters = set(inspect.signature(core.run_csv_physical_data_line_count_only).parameters)

    assert FORBIDDEN_API_NAMES.isdisjoint(parameters)


def test_generated_artifacts_exclude_values_snippets_hashes_and_unsafe_wording(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(
        tmp_path,
        f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n",
    )

    result = _run_count(tmp_path, run_id="artifact_disclosure", manifest_path=manifest_path, header_path=header_path)
    artifact_text = _all_artifact_text(result)

    for forbidden in [HEADER_SENTINEL, ROW_SENTINEL, "row_snippet", "parsed_field"]:
        assert forbidden not in artifact_text
    for wording in FORBIDDEN_OUTPUT_WORDING:
        assert wording not in result["runtime_status"]
        assert wording not in result["workflow_stage"]
        assert wording not in result["recommended_next_task"]
        assert wording not in artifact_text


def test_all_negative_proof_fields_false_for_success(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    result = _run_count(tmp_path, run_id="negative_flags", manifest_path=manifest_path, header_path=header_path)

    _assert_negative_fields_false(result)


def test_docs_project_sources_not_created_and_artifacts_stay_under_tmp_output_root(tmp_path: Path) -> None:
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")
    output_root = _output_root(tmp_path)

    result = _run_count(tmp_path, run_id="artifact_root", manifest_path=manifest_path, header_path=header_path)

    for artifact_path in result["artifact_paths"].values():
        assert _is_relative_to(Path(artifact_path), output_root)
    assert not Path("docs/project_sources").exists()


def _run_count(
    tmp_path: Path,
    *,
    run_id: str,
    manifest_path,
    header_path,
    allow: bool = True,
    max_count_input_bytes: int = 1_048_576,
) -> dict:
    return core.run_csv_physical_data_line_count_only(
        output_root=_output_root(tmp_path),
        run_id=run_id,
        package_manifest_path=manifest_path,
        header_metadata_path=header_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        file_touch_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_read_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_physical_data_line_count_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        allow_csv_physical_data_line_count_only=allow,
        max_count_input_bytes=max_count_input_bytes,
    )


def _write_valid_inputs(tmp_path: Path, csv_text: str, mutation=None) -> tuple[Path, Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(exist_ok=True)
    csv_path = allowed / "sample.csv"
    header_path = allowed / "header_metadata.json"
    manifest_path = allowed / "package_manifest.json"
    _write_file(csv_path, csv_text)
    manifest = _manifest(csv_path, header_path)
    header = _header_metadata(csv_path)
    if mutation is not None:
        mutation(manifest, header)
    _write_json(manifest_path, manifest)
    _write_json(header_path, header)
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
        "limitations": [
            "Physical non-header line count only; quoted multiline CSV records are not semantic CSV records here."
        ],
    }


def _header_metadata(csv_path: Path) -> dict:
    flags = core.csv_physical_data_line_count_safety_flags()
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
        **flags,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_raw_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"


def _assert_artifacts_exist(result: dict, run_id: str) -> None:
    assert Path(result["artifact_root"]).name == run_id
    for path in result["artifact_paths"].values():
        assert Path(path).exists()


def _assert_negative_fields_false(result: dict) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert result[field] is False, field


def _assert_artifacts_do_not_contain(result: dict, forbidden_values: set[str]) -> None:
    artifact_text = _all_artifact_text(result)
    for forbidden in forbidden_values:
        assert forbidden not in artifact_text


def _all_artifact_text(result: dict) -> str:
    chunks = []
    for path in result["artifact_paths"].values():
        chunks.append(_read_text(Path(path)))
    return "\n".join(chunks)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
