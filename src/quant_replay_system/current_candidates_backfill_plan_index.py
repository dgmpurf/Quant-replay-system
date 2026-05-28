"""Local-only index for current-candidates backfill plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


WARMUP_AWARE_COLUMNS = {
    "warmup_trading_days",
    "warmup_available",
    "earliest_required_warmup_date",
    "first_available_market_date",
    "warmup_start_date",
    "warmup_reason",
    "candidate_generation_feasible",
    "candidate_generation_blocker",
}

BACKFILL_PLAN_INDEX_COLUMNS = [
    "artifact_type",
    "plan_id",
    "status",
    "universe",
    "selection_profile",
    "selected_date_count",
    "first_signal_date",
    "last_signal_date",
    "cache_start_date",
    "cache_end_date",
    "warmup_aware",
    "warmup_trading_days",
    "warmup_feasible_count",
    "forward_1d_available_count",
    "forward_3d_available_count",
    "forward_5d_available_count",
    "forward_10d_available_count",
    "max_forward_horizon",
    "source_policy",
    "recommended_source_filter",
    "recommended_upstream_filter",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "report_path",
    "plan_csv_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local current-candidates backfill plan artifacts only.",
    "Does not run current-candidates, data-pipeline, snapshot generation, or forward-return labeling.",
    "Does not mutate market cache, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanIndexPaths:
    artifact_dir: Path
    current_candidates_backfill_plan_index_csv: Path
    current_candidates_backfill_plan_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_plan_index_csv": self.current_candidates_backfill_plan_index_csv,
            "current_candidates_backfill_plan_index_report": self.current_candidates_backfill_plan_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_current_candidates_backfill_plan_artifacts(
    root: str | Path = "outputs/reports/current_candidates_backfill_plan",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_current_candidates_backfill_plan_index(
    *,
    root: str | Path = "outputs/reports/current_candidates_backfill_plan",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_plan/index",
    include_missing_metadata: bool = False,
) -> CurrentCandidatesBackfillPlanIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_current_candidates_backfill_plan_index_paths(output_dir)
    result = CurrentCandidatesBackfillPlanIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=INDEX_LIMITATIONS,
        audit_metadata={
            "root_dir": effective_root,
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "current_candidates_executed": False,
            "data_pipeline_executed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "plan_artifacts_only": True,
        },
    )
    write_current_candidates_backfill_plan_index(result)
    return result


def resolve_current_candidates_backfill_plan_index_paths(
    output_dir: str | Path,
) -> CurrentCandidatesBackfillPlanIndexPaths:
    artifact_dir = Path(output_dir)
    return CurrentCandidatesBackfillPlanIndexPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_plan_index_csv=artifact_dir / "current_candidates_backfill_plan_index.csv",
        current_candidates_backfill_plan_index_report=artifact_dir / "current_candidates_backfill_plan_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_plan_index(result: CurrentCandidatesBackfillPlanIndexResult) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillPlanIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.current_candidates_backfill_plan_index_csv, index=False)
    metadata = build_current_candidates_backfill_plan_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_plan_index_report.write_text(
        render_current_candidates_backfill_plan_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_plan_index_metadata(
    result: CurrentCandidatesBackfillPlanIndexResult,
    paths: CurrentCandidatesBackfillPlanIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, length=12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, or network/API call was invoked.",
    }


def render_current_candidates_backfill_plan_index_report(
    result: CurrentCandidatesBackfillPlanIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# Current-Candidates Backfill Plan Index",
            "",
            "No live trading, broker API, order placement, message delivery, or network/API call was invoked. This index scans local backfill plan artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Plans",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "plan_id",
                    "status",
                    "selected_date_count",
                    "first_signal_date",
                    "last_signal_date",
                    "warmup_trading_days",
                    "warmup_feasible_count",
                    "forward_10d_available_count",
                    "report_path",
                ],
            ),
            "",
            "## Warnings",
            "",
            _warnings_section(result.warnings),
            "",
        ]
    )


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"Current-candidates backfill plan root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read current-candidates backfill plan metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        plan_id = _string_or_empty(metadata.get("plan_id"))
        if not plan_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    plan_csv = Path(output_files.get("plan_csv") or artifact_dir / "current_candidates_backfill_plan.csv")
    report = Path(output_files.get("report") or artifact_dir / "current_candidates_backfill_plan_report.md")
    plan = _read_plan_csv(plan_csv)
    horizon_counts = metadata.get("horizon_feasibility_counts") if isinstance(metadata.get("horizon_feasibility_counts"), dict) else {}
    warmup_counts = metadata.get("warmup_feasibility_counts") if isinstance(metadata.get("warmup_feasibility_counts"), dict) else {}
    return {
        "artifact_type": "CURRENT_CANDIDATES_BACKFILL_PLAN",
        "plan_id": _string_or_empty(metadata.get("plan_id")) or artifact_dir.name,
        "status": _string_or_empty(metadata.get("status")) or "READY",
        "universe": _string_or_empty(metadata.get("universe")) or _first_value(plan, "universe"),
        "selection_profile": _string_or_empty(metadata.get("selection_profile")) or _first_value(plan, "selection_profile"),
        "selected_date_count": _to_int(metadata.get("selected_date_count", len(plan))),
        "first_signal_date": _string_or_empty(metadata.get("first_signal_date")) or _first_value(plan, "signal_date"),
        "last_signal_date": _string_or_empty(metadata.get("last_signal_date")) or _last_value(plan, "signal_date"),
        "cache_start_date": _string_or_empty(metadata.get("cache_start_date_in_scope")) or _first_value(plan, "cache_start_date"),
        "cache_end_date": _string_or_empty(metadata.get("cache_end_date_in_scope")) or _last_value(plan, "cache_end_date"),
        "warmup_aware": _is_warmup_aware_plan(plan),
        "warmup_trading_days": _to_int(metadata.get("warmup_trading_days", _first_value(plan, "warmup_trading_days"))),
        "warmup_feasible_count": _to_int(warmup_counts.get("warmup_available", _true_count(plan, "warmup_available"))),
        "forward_1d_available_count": _to_int(horizon_counts.get("forward_1d_available", _true_count(plan, "forward_1d_available"))),
        "forward_3d_available_count": _to_int(horizon_counts.get("forward_3d_available", _true_count(plan, "forward_3d_available"))),
        "forward_5d_available_count": _to_int(horizon_counts.get("forward_5d_available", _true_count(plan, "forward_5d_available"))),
        "forward_10d_available_count": _to_int(horizon_counts.get("forward_10d_available", _true_count(plan, "forward_10d_available"))),
        "max_forward_horizon": _to_int(_max_value(plan, "max_forward_horizon")),
        "source_policy": _string_or_empty(metadata.get("source_policy")) or _first_value(plan, "source_policy"),
        "recommended_source_filter": _string_or_empty(metadata.get("recommended_source_filter")) or _first_value(plan, "recommended_source_filter"),
        "recommended_upstream_filter": _string_or_empty(metadata.get("recommended_upstream_filter")) or _first_value(plan, "recommended_upstream_filter"),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", _all_true(plan, "no_live_trading"))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", _all_true(plan, "no_broker_api"))),
        "no_order_placement": _to_bool(metadata.get("no_order_placement", _all_true(plan, "no_order_placement"))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", _all_true(plan, "no_message_sent"))),
        "report_path": str(report),
        "plan_csv_path": str(plan_csv),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in BACKFILL_PLAN_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "CURRENT_CANDIDATES_BACKFILL_PLAN",
            "plan_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "current_candidates_backfill_plan_report.md"),
            "plan_csv_path": str(artifact_dir / "current_candidates_backfill_plan.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _read_plan_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, keep_default_na=False, dtype={"symbols": str})
    except Exception:
        return pd.DataFrame()


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=BACKFILL_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in BACKFILL_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output["warmup_aware"] = output["warmup_aware"].map(_to_bool).astype(object)
    return output[BACKFILL_PLAN_INDEX_COLUMNS].sort_values(["created_at", "plan_id"]).reset_index(drop=True)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].dropna().tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _artifact_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return _string_or_empty(frame[column].iloc[0])


def _last_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return _string_or_empty(frame[column].iloc[-1])


def _max_value(frame: pd.DataFrame, column: str) -> Any:
    if frame.empty or column not in frame.columns:
        return ""
    return pd.to_numeric(frame[column], errors="coerce").max()


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].map(_to_bool).all())


def _is_warmup_aware_plan(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return False
    return WARMUP_AWARE_COLUMNS.issubset(set(frame.columns))


def _to_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(f"- {key}: {_format_markdown_value(value)}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 100) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    return "" if value is None else str(value).replace("\n", " ").replace("|", "\\|")
