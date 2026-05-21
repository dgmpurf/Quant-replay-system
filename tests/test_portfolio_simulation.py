import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import PortfolioSimulationSettings
from quant_replay_system.portfolio_simulation import (
    PortfolioSimulationResult,
    build_cash_ledger,
    build_equity_curve,
    build_position_ledger,
    build_trade_ledger,
    compute_portfolio_metrics,
    simulate_portfolio,
)


def test_equal_weight_sizing_works(tmp_path: Path) -> None:
    settings = _settings(tmp_path, round_lots=False)
    result = _simulate(tmp_path, settings=settings)
    buys = _filled_buys(result.trade_ledger)

    assert buys["gross_notional"].tolist() == pytest.approx([2000.0, 2000.0, 2000.0])


def test_max_position_weight_is_respected(tmp_path: Path) -> None:
    result = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False))
    buys = _filled_buys(result.trade_ledger)

    assert buys["gross_notional"].max() <= result.settings.initial_cash * result.settings.max_position_weight


def test_max_gross_exposure_is_respected(tmp_path: Path) -> None:
    result = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False))
    buys = _filled_buys(result.trade_ledger)

    assert buys["gross_notional"].sum() <= result.settings.initial_cash * result.settings.max_gross_exposure


def test_reserve_cash_pct_is_respected(tmp_path: Path) -> None:
    result = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False))
    buy_day = pd.Timestamp("2024-03-04")
    cash_after_buys = result.cash_ledger.loc[result.cash_ledger["date"] == buy_day, "ending_cash"].iloc[0]

    assert cash_after_buys >= result.settings.initial_cash * result.settings.reserve_cash_pct


def test_lot_rounding_works(tmp_path: Path) -> None:
    result = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=True, lot_size=100))
    buys = _filled_buys(result.trade_ledger).set_index("symbol")

    assert buys.loc["AAA", "quantity"] == 200
    assert buys.loc["BBB", "quantity"] == 100
    assert "CCC" not in buys.index


def test_trade_skipped_when_lot_rounding_results_in_zero_quantity(tmp_path: Path) -> None:
    trades = _simulated_trades(symbols=["HIGH"], buy_prices={"HIGH": 5000.0}, sell_prices={"HIGH": 5100.0})
    result = _simulate(tmp_path, simulated_trades=trades, settings=_settings(tmp_path, round_lots=True, lot_size=100))

    skipped = result.trade_ledger.loc[result.trade_ledger["status"] == "SKIPPED"]
    assert len(skipped) == 1
    assert skipped.iloc[0]["reason"] == "LOT_ROUNDING_ZERO"


def test_cash_never_goes_negative_by_default(tmp_path: Path) -> None:
    result = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False))

    assert result.cash_ledger["ending_cash"].min() >= 0


def test_trade_ledger_contains_expected_columns(tmp_path: Path) -> None:
    result = _simulate(tmp_path)

    expected = {
        "trade_id",
        "decision_date",
        "symbol",
        "side",
        "order_date",
        "execution_date",
        "execution_price",
        "quantity",
        "gross_notional",
        "fees",
        "taxes",
        "slippage",
        "net_cash_flow",
        "status",
        "reason",
    }
    assert expected.issubset(result.trade_ledger.columns)


def test_position_ledger_contains_expected_columns(tmp_path: Path) -> None:
    result = _simulate(tmp_path)

    expected = {
        "date",
        "symbol",
        "quantity",
        "average_cost",
        "market_price",
        "market_value",
        "unrealized_pnl",
        "realized_pnl",
        "status",
    }
    assert expected.issubset(result.position_ledger.columns)


def test_cash_ledger_reconciles_cash(tmp_path: Path) -> None:
    result = _simulate(tmp_path)

    for row in result.cash_ledger.to_dict("records"):
        expected = row["starting_cash"] + row["trade_cash_flow"] - row["fees"] - row["taxes"]
        assert row["ending_cash"] == pytest.approx(expected)


def test_equity_curve_total_equity_equals_cash_plus_market_value(tmp_path: Path) -> None:
    result = _simulate(tmp_path)

    assert result.equity_curve["total_equity"].tolist() == pytest.approx(
        (result.equity_curve["cash"] + result.equity_curve["market_value"]).tolist()
    )


