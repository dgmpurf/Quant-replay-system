import csv
import json
from pathlib import Path

from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist import (
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
    run_historical_replay_official_status_evidence_packet_closure_worklist,
)
from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist_health import (
    STATUS_HEALTH_FAIL,
    STATUS_HEALTH_WARN,
    check_historical_replay_official_status_evidence_packet_closure_worklist_health,
)
from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist_index import (
    STATUS_INDEX_CREATED,
    build_historical_replay_official_status_evidence_packet_closure_worklist_index,
)
from quant_replay_system.historical_replay_official_status_evidence_packet_closure_worklist_status import (
    NEXT_TASK,
    STATUS_CREATED,
    run_historical_replay_official_status_evidence_packet_closure_worklist_status,
)


EXPECTED_SYMBOLS = ["000001", "000002", "159915", "300750", "510300", "600000", "600519", "601318", "688981"]


def test_index_discovers_safe_official_status_worklist_artifact(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = build_historical_replay_official_status_evidence_packet_closure_worklist_index(root=tmp_path / "out")

    assert result.status == STATUS_INDEX_CREATED
    assert result.artifact_count == 1
    assert result.rows[0]["packet_worklist_run_id"] == run.packet_worklist_run_id
    assert result.artifact_paths["index_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()


def test_index_preserves_sample_identity_counts_and_leading_zero_symbols(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = build_historical_replay_official_status_evidence_packet_closure_worklist_index(root=tmp_path / "out")
    row = result.rows[0]

    assert row["signal_date"] == "2024-04-02"
    assert row["universe_name"] == "etf_core"
    assert row["row_count"] == 9
    assert row["stock_row_count"] == 7
    assert row["etf_row_count"] == 2
    assert row["blocked_count"] == 9
    assert row["profile_conflict_count"] == 7
    assert row["survivorship_warning_count"] == 9
    assert row["symbols_preview"].split(";") == EXPECTED_SYMBOLS
    assert row["recommended_next_task"]


def test_health_warn_for_complete_safe_all_blocked_scaffold(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_WARN
    assert result.error_count == 0
    assert result.warning_count >= 1
    assert "ALL_ROWS_REVIEW_REQUIRED" in _issue_codes(result)


def test_health_fail_for_missing_metadata_json(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fail_for_missing_worklist_csv(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["worklist"].unlink()

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fail_for_missing_safety_flags_json(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["safety_flags"].unlink()

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fail_if_row_count_is_not_nine(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_metadata(run.artifact_paths["metadata"], {"row_count": 8})

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "ROW_COUNT_MISMATCH" in _issue_codes(result)


def test_health_fail_if_symbol_set_is_not_exact(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    rows[-1]["symbol"] = "999999"
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "SYMBOL_SET_MISMATCH" in _issue_codes(result)


def test_health_fail_if_leading_zero_symbol_is_lost(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    rows[0]["symbol"] = "1"
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "SYMBOL_LEADING_ZERO_LOST" in _issue_codes(result)


def test_health_fail_if_stock_or_etf_counts_are_wrong(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_metadata(run.artifact_paths["metadata"], {"stock_row_count": 6, "etf_row_count": 3})

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "INSTRUMENT_COUNT_MISMATCH" in _issue_codes(result)


def test_health_fail_if_stock_profile_conflicts_are_not_true(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    rows[0]["profile_conflict_flag"] = "false"
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "STOCK_PROFILE_CONFLICT_NOT_FLAGGED" in _issue_codes(result)


def test_health_fail_if_etf_profile_conflicts_are_true(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    for row in rows:
        if row["symbol"] == "159915":
            row["profile_conflict_flag"] = "true"
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "ETF_PROFILE_CONFLICT_FLAGGED" in _issue_codes(result)


def test_health_fail_if_metadata_safety_flags_are_true(tmp_path: Path) -> None:
    for field in [
        "official_status_evidence_closed",
        "pit_admissibility_approved",
        "active_replay_input",
        "replay_execution_allowed",
        "forward_labels_created",
        "buy_review_allowed",
        "trading_allowed",
        "broker_api_called",
        "order_placed",
        "message_sent",
        "current_candidates_executed",
        "snapshot_built",
    ]:
        run = _create_core_artifact(tmp_path / field)
        _patch_metadata(run.artifact_paths["metadata"], {field: True})

        result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(
            root=run.artifact_paths["metadata"].parents[1]
        )

        assert result.status == STATUS_HEALTH_FAIL
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def test_health_fail_if_safety_flags_json_has_true_value(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    _patch_metadata(run.artifact_paths["safety_flags"], {"trading_allowed": True})

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "FORBIDDEN_SAFETY_FLAG_TRUE" in _issue_codes(result)


def test_health_fail_if_report_contains_forbidden_positive_readiness_wording(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    run.artifact_paths["report"].write_text(
        "PIT_ADMISSIBLE READY_FOR_REPLAY BUY_REVIEW_READY TRADING_READY APPROVED_FOR_PAPER PERFORMANCE_VALIDATED\n",
        encoding="utf-8",
    )

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "UNSAFE_READINESS_WORDING" in _issue_codes(result)


def test_health_confirms_required_stock_etf_and_common_blockers(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert "MISSING_STOCK_ST_BLOCKER" not in _issue_codes(result)
    assert "MISSING_ETF_ST_POLICY_BLOCKER" not in _issue_codes(result)
    assert "MISSING_COMMON_BLOCKER" not in _issue_codes(result)


def test_health_fail_if_required_common_blocker_is_missing(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)
    rows = _read_csv(run.artifact_paths["worklist"])
    for row in rows:
        row["blocker_reason"] = row["blocker_reason"].replace("blocker_missing_available_time", "")
    _write_csv(run.artifact_paths["worklist"], rows)

    result = check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")

    assert result.status == STATUS_HEALTH_FAIL
    assert "MISSING_COMMON_BLOCKER" in _issue_codes(result)


def test_status_summarizes_latest_artifact_and_writes_status_files(tmp_path: Path) -> None:
    run = _create_core_artifact(tmp_path)

    result = run_historical_replay_official_status_evidence_packet_closure_worklist_status(root=tmp_path / "out")

    assert result.status == STATUS_CREATED
    assert result.latest_packet_worklist_run_id == run.packet_worklist_run_id
    assert result.summary["latest_signal_date"] == "2024-04-02"
    assert result.summary["latest_universe_name"] == "etf_core"
    assert result.summary["latest_row_count"] == 9
    assert result.summary["latest_stock_row_count"] == 7
    assert result.summary["latest_etf_row_count"] == 2
    assert result.summary["latest_profile_conflict_count"] == 7
    assert result.recommended_next_task == NEXT_TASK
    assert result.artifact_paths["status_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()


def test_status_recommends_cli_report_only_next_task(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)

    result = run_historical_replay_official_status_evidence_packet_closure_worklist_status(root=tmp_path / "out")

    assert result.recommended_next_task == (
        "Historical Replay Official Status Evidence Packet Closure Worklist CLI Report-Only v0.1"
    )


def test_no_docs_project_sources_or_protected_data_paths_created(tmp_path: Path) -> None:
    _create_core_artifact(tmp_path)
    build_historical_replay_official_status_evidence_packet_closure_worklist_index(root=tmp_path / "out")
    check_historical_replay_official_status_evidence_packet_closure_worklist_health(root=tmp_path / "out")
    run_historical_replay_official_status_evidence_packet_closure_worklist_status(root=tmp_path / "out")

    assert not (tmp_path / "docs" / "project_sources").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _create_core_artifact(tmp_path: Path):
    return run_historical_replay_official_status_evidence_packet_closure_worklist(
        root=tmp_path / "repo",
        output_dir=tmp_path / "out",
        run_id="unit_test_run",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_metadata(path: Path, updates: dict) -> None:
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
