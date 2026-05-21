"""Local-only daily runner for manual paper trading journals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import DailyPaperRunnerSettings, PaperTradingSettings, Settings, load_settings
from quant_replay_system.data import load_market_data
from quant_replay_system.paper_trading import (
    PAPER_TRADING_LIMITATIONS,
    build_closed_trades,
    build_open_positions,
    create_paper_decision_log,
    validate_paper_fills,
)


DAILY_PAPER_LIMITATIONS = [
    *PAPER_TRADING_LIMITATIONS,
    "Daily runner loads local candidate and fill files only.",
    "Missing fills files are treated as empty manual fill logs.",
    "No command-line interface is implemented yet.",
]


@dataclass(frozen=True)
class DailyPaperArtifactPaths:
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
class DailyPaperRunResult:
    paper_date: pd.Timestamp
    journal_id: str
    decision_count: int
    fill_count: int
    open_position_count: int
    closed_trade_count: int
    artifact_paths: dict[str, Path]
    daily_summary: pd.DataFrame
    warnings: list[str]
    known_limitations: list[str]
    decisions: pd.DataFrame
    fills: pd.DataFrame
    open_positions: pd.DataFrame
    closed_trades: pd.DataFrame
    audit_metadata: dict[str, Any]


def run_daily_paper_trading(
    paper_date: str | pd.Timestamp,
    *,
    candidates: pd.DataFrame | Any | None = None,
    candidates_path: str | Path | None = None,
    fills_path: str | Path | None = None,
    mark_prices: pd.DataFrame | str | Path | None = None,
    output_dir: str | Path | None = None,
    journal_id: str | None = None,
    config: Settings | str | Path | None = None,
) -> DailyPaperRunResult:
    """Run a local-only daily paper trading journal from candidates and optional fills."""

    settings = _load_project_settings(config)
    runner_settings = settings.daily_paper_runner
    if runner_settings.enable_live_trading or runner_settings.enable_broker_api:
        raise ValueError("Daily paper runner cannot enable live trading or broker API access")

    normalized_date = _normalize_date(paper_date)
    candidate_frame = load_candidates_for_paper_trading(candidates=candidates, candidates_path=candidates_path)
    source_run_id = _first_present(candidate_frame, "source_run_id", "run_id", "replay_run_id")
    source_report_path = _first_present(candidate_frame, "source_report_path", "report_path")
    decisions = create_paper_decision_log(
        candidate_frame,
        decision_date=normalized_date,
        source_run_id=source_run_id,
        source_report_path=source_report_path,
    )

    fills, load_warnings = load_existing_paper_fills(fills_path)
    warnings = list(load_warnings)
    if not fills.empty:
        validation = validate_paper_fills(fills, decisions=decisions, settings=settings.paper_trading)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        warnings.extend(validation.warnings)
    market = load_mark_prices_for_paper_trading(mark_prices, settings)
    open_positions = build_open_positions(fills, market, mark_date=normalized_date)
    closed_trades = build_closed_trades(fills)
    warnings.extend(_daily_runner_warnings(decisions, fills))
    daily_summary = build_daily_paper_summary(
        paper_date=normalized_date,
        decisions=decisions,
        fills=fills,
        open_positions=open_positions,
        closed_trades=closed_trades,
        warnings=warnings,
    )
    effective_journal_id = journal_id or generate_daily_paper_journal_id(
        paper_date=normalized_date,
        decisions=decisions,
        config_version=runner_settings.config_version,
    )
    effective_output_dir = Path(output_dir) if output_dir is not None else runner_settings.output_dir
    paths = resolve_daily_paper_paths(effective_output_dir, normalized_date, effective_journal_id)
    audit_metadata = {
        "paper_date": normalized_date,
        "journal_id": effective_journal_id,
        "decision_count": len(decisions),
        "fill_count": len(fills),
        "open_position_count": len(open_positions),
        "closed_trade_count": len(closed_trades),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    result = DailyPaperRunResult(
        paper_date=normalized_date,
        journal_id=effective_journal_id,
        decision_count=len(decisions),
        fill_count=len(fills),
        open_position_count=len(open_positions),
        closed_trade_count=len(closed_trades),
        artifact_paths=paths.as_dict(),
        daily_summary=daily_summary,
        warnings=warnings,
        known_limitations=DAILY_PAPER_LIMITATIONS,
        decisions=decisions,
        fills=fills,
        open_positions=open_positions,
        closed_trades=closed_trades,
        audit_metadata=audit_metadata,
    )
    if runner_settings.write_artifacts:
        write_daily_paper_artifacts(result, settings.paper_trading)
    return result


def load_candidates_for_paper_trading(
    *,
    candidates: pd.DataFrame | Any | None = None,
    candidates_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load selected candidates from a DataFrame-like object or CSV path."""

    if candidates is not None and candidates_path is not None:
        raise ValueError("Provide either candidates or candidates_path, not both")
    if isinstance(candidates, pd.DataFrame):
        return candidates.copy(deep=True)
    if candidates is not None:
        for attr in ["selected_candidates", "candidates", "candidate_df"]:
            if hasattr(candidates, attr):
                value = getattr(candidates, attr)
                if isinstance(value, pd.DataFrame):
                    return value.copy(deep=True)
        raise TypeError("candidates must be a DataFrame or object with selected_candidates/candidates")
    if candidates_path is None:
        raise ValueError("Either candidates or candidates_path is required")
    path = Path(candidates_path)
    if not path.exists():
        raise FileNotFoundError(f"Candidate CSV not found: {path}")
    return pd.read_csv(path)


