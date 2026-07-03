from __future__ import annotations

import ast
import csv
import inspect
import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation as core,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_health import (
    check_reviewer_authority_quality_limitation_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_index import (
    build_reviewer_authority_quality_limitation_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_reviewer_authority_quality_limitation_status import (
    run_reviewer_authority_quality_limitation_status,
)


FULL_REVIEWER_ID_SENTINEL = "private-reviewer-identity-000001"
REVIEWER_ID_PREVIEW = FULL_REVIEWER_ID_SENTINEL[:12]
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/reviewer.json"
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SENTINEL_SHOULD_NOT_APPEAR"
TARGET_CSV_SENTINEL = "TARGET_CSV_SENTINEL_SHOULD_NOT_APPEAR"
FULL_HASH_SENTINEL = "a" * 64
CLI_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Reviewer Authority Quality "
    "Limitation Checkpoint Planning Report-Only v0.1"
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
NEGATIVE_FIELDS = [
    "reviewer_authority_validated",
    "quality_status_validated",
    "permission_class_validated",
    "source_reliability_scored",
    "source_hash_validated",
    "revision_id_validated",
    "available_time_validated",
    "pit_admissibility_validated",
    "real_csv_consumed",
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


def test_index_discovers_no_input_artifact_and_exposes_safe_fields(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_reviewer_authority_quality_limitation(output_root=root, run_id="001_no_input")

    result = build_reviewer_authority_quality_limitation_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "001_no_input"
    assert row["runtime_status"] == "NO_REVIEWER_QUALITY_LIMITATION_INPUT"
    assert row["health_status"] == "PASS"
    assert row["reviewer_authority_level"] == "REVIEWER_AUTHORITY_NONE"
    assert row["quality_status_level"] == "QUALITY_STATUS_NONE"
    assert row["limitation_review_level"] == "LIMITATION_REVIEW_NONE"
    assert row["permission_review_level"] == "PERMISSION_REVIEW_NONE"
    assert row["package_promotion_level"] == "PACKAGE_PROMOTION_NONE"
    assert row["reviewer_metadata_present"] is False
    assert row["reviewer_id_preview"] == ""
    assert row["reviewer_role_supported"] is False
    assert row["quality_status_declared"] is False
    assert row["limitations_present"] is False
    assert row["permission_class_present"] is False
    _assert_negative_fields_false(row)


def test_index_discovers_metadata_present_artifact_and_exposes_context_fields(
    tmp_path: Path,
) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = build_reviewer_authority_quality_limitation_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["runtime_status"] == "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY"
    assert row["health_status"] == "PASS"
    assert row["reviewer_authority_level"] == "REVIEWER_METADATA_PRESENT_ONLY"
    assert row["quality_status_level"] == "QUALITY_METADATA_PRESENT_ONLY"
    assert row["limitation_review_level"] == "LIMITATION_METADATA_PRESENT_ONLY"
    assert row["permission_review_level"] == "PERMISSION_CLASS_METADATA_PRESENT_ONLY"
    assert row["package_promotion_level"] == "PACKAGE_PROMOTION_NONE"
    assert row["reviewer_metadata_present"] is True
    assert row["reviewer_id_recorded"] is True
    assert row["reviewer_id_preview"] == REVIEWER_ID_PREVIEW
    assert row["reviewer_role"] == "reviewer"
    assert row["reviewer_role_supported"] is True
    assert row["reviewer_type"] == "human_declared_only"
    assert row["reviewer_attestation_present"] is True
    assert row["reviewer_authority_scope_declared"] is True
    assert row["quality_status_present"] is True
    assert row["quality_status_declared"] is True
    assert row["quality_issue_count"] == 0
    assert row["quality_warning_count"] == 0
    assert row["quality_blocker_count"] == 0
    assert row["limitations_present"] is True
    assert row["limitation_count"] == 1
    assert row["limitation_severity_max"] == "INFO"
    assert row["limitation_categories"] == ["schema_assumption"]
    assert row["permission_class"] == "public"
    assert row["legality_flag"] == "public_confirmed"
    _assert_negative_fields_false(row)


def test_index_outputs_do_not_expose_private_or_readiness_sentinels(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(
        tmp_path,
        root,
        "no_leak",
        metadata_mutation=lambda metadata: metadata.update(
            {
                "full_reviewer_id": FULL_REVIEWER_ID_SENTINEL,
                "reviewer_attestation_text": PRIVATE_PATH_SENTINEL,
                "detailed_limitation_text": SOURCE_CONTENT_SENTINEL,
            }
        ),
    )

    result = build_reviewer_authority_quality_limitation_index(root=root, output_dir=root / "index")
    text = _artifact_text(result.artifact_paths.values())

    for sentinel in [
        FULL_REVIEWER_ID_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        FULL_HASH_SENTINEL,
        "source_reliability_score_value",
        "reviewer_authority_validated: true",
        "PACKAGE_ADMISSIBLE",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
    ]:
        assert sentinel not in text


def test_health_pass_for_safe_no_input_and_metadata_present_artifacts(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_reviewer_authority_quality_limitation(output_root=root, run_id="001_no_input")
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 2
    assert result.error_count == 0
    assert result.warning_count == 0


def test_health_warn_for_warn_limitation_artifact(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(
        tmp_path,
        root,
        "warn_limitation",
        metadata_mutation=lambda metadata: metadata.update(
            {
                "quality_status": "QUALITY_STATUS_WARN_LIMITATIONS",
                "quality_warning_count": 1,
                "limitation_severity_max": "WARN",
                "limitation_categories": ["timezone_assumption"],
            }
        ),
    )

    result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert "LIMITATION_REVIEW_REQUIRED" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_blocker_limitation_and_forbidden_permission(tmp_path: Path) -> None:
    cases = [
        (
            "blocker_limitation",
            lambda metadata: metadata.update(
                {
                    "quality_status": "QUALITY_STATUS_BLOCKED_BY_LIMITATIONS",
                    "limitation_severity_max": "BLOCKER",
                    "blocking_limitation_count": 1,
                }
            ),
            "BLOCKING_LIMITATION_PRESENT",
        ),
        (
            "forbidden_permission",
            lambda metadata: metadata.update(
                {"permission_class": "restricted", "legality_flag": "restricted_use"}
            ),
            "FORBIDDEN_PERMISSION_CLASS",
        ),
    ]
    for run_id, mutation, expected_code in cases:
        root = _output_root(tmp_path / run_id)
        _run_metadata(tmp_path / run_id, root, run_id, metadata_mutation=mutation)

        result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", run_id
        assert expected_code in {row["issue_code"] for row in result.rows}


def test_health_fails_for_forbidden_downstream_flag(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    artifact = _run_metadata(tmp_path, root, "bad_flags")
    flags_path = Path(artifact["artifact_paths"]["forbidden_downstream_flags"])
    flags = _read_json(flags_path)
    flags["active_replay_input"] = True
    _write_json(flags_path, flags)

    result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_validation_and_downstream_flags(tmp_path: Path) -> None:
    unsafe_fields = [
        "reviewer_authority_validated",
        "quality_status_validated",
        "permission_class_validated",
        "limitations_overridden_by_reviewer",
        "limitations_overridden_by_quality",
        "source_reliability_scored",
        "real_package_candidate_created",
        "active_replay_input",
        "buy_review_allowed",
        "trading_allowed",
    ]
    for field in unsafe_fields:
        root = _output_root(tmp_path / field)
        artifact = _run_metadata(tmp_path / field, root, field)
        _mutate_metadata(artifact, **{field: True})

        result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_source_pit_validation_claims(tmp_path: Path) -> None:
    for field in [
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
    ]:
        root = _output_root(tmp_path / field)
        artifact = _run_metadata(tmp_path / field, root, field)
        _mutate_metadata(artifact, **{field: True})

        result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_unsafe_wording_and_private_leak_without_echoing_values(
    tmp_path: Path,
) -> None:
    root = _output_root(tmp_path)
    artifact = _run_metadata(tmp_path, root, "unsafe_wording")
    _mutate_metadata(artifact, recommended_next_task="ACTIVE_REPLAY_INPUT_READY")
    report_path = Path(artifact["artifact_paths"]["report"])
    _write_text(report_path, FULL_REVIEWER_ID_SENTINEL)

    result = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")
    text = _artifact_text(result.artifact_paths.values())

    assert result.status == "FAIL"
    issue_codes = {row["issue_code"] for row in result.rows}
    assert "FORBIDDEN_STATUS_WORDING" in issue_codes
    assert "PRIVATE_REVIEWER_ID_LEAK" in issue_codes
    assert FULL_REVIEWER_ID_SENTINEL not in text


def test_status_summarizes_latest_safe_artifact_and_recommends_cli_phase(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_reviewer_authority_quality_limitation(output_root=root, run_id="001_no_input")
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = run_reviewer_authority_quality_limitation_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "002_metadata_present"
    assert result.latest_runtime_status == "REVIEWER_QUALITY_LIMITATION_METADATA_PRESENT_REPORT_ONLY"
    assert result.latest_health_status == "PASS"
    assert result.latest_reviewer_id_preview == REVIEWER_ID_PREVIEW
    assert result.latest_reviewer_role == "reviewer"
    assert result.latest_reviewer_type == "human_declared_only"
    assert result.latest_quality_status_declared is True
    assert result.latest_limitation_severity_max == "INFO"
    assert result.latest_permission_class == "public"
    assert result.recommended_next_task == CLI_NEXT_TASK
    assert "Research-Status Planning Report-Only v0.1" not in result.recommended_next_task
    assert "CLI Report-Only v0.1" not in result.recommended_next_task
    assert "Checkpoint Planning Report-Only v0.1" in result.recommended_next_task
    _assert_negative_fields_false(result.summary)


def test_status_does_not_expose_private_or_readiness_sentinels(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "status_no_leak")

    result = run_reviewer_authority_quality_limitation_status(root=root, output_dir=root / "status")
    text = _artifact_text(result.artifact_paths.values())

    for sentinel in [
        FULL_REVIEWER_ID_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        FULL_HASH_SENTINEL,
    ]:
        assert sentinel not in text
    for phrase in UNSAFE_WORDING:
        assert phrase not in text
        assert phrase not in result.latest_runtime_status
        assert phrase not in result.recommended_next_task


def test_views_do_not_reopen_reviewer_metadata_after_core_generation(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    manifest_path, metadata_path = _write_valid_inputs(tmp_path)
    artifact = _run_metadata(
        tmp_path,
        root,
        "delete_inputs",
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )
    manifest_path.unlink()
    metadata_path.unlink()

    index = build_reviewer_authority_quality_limitation_index(root=root, output_dir=root / "index")
    health = check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")
    status = run_reviewer_authority_quality_limitation_status(root=root, output_dir=root / "status")

    assert artifact["reviewer_authority_validated"] is False
    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_run_id == "delete_inputs"


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "docs_guard")

    build_reviewer_authority_quality_limitation_index(root=root, output_dir=root / "index")
    check_reviewer_authority_quality_limitation_health(root=root, output_dir=root / "health")
    run_reviewer_authority_quality_limitation_status(root=root, output_dir=root / "status")

    assert not Path("docs/project_sources").exists()


def test_views_modules_and_tests_have_no_forbidden_imports_or_path_read_helpers() -> None:
    module_paths = [
        Path(inspect.getfile(build_reviewer_authority_quality_limitation_index)),
        Path(inspect.getfile(check_reviewer_authority_quality_limitation_health)),
        Path(inspect.getfile(run_reviewer_authority_quality_limitation_status)),
        Path(__file__),
    ]

    for path in module_paths:
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
        assert (".read_" + "text(") not in source
        assert (".read_" + "bytes(") not in source


def test_public_view_api_has_no_real_csv_or_validation_arguments() -> None:
    forbidden_names = {
        "source_artifact_path",
        "target_csv_path",
        "csv_path",
        "source_bytes",
        "recompute_hash",
        "expected_hash",
        "reverify_expected_hash",
        "replay_decision_time",
        "reviewer_authority_validation",
        "quality_to_package_promotion",
        "limitation_override",
    }
    for func in [
        build_reviewer_authority_quality_limitation_index,
        check_reviewer_authority_quality_limitation_health,
        run_reviewer_authority_quality_limitation_status,
    ]:
        assert not (set(inspect.signature(func).parameters) & forbidden_names)


def _run_metadata(
    tmp_path: Path,
    root: Path,
    run_id: str,
    *,
    manifest_path: Path | None = None,
    metadata_path: Path | None = None,
    metadata_mutation=None,
) -> dict:
    if manifest_path is None or metadata_path is None:
        manifest_path, metadata_path = _write_valid_inputs(
            tmp_path,
            metadata_mutation=metadata_mutation,
        )
    return core.run_reviewer_authority_quality_limitation(
        output_root=root,
        run_id=run_id,
        reviewer_quality_manifest_path=manifest_path,
        reviewer_quality_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        reviewer_authority_level="REVIEWER_METADATA_PRESENT_ONLY",
        quality_status_level="QUALITY_METADATA_PRESENT_ONLY",
        limitation_review_level="LIMITATION_METADATA_PRESENT_ONLY",
        permission_review_level="PERMISSION_CLASS_METADATA_PRESENT_ONLY",
        package_promotion_level="PACKAGE_PROMOTION_NONE",
        allow_reviewer_quality_limitation_metadata=True,
    )


def _write_valid_inputs(
    tmp_path: Path,
    *,
    metadata_mutation=None,
) -> tuple[Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(parents=True, exist_ok=True)
    metadata_path = allowed / "reviewer_quality_metadata.json"
    manifest_path = allowed / "manifest.json"
    metadata = _reviewer_quality_metadata()
    if metadata_mutation:
        metadata_mutation(metadata)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, _manifest(metadata_path))
    return manifest_path, metadata_path


def _manifest(metadata_path: Path) -> dict:
    return {
        "package_id": "pkg-reviewer-quality-fixture",
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


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "reviewer_quality_limitation"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    assert isinstance(loaded, dict)
    return loaded


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _artifact_text(paths) -> str:
    chunks = []
    for path in paths:
        candidate = Path(path)
        if candidate.is_file():
            chunks.append(_read_text(candidate))
    return "\n".join(chunks)


def _mutate_metadata(artifact: dict, **updates) -> None:
    metadata_path = Path(artifact["artifact_paths"]["metadata"])
    payload = _read_json(metadata_path)
    payload.update(updates)
    _write_json(metadata_path, payload)


def _assert_negative_fields_false(result: dict) -> None:
    for field in NEGATIVE_FIELDS:
        assert result[field] is False, field
