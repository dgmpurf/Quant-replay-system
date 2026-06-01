import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_export_readiness import (
    build_pit_universe_overlay_export_readiness,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_status import (
    run_pit_universe_overlay_export_readiness_status,
)


def test_no_approved_review_blocks_export_readiness(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001")])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    assert result.readiness_status == "EXPORT_BLOCKED_NO_APPROVED_ROWS"
    assert result.row_count == 1
    assert result.approved_count == 0
    assert result.export_ready_count == 0
    assert result.blocked_count == 1
    row = result.readiness_frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["export_ready"] is False
    assert row["export_readiness_status"] == "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"
    assert "APPROVED_FOR_PIT_UNIVERSE" in row["export_blocker_reason"]

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["no_approved_rows"] is True
    assert metadata["would_write_data_raw"] is False
    assert metadata["would_write_data_processed"] is False
    assert metadata["no_current_candidates_generated"] is True
    assert metadata["no_snapshot_built"] is True
    assert metadata["no_forward_labels"] is True


def test_approved_row_missing_required_universe_columns_is_blocked(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_approved_review_row("000001")])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    row = result.readiness_frame.iloc[0]
    assert result.approved_count == 1
    assert result.export_ready_count == 0
    assert row["export_readiness_status"] == "EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS"
    assert "as_of_date" in row["missing_required_columns"]
    assert "name" in row["missing_required_columns"]


def test_approved_row_with_unresolved_survivorship_warning_is_blocked(tmp_path: Path) -> None:
    row = _complete_approved_review_row("000001")
    row["survivorship_bias_warning"] = True
    row["survivorship_bias_resolved"] = False
    review = _write_review(tmp_path / "review.csv", [row])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    output = result.readiness_frame.iloc[0]
    assert output["export_ready"] is False
    assert output["export_readiness_status"] == "EXPORT_BLOCKED_UNRESOLVED_SURVIVORSHIP"
    assert result.unresolved_survivorship_warning_count == 1


def test_approved_row_with_future_available_time_is_blocked(tmp_path: Path) -> None:
    row = _complete_approved_review_row("000001")
    row["available_time"] = "2024-04-03 15:31:00"
    review = _write_review(tmp_path / "review.csv", [row])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    output = result.readiness_frame.iloc[0]
    assert output["export_ready"] is False
    assert output["export_readiness_status"] == "EXPORT_BLOCKED_INVALID_PIT_DATES"
    assert "available_time" in output["export_blocker_reason"]


def test_suggested_metadata_fields_do_not_count_as_authoritative(tmp_path: Path) -> None:
    row = _complete_approved_review_row("000001")
    row["as_of_date"] = ""
    row["name"] = ""
    row["instrument_type"] = ""
    row["exchange"] = ""
    row["industry"] = ""
    row["min_lot"] = ""
    row["t_plus_rule"] = ""
    row["available_time"] = ""
    row["revision_id"] = ""
    row["source"] = ""
    row["suggested_name"] = "Suggested Name"
    row["suggested_instrument_type"] = "STOCK"
    row["suggested_exchange"] = "SSE"
    row["suggested_industry"] = "BANKING"
    row["suggested_min_lot"] = 100
    row["suggested_t_plus_rule"] = "T+1"
    row["suggested_source"] = "SUGGESTED_SOURCE"
    row["suggested_revision_id"] = "rev-suggest"
    row["suggested_available_time"] = "2024-04-02 08:00:00"
    review = _write_review(tmp_path / "review.csv", [row])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    output = result.readiness_frame.iloc[0]
    assert output["export_ready"] is False
    assert output["export_readiness_status"] == "EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS"
    assert "as_of_date" in output["missing_required_columns"]


def test_export_readiness_preserves_leading_zero_symbol(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_complete_approved_review_row("000001")])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    assert result.readiness_frame["symbol"].tolist() == ["000001"]


