"""Auditable replay run orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.calendar import TradingCalendar, load_trading_calendar
from quant_replay_system.candidate_selection import select_candidates
from quant_replay_system.config import CandidateSelectionSettings, ExecutionSettings, Settings, load_settings
from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot
from quant_replay_system.execution import simulate_t_plus_1_execution
from quant_replay_system.factor_dataset import build_factor_dataset
from quant_replay_system.report_generation import (
    generate_replay_run_id,
    resolve_replay_artifact_paths,
    write_replay_artifacts,
)
from quant_replay_system.score_engine import score_factor_dataset


@dataclass(frozen=True)
class ReplayRunResult:
    decision_date: pd.Timestamp
    decision_time: pd.Timestamp
    universe_name: str
    top_n: int
    holding_horizon: int
    run_id: str
    factor_dataset_row_count: int
    scored_dataset_row_count: int
    selected_candidates: pd.DataFrame
    simulated_trades: pd.DataFrame
    performance_summary: dict[str, Any]
    report_path: Path
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]
    config_summary: dict[str, Any]
    factor_dataset: pd.DataFrame
    scored_dataset: pd.DataFrame


def run_replay(
    decision_date: str | pd.Timestamp,
    universe_name: str = "default",
    top_n: int | None = None,
    holding_horizon: int | None = None,
    config: Settings | str | Path | None = None,
    market_data: pd.DataFrame | None = None,
    universe_snapshot: pd.DataFrame | None = None,
    benchmark_data: pd.DataFrame | None = None,
    corporate_actions: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    report_output_path: str | Path | None = None,
    run_id: str | None = None,
) -> ReplayRunResult:
    """Run one end-to-end historical replay for a decision date."""

    settings = _load_run_settings(config)
    as_of_date = pd.Timestamp(decision_date).normalize()
    effective_top_n = top_n if top_n is not None else settings.replay_run.default_top_n
    effective_horizon = holding_horizon if holding_horizon is not None else settings.replay_run.default_holding_horizon
    effective_run_id = run_id or generate_replay_run_id(
        decision_date=as_of_date,
        universe_name=universe_name,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        config_version=settings.replay_run.config_version,
    )

    market = market_data.copy(deep=True) if market_data is not None else load_market_data(settings.data.mock_prices)
    universe = (
        universe_snapshot.copy(deep=True)
        if universe_snapshot is not None
        else load_universe_snapshot(settings.data.mock_universe_snapshots)
    )
    calendar = trading_calendar if trading_calendar is not None else load_trading_calendar(settings.data.mock_trading_calendar)
    if corporate_actions is None and settings.data.mock_corporate_actions.exists():
        corporate_actions = load_corporate_actions(settings.data.mock_corporate_actions)

    decision_time = calendar.decision_time_for(as_of_date)
    warnings: list[str] = []

    factor_dataset = build_factor_dataset(
        decision_date=as_of_date,
        market_data=market,
        universe_snapshot=universe,
        trading_calendar=calendar,
        benchmark_data=benchmark_data,
        config=settings.factor_dataset,
    )
    scored_dataset = score_factor_dataset(factor_dataset, settings.score_engine)

    selection_config = CandidateSelectionSettings(
        top_n=effective_top_n,
        min_action=settings.replay_run.min_action,
        min_final_score=settings.replay_run.min_final_score,
        exclude_blocked=settings.candidate_selection.exclude_blocked,
    )
    selected_candidates = select_candidates(scored_dataset, config=selection_config)
    selected_candidates = _prepare_candidate_output(selected_candidates)
    if selected_candidates.empty:
        warnings.append("No candidates passed selection filters.")

    execution_settings = _execution_settings_with_horizon(settings.execution, effective_horizon)
    simulated_trades = simulate_t_plus_1_execution(
        selected_candidates,
        market,
        as_of_date,
        execution_settings,
        calendar=calendar,
    )
    simulated_trades = _prepare_trade_output(simulated_trades)

    skipped = simulated_trades.loc[simulated_trades.get("trade_status", pd.Series(dtype="object")) == "SKIPPED_BUY"]
    if not skipped.empty:
        warnings.append(f"{len(skipped)} buy(s) skipped by execution eligibility.")

    exit_blocked = simulated_trades.loc[simulated_trades.get("trade_status", pd.Series(dtype="object")) == "EXIT_BLOCKED"]
    if not exit_blocked.empty:
        warnings.append(f"{len(exit_blocked)} exit(s) remained blocked after max delay.")

    performance_summary = _performance_summary(
        selected_candidates=selected_candidates,
        simulated_trades=simulated_trades,
        benchmark_data=benchmark_data,
    )
    if benchmark_data is None:
        warnings.append("No benchmark data supplied; benchmark and excess return are not computed.")

    audit_metadata = _audit_metadata(
        as_of_date=as_of_date,
        decision_time=decision_time,
        universe_name=universe_name,
        holding_horizon=effective_horizon,
        factor_dataset=factor_dataset,
        scored_dataset=scored_dataset,
        selected_candidates=selected_candidates,
        simulated_trades=simulated_trades,
        corporate_actions=corporate_actions,
    )
    config_summary = _config_summary(
        settings=settings,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        run_id=effective_run_id,
    )

    artifact_paths = resolve_replay_artifact_paths(
        output_dir=settings.replay_run.output_dir,
        decision_date=as_of_date,
        universe_name=universe_name,
        run_id=effective_run_id,
        report_output_path=report_output_path,
    )
    result = ReplayRunResult(
        decision_date=as_of_date,
        decision_time=decision_time,
        universe_name=universe_name,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        run_id=effective_run_id,
        factor_dataset_row_count=len(factor_dataset),
        scored_dataset_row_count=len(scored_dataset),
        selected_candidates=selected_candidates,
        simulated_trades=simulated_trades,
        performance_summary=performance_summary,
        report_path=artifact_paths.report,
        artifact_paths=artifact_paths.as_dict(),
        warnings=warnings,
        audit_metadata=audit_metadata,
        config_summary=config_summary,
        factor_dataset=factor_dataset,
        scored_dataset=scored_dataset,
    )
    if settings.replay_run.write_artifacts:
        write_replay_artifacts(result)
    return result


def write_replay_report(result: ReplayRunResult, path: str | Path | None = None) -> Path:
    """Write a markdown report for a replay run."""

    if path is None:
        write_replay_artifacts(result)
        return result.report_path

    replacement_paths = dict(result.artifact_paths)
    replacement_paths["report"] = Path(path)
    replacement_paths["artifact_dir"] = Path(path).parent
    patched = ReplayRunResult(
        decision_date=result.decision_date,
        decision_time=result.decision_time,
        universe_name=result.universe_name,
        top_n=result.top_n,
        holding_horizon=result.holding_horizon,
        run_id=result.run_id,
        factor_dataset_row_count=result.factor_dataset_row_count,
        scored_dataset_row_count=result.scored_dataset_row_count,
        selected_candidates=result.selected_candidates,
        simulated_trades=result.simulated_trades,
        performance_summary=result.performance_summary,
        report_path=Path(path),
        artifact_paths=replacement_paths,
        warnings=result.warnings,
        audit_metadata=result.audit_metadata,
        config_summary=result.config_summary,
        factor_dataset=result.factor_dataset,
        scored_dataset=result.scored_dataset,
    )
    write_replay_artifacts(patched)
    return Path(path)


def _prepare_candidate_output(selected: pd.DataFrame) -> pd.DataFrame:
    frame = selected.copy(deep=True)
    if frame.empty:
        return frame
    if "action" not in frame.columns and "score_action" in frame.columns:
        frame["action"] = frame["score_action"]
    return frame


def _prepare_trade_output(trades: pd.DataFrame) -> pd.DataFrame:
    frame = trades.copy(deep=True)
    for column in ["buy_price", "sell_price"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "trade_return" not in frame.columns:
        frame["trade_return"] = pd.NA
    if {"buy_price", "sell_price", "trade_status"}.issubset(frame.columns):
        filled = (frame["trade_status"] == "FILLED") & frame["buy_price"].notna() & frame["sell_price"].notna()
        frame.loc[filled, "trade_return"] = frame.loc[filled, "sell_price"] / frame.loc[filled, "buy_price"] - 1.0
    return frame


def _performance_summary(
    selected_candidates: pd.DataFrame,
    simulated_trades: pd.DataFrame,
    benchmark_data: pd.DataFrame | None,
) -> dict[str, Any]:
    if simulated_trades.empty:
        returns = pd.Series(dtype="float64")
    else:
        returns = pd.to_numeric(simulated_trades.get("trade_return", pd.Series(dtype="float64")), errors="coerce").dropna()

    benchmark_return = _benchmark_return(simulated_trades, benchmark_data)
    equal_weight_return = _none_if_nan(returns.mean()) if not returns.empty else None
    return {
        "number_of_candidates": int(len(selected_candidates)),
        "number_of_simulated_buys": int((simulated_trades.get("buy_status", pd.Series(dtype="object")) == "PASS").sum()),
        "number_of_skipped_buys": int((simulated_trades.get("trade_status", pd.Series(dtype="object")) == "SKIPPED_BUY").sum()),
        "average_return": _none_if_nan(returns.mean()) if not returns.empty else None,
        "median_return": _none_if_nan(returns.median()) if not returns.empty else None,
        "win_rate": _none_if_nan((returns > 0).mean()) if not returns.empty else None,
        "best_return": _none_if_nan(returns.max()) if not returns.empty else None,
        "worst_return": _none_if_nan(returns.min()) if not returns.empty else None,
        "total_equal_weight_return": equal_weight_return,
        "benchmark_return": benchmark_return,
        "excess_return": None if benchmark_return is None or equal_weight_return is None else equal_weight_return - benchmark_return,
    }


def _benchmark_return(simulated_trades: pd.DataFrame, benchmark_data: pd.DataFrame | None) -> float | None:
    if benchmark_data is None or simulated_trades.empty:
        return None

    filled = simulated_trades.loc[simulated_trades.get("trade_status", pd.Series(dtype="object")) == "FILLED"]
    if filled.empty:
        return None

    benchmark = benchmark_data.copy(deep=True)
    if "trade_date" not in benchmark.columns or "close" not in benchmark.columns:
        return None
    benchmark["trade_date"] = pd.to_datetime(benchmark["trade_date"], errors="coerce").dt.normalize()
    benchmark["close"] = pd.to_numeric(benchmark["close"], errors="coerce")
    benchmark = benchmark.dropna(subset=["trade_date", "close"]).sort_values("trade_date")
    if benchmark.empty:
        return None

    returns = []
    for trade in filled.to_dict("records"):
        buy_date = pd.Timestamp(trade["buy_date"]).normalize()
        sell_date = pd.Timestamp(trade["sell_date"]).normalize()
        buy_close = _benchmark_close_on_or_before(benchmark, buy_date)
        sell_close = _benchmark_close_on_or_before(benchmark, sell_date)
        if buy_close is not None and sell_close is not None and buy_close != 0:
            returns.append(sell_close / buy_close - 1.0)

    if not returns:
        return None
    return float(pd.Series(returns).mean())


def _benchmark_close_on_or_before(benchmark: pd.DataFrame, date: pd.Timestamp) -> float | None:
    rows = benchmark.loc[benchmark["trade_date"] <= date]
    if rows.empty:
        return None
    return float(rows.iloc[-1]["close"])


def _audit_metadata(
    as_of_date: pd.Timestamp,
    decision_time: pd.Timestamp,
    universe_name: str,
    holding_horizon: int,
    factor_dataset: pd.DataFrame,
    scored_dataset: pd.DataFrame,
    selected_candidates: pd.DataFrame,
    simulated_trades: pd.DataFrame,
    corporate_actions: pd.DataFrame | None,
) -> dict[str, Any]:
    latest_market_time = _max_timestamp(factor_dataset, "latest_market_available_time")
    universe_time = _max_timestamp(factor_dataset, "universe_available_time")
    return {
        "decision_date": as_of_date,
        "decision_time": decision_time,
        "universe_name": universe_name,
        "holding_horizon_trading_days": holding_horizon,
        "point_in_time_rule": "available_time <= decision_time",
        "latest_market_available_time": latest_market_time,
        "latest_universe_available_time": universe_time,
        "factor_dataset_rows": len(factor_dataset),
        "scored_dataset_rows": len(scored_dataset),
        "selected_candidate_rows": len(selected_candidates),
        "simulated_trade_rows": len(simulated_trades),
        "corporate_actions_supplied": corporate_actions is not None,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
    }


def _config_summary(settings: Settings, top_n: int, holding_horizon: int, run_id: str) -> dict[str, Any]:
    return {
        "top_n": top_n,
        "holding_horizon": holding_horizon,
        "run_id": run_id,
        "config_version": settings.replay_run.config_version,
        "min_action": settings.replay_run.min_action,
        "min_final_score": settings.replay_run.min_final_score,
        "factor_dataset": settings.factor_dataset.model_dump(),
        "score_engine_weights": settings.score_engine.weights,
        "candidate_selection": settings.candidate_selection.model_dump(),
        "execution": {
            "mode": settings.execution.mode,
            "price_field": settings.execution.price_field,
            "max_exit_delay_trading_days": settings.execution.max_exit_delay_trading_days,
            "block_buy_on_limit_up": settings.execution.block_buy_on_limit_up,
            "block_sell_on_limit_down": settings.execution.block_sell_on_limit_down,
            "default_slippage_bps": settings.execution.default_slippage_bps,
        },
    }


def _max_timestamp(frame: pd.DataFrame, column: str) -> pd.Timestamp | None:
    if column not in frame.columns or frame.empty:
        return None
    values = pd.to_datetime(frame[column], errors="coerce").dropna()
    if values.empty:
        return None
    return pd.Timestamp(values.max())


def _render_report(result: ReplayRunResult) -> str:
    lines = [
        f"# Replay Report: {result.decision_date.date()} / {result.universe_name}",
        "",
        "## 1. Replay Metadata",
        "",
        _dict_table(
            {
                "decision_date": result.decision_date.date(),
                "decision_time": result.decision_time,
                "universe_name": result.universe_name,
                "factor_dataset_row_count": result.factor_dataset_row_count,
                "scored_dataset_row_count": result.scored_dataset_row_count,
                "report_path": result.report_path,
            }
        ),
        "",
        "## 2. Data Audit Summary",
        "",
        _dict_table(result.audit_metadata),
        "",
        "## 3. Candidate Table",
        "",
        _markdown_table(
            result.selected_candidates,
            ["symbol", "final_score", "action", "risk_precheck_status", "risk_precheck_reason"],
        ),
        "",
        "## 4. Score Breakdown",
        "",
        _markdown_table(
            result.selected_candidates,
            ["symbol", "technical_score", "expectation_score", "liquidity_score", "risk_penalty", "score_reason"],
        ),
        "",
        "## 5. Simulated Trade Table",
        "",
        _markdown_table(
            result.simulated_trades,
            ["symbol", "buy_date", "buy_status", "buy_reason", "sell_date", "trade_status", "trade_return"],
        ),
        "",
        "## 6. Performance Summary",
        "",
        _dict_table(result.performance_summary),
        "",
        "## 7. Warnings and Skipped Trades",
        "",
        _warnings_section(result),
        "",
        "## 8. Known Limitations",
        "",
        "- Uses local CSV/mock data only.",
        "- Does not place live orders or call broker APIs.",
        "- Uses existing T+1 open-price execution assumptions.",
        "- Evaluation uses future market rows after the decision date only for return measurement.",
        "- Portfolio cash, sizing, and transaction ledger are not implemented in this orchestrator.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _warnings_section(result: ReplayRunResult) -> str:
    lines = []
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- None")

    skipped = result.simulated_trades.loc[
        result.simulated_trades.get("trade_status", pd.Series(dtype="object")) == "SKIPPED_BUY"
    ]
    if not skipped.empty:
        lines.append("")
        lines.append("Skipped buys:")
        for row in skipped.to_dict("records"):
            lines.append(f"- {row.get('symbol')}: {row.get('buy_reason')}")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"

    table = frame[available].head(max_rows).copy()
    header = "| " + " | ".join(available) + " |"
    separator = "| " + " | ".join("---" for _ in available) + " |"
    rows = [header, separator]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _resolve_report_path(
    settings: Settings,
    decision_date: pd.Timestamp,
    universe_name: str,
    report_output_path: str | Path | None,
) -> Path:
    if report_output_path is not None:
        return Path(report_output_path)
    safe_universe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in universe_name)
    return Path(settings.replay_run.output_dir) / f"replay_{decision_date.date()}_{safe_universe}.md"


def _execution_settings_with_horizon(settings: ExecutionSettings, holding_horizon: int) -> ExecutionSettings:
    payload = settings.model_dump() if hasattr(settings, "model_dump") else dict(settings)
    payload["default_holding_horizon_trading_days"] = holding_horizon
    return ExecutionSettings(**payload)


def _load_run_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _none_if_nan(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
