"""Local-only index for point-in-time universe overlay plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS = [
    "artifact_type",
    "overlay_plan_id",
    "status",
    "row_count",
    "signal_date_count",
    "symbol_count",
    "needs_manual_review_count",
    "valid_for_signal_date_count",
    "survivorship_bias_warning_count",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
    "report_path",
    "plan_csv_path",
    "template_csv_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local point-in-time universe overlay plan artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanIndexPaths:
    artifact_dir: Path
    point_in_time_universe_overlay_plan_index_csv: Path
    point_in_time_universe_overlay_plan_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "point_in_time_universe_overlay_plan_index_csv": self.point_in_time_universe_overlay_plan_index_csv,
            "point_in_time_universe_overlay_plan_index_report": self.point_in_time_universe_overlay_plan_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_point_in_time_universe_overlay_plan_artifacts(
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_plan",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_point_in_time_universe_overlay_plan_index(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_plan",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_plan/index",
    include_missing_metadata: bool = False,
) -> PointInTimeUniverseOverlayPlanIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_point_in_time_universe_overlay_plan_index_paths(output_dir)
    result = PointInTimeUniverseOverlayPlanIndexResult(
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
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "pit_universe_overlay_plan_artifacts_only": True,
        },
    )
    write_point_in_time_universe_overlay_plan_index(result)
    return result


def resolve_point_in_time_universe_overlay_plan_index_paths(
    output_dir: str | Path,
) -> PointInTimeUniverseOverlayPlanIndexPaths:
    artifact_dir = Path(output_dir)
    return PointInTimeUniverseOverlayPlanIndexPaths(
        artifact_dir=artifact_dir,
        point_in_time_universe_overlay_plan_index_csv=artifact_dir / "point_in_time_universe_overlay_plan_index.csv",
        point_in_time_universe_overlay_plan_index_report=artifact_dir / "point_in_time_universe_overlay_plan_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_point_in_time_universe_overlay_plan_index(
    result: PointInTimeUniverseOverlayPlanIndexResult,
) -> dict[str, Path]:
    paths = PointInTimeUniverseOverlayPlanIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.point_in_time_universe_overlay_plan_index_csv, index=False)
    metadata = build_point_in_time_universe_overlay_plan_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.point_in_time_universe_overlay_plan_index_report.write_text(
        render_point_in_time_universe_overlay_plan_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_point_in_time_universe_overlay_plan_index_metadata(
    result: PointInTimeUniverseOverlayPlanIndexResult,
    paths: PointInTimeUniverseOverlayPlanIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, length=12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
            "order placement, message delivery, LLM API, or external API was invoked."
        ),
    }


def render_point_in_time_universe_overlay_plan_index_report(
    result: PointInTimeUniverseOverlayPlanIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# Point-in-Time Universe Overlay Plan Index",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This index scans local PIT universe overlay plan artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Overlay Plans",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "overlay_plan_id",
                    "row_count",
                    "signal_date_count",
                    "symbol_count",
                    "needs_manual_review_count",
                    "survivorship_bias_warning_count",
                    "valid_for_signal_date_count",
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
        return rows, [f"PIT universe overlay plan root does not exist: {root}"]
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
            warnings.append(f"Could not read PIT universe overlay plan metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        overlay_plan_id = _string_or_empty(metadata.get("overlay_plan_id"))
        if not overlay_plan_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    plan_csv = Path(output_files.get("overlay_plan_csv") or artifact_dir / "point_in_time_universe_overlay_plan.csv")
    template_csv = Path(
        output_files.get("overlay_template_csv") or artifact_dir / "point_in_time_universe_overlay_template.csv"
    )
    report = Path(output_files.get("report") or artifact_dir / "point_in_time_universe_overlay_plan_report.md")
    plan = _read_plan_csv(plan_csv)
    return {
        "artifact_type": "PIT_UNIVERSE_OVERLAY_PLAN",
        "overlay_plan_id": _string_or_empty(metadata.get("overlay_plan_id")) or artifact_dir.name,
        "status": _string_or_empty(metadata.get("status")) or "WARN",
        "row_count": _to_int(metadata.get("row_count", len(plan))),
        "signal_date_count": _to_int(metadata.get("signal_date_count", _nunique(plan, "signal_date"))),
        "symbol_count": _to_int(metadata.get("symbol_count", _nunique(plan, "symbol"))),
        "needs_manual_review_count": _needs_manual_review_count(plan, metadata),
        "valid_for_signal_date_count": _to_int(
            metadata.get("valid_for_signal_date_count", _true_count(plan, "valid_for_signal_date"))
        ),
        "survivorship_bias_warning_count": _to_int(
            metadata.get("survivorship_bias_warning_count", _true_count(plan, "survivorship_bias_warning"))
        ),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", _all_true(plan, "no_live_trading"))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", _all_true(plan, "no_broker_api"))),
        "no_order_placement": _to_bool(metadata.get("no_order_placement", _all_true(plan, "no_order_placement"))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", _all_true(plan, "no_message_sent"))),
        "plan_only": _to_bool(metadata.get("plan_only", _all_true(plan, "plan_only"))),
        "report_path": str(report),
        "plan_csv_path": str(plan_csv),
        "template_csv_path": str(template_csv),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "PIT_UNIVERSE_OVERLAY_PLAN",
            "overlay_plan_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "point_in_time_universe_overlay_plan_report.md"),
            "plan_csv_path": str(artifact_dir / "point_in_time_universe_overlay_plan.csv"),
            "template_csv_path": str(artifact_dir / "point_in_time_universe_overlay_template.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _read_plan_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in ["no_live_trading", "no_broker_api", "no_order_placement", "no_message_sent", "plan_only"]:
        output[column] = output[column].map(_to_bool).astype(object)
    return output[PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS].sort_values(
        ["created_at", "overlay_plan_id"]
    ).reset_index(drop=True)


def _needs_manual_review_count(plan: pd.DataFrame, metadata: dict[str, Any]) -> int:
    raw_counts = metadata.get("review_status_counts")
    if isinstance(raw_counts, dict) and "NEEDS_MANUAL_REVIEW" in raw_counts:
        return _to_int(raw_counts.get("NEEDS_MANUAL_REVIEW"))
    if plan.empty:
        return 0
    if "review_status" in plan.columns:
        return int(plan["review_status"].map(_string_or_empty).str.upper().eq("NEEDS_MANUAL_REVIEW").sum())
    if "manual_review_required" in plan.columns:
        return _true_count(plan, "manual_review_required")
    return 0


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


def _nunique(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].nunique())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].map(_to_bool).all())


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
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 100) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)
