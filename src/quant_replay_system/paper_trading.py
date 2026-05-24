"""Manual paper trading journal built from reviewed replay candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import PaperTradingSettings, Settings, load_settings
from quant_replay_system.data import load_market_data, read_csv_preserve_symbol_columns


PAPER_TRADING_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Requires manual review before any paper fill is recorded.",
    "Paper fills are hypothetical manual records, not broker confirmations.",
    "Position accounting is simplified and intended for research review.",
    "Corporate actions, dividends, financing, and exchange fees are not fully modeled.",
]

PAPER_ACTIONS = {"WATCH", "PAPER_BUY", "PAPER_SELL", "HOLD", "SKIP"}
MANUAL_REVIEW_STATUSES = {"PENDING_REVIEW", "APPROVED_FOR_PAPER", "REJECTED", "WATCH_ONLY"}


@dataclass(frozen=True)
class PaperTradeDecision:
    decision_id: str
    decision_date: pd.Timestamp
    symbol: str
    name: str
    action: str
    intended_side: str
    final_score: float | None
    component_scores: dict[str, Any]
    risk_precheck_status: str
    risk_precheck_reason: str
    candidate_rank: int | None
    source_run_id: str
    source_report_path: str
    planned_holding_horizon: int | None
    planned_buy_date: pd.Timestamp | None
    planned_sell_date: pd.Timestamp | None
    manual_review_status: str
    manual_review_notes: str
    created_at: str


@dataclass(frozen=True)
class PaperTradeFill:
    fill_id: str
    decision_id: str
    symbol: str
    side: str
    fill_date: pd.Timestamp
    fill_price: float
    quantity: float
    gross_notional: float
    fees: float
    slippage: float
    net_cash_flow: float
    fill_source: str
    manual_notes: str


@dataclass(frozen=True)
class PaperFillValidationResult:
    valid: bool
    row_count: int
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class PaperPosition:
    symbol: str
    quantity: float
    average_cost: float
    open_date: pd.Timestamp
    last_mark_date: pd.Timestamp
    last_mark_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_return_pct: float
    status: str


@dataclass(frozen=True)
class PaperTradingArtifactPaths:
    artifact_dir: Path
    paper_report: Path
    decisions: Path
    fills: Path
    open_positions: Path
    closed_trades: Path
    daily_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "paper_report": self.paper_report,
            "decisions": self.decisions,
            "fills": self.fills,
            "open_positions": self.open_positions,
            "closed_trades": self.closed_trades,
            "daily_summary": self.daily_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperTradeJournal:
    journal_id: str
    settings: PaperTradingSettings
    decisions: pd.DataFrame
    fills: pd.DataFrame
    open_positions: pd.DataFrame
    closed_trades: pd.DataFrame
    daily_summary: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]
    known_limitations: list[str]


def create_paper_decision_log(
    candidates: pd.DataFrame | str | Path | Any,
    *,
    decision_date: str | pd.Timestamp | None = None,
    source_run_id: str | None = None,
    source_report_path: str | Path | None = None,
    planned_holding_horizon: int | None = None,
    planned_buy_date: str | pd.Timestamp | None = None,
    planned_sell_date: str | pd.Timestamp | None = None,
    manual_review_status: str = "PENDING_REVIEW",
    manual_review_notes: str = "",
) -> pd.DataFrame:
    """Create a deterministic manual paper-trade decision log from selected candidates."""

    if manual_review_status not in MANUAL_REVIEW_STATUSES:
        raise ValueError(f"Unsupported manual_review_status: {manual_review_status}")

    frame = _candidates_to_frame(candidates)
    if frame.empty:
        return _empty_decisions()

    rows = []
    created_at = _deterministic_created_at(decision_date, frame)
    source_id = source_run_id or _first_present(frame, "source_run_id", "run_id", "replay_run_id")
    source_path = str(source_report_path or _first_present(frame, "source_report_path", "report_path"))
    normalized_decision_date = _timestamp_or_nat(decision_date)
    normalized_buy_date = _timestamp_or_nat(planned_buy_date)
    normalized_sell_date = _timestamp_or_nat(planned_sell_date)

    sorted_frame = frame.copy(deep=True)
    if "rank" not in sorted_frame.columns and "candidate_rank" not in sorted_frame.columns:
        sorted_frame["candidate_rank"] = np.arange(1, len(sorted_frame) + 1)
    sorted_frame = sorted_frame.sort_values(
        [column for column in ["rank", "candidate_rank", "final_score", "symbol"] if column in sorted_frame.columns],
        ascending=[True, True, False, True][: len([column for column in ["rank", "candidate_rank", "final_score", "symbol"] if column in sorted_frame.columns])],
        na_position="last",
    )

    for ordinal, row in enumerate(sorted_frame.to_dict("records"), start=1):
        row_decision_date = _timestamp_or_nat(row.get("decision_date", normalized_decision_date))
        buy_date = _timestamp_or_nat(row.get("planned_buy_date", row.get("buy_date", normalized_buy_date)))
        sell_date = _timestamp_or_nat(row.get("planned_sell_date", row.get("sell_date", normalized_sell_date)))
        candidate_rank = _int_or_none(row.get("candidate_rank", row.get("rank", ordinal)))
        action = _paper_action(row)
        intended_side = _intended_side(row, action)
        symbol = str(row.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("Candidate rows must include symbol")
        row_review_status = str(row.get("manual_review_status", manual_review_status))
        if row_review_status not in MANUAL_REVIEW_STATUSES:
            raise ValueError(f"Unsupported manual_review_status: {row_review_status}")
        decision_payload = {
            "decision_date": _json_safe(row_decision_date),
            "symbol": symbol,
            "candidate_rank": candidate_rank,
            "source_run_id": source_id,
            "planned_buy_date": _json_safe(buy_date),
            "planned_sell_date": _json_safe(sell_date),
        }
        rows.append(
            {
                "decision_id": _hash_payload(decision_payload, length=12),
                "decision_date": row_decision_date,
                "symbol": symbol,
                "name": str(row.get("name", "")),
                "action": action,
                "intended_side": intended_side,
                "final_score": _float_or_none(row.get("final_score")),
                "component_scores": _component_scores(row),
                "risk_precheck_status": str(row.get("risk_precheck_status", "")),
                "risk_precheck_reason": str(row.get("risk_precheck_reason", "")),
                "candidate_rank": candidate_rank,
                "source_run_id": source_id,
                "source_report_path": source_path,
                "planned_holding_horizon": _int_or_none(row.get("planned_holding_horizon", planned_holding_horizon)),
                "planned_buy_date": buy_date,
                "planned_sell_date": sell_date,
                "manual_review_status": row_review_status,
                "manual_review_notes": str(row.get("manual_review_notes", manual_review_notes)),
                "created_at": created_at,
            }
        )

    return _finalize_decisions(pd.DataFrame(rows))


def record_paper_fill(
    decisions: pd.DataFrame,
    fills: pd.DataFrame | None = None,
    *,
    decision_id: str,
    symbol: str | None = None,
    side: str,
    fill_date: str | pd.Timestamp,
    fill_price: float,
    quantity: float,
    fees: float | None = None,
    slippage: float | None = None,
    fill_source: str = "MANUAL",
    manual_notes: str = "",
    settings: PaperTradingSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Append one manual hypothetical fill to the paper fill ledger."""

    cfg = _coerce_paper_settings(settings)
    existing = _prepare_fills(fills)
    decision_row = _decision_by_id(decisions, decision_id)
    _assert_decision_can_fill(decision_row, cfg)
    resolved_symbol = str(symbol or decision_row.get("symbol", "")).strip()
    normalized_side = str(side).upper().strip()
    if normalized_side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    if not resolved_symbol:
        raise ValueError("symbol is required")
    decision_symbol = str(decision_row.get("symbol", "")).strip()
    if decision_symbol and resolved_symbol != decision_symbol:
        raise ValueError(f"Fill symbol {resolved_symbol} does not match decision symbol {decision_symbol}")

    normalized_quantity = _normalize_quantity(float(quantity), cfg)
    normalized_price = float(fill_price)
    if normalized_price <= 0:
        raise ValueError("fill_price must be positive")

    gross_notional = normalized_quantity * normalized_price
    fee_value = gross_notional * cfg.default_fee_bps / 10_000.0 if fees is None else float(fees)
    slippage_value = gross_notional * cfg.default_slippage_bps / 10_000.0 if slippage is None else float(slippage)
    net_cash_flow = (
        -(gross_notional + fee_value + slippage_value)
        if normalized_side == "BUY"
        else gross_notional - fee_value - slippage_value
    )
    if normalized_side == "BUY" and cfg.prevent_negative_cash:
        cash_after_fill = _current_paper_cash(existing, cfg) + net_cash_flow
        if cash_after_fill < -1e-9:
            raise ValueError("BUY fill would make paper cash negative")
    if normalized_side == "SELL" and not cfg.allow_short_selling:
        available_quantity = _available_quantity(existing, resolved_symbol)
        if normalized_quantity > available_quantity + 1e-9:
            raise ValueError(
                f"SELL quantity {normalized_quantity:g} exceeds available paper position {available_quantity:g}"
            )
    fill_payload = {
        "decision_id": decision_id,
        "symbol": resolved_symbol,
        "side": normalized_side,
        "fill_date": _json_safe(_timestamp_or_nat(fill_date)),
        "fill_price": normalized_price,
        "quantity": normalized_quantity,
    }
    row = {
        "fill_id": _hash_payload(fill_payload, length=12),
        "decision_id": decision_id,
        "symbol": resolved_symbol,
        "side": normalized_side,
        "fill_date": _timestamp_or_nat(fill_date),
        "fill_price": normalized_price,
        "quantity": normalized_quantity,
        "gross_notional": gross_notional,
        "fees": fee_value,
        "slippage": slippage_value,
        "net_cash_flow": net_cash_flow,
        "fill_source": fill_source,
        "manual_notes": manual_notes,
    }
    if existing.empty:
        combined = _finalize_fills(pd.DataFrame([row]))
    else:
        combined = _finalize_fills(pd.concat([existing, pd.DataFrame([row])], ignore_index=True))
    validation = validate_paper_fills(combined, decisions=decisions, settings=cfg)
    if not validation.valid:
        raise ValueError("; ".join(validation.errors))
    return combined


