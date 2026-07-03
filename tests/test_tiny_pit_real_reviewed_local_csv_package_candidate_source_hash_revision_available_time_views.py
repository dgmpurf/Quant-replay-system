from __future__ import annotations

import ast
import csv
import inspect
import json
from pathlib import Path

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time as core,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_health import (
    check_source_hash_revision_available_time_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_index import (
    build_source_hash_revision_available_time_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_source_hash_revision_available_time_status import (
    run_source_hash_revision_available_time_status,
)


FULL_SOURCE_HASH = "a" * 64
SOURCE_HASH_PREVIEW = "a" * 16
SOURCE_CONTENT_SENTINEL = "SOURCE_CONTENT_SENTINEL_SHOULD_NOT_APPEAR"
TARGET_CSV_SENTINEL = "TARGET_CSV_SENTINEL_SHOULD_NOT_APPEAR"
ROW_VALUE_SENTINEL = "ROW_VALUE_SENTINEL_SHOULD_NOT_APPEAR"
PRIVATE_PATH_SENTINEL = "C:/Users/msjpurf/private/source.csv"
CLI_NEXT_TASK = (
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
NEGATIVE_FIELDS = [
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
UNSAFE_METADATA_FLAGS = [
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
    "source_reliability_scored",
    "reviewer_authority_validated",
    "active_replay_input",
    "buy_review_allowed",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]


def test_index_discovers_no_input_artifact_and_exposes_safe_fields(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_source_hash_revision_available_time(output_root=root, run_id="001_no_input")

    result = build_source_hash_revision_available_time_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["run_id"] == "001_no_input"
    assert row["runtime_status"] == "NO_SOURCE_REVISION_TIME_INPUT"
    assert row["health_status"] == "PASS"
    assert row["source_hash_validation_level"] == "SOURCE_HASH_VALIDATION_NONE"
    assert row["revision_id_validation_level"] == "REVISION_ID_VALIDATION_NONE"
    assert row["available_time_validation_level"] == "AVAILABLE_TIME_VALIDATION_NONE"
    assert row["pit_admissibility_level"] == "PIT_ADMISSIBILITY_NONE"
    assert row["source_hash_metadata_present"] is False
    assert row["source_hash_preview"] == ""
    assert row["available_time_compared_to_decision_time"] is False
    _assert_negative_fields_false(row)


def test_index_discovers_metadata_present_artifact_and_exposes_preview_metadata(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = build_source_hash_revision_available_time_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 1
    row = result.rows[0]
    assert row["runtime_status"] == "SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY"
    assert row["health_status"] == "PASS"
    assert row["source_hash_validation_level"] == "SOURCE_HASH_METADATA_PRESENT_ONLY"
    assert row["revision_id_validation_level"] == "REVISION_ID_METADATA_PRESENT_ONLY"
    assert row["available_time_validation_level"] == "AVAILABLE_TIME_METADATA_PRESENT_ONLY"
    assert row["pit_admissibility_level"] == "PIT_ADMISSIBILITY_NONE"
    assert row["source_hash_metadata_present"] is True
    assert row["source_hash_format_checked"] is True
    assert row["source_hash_algorithm_supported"] is True
    assert row["source_hash_algorithm"] == "SHA-256"
    assert row["source_hash_preview"] == SOURCE_HASH_PREVIEW
    assert row["revision_id_metadata_present"] is True
    assert row["revision_id_type"] == "provider_revision_id"
    assert row["revision_id_type_supported"] is True
    assert row["revision_id_value_recorded"] is True
    assert row["revision_consistency_checked"] is False
    assert row["available_time_metadata_present"] is True
    assert row["available_time_parseable"] is True
    assert row["available_time_timezone_present"] is True
    assert row["available_time_timezone_policy"] == "Asia/Shanghai"
    assert row["available_time_compared_to_decision_time"] is False


def test_index_outputs_do_not_expose_hash_content_csv_or_readiness_sentinels(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "no_leak")

    result = build_source_hash_revision_available_time_index(root=root, output_dir=root / "index")
    text = _artifact_text(result.artifact_paths.values())

    for sentinel in [
        FULL_SOURCE_HASH,
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        ROW_VALUE_SENTINEL,
        PRIVATE_PATH_SENTINEL,
        "source_reliability_score_value",
        "reviewer_approval",
        "PIT_ADMISSIBLE_PACKAGE",
        "PACKAGE_ADMISSIBLE",
        "ACTIVE_REPLAY_INPUT_READY",
        "BUY_REVIEW_READY",
        "TRADING_READY",
    ]:
        assert sentinel not in text


def test_health_pass_for_safe_no_input_and_metadata_present_artifacts(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_source_hash_revision_available_time(output_root=root, run_id="001_no_input")
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 2
    assert result.error_count == 0
    assert result.warning_count == 0


def test_health_warn_for_timezone_assumption_warning(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(
        tmp_path,
        root,
        "timezone_warning",
        metadata_mutation=lambda metadata: metadata.update(
            {"available_time": "2024-04-02T09:30:00", "available_time_timezone": ""}
        ),
    )

    result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert "TIMEZONE_ASSUMPTION_REVIEW_REQUIRED" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_blocked_core_statuses(tmp_path: Path) -> None:
    cases = [
        (
            "unsupported_hash",
            lambda metadata: metadata.__setitem__("source_hash_algorithm", "MD5"),
            "UNSUPPORTED_HASH_ALGORITHM",
        ),
        (
            "malformed_hash",
            lambda metadata: metadata.__setitem__("source_hash_value", "z" * 64),
            "MALFORMED_SOURCE_HASH",
        ),
        (
            "missing_revision",
            lambda metadata: metadata.pop("revision_id"),
            "MISSING_REVISION_ID",
        ),
        (
            "malformed_time",
            lambda metadata: metadata.__setitem__("available_time", "not-a-date"),
            "MALFORMED_AVAILABLE_TIME",
        ),
    ]
    for run_id, mutation, expected_code in cases:
        root = _output_root(tmp_path / run_id)
        _run_metadata(tmp_path / run_id, root, run_id, metadata_mutation=mutation)

        result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", run_id
        assert expected_code in {row["issue_code"] for row in result.rows}


def test_health_fails_for_full_hash_leakage_without_echoing_value(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    artifact = _run_metadata(tmp_path, root, "hash_leak")
    _write_text(Path(artifact["artifact_paths"]["report"]), FULL_SOURCE_HASH)

    result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")
    text = _artifact_text(result.artifact_paths.values())

    assert result.status == "FAIL"
    assert "FULL_SOURCE_HASH_DISCLOSURE_LEAK" in {row["issue_code"] for row in result.rows}
    assert FULL_SOURCE_HASH not in text


def test_health_fails_for_each_forbidden_metadata_flag(tmp_path: Path) -> None:
    for field in UNSAFE_METADATA_FLAGS:
        root = _output_root(tmp_path / field)
        artifact = _run_metadata(tmp_path / field, root, "unsafe")
        _mutate_metadata(artifact, **{field: True})

        result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_forbidden_downstream_safety_flags(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    artifact = _run_metadata(tmp_path, root, "bad_flags")
    flags_path = Path(artifact["artifact_paths"]["forbidden_downstream_flags"])
    flags = _read_json(flags_path)
    flags["active_replay_input"] = True
    _write_json(flags_path, flags)

    result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in {row["issue_code"] for row in result.rows}


def test_health_fails_for_unsafe_live_status_stage_or_next_task_wording(tmp_path: Path) -> None:
    for field in ["runtime_status", "workflow_stage", "recommended_next_task"]:
        root = _output_root(tmp_path / field)
        artifact = _run_metadata(tmp_path / field, root, "unsafe_wording")
        _mutate_metadata(artifact, **{field: "ACTIVE_REPLAY_INPUT_READY"})

        result = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")

        assert result.status == "FAIL", field
        assert "FORBIDDEN_STATUS_WORDING" in {row["issue_code"] for row in result.rows}


def test_status_summarizes_latest_safe_artifact_and_recommends_cli_phase(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    core.run_source_hash_revision_available_time(output_root=root, run_id="001_no_input")
    _run_metadata(tmp_path, root, "002_metadata_present")

    result = run_source_hash_revision_available_time_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "002_metadata_present"
    assert result.latest_runtime_status == "SOURCE_REVISION_TIME_METADATA_PRESENT_REPORT_ONLY"
    assert result.latest_health_status == "PASS"
    assert result.latest_source_hash_preview == SOURCE_HASH_PREVIEW
    assert result.latest_revision_id_type == "provider_revision_id"
    assert result.latest_available_time_parseable is True
    assert result.latest_available_time_timezone_present is True
    assert result.latest_available_time_compared_to_decision_time is False
    assert result.recommended_next_task == CLI_NEXT_TASK
    assert "Research-Status" not in result.recommended_next_task
    assert "Checkpoint" not in result.recommended_next_task
    _assert_negative_fields_false(result.summary)


def test_status_does_not_expose_full_hash_or_downstream_readiness(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "status_no_leak")

    result = run_source_hash_revision_available_time_status(root=root, output_dir=root / "status")
    text = _artifact_text(result.artifact_paths.values())

    assert FULL_SOURCE_HASH not in text
    for sentinel in [
        SOURCE_CONTENT_SENTINEL,
        TARGET_CSV_SENTINEL,
        ROW_VALUE_SENTINEL,
        PRIVATE_PATH_SENTINEL,
    ]:
        assert sentinel not in text
    for phrase in UNSAFE_WORDING:
        assert phrase not in text
        assert phrase not in result.latest_runtime_status
        assert phrase not in result.recommended_next_task


def test_views_do_not_reopen_source_metadata_after_core_generation(tmp_path: Path) -> None:
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

    index = build_source_hash_revision_available_time_index(root=root, output_dir=root / "index")
    health = check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")
    status = run_source_hash_revision_available_time_status(root=root, output_dir=root / "status")

    assert artifact["source_artifact_opened"] is False
    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_run_id == "delete_inputs"


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    root = _output_root(tmp_path)
    _run_metadata(tmp_path, root, "docs_guard")

    build_source_hash_revision_available_time_index(root=root, output_dir=root / "index")
    check_source_hash_revision_available_time_health(root=root, output_dir=root / "health")
    run_source_hash_revision_available_time_status(root=root, output_dir=root / "status")

    assert not Path("docs/project_sources").exists()


def test_views_modules_and_tests_have_no_forbidden_imports_or_path_read_helpers() -> None:
    module_paths = [
        Path(inspect.getfile(build_source_hash_revision_available_time_index)),
        Path(inspect.getfile(check_source_hash_revision_available_time_health)),
        Path(inspect.getfile(run_source_hash_revision_available_time_status)),
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


def test_public_view_api_has_no_real_csv_or_hash_recompute_arguments() -> None:
    forbidden_names = {
        "source_artifact_path",
        "target_csv_path",
        "csv_path",
        "source_bytes",
        "recompute_hash",
        "expected_hash",
        "reverify_expected_hash",
        "replay_decision_time",
    }
    for func in [
        build_source_hash_revision_available_time_index,
        check_source_hash_revision_available_time_health,
        run_source_hash_revision_available_time_status,
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
            suffix=run_id,
        )
    return core.run_source_hash_revision_available_time(
        output_root=root,
        run_id=run_id,
        source_lineage_manifest_path=manifest_path,
        source_lineage_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        source_hash_validation_level="SOURCE_HASH_METADATA_PRESENT_ONLY",
        revision_id_validation_level="REVISION_ID_METADATA_PRESENT_ONLY",
        available_time_validation_level="AVAILABLE_TIME_METADATA_PRESENT_ONLY",
        pit_admissibility_level="PIT_ADMISSIBILITY_NONE",
        allow_source_revision_time_metadata=True,
    )


def _write_valid_inputs(
    tmp_path: Path,
    *,
    metadata_mutation=None,
    suffix: str = "valid",
) -> tuple[Path, Path]:
    allowed = tmp_path / "allowed"
    allowed.mkdir(parents=True, exist_ok=True)
    metadata_path = allowed / f"source_metadata_{suffix}.json"
    manifest_path = allowed / f"manifest_{suffix}.json"
    metadata = _source_metadata()
    if metadata_mutation:
        metadata_mutation(metadata)
    _write_json(metadata_path, metadata)
    _write_json(manifest_path, _manifest(metadata_path))
    return manifest_path, metadata_path


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
        "row_value_sample": ROW_VALUE_SENTINEL,
        "forbidden_downstream_flags": _false_flags(),
        "limitations": ["Metadata only."],
    }


def _false_flags() -> dict[str, bool]:
    return {field: False for field in NEGATIVE_FIELDS}


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "source_revision_time"


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
