"""Local-only index for guarded PIT universe export staging artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS = [
    "artifact_type",
    "staging_id",
    "export_readiness_id",
    "review_id",
    "status",
    "staging_status",
    "row_count",
    "export_ready_input_count",
    "staged_row_count",
    "blocked_count",
    "source_is_diagnostic",
    "no_ready_rows",
    "duplicate_key_count",
    "missing_required_columns_count",
    "would_write_data_raw",
    "would_write_data_processed",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "staging_only",
    "report_path",
    "staging_csv_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class PitUniverseExportStagingIndexPaths:
    artifact_dir: Path
    pit_universe_export_staging_index_csv: Path
    pit_universe_export_staging_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_export_staging_index_csv": self.pit_universe_export_staging_index_csv,
            "pit_universe_export_staging_index_report": self.pit_universe_export_staging_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseExportStagingIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def scan_pit_universe_export_staging_artifacts(
    root: str | Path = "outputs/reports/point_in_time_universe_export_staging",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_pit_universe_export_staging_index(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_export_staging",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_export_staging/index",
    include_missing_metadata: bool = False,
) -> PitUniverseExportStagingIndexResult:
    rows, warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_pit_universe_export_staging_index_paths(output_dir)
    result = PitUniverseExportStagingIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        audit_metadata={
            "root_dir": str(root),
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "broker_api_invoked": False,
            "message_sent": False,
            "pit_universe_export_staging_artifacts_only": True,
        },
    )
    write_pit_universe_export_staging_index(result)
    return result


def resolve_pit_universe_export_staging_index_paths(output_dir: str | Path) -> PitUniverseExportStagingIndexPaths:
    artifact_dir = Path(output_dir)
    return PitUniverseExportStagingIndexPaths(
        artifact_dir=artifact_dir,
        pit_universe_export_staging_index_csv=artifact_dir / "pit_universe_export_staging_index.csv",
        pit_universe_export_staging_index_report=artifact_dir / "pit_universe_export_staging_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_export_staging_index(result: PitUniverseExportStagingIndexResult) -> dict[str, Path]:
    paths = PitUniverseExportStagingIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.pit_universe_export_staging_index_csv, index=False)
    metadata = {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, 12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, network/API, "
            "LLM/API, or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_export_staging_index_report.write_text(render_pit_universe_export_staging_index_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_export_staging_index_report(result: PitUniverseExportStagingIndexResult) -> str:
    return "\n".join(
        [
            "# PIT Universe Export Staging Index",
            "",
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
            "",
            f"- artifact_count: {result.artifact_count}",
            "",
            result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No rows.",
        ]
    )


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"PIT universe export staging root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read PIT universe export staging metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        staging_id = _text(metadata.get("staging_id"))
        if not staging_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    staging_csv = Path(output_files.get("staging_csv") or artifact_dir / "pit_universe_export_staging.csv")
    report = Path(output_files.get("report") or artifact_dir / "pit_universe_export_staging_report.md")
    staging = _read_csv(staging_csv)
    return {
        "artifact_type": "PIT_UNIVERSE_EXPORT_STAGING",
        "staging_id": _text(metadata.get("staging_id")) or artifact_dir.name,
        "export_readiness_id": _text(metadata.get("export_readiness_id")) or _first_text(staging, "export_readiness_id"),
        "review_id": _text(metadata.get("review_id")) or _first_text(staging, "review_id"),
        "status": _text(metadata.get("status")) or "WARN",
        "staging_status": _text(metadata.get("staging_status")) or _first_text(staging, "staging_status"),
        "row_count": _to_int(metadata.get("row_count", len(staging))),
        "export_ready_input_count": _to_int(metadata.get("export_ready_input_count", _true_count(staging, "export_ready"))),
        "staged_row_count": _to_int(metadata.get("staged_row_count", _staged_count(staging))),
        "blocked_count": _to_int(metadata.get("blocked_count", _blocked_count(staging))),
        "source_is_diagnostic": _to_bool(metadata.get("source_is_diagnostic", _any_true(staging, "source_is_diagnostic"))),
        "no_ready_rows": _to_bool(metadata.get("no_ready_rows")),
        "duplicate_key_count": _to_int(metadata.get("duplicate_key_count")),
        "missing_required_columns_count": _to_int(metadata.get("missing_required_columns_count")),
        "would_write_data_raw": _to_bool(metadata.get("would_write_data_raw")),
        "would_write_data_processed": _to_bool(metadata.get("would_write_data_processed")),
        "no_current_candidates_generated": _to_bool(metadata.get("no_current_candidates_generated")),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built")),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "staging_only": _to_bool(metadata.get("staging_only")),
        "report_path": str(report),
        "staging_csv_path": str(staging_csv),
        "metadata_path": str(metadata_path),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "PIT_UNIVERSE_EXPORT_STAGING",
            "staging_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "pit_universe_export_staging_report.md"),
            "staging_csv_path": str(artifact_dir / "pit_universe_export_staging.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in [
        "source_is_diagnostic",
        "no_ready_rows",
        "would_write_data_raw",
        "would_write_data_processed",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "staging_only",
    ]:
        output[column] = output[column].map(_to_bool).astype(object)
    return output[PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS].sort_values(["created_at", "staging_id"]).reset_index(drop=True)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _staged_count(frame: pd.DataFrame) -> int:
    if frame.empty or "staging_status" not in frame.columns:
        return 0
    return int(frame["staging_status"].astype(str).eq("EXPORT_STAGING_DRY_RUN_CREATED").sum())


def _blocked_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return len(frame) - _staged_count(frame)


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _any_true(frame: pd.DataFrame, column: str) -> bool:
    return _true_count(frame, column) > 0


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return next((_text(value) for value in frame[column].tolist() if _text(value)), "")


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


def _text(value: Any) -> str:
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
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
