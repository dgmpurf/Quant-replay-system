import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_evidence_review_worklist import (
    build_pit_universe_evidence_review_worklist,
)


def test_worklist_created_from_helper_and_review_rows(tmp_path: Path) -> None:
    helper = _write_helper(tmp_path / "helper.csv")
    review = _write_review(tmp_path / "review.csv")

    result = build_pit_universe_evidence_review_worklist(
        helper=helper,
        review=review,
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 2
    assert result.symbol_count == 2
    assert result.signal_date_count == 1
    assert result.needs_manual_review_count == 2
    assert result.needs_evidence_count == 2
    assert result.future_dated_hint_count == 2
    assert result.authoritative_hint_count == 0
    assert result.approved_count == 0
    assert result.valid_for_signal_date_count == 0

    frame = pd.read_csv(result.artifact_paths["worklist_csv"], dtype={"symbol": str})
    assert frame["symbol"].tolist() == ["000001", "510300"]
    assert frame["current_review_status"].tolist() == ["NEEDS_MANUAL_REVIEW", "NEEDS_MANUAL_REVIEW"]
    assert frame["current_valid_for_signal_date"].eq(False).all()
    assert frame["survivorship_bias_warning"].eq(True).all()
    assert frame["survivorship_bias_resolved"].eq(False).all()
    assert frame["hint_authoritative_for_pit"].eq(False).all()
    assert frame["hint_is_future_dated_for_signal_date"].eq(True).all()
    assert frame["missing_required_universe_metadata"].eq(True).all()
    assert frame["worklist_only"].eq(True).all()
    assert "APPROVED_FOR_PIT_UNIVERSE" not in set(frame["current_review_status"])

    update_template = pd.read_csv(result.artifact_paths["update_template"], dtype={"symbol": str}, keep_default_na=False)
    assert update_template["symbol"].tolist() == ["000001", "510300"]
    for column in [
        "review_status",
        "include_flag",
        "reviewer",
        "reviewed_at",
        "evidence_source",
        "evidence_path",
        "evidence_reference",
        "listed_date",
        "delisted_date",
        "is_active",
        "is_st",
        "is_suspended",
        "listed_date_evidence",
        "delisted_date_evidence",
        "is_active_evidence",
        "survivorship_bias_resolved",
        "as_of_date",
        "name",
        "instrument_type",
        "exchange",
        "industry",
        "min_lot",
        "t_plus_rule",
        "available_time",
        "revision_id",
        "source",
    ]:
        assert column in update_template.columns
    assert update_template["review_status"].eq("").all()
    assert update_template["include_flag"].eq("").all()

    symbol_summary = pd.read_csv(result.artifact_paths["symbol_summary"], dtype={"symbol": str})
    assert symbol_summary["symbol"].tolist() == ["000001", "510300"]
    assert symbol_summary["future_dated_hint_count"].tolist() == [1, 1]

    date_summary = pd.read_csv(result.artifact_paths["date_summary"])
    assert date_summary.loc[0, "signal_date"] == "2024-04-02"
    assert date_summary.loc[0, "symbol_count"] == 2

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["no_universe_export"] is True
    assert metadata["no_data_raw_write"] is True
    assert metadata["no_data_processed_write"] is True
    assert metadata["no_current_candidates_generated"] is True
    assert metadata["no_snapshot_built"] is True
    assert metadata["no_forward_labels"] is True
    assert metadata["cache_mutated"] is False
    assert metadata["network_api_called"] is False
    assert metadata["llm_api_called"] is False


def test_cli_pit_universe_evidence_review_worklist_works(tmp_path: Path, capsys) -> None:
    helper = _write_helper(tmp_path / "helper.csv")
    review = _write_review(tmp_path / "review.csv")

    code = cli.main(
        [
            "pit-universe-evidence-review-worklist",
            "--helper",
            str(helper),
            "--review",
            str(review),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "worklist_id:" in output.out
    assert "row_count: 2" in output.out
    assert "symbol_count: 2" in output.out
    assert "signal_date_count: 1" in output.out
    assert "approved_count: 0" in output.out
    assert "valid_for_signal_date_count: 0" in output.out
    assert "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked." in output.out


def _write_helper(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _helper_row("000001", "Ping An Bank", "STOCK", "SZSE"),
            _helper_row("510300", "CSI 300 ETF", "ETF", "SSE"),
        ]
    ).to_csv(path, index=False)
    return path


def _write_review(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _review_row("000001"),
            _review_row("510300"),
        ]
    ).to_csv(path, index=False)
    return path


def _helper_row(symbol: str, name: str, instrument_type: str, exchange: str) -> dict:
    return {
        "helper_id": "helper001",
        "review_id": "review001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "current_valid_for_signal_date": False,
        "current_survivorship_bias_warning": True,
        "current_survivorship_bias_resolved": False,
        "missing_reviewer": True,
        "missing_reviewed_at": True,
        "missing_review_reason": False,
        "missing_evidence_source": True,
        "missing_evidence_path_or_reference": True,
        "missing_listed_date_evidence": True,
        "missing_is_active_evidence": True,
        "missing_survivorship_bias_resolution": True,
        "suggested_name": name,
        "suggested_instrument_type": instrument_type,
        "suggested_exchange": exchange,
        "suggested_industry": "ETF" if instrument_type == "ETF" else "UNKNOWN",
        "suggested_min_lot": "100",
        "suggested_t_plus_rule": "T+1",
        "suggested_is_active": "True",
        "suggested_is_st": "False",
        "suggested_is_suspended": "False",
        "suggested_source": "LOCAL_HINT",
        "suggested_revision_id": "hint-v1",
        "suggested_available_time": "2024-05-20 08:00:00",
        "hint_source_path": "data/processed/universe/example.csv",
        "hint_as_of_date": "2024-05-20",
        "hint_available_time": "2024-05-20 08:00:00",
        "hint_is_future_dated_for_signal_date": True,
        "hint_authoritative_for_pit": False,
        "next_review_action": "Fill evidence fields.",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "evidence_completion_only": True,
    }


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
        "as_of_date": "",
        "name": "",
        "instrument_type": "",
        "exchange": "",
        "industry": "",
        "min_lot": "",
        "t_plus_rule": "",
        "available_time": "",
        "revision_id": "",
        "source": "",
        "manual_review_required": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "review_only": True,
    }
