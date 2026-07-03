from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from quant_replay_system import cli


COMMAND = (
    "tiny-pit-real-reviewed-local-csv-package-candidate-reviewer-authority-"
    "quality-limitation"
)
INDEX_COMMAND = f"{COMMAND}-index"
HEALTH_COMMAND = f"{COMMAND}-health"
STATUS_COMMAND = f"{COMMAND}-status"
FULL_REVIEWER_ID_SENTINEL = "private-reviewer-identity-000001"
REVIEWER_ID_PREVIEW = FULL_REVIEWER_ID_SENTINEL[:12]
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/reviewer.json"
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SENTINEL_SHOULD_NOT_PRINT"
TARGET_CSV_SENTINEL = "TARGET_CSV_SENTINEL_SHOULD_NOT_PRINT"
FULL_HASH_SENTINEL = "a" * 64
NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation Research-Status Planning Report-Only v0.1"
)
STALE_CLI_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation CLI Report-Only v0.1"
)
UNSAFE_WORDING = [
    "REVIEWER_APPROVED_PACKAGE",
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
    "--reviewer-authority-validation",
    "--validate-reviewer-authority",
    "--source-reliability-score",
    "--quality-to-package-promotion",
    "--limitation-override",
    "--real-package-candidate",
    "--pit-gate",
    "--active-input",
    "--replay",
    "--trading",
    "--automatic-discovery",
]
NEGATIVE_FIELDS = [
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "real_package_candidate_created",
    "active_replay_input",
    "buy_review_allowed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
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
    assert "runtime_status: NO_REVIEWER_QUALITY_LIMITATION_INPUT" in output
    assert "health_status: PASS" in output
    assert "reviewer_authority_level: REVIEWER_AUTHORITY_NONE" in output
    assert "quality_status_level: QUALITY_STATUS_NONE" in output
    assert "limitation_review_level: LIMITATION_REVIEW_NONE" in output
    assert "permission_review_level: PERMISSION_REVIEW_NONE" in output
    assert "package_promotion_level: PACKAGE_PROMOTION_NONE" in output
    assert "report_only: True" in output
    assert "diagnostic_only: True" in output
    assert "reviewer_metadata_present: False" in output
    assert "reviewer_id_recorded: False" in output
    assert "quality_status_declared: False" in output
    assert "limitations_present: False" in output
    assert "permission_class_present: False" in output
    assert f"recommended_next_task: {NEXT_TASK}" in output
    assert STALE_CLI_NEXT_TASK not in output
    _assert_negative_proofs(output)
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)
    assert (root / "cli_no_input" / "metadata.json").is_file()


