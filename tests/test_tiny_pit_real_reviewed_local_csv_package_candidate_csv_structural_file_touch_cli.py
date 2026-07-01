from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_csv_structural_file_touch import (
    REQUIRED_FALSE_FLAGS,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-csv-structural-header-only"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate CSV Structural Header-Only "
    "Research-Status Planning Report-Only v0.1"
)
SENTINEL = "SENTINEL_CLI_ROW_VALUE_DO_NOT_PRINT"


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "csv_structural_file_touch"


def _run_cli(args: list[str], capsys) -> str:
    code = cli.main(args)
    output = capsys.readouterr()
    assert code == 0, output.err
    assert output.err == ""
    return output.out


def _write_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "symbol,signal_date,review_note\n"
        f"000001,2024-04-02,{SENTINEL}\n",
        encoding="utf-8",
        newline="",
    )
    return path


def _manifest(csv_path: Path) -> dict[str, object]:
    return {
        "package_id": "tiny-pit-real-reviewed-local-csv-cli-001",
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


def _write_manifest(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_csv_structural_header_only_cli_commands_have_help(capsys) -> None:
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        with pytest.raises(SystemExit) as exc_info:
            cli.main([command, "--help"])
        output = capsys.readouterr()

        assert exc_info.value.code == 0
        assert command in output.out


def test_core_help_exposes_manifest_allowed_root_and_allow_flag_only(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    assert "--package-manifest-path" in output
    assert "--allowed-manifest-root" in output
    assert "--allow-csv-header-only" in output
    assert "--output-root" in output
    assert "--run-id" in output
    for forbidden in [
        "--csv-path",
        "--direct-csv-path",
        "--package-root",
        "--reviewed-csv-path",
        "--allow-row-count",
        "--allow-file-hash",
        "--replay-input",
        "--active-input",
        "automatic discovery",
    ]:
        assert forbidden not in output


def test_no_input_core_cli_smoke_writes_safe_artifact(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    assert "runtime_status: NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT" in output
    assert "file_touch_level: FILE_TOUCH_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "local_file_hash_level: LOCAL_FILE_HASH_NONE" in output
    assert "csv_header_read: False" in output
    assert "csv_header_column_count: 0" in output
    assert "csv_row_count_computed: False" in output
    assert "local_file_byte_hash_computed: False" in output
    assert "real_csv_consumed: False" in output
    assert "active_replay_input: False" in output
    assert "active_replay_input_ready_emitted: False" in output
    assert "trading_allowed: False" in output
    assert "buy_review_allowed: False" in output
    assert "data_raw_written: False" in output
    assert "data_processed_written: False" in output
    assert "data_cache_written: False" in output
    assert "artifact_path:" in output
    assert "report_path:" in output
    _assert_no_forbidden_output(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_header_only_cli_smoke_reads_header_only_and_hides_row_values(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    csv_path = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))

    output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_header",
            "--package-manifest-path",
            str(manifest_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-csv-header-only",
        ],
        capsys,
    )

    assert "runtime_status: CSV_STRUCTURAL_HEADER_ONLY_REPORT_ONLY" in output
    assert "file_touch_level: CSV_STRUCTURAL_HEADER_ONLY" in output
    assert "csv_read_level: CSV_HEADER_ONLY" in output
    assert "local_file_hash_level: LOCAL_FILE_HASH_NONE" in output
    assert "csv_header_read: True" in output
    assert "csv_header_column_count: 3" in output
    assert "csv_row_count_computed: False" in output
    assert "local_file_byte_hash_computed: False" in output
    assert "real_csv_consumed: False" in output
    assert "trading_allowed: False" in output
    assert SENTINEL not in output
    artifact_text = "\n".join(path.read_text(encoding="utf-8") for path in (root / "cli_header").iterdir() if path.is_file())
    assert SENTINEL not in artifact_text
    _assert_no_forbidden_output(output)


def test_index_health_status_cli_commands_use_tmp_path_artifact_metadata_only(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    assert "artifact_count: 1" in index_output
    assert "latest_runtime_status: NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT" in index_output
    _assert_no_forbidden_output(index_output)

    health_output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    assert "health_status: PASS" in health_output
    assert "issue_count: 0" in health_output
    _assert_no_forbidden_output(health_output)

    status_output = _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)
    assert "latest_runtime_status: NO_CSV_STRUCTURAL_FILE_TOUCH_INPUT" in status_output
    assert "latest_health_status: PASS" in status_output
    assert "file_touch_level: FILE_TOUCH_NONE" in status_output
    assert "csv_read_level: CSV_READ_NONE" in status_output
    assert "real_csv_consumed: False" in status_output
    assert f"recommended_next_task: {EXPECTED_NEXT_TASK}" in status_output
    assert "row-count" not in status_output.lower()
    assert "file-hash" not in status_output.lower()
    assert "package candidate" in status_output
    _assert_no_forbidden_output(status_output)


def test_cli_does_not_create_protected_paths(tmp_path: Path, capsys) -> None:
    _run_cli([COMMAND, "--output-root", str(_root(tmp_path))], capsys)

    assert not Path("docs/project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _assert_no_forbidden_output(output: str) -> None:
    for token in [
        "ACTIVE_REPLAY_INPUT_READY",
        "READY_FOR_REPLAY",
        "TRADING_READY",
        "BUY_REVIEW_READY",
        "PACKAGE_APPROVED",
        "PACKAGE_ADMISSIBLE",
        "PERFORMANCE_VALIDATED",
    ]:
        assert token not in output
