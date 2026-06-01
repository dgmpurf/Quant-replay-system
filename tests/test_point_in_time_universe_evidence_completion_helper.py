import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_evidence_completion_helper import (
    build_pit_universe_evidence_completion_helper,
)


def test_evidence_completion_template_preserves_non_approval_and_adds_hints(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001"), _review_row("510300")])
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    result = build_pit_universe_evidence_completion_helper(
        review=review,
        base_universe=base_universe,
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 2
    assert result.needs_evidence_count == 2
    assert result.rows_with_base_hints_count == 2
    assert result.future_dated_hint_count == 2
    assert result.authoritative_hint_count == 0
    assert result.approved_count == 0
    assert result.valid_for_signal_date_count == 0

    frame = result.template_frame.sort_values("symbol").reset_index(drop=True)
    assert frame["symbol"].tolist() == ["000001", "510300"]
    assert frame["current_review_status"].tolist() == ["NEEDS_MANUAL_REVIEW", "NEEDS_MANUAL_REVIEW"]
    assert frame["current_valid_for_signal_date"].eq(False).all()
    assert frame["current_survivorship_bias_warning"].eq(True).all()
    assert frame["hint_authoritative_for_pit"].eq(False).all()
    assert frame["hint_is_future_dated_for_signal_date"].eq(True).all()
    assert frame.loc[0, "suggested_name"] == "Ping An Bank"
    assert frame.loc[1, "suggested_instrument_type"] == "ETF"
    assert frame["missing_reviewer"].eq(True).all()
    assert frame["missing_evidence_path_or_reference"].eq(True).all()
    assert frame["missing_listed_date_evidence"].eq(True).all()
    assert frame["no_live_trading"].eq(True).all()
    assert frame["no_broker_api"].eq(True).all()
    assert frame["no_order_placement"].eq(True).all()
    assert frame["no_message_sent"].eq(True).all()
    assert frame["evidence_completion_only"].eq(True).all()

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["no_universe_export"] is True
    assert metadata["no_data_raw_write"] is True
    assert metadata["no_data_processed_write"] is True
    assert metadata["no_current_candidates_generated"] is True
    assert metadata["no_snapshot_built"] is True
    assert metadata["no_forward_labels"] is True
    assert metadata["cache_mutated"] is False


def test_evidence_completion_without_base_universe_still_reports_gaps(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001")])

    result = build_pit_universe_evidence_completion_helper(review=review, output_dir=tmp_path / "out")

    assert result.row_count == 1
    assert result.rows_with_base_hints_count == 0
    assert result.future_dated_hint_count == 0
    assert result.authoritative_hint_count == 0
    row = result.template_frame.iloc[0]
    assert row["symbol"] == "000001"
    assert row["suggested_name"] == ""
    assert row["hint_source_path"] == ""
    assert row["hint_authoritative_for_pit"] is False
    assert row["next_review_action"] == "Fill reviewer, reviewed_at, evidence, listed-date, active-status, and survivorship-resolution fields."


def test_existing_approved_input_is_not_created_or_upgraded_by_helper(tmp_path: Path) -> None:
    approved = _review_row("000001")
    approved.update(
        {
            "review_status": "APPROVED_FOR_PIT_UNIVERSE",
            "valid_for_signal_date": True,
            "include_flag": True,
            "reviewer": "human",
            "reviewed_at": "2024-05-29T10:00:00+08:00",
            "evidence_source": "LOCAL_REVIEW",
            "evidence_reference": "ticket-1",
            "listed_date_evidence": "1991-04-03",
            "is_active_evidence": True,
            "survivorship_bias_resolved": True,
        }
    )
    review = _write_review(tmp_path / "review.csv", [approved])

    result = build_pit_universe_evidence_completion_helper(review=review, output_dir=tmp_path / "out")

    assert result.approved_count == 1
    assert result.valid_for_signal_date_count == 1
    row = result.template_frame.iloc[0]
    assert row["current_review_status"] == "APPROVED_FOR_PIT_UNIVERSE"
    assert "review_status" not in result.template_frame.columns
    assert row["hint_authoritative_for_pit"] is False


def test_evidence_completion_helper_does_not_write_universe_inputs_or_run_workflows(tmp_path: Path) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001")])

    result = build_pit_universe_evidence_completion_helper(review=review, output_dir=tmp_path / "out")

    assert result.audit_metadata["no_universe_export"] is True
    assert result.audit_metadata["no_data_raw_write"] is True
    assert result.audit_metadata["no_data_processed_write"] is True
    assert result.audit_metadata["no_current_candidates_generated"] is True
    assert result.audit_metadata["no_snapshot_built"] is True
    assert result.audit_metadata["no_forward_labels"] is True
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["order_placement_enabled"] is False
    assert result.audit_metadata["message_sent"] is False
    assert result.audit_metadata["network_api_called"] is False
    assert result.audit_metadata["llm_api_called"] is False
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_cli_pit_universe_evidence_completion_helper_works(tmp_path: Path, capsys) -> None:
    review = _write_review(tmp_path / "review.csv", [_review_row("000001")])
    base_universe = _write_base_universe(tmp_path / "base_universe.csv")

    code = cli.main(
        [
            "pit-universe-evidence-completion-helper",
            "--review",
            str(review),
            "--base-universe",
            str(base_universe),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    output = capsys.readouterr()
    assert code == 0
    assert "helper_id:" in output.out
    assert "row_count: 1" in output.out
    assert "needs_evidence_count: 1" in output.out
    assert "rows_with_base_hints_count: 1" in output.out
    assert "authoritative_hint_count: 0" in output.out
    assert "approved_count: 0" in output.out
    assert "valid_for_signal_date_count: 0" in output.out
    assert "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked." in output.out


def _write_review(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _write_base_universe(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            _base_universe_row("000001", "Ping An Bank", "STOCK", "SZSE"),
            _base_universe_row("510300", "CSI 300 ETF", "ETF", "SSE"),
        ]
    ).to_csv(path, index=False)
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


def _base_universe_row(symbol: str, name: str, instrument_type: str, exchange: str) -> dict:
    return {
        "as_of_date": "2024-05-20",
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type,
        "exchange": exchange,
        "listed_date": "",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "industry": "ETF" if instrument_type == "ETF" else "UNKNOWN",
        "min_lot": 100,
        "t_plus_rule": "T+1",
        "available_time": "2024-05-20 08:00:00",
        "revision_id": "v1",
        "source": "LOCAL_HINT_FIXTURE",
    }
