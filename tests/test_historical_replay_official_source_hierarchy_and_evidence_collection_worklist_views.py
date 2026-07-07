import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist import (
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
    run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist,
)
from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_WARN,
    check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health,
)
from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index import (
    STATUS_INDEX_CREATED,
    build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index,
)
from quant_replay_system.historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status import (
    NEXT_TASK,
    STATUS_CREATED,
    run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status,
)


EXPECTED_SYMBOLS = ["000001", "000002", "159915", "300750", "510300", "600000", "600519", "601318", "688981"]
EXPECTED_NEXT_TASK = (
    "Historical Replay Official Manual Evidence Collection Template Design Report-Only v0.1"
)


def test_index_discovers_temp_core_artifact_and_writes_expected_files(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_INDEX_CREATED
    assert result.artifact_count == 1
    assert result.rows[0]["run_id"] == run.run_id
    assert result.artifact_paths["index_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()
    assert result.artifact_paths["index_md"].exists()


def test_index_exports_counts_paths_and_recommended_next_task(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index(
        root=tmp_path / "out"
    )
    row = result.rows[0]

    assert row["historical_decision_date"] == "2024-04-02"
    assert row["universe_name"] == "etf_core"
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["source_class_count"] == 7
    assert row["evidence_family_count"] == 9
    assert row["evidence_collection_worklist_row_count"] == 72
    assert row["no_hit_handoff_row_count"] == 9
    assert row["blocked_count"] == 72
    assert row["profile_conflict_count"] == 7
    assert row["survivorship_warning_count"] == 9
    assert row["symbols_preview"].split(";") == EXPECTED_SYMBOLS
    assert row["recommended_next_task"] == EXPECTED_NEXT_TASK
    assert row["report_path"].endswith(OUTPUT_FILES["report"])


def test_health_warn_for_complete_safe_blocked_scaffold(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_WARN
    assert result.checked_artifact_count == 1
    assert result.error_count == 0
    assert result.warning_count >= 1
    assert "ALL_ROWS_REVIEW_REQUIRED" in _issue_codes(result)


def test_health_fails_on_missing_required_file(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_on_broken_row_count_or_missing_symbol(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["metadata"], {"row_count": 8})

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "ROW_COUNT_MISMATCH" in _issue_codes(result)

    run = _create_core_artifact(tmp_path / "missing_symbol")
    rows = _read_csv(run.artifact_paths["worklist"])
    rows = [row for row in rows if row["symbol"] != "688981"]
    _write_csv(run.artifact_paths["worklist"], rows)
    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=run.artifact_paths["metadata"].parents[1]
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "SYMBOL_SET_MISMATCH" in _issue_codes(result)


def test_health_fails_if_leading_zero_symbol_is_broken(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    rows[0]["symbol"] = "1"
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "SYMBOL_LEADING_ZERO_LOST" in _issue_codes(result)


def test_health_fails_if_source_class_or_family_counts_are_wrong(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["metadata"], {"source_class_count": 6})

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "SOURCE_CLASS_COUNT_MISMATCH" in _issue_codes(result)

    run = _create_core_artifact(tmp_path / "family")
    _patch_json(run.artifact_paths["metadata"], {"evidence_collection_worklist_row_count": 71})
    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=run.artifact_paths["metadata"].parents[1]
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "WORKLIST_ROW_COUNT_MISMATCH" in _issue_codes(result)


def test_health_fails_if_no_hit_handoff_count_is_wrong(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["metadata"], {"no_hit_handoff_row_count": 8})

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "NO_HIT_COUNT_MISMATCH" in _issue_codes(result)


def test_health_fails_if_any_safety_flag_is_true(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["safety_flags"], {"trading_allowed": True})

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in _issue_codes(result)


def test_health_fails_if_artifact_claims_downstream_readiness(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_json(run.artifact_paths["metadata"], {"pit_admissibility_approved": True})
    run.artifact_paths["report"].write_text(
        "PIT_ADMISSIBLE READY_FOR_REPLAY BUY_REVIEW_READY TRADING_READY APPROVED_FOR_PAPER PERFORMANCE_VALIDATED\n",
        encoding="utf-8",
    )

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    codes = _issue_codes(result)
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in codes
    assert "UNSAFE_READINESS_WORDING" in codes


def test_health_fails_if_no_hit_rows_are_accepted(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["no_hit_handoff_matrix"])
    rows[0]["no_hit_acceptance_status"] = "accepted"
    _write_csv(run.artifact_paths["no_hit_handoff_matrix"], rows)

    result = check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_HEALTH_FAIL
    assert "NO_HIT_ACCEPTED_UNSAFE" in _issue_codes(result)


def test_status_summarizes_latest_artifact_and_writes_status_files(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status(
        root=tmp_path / "out"
    )

    assert result.status == STATUS_CREATED
    assert result.latest_run_id == run.run_id
    assert result.summary["latest_historical_decision_date"] == "2024-04-02"
    assert result.summary["latest_universe_name"] == "etf_core"
    assert result.summary["latest_row_count"] == 9
    assert result.summary["latest_source_class_count"] == 7
    assert result.summary["latest_evidence_collection_worklist_row_count"] == 72
    assert result.summary["latest_no_hit_handoff_row_count"] == 9
    assert result.summary["latest_blocked_count"] == 72
    assert result.summary["latest_profile_conflict_count"] == 7
    assert result.summary["latest_survivorship_warning_count"] == 9
    assert result.artifact_paths["status_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()


def test_status_recommends_cli_report_only_and_exports_false_safety_fields(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status(
        root=tmp_path / "out"
    )

    assert NEXT_TASK == EXPECTED_NEXT_TASK
    assert result.recommended_next_task == EXPECTED_NEXT_TASK
    assert result.summary["recommended_next_task"] == EXPECTED_NEXT_TASK
    for field in SAFETY_FALSE_FIELDS:
        assert result.summary[f"latest_{field}"] is False


def test_status_does_not_run_core_or_write_core_artifacts_when_no_artifacts_exist(tmp_path: Path) -> None:
    result = run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status(
        root=tmp_path / "missing"
    )

    assert result.latest_status
    assert not (tmp_path / "missing" / "metadata.json").exists()
    assert not (tmp_path / "missing" / "official_evidence_collection_worklist.csv").exists()


def test_views_do_not_create_docs_project_sources_or_protected_data_paths(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)
    build_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_index(root=tmp_path / "out")
    check_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_health(root=tmp_path / "out")
    run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist_status(root=tmp_path / "out")

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _create_core_artifact(tmp_path: Path):
    return run_historical_replay_official_source_hierarchy_and_evidence_collection_worklist(
        root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(path: Path, updates: dict) -> None:
    payload = _read_json(path)
    payload.update(updates)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.rows}
