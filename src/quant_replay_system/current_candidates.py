"""Current/as-of-date candidate generation from local point-in-time data."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.calendar import TradingCalendar, load_trading_calendar
from quant_replay_system.candidate_selection import select_candidates
from quant_replay_system.config import CandidateSelectionSettings, Settings, load_settings
from quant_replay_system.data import load_market_data, load_universe_snapshot
from quant_replay_system.factor_dataset import build_factor_dataset
from quant_replay_system.score_engine import score_factor_dataset
from quant_replay_system.snapshot_quality_gate import load_snapshot_manifest
from quant_replay_system.snapshot_quality_preflight import (
    SnapshotQualityPreflightResult,
    run_snapshot_quality_preflight,
)


CURRENT_CANDIDATE_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Uses existing point-in-time factor, scoring, and candidate selection contracts.",
    "Produces research and paper-trading inputs only; it does not simulate execution.",
    "Snapshot quality preflight validates local snapshot files but does not repair data.",
]


@dataclass(frozen=True)
class CurrentCandidateArtifactPaths:
    artifact_dir: Path
    current_candidates_report: Path
    factor_dataset: Path
    scored_dataset: Path
    candidates: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_report": self.current_candidates_report,
            "factor_dataset": self.factor_dataset,
            "scored_dataset": self.scored_dataset,
            "candidates": self.candidates,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidateResult:
    decision_date: pd.Timestamp
    decision_time: pd.Timestamp
    universe_name: str
    top_n: int
    run_id: str
    factor_dataset_row_count: int
    scored_dataset_row_count: int
    candidate_count: int
    candidates: pd.DataFrame
    artifact_paths: dict[str, Path]
    snapshot_quality_status: str | None
    snapshot_quality_report_path: Path | None
    warnings: list[str]
    known_limitations: list[str]
    factor_dataset: pd.DataFrame
    scored_dataset: pd.DataFrame
    audit_metadata: dict[str, Any]
    config_summary: dict[str, Any]


def generate_current_candidates(
    decision_date: str | pd.Timestamp,
    universe_name: str,
    top_n: int | None = None,
    config: Settings | str | Path | None = None,
    market_data: pd.DataFrame | None = None,
    universe_snapshot: pd.DataFrame | None = None,
    benchmark_data: pd.DataFrame | None = None,
    snapshot_manifest_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    trading_calendar: TradingCalendar | None = None,
    run_id: str | None = None,
    enable_snapshot_preflight: bool | None = None,
) -> CurrentCandidateResult:
    """Generate ranked current/as-of-date candidates from local point-in-time data."""

    settings = _load_project_settings(config)
    if settings.current_candidates.enable_live_trading or settings.current_candidates.enable_broker_api:
        raise ValueError("Current candidate generation cannot enable live trading or broker API access")

    settings = _settings_with_output_dir(settings, output_dir)
    settings = _settings_with_manifest_preflight(settings, snapshot_manifest_path, enable_snapshot_preflight)
    as_of_date = _normalize_date(decision_date)
    effective_top_n = top_n if top_n is not None else settings.current_candidates.default_top_n

    preflight = run_snapshot_quality_preflight(
        settings,
        snapshot_manifest_path=snapshot_manifest_path,
        context="generate_current_candidates",
    )
    snapshot_paths = _snapshot_dataset_paths(snapshot_manifest_path)

    market = (
        market_data.copy(deep=True)
        if market_data is not None
        else load_market_data(snapshot_paths.get("market", settings.data.mock_prices))
    )
    universe = (
        universe_snapshot.copy(deep=True)
        if universe_snapshot is not None
        else load_universe_snapshot(snapshot_paths.get("universe", settings.data.mock_universe_snapshots))
    )
    calendar = trading_calendar or load_trading_calendar(snapshot_paths.get("trading_calendar", settings.data.mock_trading_calendar))
    benchmark = benchmark_data
    if benchmark is None and "benchmark" in snapshot_paths:
        benchmark = load_market_data(snapshot_paths["benchmark"])

    decision_time = calendar.decision_time_for(as_of_date)
    warnings: list[str] = list(preflight.warnings or [])

    factor_dataset = build_factor_dataset(
        decision_date=as_of_date,
        market_data=market,
        universe_snapshot=universe,
        trading_calendar=calendar,
        benchmark_data=benchmark,
        config=settings.factor_dataset,
    )
    scored_dataset = score_factor_dataset(factor_dataset, settings.score_engine)
    selection_config = CandidateSelectionSettings(
        top_n=effective_top_n,
        min_action=settings.current_candidates.min_action,
        min_final_score=settings.current_candidates.min_final_score,
        exclude_blocked=settings.candidate_selection.exclude_blocked,
    )
    selected = select_candidates(scored_dataset, config=selection_config)

    effective_run_id = run_id or generate_current_candidate_run_id(
        decision_date=as_of_date,
        universe_name=universe_name,
        top_n=effective_top_n,
        config_version=settings.current_candidates.config_version,
        snapshot_manifest_path=snapshot_manifest_path,
    )
    paths = resolve_current_candidate_artifact_paths(
        output_dir=settings.current_candidates.output_dir,
        decision_date=as_of_date,
        universe_name=universe_name,
        run_id=effective_run_id,
    )
    candidates = _prepare_candidate_output(selected, effective_run_id, paths.current_candidates_report)
    if candidates.empty:
        warnings.append("No candidates passed current-candidate selection filters.")

    audit_metadata = _audit_metadata(
        decision_date=as_of_date,
        decision_time=decision_time,
        universe_name=universe_name,
        factor_dataset=factor_dataset,
        scored_dataset=scored_dataset,
        candidates=candidates,
    )
    audit_metadata.update(preflight.metadata_fields())
    config_summary = _config_summary(settings, effective_top_n, effective_run_id)
    config_summary["snapshot_quality_preflight"] = preflight.metadata_fields()
    result = CurrentCandidateResult(
        decision_date=as_of_date,
        decision_time=decision_time,
        universe_name=universe_name,
        top_n=effective_top_n,
        run_id=effective_run_id,
        factor_dataset_row_count=len(factor_dataset),
        scored_dataset_row_count=len(scored_dataset),
        candidate_count=len(candidates),
        candidates=candidates,
        artifact_paths=paths.as_dict(),
        snapshot_quality_status=preflight.status,
        snapshot_quality_report_path=preflight.report_path,
        warnings=warnings,
        known_limitations=CURRENT_CANDIDATE_LIMITATIONS,
        factor_dataset=factor_dataset,
        scored_dataset=scored_dataset,
        audit_metadata=audit_metadata,
        config_summary=config_summary,
    )
    if settings.current_candidates.write_artifacts:
        write_current_candidate_artifacts(result)
    return result


def generate_current_candidate_run_id(
    decision_date: str | pd.Timestamp,
    universe_name: str,
    top_n: int,
    config_version: str = "mvp",
    snapshot_manifest_path: str | Path | None = None,
) -> str:
    """Generate a deterministic short id for a current-candidate run."""

    payload = {
        "decision_date": str(_normalize_date(decision_date).date()),
        "universe_name": universe_name,
        "top_n": int(top_n),
        "config_version": config_version,
        "snapshot_manifest_path": str(snapshot_manifest_path) if snapshot_manifest_path is not None else "",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def resolve_current_candidate_artifact_paths(
    output_dir: str | Path,
    decision_date: str | pd.Timestamp,
    universe_name: str,
    run_id: str,
) -> CurrentCandidateArtifactPaths:
    """Resolve stable current-candidate artifact paths."""

    safe_universe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in universe_name)
    folder = Path(output_dir) / f"{_normalize_date(decision_date).date()}_{safe_universe}_{run_id}"
    return CurrentCandidateArtifactPaths(
        artifact_dir=folder,
        current_candidates_report=folder / "current_candidates_report.md",
        factor_dataset=folder / "factor_dataset.csv",
        scored_dataset=folder / "scored_dataset.csv",
        candidates=folder / "candidates.csv",
        metadata=folder / "metadata.json",
    )


def write_current_candidate_artifacts(result: CurrentCandidateResult) -> CurrentCandidateArtifactPaths:
    """Write current-candidate markdown, CSV, and metadata artifacts."""

    paths = CurrentCandidateArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.factor_dataset, paths.factor_dataset)
    _export_dataframe(result.scored_dataset, paths.scored_dataset)
    _export_dataframe(_candidate_export_frame(result.candidates), paths.candidates)
    metadata = build_current_candidate_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_report.write_text(render_current_candidate_report(result, paths, metadata), encoding="utf-8")
    return paths


def build_current_candidate_metadata(
    result: CurrentCandidateResult,
    paths: CurrentCandidateArtifactPaths,
) -> dict[str, Any]:
    """Build metadata.json content for a current-candidate run."""

    return {
        "decision_date": result.decision_date,
        "decision_time": result.decision_time,
        "universe_name": result.universe_name,
        "top_n": result.top_n,
        "run_id": result.run_id,
        "created_at": _metadata_created_at(result.decision_date),
        "config_summary": result.config_summary,
        "row_counts": {
            "factor_dataset": result.factor_dataset_row_count,
            "scored_dataset": result.scored_dataset_row_count,
            "candidates": result.candidate_count,
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "snapshot_quality": {
            "status": result.snapshot_quality_status,
            "report_path": str(result.snapshot_quality_report_path) if result.snapshot_quality_report_path is not None else "",
        },
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_current_candidate_report(
    result: CurrentCandidateResult,
    paths: CurrentCandidateArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render a markdown current-candidate report."""

    candidates = _candidate_export_frame(result.candidates)
    lines = [
        f"# Current Candidate Report: {result.decision_date.date()} / {result.universe_name}",
        "",
        "No broker or live trading integration was invoked. This is a local research and paper-trading input report only.",
        "",
        "## Candidate Metadata",
        "",
        _dict_table(
            {
                "decision_date": result.decision_date.date(),
                "decision_time": result.decision_time,
                "universe_name": result.universe_name,
                "run_id": result.run_id,
                "top_n": result.top_n,
                "candidate_count": result.candidate_count,
                "artifact_dir": paths.artifact_dir,
                "report_path": paths.current_candidates_report,
            }
        ),
        "",
        "## Config Summary",
        "",
        _dict_table(result.config_summary),
        "",
        "## Snapshot Quality Preflight",
        "",
        _dict_table(
            {
                "enabled": result.audit_metadata.get("snapshot_quality_preflight_enabled"),
                "status": result.snapshot_quality_status,
                "report_path": result.snapshot_quality_report_path,
                "gate_id": result.audit_metadata.get("snapshot_quality_gate_id"),
            }
        ),
        "",
        "## Data Audit Summary",
        "",
        _dict_table(result.audit_metadata),
        "",
        "## Dataset Counts",
        "",
        _dict_table(metadata["row_counts"]),
        "",
        "## Candidate Table",
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
        "## Paper Trading Compatibility",
        "",
        "Use `candidates.csv` with `paper-daily`, then review decisions before entering manual fills.",
        "",
        _dict_table({"candidates_csv": paths.candidates, "source_run_id": result.run_id}),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _prepare_candidate_output(selected: pd.DataFrame, run_id: str, report_path: Path) -> pd.DataFrame:
    frame = selected.copy(deep=True)
    if frame.empty:
        return _candidate_export_frame(frame)
    if "rank" not in frame.columns:
        frame.insert(0, "rank", range(1, len(frame) + 1))
    if "action" not in frame.columns and "score_action" in frame.columns:
        frame["action"] = frame["score_action"]
    for column, value in {
        "current_candidate_run_id": run_id,
        "source_run_id": run_id,
        "source_report_path": str(report_path),
    }.items():
        frame[column] = value
    return _candidate_export_frame(frame)


def _candidate_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = frame.copy(deep=True)
    if candidates.empty:
        return pd.DataFrame(columns=_candidate_columns())
    if "rank" not in candidates.columns:
        candidates.insert(0, "rank", range(1, len(candidates) + 1))
    if "action" not in candidates.columns and "score_action" in candidates.columns:
        candidates["action"] = candidates["score_action"]
    return _order_columns(candidates, _candidate_columns())


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
        "current_candidate_run_id",
        "source_run_id",
        "source_report_path",
    ]


