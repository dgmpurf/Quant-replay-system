from __future__ import annotations

import ast
import json
from pathlib import Path
from shutil import rmtree

import pytest

from quant_replay_system import cli
from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_preflight as core,
)


COMMAND = "tiny-pit-real-reviewed-local-csv-package-candidate-preflight"
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
RESEARCH_STATUS_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Research-Status "
    "Planning Report-Only v0.1"
)
STALE_CLI_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight CLI Report-Only v0.1"
)
FULL_HASH_SENTINEL = "0123456789abcdef" * 4
REVIEWER_SENTINEL = "private-reviewer-identity-should-not-print"
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/source.csv"
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SHOULD_NOT_PRINT"
TARGET_CSV_SENTINEL = "TARGET_CSV_SHOULD_NOT_PRINT"
HEADER_VALUE_SENTINEL = "HEADER_VALUE_SHOULD_NOT_PRINT"
ROW_VALUE_SENTINEL = "ROW_VALUE_SHOULD_NOT_PRINT"
FORBIDDEN_HELP = [
    "--direct-csv-path",
    "--target-csv-path",
    "--csv-path",
    "--source-artifact-path",
    "--source-bytes-path",
    "--source-content-path",
    "--package-root",
    "--source-hash-recompute",
    "--recompute-source-hash",
    "--local-file-hash-recompute",
    "--expected-hash-reverify",
    "--reverify-expected-hash",
    "--pit-gate",
    "--pit-admissibility",
    "--reviewer-authority-validation",
    "--source-reliability",
    "--quality-to-package-promotion",
    "--real-package-candidate",
    "--active-input",
    "--replay",
    "--trading",
]
UNSAFE_WORDING = [
    "REAL_PACKAGE_CANDIDATE_CREATED",
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "PERFORMANCE_VALIDATED",
]
NEGATIVE_FALSE_FIELDS = [
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "target_csv_opened",
    "source_artifact_opened",
    "source_content_read",
    "source_hash_recomputed",
    "local_file_hash_recomputed",
    "expected_hash_reverified",
    "available_time_compared_to_decision_time",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]
