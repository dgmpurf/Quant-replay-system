"""Local-only index for PIT universe overlay export-readiness artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS = [
    "artifact_type",
    "export_readiness_id",
    "review_id",
    "status",
    "readiness_status",
    "row_count",
    "approved_count",
    "export_ready_count",
    "blocked_count",
    "no_approved_rows",
    "unresolved_survivorship_warning_count",
    "missing_required_columns_count",
    "duplicate_key_count",
    "would_write_data_raw",
    "would_write_data_processed",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "report_path",
    "readiness_csv_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local PIT universe overlay export-readiness artifacts only.",
    "Does not export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessIndexPaths:
    artifact_dir: Path
    pit_universe_overlay_export_readiness_index_csv: Path
    pit_universe_overlay_export_readiness_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_overlay_export_readiness_index_csv": self.pit_universe_overlay_export_readiness_index_csv,
            "pit_universe_overlay_export_readiness_index_report": self.pit_universe_overlay_export_readiness_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_pit_universe_overlay_export_readiness_artifacts(
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_export_readiness",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_pit_universe_overlay_export_readiness_index(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_export_readiness",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_export_readiness/index",
    include_missing_metadata: bool = False,
) -> PitUniverseOverlayExportReadinessIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_pit_universe_overlay_export_readiness_index_paths(output_dir)
    result = PitUniverseOverlayExportReadinessIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=INDEX_LIMITATIONS,
        audit_metadata={
            "root_dir": effective_root,
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
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
            "pit_universe_overlay_export_readiness_artifacts_only": True,
        },
    )
    write_pit_universe_overlay_export_readiness_index(result)
    return result


def resolve_pit_universe_overlay_export_readiness_index_paths(
    output_dir: str | Path,
) -> PitUniverseOverlayExportReadinessIndexPaths:
    artifact_dir = Path(output_dir)
    return PitUniverseOverlayExportReadinessIndexPaths(
        artifact_dir=artifact_dir,
        pit_universe_overlay_export_readiness_index_csv=artifact_dir
        / "pit_universe_overlay_export_readiness_index.csv",
        pit_universe_overlay_export_readiness_index_report=artifact_dir
        / "pit_universe_overlay_export_readiness_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_overlay_export_readiness_index(
    result: PitUniverseOverlayExportReadinessIndexResult,
) -> dict[str, Path]:
    paths = PitUniverseOverlayExportReadinessIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.pit_universe_overlay_export_readiness_index_csv, index=False)
    metadata = build_pit_universe_overlay_export_readiness_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_overlay_export_readiness_index_report.write_text(
        render_pit_universe_overlay_export_readiness_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_overlay_export_readiness_index_metadata(
    result: PitUniverseOverlayExportReadinessIndexResult,
    paths: PitUniverseOverlayExportReadinessIndexPaths,
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
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, "
            "or cache mutation was invoked."
        ),
    }


def render_pit_universe_overlay_export_readiness_index_report(
    result: PitUniverseOverlayExportReadinessIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# PIT Universe Overlay Export Readiness Index",
            "",
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked. This index scans local export-readiness artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Export Readiness Runs",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "export_readiness_id",
                    "review_id",
                    "readiness_status",
                    "approved_count",
                    "export_ready_count",
                    "blocked_count",
                    "no_approved_rows",
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
        return rows, [f"PIT universe overlay export-readiness root does not exist: {root}"]
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
            warnings.append(f"Could not read PIT universe overlay export-readiness metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        export_readiness_id = _string_or_empty(metadata.get("export_readiness_id"))
        if not export_readiness_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    readiness_csv = Path(output_files.get("readiness_csv") or artifact_dir / "pit_universe_overlay_export_readiness.csv")
    report = Path(output_files.get("report") or artifact_dir / "pit_universe_overlay_export_readiness_report.md")
    readiness = _read_csv(readiness_csv)
    return {
        "artifact_type": "PIT_UNIVERSE_OVERLAY_EXPORT_READINESS",
        "export_readiness_id": _string_or_empty(metadata.get("export_readiness_id")) or artifact_dir.name,
        "review_id": _string_or_empty(metadata.get("review_id")) or _first_text(readiness, "review_id"),
        "status": _string_or_empty(metadata.get("status")) or "WARN",
        "readiness_status": _string_or_empty(metadata.get("readiness_status"))
        or _first_text(readiness, "export_readiness_status"),
        "row_count": _to_int(metadata.get("row_count", len(readiness))),
        "approved_count": _to_int(metadata.get("approved_count", _status_count(readiness, "APPROVED_FOR_PIT_UNIVERSE"))),
        "export_ready_count": _to_int(metadata.get("export_ready_count", _true_count(readiness, "export_ready"))),
        "blocked_count": _to_int(metadata.get("blocked_count", _blocked_count(readiness))),
        "no_approved_rows": _to_bool(metadata.get("no_approved_rows", _status_count(readiness, "APPROVED_FOR_PIT_UNIVERSE") == 0)),
        "unresolved_survivorship_warning_count": _to_int(
            metadata.get("unresolved_survivorship_warning_count", _unresolved_survivorship_count(readiness))
        ),
        "missing_required_columns_count": _to_int(
            metadata.get("missing_required_columns_count", _missing_required_columns_count(readiness))
        ),
        "duplicate_key_count": _to_int(metadata.get("duplicate_key_count")),
        "would_write_data_raw": _to_bool(metadata.get("would_write_data_raw")),
        "would_write_data_processed": _to_bool(metadata.get("would_write_data_processed")),
        "no_current_candidates_generated": _to_bool(
            metadata.get("no_current_candidates_generated", not _to_bool(metadata.get("current_candidates_executed")))
        ),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built", not _to_bool(metadata.get("snapshot_manifest_built")))),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels", not _to_bool(metadata.get("forward_returns_computed")))),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", _all_true(readiness, "no_live_trading"))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", _all_true(readiness, "no_broker_api"))),
        "no_order_placement": _to_bool(metadata.get("no_order_placement", _all_true(readiness, "no_order_placement"))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", _all_true(readiness, "no_message_sent"))),
        "report_path": str(report),
        "readiness_csv_path": str(readiness_csv),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "PIT_UNIVERSE_OVERLAY_EXPORT_READINESS",
            "export_readiness_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "pit_universe_overlay_export_readiness_report.md"),
            "readiness_csv_path": str(artifact_dir / "pit_universe_overlay_export_readiness.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    bool_columns = [
        "no_approved_rows",
        "would_write_data_raw",
        "would_write_data_processed",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
    ]
    for column in bool_columns:
        output[column] = output[column].map(_to_bool).astype(object)
    return output[PIT_UNIVERSE_OVERLAY_EXPORT_READINESS_INDEX_COLUMNS].sort_values(
        ["created_at", "export_readiness_id"]
    ).reset_index(drop=True)


def _status_count(frame: pd.DataFrame, status: str) -> int:
    if frame.empty or "review_status" not in frame.columns:
        return 0
    return int(frame["review_status"].map(_string_or_empty).str.upper().eq(status).sum())


def _blocked_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    if "export_ready" in frame.columns:
        return int((~frame["export_ready"].map(_to_bool)).sum())
    return len(frame)


def _missing_required_columns_count(frame: pd.DataFrame) -> int:
    if frame.empty or "required_column_missing_count" not in frame.columns:
        return 0
    return int((frame["required_column_missing_count"].map(_to_int) > 0).sum())


def _unresolved_survivorship_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    warning = frame.get("survivorship_bias_warning", pd.Series([False] * len(frame))).map(_to_bool)
    resolved = frame.get("survivorship_bias_resolved", pd.Series([False] * len(frame))).map(_to_bool)
    return int((warning & ~resolved).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].map(_to_bool).all())


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    values = [_string_or_empty(value) for value in frame[column].tolist()]
    return next((value for value in values if value), "")


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
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


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
