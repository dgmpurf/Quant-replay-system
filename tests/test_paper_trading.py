import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.config import PaperTradingSettings, load_settings
from quant_replay_system.paper_trading import (
    PaperTradeJournal,
    build_closed_trades,
    build_daily_summary,
    build_open_positions,
    create_paper_decision_log,
    generate_paper_trading_report,
    mark_to_market_paper_positions,
    record_paper_fill,
)


def test_paper_decision_log_is_created_from_candidates() -> None:
    decisions = _decisions()

    assert len(decisions) == 2
    assert set(decisions["symbol"]) == {"AAA", "BBB"}
    assert "component_scores" in decisions.columns


def test_decision_ids_are_deterministic() -> None:
    first = _decisions()
    second = _decisions()

    assert first["decision_id"].tolist() == second["decision_id"].tolist()


def test_manual_review_status_defaults_to_pending_review() -> None:
    decisions = _decisions()

    assert set(decisions["manual_review_status"]) == {"PENDING_REVIEW"}


def test_record_paper_fill_creates_fill_records() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=100)

    assert len(fills) == 1
    assert fills.iloc[0]["side"] == "BUY"
    assert fills.iloc[0]["gross_notional"] == pytest.approx(1000.0)


def test_buy_fills_create_open_positions() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=100)
    positions = build_open_positions(fills, _market_data(), mark_date="2024-03-05")

    assert len(positions) == 1
    assert positions.iloc[0]["quantity"] == pytest.approx(100.0)
    assert positions.iloc[0]["status"] == "OPEN"


def test_sell_fills_close_or_reduce_positions() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=200)
    fills = record_paper_fill(
        decisions,
        fills,
        decision_id=decisions.iloc[0]["decision_id"],
        side="SELL",
        fill_date="2024-03-06",
        fill_price=11.0,
        quantity=100,
        settings=_settings(),
    )
    positions = build_open_positions(fills, _market_data(), mark_date="2024-03-06")

    assert positions.iloc[0]["quantity"] == pytest.approx(100.0)


def test_lot_size_rounding_is_respected_if_enabled() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=150)

    assert fills.iloc[0]["quantity"] == pytest.approx(100.0)


def test_fractional_shares_are_rejected_by_default() -> None:
    decisions = _decisions()

    with pytest.raises(ValueError, match="fractional"):
        _buy_fill(decisions, price=10.0, quantity=100.5)


def test_open_positions_calculate_market_value_correctly() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=100)
    positions = build_open_positions(fills, _market_data(), mark_date="2024-03-05")

    assert positions.iloc[0]["last_mark_price"] == pytest.approx(12.0)
    assert positions.iloc[0]["market_value"] == pytest.approx(1200.0)
    assert positions.iloc[0]["unrealized_pnl"] == pytest.approx(200.0)


def test_closed_trades_calculate_realized_pnl_correctly() -> None:
    decisions = _decisions()
    fills = _round_trip_fills(decisions)
    closed = build_closed_trades(fills)

    assert len(closed) == 1
    assert closed.iloc[0]["realized_pnl"] == pytest.approx(200.0)
    assert closed.iloc[0]["realized_return_pct"] == pytest.approx(0.20)


def test_paper_cash_updates_correctly() -> None:
    decisions = _decisions()
    fills = _round_trip_fills(decisions)
    summary = build_daily_summary(
        open_positions=build_open_positions(fills, _market_data(), mark_date="2024-03-06"),
        closed_trades=build_closed_trades(fills),
        fills=fills,
        settings=_settings(),
        mark_date="2024-03-06",
    )

    assert summary.iloc[0]["paper_cash"] == pytest.approx(10_200.0)
    assert summary.iloc[0]["total_equity"] == pytest.approx(10_200.0)


def test_daily_summary_is_generated() -> None:
    journal = _journal()

    assert len(journal.daily_summary) == 1
    assert "total_equity" in journal.daily_summary.columns


def test_artifacts_are_written(tmp_path: Path) -> None:
    journal = _journal(tmp_path)

    assert journal.artifact_paths["artifact_dir"].exists()
    assert journal.artifact_paths["paper_report"].exists()
    assert journal.artifact_paths["decisions"].exists()
    assert journal.artifact_paths["fills"].exists()
    assert journal.artifact_paths["open_positions"].exists()
    assert journal.artifact_paths["closed_trades"].exists()
    assert journal.artifact_paths["daily_summary"].exists()


def test_csv_artifacts_are_readable_by_pandas(tmp_path: Path) -> None:
    journal = _journal(tmp_path)

    for key in ["decisions", "fills", "open_positions", "closed_trades", "daily_summary"]:
        exported = pd.read_csv(journal.artifact_paths[key])
        assert isinstance(exported, pd.DataFrame)


