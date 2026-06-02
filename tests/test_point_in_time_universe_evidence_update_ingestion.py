import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    build_pit_universe_evidence_update_ingestion,
)


def test_complete_approval_row_is_ready_and_preserves_leading_zero_symbol(tmp_path: Path) -> None:
    updates = _write_updates(tmp_path / "updates.csv", [_complete_approved_update("000001")])
    worklist = _write_worklist(tmp_path / "worklist.csv", [_worklist_row("000001")])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        worklist=worklist,
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 1
    assert result.ready_for_review_update_count == 1
    assert result.blocked_count == 0
    assert result.approval_requested_count == 1
    assert result.approved_ready_count == 1
    assert result.duplicate_identity_count == 0
    assert result.suggested_copy_risk_count == 0

    frame = pd.read_csv(result.artifact_paths["ingestion_csv"], dtype={"symbol": str})
    row = frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["ingestion_status"] == "UPDATE_READY_FOR_REVIEW_APPLY"
    assert row["ready_for_review_update"] == True  # noqa: E712
    assert row["approval_requested"] == True  # noqa: E712
    assert row["no_universe_export"] == True  # noqa: E712
    assert row["no_data_raw_write"] == True  # noqa: E712
    assert row["no_data_processed_write"] == True  # noqa: E712
    assert row["no_current_candidates_generated"] == True  # noqa: E712
    assert row["no_snapshot_built"] == True  # noqa: E712
    assert row["no_forward_labels"] == True  # noqa: E712
    assert row["no_live_trading"] == True  # noqa: E712
    assert row["no_broker_api"] == True  # noqa: E712
    assert row["no_order_placement"] == True  # noqa: E712
    assert row["no_message_sent"] == True  # noqa: E712
    assert row["ingestion_only"] == True  # noqa: E712

    clean = pd.read_csv(result.artifact_paths["review_updates"], dtype={"symbol": str})
    assert clean["symbol"].tolist() == ["000001"]
    assert clean["review_status"].tolist() == ["APPROVED_FOR_PIT_UNIVERSE"]
    assert "valid_for_signal_date" not in clean.columns

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["no_universe_export"] is True
    assert metadata["no_data_raw_write"] is True
    assert metadata["no_data_processed_write"] is True
    assert metadata["no_current_candidates_generated"] is True
    assert metadata["no_snapshot_built"] is True
    assert metadata["no_forward_labels"] is True