def test_approved_row_with_invalid_listed_or_delisted_dates_is_blocked(tmp_path: Path) -> None:
    listed_after_signal = _complete_approved_review_row("000001")
    listed_after_signal["listed_date"] = "2024-04-03"
    delisted_before_signal = _complete_approved_review_row("000002")
    delisted_before_signal["delisted_date"] = "2024-04-01"
    review = _write_review(tmp_path / "review.csv", [listed_after_signal, delisted_before_signal])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    assert result.export_ready_count == 0
    assert set(result.readiness_frame["export_readiness_status"]) == {"EXPORT_BLOCKED_INVALID_PIT_DATES"}
    assert all("signal_date" in reason for reason in result.readiness_frame["export_blocker_reason"])


def test_duplicate_export_ready_keys_are_blocked(tmp_path: Path) -> None:
    first = _complete_approved_review_row("000001")
    duplicate = _complete_approved_review_row("000001")
    review = _write_review(tmp_path / "review.csv", [first, duplicate])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    assert result.duplicate_key_count == 2
    assert result.export_ready_count == 0
    assert result.blocked_count == 2
    assert set(result.readiness_frame["export_readiness_status"]) == {"EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"}
    assert all("Duplicate export-ready key" in reason for reason in result.readiness_frame["export_blocker_reason"])


def test_complete_synthetic_approved_row_is_export_ready_in_readiness_artifact_only(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_complete_approved_review_row("000001")])

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "out")

    assert result.readiness_status == "EXPORT_READY_FOR_DRY_RUN"
    assert result.approved_count == 1
    assert result.export_ready_count == 1
    assert result.blocked_count == 0
    row = result.readiness_frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["export_ready"] is True
    assert row["required_column_missing_count"] == 0
    assert row["missing_required_columns"] == ""
    assert row["export_readiness_only"] is True

    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_mixed_complete_and_blocked_rows_stabilize_readiness_and_status(tmp_path: Path) -> None:
    rows = [
        _complete_approved_review_row("000001"),
        _complete_approved_review_row("000001"),
        _approved_review_row("000002"),
        _unresolved_survivorship_review_row("000003"),
        _future_available_time_review_row("000004"),
        _complete_approved_review_row("000006"),
    ]
    rows[-1]["as_of_date"] = "2024-04-01"
    rows[-1]["industry"] = "BANKING"
    rows[-1]["name"] = "Sample Name 000006"
    rows[-1]["instrument_type"] = "STOCK"
    rows[-1]["exchange"] = "SZSE"
    rows[-1]["min_lot"] = 100
    rows[-1]["t_plus_rule"] = "T+1"
    rows[-1]["revision_id"] = "r5"
    rows[-1]["source"] = "LOCAL_REVIEW"
    rows[-1]["survivorship_bias_warning"] = False
    rows[-1]["survivorship_bias_resolved"] = True

    review = _write_review(tmp_path / "review.csv", rows)

    result = build_pit_universe_overlay_export_readiness(review=review, output_dir=tmp_path / "export_readiness")

    assert result.approved_count == 6
    assert result.export_ready_count == 1
    assert result.blocked_count == 5
    assert result.readiness_status == "EXPORT_READY_REVIEW_ONLY"
    assert result.duplicate_key_count == 2
    assert result.missing_required_columns_count == 1
    assert result.unresolved_survivorship_warning_count >= 1

    status_counts = result.readiness_frame["export_readiness_status"].value_counts().to_dict()
    assert status_counts["EXPORT_READY_FOR_DRY_RUN"] == 1
    assert status_counts.get("EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE", 0) >= 1
    assert status_counts["EXPORT_READY_FOR_DRY_RUN"] + sum(
        count
        for status, count in status_counts.items()
        if status != "EXPORT_READY_FOR_DRY_RUN"
    ) == 6

    ready_row = result.readiness_frame[result.readiness_frame["export_readiness_status"] == "EXPORT_READY_FOR_DRY_RUN"].iloc[0]
    assert ready_row["symbol"] in {"000001", "000006"}
    assert ready_row["export_ready"] is True
    assert ready_row["missing_required_columns"] == ""

    blocked_rows = result.readiness_frame[result.readiness_frame["export_ready"] == False]  # noqa: E712
    assert any("Duplicate export-ready key signal_date+symbol+universe_name" in str(reason) for reason in blocked_rows["export_blocker_reason"])
    assert any("missing required universe columns" in str(reason) for reason in blocked_rows["export_blocker_reason"])
    assert any("survivorship_bias_warning is unresolved" in str(reason) for reason in blocked_rows["export_blocker_reason"])
    assert any("available_time must be on or before signal decision time" in str(reason) for reason in blocked_rows["export_blocker_reason"])

    status = run_pit_universe_overlay_export_readiness_status(
        root=tmp_path / "export_readiness",
        output_dir=tmp_path / "status",
    )
    assert status.workflow_stage == "PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN"
    assert status.export_ready_count == 1
    assert status.blocked_count == 5
    assert status.health_status == "PASS"
    assert "Review export-ready PIT universe rows before a separate explicit universe export workflow." in status.next_manual_action


