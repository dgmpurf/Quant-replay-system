from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype import (
    ARTIFACT_FILENAMES,
    FORBIDDEN_STATUS_WORDING,
    INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
    INPUT_MODE_NO_INPUT_SYNTHETIC_DECLARATIONS,
    REQUIRED_FALSE_FLAGS,
    REQUIRED_MANIFEST_FIELDS,
    STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_BLOCKED_BY_PROTECTED_PATH,
    STATUS_MANIFEST_DECLARED_REPORT_ONLY,
    STATUS_NO_INPUT,
    STATUS_REPORT_ONLY_PASS_CANDIDATE,
    real_reviewed_local_csv_package_candidate_real_preflight_prototype_statuses,
    run_manifest_only_preflight_prototype,
)


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "manifest_only_preflight"


def _valid_manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_schema_version": "v0.1",
        "package_id": "tiny-pit-local-csv-candidate-001",
        "package_version": "0.1.0",
        "package_type": "TINY_PIT_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE",
        "package_created_at": "2026-06-30T00:00:00Z",
        "package_prepared_by": "synthetic-reviewer",
        "replay_decision_time": "2024-04-02T15:00:00+08:00",
        "source_registry_snapshot_ref": "source_registry_snapshot.json",
        "reviewed_file_manifest_ref": "reviewed_file_manifest.json",
        "table_schema_manifest_ref": "table_schema_manifest.json",
        "row_lineage_manifest_ref": "row_lineage_manifest.json",
        "available_time_manifest_ref": "available_time_manifest.json",
        "source_hash_revision_manifest_ref": "source_hash_revision_manifest.json",
        "reviewer_attestation_manifest_ref": "reviewer_attestation_manifest.json",
        "quality_review_manifest_ref": "quality_review_manifest.json",
        "limitation_manifest_ref": "limitation_manifest.json",
        "forbidden_downstream_flags_ref": "forbidden_downstream_flags.json",
        "declared_csv_read_level": "CSV_READ_NONE",
        "declared_real_csv_required": False,
        "declared_real_csv_consumed": False,
        "declared_real_package_candidate_created": False,
        "declared_active_reviewed_input_candidate_created": False,
        "declared_active_replay_input_ready_emitted": False,
        "declared_trading_allowed": False,
    }
    manifest.update({flag: False for flag in REQUIRED_FALSE_FLAGS})
    manifest.update(overrides)
    return manifest


def _write_manifest(path: Path, manifest: dict[str, object]) -> Path:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_no_input_synthetic_declarations_create_expected_artifacts_under_tmp_path(tmp_path: Path) -> None:
    result = run_manifest_only_preflight_prototype(output_root=_output_root(tmp_path))

    assert result["runtime_status"] == STATUS_NO_INPUT
    assert result["input_mode"] == INPUT_MODE_NO_INPUT_SYNTHETIC_DECLARATIONS
    assert result["health_status"] == "PASS"
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["references_followed"] is False
    assert result["local_file_hash_computed"] is False
    assert set(Path(result["artifact_path"]).iterdir()) == {
        Path(result["artifact_path"]) / name for name in ARTIFACT_FILENAMES.values()
    }
    for flag in REQUIRED_FALSE_FLAGS:
        assert result[flag] is False


def test_explicit_manifest_path_without_allowed_manifest_roots_blocks_before_reading(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path / "manifest.json", _valid_manifest())

    result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=manifest_path,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["manifest_read"] is False
    assert "allowed_manifest_roots" in ";".join(result["blocker_reasons"])


def test_valid_json_manifest_under_explicit_allowed_root_is_report_only_candidate(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path / "manifest.json", _valid_manifest())

    result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
    )

    assert result["runtime_status"] in {STATUS_MANIFEST_DECLARED_REPORT_ONLY, STATUS_REPORT_ONLY_PASS_CANDIDATE}
    assert result["pass_candidate"] is True
    assert result["manifest_read"] is True
    assert result["references_followed"] is False
    assert result["real_csv_consumed"] is False
    assert result["real_package_candidate_created"] is False
    assert result["active_replay_input_ready_emitted"] is False
    assert not (tmp_path / "reviewed_file_manifest.json").exists()


def test_manifest_outside_allowed_root_blocks(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    manifest_path = _write_manifest(outside / "manifest.json", _valid_manifest())

    result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[allowed],
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["manifest_read"] is False


def test_network_url_non_json_malformed_and_large_manifest_block(tmp_path: Path) -> None:
    network_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "network"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path="https://example.test/manifest.json",
        allowed_manifest_roots=[tmp_path],
    )
    assert network_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD

    text_path = tmp_path / "manifest.txt"
    text_path.write_text("{}", encoding="utf-8")
    text_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "text"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=text_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert text_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD

    bad_json_path = tmp_path / "bad.json"
    bad_json_path.write_text("{", encoding="utf-8")
    bad_json_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "bad-json"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=bad_json_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert bad_json_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA

    large_path = tmp_path / "large.json"
    large_path.write_text('{"x":"' + ("x" * 70000) + '"}', encoding="utf-8")
    large_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "large"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=large_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert large_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD


def test_missing_required_fields_and_bad_declared_csv_read_level_block(tmp_path: Path) -> None:
    missing = _valid_manifest()
    missing.pop("manifest_schema_version")
    missing_path = _write_manifest(tmp_path / "missing.json", missing)

    missing_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "missing"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=missing_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert missing_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert "manifest_schema_version" in ";".join(missing_result["missing_required_fields"])

    csv_read_path = _write_manifest(tmp_path / "csv_read.json", _valid_manifest(declared_csv_read_level="CSV_HEADER_ONLY"))
    csv_read_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "csv-read"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=csv_read_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert csv_read_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert csv_read_result["csv_read_level"] == "CSV_READ_NONE"


