from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from quant_replay_system import cli
from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time as core,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-source-hash-revision-available-time"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
FULL_SOURCE_HASH = "a" * 64
SOURCE_HASH_PREVIEW = "a" * 16
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SENTINEL_SHOULD_NOT_PRINT"
TARGET_CSV_SENTINEL = "TARGET_CSV_SENTINEL_SHOULD_NOT_PRINT"
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/source.csv"
CLI_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time Research-Status Planning Report-Only v0.1"
)
STALE_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Source Hash Revision "
    "Available-Time CLI Report-Only v0.1"
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
FORBIDDEN_HELP = [
    "--direct-csv-path",
    "--target-csv-path",
    "--csv-path",
    "--source-artifact-path",
    "--source-bytes-path",
    "--package-root",
    "--source-hash-recompute",
    "--recompute-source-hash",
    "--local-file-hash-recompute",
    "--recompute-local-file-hash",
    "--expected-hash-reverify",
    "--reverify-expected-hash",
    "--pit-gate",
    "--decision-time-validation",
    "--reviewer-authority",
    "--source-reliability-score",
    "--real-package-candidate",
    "--active-input",
    "--replay",
    "--trading",
    "--automatic-discovery",
]


def test_cli_command_registration_for_all_four_commands(capsys) -> None:
    for command in [COMMAND, INDEX_COMMAND, HEALTH_COMMAND, STATUS_COMMAND]:
        with pytest.raises(SystemExit) as exc_info:
            cli.main([command, "--help"])
        output = capsys.readouterr().out

        assert exc_info.value.code == 0
        assert command in output


