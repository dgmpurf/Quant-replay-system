from __future__ import annotations

import json
from pathlib import Path

from quant_replay_system import tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification as core
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_health import (
    check_expected_hash_verification_health,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_index import (
    build_expected_hash_verification_index,
)
from quant_replay_system.tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_status import (
    run_expected_hash_verification_status,
)


EXPECTED_FULL_HASH = "a" * 64
ACTUAL_FULL_HASH = "b" * 64
MATCHING_FULL_HASH = "c" * 64
PREVIEW_CHARS = 16
STATUS_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Expected-Hash Verification "
    "Research-Status Planning Report-Only v0.1"
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


def test_index_discovers_no_input_matched_and_mismatched_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_expected_hash_verification(output_root=root, run_id="001_no_input")
    _run_core(tmp_path, "002_matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _run_core(tmp_path, "003_mismatch", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = build_expected_hash_verification_index(root=root, output_dir=root / "index")

    assert result.artifact_count == 3
    rows = {row["run_id"]: row for row in result.index_frame.to_dict("records")}
    assert rows["001_no_input"]["runtime_status"] == "NO_EXPECTED_HASH_VERIFICATION_INPUT"
    assert rows["002_matched"]["runtime_status"] == "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"
    assert rows["003_mismatch"]["runtime_status"] == "EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY"
    assert rows["002_matched"]["expected_hash_preview"] == MATCHING_FULL_HASH[:PREVIEW_CHARS]
    assert rows["003_mismatch"]["actual_local_file_byte_hash_preview"] == ACTUAL_FULL_HASH[:PREVIEW_CHARS]
    assert rows["003_mismatch"]["expected_hash_mismatch"] is True
    assert rows["003_mismatch"]["expected_hash_verified_against_source_hash"] is False
    assert rows["003_mismatch"]["source_hash_validated"] is False
    assert rows["003_mismatch"]["revision_id_validated"] is False
    assert rows["003_mismatch"]["available_time_validated"] is False
    assert rows["003_mismatch"]["pit_admissibility_validated"] is False
    assert rows["003_mismatch"]["source_reliability_scored"] is False
    assert rows["003_mismatch"]["reviewer_authority_validated"] is False
    assert rows["003_mismatch"]["local_file_byte_hash_recomputed"] is False
    assert rows["003_mismatch"]["target_file_opened_for_expected_hash_verification"] is False
    assert rows["003_mismatch"]["real_csv_consumed"] is False


def test_index_output_is_preview_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core(tmp_path, "mismatch", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = build_expected_hash_verification_index(root=root, output_dir=root / "index")
    text = _view_text(result.artifact_paths)

    assert EXPECTED_FULL_HASH not in text
    assert ACTUAL_FULL_HASH not in text
    assert EXPECTED_FULL_HASH[:PREVIEW_CHARS] in text
    assert ACTUAL_FULL_HASH[:PREVIEW_CHARS] in text


def test_health_pass_for_no_input_and_matched_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_expected_hash_verification(output_root=root, run_id="001_no_input")
    _run_core(tmp_path, "002_matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    result = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert result.status == "PASS"
    assert result.checked_artifact_count == 2
    assert result.issue_count == 0
    assert result.error_count == 0
    assert result.warning_count == 0


def test_health_warn_for_mismatched_artifact_without_crash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core(tmp_path, "mismatch", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert result.warning_count >= 1
    assert "EXPECTED_HASH_MISMATCH_ACTIONABLE" in set(result.health_frame["issue_code"])


def test_health_fails_for_full_expected_or_actual_hash_leakage_without_echoing_hash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "leak", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)
    Path(result["artifact_paths"]["report"]).write_text(
        f"leaked expected {EXPECTED_FULL_HASH} and actual {ACTUAL_FULL_HASH}",
        encoding="utf-8",
    )

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")
    health_text = _view_text(health.artifact_paths)

    assert health.status == "FAIL"
    assert "FULL_HASH_DISCLOSURE_LEAK" in set(health.health_frame["issue_code"])
    assert EXPECTED_FULL_HASH not in health_text
    assert ACTUAL_FULL_HASH not in health_text


def test_health_fails_for_unsupported_algorithm(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "bad_algorithm", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(result, expected_hash_algorithm="MD5")

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "UNSUPPORTED_EXPECTED_HASH_ALGORITHM" in set(health.health_frame["issue_code"])


def test_health_fails_for_missing_required_artifact(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "missing_report", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    Path(result["artifact_paths"]["report"]).unlink()

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in set(health.health_frame["issue_code"])


def test_health_fails_for_malformed_metadata_schema(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "malformed", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(result, workflow_stage="WRONG_STAGE")

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "WORKFLOW_STAGE_INVALID" in set(health.health_frame["issue_code"])


def test_health_fails_for_inconsistent_match_mismatch_booleans(tmp_path: Path) -> None:
    root = _root(tmp_path)
    performed_but_neither = _run_core(tmp_path, "bad_neither", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(performed_but_neither, expected_hash_matched=False, expected_hash_mismatch=False)
    both_true = _run_core(tmp_path, "bad_both", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(both_true, expected_hash_matched=True, expected_hash_mismatch=True)
    matched_status_bad = _run_core(tmp_path, "bad_matched_status", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(matched_status_bad, expected_hash_matched=False)
    mismatch_status_bad = _run_core(tmp_path, "bad_mismatch_status", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)
    _mutate_metadata(mismatch_status_bad, expected_hash_mismatch=False, health_status="PASS")

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    codes = set(health.health_frame["issue_code"])
    assert "EXPECTED_HASH_MATCH_MISMATCH_INCONSISTENT" in codes
    assert "MATCHED_STATUS_WITHOUT_MATCH" in codes
    assert "MISMATCH_STATUS_POLICY_INVALID" in codes


def test_health_fails_for_hash_recompute_and_csv_semantic_read_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "unsafe_csv", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(
        result,
        target_file_opened_for_expected_hash_verification=True,
        local_file_byte_hash_recomputed=True,
        csv_header_read=True,
        csv_row_count_computed=True,
        csv_values_read=True,
        csv_full_content_read=True,
        real_csv_consumed=True,
    )

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")
    codes = set(health.health_frame["issue_code"])

    assert health.status == "FAIL"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in codes


def test_health_fails_for_source_pit_reviewer_and_downstream_flags(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "unsafe_downstream", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(
        result,
        source_hash_validated=True,
        revision_id_validated=True,
        available_time_validated=True,
        pit_admissibility_validated=True,
        source_reliability_scored=True,
        reviewer_authority_validated=True,
        active_replay_input=True,
        trading_allowed=True,
        buy_review_allowed=True,
        data_raw_written=True,
        data_processed_written=True,
        data_cache_written=True,
    )

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in set(health.health_frame["issue_code"])


def test_health_fails_each_unsafe_flag_family(tmp_path: Path) -> None:
    unsafe_fields = [
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "source_reliability_scored",
        "reviewer_authority_validated",
        "local_file_byte_hash_recomputed",
        "target_file_opened_for_expected_hash_verification",
        "csv_header_read",
        "csv_row_count_computed",
        "csv_values_read",
        "csv_full_content_read",
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
    for field in unsafe_fields:
        root = _root(tmp_path / field)
        result = _run_core(tmp_path / field, "unsafe", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
        _mutate_metadata(result, **{field: True})

        health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

        assert health.status == "FAIL", field
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in set(health.health_frame["issue_code"])


def test_status_summarizes_latest_no_input_matched_and_mismatch_artifacts(tmp_path: Path) -> None:
    root = _root(tmp_path)
    core.run_expected_hash_verification(output_root=root, run_id="001_no_input")
    _run_core(tmp_path, "002_matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _run_core(tmp_path, "003_mismatch", EXPECTED_FULL_HASH, ACTUAL_FULL_HASH)

    result = run_expected_hash_verification_status(root=root, output_dir=root / "status")

    assert result.latest_run_id == "003_mismatch"
    assert result.latest_runtime_status == "EXPECTED_HASH_VERIFICATION_MISMATCHED_REPORT_ONLY"
    assert result.latest_health_status == "WARN"
    assert result.latest_expected_hash_preview == EXPECTED_FULL_HASH[:PREVIEW_CHARS]
    assert result.latest_actual_local_file_byte_hash_preview == ACTUAL_FULL_HASH[:PREVIEW_CHARS]
    assert result.latest_expected_hash_mismatch is True
    assert result.latest_actionable_mismatch is True
    assert result.latest_runtime_status != "FAIL"
    assert result.recommended_next_task == STATUS_NEXT_TASK


def test_status_output_is_preview_only_and_negative_proof_fields_are_false(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core(tmp_path, "matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    result = run_expected_hash_verification_status(root=root, output_dir=root / "status")
    text = _view_text(result.artifact_paths)

    assert MATCHING_FULL_HASH not in text
    assert MATCHING_FULL_HASH[:PREVIEW_CHARS] in text
    assert result.latest_csv_read_level == "CSV_READ_NONE"
    assert result.latest_target_file_opened_for_expected_hash_verification is False
    assert result.latest_local_file_byte_hash_recomputed is False
    assert result.latest_csv_header_read is False
    assert result.latest_csv_row_count_computed is False
    assert result.latest_csv_values_read is False
    assert result.latest_csv_full_content_read is False
    assert result.latest_real_csv_consumed is False
    assert result.latest_source_hash_validated is False
    assert result.latest_revision_id_validated is False
    assert result.latest_available_time_validated is False
    assert result.latest_pit_admissibility_validated is False
    assert result.latest_source_reliability_scored is False
    assert result.latest_reviewer_authority_validated is False
    assert result.latest_active_replay_input is False
    assert result.latest_trading_allowed is False
    assert result.latest_buy_review_allowed is False


def test_views_pass_after_source_csv_never_exists(tmp_path: Path) -> None:
    root = _root(tmp_path)
    target_csv = tmp_path / "allowed" / "reviewed.csv"
    _run_core(tmp_path, "matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    assert not target_csv.exists()

    index = build_expected_hash_verification_index(root=root, output_dir=root / "index")
    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")
    status = run_expected_hash_verification_status(root=root, output_dir=root / "status")

    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_runtime_status == "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"


def test_views_pass_after_source_byte_hash_metadata_fixture_is_deleted(tmp_path: Path) -> None:
    root = _root(tmp_path)
    manifest_path, metadata_path = _write_inputs(tmp_path, MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    core.run_expected_hash_verification(
        output_root=root,
        run_id="matched",
        expected_hash_manifest_path=manifest_path,
        local_file_byte_hash_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        verification_level="EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        allow_expected_hash_verification=True,
    )
    metadata_path.unlink()

    index = build_expected_hash_verification_index(root=root, output_dir=root / "index")
    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")
    status = run_expected_hash_verification_status(root=root, output_dir=root / "status")

    assert index.artifact_count == 1
    assert health.status == "PASS"
    assert status.latest_runtime_status == "EXPECTED_HASH_VERIFICATION_MATCHED_REPORT_ONLY"


def test_view_modules_do_not_import_hashlib_or_unsafe_read_dependencies() -> None:
    for module in [
        "src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_index.py",
        "src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_health.py",
        "src/quant_replay_system/tiny_pit_real_reviewed_local_csv_package_candidate_expected_hash_verification_status.py",
    ]:
        source = Path(module).read_text(encoding="utf-8")
        assert "hashlib" not in source
        assert "read_bytes" not in source
        assert "import csv" not in source


def test_unsafe_readiness_wording_does_not_appear_positively(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core(tmp_path, "matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    index = build_expected_hash_verification_index(root=root, output_dir=root / "index")
    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")
    status = run_expected_hash_verification_status(root=root, output_dir=root / "status")
    text = _view_text(index.artifact_paths) + _view_text(health.artifact_paths) + _view_text(status.artifact_paths)

    for wording in UNSAFE_WORDING:
        assert wording not in text


def test_health_fails_for_positive_unsafe_readiness_wording(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = _run_core(tmp_path, "unsafe_wording", MATCHING_FULL_HASH, MATCHING_FULL_HASH)
    _mutate_metadata(result, recommended_next_task="Emit ACTIVE_REPLAY_INPUT_READY now")

    health = check_expected_hash_verification_health(root=root, output_dir=root / "health")

    assert health.status == "FAIL"
    assert "FORBIDDEN_STATUS_WORDING" in set(health.health_frame["issue_code"])


def test_docs_project_sources_not_created_and_views_stay_under_tmp_output_root(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _run_core(tmp_path, "matched", MATCHING_FULL_HASH, MATCHING_FULL_HASH)

    results = [
        build_expected_hash_verification_index(root=root, output_dir=root / "index"),
        check_expected_hash_verification_health(root=root, output_dir=root / "health"),
        run_expected_hash_verification_status(root=root, output_dir=root / "status"),
    ]

    assert not Path("docs/project_sources").exists()
    for result in results:
        for path in result.artifact_paths.values():
            assert Path(path).resolve().is_relative_to(root.resolve())
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _run_core(tmp_path: Path, run_id: str, expected_full_hash: str, actual_full_hash: str) -> dict:
    manifest_path, metadata_path = _write_inputs(tmp_path, expected_full_hash, actual_full_hash)
    return core.run_expected_hash_verification(
        output_root=_root(tmp_path),
        run_id=run_id,
        expected_hash_manifest_path=manifest_path,
        local_file_byte_hash_metadata_path=metadata_path,
        allowed_manifest_roots=[tmp_path / "allowed"],
        verification_level="EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        allow_expected_hash_verification=True,
    )


def _write_inputs(tmp_path: Path, expected_full_hash: str, actual_full_hash: str) -> tuple[Path, Path]:
    metadata_path = tmp_path / "allowed" / "byte_hash_artifact" / "metadata.json"
    manifest_path = tmp_path / "allowed" / "manifest" / "expected_hash_manifest.json"
    metadata = _valid_local_metadata(actual_full_hash)
    manifest = _valid_manifest(expected_full_hash, metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path, metadata_path


def _valid_manifest(expected_full_hash: str, metadata_path: Path) -> dict:
    return {
        "verification_id": "verify_fixture",
        "package_id": "package_fixture",
        "package_schema_version": "tiny-pit-expected-hash-v0.1",
        "created_at": "2026-07-02T00:00:00Z",
        "prepared_by": "pytest",
        "report_only": True,
        "diagnostic_only": True,
        "requested_expected_hash_verification_level": "EXPECTED_HASH_SHA256_AGAINST_LOCAL_METADATA_ONLY",
        "requested_csv_read_level": "CSV_READ_NONE",
        "requested_local_file_hash_level": "LOCAL_FILE_HASH_SHA256_METADATA_REFERENCE_ONLY",
        "source_local_file_byte_hash_artifact_metadata_path": str(metadata_path),
        "expected_hash_algorithm": "SHA-256",
        "expected_hash_value": expected_full_hash,
        "expected_hash_disclosure_level": "PREVIEW_ONLY_STATUS",
        "forbidden_downstream_flags": {field: False for field in core.REQUIRED_FALSE_FLAGS},
        "limitations": ["Synthetic expected-hash verification fixture."],
    }


def _valid_local_metadata(actual_full_hash: str) -> dict:
    metadata = {
        "local_file_byte_hash_computed": True,
        "local_file_byte_hash_algorithm": "SHA-256",
        "local_file_byte_hash_value": actual_full_hash,
        "csv_read_level": "CSV_READ_NONE",
        "csv_header_read": False,
        "csv_row_count_computed": False,
        "csv_values_read": False,
        "csv_full_content_read": False,
        "real_csv_consumed": False,
        "source_hash_validated": False,
        "revision_id_validated": False,
        "available_time_validated": False,
        "pit_admissibility_validated": False,
        "source_reliability_scored": False,
        "reviewer_authority_validated": False,
    }
    metadata.update({field: False for field in core.REQUIRED_FALSE_FLAGS})
    return metadata


def _root(tmp_path: Path) -> Path:
    return tmp_path / "outputs" / "reports" / "manual_diagnostics" / "expected_hash_verification"


def _mutate_metadata(result: dict, **updates) -> None:
    metadata_path = Path(result["artifact_paths"]["metadata"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(updates)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _view_text(paths: dict[str, Path]) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in paths.values() if Path(path).is_file())