def test_core_cli_metadata_present_prints_safe_context_only(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(tmp_path)

    code, output = _run_metadata_cli(root, manifest_path, metadata_path, tmp_path, "cli_metadata", capsys)

    assert code == 0
    assert "runtime_status: REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY" in output
    assert "health_status: PASS" in output
    assert "reviewer_authority_level: REVIEWER_METADATA_PRESENT_ONLY" in output
    assert "quality_status_level: QUALITY_METADATA_PRESENT_ONLY" in output
    assert "limitation_review_level: LIMITATION_METADATA_PRESENT_ONLY" in output
    assert "permission_review_level: PERMISSION_CLASS_METADATA_PRESENT_ONLY" in output
    assert "package_promotion_level: PACKAGE_PROMOTION_NONE" in output
    assert "reviewer_metadata_present: True" in output
    assert "reviewer_id_recorded: True" in output
    assert f"reviewer_id_preview: {REVIEWER_ID_PREVIEW}" in output
    assert "reviewer_role: reviewer" in output
    assert "reviewer_type: human_declared_only" in output
    assert "reviewer_role_supported: True" in output
    assert "quality_status_declared: True" in output
    assert "limitation_count: 1" in output
    assert "limitation_severity_max: INFO" in output
    assert "permission_class: public" in output
    assert "legality_flag: public_confirmed" in output
    assert f"recommended_next_task: {NEXT_TASK}" in output
    assert STALE_CLI_NEXT_TASK not in output
    _assert_negative_proofs(output)
    _assert_no_disclosure(output)
    _assert_no_unsafe_wording(output)


def test_core_cli_warn_and_blocked_cases(tmp_path: Path, capsys) -> None:
    warn_root, warn_manifest, warn_metadata = _write_valid_inputs(
        tmp_path / "warn",
        metadata_mutation=lambda metadata: metadata.update(
            {
                "quality_warning_count": 1,
                "limitation_severity_max": "WARN",
                "limitation_categories": ["manual_review_needed"],
                "limitations": ["WARN limitation remains visible."],
            }
        ),
    )
    warn_code, warn_output = _run_metadata_cli(
        warn_root,
        warn_manifest,
        warn_metadata,
        tmp_path / "warn",
        "warn_limitation",
        capsys,
    )
    assert warn_code == 0
    assert "runtime_status: REVIEWER_QUALITY_LIMITATION_WARN_LIMITATIONS_PRESENT" in warn_output
    assert "health_status: WARN" in warn_output
    assert "reviewer_authority_validated: False" in warn_output

    blocked_cases = [
        ("missing_allow", None, None, "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_ALLOW_FLAG", False),
        ("malformed_manifest", "{malformed", None, "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MANIFEST_SCHEMA", True),
        (
            "unsupported_role",
            None,
            lambda metadata: metadata.__setitem__("reviewer_role", "broker"),
            "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_UNSUPPORTED_REVIEWER_ROLE",
            True,
        ),
        (
            "missing_quality",
            None,
            lambda metadata: metadata.pop("quality_status"),
            "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_MISSING_QUALITY_STATUS",
            True,
        ),
        (
            "blocker_limitation",
            None,
            lambda metadata: metadata.update(
                {"blocking_limitation_count": 1, "limitation_severity_max": "BLOCKER"}
            ),
            "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_BLOCKING_LIMITATION",
            True,
        ),
        (
            "forbidden_permission",
            None,
            lambda metadata: metadata.update(
                {"permission_class": "private", "legality_flag": "private_source"}
            ),
            "REVIEWER_QUALITY_LIMITATION_BLOCKED_BY_FORBIDDEN_PERMISSION",
            True,
        ),
    ]
    for run_id, manifest_text, metadata_mutation, expected_status, allow in blocked_cases:
        case_root, case_manifest, case_metadata = _write_valid_inputs(tmp_path / run_id)
        if manifest_text is not None:
            _write_text(case_manifest, manifest_text)
        if metadata_mutation is not None:
            metadata = _reviewer_quality_metadata()
            metadata_mutation(metadata)
            _write_json(case_metadata, metadata)
        code, output = _run_cli(
            [
                COMMAND,
                "--output-root",
                str(case_root),
                "--run-id",
                run_id,
                "--reviewer-quality-manifest-path",
                str(case_manifest),
                "--reviewer-quality-metadata-path",
                str(case_metadata),
                "--allowed-manifest-root",
                str(tmp_path / run_id / "allowed"),
                *(["--allow-reviewer-quality-limitation-metadata"] if allow else []),
            ],
            capsys,
        )

        assert code != 0, run_id
        assert expected_status in output
        assert "health_status: FAIL" in output
        _assert_no_disclosure(output)


def test_core_cli_help_contains_no_forbidden_args(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main([COMMAND, "--help"])
    output = capsys.readouterr().out

    assert exc_info.value.code == 0
    for allowed in [
        "--output-root",
        "--run-id",
        "--reviewer-quality-manifest-path",
        "--reviewer-quality-metadata-path",
        "--allowed-manifest-root",
        "--allow-reviewer-quality-limitation-metadata",
    ]:
        assert allowed in output
    for forbidden in FORBIDDEN_HELP:
        assert forbidden not in output


def test_index_health_status_cli_after_reviewer_metadata_deleted(tmp_path: Path, capsys) -> None:
    root, manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    code, _ = _run_metadata_cli(root, manifest_path, metadata_path, tmp_path, "cli_metadata", capsys)
    assert code == 0
    manifest_path.unlink()
    metadata_path.unlink()

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
    assert "latest_runtime_status: REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY" in index_output
    assert f"latest_reviewer_id_preview: {REVIEWER_ID_PREVIEW}" in index_output
    assert health_code == 0
    assert "health_status: PASS" in health_output
    assert "checked_artifact_count: 1" in health_output
    assert status_code == 0
    assert "latest_run_id: cli_metadata" in status_output
    assert "latest_runtime_status: REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY" in status_output
    assert "latest_reviewer_authority_level: REVIEWER_METADATA_PRESENT_ONLY" in status_output
    assert "latest_quality_status_level: QUALITY_METADATA_PRESENT_ONLY" in status_output
    assert "latest_limitation_review_level: LIMITATION_METADATA_PRESENT_ONLY" in status_output
    assert "latest_permission_review_level: PERMISSION_CLASS_METADATA_PRESENT_ONLY" in status_output
    assert "latest_package_promotion_level: PACKAGE_PROMOTION_NONE" in status_output
    assert "latest_quality_status_declared: True" in status_output
    assert "latest_limitation_severity_max: INFO" in status_output
    assert "latest_permission_class: public" in status_output
    assert f"recommended_next_task: {NEXT_TASK}" in status_output
    assert STALE_CLI_NEXT_TASK not in status_output
    for output_text in [index_output, health_output, status_output]:
        _assert_no_disclosure(output_text)
        _assert_no_unsafe_wording(output_text)


def test_health_cli_warn_and_fail_paths_do_not_echo_sensitive_values(tmp_path: Path, capsys) -> None:
    warn_root, warn_manifest, warn_metadata = _write_valid_inputs(
        tmp_path / "health_warn",
        metadata_mutation=lambda metadata: metadata.update(
            {"quality_warning_count": 1, "limitation_severity_max": "WARN"}
        ),
    )
    _run_metadata_cli(warn_root, warn_manifest, warn_metadata, tmp_path / "health_warn", "warn", capsys)
    warn_code, warn_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(warn_root), "--output-dir", str(warn_root / "health")],
        capsys,
    )
    assert warn_code == 0
    assert "health_status: WARN" in warn_output
    assert "warning_count: 1" in warn_output

    fail_root, fail_manifest, fail_metadata = _write_valid_inputs(tmp_path / "health_fail")
    _run_metadata_cli(fail_root, fail_manifest, fail_metadata, tmp_path / "health_fail", "leak", capsys)
    _write_text(fail_root / "leak" / "reviewer_quality_limitation_report.md", FULL_REVIEWER_ID_SENTINEL)
    fail_code, fail_output = _run_cli(
        [HEALTH_COMMAND, "--root", str(fail_root), "--output-dir", str(fail_root / "health")],
        capsys,
    )
    assert fail_code != 0
    assert "health_status: FAIL" in fail_output
    assert FULL_REVIEWER_ID_SENTINEL not in fail_output


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
            "--reviewer-quality-manifest-path",
            str(manifest_path),
            "--reviewer-quality-metadata-path",
            str(metadata_path),
            "--allowed-manifest-root",
            str(tmp_path / "allowed"),
            "--allow-reviewer-quality-limitation-metadata",
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
    root = tmp_path / "outputs" / "reports" / "manual_diagnostics" / "reviewer_quality_cli"
    metadata_path = allowed / "reviewer_quality_metadata.json"
    manifest_path = allowed / "manifest.json"
    metadata = _reviewer_quality_metadata()
    if metadata_mutation:
        metadata_mutation(metadata)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, _manifest(metadata_path))
    return root, manifest_path, metadata_path