def test_cli_pit_universe_overlay_export_readiness_works(tmp_path: Path, capsys) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001")])

    code = cli.main(
        [
            "pit-universe-overlay-export-readiness",
            "--review",
            str(review),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "export_readiness_id:" in output.out
    assert "readiness_status: EXPORT_BLOCKED_NO_APPROVED_ROWS" in output.out
    assert "approved_count: 0" in output.out
    assert "export_ready_count: 0" in output.out
    assert "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked." in output.out


def _write_review(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _review_row(symbol: str) -> dict:
    return {
        "review_id": "review001",
        "overlay_plan_id": "overlay001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "include_flag": False,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "valid_for_signal_date": False,
        "blocker_reason": "Manual review required.",
        "reviewer": "",
        "reviewed_at": "",
        "review_reason": "Manual review required.",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "listed_date": "",
        "delisted_date": "",
        "is_active": "",
        "is_st": "",
        "is_suspended": "",
        "listed_date_evidence": "",
        "delisted_date_evidence": "",
        "is_active_evidence": "",
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": False,
        "manual_review_required": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "review_only": True,
    }


def _approved_review_row(symbol: str) -> dict:
    row = _review_row(symbol)
    row.update(
        {
            "include_flag": True,
            "review_status": "APPROVED_FOR_PIT_UNIVERSE",
            "valid_for_signal_date": True,
            "blocker_reason": "",
            "reviewer": "reviewer-a",
            "reviewed_at": "2024-05-29T10:00:00+08:00",
            "review_reason": "Local PIT evidence reviewed.",
            "evidence_source": "LOCAL_REVIEW_FIXTURE",
            "evidence_path": "outputs/reports/manual_diagnostics/local_evidence.csv",
            "listed_date": "1991-04-03",
            "is_active": True,
            "is_st": False,
            "is_suspended": False,
            "listed_date_evidence": "1991-04-03",
            "is_active_evidence": True,
            "survivorship_bias_warning": True,
            "survivorship_bias_resolved": True,
        }
    )
    return row


def _unresolved_survivorship_review_row(symbol: str) -> dict:
    row = _complete_approved_review_row(symbol)
    row["survivorship_bias_warning"] = True
    row["survivorship_bias_resolved"] = False
    return row


def _future_available_time_review_row(symbol: str) -> dict:
    row = _complete_approved_review_row(symbol)
    row["available_time"] = "2024-04-02 15:31:00"
    return row


def _complete_approved_review_row(symbol: str) -> dict:
    row = _approved_review_row(symbol)
    row.update(
        {
            "as_of_date": "2024-04-02",
            "name": f"Name {symbol}",
            "instrument_type": "STOCK",
            "exchange": "SZSE",
            "industry": "UNKNOWN",
            "min_lot": 100,
            "t_plus_rule": "T+1",
            "available_time": "2024-04-02 08:00:00",
            "revision_id": "review001",
            "source": "LOCAL_REVIEWED_PIT_OVERLAY",
        }
    )
    return row