def test_core_cli_no_input_exits_zero_and_writes_safe_artifacts(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)

    code, output = _run_cli([COMMAND, "--output-root", str(root), "--run-id", "cli_no_input"], capsys)

    assert code == 0
    assert "runtime_status: NO_SOURCE_REVISION_TIME_INPUT" in output
    assert "health_status: PASS" in output
    assert "source_hash_validation_level: SOURCE_HASH_VALIDATION_NONE" in output
    assert "revision_id_validation_level: REVISION_ID_VALIDATION_NONE" in output
    assert "available_time_validation_level: AVAILABLE_TIME_VALIDATION_NONE" in output
    assert "pit_admissibility_level: PIT_ADMISSIBILITY_NONE" in output
    assert "report_only: True" in output
    assert "diagnostic_only: True" in output
    assert "source_hash_metadata_present: False" in output
    assert "revision_id_metadata_present: False" in output
    assert "available_time_metadata_present: False" in output
    _assert_negative_proofs(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_metadata_present_prints_preview_and_metadata_only(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    code, output = _run_metadata_cli(root, manifest_path, metadata_path, tmp_path, "cli_metadata", capsys)

    assert code == 0
    assert "runtime_status: SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY" in output
    assert "health_status: PASS" in output
    assert "source_hash_validation_level: SOURCE_HASH_METADATA_PRESENT_ONLY" in output
    assert "revision_id_validation_level: REVISION_ID_METADATA_PRESENT_ONLY" in output
    assert "available_time_validation_level: AVAILABLE_TIME_METADATA_PRESENT_ONLY" in output
    assert "pit_admissibility_level: PIT_ADMISSIBILITY_NONE" in output
    assert "source_hash_metadata_present: True" in output
    assert "source_hash_format_checked: True" in output
    assert "source_hash_algorithm_supported: True" in output
    assert "source_hash_algorithm: SHA-256" in output
    assert f"source_hash_preview: {SOURCE_HASH_PREVIEW}" in output
    assert "revision_id_metadata_present: True" in output
    assert "revision_id_type: provider_revision_id" in output
    assert "revision_id_type_supported: True" in output
    assert "available_time_metadata_present: True" in output
    assert "available_time_parseable: True" in output
    assert "available_time_timezone_present: True" in output
    assert "available_time_timezone_policy: Asia/Shanghai" in output
    assert "available_time_compared_to_decision_time: False" in output
    _assert_negative_proofs(output)
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_timezone_warning_exits_zero_and_does_not_validate_time(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(
        tmp_path,
        metadata_mutation=lambda metadata: metadata.update(
            {"available_time": "2024-04-02T09:30:00", "available_time_timezone": ""}
        ),
    )

    code, output = _run_metadata_cli(root, manifest_path, metadata_path, tmp_path, "timezone_warn", capsys)

    assert code == 0
    assert "runtime_status: SOURCE_REVISION_TIME_WARN_TIMEZONE_ASSUMPTION_REQUIRED" in output
    assert "health_status: WARN" in output
    assert "available_time_parseable: True" in output
    assert "available_time_timezone_present: False" in output
    assert "available_time_validated: False" in output
    assert "available_time_compared_to_decision_time: False" in output


def test_core_cli_blocked_cases_return_fail_style_output(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    missing_allow_code, missing_allow_output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "missing_allow",
            "--source-lineage-manifest-path",
            str(manifest_path),
            "--source-lineage-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
        ],
        capsys,
    )
    assert missing_allow_code != 0
    assert "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_ALLOW_FLAG" in missing_allow_output
    assert "health_status: FAIL" in missing_allow_output

    blocked_cases = [
        ("malformed_manifest", None, "{malformed", "SOURCE_REVISION_TIME_BLOCKED_BY_MANIFEST_SCHEMA"),
        ("protected_path", Path("data/raw/manifest.json"), None, "SOURCE_REVISION_TIME_BLOCKED_BY_PATH_GUARD"),
        (
            "unsupported_algorithm",
            None,
            lambda metadata: metadata.__setitem__("source_hash_algorithm", "MD5"),
            "SOURCE_REVISION_TIME_BLOCKED_BY_UNSUPPORTED_HASH_ALGORITHM",
        ),
        (
            "malformed_hash",
            None,
            lambda metadata: metadata.__setitem__("source_hash_value", "z" * 64),
            "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_SOURCE_HASH",
        ),
        (
            "missing_revision",
            None,
            lambda metadata: metadata.pop("revision_id"),
            "SOURCE_REVISION_TIME_BLOCKED_BY_MISSING_REVISION_ID",
        ),
        (
            "malformed_time",
            None,
            lambda metadata: metadata.__setitem__("available_time", "not-a-date"),
            "SOURCE_REVISION_TIME_BLOCKED_BY_MALFORMED_AVAILABLE_TIME",
        ),
    ]
    for run_id, manifest_override, mutation_or_text, expected_status in blocked_cases:
        case_root, case_manifest, case_metadata = _write_valid_inputs(tmp_path / run_id)
        if isinstance(mutation_or_text, str):
            _write_text(case_manifest, mutation_or_text)
        elif callable(mutation_or_text):
            metadata = _source_metadata()
            mutation_or_text(metadata)
            _write_json(case_metadata, metadata)
        if manifest_override is not None:
            case_manifest = manifest_override

        code, output = _run_metadata_cli(case_root, case_manifest, case_metadata, tmp_path / run_id, run_id, capsys)

        assert code != 0, run_id
        assert expected_status in output
        assert "health_status: FAIL" in output


def test_core_cli_help_contains_no_forbidden_args(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for allowed in [
        "--output-root",
        "--run-id",
        "--source-lineage-manifest-path",
        "--source-lineage-metadata-path",
        "--allowed-manifest-root",
        "--allow-source-revision-time-metadata",
    ]:
        assert allowed in output
    for forbidden in FORBIDDEN_HELP:
        assert forbidden not in output


def test_index_health_status_cli_after_source_metadata_deleted(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    code, output = _run_metadata_cli(root, manifest_path, metadata_path, tmp_path, "cli_metadata", capsys)
    assert code == 0
    manifest_path.unlink()
    metadata_path.unlink()

    index_code, index_output = _run_cli([INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")], capsys)
    health_code, health_output = _run_cli([HEALTH_COMMAND, "--root", str(root), "--output-dir", str(root / "health")], capsys)
    status_code, status_output = _run_cli([STATUS_COMMAND, "--root", str(root), "--output-dir", str(root / "status")], capsys)

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert "latest_run_id: cli_metadata" in index_output
    assert "latest_runtime_status: SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY" in index_output
    assert f"latest_source_hash_preview: {SOURCE_HASH_PREVIEW}" in index_output
    assert health_code == 0
    assert "health_status: PASS" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_metadata" in status_output
    assert "latest_runtime_status: SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY" in status_output
    assert "latest_source_hash_validation_level: SOURCE_HASH_METADATA_PRESENT_ONLY" in status_output
    assert "latest_revision_id_validation_level: REVISION_ID_METADATA_PRESENT_ONLY" in status_output
    assert "latest_available_time_validation_level: AVAILABLE_TIME_METADATA_PRESENT_ONLY" in status_output
    assert "latest_pit_admissibility_level: PIT_ADMISSIBILITY_NONE" in status_output
    assert f"latest_source_hash_preview: {SOURCE_HASH_PREVIEW}" in status_output
    assert "latest_revision_id_type: provider_revision_id" in status_output
    assert "latest_available_time_parseable: True" in status_output
    assert "latest_available_time_timezone_present: True" in status_output
    assert "latest_available_time_compared_to_decision_time: False" in status_output
    assert f"recommended_next_task: {CLI_NEXT_TASK}" in status_output
    assert STALE_NEXT_TASK not in status_output
    for output_text in [index_output, health_output, status_output]:
        _assert_no_disclosure(output_text)
        _assert_no_unsafe_wording(output_text)


def test_health_cli_warn_and_fail_paths(tmp_path: Path, capsys) -> None:
    warn_root, warn_manifest, warn_metadata = _write_valid_inputs(
        tmp_path / "warn",
        metadata_mutation=lambda metadata: metadata.update(
            {"available_time": "2024-04-02T09:30:00", "available_time_timezone": ""}
        ),
    )
    _run_metadata_cli(warn_root, warn_manifest, warn_metadata, tmp_path / "warn", "timezone_warn", capsys)
    warn_code, warn_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(warn_root), "--output-dir", str(warn_root / "health")],
        capsys,
    )
    assert warn_code == 0
    assert "health_status: WARN" in warn_output
    assert "warning_count: 1" in warn_output

    fail_root, fail_manifest, fail_metadata = _write_valid_inputs(tmp_path / "fail")
    artifact_code, _ = _run_metadata_cli(fail_root, fail_manifest, fail_metadata, tmp_path / "fail", "hash_leak", capsys)
    assert artifact_code == 0
    _write_text(fail_root / "hash_leak" / "source_revision_time_report.md", FULL_SOURCE_HASH)
    fail_code, fail_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(fail_root), "--output-dir", str(fail_root / "health")],
        capsys,
    )
    assert fail_code != 0
    assert "health_status: FAIL" in fail_output
    assert FULL_SOURCE_HASH not in fail_output


def test_cli_module_and_tests_do_not_import_forbidden_hash_module() -> None:
    for path in [Path(cli.__file__), Path(__file__)]:
        source = _read_text(path)
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        assert ("hash" + "lib") not in imported_modules


def test_docs_project_sources_not_created(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "docs_guard"], capsys)

    assert not Path("docs/project_sources").exists()


def _run_metadata_cli(
    root: Path,
    manifest_path: Path,
    metadata_path: Path,
    tmp_path: Path,
    run_id: str,
    capsys,
) -> tuple[int, str]:
    return _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            run_id,
            "--source-lineage-manifest-path",
            str(manifest_path),
            "--source-lineage-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-source-revision-time-metadata",
        ],
        capsys,
    )


