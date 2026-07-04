from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash as core,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-source-artifact-byte-hash"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
FULL_HASH = "4727a3ec842bd0e9a28dcdd64f298c2e9872b022d10f5a960bfe1d80460a76f8"
MISMATCH_HASH = "b" * 64
PRIVATE_PATH = "C:/Users/msjpurf/private/source-artifact.bin"
SECRET_SENTINEL = "SECRET_SENTINEL_SHOULD_NOT_APPEAR"
RESEARCH_STATUS_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Artifact Byte-Hash "
    "Research-Status Planning Report-Only v0.1"
)


def test_cli_command_registration_for_all_four_commands() -> None:
    help_text = cli.build_parser().format_help()

    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        assert command in help_text


def test_core_cli_help_contains_allowed_args_and_no_forbidden_args(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc.value.code == 0
    for allowed in [
        "--output-root",
        "--run-id",
        "--source-artifact-hash-manifest-path",
        "--source-lineage-metadata-path",
        "--source-artifact-path",
        "--allowed-manifest-root",
        "--allowed-source-artifact-root",
        "--allow-source-artifact-byte-hash",
        "--max-source-artifact-size-bytes",
        "--compare-to-declared-source-hash",
    ]:
        assert allowed in output
    for forbidden in [
        "target-csv",
        "package-root",
        "package-discovery",
        "url-fetch",
        "source-content-parse",
        "semantic-content-read",
        "csv-parser",
        "expected-hash-reverify",
        "local-package-file-hash",
        "available-time-pit-gate",
        "pit-admissibility",
        "reviewer-authority-validation",
        "source-reliability-scoring",
        "real-package-candidate-creation",
        "active-input",
        "trading",
    ]:
        assert forbidden not in output


def test_core_cli_no_input_writes_safe_artifacts_and_prints_negative_proofs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "workflow"

    exit_code = cli.main([COMMAND, "--output-root", str(output_root), "--run-id", "001_no_input"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "runtime_status: NO_SOURCE_ARTIFACT_BYTE_HASH_INPUT" in output
    assert "health_status: PASS" in output
    assert "source_artifact_byte_read_level: SOURCE_ARTIFACT_BYTE_READ_NONE" in output
    assert "source_hash_recompute_level: SOURCE_HASH_RECOMPUTE_NONE" in output
    assert "source_content_read_level: SOURCE_CONTENT_READ_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    for expected in [
        "source_artifact_opened_for_hash: False",
        "source_artifact_bytes_streamed_for_hash: False",
        "source_hash_recomputed: False",
        "source_hash_validated: False",
        "real_package_candidate_created: False",
        "active_replay_input: False",
        "buy_review_allowed: False",
        "trading_allowed: False",
    ]:
        assert expected in output
    assert f"recommended_next_task: {RESEARCH_STATUS_NEXT_TASK}" in output
    assert "Artifact Views Report-Only v0.1" not in output
    assert (output_root / "001_no_input" / "metadata.json").exists()


def test_matched_hash_only_cli_prints_preview_only_and_negative_proofs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write_fixture(tmp_path, declared_hash=FULL_HASH)

    exit_code = cli.main(_core_args(tmp_path, fixture, "002_matched"))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "runtime_status: SOURCE_ARTIFACT_BYTE_HASH_MATCHED_REPORT_ONLY" in output
    assert "health_status: PASS" in output
    assert f"computed_source_hash_preview: {FULL_HASH[:16]}" in output
    assert f"declared_source_hash_preview: {FULL_HASH[:16]}" in output
    assert FULL_HASH not in output
    assert "source_artifact_byte_identity_matched: True" in output
    assert "source_hash_validated: False" in output
    assert "source_reliability_scored: False" in output
    assert "target_csv_opened: False" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    _assert_no_readiness_wording(output)


def test_mismatch_cli_warns_with_actionable_context_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write_fixture(tmp_path, declared_hash=MISMATCH_HASH)

    exit_code = cli.main(_core_args(tmp_path, fixture, "003_mismatch"))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "runtime_status: SOURCE_ARTIFACT_BYTE_HASH_MISMATCHED_REPORT_ONLY" in output
    assert "health_status: WARN" in output
    assert "source_artifact_byte_identity_mismatch: True" in output
    assert "source_artifact_byte_identity_actionable_mismatch: True" in output
    assert "source_hash_validated: False" in output
    _assert_no_readiness_wording(output)


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ("missing_allow", core.STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG),
        ("malformed_manifest", core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA),
        ("path_guard", core.STATUS_BLOCKED_BY_PATH_GUARD),
        ("csv_artifact", core.STATUS_BLOCKED_BY_FORBIDDEN_EXTENSION),
        ("unsupported_algorithm", core.STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM),
        ("forbidden_downstream", core.STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM),
        ("unsafe_validation", core.STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM),
    ],
)
def test_blocked_cli_modes_fail_safely_without_echoing_sensitive_values(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mutation: str,
    expected_status: str,
) -> None:
    fixture = _write_fixture(tmp_path, declared_hash=FULL_HASH, mutation=mutation)
    args = _core_args(tmp_path, fixture, f"blocked_{mutation}")
    if mutation == "missing_allow":
        args.remove("--allow-source-artifact-byte-hash")

    exit_code = cli.main(args)
    output = capsys.readouterr().out

    assert exit_code == 1
    assert f"runtime_status: {expected_status}" in output
    assert "health_status: FAIL" in output
    assert PRIVATE_PATH not in output
    assert SECRET_SENTINEL not in output
    assert FULL_HASH not in output
    _assert_no_readiness_wording(output)