def test_declared_real_csv_consumed_true_forbidden_flag_true_and_required_false_flag_missing_block(tmp_path: Path) -> None:
    consumed_path = _write_manifest(tmp_path / "consumed.json", _valid_manifest(declared_real_csv_consumed=True))
    consumed_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "consumed"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=consumed_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert consumed_result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM

    flag_true_path = _write_manifest(tmp_path / "flag_true.json", _valid_manifest(active_replay_input=True))
    flag_true_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "flag-true"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=flag_true_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert flag_true_result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert "active_replay_input" in ";".join(flag_true_result["forbidden_flag_failures"])

    missing_flag = _valid_manifest()
    missing_flag.pop("real_replay_input_created")
    missing_flag_path = _write_manifest(tmp_path / "missing_flag.json", missing_flag)
    missing_flag_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "missing-flag"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=missing_flag_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert missing_flag_result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert "real_replay_input_created" in ";".join(missing_flag_result["missing_false_flags"])


def test_path_guard_rejects_protected_manifest_paths_and_path_traversal(tmp_path: Path) -> None:
    unsafe_manifest = tmp_path / "data" / "raw" / "manifest.json"
    unsafe_manifest.parent.mkdir(parents=True)
    _write_manifest(unsafe_manifest, _valid_manifest())
    result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "unsafe-data"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=unsafe_manifest,
        allowed_manifest_roots=[tmp_path],
    )
    assert result["runtime_status"] == STATUS_BLOCKED_BY_PROTECTED_PATH

    traversal_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "traversal"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=tmp_path / ".." / "manifest.json",
        allowed_manifest_roots=[tmp_path],
    )
    assert traversal_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD


@pytest.mark.parametrize(
    "unsafe_parts",
    [
        ("data", "raw"),
        ("data", "processed"),
        ("data", "cache"),
        ("docs", "project_sources"),
        (".env",),
        ("secrets",),
        ("auth",),
        ("token",),
        ("credential",),
    ],
)
def test_output_root_protected_paths_are_rejected(tmp_path: Path, unsafe_parts: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        run_manifest_only_preflight_prototype(output_root=tmp_path.joinpath(*unsafe_parts))


def test_references_are_declared_but_not_followed_and_forbidden_reference_strings_block(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path / "manifest.json", _valid_manifest(reviewed_file_manifest_ref="missing.json"))
    result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "declared"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert result["runtime_status"] in {STATUS_MANIFEST_DECLARED_REPORT_ONLY, STATUS_REPORT_ONLY_PASS_CANDIDATE}
    assert result["references_followed"] is False

    forbidden_ref_path = _write_manifest(
        tmp_path / "forbidden_ref.json",
        _valid_manifest(available_time_manifest_ref="https://example.test/available_time.json"),
    )
    forbidden_result = run_manifest_only_preflight_prototype(
        output_root=_output_root(tmp_path / "forbidden-ref"),
        input_mode=INPUT_MODE_EXPLICIT_MANIFEST_METADATA_ONLY,
        package_manifest_path=forbidden_ref_path,
        allowed_manifest_roots=[tmp_path],
    )
    assert forbidden_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert forbidden_result["references_followed"] is False


def test_runtime_status_vocabulary_excludes_forbidden_status_wording() -> None:
    statuses = real_reviewed_local_csv_package_candidate_real_preflight_prototype_statuses()

    for forbidden in FORBIDDEN_STATUS_WORDING:
        assert forbidden not in statuses
    assert "ACTIVE_REPLAY_INPUT_READY" not in statuses


def test_public_api_does_not_accept_reviewed_csv_or_package_root_arguments() -> None:
    parameters = inspect.signature(run_manifest_only_preflight_prototype).parameters

    assert "reviewed_csv_path" not in parameters
    assert "package_root" not in parameters
    assert "csv_path" not in parameters
    assert "manifest_path" not in parameters
    assert "package_manifest_path" in parameters


def test_required_artifact_files_and_csv_reports_parse(tmp_path: Path) -> None:
    result = run_manifest_only_preflight_prototype(output_root=_output_root(tmp_path))
    artifact_path = Path(result["artifact_path"])

    assert {path.name for path in artifact_path.iterdir()} == set(ARTIFACT_FILENAMES.values())
    assert json.loads((artifact_path / "metadata.json").read_text(encoding="utf-8"))["runtime_status"] == STATUS_NO_INPUT
    assert (artifact_path / "preflight_prototype_report.md").read_text(encoding="utf-8").strip()
    assert (artifact_path / "limitations.md").read_text(encoding="utf-8").strip()
    for csv_name in [
        "package_manifest_inspection.csv",
        "path_guard_report.csv",
        "manifest_schema_presence.csv",
        "manifest_reference_presence.csv",
    ]:
        assert (artifact_path / csv_name).read_text(encoding="utf-8").splitlines()[0]


def test_no_docs_project_sources_or_protected_data_writes(tmp_path: Path) -> None:
    result = run_manifest_only_preflight_prototype(output_root=_output_root(tmp_path))

    assert not Path("docs/project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert result["data_raw_written"] is False
    assert result["data_processed_written"] is False
    assert result["data_cache_written"] is False


def test_required_manifest_fields_are_explicit_and_stable() -> None:
    assert set(REQUIRED_MANIFEST_FIELDS).issubset(_valid_manifest())
    assert "declared_csv_read_level" in REQUIRED_MANIFEST_FIELDS
    assert "forbidden_downstream_flags_ref" in REQUIRED_MANIFEST_FIELDS

