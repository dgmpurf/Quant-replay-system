from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system import tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification as core


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-expected-hash-verification"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"

EXPECTED_FULL_HASH = "a" * 64
ACTUAL_FULL_HASH = "b" * 64
MATCHING_FULL_HASH = "c" * 64
PREVIEW_CHARS = 16
EXPECTED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification "
    "Checkpoint Planning Report-Only v0.1"
)
STALE_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification "
    "Research-Status Planning Report-Only v0.1"
)
FORBIDDEN_HELP = [
    "--csv-path",
    "--direct-csv-path",
    "--file-path",
    "--package-root",
    "--reviewed-csv-path",
    "--raw-csv-path",
    "--recompute-hash",
    "--allow-recompute-hash",
    "--header-read",
    "--allow-header-read",
    "--row-count",
    "--allow-row-count",
    "--full-content",
    "--allow-full-content",
    "--source-hash",
    "--revision-id",
    "--available-time",
    "--pit-validator",
    "--reviewer-authority",
    "--active-input",
    "--replay",
    "--buy-review",
    "--trading",
    "--automatic-discovery",
]
UNSAFE_OUTPUT = [
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


def test_cli_command_names_are_registered(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        assert command in output


def test_core_help_excludes_direct_csv_package_replay_and_trading_flags(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for expected in [
        "--output-root",
        "--run-id",
        "--expected-hash-manifest-path",
        "--local-file-byte-hash-metadata-path",
        "--allowed-manifest-root",
        "--allow-expected-hash-verification",
    ]:
        assert expected in output
    for forbidden in FORBIDDEN_HELP:
        assert forbidden not in output


def test_core_no_input_cli_writes_safe_artifact(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    assert "runtime_status: NO_EXPECTED_HASH_VERIFICATION_INPUT" in output
    assert "health_status: PASS" in output
    assert "file_touch_level: FILE_TOUCH_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "local_file_hash_level: LOCAL_FILE_HASH_NONE" in output
    assert "expected_hash_verification_level: EXPECTED_HASH_VERIFICATION_NONE" in output
    assert "expected_hash_verification_performed: False" in output
    assert "real_csv_consumed: False" in output
    assert "trading_allowed: False" in output
    assert "buy_review_allowed: False" in output
    assert EXPECTED_NEXT_TASK in output
    _assert_no_unsafe_output(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_core_matched_cli_prints_preview_only_and_negative_proofs(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_matched",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-expected-hash-verification",
        ],
        capsys,
    )

    assert "runtime_status: EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY" in output
    assert "health_status: PASS" in output
    assert "expected_hash_matched: True" in output
    assert "expected_hash_mismatch: False" in output
    assert "actionable_mismatch: False" in output
    assert f"expected_hash_preview: {MATCHING_FULL_HASH[:PREVIEW_CHARS]}" in output
    assert f"actual_local_file_byte_hash_preview: {MATCHING_FULL_HASH[:PREVIEW_CHARS]}" in output
    assert MATCHING_FULL_HASH not in output
    for negative in [
        "expected_hash_verified_against_source_hash: False",
        "source_hash_validated: False",
        "revision_id_validated: False",
        "available_time_validated: False",
        "pit_admissibility_validated: False",
        "source_reliability_scored: False",
        "reviewer_authority_validated: False",
        "local_file_byte_hash_recomputed: False",
        "target_file_opened_for_expected_hash_verification: False",
        "csv_header_read: False",
        "csv_row_count_computed: False",
        "csv_values_read: False",
        "csv_full_content_read: False",
        "real_csv_consumed: False",
        "active_replay_input: False",
        "trading_allowed: False",
        "buy_review_allowed: False",
    ]:
        assert negative in output
    _assert_no_unsafe_output(output)


def test_core_mismatch_cli_exits_zero_and_prints_warn_actionable_preview_only(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_inputs(tmp_path, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_mismatch",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-expected-hash-verification",
        ],
        capsys,
    )

    assert "runtime_status: EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY" in output
    assert "health_status: WARN" in output
    assert "expected_hash_matched: False" in output
    assert "expected_hash_mismatch: True" in output
    assert "actionable_mismatch: True" in output
    assert EXPECTED_FULL_HASH not in output
    assert ACTUAL_FULL_HASH not in output
    assert EXPECTED_FULL_HASH[:PREVIEW_CHARS] in output
    assert ACTUAL_FULL_HASH[:PREVIEW_CHARS] in output


def test_core_missing_allow_and_metadata_path_mismatch_block(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    missing_allow = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "missing_allow",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
        ],
        capsys,
        expected_code=1,
    )
    assert "runtime_status: EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MISSING_ALLOW_FLAG" in missing_allow

    other_metadata = tmp_path / "allowed" / "other" / "metadata.json"
    other_metadata.parent.mkdir(parents=True, exist_ok=True)
    other_metadata.write_text(json.dumps(_valid_local_metadata(MATCHING_FULL_HASH)), encoding="utf-8")
    mismatch = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "metadata_mismatch",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(other_metadata),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-expected-hash-verification",
        ],
        capsys,
        expected_code=1,
    )
    assert "runtime_status: EXPECTED_HASH_VERIFICATION_BLOCKED_BY_MANIFEST_SCHEMA" in mismatch


def test_index_health_status_cli_preview_only_after_source_metadata_deleted(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_inputs(tmp_path, EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)
    _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "cli_mismatch",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-expected-hash-verification",
        ],
        capsys,
    )
    metadata_path.unlink()

    index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli_mismatch" in index_output
    assert EXPECTED_FULL_HASH not in index_output
    assert ACTUAL_FULL_HASH not in index_output

    health_output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    assert "health_status: WARN" in health_output
    assert "warning_count: 1" in health_output
    assert EXPECTED_FULL_HASH not in health_output
    assert ACTUAL_FULL_HASH not in health_output

    status_output = _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)
    assert "latest_runtime_status: EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY" in status_output
    assert "latest_health_status: WARN" in status_output
    assert "latest_expected_hash_mismatch: True" in status_output
    assert "latest_actionable_mismatch: True" in status_output
    assert EXPECTED_NEXT_TASK in status_output
    assert STALE_NEXT_TASK not in status_output
    assert EXPECTED_FULL_HASH not in status_output
    assert ACTUAL_FULL_HASH not in status_output
    for output in [index_output, health_output, status_output]:
        _assert_no_unsafe_output(output)