def load_existing_paper_fills(fills_path: str | Path | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Load manual paper fills, returning an empty ledger when no file is available."""

    columns = [
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
    if fills_path is None:
        return pd.DataFrame(columns=columns), ["No fills_path provided; continuing with empty paper fills."]
    path = Path(fills_path)
    if not path.exists():
        return pd.DataFrame(columns=columns), [f"Fills file not found: {path}; continuing with empty paper fills."]
    fills = pd.read_csv(path)
    if "fill_date" in fills.columns:
        fills["fill_date"] = pd.to_datetime(fills["fill_date"], errors="coerce").dt.normalize()
    for column in ["fill_price", "quantity", "gross_notional", "fees", "slippage", "net_cash_flow"]:
        if column in fills.columns:
            fills[column] = pd.to_numeric(fills[column], errors="coerce")
    for column in columns:
        if column not in fills.columns:
            fills[column] = pd.NA
    return fills[columns].sort_values(["fill_date", "symbol", "side"], na_position="last").reset_index(drop=True), []


def load_mark_prices_for_paper_trading(
    mark_prices: pd.DataFrame | str | Path | None,
    settings: Settings,
) -> pd.DataFrame:
    """Load local mark-to-market prices from DataFrame, CSV, or configured mock data."""

    if isinstance(mark_prices, pd.DataFrame):
        return mark_prices.copy(deep=True)
    if isinstance(mark_prices, (str, Path)):
        path = Path(mark_prices)
        if not path.exists():
            raise FileNotFoundError(f"Mark prices CSV not found: {path}")
        return pd.read_csv(path)
    return load_market_data(settings.data.mock_prices)


def build_daily_paper_summary(
    *,
    paper_date: str | pd.Timestamp,
    decisions: pd.DataFrame,
    fills: pd.DataFrame,
    open_positions: pd.DataFrame,
    closed_trades: pd.DataFrame,
    warnings: list[str],
) -> pd.DataFrame:
    """Build the daily runner summary row."""

    total_market_value = _sum_numeric(open_positions, "market_value")
    total_unrealized = _sum_numeric(open_positions, "unrealized_pnl")
    total_realized = _sum_numeric(closed_trades, "realized_pnl")
    approved_count = (
        int((decisions["manual_review_status"] == "APPROVED_FOR_PAPER").sum())
        if "manual_review_status" in decisions.columns and not decisions.empty
        else 0
    )
    return pd.DataFrame(
        [
            {
                "paper_date": _normalize_date(paper_date),
                "decision_count": len(decisions),
                "approved_count": approved_count,
                "fill_count": len(fills),
                "open_position_count": len(open_positions),
                "closed_trade_count": len(closed_trades),
                "total_market_value": total_market_value,
                "total_unrealized_pnl": total_unrealized,
                "total_realized_pnl": total_realized,
                "total_pnl": total_unrealized + total_realized,
                "warnings_count": len(warnings),
            }
        ]
    )


def generate_daily_paper_journal_id(
    *,
    paper_date: str | pd.Timestamp,
    decisions: pd.DataFrame,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic daily paper journal id from date and candidate source."""

    payload = {
        "paper_date": str(_normalize_date(paper_date).date()),
        "source_run_ids": sorted(
            str(value)
            for value in decisions.get("source_run_id", pd.Series(dtype="object")).dropna().unique()
            if str(value)
        ),
        "symbols": sorted(str(value) for value in decisions.get("symbol", pd.Series(dtype="object")).dropna().unique()),
        "decision_ids": sorted(str(value) for value in decisions.get("decision_id", pd.Series(dtype="object")).dropna().unique()),
        "config_version": config_version,
    }
    return _hash_payload(payload, length=10)


def resolve_daily_paper_paths(
    output_dir: str | Path,
    paper_date: str | pd.Timestamp,
    journal_id: str,
) -> DailyPaperArtifactPaths:
    """Resolve stable daily paper runner artifact paths."""

    folder = Path(output_dir) / f"{_normalize_date(paper_date).date()}_{journal_id}"
    return DailyPaperArtifactPaths(
        artifact_dir=folder,
        paper_report=folder / "paper_report.md",
        decisions=folder / "decisions.csv",
        fills=folder / "fills.csv",
        open_positions=folder / "open_positions.csv",
        closed_trades=folder / "closed_trades.csv",
        daily_summary=folder / "daily_summary.csv",
        metadata=folder / "metadata.json",
    )


def write_daily_paper_artifacts(
    result: DailyPaperRunResult,
    paper_settings: PaperTradingSettings | None = None,
) -> Path:
    """Write daily paper runner artifacts."""

    paths = DailyPaperArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.decisions, paths.decisions)
    _export_dataframe(result.fills, paths.fills)
    _export_dataframe(result.open_positions, paths.open_positions)
    _export_dataframe(result.closed_trades, paths.closed_trades)
    _export_dataframe(result.daily_summary, paths.daily_summary)
    metadata = build_daily_paper_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")

    report_content = _render_daily_paper_report(result, paths, metadata)
    paths.paper_report.write_text(report_content, encoding="utf-8")
    return paths.paper_report