def test_max_drawdown_calculation_works(tmp_path: Path) -> None:
    result = _simulate(
        tmp_path,
        simulated_trades=_simulated_trades(symbols=["AAA"], buy_prices={"AAA": 10.0}, sell_prices={"AAA": 11.0}),
        market_data=_market_data({"AAA": {"2024-03-04": 10.0, "2024-03-05": 8.0, "2024-03-06": 8.0, "2024-03-07": 11.0}}),
        settings=_settings(tmp_path, round_lots=False),
    )

    assert result.portfolio_metrics["max_drawdown"] == pytest.approx(-0.04)


def test_fees_and_slippage_reduce_returns(tmp_path: Path) -> None:
    clean = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False, commission_bps=0, slippage_bps=0))
    costly = _simulate(tmp_path, settings=_settings(tmp_path, round_lots=False, commission_bps=10, slippage_bps=10))

    assert costly.portfolio_metrics["total_return"] < clean.portfolio_metrics["total_return"]


def test_skipped_replay_trades_do_not_open_positions(tmp_path: Path) -> None:
    trades = _simulated_trades(symbols=["AAA"])
    trades.loc[0, "trade_status"] = "SKIPPED_BUY"
    trades.loc[0, "buy_status"] = "BLOCK"
    trades.loc[0, "buy_reason"] = "symbol suspended on execution date"
    result = _simulate(tmp_path, simulated_trades=trades)

    assert result.position_ledger.empty
    assert result.portfolio_metrics["number_of_positions"] == 0


def test_deterministic_output_for_same_inputs(tmp_path: Path) -> None:
    first = _simulate(tmp_path)
    second = _simulate(tmp_path)

    assert first.portfolio_run_id == second.portfolio_run_id
    assert first.portfolio_metrics == second.portfolio_metrics
    assert_frame_equal(first.trade_ledger, second.trade_ledger)
    assert_frame_equal(first.position_ledger, second.position_ledger)
    assert_frame_equal(first.cash_ledger, second.cash_ledger)
    assert_frame_equal(first.equity_curve, second.equity_curve)