REQUIRED_REFERENCE_NAMES = [
    "csv_structural_header_metadata",
    "local_file_byte_hash_metadata",
    "expected_hash_verification_metadata",
    "csv_physical_data_line_count_metadata",
    "source_revision_time_metadata",
    "reviewer_quality_limitation_metadata",
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
    assert core.STATUS_NO_INPUT in output
    assert "health_status: PASS" in output
    assert "preflight_level: PREFLIGHT_NONE" in output
    assert "package_creation_level: PACKAGE_CREATION_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert f"recommended_next_task: {RESEARCH_STATUS_NEXT_TASK}" in output
    _assert_negative_proofs(output)
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_core_cli_metadata_context_prints_metadata_only_and_safe_counts(tmp_path: Path, capsys) -> None:
    root, manifest_path, refs = _write_valid_inputs(
        tmp_path,
        metadata_overrides={
            "source_revision_time_metadata": {
                "full_source_hash": FULL_HASH_SENTINEL,
                "private_path": PRIVATE_PATH_SENTINEL,
                "source_content_sample": SOURCE_CONTENT_SENTINEL,
            },
            "reviewer_quality_limitation_metadata": {
                "reviewer_id": REVIEWER_SENTINEL,
            },
            "csv_structural_header_metadata": {
                "target_csv_sample": TARGET_CSV_SENTINEL,
                "header_value_sample": HEADER_VALUE_SENTINEL,
            },
            "csv_physical_data_line_count_metadata": {
                "row_value_sample": ROW_VALUE_SENTINEL,
            },
        },
    )

    code, output = _run_metadata_cli(root, manifest_path, refs, tmp_path, "cli_metadata", capsys)

    assert code == 0
    assert core.STATUS_METADATA_CONTEXT_REPORT_ONLY in output
    assert "health_status: PASS" in output
    assert "declared_package_id: declared-package-001 (metadata only)" in output
    assert "preflight_level: REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_METADATA_REFERENCES_ONLY" in output
    assert "package_creation_level: PACKAGE_CREATION_NONE" in output
    assert "csv_read_level: CSV_READ_NONE" in output
    assert "required_reference_present_count: 6" in output
    assert "missing_required_reference_count: 0" in output
    assert "missing_optional_reference_count: 0" in output
    assert "real_package_candidate_created: False" in output
    assert "active_replay_input: False" in output
    assert "buy_review_allowed: False" in output
    assert "trading_allowed: False" in output
    _assert_negative_proofs(output)
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_warn_optional_evidence_exits_zero(tmp_path: Path, capsys) -> None:
    root, manifest_path, refs = _write_valid_inputs(tmp_path)
    refs["metadata_reference_following_metadata_path"] = (
        tmp_path / "allowed" / "metadata" / "missing_optional.json"
    )

    code, output = _run_metadata_cli(root, manifest_path, refs, tmp_path, "optional_warn", capsys)

    assert code == 0
    assert core.STATUS_WARN_MISSING_OPTIONAL_EVIDENCE in output
    assert "health_status: WARN" in output
    assert "missing_optional_reference_count: 1" in output
    _assert_negative_proofs(output)


def test_core_cli_blocked_cases_return_nonzero_and_safe_output(tmp_path: Path, capsys) -> None:
    root, manifest_path, refs = _write_valid_inputs(tmp_path)
    missing_allow_code, missing_allow_output = _run_cli(
        [
            COMMAND,
            "--output-root",
            str(root),
            "--run-id",
            "missing_allow",
            "--preflight-manifest-path",
            str(manifest_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            *(_metadata_args(refs)),
        ],
        capsys,
    )
    assert missing_allow_code != 0
    assert core.STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG in missing_allow_output

    cases = [
        ("malformed", lambda case: _write_text(case["manifest"], "{malformed"), core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA),
        (
            "protected",
            lambda case: case.__setitem__("manifest", Path("data/raw/preflight_manifest.json")),
            core.STATUS_BLOCKED_BY_PATH_GUARD,
        ),
        (
            "missing_required",
            lambda case: (
                case["refs"].pop("source_revision_time_metadata_path").unlink(),
            ),
            core.STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA,
        ),
        (
            "unsafe_validation",
            lambda case: _update_reference(
                case["refs"]["source_revision_time_metadata_path"],
                {"source_hash_validated": True},
            ),
            core.STATUS_BLOCKED_BY_UNSUPPORTED_VALIDATION_CLAIM,
        ),
        (
            "forbidden_downstream",
            lambda case: _mutate_manifest(
                case["manifest"],
                lambda manifest: manifest["forbidden_downstream_flags"].update({"active_replay_input": True}),
            ),
            core.STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        ),
        (
            "reviewer_block",
            lambda case: _update_reference(
                case["refs"]["reviewer_quality_limitation_metadata_path"],
                {
                    "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION",
                    "health_status": "FAIL",
                    "limitation_severity_max": "BLOCKER",
                },
            ),
            core.STATUS_BLOCKED_BY_REVIEWER_QUALITY_LIMITATION,
        ),
        (
            "permission_block",
            lambda case: _update_reference(
                case["refs"]["reviewer_quality_limitation_metadata_path"],
                {
                    "runtime_status": "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION",
                    "health_status": "FAIL",
                    "permission_class": "restricted",
                },
            ),
            core.STATUS_BLOCKED_BY_PERMISSION,
        ),
    ]
    for run_id, mutation, expected_status in cases:
        case_root, case_manifest, case_refs = _write_valid_inputs(tmp_path / run_id)
        case = {"manifest": case_manifest, "refs": case_refs}
        mutation(case)

        code, output = _run_metadata_cli(case_root, case["manifest"], case["refs"], tmp_path / run_id, run_id, capsys)

        assert code != 0, run_id
        assert expected_status in output
        assert "health_status: FAIL" in output
        _assert_no_disclosure(output)
        _assert_no_unsafe_wording(output)


def test_core_cli_help_contains_no_forbidden_args(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for allowed in [
        "--output-root",
        "--run-id",
        "--preflight-manifest-path",
        "--preflight-metadata-path",
        "--allowed-manifest-root",
        "--allow-real-reviewed-local-csv-package-candidate-preflight",
        "--csv-structural-header-metadata-path",
        "--local-file-byte-hash-metadata-path",
        "--expected-hash-verification-metadata-path",
        "--csv-physical-data-line-count-metadata-path",
        "--source-revision-time-metadata-path",
        "--reviewer-quality-limitation-metadata-path",
    ]:
        assert allowed in output
    for forbidden in FORBIDDEN_HELP:
        assert forbidden not in output


def test_index_health_status_cli_after_reference_metadata_deleted(tmp_path: Path, capsys) -> None:
    root, manifest_path, refs = _write_valid_inputs(tmp_path)
    code, output = _run_metadata_cli(root, manifest_path, refs, tmp_path, "cli_metadata", capsys)
    assert code == 0
    rmtree(tmp_path / "allowed" / "metadata")

    index_code, index_output = _run_cli(
        [INDEX_COMMAND, "--root", str(root), "--output-dir", str(root / "index")],
        capsys,
    )
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
    assert "latest_run_id: cli_metadata" in index_output
    assert core.STATUS_METADATA_CONTEXT_REPORT_ONLY in index_output
    assert health_code == 0
    assert "health_status: PASS" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_metadata" in status_output
    assert core.STATUS_METADATA_CONTEXT_REPORT_ONLY in status_output
    assert "latest_preflight_id: preflight-001" in status_output
    assert "latest_declared_package_id: declared-package-001 (metadata only)" in status_output
    assert "latest_required_reference_present_count: 6" in status_output
    assert f"recommended_next_task: {RESEARCH_STATUS_NEXT_TASK}" in status_output
    assert STALE_CLI_NEXT_TASK not in status_output
    for output_text in [index_output, health_output, status_output]:
        _assert_no_disclosure(output_text)
        _assert_no_unsafe_wording(output_text)


def test_health_cli_warn_and_fail_paths(tmp_path: Path, capsys) -> None:
    warn_root, warn_manifest, warn_refs = _write_valid_inputs(tmp_path / "warn")
    warn_refs["metadata_reference_following_metadata_path"] = (
        tmp_path / "warn" / "allowed" / "metadata" / "missing_optional.json"
    )
    _run_metadata_cli(warn_root, warn_manifest, warn_refs, tmp_path / "warn", "optional_warn", capsys)
    warn_code, warn_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(warn_root), "--output-dir", str(warn_root / "health")],
        capsys,
    )
    assert warn_code == 0
    assert "health_status: WARN" in warn_output
    assert "warning_count: 1" in warn_output

    fail_root, fail_manifest, fail_refs = _write_valid_inputs(tmp_path / "fail")
    _run_metadata_cli(fail_root, fail_manifest, fail_refs, tmp_path / "fail", "hash_leak", capsys)
    _write_text(fail_root / "hash_leak" / "real_reviewed_local_csv_package_candidate_preflight_report.md", FULL_HASH_SENTINEL)
    fail_code, fail_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(fail_root), "--output-dir", str(fail_root / "health")],
        capsys,
    )
    assert fail_code != 0
    assert "health_status: FAIL" in fail_output
    assert FULL_HASH_SENTINEL not in fail_output


