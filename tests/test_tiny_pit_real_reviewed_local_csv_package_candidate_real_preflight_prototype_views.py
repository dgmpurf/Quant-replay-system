from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype import (
    ARTIFACT_FILENAMES,
    REQUIRED_FALSE_FLAGS,
    STATUS_NO_INPUT,
    STATUS_REPORT_ONLY_PASS_CANDIDATE,
    run_manifest_only_preflight_prototype,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health import (
    check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index import (
    build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status import (
    VIEWS_NEXT_ACTION,
    run_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status,
)


def _root(tmp_path: Path) -> Path:
    return (
        tmp_path
        / "outputs"
        / "reports"
        / "manual_diagnostics"
        / "tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_v0_1"
    )


def _build_run(tmp_path: Path, *, run_id: str = "run_a") -> dict[str, object]:
    return run_manifest_only_preflight_prototype(output_root=_root(tmp_path), run_id=run_id)


def _metadata(artifact_path: Path) -> dict[str, object]:
    return json.loads((artifact_path / "metadata.json").read_text(encoding="utf-8"))


def _write_metadata(artifact_path: Path, metadata: dict[str, object]) -> None:
    (artifact_path / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.health_frame.to_dict("records")}


def test_index_discovers_no_input_artifact_ignores_view_dirs_and_skips_malformed_metadata(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path, run_id="run_a")
    for view_dir in ["index", "health", "status"]:
        (root / view_dir).mkdir(parents=True, exist_ok=True)
    malformed = root / "malformed"
    malformed.mkdir()
    (malformed / "metadata.json").write_text("{bad json", encoding="utf-8")

    result = build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index(
        root=root,
        output_dir=root / "index",
    )

    assert result.artifact_count == 1
    assert result.latest_run_id == run["run_id"]
    assert result.latest_runtime_status == STATUS_NO_INPUT
    assert result.latest_health_status == "PASS"
    assert result.index_frame.iloc[0]["report_only"] is True
    assert result.index_frame.iloc[0]["diagnostic_only"] is True
    assert result.index_frame.iloc[0]["real_manifest_read"] is False
    assert result.index_frame.iloc[0]["references_followed"] is False
    assert result.index_frame.iloc[0]["local_file_hash_computed"] is False
    assert result.index_frame.iloc[0]["real_csv_consumed"] is False
    assert result.index_frame.iloc[0]["active_replay_input_ready_emitted"] is False
    assert result.index_frame.iloc[0]["trading_allowed"] is False
    assert result.warnings
    assert not any(row["run_id"] in {"index", "health", "status"} for row in result.index_frame.to_dict("records"))


def test_health_passes_for_safe_report_only_no_input_artifact(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_run(tmp_path)

    result = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_health_passes_for_safe_blocked_or_pass_candidate_report_only_statuses(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    artifact_path = Path(str(run["artifact_path"]))
    metadata = _metadata(artifact_path)
    metadata["runtime_status"] = STATUS_REPORT_ONLY_PASS_CANDIDATE
    metadata["status"] = STATUS_REPORT_ONLY_PASS_CANDIDATE
    metadata["pass_candidate"] = True
    _write_metadata(artifact_path, metadata)

    result = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "PASS"
    assert result.error_count == 0


def test_health_fails_for_missing_required_artifact(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    (Path(str(run["artifact_path"])) / "limitations.md").unlink()

    result = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_for_forbidden_runtime_status(tmp_path: Path) -> None:
    root = _root(tmp_path)
    run = _build_run(tmp_path)
    artifact_path = Path(str(run["artifact_path"]))
    metadata = _metadata(artifact_path)
    metadata["runtime_status"] = "ACTIVE_REPLAY_INPUT_READY"
    metadata["status"] = "ACTIVE_REPLAY_INPUT_READY"
    _write_metadata(artifact_path, metadata)

    result = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=root / "health",
    )

    assert result.status == "FAIL"
    assert "INVALID_RUNTIME_STATUS" in _issue_codes(result)
    assert "FORBIDDEN_STATUS_WORDING" in _issue_codes(result)


def test_health_fails_for_unsafe_metadata_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    for field in [
        "csv_read_level",
        "references_followed",
        "local_file_hash_computed",
        "external_source_validated",
        "pit_admissibility_validated",
        "active_replay_input_ready_emitted",
        "trading_allowed",
        "data_raw_written",
        "data_processed_written",
        "data_cache_written",
    ]:
        run = _build_run(tmp_path, run_id=f"bad_{field}")
        artifact_path = Path(str(run["artifact_path"]))
        metadata = _metadata(artifact_path)
        metadata[field] = "CSV_HEADER_ONLY" if field == "csv_read_level" else True
        _write_metadata(artifact_path, metadata)

        result = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
            root=root,
            output_dir=root / "health",
        )
        assert result.status == "FAIL"


def test_status_selects_latest_deterministically_and_preserves_safe_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    older = _build_run(tmp_path, run_id="aaa_older")
    older_path = Path(str(older["artifact_path"]))
    older_metadata = _metadata(older_path)
    older_metadata["created_at"] = "2026-01-01T00:00:00Z"
    _write_metadata(older_path, older_metadata)

    newer = _build_run(tmp_path, run_id="zzz_newer")
    newer_path = Path(str(newer["artifact_path"]))
    newer_metadata = _metadata(newer_path)
    newer_metadata["created_at"] = "2026-02-01T00:00:00Z"
    _write_metadata(newer_path, newer_metadata)

    result = run_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status(
        root=root,
        output_dir=root / "status",
    )

    assert result.latest_run_id == "zzz_newer"
    assert result.latest_runtime_status == STATUS_NO_INPUT
    assert result.latest_health_status == "PASS"
    assert result.csv_read_level == "CSV_READ_NONE"
    assert result.recommended_next_task == VIEWS_NEXT_ACTION
    for flag in REQUIRED_FALSE_FLAGS:
        assert getattr(result, flag) is False
    assert "Post-Checkpoint Governance Audit Report-Only" in result.recommended_next_task
    assert "Research-Status and Checkpoint Report-Only" not in result.recommended_next_task
    assert "ACTIVE_REPLAY_INPUT_READY" not in result.latest_runtime_status
    assert "TRADING_READY" not in result.latest_runtime_status
    assert "PERFORMANCE_VALIDATED" not in result.latest_runtime_status


def test_cli_core_index_health_status_smoke_has_no_real_path_arguments(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}

    commands = [
        "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype",
        "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-index",
        "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-health",
        "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-status",
    ]
    for command in commands:
        help_result = subprocess.run(
            [sys.executable, "-m", "quant_replay_system.cli", command, "--help"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        assert "package_manifest_path" not in help_result.stdout
        assert "allowed_manifest_roots" not in help_result.stdout
        assert "reviewed-csv" not in help_result.stdout.lower()
        assert "package-root" not in help_result.stdout.lower()

    core = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert f"runtime_status: {STATUS_NO_INPUT}" in core.stdout
    assert "csv_read_level: CSV_READ_NONE" in core.stdout
    assert "real_csv_consumed: False" in core.stdout
    assert "active_replay_input_ready_emitted: False" in core.stdout
    assert "trading_allowed: False" in core.stdout

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-index",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "latest_runtime_status:" in index.stdout

    health = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-health",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "health_status: PASS" in health.stdout

    status = subprocess.run(
        [
            sys.executable,
            "-m",
            "quant_replay_system.cli",
            "tiny-pit-real-reviewed-local-csv-package-candidate-real-preflight-prototype-status",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert f"latest_runtime_status: {STATUS_NO_INPUT}" in status.stdout
    assert "recommended_next_task: Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Manifest-Only Preflight Prototype Post-Checkpoint Governance Audit Report-Only v0.1" in status.stdout
    assert "Research-Status and Checkpoint Report-Only v0.1" not in status.stdout
    assert "active_replay_input_ready_emitted: False" in status.stdout
    assert "trading_allowed: False" in status.stdout
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()


def test_views_write_only_expected_view_artifacts_under_root(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _build_run(tmp_path)
    index = build_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_index(
        root=root,
        output_dir=root / "index",
    )
    health = check_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_health(
        root=root,
        output_dir=root / "health",
    )
    status = run_tiny_pit_real_reviewed_local_csv_package_candidate_real_preflight_prototype_status(
        root=root,
        output_dir=root / "status",
    )

    assert index.artifact_paths["index_csv"].is_file()
    assert health.artifact_paths["health_csv"].is_file()
    assert status.artifact_paths["status_csv"].is_file()
    run_dir = next(path for path in root.iterdir() if path.is_dir() and path.name not in {"index", "health", "status"})
    assert set(ARTIFACT_FILENAMES.values()).issubset({path.name for path in run_dir.iterdir()})
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()
    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not Path("docs/project_sources").exists()