def test_artifacts_are_written_and_csvs_are_readable_by_pandas(tmp_path: Path) -> None:
    result = _simulate(tmp_path)

    for key in [
        "trade_ledger",
        "position_ledger",
        "cash_ledger",
        "equity_curve",
        "portfolio_metrics",
    ]:
        assert result.artifact_paths[key].exists()
        exported = pd.read_csv(result.artifact_paths[key])
        assert isinstance(exported, pd.DataFrame)
    assert result.artifact_paths["portfolio_report"].exists()
    assert result.artifact_paths["metadata"].exists()


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = _simulate(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_low_level_builders_work_together(tmp_path: Path) -> None:
    settings = _settings(tmp_path, round_lots=False)
    trades = _simulated_trades()
    market = _market_data()
    calendar = _calendar()

    trade_ledger = build_trade_ledger(trades, settings, market, calendar)
    cash_ledger = build_cash_ledger(trade_ledger, settings, calendar)
    position_ledger = build_position_ledger(trade_ledger, market, calendar, settings)
    equity_curve = build_equity_curve(cash_ledger, position_ledger, settings)
    metrics = compute_portfolio_metrics(trade_ledger, position_ledger, cash_ledger, equity_curve, settings)

    assert not trade_ledger.empty
    assert not cash_ledger.empty
    assert not equity_curve.empty
    assert metrics["final_equity"] == pytest.approx(equity_curve.iloc[-1]["total_equity"])


def _simulate(
    tmp_path: Path,
    *,
    simulated_trades: pd.DataFrame | None = None,
    market_data: pd.DataFrame | None = None,
    settings: PortfolioSimulationSettings | None = None,
) -> PortfolioSimulationResult:
    return simulate_portfolio(
        simulated_trades=simulated_trades if simulated_trades is not None else _simulated_trades(),
        market_data=market_data if market_data is not None else _market_data(),
        trading_calendar=_calendar(),
        settings=settings or _settings(tmp_path),
    )


def _settings(tmp_path: Path, **updates) -> PortfolioSimulationSettings:
    payload = {
        "output_dir": tmp_path / "portfolio_simulations",
        "initial_cash": 10_000.0,
        "max_gross_exposure": 0.60,
        "max_position_weight": 0.20,
        "reserve_cash_pct": 0.40,
        "round_lots": True,
        "lot_size": 100,
        "commission_bps": 0.0,
        "slippage_bps": 0.0,
        "tax_bps": 0.0,
        "write_artifacts": True,
    }
    payload.update(updates)
    return PortfolioSimulationSettings(**payload)


def _filled_buys(trade_ledger: pd.DataFrame) -> pd.DataFrame:
    return trade_ledger.loc[(trade_ledger["side"] == "BUY") & (trade_ledger["status"] == "FILLED")].reset_index(drop=True)


def _simulated_trades(
    *,
    symbols: list[str] | None = None,
    buy_prices: dict[str, float] | None = None,
    sell_prices: dict[str, float] | None = None,
) -> pd.DataFrame:
    symbols = symbols or ["AAA", "BBB", "CCC"]
    default_buy = {"AAA": 10.0, "BBB": 20.0, "CCC": 25.0}
    default_sell = {"AAA": 11.0, "BBB": 22.0, "CCC": 20.0}
    if buy_prices:
        default_buy.update(buy_prices)
    if sell_prices:
        default_sell.update(sell_prices)

    rows = []
    for symbol in symbols:
        rows.append(
            {
                "decision_date": pd.Timestamp("2024-03-01"),
                "signal_date": pd.Timestamp("2024-03-01"),
                "symbol": symbol,
                "trade_status": "FILLED",
                "buy_status": "PASS",
                "buy_reason": "eligible",
                "buy_date": pd.Timestamp("2024-03-04"),
                "buy_price": default_buy[symbol],
                "planned_sell_date": pd.Timestamp("2024-03-07"),
                "sell_date": pd.Timestamp("2024-03-07"),
                "sell_price": default_sell[symbol],
                "sell_status": "PASS",
                "sell_reason": "eligible",
                "trade_return": default_sell[symbol] / default_buy[symbol] - 1.0,
            }
        )
    return pd.DataFrame(rows)


def _market_data(overrides: dict[str, dict[str, float]] | None = None) -> pd.DataFrame:
    prices = {
        "AAA": {"2024-03-04": 10.0, "2024-03-05": 10.5, "2024-03-06": 10.8, "2024-03-07": 11.0},
        "BBB": {"2024-03-04": 20.0, "2024-03-05": 21.0, "2024-03-06": 21.5, "2024-03-07": 22.0},
        "CCC": {"2024-03-04": 25.0, "2024-03-05": 23.0, "2024-03-06": 21.0, "2024-03-07": 20.0},
        "HIGH": {"2024-03-04": 5000.0, "2024-03-05": 5050.0, "2024-03-06": 5080.0, "2024-03-07": 5100.0},
    }
    if overrides:
        prices.update(overrides)

    rows = []
    for symbol, by_date in prices.items():
        for date, close in by_date.items():
            trade_date = pd.Timestamp(date)
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 1_000_000,
                    "amount": close * 1_000_000,
                    "pre_close": close,
                    "adj_factor": 1.0,
                    "is_suspended": False,
                    "limit_up": close * 1.1,
                    "limit_down": close * 0.9,
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "m1",
                    "source": "unit-test",
                }
            )
    return pd.DataFrame(rows)


def _calendar() -> TradingCalendar:
    rows = []
    for date in pd.date_range("2024-03-01", "2024-03-08", freq="D"):
        is_trading = date.weekday() < 5
        rows.append(
            {
                "trade_date": date,
                "is_trading_day": is_trading,
                "session_open": "09:30" if is_trading else "",
                "session_close": "15:00" if is_trading else "",
                "decision_time": "15:30" if is_trading else "",
                "reason": "normal" if is_trading else "weekend",
            }
        )
    return TradingCalendar(pd.DataFrame(rows))
