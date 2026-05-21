"""Batch replay orchestration across multiple decision dates."""

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
from quant_replay_system.config import BatchReplaySettings, Settings, load_settings
from quant_replay_system.data import load_corporate_actions, load_market_data, load_universe_snapshot
from quant_replay_system.report_generation import KNOWN_LIMITATIONS
from quant_replay_system.replay_run import ReplayRunResult, run_replay


@dataclass(frozen=True)
class BatchArtifactPaths:
    """Stable artifact paths for one batch replay."""

    artifact_dir: Path
    batch_report: Path
    batch_index: Path
    aggregate_performance: Path
    replay_runs: Path
    skipped_dates: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "batch_report": self.batch_report,
            "batch_index": self.batch_index,
            "aggregate_performance": self.aggregate_performance,
            "replay_runs": self.replay_runs,
            "skipped_dates": self.skipped_dates,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class BatchReplayResult:
    """Structured result returned by a batch replay run."""

    batch_id: str
    universe_name: str
    top_n: int
    holding_horizon: int
    requested_decision_dates: list[pd.Timestamp]
    executed_decision_dates: list[pd.Timestamp]
    skipped_decision_dates: pd.DataFrame
    replay_results: list[ReplayRunResult]
    aggregate_performance: dict[str, Any]
    artifact_paths: dict[str, Path]
    warnings: list[str]
    batch_index: pd.DataFrame
    replay_runs_frame: pd.DataFrame
    config_summary: dict[str, Any]


def run_batch_replay(
    decision_dates: Iterable[str | pd.Timestamp] | str | pd.Timestamp,
    universe_name: str = "default",
    top_n: int | None = None,
    holding_horizon: int | None = None,
    config: Settings | str | Path | None = None,
    market_data: pd.DataFrame | None = None,
    universe_snapshot: pd.DataFrame | None = None,
    benchmark_data: pd.DataFrame | None = None,
    corporate_actions: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    batch_id: str | None = None,
) -> BatchReplayResult:
    """Run auditable single-date replay orchestration over many decision dates."""

    settings = _load_batch_settings(config)
    batch_settings = settings.batch_replay
    requested_dates, initial_skips = _normalize_decision_dates(decision_dates, fail_fast=batch_settings.fail_fast)
    effective_top_n = top_n if top_n is not None else batch_settings.default_top_n
    effective_horizon = holding_horizon if holding_horizon is not None else batch_settings.default_holding_horizon
    effective_batch_id = batch_id or generate_batch_id(
        decision_dates=requested_dates,
        universe_name=universe_name,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        config_version=batch_settings.config_version,
    )

    market = market_data.copy(deep=True) if market_data is not None else load_market_data(settings.data.mock_prices)
    universe = (
        universe_snapshot.copy(deep=True)
        if universe_snapshot is not None
        else load_universe_snapshot(settings.data.mock_universe_snapshots)
    )
    calendar = trading_calendar if trading_calendar is not None else load_trading_calendar(settings.data.mock_trading_calendar)
    actions = corporate_actions
    if actions is None and settings.data.mock_corporate_actions.exists():
        actions = load_corporate_actions(settings.data.mock_corporate_actions)

    skipped_rows = list(initial_skips)
    replay_results: list[ReplayRunResult] = []
    warnings: list[str] = []

    for decision_date in requested_dates:
        try:
            if batch_settings.skip_non_trading_days and not calendar.is_trading_day(decision_date):
                skipped_rows.append(
                    _skipped_row(
                        decision_date=decision_date,
                        reason="NON_TRADING_DAY",
                        detail=_calendar_reason(calendar, decision_date),
                    )
                )
                continue

            result = run_replay(
                decision_date=decision_date,
                universe_name=universe_name,
                top_n=effective_top_n,
                holding_horizon=effective_horizon,
                config=settings,
                market_data=market,
                universe_snapshot=universe,
                benchmark_data=benchmark_data,
                corporate_actions=actions,
                trading_calendar=calendar,
            )
            replay_results.append(result)
        except Exception as exc:
            if batch_settings.fail_fast:
                raise
            message = f"{decision_date.date()} replay failed: {exc}"
            warnings.append(message)
            skipped_rows.append(_skipped_row(decision_date=decision_date, reason="RUN_FAILED", detail=str(exc)))

    skipped_dates = _skipped_dates_frame(skipped_rows)
    executed_dates = [result.decision_date for result in replay_results]
    aggregate_performance = aggregate_batch_performance(
        replay_results=replay_results,
        requested_count=len(requested_dates) + len(initial_skips),
        skipped_dates=skipped_dates,
    )
    batch_index = build_batch_index(replay_results)
    replay_runs_frame = build_replay_runs_frame(replay_results)
    config_summary = _batch_config_summary(
        settings=settings,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        batch_id=effective_batch_id,
    )
    paths = resolve_batch_artifact_paths(batch_settings.output_dir, effective_batch_id)

    result = BatchReplayResult(
        batch_id=effective_batch_id,
        universe_name=universe_name,
        top_n=effective_top_n,
        holding_horizon=effective_horizon,
        requested_decision_dates=requested_dates,
        executed_decision_dates=executed_dates,
        skipped_decision_dates=skipped_dates,
        replay_results=replay_results,
        aggregate_performance=aggregate_performance,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        batch_index=batch_index,
        replay_runs_frame=replay_runs_frame,
        config_summary=config_summary,
    )
    if batch_settings.write_artifacts:
        write_batch_replay_report(result)
    return result