def test_cli_module_and_tests_do_not_import_forbidden_hash_library() -> None:
    forbidden_import_name = "hash" + "lib"
    for path in [Path(cli.__file__), Path(__file__)]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
        assert forbidden_import_name not in imported_modules


def test_docs_project_sources_not_created(tmp_path: Path, capsys) -> None:
    root = _root(tmp_path)
    _run_cli([COMMAND, "--output-root", str(root), "--run-id", "docs_guard"], capsys)

    assert not Path("docs/project_sources").exists()


def _run_metadata_cli(
    root: Path,
    manifest_path: Path,
    refs: dict[str, Path],
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
            "--preflight-manifest-path",
            str(manifest_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-real-reviewed-local-csv-package-candidate-preflight",
            *(_metadata_args(refs)),
        ],
        capsys,
    )


def _metadata_args(refs: dict[str, Path]) -> list[str]:
    mapping = {
        "csv_structural_header_metadata_path": "--csv-structural-header-metadata-path",
        "local_file_byte_hash_metadata_path": "--local-file-byte-hash-metadata-path",
        "expected_hash_verification_metadata_path": "--expected-hash-verification-metadata-path",
        "csv_physical_data_line_count_metadata_path": "--csv-physical-data-line-count-metadata-path",
        "source_revision_time_metadata_path": "--source-revision-time-metadata-path",
        "reviewer_quality_limitation_metadata_path": "--reviewer-quality-limitation-metadata-path",
        "metadata_reference_following_metadata_path": "--metadata-reference-following-metadata-path",
        "manifest_only_preflight_metadata_path": "--manifest-only-preflight-metadata-path",
    }
    args: list[str] = []
    for key, flag in mapping.items():
        if key in refs:
            args.extend([flag, str(refs[key])])
    return args


