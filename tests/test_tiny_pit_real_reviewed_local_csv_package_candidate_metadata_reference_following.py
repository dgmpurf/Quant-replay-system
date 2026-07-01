from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following import (
    ALLOWED_METADATA_REFERENCE_TYPES,
    ARTIFACT_FILENAMES,
    FORBIDDEN_STATUS_WORDING,
    INSPECTION_LEVEL_DECLARED_ONLY,
    INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY,
    INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    INSPECTION_LEVEL_NO_INPUT,
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE,
    STATUS_BLOCKED_BY_MALFORMED_METADATA,
    STATUS_BLOCKED_BY_MANIFEST_SCHEMA,
    STATUS_BLOCKED_BY_METADATA_SCHEMA,
    STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA,
    STATUS_BLOCKED_BY_PATH_GUARD,
    STATUS_DECLARED_REPORT_ONLY,
    STATUS_FOLLOWED_REPORT_ONLY,
    STATUS_NO_INPUT,
    STATUS_WARN_REVIEW_REQUIRED,
    metadata_reference_following_statuses,
    run_metadata_reference_following,
)


EXPECTED_NEXT_BOUNDARY_DESIGN_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Metadata-Reference-Following "
    "Next Boundary Design Planning Report-Only v0.1"
)
STALE_NEXT_ACTION_PHRASES = [
    "CLI or Research-Status Planning",
    "Research-Status and Checkpoint",
    "Artifact Views / Index / Health / Status",
    "checkpoint planning",
]


def _output_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "metadata_reference_following"


def _metadata_file(path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema_version": "v0.1",
        "metadata_kind": "syntactic_fixture_metadata",
        "available_time": "2024-04-02T15:00:00+08:00",
        "source_hash": "sha256:fixture",
        "revision_id": "rev-001",
        "reviewer_id": "reviewer-fixture",
        "quality_status": "accepted_for_review_context_only",
        "limitation_note": "Synthetic metadata-only fixture.",
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _manifest(root: Path, refs: list[dict[str, object]] | None = None, **overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "package_id": "tiny-pit-real-reviewed-local-csv-candidate-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-06-30T00:00:00Z",
        "prepared_by": "synthetic-reviewer",
        "report_only": True,
        "diagnostic_only": True,
        "inspection_level": INSPECTION_LEVEL_DECLARED_ONLY,
        "metadata_references": refs if refs is not None else [],
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
        "limitations": ["metadata-reference-following is report-only and CSV_READ_NONE"],
    }
    manifest.update(overrides)
    return manifest


def _write_manifest(path: Path, manifest: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _ref(reference_type: str, path: Path | str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "reference_type": reference_type,
        "reference_name": f"{reference_type}-fixture",
        "path": str(path),
        "required": True,
        "expected_schema_version": "v0.1",
        "declared_only": False,
        "notes": "synthetic metadata reference",
    }
    row.update(overrides)
    return row


def test_no_input_remains_synthetic_report_only(tmp_path: Path) -> None:
    result = run_metadata_reference_following(output_root=_output_root(tmp_path))

    assert result["runtime_status"] == STATUS_NO_INPUT
    assert result["inspection_level"] == INSPECTION_LEVEL_NO_INPUT
    assert result["health_status"] == "PASS"
    assert result["report_only"] is True
    assert result["diagnostic_only"] is True
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["real_manifest_read"] is False
    assert result["references_followed"] is False
    assert result["local_file_hash_computed"] is False
    assert all(result[flag] is False for flag in REQUIRED_FALSE_FLAGS)
    assert result["recommended_next_task"] == EXPECTED_NEXT_BOUNDARY_DESIGN_TASK
    for phrase in STALE_NEXT_ACTION_PHRASES:
        assert phrase not in result["recommended_next_task"]
    assert "CSV header allowed" not in result["recommended_next_task"]
    assert "row count allowed" not in result["recommended_next_task"]
    assert "file hash allowed" not in result["recommended_next_task"]


def test_explicit_manifest_requires_explicit_allowed_roots(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path / "manifest.json", _manifest(tmp_path))

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        inspection_level=INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD
    assert result["real_manifest_read"] is False
    assert "allowed_manifest_roots" in ";".join(result["blocker_reasons"])


def test_explicit_manifest_metadata_only_reads_top_level_manifest_only(tmp_path: Path) -> None:
    missing_ref = tmp_path / "missing_metadata.json"
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", missing_ref)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_EXPLICIT_MANIFEST_METADATA_ONLY,
    )

    assert result["runtime_status"] == STATUS_DECLARED_REPORT_ONLY
    assert result["real_manifest_read"] is True
    assert result["references_declared"] is True
    assert result["references_followed"] is False
    assert result["metadata_files_followed_count"] == 0


def test_declared_only_validates_references_without_opening_metadata_refs(tmp_path: Path) -> None:
    missing_ref = tmp_path / "declared_but_not_opened.json"
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("available_time_manifest_ref", missing_ref)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )

    assert result["runtime_status"] == STATUS_DECLARED_REPORT_ONLY
    assert result["references_followed"] is False
    assert result["metadata_files_followed_count"] == 0