def _snapshot_dataset_paths(snapshot_manifest_path: str | Path | None) -> dict[str, Path]:
    if snapshot_manifest_path is None:
        return {}
    manifest = load_snapshot_manifest(snapshot_manifest_path)
    base_dir = Path(manifest["manifest_path"]).parent
    resolved: dict[str, Path] = {}
    for dataset_type, raw_path in manifest["dataset_paths"].items():
        path = Path(raw_path)
        if not path.is_absolute() and not path.exists():
            path = base_dir / path
        resolved[str(dataset_type)] = path
    return resolved


def _settings_with_manifest_preflight(
    settings: Settings,
    snapshot_manifest_path: str | Path | None,
    enable_snapshot_preflight: bool | None,
) -> Settings:
    if enable_snapshot_preflight is False:
        return settings.model_copy(
            update={
                "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(update={"enabled": False})
            }
        )
    if enable_snapshot_preflight is True:
        updates: dict[str, Any] = {"enabled": True}
        if snapshot_manifest_path is not None:
            updates["manifest_path"] = Path(snapshot_manifest_path)
        return settings.model_copy(
            update={
                "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(update=updates)
            }
        )
    if snapshot_manifest_path is not None and settings.current_candidates.enable_snapshot_quality_preflight:
        return settings.model_copy(
            update={
                "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(
                    update={"enabled": True, "manifest_path": Path(snapshot_manifest_path)}
                )
            }
        )
    if not settings.current_candidates.enable_snapshot_quality_preflight:
        return settings.model_copy(
            update={
                "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(update={"enabled": False})
            }
        )
    return settings