def build_open_positions(
    fills: pd.DataFrame,
    market_data: pd.DataFrame | None = None,
    *,
    mark_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Build open paper positions from manual hypothetical fills."""

    ledger = _position_state_from_fills(fills)
    rows = []
    normalized_market = _prepare_market_data(market_data)
    default_mark_date = _latest_fill_date(fills)
    effective_mark_date = _timestamp_or_nat(mark_date) if mark_date is not None else default_mark_date

    for symbol, state in sorted(ledger.items()):
        quantity = float(state["quantity"])
        if quantity <= 1e-9:
            continue
        average_cost = float(state["total_cost"]) / quantity
        mark_price = _market_price(symbol, effective_mark_date, normalized_market, fallback=average_cost)
        market_value = quantity * mark_price
        unrealized_pnl = market_value - quantity * average_cost
        cost_basis = quantity * average_cost
        rows.append(
            {
                "symbol": symbol,
                "quantity": quantity,
                "average_cost": average_cost,
                "open_date": state["open_date"],
                "last_mark_date": effective_mark_date,
                "last_mark_price": mark_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_return_pct": unrealized_pnl / cost_basis if cost_basis else 0.0,
                "status": "OPEN",
            }
        )
    return _finalize_open_positions(pd.DataFrame(rows))


def build_closed_trades(
    fills: pd.DataFrame,
    settings: PaperTradingSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build closed paper trades by matching manual sells against prior buys."""

    prepared = _prepare_fills(fills)
    cfg = _coerce_paper_settings(settings)
    lots: dict[str, list[dict[str, Any]]] = {}
    rows = []
    for fill in prepared.sort_values(["fill_date", "fill_id"]).to_dict("records"):
        symbol = str(fill["symbol"])
        quantity = float(fill["quantity"])
        if str(fill["side"]).upper() == "BUY":
            entry_cost_per_share = (abs(float(fill["net_cash_flow"])) / quantity) if quantity else float(fill["fill_price"])
            lots.setdefault(symbol, []).append(
                {
                    "open_date": fill["fill_date"],
                    "entry_price": float(fill["fill_price"]),
                    "entry_cost_per_share": entry_cost_per_share,
                    "remaining_quantity": quantity,
                }
            )
            continue

        remaining = quantity
        exit_proceeds_per_share = (float(fill["net_cash_flow"]) / quantity) if quantity else float(fill["fill_price"])
        for lot in lots.get(symbol, []):
            if remaining <= 1e-9:
                break
            matched = min(float(lot["remaining_quantity"]), remaining)
            if matched <= 0:
                continue
            realized_pnl = (exit_proceeds_per_share - float(lot["entry_cost_per_share"])) * matched
            cost_basis = float(lot["entry_cost_per_share"]) * matched
            holding_calendar_days = max(0, (pd.Timestamp(fill["fill_date"]) - pd.Timestamp(lot["open_date"])).days)
            rows.append(
                {
                    "symbol": symbol,
                    "open_date": lot["open_date"],
                    "close_date": fill["fill_date"],
                    "entry_price": float(lot["entry_price"]),
                    "exit_price": float(fill["fill_price"]),
                    "quantity": matched,
                    "realized_pnl": realized_pnl,
                    "realized_return_pct": realized_pnl / cost_basis if cost_basis else 0.0,
                    "holding_calendar_days": holding_calendar_days,
                    "holding_days": holding_calendar_days,
                    "exit_reason": str(fill.get("manual_notes") or "PAPER_SELL"),
                }
            )
            lot["remaining_quantity"] = float(lot["remaining_quantity"]) - matched
            remaining -= matched
        if remaining > 1e-9 and not cfg.allow_short_selling:
            raise ValueError(f"SELL quantity exceeds available paper position for {symbol}")
    return _finalize_closed_trades(pd.DataFrame(rows))


def mark_to_market_paper_positions(
    open_positions: pd.DataFrame,
    market_data: pd.DataFrame,
    *,
    mark_date: str | pd.Timestamp,
) -> pd.DataFrame:
    """Mark existing open paper positions to market."""

    positions = open_positions.copy(deep=True)
    if positions.empty:
        return _empty_open_positions()
    market = _prepare_market_data(market_data)
    normalized_mark_date = _timestamp_or_nat(mark_date)
    rows = []
    for row in positions.to_dict("records"):
        symbol = str(row["symbol"])
        quantity = float(row["quantity"])
        average_cost = float(row["average_cost"])
        mark_price = _market_price(symbol, normalized_mark_date, market, fallback=float(row.get("last_mark_price", average_cost)))
        market_value = quantity * mark_price
        unrealized_pnl = market_value - quantity * average_cost
        cost_basis = quantity * average_cost
        updated = dict(row)
        updated.update(
            {
                "last_mark_date": normalized_mark_date,
                "last_mark_price": mark_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_return_pct": unrealized_pnl / cost_basis if cost_basis else 0.0,
                "status": "OPEN",
            }
        )
        rows.append(updated)
    return _finalize_open_positions(pd.DataFrame(rows))


def generate_paper_trading_report(
    *,
    decisions: pd.DataFrame,
    fills: pd.DataFrame | None = None,
    market_data: pd.DataFrame | None = None,
    mark_date: str | pd.Timestamp | None = None,
    settings: PaperTradingSettings | dict[str, Any] | None = None,
    config: Settings | str | Path | None = None,
    journal_id: str | None = None,
) -> PaperTradeJournal:
    """Generate a structured manual paper trading journal and optional artifacts."""

    project_settings = _load_project_settings(config)
    paper_settings = _coerce_paper_settings(settings or project_settings.paper_trading)
    if paper_settings.enable_live_trading or paper_settings.enable_broker_api:
        raise ValueError("Manual paper trading cannot enable live trading or broker API access")

    prepared_decisions = _finalize_decisions(decisions)
    prepared_fills = _prepare_fills(fills)
    fill_validation = validate_paper_fills(prepared_fills, decisions=prepared_decisions, settings=paper_settings)
    if not fill_validation.valid:
        raise ValueError("; ".join(fill_validation.errors))
    market = (
        _prepare_market_data(market_data)
        if market_data is not None
        else _prepare_market_data(load_market_data(project_settings.data.mock_prices))
    )
    effective_mark_date = _timestamp_or_nat(mark_date) if mark_date is not None else _latest_date(prepared_decisions, prepared_fills)
    open_positions = build_open_positions(prepared_fills, market, mark_date=effective_mark_date)
    closed_trades = build_closed_trades(prepared_fills, settings=paper_settings)
    daily_summary = build_daily_summary(
        open_positions=open_positions,
        closed_trades=closed_trades,
        fills=prepared_fills,
        settings=paper_settings,
        mark_date=effective_mark_date,
    )
    effective_journal_id = journal_id or generate_paper_journal_id(
        decisions=prepared_decisions,
        fills=prepared_fills,
        settings=paper_settings,
    )
    paths = resolve_paper_trading_artifact_paths(paper_settings.output_dir, effective_journal_id)
    warnings = _paper_warnings(prepared_decisions, prepared_fills, paper_settings)
    audit_metadata = {
        "journal_id": effective_journal_id,
        "decision_rows": len(prepared_decisions),
        "fill_rows": len(prepared_fills),
        "open_position_rows": len(open_positions),
        "closed_trade_rows": len(closed_trades),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    journal = PaperTradeJournal(
        journal_id=effective_journal_id,
        settings=paper_settings,
        decisions=prepared_decisions,
        fills=prepared_fills,
        open_positions=open_positions,
        closed_trades=closed_trades,
        daily_summary=daily_summary,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        audit_metadata=audit_metadata,
        known_limitations=PAPER_TRADING_LIMITATIONS,
    )
    if paper_settings.write_artifacts:
        write_paper_trading_artifacts(journal)
    return journal


def build_daily_summary(
    *,
    open_positions: pd.DataFrame,
    closed_trades: pd.DataFrame,
    fills: pd.DataFrame,
    settings: PaperTradingSettings,
    mark_date: str | pd.Timestamp | None,
) -> pd.DataFrame:
    """Build one-row daily paper trading performance summary."""

    prepared_fills = _prepare_fills(fills)
    normalized_mark_date = _timestamp_or_nat(mark_date)
    paper_cash = float(settings.initial_paper_cash)
    if not prepared_fills.empty:
        paper_cash += float(prepared_fills["net_cash_flow"].sum())
    total_market_value = 0.0 if open_positions.empty else float(open_positions["market_value"].sum())
    unrealized = 0.0 if open_positions.empty else float(open_positions["unrealized_pnl"].sum())
    realized = 0.0 if closed_trades.empty else float(closed_trades["realized_pnl"].sum())
    total_equity = paper_cash + total_market_value
    win_rate = None
    if not closed_trades.empty:
        win_rate = float((pd.to_numeric(closed_trades["realized_pnl"], errors="coerce") > 0).mean())
    exposure = total_market_value / total_equity if total_equity else 0.0
    warnings = []
    if paper_cash < -1e-9:
        warnings.append("NEGATIVE_PAPER_CASH")
    return pd.DataFrame(
        [
            {
                "date": normalized_mark_date,
                "paper_cash": paper_cash,
                "open_position_count": 0 if open_positions.empty else int(len(open_positions)),
                "closed_trade_count": 0 if closed_trades.empty else int(len(closed_trades)),
                "total_market_value": total_market_value,
                "total_equity": total_equity,
                "daily_unrealized_pnl": unrealized,
                "realized_pnl": realized,
                "total_pnl": unrealized + realized,
                "win_rate_closed_trades": win_rate,
                "exposure_pct": exposure,
                "warnings": ";".join(warnings),
            }
        ]
    )


def validate_paper_fills(
    fills: pd.DataFrame,
    decisions: pd.DataFrame | None = None,
    settings: PaperTradingSettings | dict[str, Any] | None = None,
) -> PaperFillValidationResult:
    """Validate manual hypothetical paper fills against accounting guardrails."""

    cfg = _coerce_paper_settings(settings)
    errors: list[str] = []
    warnings: list[str] = []
    if fills is None:
        fills = _empty_fills()
    missing = [column for column in _fill_columns() if column not in fills.columns]
    if missing:
        return PaperFillValidationResult(
            valid=False,
            row_count=0 if fills is None else len(fills),
            errors=[f"Missing required fill columns: {', '.join(missing)}"],
            warnings=[],
        )

    prepared = _prepare_fills(fills)
    if prepared.empty:
        return PaperFillValidationResult(valid=True, row_count=0, errors=[], warnings=["No paper fills to validate."])

    sides = prepared["side"].astype(str).str.upper().str.strip()
    invalid_sides = prepared.loc[~sides.isin({"BUY", "SELL"})]
    if not invalid_sides.empty:
        errors.append(f"Invalid side values at rows: {_row_numbers(invalid_sides.index)}")

    quantity = pd.to_numeric(prepared["quantity"], errors="coerce")
    invalid_quantity = prepared.loc[quantity.isna() | (quantity <= 0)]
    if not invalid_quantity.empty:
        errors.append(f"Non-positive quantity at rows: {_row_numbers(invalid_quantity.index)}")

    fill_price = pd.to_numeric(prepared["fill_price"], errors="coerce")
    invalid_price = prepared.loc[fill_price.isna() | (fill_price <= 0)]
    if not invalid_price.empty:
        errors.append(f"Non-positive fill_price at rows: {_row_numbers(invalid_price.index)}")

    gross_notional = pd.to_numeric(prepared["gross_notional"], errors="coerce")
    expected_gross = quantity * fill_price
    gross_mismatch = prepared.loc[
        gross_notional.isna() | ((gross_notional - expected_gross).abs() > np.maximum(0.01, expected_gross.abs() * 0.0001))
    ]
    if not gross_mismatch.empty:
        errors.append(f"Mismatched gross_notional at rows: {_row_numbers(gross_mismatch.index)}")

    net_cash_flow = pd.to_numeric(prepared["net_cash_flow"], errors="coerce")
    buy_wrong_sign = prepared.loc[(sides == "BUY") & (net_cash_flow >= 0)]
    sell_wrong_sign = prepared.loc[(sides == "SELL") & (net_cash_flow <= 0)]
    if not buy_wrong_sign.empty:
        errors.append(f"BUY net_cash_flow must be negative at rows: {_row_numbers(buy_wrong_sign.index)}")
    if not sell_wrong_sign.empty:
        errors.append(f"SELL net_cash_flow must be positive at rows: {_row_numbers(sell_wrong_sign.index)}")

    if decisions is not None:
        decision_frame = _finalize_decisions(decisions)
        decision_ids = set(str(value) for value in decision_frame["decision_id"].dropna())
        decision_by_id = {
            str(row["decision_id"]): row
            for row in decision_frame.to_dict("records")
            if row.get("decision_id") is not None and not pd.isna(row.get("decision_id"))
        }
        missing_decisions = prepared.loc[~prepared["decision_id"].astype(str).isin(decision_ids)]
        if not missing_decisions.empty:
            errors.append(f"Unknown decision_id at rows: {_row_numbers(missing_decisions.index)}")
        for idx, fill in prepared.to_dict("index").items():
            decision = decision_by_id.get(str(fill.get("decision_id")))
            if decision is None:
                continue
            decision_symbol = str(decision.get("symbol", "")).strip()
            if decision_symbol and str(fill.get("symbol", "")).strip() != decision_symbol:
                errors.append(f"Fill symbol does not match decision symbol at row: {idx + 2}")
            status = str(decision.get("manual_review_status", "")).strip()
            if cfg.require_approved_decision_for_fills and status != "APPROVED_FOR_PAPER":
                errors.append(f"Fill decision is not APPROVED_FOR_PAPER at row: {idx + 2}")

    if not cfg.allow_short_selling:
        oversell_errors = _oversell_errors(prepared)
        errors.extend(oversell_errors)

    if cfg.prevent_negative_cash:
        cash_errors = _negative_cash_errors(prepared, cfg)
        errors.extend(cash_errors)

    return PaperFillValidationResult(valid=not errors, row_count=len(prepared), errors=errors, warnings=warnings)


def generate_paper_journal_id(
    *,
    decisions: pd.DataFrame,
    fills: pd.DataFrame | None = None,
    settings: PaperTradingSettings | dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic paper journal id independent of fill activity."""

    cfg = _coerce_paper_settings(settings)
    decision_frame = _finalize_decisions(decisions)
    payload = {
        "decision_dates": _unique_dates(decision_frame, "decision_date"),
        "source_run_ids": sorted(str(value) for value in decision_frame.get("source_run_id", pd.Series(dtype="object")).dropna().unique()),
        "symbols": sorted(str(value) for value in decision_frame.get("symbol", pd.Series(dtype="object")).dropna().unique()),
        "config_version": cfg.config_version,
    }
    return _hash_payload(payload, length=10)


def resolve_paper_trading_artifact_paths(output_dir: str | Path, journal_id: str) -> PaperTradingArtifactPaths:
    """Resolve stable artifact paths for one paper trading journal."""

    artifact_dir = Path(output_dir) / journal_id
    return PaperTradingArtifactPaths(
        artifact_dir=artifact_dir,
        paper_report=artifact_dir / "paper_report.md",
        decisions=artifact_dir / "decisions.csv",
        fills=artifact_dir / "fills.csv",
        open_positions=artifact_dir / "open_positions.csv",
        closed_trades=artifact_dir / "closed_trades.csv",
        daily_summary=artifact_dir / "daily_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_paper_trading_artifacts(journal: PaperTradeJournal) -> Path:
    """Write paper trading markdown, CSV, and metadata artifacts."""

    paths = PaperTradingArtifactPaths(**journal.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(journal.decisions, paths.decisions)
    _export_dataframe(journal.fills, paths.fills)
    _export_dataframe(journal.open_positions, paths.open_positions)
    _export_dataframe(journal.closed_trades, paths.closed_trades)
    _export_dataframe(journal.daily_summary, paths.daily_summary)
    metadata = build_paper_trading_metadata(journal, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.paper_report.write_text(render_paper_trading_report(journal, paths, metadata), encoding="utf-8")
    return paths.paper_report


def build_paper_trading_metadata(journal: PaperTradeJournal, paths: PaperTradingArtifactPaths) -> dict[str, Any]:
    """Build metadata for a manual paper trading journal."""

    return {
        "journal_id": journal.journal_id,
        "created_at": _metadata_created_at(journal.decisions),
        "config_summary": {
            "initial_paper_cash": journal.settings.initial_paper_cash,
            "default_lot_size": journal.settings.default_lot_size,
            "round_lots": journal.settings.round_lots,
            "allow_fractional_shares": journal.settings.allow_fractional_shares,
            "default_fee_bps": journal.settings.default_fee_bps,
            "default_slippage_bps": journal.settings.default_slippage_bps,
            "enable_live_trading": False,
            "enable_broker_api": False,
        },
        "row_counts": {
            "decisions": len(journal.decisions),
            "fills": len(journal.fills),
            "open_positions": len(journal.open_positions),
            "closed_trades": len(journal.closed_trades),
            "daily_summary": len(journal.daily_summary),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": journal.warnings,
        "known_limitations": journal.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_paper_trading_report(
    journal: PaperTradeJournal,
    paths: PaperTradingArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render the manual paper trading markdown report."""

    lines = [
        f"# Manual Paper Trading Journal: {journal.journal_id}",
        "",
        "No broker or live trading integration was invoked. This report records manual hypothetical paper trades only.",
        "",
        "## Journal Metadata",
        "",
        _dict_table(
            {
                "journal_id": journal.journal_id,
                "artifact_dir": paths.artifact_dir,
                "decision_rows": len(journal.decisions),
                "fill_rows": len(journal.fills),
            }
        ),
        "",
        "## Candidate Decisions",
        "",
        _markdown_table(
            journal.decisions,
            [
                "decision_id",
                "decision_date",
                "candidate_rank",
                "symbol",
                "name",
                "action",
                "intended_side",
                "final_score",
                "risk_precheck_status",
                "manual_review_status",
            ],
        ),
        "",
        "## Manual Review Summary",
        "",
        _manual_review_summary(journal.decisions),
        "",
        "## Paper Fills",
        "",
        _markdown_table(
            journal.fills,
            ["fill_id", "decision_id", "symbol", "side", "fill_date", "fill_price", "quantity", "net_cash_flow", "fill_source"],
        ),
        "",
        "## Open Positions",
        "",
        _markdown_table(
            journal.open_positions,
            [
                "symbol",
                "quantity",
                "average_cost",
                "last_mark_date",
                "last_mark_price",
                "market_value",
                "unrealized_pnl",
                "unrealized_return_pct",
                "status",
            ],
        ),
        "",
        "## Closed Trades",
        "",
        _markdown_table(
            journal.closed_trades,
            ["symbol", "open_date", "close_date", "entry_price", "exit_price", "quantity", "realized_pnl", "realized_return_pct"],
        ),
        "",
        "## Daily Performance Summary",
        "",
        _markdown_table(
            journal.daily_summary,
            [
                "date",
                "paper_cash",
                "open_position_count",
                "closed_trade_count",
                "total_market_value",
                "total_equity",
                "total_pnl",
                "exposure_pct",
                "warnings",
            ],
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(journal.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in metadata["known_limitations"]),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _position_state_from_fills(fills: pd.DataFrame) -> dict[str, dict[str, Any]]:
    prepared = _prepare_fills(fills)
    remaining_lots = _fifo_remaining_lots(prepared)
    states: dict[str, dict[str, Any]] = {}
    for symbol, lots in remaining_lots.items():
        active_lots = [lot for lot in lots if float(lot["remaining_quantity"]) > 1e-9]
        if not active_lots:
            continue
        quantity = sum(float(lot["remaining_quantity"]) for lot in active_lots)
        total_cost = sum(float(lot["remaining_quantity"]) * float(lot["entry_cost_per_share"]) for lot in active_lots)
        states[symbol] = {
            "quantity": quantity,
            "total_cost": total_cost,
            "open_date": min(pd.Timestamp(lot["open_date"]) for lot in active_lots),
        }
    return states


def _fifo_remaining_lots(fills: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    lots: dict[str, list[dict[str, Any]]] = {}
    for fill in _prepare_fills(fills).sort_values(["fill_date", "fill_id"]).to_dict("records"):
        symbol = str(fill["symbol"])
        quantity = float(fill["quantity"])
        if str(fill["side"]).upper() == "BUY":
            entry_cost_per_share = abs(float(fill["net_cash_flow"])) / quantity if quantity else float(fill["fill_price"])
            lots.setdefault(symbol, []).append(
                {
                    "open_date": fill["fill_date"],
                    "entry_price": float(fill["fill_price"]),
                    "entry_cost_per_share": entry_cost_per_share,
                    "remaining_quantity": quantity,
                }
            )
            continue

        remaining = quantity
        for lot in lots.get(symbol, []):
            if remaining <= 1e-9:
                break
            matched = min(float(lot["remaining_quantity"]), remaining)
            lot["remaining_quantity"] = float(lot["remaining_quantity"]) - matched
            remaining -= matched
    return lots


def _available_quantity(fills: pd.DataFrame, symbol: str) -> float:
    lots = _fifo_remaining_lots(fills).get(str(symbol), [])
    return float(sum(float(lot["remaining_quantity"]) for lot in lots))


def _current_paper_cash(fills: pd.DataFrame, settings: PaperTradingSettings) -> float:
    prepared = _prepare_fills(fills)
    if prepared.empty:
        return float(settings.initial_paper_cash)
    return float(settings.initial_paper_cash) + float(pd.to_numeric(prepared["net_cash_flow"], errors="coerce").fillna(0.0).sum())


def _assert_decision_can_fill(decision_row: dict[str, Any], settings: PaperTradingSettings) -> None:
    if not settings.require_approved_decision_for_fills:
        return
    status = str(decision_row.get("manual_review_status", "")).strip()
    if status != "APPROVED_FOR_PAPER":
        raise ValueError("Paper fills require manual_review_status == APPROVED_FOR_PAPER")


def _oversell_errors(fills: pd.DataFrame) -> list[str]:
    errors = []
    positions: dict[str, float] = {}
    for idx, fill in _prepare_fills(fills).sort_values(["fill_date", "fill_id"]).to_dict("index").items():
        symbol = str(fill["symbol"])
        side = str(fill["side"]).upper()
        quantity = float(fill["quantity"])
        if side == "BUY":
            positions[symbol] = positions.get(symbol, 0.0) + quantity
            continue
        if side != "SELL":
            continue
        available = positions.get(symbol, 0.0)
        if quantity > available + 1e-9:
            errors.append(
                f"SELL quantity {quantity:g} exceeds available paper position {available:g} at row: {idx + 2}"
            )
            positions[symbol] = available
        else:
            positions[symbol] = available - quantity
    return errors


def _negative_cash_errors(fills: pd.DataFrame, settings: PaperTradingSettings) -> list[str]:
    errors = []
    cash = float(settings.initial_paper_cash)
    for idx, fill in _prepare_fills(fills).sort_values(["fill_date", "fill_id"]).to_dict("index").items():
        cash += float(fill["net_cash_flow"])
        if cash < -1e-9:
            errors.append(f"Paper cash would become negative at row: {idx + 2}")
    return errors


def _candidates_to_frame(candidates: pd.DataFrame | str | Path | Any) -> pd.DataFrame:
    if isinstance(candidates, pd.DataFrame):
        return candidates.copy(deep=True)
    if isinstance(candidates, (str, Path)):
        return read_csv_preserve_symbol_columns(candidates)
    for attr in ["selected_candidates", "candidates", "candidate_df"]:
        if hasattr(candidates, attr):
            value = getattr(candidates, attr)
            if isinstance(value, pd.DataFrame):
                return value.copy(deep=True)
    raise TypeError("candidates must be a DataFrame, CSV path, or object with selected_candidates/candidates")


def _paper_action(row: dict[str, Any]) -> str:
    value = str(row.get("paper_action", row.get("action", "WATCH"))).upper()
    if value in PAPER_ACTIONS:
        return value
    if value in {"PAPER_TRADE", "LIVE_CANDIDATE_SMALL", "STRONG_CANDIDATE_REVIEW_REQUIRED"}:
        return "PAPER_BUY"
    if value == "OBSERVE":
        return "WATCH"
    if value in {"NO_TRADE", "BLOCKED"}:
        return "SKIP"
    return "WATCH"


def _intended_side(row: dict[str, Any], action: str) -> str:
    value = str(row.get("intended_side", "")).upper().strip()
    if value in {"BUY", "SELL"}:
        return value
    if action == "PAPER_SELL":
        return "SELL"
    if action == "SKIP":
        return ""
    return "BUY"


def _component_scores(row: dict[str, Any]) -> dict[str, Any]:
    if isinstance(row.get("component_scores"), dict):
        return dict(row["component_scores"])
    keys = [
        "technical_score",
        "liquidity_score",
        "expectation_score",
        "reality_score",
        "sentiment_score",
        "risk_penalty",
    ]
    return {key: _float_or_none(row.get(key)) for key in keys if key in row and _float_or_none(row.get(key)) is not None}


def _decision_by_id(decisions: pd.DataFrame, decision_id: str) -> dict[str, Any]:
    frame = _finalize_decisions(decisions)
    rows = frame.loc[frame["decision_id"] == decision_id]
    if rows.empty:
        raise ValueError(f"Unknown decision_id: {decision_id}")
    return rows.iloc[0].to_dict()


def _normalize_quantity(quantity: float, settings: PaperTradingSettings) -> float:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if not settings.allow_fractional_shares and not float(quantity).is_integer():
        raise ValueError("fractional shares are disabled by default")
    if settings.allow_fractional_shares:
        return float(quantity)
    whole_quantity = float(int(quantity))
    if settings.round_lots:
        whole_quantity = float(np.floor(whole_quantity / settings.default_lot_size) * settings.default_lot_size)
    if whole_quantity <= 0:
        raise ValueError("quantity becomes zero after lot-size rounding")
    return whole_quantity


def _prepare_fills(fills: pd.DataFrame | None) -> pd.DataFrame:
    if fills is None or fills.empty:
        return _empty_fills()
    frame = fills.copy(deep=True)
    for column in ["fill_date"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.normalize()
    for column in ["fill_price", "quantity", "gross_notional", "fees", "slippage", "net_cash_flow"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return _finalize_fills(frame)


def _prepare_market_data(market_data: pd.DataFrame | None) -> pd.DataFrame:
    if market_data is None:
        return pd.DataFrame()
    market = market_data.copy(deep=True)
    if market.empty:
        return market
    if "trade_date" in market.columns:
        market["trade_date"] = pd.to_datetime(market["trade_date"], errors="coerce").dt.normalize()
    for column in ["close", "open"]:
        if column in market.columns:
            market[column] = pd.to_numeric(market[column], errors="coerce")
    return market.sort_values([column for column in ["symbol", "trade_date"] if column in market.columns]).reset_index(drop=True)


def _market_price(symbol: str, date: pd.Timestamp, market_data: pd.DataFrame, *, fallback: float) -> float:
    if market_data.empty or "trade_date" not in market_data.columns:
        return fallback
    price_column = "close" if "close" in market_data.columns else "open" if "open" in market_data.columns else None
    if price_column is None:
        return fallback
    rows = market_data.loc[(market_data["symbol"] == symbol) & (market_data["trade_date"] <= date)].dropna(subset=[price_column])
    if rows.empty:
        return fallback
    return float(rows.sort_values("trade_date").iloc[-1][price_column])


def _paper_warnings(decisions: pd.DataFrame, fills: pd.DataFrame, settings: PaperTradingSettings) -> list[str]:
    warnings = []
    pending = int((decisions["manual_review_status"] == "PENDING_REVIEW").sum()) if not decisions.empty else 0
    if pending:
        warnings.append(f"{pending} decision(s) still pending manual review.")
    if fills.empty:
        warnings.append("No manual hypothetical fills recorded.")
    if settings.enable_live_trading or settings.enable_broker_api:
        warnings.append("Invalid live/broker setting detected.")
    return warnings


def _manual_review_summary(decisions: pd.DataFrame) -> str:
    if decisions.empty:
        return "_No decisions._"
    counts = decisions["manual_review_status"].value_counts().rename_axis("manual_review_status").reset_index(name="count")
    return _markdown_table(counts, ["manual_review_status", "count"])


def _finalize_decisions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty_decisions()
    decisions = frame.copy(deep=True)
    for column in ["decision_date", "planned_buy_date", "planned_sell_date"]:
        if column in decisions.columns:
            decisions[column] = pd.to_datetime(decisions[column], errors="coerce").dt.normalize()
    for column in _decision_columns():
        if column not in decisions.columns:
            decisions[column] = pd.NA
    return decisions[_decision_columns()].sort_values(["decision_date", "candidate_rank", "symbol"], na_position="last").reset_index(drop=True)


def _finalize_fills(frame: pd.DataFrame) -> pd.DataFrame:
    fills = frame.copy(deep=True)
    for column in _fill_columns():
        if column not in fills.columns:
            fills[column] = pd.NA
    if fills.empty:
        return fills[_fill_columns()]
    return fills[_fill_columns()].sort_values(["fill_date", "symbol", "side", "fill_id"], na_position="last").reset_index(drop=True)


def _finalize_open_positions(frame: pd.DataFrame) -> pd.DataFrame:
    positions = frame.copy(deep=True)
    for column in _open_position_columns():
        if column not in positions.columns:
            positions[column] = pd.NA
    if positions.empty:
        return positions[_open_position_columns()]
    return positions[_open_position_columns()].sort_values(["symbol"]).reset_index(drop=True)


def _finalize_closed_trades(frame: pd.DataFrame) -> pd.DataFrame:
    closed = frame.copy(deep=True)
    for column in _closed_trade_columns():
        if column not in closed.columns:
            closed[column] = pd.NA
    if closed.empty:
        return closed[_closed_trade_columns()]
    return closed[_closed_trade_columns()].sort_values(["close_date", "symbol"]).reset_index(drop=True)


def _empty_decisions() -> pd.DataFrame:
    return pd.DataFrame(columns=_decision_columns())


def _empty_fills() -> pd.DataFrame:
    return pd.DataFrame(columns=_fill_columns())


def _empty_open_positions() -> pd.DataFrame:
    return pd.DataFrame(columns=_open_position_columns())


def _decision_columns() -> list[str]:
    return [
        "decision_id",
        "decision_date",
        "symbol",
        "name",
        "action",
        "intended_side",
        "final_score",
        "component_scores",
        "risk_precheck_status",
        "risk_precheck_reason",
        "candidate_rank",
        "source_run_id",
        "source_report_path",
        "planned_holding_horizon",
        "planned_buy_date",
        "planned_sell_date",
        "manual_review_status",
        "manual_review_notes",
        "created_at",
    ]


def _fill_columns() -> list[str]:
    return [
        "fill_id",
        "decision_id",
        "symbol",
        "side",
        "fill_date",
        "fill_price",
        "quantity",
        "gross_notional",
        "fees",
        "slippage",
        "net_cash_flow",
        "fill_source",
        "manual_notes",
    ]


def _open_position_columns() -> list[str]:
    return [
        "symbol",
        "quantity",
        "average_cost",
        "open_date",
        "last_mark_date",
        "last_mark_price",
        "market_value",
        "unrealized_pnl",
        "unrealized_return_pct",
        "status",
    ]


def _closed_trade_columns() -> list[str]:
    return [
        "symbol",
        "open_date",
        "close_date",
        "entry_price",
        "exit_price",
        "quantity",
        "realized_pnl",
        "realized_return_pct",
        "holding_calendar_days",
        "holding_days",
        "exit_reason",
    ]


def _unique_dates(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns or frame.empty:
        return []
    values = pd.to_datetime(frame[column], errors="coerce").dropna().dt.normalize().unique()
    return sorted(str(pd.Timestamp(value).date()) for value in values)


def _latest_date(decisions: pd.DataFrame, fills: pd.DataFrame) -> pd.Timestamp:
    values = []
    for frame, column in [(fills, "fill_date"), (decisions, "decision_date")]:
        if not frame.empty and column in frame.columns:
            values.extend(pd.to_datetime(frame[column], errors="coerce").dropna().dt.normalize().tolist())
    if not values:
        return pd.NaT
    return max(pd.Timestamp(value).normalize() for value in values)


def _latest_fill_date(fills: pd.DataFrame) -> pd.Timestamp:
    prepared = _prepare_fills(fills)
    if prepared.empty:
        return pd.NaT
    dates = pd.to_datetime(prepared["fill_date"], errors="coerce").dropna().dt.normalize()
    return pd.Timestamp(dates.max()).normalize() if not dates.empty else pd.NaT


def _first_present(frame: pd.DataFrame, *columns: str) -> str:
    for column in columns:
        if column in frame.columns:
            values = frame[column].dropna()
            if not values.empty:
                return str(values.iloc[0])
    return ""


def _deterministic_created_at(decision_date: str | pd.Timestamp | None, frame: pd.DataFrame) -> str:
    timestamp = _timestamp_or_nat(decision_date)
    if pd.isna(timestamp) and "decision_date" in frame.columns:
        dates = pd.to_datetime(frame["decision_date"], errors="coerce").dropna().dt.normalize()
        if not dates.empty:
            timestamp = pd.Timestamp(dates.min()).normalize()
    if pd.isna(timestamp):
        return "1970-01-01T00:00:00+00:00"
    return pd.Timestamp(timestamp).isoformat()


def _metadata_created_at(decisions: pd.DataFrame) -> str:
    if not decisions.empty and "created_at" in decisions.columns:
        value = decisions["created_at"].dropna()
        if not value.empty:
            return str(value.iloc[0])
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_or_nat(value: Any) -> pd.Timestamp:
    if value is None:
        return pd.NaT
    try:
        if pd.isna(value):
            return pd.NaT
    except (TypeError, ValueError):
        pass
    return pd.Timestamp(value).normalize()


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return int(value)


def _row_numbers(index: pd.Index) -> str:
    return ", ".join(str(int(value) + 2) for value in index)


def _coerce_paper_settings(settings: PaperTradingSettings | dict[str, Any] | None) -> PaperTradingSettings:
    if settings is None:
        return PaperTradingSettings()
    if isinstance(settings, PaperTradingSettings):
        return settings
    if isinstance(settings, dict):
        return PaperTradingSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperTradingSettings(**settings.model_dump())
    raise TypeError("settings must be PaperTradingSettings, dict, or None")


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


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
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
