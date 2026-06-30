from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following import (
    ARTIFACT_FILENAMES,
    INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
    REQUIRED_FALSE_FLAGS,
    STATUS_FOLLOWED_REPORT_ONLY,
    STATUS_NO_INPUT,
    run_metadata_reference_following,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_health import (
    check_metadata_reference_following_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_index import (
    build_metadata_reference_following_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_status import (
    VIEWS_NEXT_ACTION,
    run_metadata_reference_following_status,
)


def _root(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_real_reviewed_local_csv_package_candidate_metadata_reference_following_v0_1"
    )


def _metadata(path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema_version": "v0.1",
        "available_time": "2024-04-02T15:00:00+08:00",
        "source_hash": "sha256:fixture",
        "revision_id": "rev-001",
        "limitation_note": "fixture limitation",
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _manifest(path: Path, metadata_path: Path) -> Path:
    payload = {
        "package_id": "tiny-pit-local-csv-candidate-001",
        "package_schema_version": "v0.1",
        "created_at": "2026-06-30T00:00:00Z",
        "prepared_by": "synthetic-reviewer",
        "report_only": True,
        "diagnostic_only": True,
        "inspection_level": INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
        "metadata_references": [
            {
                "reference_type": "source_registry_snapshot_ref",
                "reference_name": "source-registry",
                "path": str(metadata_path),
                "required": True,
                "expected_schema_version": "v0.1",
                "declared_only": False,
                "notes": "synthetic metadata reference",
            }
        ],
        "forbidden_downstream_flags": {flag: False for flag in REQUIRED_FALSE_FLAGS},
        "limitations": ["metadata-reference-following view fixture"],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_no_input(tmp_path: Path, *, run_id: str = "run_a") -> dict[str, object]:
    return run_metadata_reference_following(output_root=_root(tmp_path), run_id=run_id)


def _build_followed(tmp_path: Path, *, run_id: str = "run_followed") -> dict[str, object]:
    root = _root(tmp_path)
    metadata_path = _metadata(tmp_path / "metadata" / "source_registry_snapshot.json")
    manifest_path = _manifest(tmp_path / "manifest.json", metadata_path)
    return run_metadata_reference_following(
        output_root=root,
        package_manifest_path=manifest_path,
        allowed_manifest_roots=[tmp_path],
        inspection_level=INSPECTION_LEVEL_FOLLOWED_METADATA_ONLY,
        run_id=run_id,
    )


def _artifact_metadata(artifact_path: Path) -> dict[str, object]:
    return json.loads((artifact_path / "metadata.json").read_text(encoding="utf-8"))


def _write_artifact_metadata(artifact_path: Path, payload: dict[str, object]) -> None:
    (artifact_path / "metadata.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.health_frame.to_dict("records")}


def test_index_discovers_metadata_reference_artifacts_and_ignores_view_dirs(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = _build_no_input(tmp_path, run_id="aaa_first")
    second = _build_followed(tmp_path, run_id="zzz_second")
    for view_dir in ["index", "health", "status"]:
        (root / view_dir).mkdir(parents=True, exist_ok=True)

    result = build_metadata_reference_following_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 2
    assert result.latest_run_id == second["run_id"]
    assert result.latest_runtime_status == STATUS_FOLLOWED_REPORT_ONLY
    assert result.latest_health_status == "PASS"
    assert result.index_frame.iloc[0]["csv_read_level"] == "CSV_READ_NONE"
    assert set(result.index_frame["run_id"]) == {first["run_id"], second["run_id"]}
    assert not any(row["run_id"] in {"index", "health", "status"} for row in result.index_frame.to_dict("records"))


def test_health_passes_for_safe_report_only_metadata_reference_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_followed(tmp_path)

    result = check_metadata_reference_following_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_health_fails_for_missing_required_artifact(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_no_input(tmp_path)
    (Path(str(run["artifact_path"])) / "limitations.md").unlink()

    result = check_metadata_reference_following_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_for_unsafe_metadata_flags_and_csv_read_level(tmp_path: Path) -> None:
    root = _root(tmp_path)
    for field in [
        "csv_read_level",
        "real_csv_consumed",
        "active_replay_input_ready_emitted",
        "trading_allowed",
        "buy_review_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]:
        run = _build_no_input(tmp_path, run_id=f"bad_{field}")
        artifact_path = Path(str(run["artifact_path"]))
        metadata = _artifact_metadata(artifact_path)
        metadata[field] = "CSV_HEADER_ONLY" if field == "csv_read_level" else True
        _write_artifact_metadata(artifact_path, metadata)

        result = check_metadata_reference_following_health(root=root, output_dir=root / "health")
        assert result.status == "FAIL"


def test_health_fails_for_forbidden_downstream_flags_file(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_no_input(tmp_path)
    artifact_path = Path(str(run["artifact_path"]))
    flags = {flag: False for flag in REQUIRED_FALSE_FLAGS}
    flags["trading_allowed"] = True
    (artifact_path / "forbidden_downstream_flags.json").write_text(
        json.dumps(flags, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = check_metadata_reference_following_health(root=root, output_dir=root / "health")

    assert result.status == "FAIL"
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in _issue_codes(result)


def test_status_selects_latest_and_preserves_compact_safety_summary(tmp_path: Path) -> None:
    root = _root(tmp_path)
    older = _build_no_input(tmp_path, run_id="aaa_older")
    older_path = Path(str(older["artifact_path"]))
    older_metadata = _artifact_metadata(older_path)
    older_metadata["created_at"] = "2026-01-01T00:00:00Z"
    _write_artifact_metadata(older_path, older_metadata)

    newer = _build_followed(tmp_path, run_id="zzz_newer")
    newer_path = Path(str(newer["artifact_path"]))
    newer_metadata = _artifact_metadata(newer_path)
    newer_metadata["created_at"] = "2026-02-01T00:00:00Z"
    _write_artifact_metadata(newer_path, newer_metadata)

    result = run_metadata_reference_following_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "zzz_newer"
    assert result.latest_runtime_status == STATUS_FOLLOWED_REPORT_ONLY
    assert result.latest_health_status == "PASS"
    assert result.csv_read_level == "CSV_READ_NONE"
    assert result.references_followed is True
    assert result.metadata_files_followed_count == 1
    assert result.recommended_next_task == VIEWS_NEXT_ACTION
    for flag in REQUIRED_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.latest_runtime_status


def test_views_write_only_expected_view_artifacts_under_root(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_no_input(tmp_path)

    index = build_metadata_reference_following_index(root=root, output_dir=root / "index")
    health = check_metadata_reference_following_health(root=root, output_dir=root / "health")
    status = run_metadata_reference_following_status(root=root, output_dir=root / "status")

    assert index.artifact_paths["index_csv"].is_file()
    assert health.artifact_paths["health_csv"].is_file()
    assert status.artifact_paths["status_csv"].is_file()
    run_dir = next(path for path in root.iterdir() if path.is_dir() and path.name not in {"index", "health", "status"})
    assert set(ARTIFACT_FILENAMES.values()).issubset({path.name for path in run_dir.iterdir()})
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not Path("docs/project_sources").exists()


def test_no_artifact_status_is_report_only_and_no_input_context(tmp_path: Path) -> None:
    root = _root(tmp_path)

    result = run_metadata_reference_following_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == ""
    assert result.latest_runtime_status == STATUS_NO_INPUT
    assert result.latest_health_status == "WARN"
    assert result.report_only is True
    assert result.diagnostic_only is True
    assert result.csv_read_level == "CSV_READ_NONE"
    assert result.trading_allowed is False
    assert result.data_raw_written is False