def test_followed_mode_reads_whitelisted_metadata_json_only(tmp_path: Path) -> None:
    metadata_path = _metadata_file(tmp_path / "metadata" / "source_registry_snapshot.json")
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", metadata_path)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )

    assert result["runtime_status"] == STATUS_FOLLOWED_REPORT_ONLY
    assert result["health_status"] == "PASS"
    assert result["references_followed"] is True
    assert result["metadata_files_followed_count"] == 1
    assert result["csv_read_level"] == "CSV_READ_NONE"


@pytest.mark.parametrize(
    ("bad_path", "expected_status"),
    [
        ("../metadata.json", STATUS_BLOCKED_BY_PATH_GUARD),
        ("https://example.test/metadata.json", STATUS_BLOCKED_BY_PATH_GUARD),
        ("data/raw/metadata.json", STATUS_BLOCKED_BY_PATH_GUARD),
        ("docs/project_sources/metadata.json", STATUS_BLOCKED_BY_PATH_GUARD),
        ("secrets/metadata.json", STATUS_BLOCKED_BY_PATH_GUARD),
        ("reviewed.csv", STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE),
    ],
)
def test_path_guard_rejects_traversal_urls_protected_paths_and_direct_csv_paths(
    tmp_path: Path, bad_path: str, expected_status: str
) -> None:
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", bad_path)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )

    assert result["runtime_status"] == expected_status
    assert result["references_followed"] is False


def test_symlink_escape_rejected_if_platform_supports_symlinks(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    allowed = tmp_path / "allowed"
    outside.mkdir()
    allowed.mkdir()
    outside_metadata = _metadata_file(outside / "metadata.json")
    link = allowed / "linked_metadata.json"
    try:
        link.symlink_to(outside_metadata)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")
    manifest_path = _write_manifest(
        allowed / "manifest.json",
        _manifest(allowed, [_ref("source_registry_snapshot_ref", link)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[allowed],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD


def test_package_root_and_reviewed_csv_input_arguments_are_not_public_api() -> None:
    parameters = inspect.signature(run_metadata_reference_following).parameters

    assert "package_root" not in parameters
    assert "reviewed_csv_path" not in parameters
    assert "csv_path" not in parameters
    assert "package_manifest_path" in parameters


def test_forbidden_reference_type_and_forbidden_extension_block_without_opening_target(tmp_path: Path) -> None:
    missing_csv = tmp_path / "not_created.csv"
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("reviewed_csv_path", missing_csv)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE
    assert result["forbidden_data_references_count"] == 1
    assert missing_csv.exists() is False


def test_malformed_top_level_manifest_and_malformed_metadata_block(tmp_path: Path) -> None:
    bad_manifest = tmp_path / "bad_manifest.json"
    bad_manifest.write_text("{", encoding="utf-8")
    manifest_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "bad-manifest"),
        package_manifest_path=bad_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )
    assert manifest_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA

    bad_metadata = tmp_path / "bad_metadata.json"
    bad_metadata.write_text("{", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", bad_metadata)]),
    )
    metadata_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "bad-metadata"),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )
    assert metadata_result["runtime_status"] == STATUS_BLOCKED_BY_MALFORMED_METADATA


def test_missing_required_metadata_blocks_and_missing_optional_metadata_warns(tmp_path: Path) -> None:
    required_manifest = _write_manifest(
        tmp_path / "required_manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", tmp_path / "missing_required.json", required=True)]),
    )
    required_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "required"),
        package_manifest_path=required_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )
    assert required_result["runtime_status"] == STATUS_BLOCKED_BY_MISSING_REQUIRED_METADATA

    optional_manifest = _write_manifest(
        tmp_path / "optional_manifest.json",
        _manifest(tmp_path, [_ref("limitation_manifest_ref", tmp_path / "missing_optional.json", required=False)]),
    )
    optional_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "optional"),
        package_manifest_path=optional_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )
    assert optional_result["runtime_status"] == STATUS_WARN_REVIEW_REQUIRED
    assert optional_result["health_status"] == "WARN"