def _manifest(metadata_path: Path) -> dict:
    return {
        "package_id": "pkg-reviewer-quality",
        "package_schema_version": "reviewer_quality_limitation_v0_1",
        "created_at": "2026-07-03T00:00:00Z",
        "prepared_by": "codex-test",
        "report_only": True,
        "diagnostic_only": True,
        "requested_reviewer_authority_level": "REVIEWER_METADATA_PRESENT_ONLY",
        "requested_quality_status_level": "QUALITY_METADATA_PRESENT_ONLY",
        "requested_limitation_review_level": "LIMITATION_METADATA_PRESENT_ONLY",
        "requested_permission_review_level": "PERMISSION_CLASS_METADATA_PRESENT_ONLY",
        "requested_package_promotion_level": "PACKAGE_PROMOTION_NONE",
        "reviewer_quality_metadata_reference": {
            "path": str(metadata_path),
            "required": True,
            "reference_type": "reviewer_quality_limitation_metadata_ref",
            "intended_touch_level": "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_ONLY",
            "declared_only": False,
        },
        "reviewer_policy": "metadata-present-only",
        "quality_policy": "declared-only",
        "limitation_policy": "visible-non-override",
        "permission_policy": "declared-permission-class-only",
        "disclosure_policy": "preview-only",
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata shape only; no reviewer authority validation."],
    }


def _reviewer_quality_metadata() -> dict:
    return {
        "reviewer_id_recorded": True,
        "reviewer_id_preview": REVIEWER_ID_PREVIEW,
        "reviewer_role": "reviewer",
        "reviewer_type": "human_declared_only",
        "reviewer_attestation_present": True,
        "reviewer_authority_scope_declared": True,
        "reviewer_authority_validated": False,
        "manual_review_status": "declared_context_only",
        "quality_status": "QUALITY_METADATA_PRESENT_ONLY",
        "quality_status_validated": False,
        "quality_issue_count": 0,
        "quality_warning_count": 0,
        "quality_blocker_count": 0,
        "limitations_present": True,
        "limitation_count": 1,
        "limitation_severity_max": "INFO",
        "limitation_categories": ["schema_assumption"],
        "unresolved_limitation_count": 0,
        "blocking_limitation_count": 0,
        "limitation_policy": "visible-non-override",
        "limitations_overridden_by_reviewer": False,
        "limitations_overridden_by_quality": False,
        "assumptions_present": True,
        "assumption_count": 1,
        "permission_class": "public",
        "legality_flag": "public_confirmed",
        "permission_class_validated": False,
        "report_only": True,
        "diagnostic_only": True,
        "full_reviewer_id": FULL_REVIEWER_ID_SENTINEL,
        "source_content_sample": SOURCE_CONTENT_SENTINEL,
        "target_csv_sample": TARGET_CSV_SENTINEL,
        "private_path": PRIVATE_PATH_SENTINEL,
        "full_hash_sentinel": FULL_HASH_SENTINEL,
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Synthetic INFO limitation context."],
    }


def _false_flags() -> dict[str, bool]:
    return {field: False for field in NEGATIVE_FIELDS}


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "reviewer_quality_cli"


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
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _assert_negative_proofs(output: str) -> None:
    for field in NEGATIVE_FIELDS:
        assert f"{field}: False" in output


def _assert_no_disclosure(output: str) -> None:
    for sentinel in [
        FULL_REVIEWER_ID_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        FULL_HASH_SENTINEL,
    ]:
        assert sentinel not in output


def _assert_no_unsafe_wording(output: str) -> None:
    for phrase in UNSAFE_WORDING:
        assert phrase not in output
