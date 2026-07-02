from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_csv_physical_data_line_count_only as core,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
RESEARCH_STATUS_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Physical Data-Line "
    "Count-Only Research-Status Planning Report-Only v0.1"
)
HEADER_SENTINEL = "HEADER_SENTINEL_SHOULD_NOT_PRINT"
ROW_SENTINEL = "ROW_SENTINEL_SHOULD_NOT_PRINT"
FULL_CONTENT_SENTINEL = "FULL_CONTENT_SENTINEL_SHOULD_NOT_PRINT"
HASH_SENTINEL = "SOURCE_HASH_EXPECTED_HASH_LOCAL_BYTE_HASH_SHOULD_NOT_PRINT"
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


def test_cli_command_registration_for_all_four_commands(capsys) -> None:
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        with pytest.raises(SystemExit) as exc_info:
            cli.main([command, "--help"])
        output = capsys.readouterr()

        assert exc_info.value.code == 0
        assert command in output.out


def test_core_cli_no_input_exits_zero_and_writes_safe_artifacts(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    code, output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    assert code == 0
    assert "runtime_status: NO_CSV_PHYSICAL_DATA_LINE_COUNT_INPUT" in output
    assert "health_status: PASS" in output
    assert "file_touch_level: FILE_TOUCH_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "csv_physical_data_line_count_level: CSV_PHYSICAL_DATA_LINE_COUNT_NONE" in output
    assert "report_only: True" in output
    assert "diagnostic_only: True" in output
    assert "csv_values_read: False" in output
    assert "csv_full_content_read: False" in output
    assert "local_file_byte_hash_computed: False" in output
    assert "expected_hash_verification_performed: False" in output
    assert "source_hash_validated: False" in output
    assert "revision_id_validated: False" in output
    assert "available_time_validated: False" in output
    assert "pit_admissibility_validated: False" in output
    assert "reviewer_authority_validated: False" in output
    assert "active_replay_input: False" in output
    assert "trading_allowed: False" in output
    assert "buy_review_allowed: False" in output
    assert "data_raw_written: False" in output
    assert (root / "cli_no_input" / "metadata.json").is_file()
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_safe_count_outputs_count_policy_and_hides_values(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    manifest_path, header_path, _csv_path = _write_valid_inputs(
        tmp_path,
        f"{HEADER_SENTINEL},h2\n{ROW_SENTINEL}1,r2\n{ROW_SENTINEL}2,r4\n",
    )

    code, output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_count",
            "--package-manifest-path",
            str(manifest_path),
            "--header-metadata-path",
            str(header_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-csv-physical-data-line-count-only",
        ],
        capsys,
    )

    assert code == 0
    assert "runtime_status: CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY" in output
    assert "health_status: PASS" in output
    assert "csv_physical_data_line_count: 2" in output
    assert "csv_physical_data_line_count_policy: PHYSICAL_NON_HEADER_LINE_COUNT" in output
    assert "csv_physical_line_count_total: 3" in output
    assert "target_csv_opened_for_physical_data_line_count: True" in output
    assert "csv_values_read: False" in output
    assert "csv_full_content_read: False" in output
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_zero_data_lines_warns_without_failure_exit(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path, "h1,h2\n")

    code, output = _run_count_cli(tmp_path, root, "cli_zero", manifest_path, header_path, capsys)

    assert code == 0
    assert "runtime_status: CSV_PHYSICAL_DATA_LINE_COUNT_WARN_ZERO_DATA_LINES" in output
    assert "health_status: WARN" in output
    assert "csv_physical_data_line_count: 0" in output


def test_core_cli_blocked_cases_return_fail_style_output(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    manifest_path, header_path, csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\n")

    missing_allow_code, missing_allow_output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "missing_allow",
            "--package-manifest-path",
            str(manifest_path),
            "--header-metadata-path",
            str(header_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
        ],
        capsys,
    )
    assert missing_allow_code != 0
    assert "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MISSING_ALLOW_FLAG" in missing_allow_output
    assert "health_status: FAIL" in missing_allow_output

    malformed_manifest = tmp_path / "allowed" / "malformed.json"
    _write_text(malformed_manifest, "{malformed")
    malformed_code, malformed_output = _run_count_cli(tmp_path, root, "malformed", malformed_manifest, header_path, capsys)
    assert malformed_code != 0
    assert "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_MANIFEST_SCHEMA" in malformed_output

    protected_csv = tmp_path / "data" / "raw" / "protected.csv"
    _write_json(manifest_path, _manifest(protected_csv, header_path))
    _write_json(header_path, _header_metadata(protected_csv))
    protected_code, protected_output = _run_count_cli(tmp_path, root, "protected", manifest_path, header_path, capsys)
    assert protected_code != 0
    assert "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_PATH_GUARD" in protected_output

    _write_json(manifest_path, _manifest(csv_path, header_path))
    header = _header_metadata(csv_path)
    header["csv_values_read"] = True
    _write_json(header_path, header)
    unsafe_header_code, unsafe_header_output = _run_count_cli(
        tmp_path, root, "unsafe_header", manifest_path, header_path, capsys
    )
    assert unsafe_header_code != 0
    assert "CSV_PHYSICAL_DATA_LINE_COUNT_BLOCKED_BY_HEADER_POLICY" in unsafe_header_output


def test_core_cli_help_contains_no_forbidden_args(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for allowed in [
        "--output-root",
        "--run-id",
        "--package-manifest-path",
        "--header-metadata-path",
        "--allowed-manifest-root",
        "--allow-csv-physical-data-line-count-only",
        "--max-count-input-bytes",
    ]:
        assert allowed in output
    for forbidden in [
        "--csv-path",
        "--direct-csv-path",
        "--file-path",
        "--package-root",
        "--reviewed-csv-path",
        "--raw-csv-path",
        "--csv-parser",
        "--true-record-count",
        "--value-read",
        "--full-content",
        "--local-file-hash",
        "--expected-hash",
        "--source-hash-validation",
        "--revision-id-validation",
        "--available-time-validation",
        "--pit-validator",
        "--reviewer-authority",
        "--active-input",
        "--replay",
        "--package-candidate",
        "--trading",
        "--automatic-discovery",
    ]:
        assert forbidden not in output


def test_index_health_status_cli_smoke_and_source_deletion_boundary(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    manifest_path, header_path, csv_path = _write_valid_inputs(tmp_path, "h1,h2\nr1,r2\nr3,r4\n")
    code, output = _run_count_cli(tmp_path, root, "cli_count", manifest_path, header_path, capsys)
    assert code == 0
    csv_path.unlink()
    header_path.unlink()

    index_code, index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    health_code, health_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")],
        capsys,
    )
    status_code, status_output = _run_cli(
        [STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")],
        capsys,
    )

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli_count" in index_output
    assert "latest_runtime_status: CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY" in index_output
    assert "latest_csv_physical_data_line_count: 2" in index_output
    assert "latest_csv_physical_data_line_count_policy: PHYSICAL_NON_HEADER_LINE_COUNT" in index_output
    assert health_code == 0
    assert "health_status: PASS" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_count" in status_output
    assert "latest_runtime_status: CSV_PHYSICAL_DATA_LINE_COUNT_ONLY_REPORT_ONLY" in status_output
    assert "latest_csv_physical_data_line_count: 2" in status_output
    assert f"recommended_next_task: {RESEARCH_STATUS_NEXT_TASK}" in status_output
    assert "CLI Report-Only v0.1" not in status_output
    for output_text in [index_output, health_output, status_output]:
        _assert_no_disclosure(output_text)
        _assert_no_unsafe_wording(output_text)


def test_health_cli_warn_and_fail_paths(tmp_path: Path, capsys) -> None:
    warn_root = _root(tmp_path / "warn")
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path / "warn", "")
    zero_code, _zero_output = _run_count_cli(tmp_path / "warn", warn_root, "zero", manifest_path, header_path, capsys)
    assert zero_code == 0

    warn_health_code, warn_health_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(warn_root), "--output-dir", str(warn_root / "health")],
        capsys,
    )
    assert warn_health_code == 0
    assert "health_status: WARN" in warn_health_output

    fail_root = _root(tmp_path / "fail")
    manifest_path, header_path, _csv_path = _write_valid_inputs(tmp_path / "fail", "h1,h2\nr1,r2\n")
    artifact = core.run_csv_physical_data_line_count_only(
        output_root=fail_root,
        run_id="unsafe",
        package_manifest_path=manifest_path,
        header_metadata_path=header_path,
        allowed_manifest_roots=[tmp_path / "fail" / "allowed"],
        file_touch_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_read_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        csv_physical_data_line_count_level="CSV_PHYSICAL_DATA_LINE_COUNT_ONLY",
        allow_csv_physical_data_line_count_only=True,
    )
    _mutate_metadata(artifact, csv_values_read=True)
    fail_health_code, fail_health_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(fail_root), "--output-dir", str(fail_root / "health")],
        capsys,
    )
    assert fail_health_code != 0
    assert "health_status: FAIL" in fail_health_output
    assert "error_count:" in fail_health_output