def _run_cli(argv: list[str], capsys) -> tuple[int, str]:
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _write_valid_inputs(
    tmp_path: Path,
    *,
    metadata_mutation=None,
) -> tuple[Path, Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(parents=True, exist_ok=True)
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "source_revision_time_cli"
    metadata_path = allowed / "source_metadata.json"
    manifest_path = allowed / "manifest.json"
    metadata = _source_metadata()
    if metadata_mutation:
        metadata_mutation(metadata)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, _manifest(metadata_path))
    return root, manifest_path, metadata_path


def _manifest(metadata_path: Path) -> dict:
    return {
        "package_id": "pkg-source-revision-time",
        "package_schema_version": "source_revision_time_v0_1",
        "created_at": "2026-07-03T00:00:00Z",
        "prepared_by": "codex-test",
        "report_only": True,
        "diagnostic_only": True,
        "requested_source_hash_validation_level": "SOURCE_HASH_METADATA_PRESENT_ONLY",
        "requested_revision_id_validation_level": "REVISION_ID_METADATA_PRESENT_ONLY",
        "requested_available_time_validation_level": "AVAILABLE_TIME_METADATA_PRESENT_ONLY",
        "requested_pit_admissibility_level": "PIT_ADMISSIBILITY_NONE",
        "source_lineage_metadata_reference": {
            "path": str(metadata_path),
            "required": True,
            "reference_type": "source_lineage_metadata_ref",
            "intended_touch_level": "SOURCE_REVISION_TIME_METADATA_PRESENT_ONLY",
            "declared_only": False,
        },
        "source_hash_policy": "SOURCE_HASH_METADATA_PRESENT_ONLY",
        "revision_id_policy": "REVISION_ID_REQUIRED_METADATA_ONLY",
        "available_time_policy": "AVAILABLE_TIME_PARSEABILITY_ONLY",
        "timezone_policy": "TIMEZONE_REQUIRED_FOR_PASS",
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata shape only; no PIT admissibility validation."],
    }