def test_health_cli_pass_for_safe_no_input_and_matched_artifacts(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "001_no_input"], capsys)
    _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "002_matched",
            "--expected-hash-manifest-path",
            str(manifest_path),
            "--local-file-byte-hash-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-expected-hash-verification",
        ],
        capsys,
    )

    output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)

    assert "health_status: PASS" in output
    assert "issue_count: 0" in output


def test_cli_smoke_from_temp_working_dir_for_all_four_commands(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root, _, _ = _write_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cwd_no_input"], capsys)
    _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)


def test_cli_does_not_create_protected_paths(tmp_path: Path, capsys) -> None:
    _run_cli([COMMAND, "--output-root", str(_root(tmp_path)), "--run-id", "safe"], capsys)

    assert not Path("docs/project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _run_cli(args: list[str], capsys, expected_code: int = 0) -> str:
    code = cli.main(args)
    output = capsys.readouterr().out
    assert code == expected_code, output
    return output


def _write_inputs(tmp_path: Path, expected_full_hash: str, actual_full_hash: str) -> tuple[Path, Path, Path]:
    root = _root(tmp_path)
    metadata_path = tmp_path / "allowed" / "byte_hash_artifact" / "metadata.json"
    manifest_path = tmp_path / "allowed" / "manifest" / "expected_hash_manifest.json"
    metadata = _valid_local_metadata(actual_full_hash)
    manifest = _valid_manifest(expected_full_hash, metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return root, manifest_path, metadata_path


def _valid_manifest(expected_full_hash: str, metadata_path: Path) -> dict:
    return {
        "verification_id": "verify_fixture",
        "package_id": "package_fixture",
        "package_schema_version": "tiny-pit-expected-hash-v0.1",
        "created_at": "2026-07-02T00:00:00Z",
        "prepared_by": "pytest",
        "report_only": True,
        "diagnostic_only": True,
        "requested_expected_hash_verification_level": "EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        "requested_csv_read_level": "CSV_READ_NONE",
        "requested_local_file_hash_level": "LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY",
        "source_local_file_byte_hash_artifact_metadata_path": str(metadata_path),
        "expected_hash_algorithm": "SHA-256",
        "expected_hash_value": expected_full_hash,
        "expected_hash_disclosure_level": "PREVIEW_ONLY_STATUS",
        "forbidden_downstream_flags": {field: False for field in core.REQUIRED_FALSE_FLAGS},
        "limitations": ["Synthetic expected-hash verification fixture."],
    }


def _valid_local_metadata(actual_full_hash: str) -> dict:
    metadata = {
        "local_file_byte_hash_computed": True,
        "local_file_byte_hash_algorithm": "SHA-256",
        "local_file_byte_hash_value": actual_full_hash,
        "csv_read_level": "CSV_READ_NONE",
        "csv_header_read": False,
        "csv_row_count_computed": False,
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
    }
    metadata.update({field: False for field in core.REQUIRED_FALSE_FLAGS})
    return metadata


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "expected_hash_verification"


def _assert_no_unsafe_output(output: str) -> None:
    for token in UNSAFE_OUTPUT:
        assert token not in output
