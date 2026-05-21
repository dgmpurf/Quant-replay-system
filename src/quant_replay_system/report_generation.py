"""Replay report and artifact generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


KNOWN_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Uses existing T+1 open-price execution assumptions.",
    "Evaluation uses future market rows after the decision date only for return measurement.",
    "Portfolio cash, sizing, and transaction ledger are not implemented in this orchestrator.",
]


@dataclass(frozen=True)
class ReplayArtifactPaths:
    artifact_dir: Path
    report: Path
    factor_dataset: Path
    scored_dataset: Path
    candidates: Path
    simulated_trades: Path
    performance_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "report": self.report,
            "factor_dataset": self.factor_dataset,
            "scored_dataset": self.scored_dataset,
            "candidates": self.candidates,
            "simulated_trades": self.simulated_trades,
            "performance_summary": self.performance_summary,
            "metadata": self.metadata,
        }


def generate_replay_run_id(
    decision_date: str | pd.Timestamp,
    universe_name: str,
    top_n: int,
    holding_horizon: int,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic short run id from replay parameters."""

    payload = {
        "decision_date": str(pd.Timestamp(decision_date).normalize().date()),
        "universe_name": universe_name,
        "top_n": int(top_n),
        "holding_horizon": int(holding_horizon),
        "config_version": config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def resolve_replay_artifact_paths(
    output_dir: str | Path,
    decision_date: str | pd.Timestamp,
    universe_name: str,
    run_id: str,
    report_output_path: str | Path | None = None,
) -> ReplayArtifactPaths:
    """Resolve stable artifact paths for one replay run."""

    if report_output_path is not None:
        requested = Path(report_output_path)
        if requested.suffix.lower() == ".md":
            artifact_dir = requested.parent
            report = requested
        else:
            artifact_dir = _stable_artifact_dir(requested, decision_date, universe_name, run_id)
            report = artifact_dir / "report.md"
    else:
        artifact_dir = _stable_artifact_dir(Path(output_dir), decision_date, universe_name, run_id)
        report = artifact_dir / "report.md"

    return ReplayArtifactPaths(
        artifact_dir=artifact_dir,
        report=report,
        factor_dataset=artifact_dir / "factor_dataset.csv",
        scored_dataset=artifact_dir / "scored_dataset.csv",
        candidates=artifact_dir / "candidates.csv",
        simulated_trades=artifact_dir / "simulated_trades.csv",
        performance_summary=artifact_dir / "performance_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_replay_artifacts(result: Any) -> ReplayArtifactPaths:
    """Write markdown, CSV, and JSON artifacts for a replay result."""

    paths = ReplayArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)

    _export_dataframe(result.factor_dataset, paths.factor_dataset)
    _export_dataframe(result.scored_dataset, paths.scored_dataset)
    _export_dataframe(_candidate_export_frame(result.selected_candidates), paths.candidates)
    _export_dataframe(_trade_export_frame(result.simulated_trades), paths.simulated_trades)
    _export_dataframe(pd.DataFrame([result.performance_summary]), paths.performance_summary)

    metadata = build_replay_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.report.write_text(render_replay_report(result, paths, metadata), encoding="utf-8")
    return paths


def build_replay_metadata(result: Any, paths: ReplayArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for a replay result."""

    output_files = {name: str(path) for name, path in paths.as_dict().items() if name != "artifact_dir"}
    return {
        "decision_date": result.decision_date,
        "decision_time": result.decision_time,
        "universe_name": result.universe_name,
        "top_n": result.top_n,
        "holding_horizon": result.holding_horizon,
        "run_id": result.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_summary": result.config_summary,
        "row_counts": {
            "factor_dataset": result.factor_dataset_row_count,
            "scored_dataset": result.scored_dataset_row_count,
            "selected_candidates": len(result.selected_candidates),
            "simulated_trades": len(result.simulated_trades),
        },
        "output_files": output_files,
        "warnings": result.warnings,
        "known_limitations": KNOWN_LIMITATIONS,
        "audit_metadata": result.audit_metadata,
    }


def render_replay_report(result: Any, paths: ReplayArtifactPaths, metadata: dict[str, Any]) -> str:
    """Render a hardened markdown replay report."""

    candidates = _candidate_export_frame(result.selected_candidates)
    trades = _trade_export_frame(result.simulated_trades)
    skipped = trades.loc[trades["status"].isin(["SKIPPED_BUY", "EXIT_BLOCKED"])] if "status" in trades.columns else trades.iloc[0:0]

    lines = [
        f"# Replay Report: {result.decision_date.date()} / {result.universe_name}",
        "",
        "## Replay Metadata",
        "",
        _dict_table(
            {
                "decision_date": result.decision_date.date(),
                "decision_time": result.decision_time,
                "universe_name": result.universe_name,
                "run_id": result.run_id,
                "top_n": result.top_n,
                "holding_horizon": result.holding_horizon,
                "artifact_dir": paths.artifact_dir,
                "report_path": paths.report,
            }
        ),
        "",
        "## Config Summary",
        "",
        _dict_table(result.config_summary),
        "",
        "## Data Audit Summary",
        "",
        _dict_table(result.audit_metadata),
        "",
        "## Universe and Dataset Counts",
        "",
        _dict_table(metadata["row_counts"]),
        "",
        "## Candidate Table",
        "<!-- ## 3. Candidate Table -->",
        "",
        _markdown_table(
            candidates,
            [
                "rank",
                "symbol",
                "name",
                "final_score",
                "action",
                "technical_score",
                "liquidity_score",
                "expectation_score",
                "reality_score",
                "sentiment_score",
                "risk_penalty",
                "risk_precheck_status",
                "risk_precheck_reason",
            ],
        ),
        "",
        "Candidate compact view:",
        "",
        _markdown_table(candidates, ["symbol", "final_score", "action"]),
        "",
        "## Score Breakdown",
        "",
        _markdown_table(
            candidates,
            [
                "rank",
                "symbol",
                "final_score",
                "technical_score",
                "liquidity_score",
                "expectation_score",
                "reality_score",
                "sentiment_score",
                "risk_penalty",
                "score_reason",
            ],
        ),
        "",
        "## Simulated Trade Table",
        "",
        _markdown_table(
            trades,
            [
                "symbol",
                "buy_date",
                "buy_price",
                "planned_sell_date",
                "sell_date",
                "sell_price",
                "return_pct",
                "status",
                "skip_reason",
            ],
        ),
        "",
        "## Skipped and Blocked Trades",
        "",
        _markdown_table(skipped, ["symbol", "status", "skip_reason", "buy_date", "planned_sell_date", "sell_date"]),
        "",
        "## Performance Summary",
        "<!-- ## 6. Performance Summary -->",
        "",
        _dict_table(result.performance_summary),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known Limitations",
        "",
        "\n".join(f"- {item}" for item in KNOWN_LIMITATIONS),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _stable_artifact_dir(output_dir: Path, decision_date: str | pd.Timestamp, universe_name: str, run_id: str) -> Path:
    safe_universe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in universe_name)
    folder = f"{pd.Timestamp(decision_date).normalize().date()}_{safe_universe}_{run_id}"
    return output_dir / "replay_runs" / folder


def _candidate_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = frame.copy(deep=True)
    if candidates.empty:
        return pd.DataFrame(columns=_candidate_columns())
    if "rank" not in candidates.columns:
        candidates.insert(0, "rank", range(1, len(candidates) + 1))
    if "action" not in candidates.columns and "score_action" in candidates.columns:
        candidates["action"] = candidates["score_action"]
    return _order_columns(candidates, _candidate_columns())


def _trade_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    trades = frame.copy(deep=True)
    if trades.empty:
        return pd.DataFrame(columns=_trade_columns())
    if "return_pct" not in trades.columns:
        trade_return = pd.to_numeric(trades.get("trade_return", pd.Series(dtype="float64")), errors="coerce")
        trades["return_pct"] = trade_return * 100.0
    if "status" not in trades.columns and "trade_status" in trades.columns:
        trades["status"] = trades["trade_status"]
    if "skip_reason" not in trades.columns:
        trades["skip_reason"] = ""
        if "trade_status" in trades.columns:
            skipped_buy = trades["trade_status"] == "SKIPPED_BUY"
            exit_blocked = trades["trade_status"] == "EXIT_BLOCKED"
            if "buy_reason" in trades.columns:
                trades.loc[skipped_buy, "skip_reason"] = trades.loc[skipped_buy, "buy_reason"]
            if "sell_reason" in trades.columns:
                trades.loc[exit_blocked, "skip_reason"] = trades.loc[exit_blocked, "sell_reason"]
    return _order_columns(trades, _trade_columns())


def _candidate_columns() -> list[str]:
    return [
        "rank",
        "symbol",
        "name",
        "final_score",
        "action",
        "technical_score",
        "liquidity_score",
        "expectation_score",
        "reality_score",
        "sentiment_score",
        "risk_penalty",
        "risk_precheck_status",
        "risk_precheck_reason",
        "score_reason",
        "score_breakdown",
    ]


def _trade_columns() -> list[str]:
    return [
        "symbol",
        "buy_date",
        "buy_price",
        "planned_sell_date",
        "sell_date",
        "sell_price",
        "return_pct",
        "status",
        "skip_reason",
        "buy_status",
        "buy_reason",
        "sell_status",
        "sell_reason",
    ]


def _order_columns(frame: pd.DataFrame, preferred: list[str]) -> pd.DataFrame:
    for column in preferred:
        if column not in frame.columns:
            frame[column] = pd.NA
    remaining = [column for column in frame.columns if column not in preferred]
    return frame[[*preferred, *remaining]]


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


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
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
    if isinstance(value, pd.Timestamp):
        return str(value)
    if isinstance(value, Path):
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