def _run_cli(argv: list[str], capsys) -> tuple[int, str]:
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _write_valid_inputs(
    tmp_path: Path,
    *,
    metadata_overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[Path, Path, dict[str, Path]]:
    allowed = tmp_path / "allowed"
    metadata_root = allowed / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    root = _root(tmp_path)
    overrides = metadata_overrides or {}
    refs: dict[str, Path] = {}
    entries = []
    for reference_name in REQUIRED_REFERENCE_NAMES:
        path = metadata_root / f"{reference_name}.json"
        refs[f"{reference_name}_path"] = path
        _write_json(path, _reference_metadata(reference_name, **overrides.get(reference_name, {})))
        entries.append(_reference_entry(reference_name, path))
    manifest_path = allowed / "preflight_manifest.json"
    _write_json(manifest_path, _manifest(entries))
    return root, manifest_path, refs


def _manifest(entries: list[dict[str, object]]) -> dict[str, object]:
    return {
        "preflight_id": "preflight-001",
        "declared_package_id": "declared-package-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-07-04T00:00:00Z",
        "prepared_by": "synthetic-preparer",
        "report_only": True,
        "diagnostic_only": True,
        "requested_preflight_level": core.PREFLIGHT_METADATA_REFERENCES_ONLY,
        "requested_package_creation_level": core.PACKAGE_CREATION_NONE,
        "requested_csv_read_level": core.CSV_READ_NONE,
        "requested_source_hash_validation_level": core.SOURCE_HASH_VALIDATION_NONE,
        "requested_revision_id_validation_level": core.REVISION_ID_VALIDATION_NONE,
        "requested_available_time_validation_level": core.AVAILABLE_TIME_VALIDATION_NONE,
        "requested_pit_admissibility_level": core.PIT_ADMISSIBILITY_NONE,
        "requested_reviewer_authority_level": core.REVIEWER_AUTHORITY_NONE,
        "requested_quality_status_level": core.QUALITY_STATUS_NONE,
        "requested_limitation_review_level": core.LIMITATION_REVIEW_NONE,
        "requested_permission_review_level": core.PERMISSION_REVIEW_NONE,
        "requested_source_reliability_level": core.SOURCE_RELIABILITY_NONE,
        "requested_active_input_level": core.ACTIVE_INPUT_NONE,
        "requested_replay_readiness_level": core.REPLAY_READINESS_NONE,
        "evidence_references": entries,
        "required_evidence_policy": "strict_metadata_complete",
        "warning_policy": {"missing_optional_evidence": "WARN"},
        "blocker_policy": {"missing_required_evidence": "FAIL"},
        "disclosure_policy": {"hashes": "preview_only", "reviewer": "preview_only"},
        "forbidden_downstream_flags": {field: False for field in NEGATIVE_FALSE_FIELDS},
        "limitations": ["preflight is metadata-reference context only"],
    }


def _reference_entry(reference_name: str, path: Path) -> dict[str, object]:
    return {
        "reference_name": reference_name,
        "reference_type": reference_name,
        "path": str(path),
        "required": True,
        "expected_workflow_area": reference_name,
        "expected_report_only": True,
        "expected_diagnostic_only": True,
        "expected_metadata_only": True,
        "expected_negative_flags": NEGATIVE_FALSE_FIELDS,
        "allow_statuses": ["PASS", "WARN", "METADATA_PRESENT_REPORT_ONLY"],
        "warn_statuses": ["WARN", "EXPECTED_HASH_VERIFICATION_WARN_HASH_MISMATCH"],
        "block_statuses": ["FAIL"],
        "disclosure_level": "preview_only",
    }


def _reference_metadata(reference_name: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "reference_name": reference_name,
        "runtime_status": "METADATA_PRESENT_REPORT_ONLY",
        "health_status": "PASS",
        "workflow_stage": f"{reference_name.upper()}_REPORT_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "metadata_only": True,
        "issue_count": 0,
        "warning_count": 0,
        "blocker_count": 0,
        "source_hash_preview": "abcdef123456",
        "reviewer_id_preview": "reviewer-001",
        "forbidden_downstream_flags": {field: False for field in NEGATIVE_FALSE_FIELDS},
        "limitations": ["synthetic metadata reference"],
    }
    for field in NEGATIVE_FALSE_FIELDS:
        payload[field] = False
    payload.update(overrides)
    return payload


def _mutate_manifest(path: Path, mutation) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    _write_json(path, payload)


def _update_reference(path: Path, updates: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    _write_json(path, payload)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "preflight_cli"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _assert_negative_proofs(output: str) -> None:
    for field in NEGATIVE_FALSE_FIELDS:
        assert f"{field}: False" in output, field


def _assert_no_disclosure(output: str) -> None:
    for sentinel in [
        FULL_HASH_SENTINEL,
        REVIEWER_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        HEADER_VALUE_SENTINEL,
        ROW_VALUE_SENTINEL,
    ]:
        assert sentinel not in output


def _assert_no_unsafe_wording(output: str) -> None:
    for phrase in UNSAFE_WORDING:
        assert phrase not in output
