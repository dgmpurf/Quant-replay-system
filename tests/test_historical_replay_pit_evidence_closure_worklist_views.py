import json
from pathlib import Path

import pandas as pd

from quant_replay_system.historical_replay_pit_evidence_closure_worklist import (
    SAFETY_FALSE_FIELDS,
    run_historical_replay_pit_evidence_closure_worklist,
)
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_health import (
    check_historical_replay_pit_evidence_closure_worklist_health,
)
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_index import (
    build_historical_replay_pit_evidence_closure_worklist_index,
)
from quant_replay_system.historical_replay_pit_evidence_closure_worklist_status import (
    run_historical_replay_pit_evidence_closure_worklist_status,
)


def test_index_discovers_safe_no_context_worklist_artifact(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = build_historical_replay_pit_evidence_closure_worklist_index(root=tmp_path / "out")

    assert result.artifact_count == 1
    assert result.rows[0]["status"] == "PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT"
    assert result.artifact_paths["index_csv"].exists()


def test_index_preserves_signal_date_and_universe_name(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = build_historical_replay_pit_evidence_closure_worklist_index(root=tmp_path / "out")

    assert result.rows[0]["signal_date"] == "2024-04-02"
    assert result.rows[0]["universe_name"] == "etf_core"


def test_index_preserves_leading_zero_symbols_when_rows_exist(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")

    result = build_historical_replay_pit_evidence_closure_worklist_index(root=tmp_path / "out")

    assert result.rows[0]["symbols_preview"].split(";")[0] == "000001"
    index = pd.read_csv(result.artifact_paths["index_csv"], dtype=str).fillna("")
    assert index.iloc[0]["symbols_preview"].split(";")[0] == "000001"


def test_health_warn_for_safe_no_context_artifact(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED"
    assert result.error_count == 0
    assert result.warning_count >= 1


def test_health_warn_for_all_blocked_review_required_artifact(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_overlay(root)
    run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_WARN_REVIEW_REQUIRED"
    assert result.error_count == 0
    assert "REVIEW_REQUIRED_ROWS" in _issue_codes(result)


def test_health_pass_only_when_required_files_and_safety_fields_are_safe_and_complete(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=run.artifact_paths["metadata"].parents[1])

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY"
    assert result.error_count == 0
    assert result.warning_count == 0


def test_health_fail_for_missing_metadata_json(tmp_path: Path) -> None:
    run = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    run.artifact_paths["metadata"].unlink()

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fail_for_missing_worklist_csv(tmp_path: Path) -> None:
    run = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    run.artifact_paths["worklist"].unlink()

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fail_if_pit_evidence_closed_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "pit_evidence_closed")


def test_health_fail_if_pit_admissibility_approved_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "pit_admissibility_approved")


def test_health_fail_if_active_replay_input_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "active_replay_input")


def test_health_fail_if_replay_execution_allowed_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "replay_execution_allowed")


def test_health_fail_if_forward_labels_created_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "forward_labels_created")


def test_health_fail_if_buy_review_allowed_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "buy_review_allowed")


def test_health_fail_if_trading_allowed_true(tmp_path: Path) -> None:
    _assert_metadata_flag_fails(tmp_path, "trading_allowed")


def test_health_fail_if_broker_order_or_message_true(tmp_path: Path) -> None:
    for field in ["broker_api_called", "order_placed", "message_sent"]:
        _assert_metadata_flag_fails(tmp_path, field)


def test_health_fail_if_current_candidates_or_snapshot_true(tmp_path: Path) -> None:
    for field in ["current_candidates_executed", "snapshot_built"]:
        _assert_metadata_flag_fails(tmp_path, field)


def test_health_fail_if_report_contains_forbidden_readiness_wording(tmp_path: Path) -> None:
    run = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    run.artifact_paths["report"].write_text("PIT_ADMISSIBLE READY_FOR_REPLAY BUY_REVIEW_READY TRADING_READY\n", encoding="utf-8")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"
    assert "UNSAFE_READINESS_WORDING" in _issue_codes(result)


def test_health_flags_rows_with_missing_source_id_as_blocked_or_review_required(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)
    _set_worklist_field(run.artifact_paths["worklist"], "source_id", "missing")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"
    assert "ROW_MISSING_FIELD_NOT_BLOCKED" in _issue_codes(result)


def test_health_flags_rows_with_missing_permission_class_as_blocked_or_review_required(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)
    _set_worklist_field(run.artifact_paths["worklist"], "permission_class", "missing")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert "ROW_MISSING_FIELD_NOT_BLOCKED" in _issue_codes(result)


def test_health_flags_rows_with_missing_available_time_as_blocked_or_review_required(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)
    _set_worklist_field(run.artifact_paths["worklist"], "available_time", "missing")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert "ROW_MISSING_FIELD_NOT_BLOCKED" in _issue_codes(result)


def test_health_flags_rows_with_available_time_after_signal_date_as_blocked(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)
    _set_worklist_field(run.artifact_paths["worklist"], "available_time", "2024-04-03 08:00:00")
    _set_worklist_field(run.artifact_paths["worklist"], "timing_relation_to_decision", "after_decision")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert "ROW_AFTER_DECISION_NOT_BLOCKED" in _issue_codes(result)