def _source_metadata() -> dict:
    return {
        "source_id": "official_test_source",
        "source_name": "Official Test Source",
        "source_type": "official_public",
        "permission_class": "reviewed_local_metadata_only",
        "source_hash_algorithm": "SHA-256",
        "source_hash_value": FULL_SOURCE_HASH,
        "source_hash_disclosure_level": "PREVIEW_ONLY_STATUS",
        "revision_id": "provider-2024-04-02-v1",
        "revision_id_type": "provider_revision_id",
        "available_time": "2024-04-02T09:30:00+08:00",
        "available_time_timezone": "Asia/Shanghai",
        "available_time_policy": "available_time_metadata_present_only",
        "quality_status": "review_context_only",
        "manual_review_status": "review_context_only",
        "report_only": True,
        "diagnostic_only": True,
        "source_artifact_reference": PRIVATE_PATH_SENTINEL,
        "source_content_sample": SOURCE_CONTENT_SENTINEL,
        "target_csv_sample": TARGET_CSV_SENTINEL,
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata only."],
    }


def _false_flags() -> dict[str, bool]:
    return {
        field: False
        for field in [
            "source_hash_recomputed",
            "source_artifact_opened",
            "source_content_read",
            "local_file_hash_recomputed",
            "expected_hash_reverified",
            "target_csv_opened",
            "real_csv_consumed",
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
    }


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "source_revision_time_cli"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _assert_negative_proofs(output: str) -> None:
    for expected in [
        "source_hash_recomputed: False",
        "source_artifact_opened: False",
        "source_content_read: False",
        "local_file_hash_recomputed: False",
        "expected_hash_reverified: False",
        "target_csv_opened: False",
        "real_csv_consumed: False",
        "source_hash_validated: False",
        "revision_id_validated: False",
        "available_time_validated: False",
        "pit_admissibility_validated: False",
        "source_reliability_scored: False",
        "reviewer_authority_validated: False",
        "active_replay_input: False",
        "trading_allowed: False",
        "buy_review_allowed: False",
        "data_raw_written: False",
        "data_processed_written: False",
        "data_cache_written: False",
    ]:
        assert expected in output


def _assert_no_disclosure(output: str) -> None:
    for sentinel in [FULL_SOURCE_HASH, SOURCE_CONTENT_SENTINEL, TARGET_CSV_SENTINEL, PRIVATE_PATH_SENTINEL]:
        assert sentinel not in output


def _assert_no_unsafe_wording(output: str) -> None:
    for phrase in UNSAFE_WORDING:
        assert phrase not in output