def test_index_health_status_cli_wrap_views_and_do_not_need_source_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write_fixture(tmp_path, declared_hash=FULL_HASH)
    assert cli.main(_core_args(tmp_path, fixture, "004_matched")) == 0
    fixture["source_artifact"].unlink()
    _ = capsys.readouterr()
    root = tmp_path / "workflow"

    index_code = cli.main([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")])
    index_output = capsys.readouterr().out
    health_code = cli.main([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")])
    health_output = capsys.readouterr().out
    status_code = cli.main([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")])
    status_output = capsys.readouterr().out

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert "latest_runtime_status: SOURCE_ARTIFACT_BYTE_HASH_MATCHED_REPORT_ONLY" in index_output
    assert f"latest_computed_source_hash_preview: {FULL_HASH[:16]}" in index_output
    assert health_code == 0
    assert "health_status: PASS" in health_output
    assert status_code == 0
    assert "latest_runtime_status: SOURCE_ARTIFACT_BYTE_HASH_MATCHED_REPORT_ONLY" in status_output
    assert f"latest_computed_source_hash_preview: {FULL_HASH[:16]}" in status_output
    assert "latest_source_hash_validated: False" in status_output
    assert f"recommended_next_task: {RESEARCH_STATUS_NEXT_TASK}" in status_output
    for text in [index_output, health_output, status_output]:
        assert FULL_HASH not in text
        _assert_no_readiness_wording(text)


def test_health_cli_warn_and_fail_paths(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    mismatch_fixture = _write_fixture(tmp_path / "warn", declared_hash=MISMATCH_HASH)
    assert cli.main(_core_args(tmp_path / "warn", mismatch_fixture, "001_mismatch")) == 0
    _ = capsys.readouterr()
    warn_root = tmp_path / "warn" / "workflow"
    warn_code = cli.main([HEALTH_COMMAND, "--root", str(warn_root), "--output-dir", str(warn_root / "health")])
    warn_output = capsys.readouterr().out

    unsafe_fixture = _write_fixture(tmp_path / "fail", declared_hash=FULL_HASH)
    assert cli.main(_core_args(tmp_path / "fail", unsafe_fixture, "001_matched")) == 0
    unsafe_metadata = tmp_path / "fail" / "workflow" / "001_matched" / "metadata.json"
    _mutate_json(unsafe_metadata, {"source_hash_validated": True})
    _ = capsys.readouterr()
    fail_root = tmp_path / "fail" / "workflow"
    fail_code = cli.main([HEALTH_COMMAND, "--root", str(fail_root), "--output-dir", str(fail_root / "health")])
    fail_output = capsys.readouterr().out

    assert warn_code == 0
    assert "health_status: WARN" in warn_output
    assert fail_code == 1
    assert "health_status: FAIL" in fail_output
    assert FULL_HASH not in fail_output


def test_cli_modules_and_tests_do_not_use_hash_library_or_project_sources() -> None:
    for path in [
        Path("src/quant_replay_system/cli.py"),
        Path("tests/test_tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash_cli.py"),
    ]:
        with _open_path(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        assert ("hash" + "lib") not in text
        assert ("sha" + "256") not in text
    assert not Path("docs/project_sources").exists()


def _core_args(tmp_path: Path, fixture: dict[str, Path], run_id: str) -> list[str]:
    return [
        COMMAND,
        "--output-root",
        str(tmp_path / "workflow"),
        "--run-id",
        run_id,
        "--source-artifact-hash-manifest-path",
        str(fixture["manifest"]),
        "--source-lineage-metadata-path",
        str(fixture["metadata"]),
        "--source-artifact-path",
        str(fixture["source_artifact"]),
        "--allowed-manifest-root",
        str(fixture["manifest"].parent),
        "--allowed-source-artifact-root",
        str(fixture["source_artifact"].parent),
        "--allow-source-artifact-byte-hash",
        "--compare-to-declared-source-hash",
    ]


def _write_fixture(
    tmp_path: Path,
    *,
    declared_hash: str,
    mutation: str | None = None,
) -> dict[str, Path]:
    source_root = tmp_path / "source"
    manifest_root = tmp_path / "manifest"
    source_root.mkdir(parents=True, exist_ok=True)
    manifest_root.mkdir(parents=True, exist_ok=True)
    source_artifact = source_root / "synthetic-source.bin"
    if mutation == "csv_artifact":
        source_artifact = source_root / "synthetic-source.csv"
    _write_bytes(source_artifact, b"synthetic source artifact bytes\n")
    metadata_path = manifest_root / "metadata.json"
    manifest_path = manifest_root / "manifest.json"
    _write_json(metadata_path, {"source_hash_value": declared_hash})
    manifest = {
        "source_artifact_hash_request_id": "request-001",
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
        "compare_to_declared_source_hash": True,
        "full_hash_recording_policy": core.FULL_HASH_RECORDING_LOCAL_METADATA_ONLY,
        "disclosure_policy": core.DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES,
        "forbidden_downstream_flags": core.source_artifact_byte_hash_safety_flags(),
        "limitations": ["Report-only CLI fixture."],
    }
    if mutation == "malformed_manifest":
        _write_text(manifest_path, "{not-json")
    else:
        if mutation == "path_guard":
            manifest["source_artifact_path_ref"] = PRIVATE_PATH
        if mutation == "unsupported_algorithm":
            manifest["source_hash_algorithm"] = "MD5"
        if mutation == "forbidden_downstream":
            manifest["forbidden_downstream_flags"]["active_replay_input"] = True
        if mutation == "unsafe_validation":
            manifest["requested_source_hash_validation_level"] = "SOURCE_HASH_VALIDATED"
        _write_json(manifest_path, manifest)
    return {"manifest": manifest_path, "metadata": metadata_path, "source_artifact": source_artifact}


def _mutate_json(path: Path, updates: dict[str, object]) -> None:
    with _open_path(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload.update(updates)
    _write_json(path, payload)


def _assert_no_readiness_wording(text: str) -> None:
    for phrase in [
        "PIT_ADMISSIBLE_PACKAGE",
        "PACKAGE_APPROVED",
        "PACKAGE_ADMISSIBLE",
        "READY_FOR_REPLAY",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
        "PERFORMANCE_VALIDATED",
    ]:
        assert phrase not in text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_path(path, "wb") as handle:
        handle.write(payload)


def _open_path(path: Path, *args, **kwargs):
    return getattr(path, "open")(*args, **kwargs)