def test_metadata_json_is_written(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    metadata = json.loads(journal.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["journal_id"] == journal.journal_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_report_contains_no_live_trading_statement(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    content = journal.artifact_paths["paper_report"].read_text(encoding="utf-8")

    assert "No broker or live trading integration was invoked" in content


def test_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _journal(tmp_path)
    second = _journal(tmp_path)

    assert first.journal_id == second.journal_id
    assert_frame_equal(first.decisions, second.decisions)
    assert_frame_equal(first.fills, second.fills)
    assert_frame_equal(first.open_positions, second.open_positions)
    assert_frame_equal(first.closed_trades, second.closed_trades)
    assert_frame_equal(first.daily_summary, second.daily_summary)


def test_no_broker_or_live_trading_integration_is_invoked(tmp_path: Path) -> None:
    journal = _journal(tmp_path)

    assert journal.audit_metadata["live_trading_enabled"] is False
    assert journal.audit_metadata["broker_api_invoked"] is False
    assert journal.audit_metadata["paper_trading_only"] is True


def test_mark_to_market_updates_existing_positions() -> None:
    decisions = _decisions()
    fills = _buy_fill(decisions, price=10.0, quantity=100)
    positions = build_open_positions(fills, _market_data(), mark_date="2024-03-04")
    marked = mark_to_market_paper_positions(positions, _market_data(), mark_date="2024-03-05")

    assert marked.iloc[0]["last_mark_price"] == pytest.approx(12.0)
    assert marked.iloc[0]["market_value"] == pytest.approx(1200.0)


def test_generate_paper_trading_report_returns_structured_journal(tmp_path: Path) -> None:
    journal = _journal(tmp_path)

    assert isinstance(journal, PaperTradeJournal)
    assert journal.settings.enable_live_trading is False
    assert journal.settings.enable_broker_api is False


def _journal(tmp_path: Path | None = None) -> PaperTradeJournal:
    decisions = _decisions()
    fills = _round_trip_fills(decisions)
    return generate_paper_trading_report(
        decisions=decisions,
        fills=fills,
        market_data=_market_data(),
        mark_date="2024-03-06",
        settings=_settings(tmp_path),
    )


def _decisions() -> pd.DataFrame:
    return create_paper_decision_log(
        _candidates(),
        decision_date="2024-03-01",
        source_run_id="replay123",
        source_report_path="outputs/reports/replay123/report.md",
        planned_holding_horizon=5,
        planned_buy_date="2024-03-04",
        planned_sell_date="2024-03-08",
    )


def _buy_fill(decisions: pd.DataFrame, *, price: float, quantity: float) -> pd.DataFrame:
    return record_paper_fill(
        decisions,
        decision_id=decisions.iloc[0]["decision_id"],
        side="BUY",
        fill_date="2024-03-04",
        fill_price=price,
        quantity=quantity,
        settings=_settings(),
    )


def _round_trip_fills(decisions: pd.DataFrame) -> pd.DataFrame:
    fills = _buy_fill(decisions, price=10.0, quantity=100)
    return record_paper_fill(
        decisions,
        fills,
        decision_id=decisions.iloc[0]["decision_id"],
        side="SELL",
        fill_date="2024-03-06",
        fill_price=12.0,
        quantity=100,
        settings=_settings(),
    )


def _settings(tmp_path: Path | None = None) -> PaperTradingSettings:
    settings = load_settings(Path("config/default.yaml")).paper_trading
    updates = {"write_artifacts": tmp_path is not None}
    if tmp_path is not None:
        updates["output_dir"] = tmp_path / "paper_trading"
    return settings.model_copy(update=updates)


def _candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_date": pd.Timestamp("2024-03-01"),
                "symbol": "AAA",
                "name": "AAA Fund",
                "action": "PAPER_TRADE",
                "final_score": 82.5,
                "technical_score": 75.0,
                "liquidity_score": 70.0,
                "expectation_score": 65.0,
                "reality_score": 50.0,
                "sentiment_score": 50.0,
                "risk_penalty": 5.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 1,
            },
            {
                "decision_date": pd.Timestamp("2024-03-01"),
                "symbol": "BBB",
                "name": "BBB Fund",
                "action": "OBSERVE",
                "final_score": 68.0,
                "technical_score": 55.0,
                "liquidity_score": 60.0,
                "expectation_score": 52.0,
                "reality_score": 50.0,
                "sentiment_score": 50.0,
                "risk_penalty": 10.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 2,
            },
        ]
    )


def _market_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "trade_date": pd.Timestamp("2024-03-04"), "close": 10.0},
            {"symbol": "AAA", "trade_date": pd.Timestamp("2024-03-05"), "close": 12.0},
            {"symbol": "AAA", "trade_date": pd.Timestamp("2024-03-06"), "close": 12.0},
            {"symbol": "BBB", "trade_date": pd.Timestamp("2024-03-04"), "close": 20.0},
            {"symbol": "BBB", "trade_date": pd.Timestamp("2024-03-05"), "close": 21.0},
        ]
    )