def test_health_flags_missing_survivorship_rationale(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)
    _set_worklist_field(run.artifact_paths["worklist"], "survivorship_rationale", "missing")

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert "ROW_MISSING_FIELD_NOT_BLOCKED" in _issue_codes(result)


def test_health_preserves_closure_ready_not_pit_approved(tmp_path: Path) -> None:
    run = _write_closure_ready_artifact(tmp_path)

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")
    metadata = json.loads(run.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_PASS_REPORT_ONLY"
    assert metadata["closure_ready_not_pit_approved_count"] == 1
    assert metadata["pit_admissibility_approved"] is False


def test_status_summarizes_latest_artifact_and_writes_status_files(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = run_historical_replay_pit_evidence_closure_worklist_status(root=tmp_path / "out")

    assert result.latest_status == "PIT_EVIDENCE_CLOSURE_WORKLIST_WARN_NO_CONTEXT"
    assert result.artifact_paths["status_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()


def test_status_recommends_next_task(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = run_historical_replay_pit_evidence_closure_worklist_status(root=tmp_path / "out")

    assert (
        result.recommended_next_task
        == "Historical Replay Official Status Evidence Packet Closure Planning for 2024-04-02 etf_core Report-Only v0.1"
    )
    assert "Artifact Views / Status Planning" not in result.recommended_next_task
    assert "Research-Status Integration Planning" not in result.recommended_next_task


def test_no_docs_project_sources_is_created(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    build_historical_replay_pit_evidence_closure_worklist_index(root=tmp_path / "out")
    check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")
    run_historical_replay_pit_evidence_closure_worklist_status(root=tmp_path / "out")

    assert not (tmp_path / "docs" / "project_sources").exists()


def test_protected_tracked_scan_fixture_expectation_is_limited_to_report_only_paths(tmp_path: Path) -> None:
    run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()
    assert not (tmp_path / "data" / "cache").exists()


def _write_overlay(root: Path) -> None:
    path = root / "point_in_time_universe_overlay_plan" / "38a254c54024"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "overlay_plan_id": "38a254c54024",
                "signal_date": "2024-04-02",
                "symbol": "000001",
                "universe_name": "etf_core",
                "proposed_available_time": "2024-04-02 08:00:00",
                "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/raw_data.csv",
                "base_universe_as_of_date": "2024-05-20",
                "base_universe_available_time": "2024-05-20 08:00:00",
                "source": "AKSHARE_OPTIONAL",
                "survivorship_bias_warning": "True",
                "valid_for_signal_date": "False",
                "blocker_reason": "Universe as_of_date is later than signal date.",
            }
        ]
    ).to_csv(path / "point_in_time_universe_overlay_plan.csv", index=False)


def _write_symbol_summary(root: Path) -> None:
    path = root / "point_in_time_universe_evidence_review_worklist" / "1c7972988f59"
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "worklist_id": "1c7972988f59",
                "symbol": "000001",
                "universe_name": "etf_core",
                "first_signal_date": "2024-04-02",
                "suggested_name": "Ping An Bank",
                "suggested_instrument_type": "STOCK",
                "suggested_exchange": "SZSE",
            }
        ]
    ).to_csv(path / "pit_universe_evidence_review_symbol_summary.csv", index=False)


def _write_closure_ready_artifact(tmp_path: Path):
    root = tmp_path / "reports"
    _write_overlay(root)
    _write_symbol_summary(root)
    run = run_historical_replay_pit_evidence_closure_worklist(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(run.artifact_paths["worklist"], dtype=str).fillna("")
    rows.loc[:, "source_id"] = "source-a"
    rows.loc[:, "permission_class"] = "allowed_context"
    rows.loc[:, "available_time"] = "2024-04-02 08:00:00"
    rows.loc[:, "available_time_timezone"] = "Asia/Shanghai"
    rows.loc[:, "survivorship_rationale"] = "reviewed context only"
    rows.loc[:, "reviewer_id"] = "reviewer"
    rows.loc[:, "reviewer_role"] = "research_reviewer"
    rows.loc[:, "reviewer_scope"] = "report_only"
    rows.loc[:, "reviewer_attestation"] = "attested"
    rows.loc[:, "closure_status"] = "closure_ready_not_pit_approved"
    rows.loc[:, "blocker_status"] = ""
    rows.to_csv(run.artifact_paths["worklist"], index=False)
    _patch_metadata(run.artifact_paths["metadata"], {"blocked_count": 0, "closure_ready_not_pit_approved_count": 1})
    return run


def _assert_metadata_flag_fails(tmp_path: Path, field: str) -> None:
    run = run_historical_replay_pit_evidence_closure_worklist(root=tmp_path / "reports", output_dir=tmp_path / "out")
    _patch_metadata(run.artifact_paths["metadata"], {field: True})

    result = check_historical_replay_pit_evidence_closure_worklist_health(root=tmp_path / "out")

    assert result.status == "PIT_EVIDENCE_CLOSURE_WORKLIST_HEALTH_FAIL_UNSAFE"
    assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)


def _patch_metadata(path: Path, updates: dict) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _set_worklist_field(path: Path, field: str, value: str) -> None:
    rows = pd.read_csv(path, dtype=str).fillna("")
    rows.loc[:, field] = value
    rows.to_csv(path, index=False)


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.rows}