def _settings_with_output_dir(settings: Settings, output_dir: str | Path | None) -> Settings:
    if output_dir is None:
        return settings
    return settings.model_copy(
        update={
            "current_candidates": settings.current_candidates.model_copy(update={"output_dir": Path(output_dir)})
        }
    )


def _audit_metadata(
    *,
    decision_date: pd.Timestamp,
    decision_time: pd.Timestamp,
    universe_name: str,
    factor_dataset: pd.DataFrame,
    scored_dataset: pd.DataFrame,
    candidates: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "decision_date": decision_date,
        "decision_time": decision_time,
        "universe_name": universe_name,
        "point_in_time_rule": "available_time <= decision_time",
        "latest_market_available_time": _max_timestamp(factor_dataset, "latest_market_available_time"),
        "latest_universe_available_time": _max_timestamp(factor_dataset, "universe_available_time"),
        "factor_dataset_rows": len(factor_dataset),
        "scored_dataset_rows": len(scored_dataset),
        "candidate_rows": len(candidates),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "current_candidate_generation_only": True,
    }


def _config_summary(settings: Settings, top_n: int, run_id: str) -> dict[str, Any]:
    return {
        "top_n": top_n,
        "run_id": run_id,
        "config_version": settings.current_candidates.config_version,
        "min_action": settings.current_candidates.min_action,
        "min_final_score": settings.current_candidates.min_final_score,
        "factor_dataset": settings.factor_dataset.model_dump(),
        "score_engine_weights": settings.score_engine.weights,
        "candidate_selection": {
            "exclude_blocked": settings.candidate_selection.exclude_blocked,
            "top_n": top_n,
            "min_action": settings.current_candidates.min_action,
            "min_final_score": settings.current_candidates.min_final_score,
        },
    }


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _max_timestamp(frame: pd.DataFrame, column: str) -> pd.Timestamp | None:
    if column not in frame.columns or frame.empty:
        return None
    values = pd.to_datetime(frame[column], errors="coerce").dropna()
    if values.empty:
        return None
    return pd.Timestamp(values.max())


def _metadata_created_at(decision_date: pd.Timestamp) -> str:
    if pd.notna(decision_date):
        return decision_date.isoformat()
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _order_columns(frame: pd.DataFrame, preferred: list[str]) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in preferred:
        if column not in output.columns:
            output[column] = pd.NA
    remaining = [column for column in output.columns if column not in preferred]
    return output[[*preferred, *remaining]]


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


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


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
    if isinstance(value, (list, tuple, set)):
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