def generate_batch_id(
    decision_dates: Iterable[str | pd.Timestamp],
    universe_name: str,
    top_n: int,
    holding_horizon: int,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic short batch id from batch parameters."""

    normalized_dates = [str(pd.Timestamp(date).normalize().date()) for date in decision_dates]
    payload = {
        "decision_dates": normalized_dates,
        "universe_name": universe_name,
        "top_n": int(top_n),
        "holding_horizon": int(holding_horizon),
        "config_version": config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def resolve_batch_artifact_paths(output_dir: str | Path, batch_id: str) -> BatchArtifactPaths:
    """Resolve stable artifact paths for one batch replay."""

    artifact_dir = Path(output_dir) / batch_id
    return BatchArtifactPaths(
        artifact_dir=artifact_dir,
        batch_report=artifact_dir / "batch_report.md",
        batch_index=artifact_dir / "batch_index.csv",
        aggregate_performance=artifact_dir / "aggregate_performance.csv",
        replay_runs=artifact_dir / "replay_runs.csv",
        skipped_dates=artifact_dir / "skipped_dates.csv",
        metadata=artifact_dir / "metadata.json",
    )


def aggregate_batch_performance(
    replay_results: list[ReplayRunResult],
    requested_count: int,
    skipped_dates: pd.DataFrame,
) -> dict[str, Any]:
    """Aggregate run-level and trade-level performance across replay results."""

    skipped_count = len(skipped_dates)
    failed_count = int((skipped_dates.get("reason", pd.Series(dtype="object")) == "RUN_FAILED").sum())
    return_series = _all_trade_returns(replay_results)
    equal_weight_returns = _summary_series(replay_results, "total_equal_weight_return")
    benchmark_returns = _summary_series(replay_results, "benchmark_return")
    excess_returns = _summary_series(replay_results, "excess_return")

    return {
        "number_of_requested_dates": int(requested_count),
        "number_of_executed_dates": int(len(replay_results)),
        "number_of_skipped_dates": int(skipped_count),
        "number_of_failed_dates": int(failed_count),
        "total_candidates": int(sum(_summary_int(result, "number_of_candidates") for result in replay_results)),
        "total_simulated_trades": int(sum(len(result.simulated_trades) for result in replay_results)),
        "total_skipped_trades": int(sum(_summary_int(result, "number_of_skipped_buys") for result in replay_results)),
        "average_return": _none_if_nan(return_series.mean()) if not return_series.empty else None,
        "median_return": _none_if_nan(return_series.median()) if not return_series.empty else None,
        "win_rate": _none_if_nan((return_series > 0).mean()) if not return_series.empty else None,
        "best_return": _none_if_nan(return_series.max()) if not return_series.empty else None,
        "worst_return": _none_if_nan(return_series.min()) if not return_series.empty else None,
        "average_equal_weight_return_by_run": (
            _none_if_nan(equal_weight_returns.mean()) if not equal_weight_returns.empty else None
        ),
        "average_benchmark_return": _none_if_nan(benchmark_returns.mean()) if not benchmark_returns.empty else None,
        "average_excess_return": _none_if_nan(excess_returns.mean()) if not excess_returns.empty else None,
    }


def build_batch_index(replay_results: list[ReplayRunResult]) -> pd.DataFrame:
    """Build one index row per successful replay run."""

    rows = []
    for result in replay_results:
        paths = result.artifact_paths
        performance = result.performance_summary
        rows.append(
            {
                "decision_date": result.decision_date,
                "run_id": result.run_id,
                "report_path": paths.get("report"),
                "candidates_path": paths.get("candidates"),
                "trades_path": paths.get("simulated_trades"),
                "number_of_candidates": performance.get("number_of_candidates", len(result.selected_candidates)),
                "number_of_simulated_buys": performance.get("number_of_simulated_buys"),
                "number_of_skipped_buys": performance.get("number_of_skipped_buys"),
                "average_return": performance.get("average_return"),
                "win_rate": performance.get("win_rate"),
                "benchmark_return": performance.get("benchmark_return"),
                "excess_return": performance.get("excess_return"),
                "status": "COMPLETED",
                "warning_count": len(result.warnings),
            }
        )
    return _ordered_frame(rows, _batch_index_columns())


def build_replay_runs_frame(replay_results: list[ReplayRunResult]) -> pd.DataFrame:
    """Build flattened replay-run metadata rows."""

    rows = []
    for result in replay_results:
        rows.append(
            {
                "decision_date": result.decision_date,
                "decision_time": result.decision_time,
                "universe_name": result.universe_name,
                "run_id": result.run_id,
                "top_n": result.top_n,
                "holding_horizon": result.holding_horizon,
                "factor_dataset_row_count": result.factor_dataset_row_count,
                "scored_dataset_row_count": result.scored_dataset_row_count,
                "selected_candidate_rows": len(result.selected_candidates),
                "simulated_trade_rows": len(result.simulated_trades),
                "report_path": result.report_path,
                "status": "COMPLETED",
                "warning_count": len(result.warnings),
            }
        )
    return _ordered_frame(rows, _replay_runs_columns())


def write_batch_replay_report(result: BatchReplayResult, path: str | Path | None = None) -> Path:
    """Write batch-level markdown, CSV, and metadata artifacts."""

    paths = BatchArtifactPaths(**result.artifact_paths)
    if path is not None:
        paths = BatchArtifactPaths(
            artifact_dir=Path(path).parent,
            batch_report=Path(path),
            batch_index=paths.batch_index,
            aggregate_performance=paths.aggregate_performance,
            replay_runs=paths.replay_runs,
            skipped_dates=paths.skipped_dates,
            metadata=paths.metadata,
        )

    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.batch_index, paths.batch_index)
    _export_dataframe(pd.DataFrame([result.aggregate_performance]), paths.aggregate_performance)
    _export_dataframe(result.replay_runs_frame, paths.replay_runs)
    _export_dataframe(result.skipped_decision_dates, paths.skipped_dates)

    metadata = build_batch_replay_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.batch_report.write_text(render_batch_replay_report(result, paths, metadata), encoding="utf-8")
    return paths.batch_report


def build_batch_replay_metadata(result: BatchReplayResult, paths: BatchArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for a batch replay result."""

    output_files = {name: str(path) for name, path in paths.as_dict().items() if name != "artifact_dir"}
    return {
        "batch_id": result.batch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "universe_name": result.universe_name,
        "top_n": result.top_n,
        "holding_horizon": result.holding_horizon,
        "config_summary": result.config_summary,
        "requested_dates": result.requested_decision_dates,
        "executed_dates": result.executed_decision_dates,
        "skipped_dates": result.skipped_decision_dates.to_dict("records"),
        "output_files": output_files,
        "row_counts": {
            "batch_index": len(result.batch_index),
            "replay_runs": len(result.replay_runs_frame),
            "skipped_dates": len(result.skipped_decision_dates),
        },
        "aggregate_performance": result.aggregate_performance,
        "known_limitations": KNOWN_LIMITATIONS,
        "warnings": result.warnings,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
    }


def render_batch_replay_report(
    result: BatchReplayResult,
    paths: BatchArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render the batch-level markdown report."""

    date_summary = {
        "requested_dates": result.aggregate_performance["number_of_requested_dates"],
        "executed_dates": result.aggregate_performance["number_of_executed_dates"],
        "skipped_dates": result.aggregate_performance["number_of_skipped_dates"],
        "failed_dates": result.aggregate_performance["number_of_failed_dates"],
    }
    lines = [
        f"# Batch Replay Report: {result.batch_id}",
        "",
        "## Batch Metadata",
        "",
        _dict_table(
            {
                "batch_id": result.batch_id,
                "universe_name": result.universe_name,
                "top_n": result.top_n,
                "holding_horizon": result.holding_horizon,
                "artifact_dir": paths.artifact_dir,
                "batch_report": paths.batch_report,
            }
        ),
        "",
        "## Config Summary",
        "",
        _dict_table(result.config_summary),
        "",
        "## Date Execution Summary",
        "",
        _dict_table(date_summary),
        "",
        "## Aggregate Performance Summary",
        "",
        _dict_table(result.aggregate_performance),
        "",
        "## Replay Run Table",
        "",
        _markdown_table(result.batch_index, _batch_index_columns()),
        "",
        "## Skipped and Failed Dates",
        "",
        _markdown_table(result.skipped_decision_dates, ["decision_date", "reason", "detail"]),
        "",
        "## Individual Replay Reports",
        "",
        _markdown_table(result.batch_index, ["decision_date", "run_id", "report_path"]),
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


def _load_batch_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _normalize_decision_dates(
    decision_dates: Iterable[str | pd.Timestamp] | str | pd.Timestamp,
    *,
    fail_fast: bool,
) -> tuple[list[pd.Timestamp], list[dict[str, Any]]]:
    raw_dates = [decision_dates] if isinstance(decision_dates, (str, pd.Timestamp)) else list(decision_dates)
    normalized_dates: list[pd.Timestamp] = []
    skipped_rows: list[dict[str, Any]] = []
    for raw_date in raw_dates:
        try:
            normalized_dates.append(_normalize_date(raw_date))
        except Exception as exc:
            if fail_fast:
                raise ValueError(f"Invalid decision date {raw_date!r}: {exc}") from exc
            skipped_rows.append({"decision_date": str(raw_date), "reason": "INVALID_DATE", "detail": str(exc)})
    return normalized_dates, skipped_rows


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _calendar_reason(calendar: TradingCalendar, decision_date: pd.Timestamp) -> str:
    rows = calendar.frame.loc[calendar.frame["trade_date"] == decision_date]
    if rows.empty:
        return "outside loaded trading calendar"
    reason = str(rows.iloc[0].get("reason", "")).strip()
    return reason or "non-trading day"


def _skipped_row(decision_date: pd.Timestamp, reason: str, detail: str) -> dict[str, Any]:
    return {"decision_date": decision_date, "reason": reason, "detail": detail}


def _skipped_dates_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return _ordered_frame(rows, ["decision_date", "reason", "detail"])


def _batch_config_summary(
    settings: Settings,
    top_n: int,
    holding_horizon: int,
    batch_id: str,
) -> dict[str, Any]:
    batch_settings = settings.batch_replay
    return {
        "batch_id": batch_id,
        "top_n": top_n,
        "holding_horizon": holding_horizon,
        "config_version": batch_settings.config_version,
        "skip_non_trading_days": batch_settings.skip_non_trading_days,
        "fail_fast": batch_settings.fail_fast,
        "output_dir": batch_settings.output_dir,
        "replay_run": {
            "min_action": settings.replay_run.min_action,
            "min_final_score": settings.replay_run.min_final_score,
            "config_version": settings.replay_run.config_version,
            "write_artifacts": settings.replay_run.write_artifacts,
        },
    }


def _all_trade_returns(replay_results: list[ReplayRunResult]) -> pd.Series:
    values = []
    for result in replay_results:
        if "trade_return" not in result.simulated_trades.columns:
            continue
        returns = pd.to_numeric(result.simulated_trades["trade_return"], errors="coerce").dropna()
        values.extend(returns.tolist())
    return pd.Series(values, dtype="float64")


def _summary_series(replay_results: list[ReplayRunResult], key: str) -> pd.Series:
    values = []
    for result in replay_results:
        value = result.performance_summary.get(key)
        if value is not None and not pd.isna(value):
            values.append(float(value))
    return pd.Series(values, dtype="float64")


def _summary_int(result: ReplayRunResult, key: str) -> int:
    value = result.performance_summary.get(key)
    if value is None or pd.isna(value):
        return 0
    return int(value)


def _ordered_frame(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    remaining = [column for column in frame.columns if column not in columns]
    return frame[[*columns, *remaining]]


def _batch_index_columns() -> list[str]:
    return [
        "decision_date",
        "run_id",
        "report_path",
        "candidates_path",
        "trades_path",
        "number_of_candidates",
        "number_of_simulated_buys",
        "number_of_skipped_buys",
        "average_return",
        "win_rate",
        "benchmark_return",
        "excess_return",
        "status",
        "warning_count",
    ]


def _replay_runs_columns() -> list[str]:
    return [
        "decision_date",
        "decision_time",
        "universe_name",
        "run_id",
        "top_n",
        "holding_horizon",
        "factor_dataset_row_count",
        "scored_dataset_row_count",
        "selected_candidate_rows",
        "simulated_trade_rows",
        "report_path",
        "status",
        "warning_count",
    ]


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
    if isinstance(value, BatchReplaySettings):
        return value.model_dump() if hasattr(value, "model_dump") else dict(value)
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


def _none_if_nan(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
