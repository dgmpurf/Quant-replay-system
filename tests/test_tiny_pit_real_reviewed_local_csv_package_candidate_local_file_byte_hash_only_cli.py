from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_local_file_byte_hash_only import (
    CSV_READ_NONE,
    LOCAL_FILE_BYTE_HASH_ONLY,
    LOCAL_FILE_BYTE_HASH_SHA256_ONLY,
    REQUIRED_FALSE_FLAGS,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-local-file-byte-hash-only"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Local File Byte-Hash-Only "
    "Research-Status Planning Report-Only v0.1"
)
SENTINEL = "SENTINEL_BYTE_HASH_CLI_ROW_VALUE_DO_NOT_PRINT"
FORBIDDEN_OUTPUT = [
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
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "local_file_byte_hash_only"


def _run_cli(args: list[str], capsys, *, expected_code: int = 0) -> str:
    code = cli.main(args)
    output = capsys.readouterr()
    assert code == expected_code, output.err
    assert output.err == ""
    return output.out


def _write_csv(path: Path) -> tuple[Path, bytes]:
    payload = (
        b"symbol,signal_date,review_note\n"
        + b"000001,2024-04-02,"
        + SENTINEL.encode("utf-8")
        + b"\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path, payload


def _manifest(csv_path: Path | str) -> dict[str, object]:
    return {
        "package_id": "tiny-pit-real-reviewed-local-csv-byte-hash-cli-001",
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
        "limitations": ["Byte-hash-only CLI fixture; no CSV parsing."],
    }


def _write_manifest(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_hash_artifact(tmp_path: Path, capsys, run_id: str = "cli_hash") -> tuple[Path, str, Path, str]:
    root = _root(tmp_path)
    csv_path, payload = _write_csv(tmp_path / "allowed" / f"{run_id}.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / f"{run_id}.json", _manifest(csv_path))
    output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            run_id,
            "--package-manifest-path",
            str(manifest_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-local-file-byte-hash-only",
        ],
        capsys,
    )
    _assert_no_forbidden_output(output)
    return root, hashlib.sha256(payload).hexdigest(), csv_path, output


def test_cli_command_names_are_registered(capsys) -> None:
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        with pytest.raises(SystemExit) as exc_info:
            cli.main([command, "--help"])
        output = capsys.readouterr()

        assert exc_info.value.code == 0
        assert command in output.out


def test_core_help_excludes_direct_csv_package_replay_and_trading_flags(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for expected in [
        "--package-manifest-path",
        "--allowed-manifest-root",
        "--allow-local-file-byte-hash-only",
        "--output-root",
        "--run-id",
    ]:
        assert expected in output
    for forbidden in [
        "--csv-path",
        "--direct-csv-path",
        "--file-path",
        "--package-root",
        "--reviewed-csv-path",
        "--allow-row-count",
        "--allow-header-read",
        "--allow-full-content",
        "--source-reliability",
        "--reviewer-authority",
        "--pit-validator",
        "--replay-input",
        "--active-input",
        "--trading",
        "automatic discovery",
    ]:
        assert forbidden not in output


def test_core_no_input_cli_writes_safe_artifact(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    assert "runtime_status: NO_LOCAL_FILE_BYTE_HASH_INPUT" in output
    assert "file_touch_level: FILE_TOUCH_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "local_file_hash_level: LOCAL_FILE_HASH_NONE" in output
    assert "local_file_byte_hash_computed: False" in output
    assert "real_csv_consumed: False" in output
    assert "csv_header_read: False" in output
    assert "csv_row_count_computed: False" in output
    assert "csv_values_read: False" in output
    assert "csv_full_content_read: False" in output
    assert "trading_allowed: False" in output
    assert "buy_review_allowed: False" in output
    assert EXPECTED_NEXT_TASK in output
    _assert_no_forbidden_output(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_core_hash_only_cli_prints_preview_only_and_stores_full_hash_in_metadata(tmp_path: Path, capsys) -> None:
    root, full_hash, _, output = _build_hash_artifact(tmp_path, capsys)
    metadata = json.loads((root / "cli_hash" / "metadata.json").read_text(encoding="utf-8"))

    assert "runtime_status: LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY" in output
    assert "file_touch_level: LOCAL_FILE_BYTE_HASH_ONLY" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "local_file_hash_level: LOCAL_FILE_BYTE_HASH_SHA256_ONLY" in output
    assert f"local_file_byte_hash_preview: {full_hash[:16]}" in output
    assert full_hash not in output
    assert metadata["local_file_byte_hash_value"] == full_hash
    assert SENTINEL not in output


def test_core_cli_rejects_missing_allow_flag_and_protected_manifest_reference(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    csv_path, _ = _write_csv(tmp_path / "allowed" / "reviewed.csv")
    manifest_path = _write_manifest(tmp_path / "allowed" / "manifest.json", _manifest(csv_path))

    missing_allow = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "missing_allow",
            "--package-manifest-path",
            str(manifest_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
        ],
        capsys,
        expected_code=1,
    )
    assert "runtime_status: LOCAL_FILE_BYTE_HASH_BLOCKED_BY_MISSING_ALLOW_FLAG" in missing_allow
    assert "local_file_byte_hash_computed: False" in missing_allow

    protected_manifest = _write_manifest(
        tmp_path / "allowed" / "protected.json",
        _manifest("data/raw/reviewed.csv"),
    )
    protected = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "protected",
            "--package-manifest-path",
            str(protected_manifest),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-local-file-byte-hash-only",
        ],
        capsys,
        expected_code=1,
    )
    assert "runtime_status: LOCAL_FILE_BYTE_HASH_BLOCKED_BY_PATH_GUARD" in protected
    assert "local_file_byte_hash_computed: False" in protected


def test_index_health_status_cli_use_preview_only_and_survive_deleted_target_csv(tmp_path: Path, capsys) -> None:
    root, full_hash, csv_path, _ = _build_hash_artifact(tmp_path, capsys)
    csv_path.unlink()

    index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli_hash" in index_output
    assert "latest_runtime_status: LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY" in index_output
    assert full_hash not in index_output

    health_output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    assert "health_status: PASS" in health_output
    assert "issue_count: 0" in health_output
    assert full_hash not in health_output

    status_output = _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)
    assert "latest_runtime_status: LOCAL_FILE_BYTE_HASH_ONLY_REPORT_ONLY" in status_output
    assert "latest_health_status: PASS" in status_output
    assert "latest_file_touch_level: LOCAL_FILE_BYTE_HASH_ONLY" in status_output
    assert "latest_csv_read_level: CSV_READ_NONE" in status_output
    assert "latest_local_file_hash_level: LOCAL_FILE_BYTE_HASH_SHA256_ONLY" in status_output
    assert f"latest_local_file_byte_hash_preview: {full_hash[:16]}" in status_output
    assert "latest_csv_header_read: False" in status_output
    assert "latest_csv_row_count_computed: False" in status_output
    assert "latest_csv_values_read: False" in status_output
    assert "latest_csv_full_content_read: False" in status_output
    assert "latest_real_csv_consumed: False" in status_output
    assert "latest_active_replay_input: False" in status_output
    assert "latest_trading_allowed: False" in status_output
    assert "latest_buy_review_allowed: False" in status_output
    assert EXPECTED_NEXT_TASK in status_output
    assert full_hash not in status_output
    for output in [index_output, health_output, status_output]:
        _assert_no_forbidden_output(output)


def test_cli_smoke_from_temp_working_dir_for_all_four_commands(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root, _, csv_path, _ = _build_hash_artifact(tmp_path, capsys, run_id="cwd_hash")
    csv_path.unlink()

    _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)


def test_cli_does_not_create_protected_paths(tmp_path: Path, capsys) -> None:
    _run_cli([COMMAND, "--output-root", str(_root(tmp_path)), "--run-id", "safe"], capsys)

    assert not Path("docs/project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _assert_no_forbidden_output(output: str) -> None:
    for token in FORBIDDEN_OUTPUT:
        assert token not in output