def test_missing_identity_blocks_ingestion(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["symbol"] = ""
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.ready_for_review_update_count == 0
    assert result.blocked_count == 1
    assert result.missing_identity_count == 1
    assert result.ingestion_frame.iloc[0]["ingestion_status"] == "UPDATE_BLOCKED_MISSING_IDENTITY"


def test_duplicate_identity_blocks_all_duplicate_rows(tmp_path: Path) -> None:
    updates = _write_updates(
        tmp_path / "updates.csv",
        [_complete_approved_update("000001"), _complete_approved_update("000001")],
    )

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.ready_for_review_update_count == 0
    assert result.blocked_count == 2
    assert result.duplicate_identity_count == 2
    assert set(result.ingestion_frame["ingestion_status"]) == {"UPDATE_BLOCKED_DUPLICATE_IDENTITY"}


def test_invalid_review_status_blocks_ingestion(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["review_status"] = "APPROVE_NOW"
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.ready_for_review_update_count == 0
    assert result.blocked_count == 1
    assert result.ingestion_frame.iloc[0]["ingestion_status"] == "UPDATE_BLOCKED_INVALID_STATUS"


def test_approval_missing_reviewer_blocks(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["reviewer"] = ""
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    output = result.ingestion_frame.iloc[0]
    assert output["ingestion_status"] == "UPDATE_BLOCKED_MISSING_REVIEWER"
    assert output["ready_for_review_update"] is False
    assert "reviewer" in output["ingestion_blocker_reason"]


def test_approval_missing_evidence_path_or_reference_blocks(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["evidence_path"] = ""
    row["evidence_reference"] = ""
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    output = result.ingestion_frame.iloc[0]
    assert output["ingestion_status"] == "UPDATE_BLOCKED_MISSING_EVIDENCE"
    assert "evidence_path or evidence_reference" in output["ingestion_blocker_reason"]


def test_approval_unresolved_survivorship_blocks(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["survivorship_bias_resolved"] = False
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    output = result.ingestion_frame.iloc[0]
    assert output["ingestion_status"] == "UPDATE_BLOCKED_UNRESOLVED_SURVIVORSHIP"
    assert "survivorship_bias_resolved" in output["ingestion_blocker_reason"]


def test_approval_missing_required_universe_metadata_blocks(tmp_path: Path) -> None:
    row = _complete_approved_update("000001")
    row["as_of_date"] = ""
    row["name"] = ""
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    output = result.ingestion_frame.iloc[0]
    assert output["ingestion_status"] == "UPDATE_BLOCKED_MISSING_UNIVERSE_METADATA"
    assert "as_of_date" in output["ingestion_blocker_reason"]
    assert "name" in output["ingestion_blocker_reason"]


def test_approval_invalid_pit_dates_block(tmp_path: Path) -> None:
    listed_after = _complete_approved_update("000001")
    listed_after["listed_date"] = "2024-04-03"
    delisted_before = _complete_approved_update("000002")
    delisted_before["delisted_date"] = "2024-04-01"
    future_available = _complete_approved_update("000003")
    future_available["available_time"] = "2024-04-03 08:00:00"
    updates = _write_updates(tmp_path / "updates.csv", [listed_after, delisted_before, future_available])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.ready_for_review_update_count == 0
    assert result.blocked_count == 3
    assert set(result.ingestion_frame["ingestion_status"]) == {"UPDATE_BLOCKED_INVALID_PIT_DATES"}


def test_rejected_row_requires_reviewer_reviewed_at_and_reason(tmp_path: Path) -> None:
    blocked = _rejected_update("000001")
    blocked["reviewer"] = ""
    ready = _rejected_update("000002")
    updates = _write_updates(tmp_path / "updates.csv", [blocked, ready])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    by_symbol = result.ingestion_frame.set_index("symbol")
    assert by_symbol.loc["000001", "ingestion_status"] == "UPDATE_BLOCKED_MISSING_REVIEWER"
    assert by_symbol.loc["000002", "ingestion_status"] == "UPDATE_READY_FOR_REVIEW_APPLY"
    assert result.rejected_ready_count == 1


def test_needs_more_evidence_can_pass_with_reason_when_reviewer_supplied(tmp_path: Path) -> None:
    row = _needs_more_evidence_update("000001")
    updates = _write_updates(tmp_path / "updates.csv", [row])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.ready_for_review_update_count == 1
    assert result.needs_more_evidence_ready_count == 1
    assert result.ingestion_frame.iloc[0]["ingestion_status"] == "UPDATE_READY_FOR_REVIEW_APPLY"


def test_suggested_hints_are_not_authoritative_and_clean_csv_excludes_blocked_rows(tmp_path: Path) -> None:
    copied = _complete_approved_update("000001")
    copied["name"] = "Suggested Name"
    copied["instrument_type"] = "STOCK"
    copied["exchange"] = "SZSE"
    copied["industry"] = "BANKING"
    copied["min_lot"] = "100"
    copied["t_plus_rule"] = "T+1"
    copied["source"] = "LOCAL_HINT"
    copied["revision_id"] = "hint-v1"
    copied["available_time"] = "2024-04-02 08:00:00"
    copied["evidence_source"] = ""
    updates = _write_updates(tmp_path / "updates.csv", [copied, _complete_approved_update("000002")])
    worklist = _write_worklist(
        tmp_path / "worklist.csv",
        [_worklist_row("000001"), _worklist_row("000002")],
    )

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        worklist=worklist,
        output_dir=tmp_path / "out",
    )

    by_symbol = result.ingestion_frame.set_index("symbol")
    assert by_symbol.loc["000001", "suggested_copy_risk"] is True
    assert by_symbol.loc["000001", "ingestion_status"] == "UPDATE_BLOCKED_SUGGESTED_HINT_COPY_RISK"
    assert by_symbol.loc["000002", "ready_for_review_update"] is True
    assert result.suggested_copy_risk_count == 1

    clean = pd.read_csv(result.artifact_paths["review_updates"], dtype={"symbol": str})
    assert clean["symbol"].tolist() == ["000002"]


def test_blank_template_rows_remain_not_ready_without_approval(tmp_path: Path) -> None:
    updates = _write_updates(tmp_path / "updates.csv", [_blank_template_update("000001")])

    result = build_pit_universe_evidence_update_ingestion(
        completed_updates=updates,
        output_dir=tmp_path / "out",
    )

    assert result.approval_requested_count == 0
    assert result.ready_for_review_update_count == 0
    assert result.blocked_count == 1
    assert result.ingestion_frame.iloc[0]["ingestion_status"] == "UPDATE_BLOCKED_INVALID_STATUS"


def test_cli_pit_universe_evidence_update_ingestion_works(tmp_path: Path, capsys) -> None:
    updates = _write_updates(tmp_path / "updates.csv", [_complete_approved_update("000001")])
    worklist = _write_worklist(tmp_path / "worklist.csv", [_worklist_row("000001")])

    code = cli.main(
        [
            "pit-universe-evidence-update-ingestion",
            "--completed-updates",
            str(updates),
            "--worklist",
            str(worklist),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "ingestion_id:" in output.out
    assert "ready_for_review_update_count: 1" in output.out
    assert "approval_requested_count: 1" in output.out
    assert "No approval was applied, no universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked." in output.out


def _write_updates(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_worklist(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _complete_approved_update(symbol: str) -> dict:
    return {
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "review_status": "APPROVED_FOR_PIT_UNIVERSE",
        "include_flag": True,
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-06-02 10:00:00",
        "review_reason": "Manual PIT evidence reviewed.",
        "evidence_source": "LOCAL_REVIEW",
        "evidence_path": "docs/evidence/local_review.csv",
        "evidence_reference": "",
        "listed_date": "1991-04-03",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "listed_date_evidence": "1991-04-03",
        "delisted_date_evidence": "",
        "is_active_evidence": True,
        "survivorship_bias_resolved": True,
        "as_of_date": "2024-04-02",
        "name": f"Sample {symbol}",
        "instrument_type": "STOCK",
        "exchange": "SZSE",
        "industry": "BANKING",
        "min_lot": "100",
        "t_plus_rule": "T+1",
        "available_time": "2024-04-02 08:00:00",
        "revision_id": "review-v1",
        "source": "LOCAL_REVIEW",
    }


def _rejected_update(symbol: str) -> dict:
    row = _blank_template_update(symbol)
    row.update(
        {
            "review_status": "REJECTED",
            "reviewer": "reviewer-a",
            "reviewed_at": "2024-06-02 10:00:00",
            "review_reason": "No PIT evidence available.",
        }
    )
    return row


def _needs_more_evidence_update(symbol: str) -> dict:
    row = _blank_template_update(symbol)
    row.update(
        {
            "review_status": "NEEDS_MORE_EVIDENCE",
            "reviewer": "reviewer-a",
            "reviewed_at": "2024-06-02 10:00:00",
            "review_reason": "Need independent listed-date evidence.",
        }
    )
    return row


def _blank_template_update(symbol: str) -> dict:
    row = {key: "" for key in _complete_approved_update(symbol)}
    row["signal_date"] = "2024-04-02"
    row["symbol"] = symbol
    row["universe_name"] = "etf_core"
    return row


def _worklist_row(symbol: str) -> dict:
    return {
        "worklist_id": "worklist001",
        "review_id": "review001",
        "helper_id": "helper001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "current_valid_for_signal_date": False,
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": False,
        "suggested_name": "Suggested Name" if symbol == "000001" else "Other Name",
        "suggested_instrument_type": "STOCK",
        "suggested_exchange": "SZSE",
        "suggested_industry": "BANKING",
        "suggested_min_lot": "100",
        "suggested_t_plus_rule": "T+1",
        "suggested_is_active": True,
        "suggested_is_st": False,
        "suggested_is_suspended": False,
        "suggested_source": "LOCAL_HINT",
        "suggested_revision_id": "hint-v1",
        "hint_available_time": "2024-05-20 08:00:00",
        "hint_is_future_dated_for_signal_date": True,
        "hint_authoritative_for_pit": False,
        "missing_reviewer": True,
        "missing_reviewed_at": True,
        "missing_review_reason": False,
        "missing_evidence_source": True,
        "missing_evidence_path_or_reference": True,
        "missing_listed_date_evidence": True,
        "missing_is_active_evidence": True,
        "missing_survivorship_bias_resolution": True,
        "missing_required_universe_metadata": True,
        "required_next_evidence_fields": "reviewer,evidence_source",
        "suggested_next_review_action": "Collect PIT evidence.",
        "reviewer": "",
        "reviewed_at": "",
        "review_reason": "Manual review required.",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "listed_date_evidence": "",
        "delisted_date_evidence": "",
        "is_active_evidence": "",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }
