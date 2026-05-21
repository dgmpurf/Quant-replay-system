"""Account-level portfolio simulation from replay outputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from quant_replay_system.calendar import TradingCalendar, load_trading_calendar
from quant_replay_system.config import PortfolioSimulationSettings, Settings, load_settings
from quant_replay_system.data import load_market_data


PORTFOLIO_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Uses replay-provided execution outcomes; it does not re-check exchange execution eligibility.",
    "MVP position sizing is equal-weight only.",
    "Corporate-action cash flows and benchmark-aware attribution are not implemented.",
    "Portfolio accounting is simplified and intended for research review, not brokerage reconciliation.",
]


@dataclass(frozen=True)
class TradeLedgerEntry:
    trade_id: str
    decision_date: pd.Timestamp
    symbol: str
    side: str
    order_date: pd.Timestamp
    execution_date: pd.Timestamp
    execution_price: float | None
    quantity: float
    gross_notional: float
    fees: float
    taxes: float
    slippage: float
    net_cash_flow: float
    status: str
    reason: str


@dataclass(frozen=True)
class PositionLedgerEntry:
    date: pd.Timestamp
    symbol: str
    quantity: float
    average_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    status: str


@dataclass(frozen=True)
class CashLedgerEntry:
    date: pd.Timestamp
    starting_cash: float
    trade_cash_flow: float
    fees: float
    ending_cash: float


@dataclass(frozen=True)
class PortfolioArtifactPaths:
    artifact_dir: Path
    portfolio_report: Path
    trade_ledger: Path
    position_ledger: Path
    cash_ledger: Path
    equity_curve: Path
    portfolio_metrics: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "portfolio_report": self.portfolio_report,
            "trade_ledger": self.trade_ledger,
            "position_ledger": self.position_ledger,
            "cash_ledger": self.cash_ledger,
            "equity_curve": self.equity_curve,
            "portfolio_metrics": self.portfolio_metrics,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PortfolioSimulationResult:
    portfolio_run_id: str
    settings: PortfolioSimulationSettings
    trade_ledger: pd.DataFrame
    position_ledger: pd.DataFrame
    cash_ledger: pd.DataFrame
    equity_curve: pd.DataFrame
    portfolio_metrics: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def simulate_portfolio(
    replay_results: Any | None = None,
    market_data: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    settings: PortfolioSimulationSettings | dict[str, Any] | None = None,
    config: Settings | str | Path | None = None,
    *,
    simulated_trades: pd.DataFrame | None = None,
    portfolio_run_id: str | None = None,
) -> PortfolioSimulationResult:
    """Simulate account-level ledgers from replay outputs or simulated trades."""

    project_settings = _load_project_settings(config)
    portfolio_settings = _coerce_portfolio_settings(settings or project_settings.portfolio_simulation)
    market = market_data.copy(deep=True) if market_data is not None else load_market_data(project_settings.data.mock_prices)
    calendar = (
        trading_calendar
        if trading_calendar is not None
        else load_trading_calendar(project_settings.data.mock_trading_calendar)
    )
    trades = _extract_simulated_trades(replay_results=replay_results, simulated_trades=simulated_trades)
    normalized_market = _prepare_market_data(market)
    source_ids = _source_ids(replay_results)
    effective_run_id = portfolio_run_id or generate_portfolio_run_id(trades, portfolio_settings, source_ids)
    paths = resolve_portfolio_artifact_paths(portfolio_settings.output_dir, effective_run_id)

    trade_ledger = build_trade_ledger(trades, portfolio_settings, normalized_market, calendar)
    cash_ledger = build_cash_ledger(trade_ledger, portfolio_settings, calendar)
    position_ledger = build_position_ledger(trade_ledger, normalized_market, calendar, portfolio_settings)
    equity_curve = build_equity_curve(cash_ledger, position_ledger, portfolio_settings)
    metrics = compute_portfolio_metrics(trade_ledger, position_ledger, cash_ledger, equity_curve, portfolio_settings)
    warnings = _portfolio_warnings(trades, trade_ledger)
    audit_metadata = {
        "portfolio_run_id": effective_run_id,
        "source_ids": source_ids,
        "input_trade_rows": len(trades),
        "trade_ledger_rows": len(trade_ledger),
        "position_ledger_rows": len(position_ledger),
        "cash_ledger_rows": len(cash_ledger),
        "equity_curve_rows": len(equity_curve),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
    }

    result = PortfolioSimulationResult(
        portfolio_run_id=effective_run_id,
        settings=portfolio_settings,
        trade_ledger=trade_ledger,
        position_ledger=position_ledger,
        cash_ledger=cash_ledger,
        equity_curve=equity_curve,
        portfolio_metrics=metrics,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        audit_metadata=audit_metadata,
    )
    if portfolio_settings.write_artifacts:
        write_portfolio_simulation_artifacts(result)
    return result


def build_trade_ledger(
    simulated_trades: pd.DataFrame,
    settings: PortfolioSimulationSettings,
    market_data: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
) -> pd.DataFrame:
    """Build buy/sell trade ledger rows from replay-simulated trades."""

    trades = _prepare_simulated_trades(simulated_trades)
    if trades.empty:
        return _empty_trade_ledger()

    ledger_rows: list[dict[str, Any]] = []
    active_positions: dict[str, dict[str, Any]] = {}
    cash = float(settings.initial_cash)
    skipped_due_to_replay = trades.loc[~_is_replay_buy_fillable(trades)].copy()
    for row in skipped_due_to_replay.to_dict("records"):
        ledger_rows.append(_skipped_trade_row(row, _replay_skip_reason(row)))

    fillable = trades.loc[_is_replay_buy_fillable(trades)].copy()
    for event_date in _event_dates(fillable):
        sell_rows = _rows_selling_on(fillable, event_date)
        for row in sell_rows.to_dict("records"):
            symbol = str(row["symbol"])
            position = active_positions.pop(symbol, None)
            if position is None:
                continue
            sell_entry = _sell_ledger_row(row, position, settings)
            cash += float(sell_entry["net_cash_flow"])
            ledger_rows.append(sell_entry)

        buy_rows = _rows_buying_on(fillable, event_date)
        if buy_rows.empty:
            continue

        current_market_value = _current_market_value(active_positions, event_date, market_data)
        current_equity = cash + current_market_value if settings.allow_reinvestment else settings.initial_cash
        deployable_capital = _deployable_capital(current_equity, current_market_value, settings)
        per_candidate_allocation = (
            min(deployable_capital / len(buy_rows), current_equity * settings.max_position_weight)
            if len(buy_rows)
            else 0.0
        )
        for row in buy_rows.sort_values("symbol").to_dict("records"):
            buy_entry = _buy_ledger_row(
                row=row,
                cash=cash,
                allocation=per_candidate_allocation,
                settings=settings,
            )
            ledger_rows.append(buy_entry)
            if buy_entry["status"] != "FILLED":
                continue
            cash += float(buy_entry["net_cash_flow"])
            active_positions[str(row["symbol"])] = {
                "symbol": str(row["symbol"]),
                "decision_date": buy_entry["decision_date"],
                "buy_date": buy_entry["execution_date"],
                "sell_date": _timestamp_or_nat(row.get("sell_date")),
                "quantity": float(buy_entry["quantity"]),
                "average_cost": (abs(float(buy_entry["net_cash_flow"])) / float(buy_entry["quantity"])),
                "buy_total_cost": abs(float(buy_entry["net_cash_flow"])),
                "buy_trade_id": buy_entry["trade_id"],
            }

    # Sell any remaining closed positions after the last buy date.
    for row in fillable.sort_values(["sell_date", "symbol"]).to_dict("records"):
        symbol = str(row["symbol"])
        sell_date = _timestamp_or_nat(row.get("sell_date"))
        if symbol not in active_positions or pd.isna(sell_date):
            continue
        position = active_positions.pop(symbol)
        sell_entry = _sell_ledger_row(row, position, settings)
        cash += float(sell_entry["net_cash_flow"])
        ledger_rows.append(sell_entry)

    return _finalize_trade_ledger(pd.DataFrame(ledger_rows))


def build_cash_ledger(
    trade_ledger: pd.DataFrame,
    settings: PortfolioSimulationSettings,
    trading_calendar: TradingCalendar | None = None,
) -> pd.DataFrame:
    """Build daily cash ledger from trade cash flows."""

    if trade_ledger.empty:
        return pd.DataFrame(
            [
                {
                    "date": pd.NaT,
                    "starting_cash": settings.initial_cash,
                    "trade_cash_flow": 0.0,
                    "fees": 0.0,
                    "taxes": 0.0,
                    "ending_cash": settings.initial_cash,
                }
            ]
        )

    filled = trade_ledger.loc[trade_ledger["status"] == "FILLED"].copy()
    dates = _ledger_dates(trade_ledger, trading_calendar)
    cash = float(settings.initial_cash)
    rows = []
    for date in dates:
        day_trades = filled.loc[filled["execution_date"] == date]
        trade_cash_flow = float(day_trades["signed_gross_cash_flow"].sum()) if not day_trades.empty else 0.0
        fees = float(day_trades["fees"].sum()) if not day_trades.empty else 0.0
        taxes = float(day_trades["taxes"].sum()) if not day_trades.empty else 0.0
        starting_cash = cash
        cash = starting_cash + trade_cash_flow - fees - taxes
        rows.append(
            {
                "date": date,
                "starting_cash": starting_cash,
                "trade_cash_flow": trade_cash_flow,
                "fees": fees,
                "taxes": taxes,
                "ending_cash": cash,
            }
        )
    return pd.DataFrame(rows)


def build_position_ledger(
    trade_ledger: pd.DataFrame,
    market_data: pd.DataFrame,
    trading_calendar: TradingCalendar | None,
    settings: PortfolioSimulationSettings,
) -> pd.DataFrame:
    """Build end-of-day position ledger rows."""

    if trade_ledger.empty:
        return _empty_position_ledger()

    buys = trade_ledger.loc[(trade_ledger["side"] == "BUY") & (trade_ledger["status"] == "FILLED")].copy()
    sells = trade_ledger.loc[(trade_ledger["side"] == "SELL") & (trade_ledger["status"] == "FILLED")].copy()
    if buys.empty:
        return _empty_position_ledger()

    sell_by_symbol = sells.sort_values("execution_date").groupby("symbol", as_index=False).tail(1)
    sell_map = {row["symbol"]: row for row in sell_by_symbol.to_dict("records")}
    dates = _ledger_dates(trade_ledger, trading_calendar)
    rows = []

    for buy in buys.sort_values(["execution_date", "symbol"]).to_dict("records"):
        symbol = str(buy["symbol"])
        buy_date = pd.Timestamp(buy["execution_date"]).normalize()
        sell = sell_map.get(symbol)
        sell_date = pd.Timestamp(sell["execution_date"]).normalize() if sell is not None else pd.NaT
        average_cost = abs(float(buy["net_cash_flow"])) / float(buy["quantity"])
        for date in dates:
            if date < buy_date:
                continue
            if pd.notna(sell_date) and date > sell_date:
                continue
            closed = pd.notna(sell_date) and date == sell_date
            quantity = 0.0 if closed else float(buy["quantity"])
            market_price = _market_price(symbol, date, market_data, fallback=float(buy["execution_price"]))
            market_value = 0.0 if closed else quantity * market_price
            unrealized_pnl = 0.0 if closed else market_value - quantity * average_cost
            realized_pnl = 0.0
            if closed and sell is not None:
                realized_pnl = float(sell["net_cash_flow"]) - abs(float(buy["net_cash_flow"]))
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "quantity": quantity,
                    "average_cost": average_cost,
                    "market_price": market_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl,
                    "status": "CLOSED" if closed else "OPEN",
                }
            )
    return _finalize_position_ledger(pd.DataFrame(rows))


def build_equity_curve(
    cash_ledger: pd.DataFrame,
    position_ledger: pd.DataFrame,
    settings: PortfolioSimulationSettings,
) -> pd.DataFrame:
    """Build daily portfolio equity curve."""

    if cash_ledger.empty:
        return _empty_equity_curve()

    rows = []
    cumulative_peak = None
    previous_equity = None
    for cash_row in cash_ledger.sort_values("date").to_dict("records"):
        date = cash_row["date"]
        positions = position_ledger.loc[position_ledger["date"] == date] if not position_ledger.empty else position_ledger
        market_value = float(positions["market_value"].sum()) if not positions.empty and settings.mark_to_market else 0.0
        cash = float(cash_row["ending_cash"])
        total_equity = cash + market_value
        daily_return = 0.0 if previous_equity in {None, 0.0} else total_equity / previous_equity - 1.0
        cumulative_peak = total_equity if cumulative_peak is None else max(cumulative_peak, total_equity)
        drawdown = 0.0 if cumulative_peak in {None, 0.0} else total_equity / cumulative_peak - 1.0
        rows.append(
            {
                "date": date,
                "cash": cash,
                "market_value": market_value,
                "total_equity": total_equity,
                "daily_return": daily_return,
                "drawdown": drawdown,
            }
        )
        previous_equity = total_equity
    return pd.DataFrame(rows)


def compute_portfolio_metrics(
    trade_ledger: pd.DataFrame,
    position_ledger: pd.DataFrame,
    cash_ledger: pd.DataFrame,
    equity_curve: pd.DataFrame,
    settings: PortfolioSimulationSettings,
) -> dict[str, Any]:
    """Compute portfolio-level performance and exposure metrics."""

    initial_cash = float(settings.initial_cash)
    final_equity = initial_cash if equity_curve.empty else float(equity_curve.iloc[-1]["total_equity"])
    total_return = final_equity / initial_cash - 1.0 if initial_cash else None
    dates = len(equity_curve)
    annualized_return = None
    if total_return is not None and dates > 1 and total_return > -1:
        annualized_return = (1.0 + total_return) ** (252.0 / (dates - 1)) - 1.0

    round_trips = _round_trip_returns(trade_ledger)
    exposure = pd.Series(dtype="float64")
    if not equity_curve.empty:
        exposure = (
            pd.to_numeric(equity_curve["market_value"], errors="coerce")
            / pd.to_numeric(equity_curve["total_equity"], errors="coerce").replace(0, np.nan)
        ).dropna()

    filled_trades = trade_ledger.loc[trade_ledger["status"] == "FILLED"] if not trade_ledger.empty else trade_ledger
    skipped = trade_ledger.loc[trade_ledger["status"] != "FILLED"] if not trade_ledger.empty else trade_ledger
    turnover_denominator = equity_curve["total_equity"].mean() if not equity_curve.empty else initial_cash
    turnover = (
        float(filled_trades["gross_notional"].abs().sum()) / float(turnover_denominator)
        if turnover_denominator
        else None
    )
    cash_utilization = None
    if not equity_curve.empty:
        cash_utilization = 1.0 - float(equity_curve["cash"].mean()) / float(equity_curve["total_equity"].mean())

    return {
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "total_return": total_return,
        "annualized_return": annualized_return,
        "max_drawdown": None if equity_curve.empty else float(equity_curve["drawdown"].min()),
        "win_rate": None if round_trips.empty else float((round_trips > 0).mean()),
        "average_trade_return": None if round_trips.empty else float(round_trips.mean()),
        "median_trade_return": None if round_trips.empty else float(round_trips.median()),
        "best_trade_return": None if round_trips.empty else float(round_trips.max()),
        "worst_trade_return": None if round_trips.empty else float(round_trips.min()),
        "turnover": turnover,
        "average_gross_exposure": None if exposure.empty else float(exposure.mean()),
        "max_gross_exposure": None if exposure.empty else float(exposure.max()),
        "cash_utilization": cash_utilization,
        "number_of_trades": int(len(filled_trades)),
        "number_of_positions": int(
            trade_ledger.loc[(trade_ledger["side"] == "BUY") & (trade_ledger["status"] == "FILLED"), "symbol"].nunique()
        )
        if not trade_ledger.empty
        else 0,
        "skipped_trades_due_to_cash_or_lot_rounding": int(
            skipped["reason"].isin(["LOT_ROUNDING_ZERO", "INSUFFICIENT_CASH", "EXPOSURE_LIMIT"]).sum()
        )
        if not skipped.empty
        else 0,
    }


def generate_portfolio_run_id(
    simulated_trades: pd.DataFrame,
    settings: PortfolioSimulationSettings,
    source_ids: list[str] | None = None,
) -> str:
    """Generate a deterministic portfolio run id."""

    frame = _prepare_simulated_trades(simulated_trades)
    payload = {
        "source_ids": source_ids or [],
        "decision_dates": sorted(
            str(pd.Timestamp(date).date())
            for date in pd.to_datetime(frame["decision_date"]).dropna().dt.normalize().unique()
        )
        if "decision_date" in frame.columns and not frame.empty
        else [],
        "symbols": sorted(str(symbol) for symbol in frame["symbol"].dropna().unique()) if "symbol" in frame.columns else [],
        "settings": settings.model_dump() if hasattr(settings, "model_dump") else dict(settings),
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def resolve_portfolio_artifact_paths(output_dir: str | Path, portfolio_run_id: str) -> PortfolioArtifactPaths:
    """Resolve stable artifact paths for one portfolio simulation."""

    artifact_dir = Path(output_dir) / portfolio_run_id
    return PortfolioArtifactPaths(
        artifact_dir=artifact_dir,
        portfolio_report=artifact_dir / "portfolio_report.md",
        trade_ledger=artifact_dir / "trade_ledger.csv",
        position_ledger=artifact_dir / "position_ledger.csv",
        cash_ledger=artifact_dir / "cash_ledger.csv",
        equity_curve=artifact_dir / "equity_curve.csv",
        portfolio_metrics=artifact_dir / "portfolio_metrics.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_portfolio_simulation_artifacts(result: PortfolioSimulationResult) -> PortfolioArtifactPaths:
    """Write portfolio ledgers, metrics, markdown report, and metadata."""

    paths = PortfolioArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.trade_ledger, paths.trade_ledger)
    _export_dataframe(result.position_ledger, paths.position_ledger)
    _export_dataframe(result.cash_ledger, paths.cash_ledger)
    _export_dataframe(result.equity_curve, paths.equity_curve)
    _export_dataframe(pd.DataFrame([result.portfolio_metrics]), paths.portfolio_metrics)

    metadata = build_portfolio_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.portfolio_report.write_text(render_portfolio_report(result, paths, metadata), encoding="utf-8")
    return paths


def build_portfolio_metadata(result: PortfolioSimulationResult, paths: PortfolioArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for portfolio simulation."""

    output_files = {name: str(path) for name, path in paths.as_dict().items() if name != "artifact_dir"}
    return {
        "portfolio_run_id": result.portfolio_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "settings": result.settings.model_dump() if hasattr(result.settings, "model_dump") else dict(result.settings),
        "row_counts": {
            "trade_ledger": len(result.trade_ledger),
            "position_ledger": len(result.position_ledger),
            "cash_ledger": len(result.cash_ledger),
            "equity_curve": len(result.equity_curve),
        },
        "portfolio_metrics": result.portfolio_metrics,
        "audit_metadata": result.audit_metadata,
        "output_files": output_files,
        "warnings": result.warnings,
        "known_limitations": PORTFOLIO_LIMITATIONS,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
    }


def render_portfolio_report(
    result: PortfolioSimulationResult,
    paths: PortfolioArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render markdown portfolio simulation report."""

    lines = [
        f"# Portfolio Simulation Report: {result.portfolio_run_id}",
        "",
        "## Portfolio Metadata",
        "",
        _dict_table(
            {
                "portfolio_run_id": result.portfolio_run_id,
                "artifact_dir": paths.artifact_dir,
                "initial_cash": result.settings.initial_cash,
                "sizing_method": result.settings.sizing_method,
                "max_gross_exposure": result.settings.max_gross_exposure,
                "max_position_weight": result.settings.max_position_weight,
            }
        ),
        "",
        "## Portfolio Metrics",
        "",
        _dict_table(result.portfolio_metrics),
        "",
        "## Trade Ledger",
        "",
        _markdown_table(result.trade_ledger, _trade_ledger_columns()),
        "",
        "## Position Ledger",
        "",
        _markdown_table(result.position_ledger, _position_ledger_columns()),
        "",
        "## Cash Ledger",
        "",
        _markdown_table(result.cash_ledger, _cash_ledger_columns()),
        "",
        "## Equity Curve",
        "",
        _markdown_table(result.equity_curve, _equity_curve_columns()),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known Limitations",
        "",
        "\n".join(f"- {item}" for item in metadata["known_limitations"]),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _extract_simulated_trades(replay_results: Any | None, simulated_trades: pd.DataFrame | None) -> pd.DataFrame:
    if simulated_trades is not None:
        return _prepare_simulated_trades(simulated_trades)
    if isinstance(replay_results, pd.DataFrame):
        return _prepare_simulated_trades(replay_results)
    if replay_results is None:
        return _empty_simulated_trades()

    frames = []
    if hasattr(replay_results, "replay_results"):
        iterable = replay_results.replay_results
    elif hasattr(replay_results, "simulated_trades"):
        iterable = [replay_results]
    else:
        iterable = list(replay_results)

    for result in iterable:
        frame = result.simulated_trades.copy(deep=True)
        if "decision_date" not in frame.columns:
            frame["decision_date"] = getattr(result, "decision_date", pd.NaT)
        if "replay_run_id" not in frame.columns and hasattr(result, "run_id"):
            frame["replay_run_id"] = result.run_id
        frames.append(frame)
    if not frames:
        return _empty_simulated_trades()
    return _prepare_simulated_trades(pd.concat(frames, ignore_index=True))


def _prepare_simulated_trades(frame: pd.DataFrame) -> pd.DataFrame:
    trades = frame.copy(deep=True)
    if trades.empty:
        return _empty_simulated_trades()
    if "decision_date" not in trades.columns:
        trades["decision_date"] = trades.get("signal_date", pd.NaT)
    for column in ["decision_date", "signal_date", "buy_date", "sell_date", "planned_sell_date", "execution_date"]:
        if column in trades.columns:
            trades[column] = pd.to_datetime(trades[column], errors="coerce").dt.normalize()
    for column in ["buy_price", "sell_price"]:
        if column in trades.columns:
            trades[column] = pd.to_numeric(trades[column], errors="coerce")
    for column in ["symbol", "trade_status", "buy_status", "buy_reason", "sell_status", "sell_reason"]:
        if column not in trades.columns:
            trades[column] = pd.NA
    for column in ["buy_date", "sell_date", "planned_sell_date", "execution_date", "buy_price", "sell_price"]:
        if column not in trades.columns:
            trades[column] = pd.NA
    return trades.sort_values(["buy_date", "symbol"], na_position="last").reset_index(drop=True)


def _prepare_market_data(market_data: pd.DataFrame) -> pd.DataFrame:
    market = market_data.copy(deep=True)
    if market.empty:
        return market
    if "trade_date" in market.columns:
        market["trade_date"] = pd.to_datetime(market["trade_date"], errors="coerce").dt.normalize()
    if "close" in market.columns:
        market["close"] = pd.to_numeric(market["close"], errors="coerce")
    return market.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def _source_ids(replay_results: Any | None) -> list[str]:
    if replay_results is None or isinstance(replay_results, pd.DataFrame):
        return []
    if hasattr(replay_results, "batch_id"):
        return [str(replay_results.batch_id)]
    if hasattr(replay_results, "run_id"):
        return [str(replay_results.run_id)]
    ids = []
    try:
        for result in replay_results:
            if hasattr(result, "run_id"):
                ids.append(str(result.run_id))
    except TypeError:
        return []
    return ids


def _is_replay_buy_fillable(trades: pd.DataFrame) -> pd.Series:
    return (
        (trades["buy_status"].fillna("PASS") == "PASS")
        & (trades["trade_status"].isin(["FILLED", "EXIT_BLOCKED"]))
        & trades["buy_price"].notna()
        & trades["buy_date"].notna()
    )


def _event_dates(trades: pd.DataFrame) -> list[pd.Timestamp]:
    values = []
    for column in ["buy_date", "sell_date"]:
        if column in trades.columns:
            values.extend(pd.to_datetime(trades[column], errors="coerce").dropna().dt.normalize().tolist())
    return sorted(set(pd.Timestamp(value).normalize() for value in values))


def _rows_selling_on(trades: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    if "sell_date" not in trades.columns:
        return trades.iloc[0:0]
    return trades.loc[(trades["sell_date"] == date) & (trades["sell_price"].notna()) & (trades["trade_status"] == "FILLED")]


def _rows_buying_on(trades: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    return trades.loc[trades["buy_date"] == date].copy()


def _deployable_capital(current_equity: float, current_market_value: float, settings: PortfolioSimulationSettings) -> float:
    target_gross = current_equity * min(settings.max_gross_exposure, max(0.0, 1.0 - settings.reserve_cash_pct))
    return max(0.0, target_gross - current_market_value)


def _buy_ledger_row(
    row: dict[str, Any],
    cash: float,
    allocation: float,
    settings: PortfolioSimulationSettings,
) -> dict[str, Any]:
    symbol = str(row["symbol"])
    buy_date = _timestamp_or_nat(row.get("buy_date"))
    base_price = float(row["buy_price"])
    execution_price = base_price * (1.0 + settings.slippage_bps / 10_000.0)
    quantity = _sized_quantity(allocation, execution_price, settings)
    if allocation <= 0:
        return _skipped_trade_row(row, "EXPOSURE_LIMIT")
    if quantity <= 0:
        return _skipped_trade_row(row, "LOT_ROUNDING_ZERO")

    quantity = _reduce_quantity_for_cash(quantity, execution_price, cash, settings)
    if quantity <= 0:
        return _skipped_trade_row(row, "INSUFFICIENT_CASH")

    gross_notional = quantity * execution_price
    fees = _fees(gross_notional, settings)
    taxes = 0.0
    if not settings.allow_negative_cash and gross_notional + fees + taxes > cash + 1e-9:
        return _skipped_trade_row(row, "INSUFFICIENT_CASH")

    slippage = (execution_price - base_price) * quantity
    net_cash_flow = -(gross_notional + fees + taxes)
    return {
        "trade_id": _trade_id(row, "BUY"),
        "decision_date": _timestamp_or_nat(row.get("decision_date")),
        "symbol": symbol,
        "side": "BUY",
        "order_date": _timestamp_or_nat(row.get("signal_date", row.get("decision_date"))),
        "execution_date": buy_date,
        "execution_price": execution_price,
        "quantity": quantity,
        "gross_notional": gross_notional,
        "signed_gross_cash_flow": -gross_notional,
        "fees": fees,
        "taxes": taxes,
        "slippage": slippage,
        "net_cash_flow": net_cash_flow,
        "status": "FILLED",
        "reason": "eligible",
    }


def _sell_ledger_row(
    row: dict[str, Any],
    position: dict[str, Any],
    settings: PortfolioSimulationSettings,
) -> dict[str, Any]:
    symbol = str(row["symbol"])
    sell_date = _timestamp_or_nat(row.get("sell_date"))
    base_price = float(row["sell_price"])
    execution_price = base_price * (1.0 - settings.slippage_bps / 10_000.0)
    quantity = float(position["quantity"])
    gross_notional = quantity * execution_price
    fees = _fees(gross_notional, settings)
    taxes = gross_notional * settings.tax_bps / 10_000.0
    slippage = (base_price - execution_price) * quantity
    net_cash_flow = gross_notional - fees - taxes
    return {
        "trade_id": _trade_id(row, "SELL"),
        "decision_date": _timestamp_or_nat(row.get("decision_date")),
        "symbol": symbol,
        "side": "SELL",
        "order_date": _timestamp_or_nat(row.get("planned_sell_date", sell_date)),
        "execution_date": sell_date,
        "execution_price": execution_price,
        "quantity": quantity,
        "gross_notional": gross_notional,
        "signed_gross_cash_flow": gross_notional,
        "fees": fees,
        "taxes": taxes,
        "slippage": slippage,
        "net_cash_flow": net_cash_flow,
        "status": "FILLED",
        "reason": "planned_exit",
    }


def _skipped_trade_row(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "trade_id": _trade_id(row, "BUY"),
        "decision_date": _timestamp_or_nat(row.get("decision_date")),
        "symbol": str(row.get("symbol", "")),
        "side": "BUY",
        "order_date": _timestamp_or_nat(row.get("signal_date", row.get("decision_date"))),
        "execution_date": _timestamp_or_nat(row.get("buy_date", row.get("execution_date"))),
        "execution_price": _none_if_nan(row.get("buy_price")),
        "quantity": 0.0,
        "gross_notional": 0.0,
        "signed_gross_cash_flow": 0.0,
        "fees": 0.0,
        "taxes": 0.0,
        "slippage": 0.0,
        "net_cash_flow": 0.0,
        "status": "SKIPPED",
        "reason": reason,
    }


def _replay_skip_reason(row: dict[str, Any]) -> str:
    status = str(row.get("trade_status", "")).strip()
    if status and status != "nan":
        return status
    for key in ["buy_reason", "sell_reason"]:
        value = row.get(key)
        if value is not None and not pd.isna(value):
            return str(value)
    return "REPLAY_BLOCKED"


def _sized_quantity(allocation: float, execution_price: float, settings: PortfolioSimulationSettings) -> float:
    raw_quantity = allocation / execution_price if execution_price else 0.0
    if settings.allow_fractional_shares:
        return raw_quantity
    whole_quantity = np.floor(raw_quantity)
    if settings.round_lots:
        return float(np.floor(whole_quantity / settings.lot_size) * settings.lot_size)
    return float(whole_quantity)


def _reduce_quantity_for_cash(
    quantity: float,
    execution_price: float,
    cash: float,
    settings: PortfolioSimulationSettings,
) -> float:
    if settings.allow_negative_cash:
        return quantity
    candidate = quantity
    while candidate > 0:
        gross = candidate * execution_price
        if gross + _fees(gross, settings) <= cash + 1e-9:
            return candidate
        candidate = candidate - (settings.lot_size if settings.round_lots and not settings.allow_fractional_shares else 1.0)
    return 0.0


def _fees(gross_notional: float, settings: PortfolioSimulationSettings) -> float:
    if gross_notional <= 0:
        return 0.0
    computed = gross_notional * settings.commission_bps / 10_000.0
    return max(computed, settings.min_commission)


def _current_market_value(
    positions: dict[str, dict[str, Any]],
    date: pd.Timestamp,
    market_data: pd.DataFrame | None,
) -> float:
    if not positions:
        return 0.0
    total = 0.0
    for position in positions.values():
        price = _market_price(str(position["symbol"]), date, market_data, fallback=float(position["average_cost"]))
        total += float(position["quantity"]) * price
    return total


def _market_price(symbol: str, date: pd.Timestamp, market_data: pd.DataFrame | None, fallback: float) -> float:
    if market_data is None or market_data.empty or "trade_date" not in market_data.columns or "close" not in market_data.columns:
        return fallback
    rows = market_data.loc[(market_data["symbol"] == symbol) & (market_data["trade_date"] <= date)].dropna(subset=["close"])
    if rows.empty:
        return fallback
    return float(rows.sort_values("trade_date").iloc[-1]["close"])


def _ledger_dates(trade_ledger: pd.DataFrame, trading_calendar: TradingCalendar | None) -> list[pd.Timestamp]:
    dates = pd.to_datetime(trade_ledger["execution_date"], errors="coerce").dropna().dt.normalize()
    if dates.empty:
        return []
    start = pd.Timestamp(dates.min()).normalize()
    end = pd.Timestamp(dates.max()).normalize()
    if trading_calendar is not None:
        try:
            return trading_calendar.trading_days_between(start, end)
        except ValueError:
            pass
    return [pd.Timestamp(date).normalize() for date in pd.date_range(start, end, freq="D")]


def _round_trip_returns(trade_ledger: pd.DataFrame) -> pd.Series:
    if trade_ledger.empty:
        return pd.Series(dtype="float64")
    returns = []
    buys = trade_ledger.loc[(trade_ledger["side"] == "BUY") & (trade_ledger["status"] == "FILLED")]
    sells = trade_ledger.loc[(trade_ledger["side"] == "SELL") & (trade_ledger["status"] == "FILLED")]
    sell_by_symbol = sells.sort_values("execution_date").groupby("symbol", as_index=False).tail(1)
    sell_map = {row["symbol"]: row for row in sell_by_symbol.to_dict("records")}
    for buy in buys.to_dict("records"):
        sell = sell_map.get(buy["symbol"])
        if sell is None:
            continue
        cost = abs(float(buy["net_cash_flow"]))
        if cost:
            returns.append((float(sell["net_cash_flow"]) - cost) / cost)
    return pd.Series(returns, dtype="float64")


def _portfolio_warnings(simulated_trades: pd.DataFrame, trade_ledger: pd.DataFrame) -> list[str]:
    warnings = []
    replay_skips = int((simulated_trades.get("trade_status", pd.Series(dtype="object")) != "FILLED").sum()) if not simulated_trades.empty else 0
    if replay_skips:
        warnings.append(f"{replay_skips} replay trade(s) were not opened as positions.")
    sizing_skips = trade_ledger.loc[trade_ledger["reason"].isin(["LOT_ROUNDING_ZERO", "INSUFFICIENT_CASH", "EXPOSURE_LIMIT"])]
    if not sizing_skips.empty:
        warnings.append(f"{len(sizing_skips)} trade(s) skipped by portfolio sizing constraints.")
    return warnings


def _finalize_trade_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    ledger = frame.copy()
    for column in _trade_ledger_columns():
        if column not in ledger.columns:
            ledger[column] = pd.NA
    return ledger[_trade_ledger_columns()].sort_values(["execution_date", "symbol", "side"]).reset_index(drop=True)


def _finalize_position_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    ledger = frame.copy()
    for column in _position_ledger_columns():
        if column not in ledger.columns:
            ledger[column] = pd.NA
    return ledger[_position_ledger_columns()].sort_values(["date", "symbol"]).reset_index(drop=True)


def _empty_simulated_trades() -> pd.DataFrame:
    return pd.DataFrame(columns=["decision_date", "symbol", "trade_status", "buy_status", "buy_date", "buy_price"])


def _empty_trade_ledger() -> pd.DataFrame:
    return pd.DataFrame(columns=_trade_ledger_columns())


def _empty_position_ledger() -> pd.DataFrame:
    return pd.DataFrame(columns=_position_ledger_columns())


def _empty_equity_curve() -> pd.DataFrame:
    return pd.DataFrame(columns=_equity_curve_columns())


def _trade_ledger_columns() -> list[str]:
    return [
        "trade_id",
        "decision_date",
        "symbol",
        "side",
        "order_date",
        "execution_date",
        "execution_price",
        "quantity",
        "gross_notional",
        "signed_gross_cash_flow",
        "fees",
        "taxes",
        "slippage",
        "net_cash_flow",
        "status",
        "reason",
    ]


def _position_ledger_columns() -> list[str]:
    return [
        "date",
        "symbol",
        "quantity",
        "average_cost",
        "market_price",
        "market_value",
        "unrealized_pnl",
        "realized_pnl",
        "status",
    ]


def _cash_ledger_columns() -> list[str]:
    return ["date", "starting_cash", "trade_cash_flow", "fees", "taxes", "ending_cash"]


def _equity_curve_columns() -> list[str]:
    return ["date", "cash", "market_value", "total_equity", "daily_return", "drawdown"]


def _trade_id(row: dict[str, Any], side: str) -> str:
    payload = {
        "decision_date": _json_safe(_timestamp_or_nat(row.get("decision_date"))),
        "symbol": str(row.get("symbol", "")),
        "side": side,
        "buy_date": _json_safe(_timestamp_or_nat(row.get("buy_date", row.get("execution_date")))),
        "sell_date": _json_safe(_timestamp_or_nat(row.get("sell_date"))),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _timestamp_or_nat(value: Any) -> pd.Timestamp:
    if value is None:
        return pd.NaT
    try:
        if pd.isna(value):
            return pd.NaT
    except (TypeError, ValueError):
        pass
    return pd.Timestamp(value).normalize()


def _none_if_nan(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _coerce_portfolio_settings(
    settings: PortfolioSimulationSettings | dict[str, Any] | None,
) -> PortfolioSimulationSettings:
    if settings is None:
        return PortfolioSimulationSettings()
    if isinstance(settings, PortfolioSimulationSettings):
        return settings
    if isinstance(settings, dict):
        return PortfolioSimulationSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PortfolioSimulationSettings(**settings.model_dump())
    raise TypeError("settings must be PortfolioSimulationSettings, dict, or None")


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