def test_cli_source_slice_and_test_file_exclude_forbidden_dependencies_and_bulk_reads() -> None:
    test_source = _read_file(Path(__file__))
    cli_source = _read_file(Path("src/quant_replay_system/cli.py"))
    relevant_cli = cli_source[
        cli_source.index("tiny-pit-real-reviewed-local-csv-package-candidate-csv-physical-data-line-count-only") :
    ]
    relevant_cli = relevant_cli[
        : relevant_cli.index("reviewed-local-csv-replay-prototype-input-contract-fixture-index")
    ]

    forbidden_imports = [
        "import " + "pandas",
        "from " + "pandas",
        "import " + "csv",
        "from " + "csv",
        "hash" + "lib",
    ]
    forbidden_reads = [".read_" + "text(", ".read_" + "bytes("]
    for source in [test_source, relevant_cli]:
        for forbidden in [*forbidden_imports, *forbidden_reads]:
            assert forbidden not in source


def test_docs_project_sources_not_created(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    code, _output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "no_input"], capsys)
    assert code == 0

    assert not Path("docs/project_sources").exists()


def _run_count_cli(
    tmp_path: Path,
    root: Path,
    run_id: str,
    manifest_path: Path,
    header_path: Path,
    capsys,
) -> tuple[int, str]:
    return _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            run_id,
            "--package-manifest-path",
            str(manifest_path),
            "--header-metadata-path",
            str(header_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-csv-physical-data-line-count-only",
        ],
        capsys,
    )


def _run_cli(args: list[str], capsys) -> tuple[int, str]:
    code = cli.main(args)
    output = capsys.readouterr()
    assert output.err == ""
    return code, output.out


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


def _assert_no_disclosure(output: str) -> None:
    for sentinel in [HEADER_SENTINEL, ROW_SENTINEL, FULL_CONTENT_SENTINEL, HASH_SENTINEL]:
        assert sentinel not in output
    for token in ["row_snippet", "parsed_field", "full_content_sample"]:
        assert token not in output


def _assert_no_unsafe_wording(output: str) -> None:
    for wording in UNSAFE_WORDING:
        assert wording not in output


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "csv_physical_data_line_count_only"