def build_daily_paper_metadata(result: DailyPaperRunResult, paths: DailyPaperArtifactPaths) -> dict[str, Any]:
    """Build metadata for the daily paper runner."""

    return {
        "paper_date": result.paper_date,
        "journal_id": result.journal_id,
        "created_at": _metadata_created_at(result.paper_date),
        "decision_count": result.decision_count,
        "fill_count": result.fill_count,
        "open_position_count": result.open_position_count,
        "closed_trade_count": result.closed_trade_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def _render_daily_paper_report(
    result: DailyPaperRunResult,
    paths: DailyPaperArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    lines = [
        f"# Daily Paper Trading Report: {result.paper_date.date()}",
        "",
        "No broker or live trading integration was invoked. This is a local manual paper-trading report only.",
        "",
        "## Journal Metadata",
        "",
        _dict_table(
            {
                "paper_date": result.paper_date,
                "journal_id": result.journal_id,
                "artifact_dir": paths.artifact_dir,
                "decision_count": result.decision_count,
                "fill_count": result.fill_count,
            }
        ),
        "",
        "## Candidate Decisions",
        "",
        _markdown_table(
            result.decisions,
            [
                "decision_id",
                "decision_date",
                "candidate_rank",
                "symbol",
                "name",
                "action",
                "final_score",
                "risk_precheck_status",
                "manual_review_status",
            ],
        ),
        "",
        "## Manual Review Summary",
        "",
        _manual_review_summary(result.decisions),
        "",
        "## Paper Fills",
        "",
        _markdown_table(
            result.fills,
            ["fill_id", "decision_id", "symbol", "side", "fill_date", "fill_price", "quantity", "net_cash_flow"],
        ),
        "",
        "## Open Positions",
        "",
        _markdown_table(
            result.open_positions,
            ["symbol", "quantity", "average_cost", "last_mark_price", "market_value", "unrealized_pnl", "status"],
        ),
        "",
        "## Closed Trades",
        "",
        _markdown_table(
            result.closed_trades,
            ["symbol", "open_date", "close_date", "entry_price", "exit_price", "quantity", "realized_pnl"],
        ),
        "",
        "## Daily Performance Summary",
        "",
        _markdown_table(
            result.daily_summary,
            [
                "paper_date",
                "decision_count",
                "approved_count",
                "fill_count",
                "open_position_count",
                "closed_trade_count",
                "total_market_value",
                "total_pnl",
                "warnings_count",
            ],
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in metadata["known_limitations"]),
        "",
    ]
    lines.extend(["## Paper Journal Audit", "", _dict_table(result.audit_metadata), ""])
    return "\n".join(str(line) for line in lines)


def _daily_runner_warnings(decisions: pd.DataFrame, fills: pd.DataFrame) -> list[str]:
    warnings = []
    if decisions.empty:
        warnings.append("No paper decisions were created.")
    pending = int((decisions["manual_review_status"] == "PENDING_REVIEW").sum()) if "manual_review_status" in decisions.columns else 0
    if pending:
        warnings.append(f"{pending} decision(s) pending manual review.")
    if fills.empty:
        warnings.append("No manual paper fills loaded.")
    return warnings


def _manual_review_summary(decisions: pd.DataFrame) -> str:
    if decisions.empty or "manual_review_status" not in decisions.columns:
        return "_No decisions._"
    counts = decisions["manual_review_status"].value_counts().rename_axis("manual_review_status").reset_index(name="count")
    return _markdown_table(counts, ["manual_review_status", "count"])


def _sum_numeric(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).sum())


def _first_present(frame: pd.DataFrame, *columns: str) -> str:
    for column in columns:
        if column in frame.columns:
            values = frame[column].dropna()
            if not values.empty:
                return str(values.iloc[0])
    return ""


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _metadata_created_at(paper_date: pd.Timestamp) -> str:
    if pd.notna(paper_date):
        return paper_date.isoformat()
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