def test_reference_depth_reference_count_cap_and_metadata_size_cap_block(tmp_path: Path) -> None:
    nested = tmp_path / "nested.json"
    _metadata_file(nested, metadata_references=[{"path": "second_depth.json"}])
    nested_manifest = _write_manifest(
        tmp_path / "nested_manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", nested)]),
    )
    nested_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "nested"),
        package_manifest_path=nested_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )
    assert nested_result["runtime_status"] == STATUS_BLOCKED_BY_METADATA_SCHEMA

    refs = [_ref("source_registry_snapshot_ref", tmp_path / f"m{i}.json", reference_name=f"ref-{i}") for i in range(25)]
    count_manifest = _write_manifest(tmp_path / "count_manifest.json", _manifest(tmp_path, refs))
    count_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "count"),
        package_manifest_path=count_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )
    assert count_result["runtime_status"] == STATUS_BLOCKED_BY_MANIFEST_SCHEMA

    large_metadata = tmp_path / "large_metadata.json"
    large_metadata.write_text(json.dumps({"schema_version": "v0.1", "payload": "x" * 300000}), encoding="utf-8")
    large_manifest = _write_manifest(
        tmp_path / "large_manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", large_metadata)]),
    )
    large_result = run_metadata_reference_following(
        output_root=_output_root(tmp_path / "large"),
        package_manifest_path=large_manifest,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )
    assert large_result["runtime_status"] == STATUS_BLOCKED_BY_PATH_GUARD


def test_deterministic_reference_ordering(tmp_path: Path) -> None:
    first = _metadata_file(tmp_path / "b.json")
    second = _metadata_file(tmp_path / "a.json")
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(
            tmp_path,
            [
                _ref("reviewer_attestation_manifest_ref", first, reference_name="z-ref"),
                _ref("source_registry_snapshot_ref", second, reference_name="a-ref"),
            ],
        ),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )

    rows = result["metadata_reference_inspection"]
    assert [(row["reference_type"], row["reference_name"]) for row in rows] == [
        ("reviewer_attestation_manifest_ref", "z-ref"),
        ("source_registry_snapshot_ref", "a-ref"),
    ]


def test_syntactic_timestamp_available_time_source_hash_and_revision_checks(tmp_path: Path) -> None:
    bad_time = _metadata_file(tmp_path / "bad_time.json", available_time="not-a-timestamp")
    no_hash = _metadata_file(tmp_path / "no_hash.json", source_hash="")
    no_revision = _metadata_file(tmp_path / "no_revision.json", revision_id="")
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(
            tmp_path,
            [
                _ref("available_time_manifest_ref", bad_time),
                _ref("source_hash_revision_manifest_ref", no_hash, reference_name="no-hash"),
                _ref("source_hash_revision_manifest_ref", no_revision, reference_name="no-revision"),
            ],
        ),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_METADATA_SCHEMA
    assert result["available_time_metadata_blocker_count"] == 1
    assert result["source_hash_revision_metadata_blocker_count"] == 2
    assert result["pit_admissibility_validated"] is False
    assert result["external_source_validated"] is False


def test_all_required_artifacts_are_written_and_parse(tmp_path: Path) -> None:
    metadata_path = _metadata_file(tmp_path / "metadata.json")
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("source_registry_snapshot_ref", metadata_path)]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    )

    artifact_path = Path(result["artifact_path"])
    assert {path.name for path in artifact_path.iterdir()} == set(ARTIFACT_FILENAMES.values())
    assert json.loads((artifact_path / "metadata.json").read_text(encoding="utf-8"))["run_id"] == result["run_id"]
    assert (artifact_path / "metadata_reference_following_report.md").read_text(encoding="utf-8").strip()
    assert (artifact_path / "limitations.md").read_text(encoding="utf-8").strip()
    for csv_name in [
        "package_manifest_inspection.csv",
        "metadata_reference_inspection.csv",
        "metadata_path_guard.csv",
        "forbidden_data_reference.csv",
        "available_time_metadata_inspection.csv",
        "source_hash_revision_metadata_inspection.csv",
        "reviewer_quality_limitation_metadata_inspection.csv",
    ]:
        assert (artifact_path / csv_name).read_text(encoding="utf-8").splitlines()[0]


def test_status_vocabulary_and_runtime_statuses_exclude_forbidden_wording() -> None:
    statuses = metadata_reference_following_statuses()

    assert set(ALLOWED_METADATA_REFERENCE_TYPES)
    for forbidden in FORBIDDEN_STATUS_WORDING:
        assert forbidden not in statuses
    assert "ACTIVE_REPLAY_INPUT_READY" not in statuses


def test_no_csv_header_row_count_content_hash_or_data_writes(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path / "manifest.json",
        _manifest(tmp_path, [_ref("data_file_ref", tmp_path / "never_opened.csv")]),
    )

    result = run_metadata_reference_following(
        output_root=_output_root(tmp_path),
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_DECLARED_ONLY,
    )

    assert result["runtime_status"] == STATUS_BLOCKED_BY_FORBIDDEN_DATA_REFERENCE
    assert result["csv_read_level"] == "CSV_READ_NONE"
    assert result["local_file_hash_computed"] is False
    assert result["real_csv_consumed"] is False
    assert result["data_raw_written"] is False
    assert result["data_processed_written"] is False
    assert result["data_cache_written"] is False
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def test_module_source_does_not_import_forbidden_data_loaders() -> None:
    import quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following as module

    source = inspect.getsource(module)

    forbidden_snippets = ["pandas", "read_csv", "openpyxl", "pyarrow", "requests", "hashlib"]
    for snippet in forbidden_snippets:
        assert snippet not in source
