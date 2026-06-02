"""Local-only index for PIT universe evidence update ingestion artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_INDEX_COLUMNS = [
    "artifact_type",
    "ingestion_id",
    "status",
    "row_count",
    "ready_for_review_update_count",
    "blocked_count",
    "approval_requested_count",
    "approved_ready_count",
    "rejected_ready_count",
    "needs_more_evidence_ready_count",
    "duplicate_identity_count",
    "missing_identity_count",
    "suggested_copy_risk_count",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "ingestion_only",
    "report_path",
    "ingestion_csv_path",
    "review_updates_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local PIT universe evidence update ingestion artifacts only.",
    "Does not apply approvals, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionIndexPaths:
    artifact_dir: Path
    pit_universe_evidence_update_ingestion_index_csv: Path
    pit_universe_evidence_update_ingestion_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_update_ingestion_index_csv": self.pit_universe_evidence_update_ingestion_index_csv,
            "pit_universe_evidence_update_ingestion_index_report": self.pit_universe_evidence_update_ingestion_index_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_pit_universe_evidence_update_ingestion_artifacts(
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_pit_universe_evidence_update_ingestion_index(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion/index",
    include_missing_metadata: bool = False,
) -> PitUniverseEvidenceUpdateIngestionIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_pit_universe_evidence_update_ingestion_index_paths(output_dir)
    result = PitUniverseEvidenceUpdateIngestionIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=INDEX_LIMITATIONS,
        audit_metadata={
            "root_dir": effective_root,
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "approval_applied": False,
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
            "pit_universe_evidence_update_ingestion_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_update_ingestion_index(result)
    return result


def resolve_pit_universe_evidence_update_ingestion_index_paths(
    output_dir: str | Path,
) -> PitUniverseEvidenceUpdateIngestionIndexPaths:
    artifact_dir = Path(output_dir)
    return PitUniverseEvidenceUpdateIngestionIndexPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_update_ingestion_index_csv=artifact_dir
        / "pit_universe_evidence_update_ingestion_index.csv",
        pit_universe_evidence_update_ingestion_index_report=artifact_dir
        / "pit_universe_evidence_update_ingestion_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_update_ingestion_index(
    result: PitUniverseEvidenceUpdateIngestionIndexResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceUpdateIngestionIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.pit_universe_evidence_update_ingestion_index_csv, index=False)
    metadata = build_pit_universe_evidence_update_ingestion_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_update_ingestion_index_report.write_text(
        render_pit_universe_evidence_update_ingestion_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_update_ingestion_index_metadata(
    result: PitUniverseEvidenceUpdateIngestionIndexResult,
    paths: PitUniverseEvidenceUpdateIngestionIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, length=12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": _safety_statement(),
    }


def render_pit_universe_evidence_update_ingestion_index_report(
    result: PitUniverseEvidenceUpdateIngestionIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# PIT Universe Evidence Update Ingestion Index",
            "",
            _safety_statement(),
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Ingestion Runs",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "ingestion_id",
                    "row_count",
                    "ready_for_review_update_count",
                    "blocked_count",
                    "approval_requested_count",
                    "suggested_copy_risk_count",
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
        return rows, [f"PIT universe evidence update ingestion root does not exist: {root}"]
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
            warnings.append(f"Could not read PIT universe evidence update ingestion metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        ingestion_id = _string_or_empty(metadata.get("ingestion_id")) or artifact_dir.name
        if not ingestion_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    ingestion_csv = Path(output_files.get("ingestion_csv") or artifact_dir / "pit_universe_evidence_update_ingestion.csv")
    review_updates = Path(output_files.get("review_updates") or artifact_dir / "pit_universe_review_updates.csv")
    report = Path(output_files.get("report") or artifact_dir / "pit_universe_evidence_update_ingestion_report.md")
    ingestion = _read_csv(ingestion_csv)
    return {
        "artifact_type": "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
        "ingestion_id": _string_or_empty(metadata.get("ingestion_id")) or artifact_dir.name,
        "status": _string_or_empty(metadata.get("status")) or _status_from_counts(metadata),
        "row_count": _int_or(metadata.get("row_count"), len(ingestion)),
        "ready_for_review_update_count": _int_or(
            metadata.get("ready_for_review_update_count"),
            _true_count(ingestion, "ready_for_review_update"),
        ),
        "blocked_count": _int_or(metadata.get("blocked_count"), _false_count(ingestion, "ready_for_review_update")),
        "approval_requested_count": _int_or(metadata.get("approval_requested_count"), _true_count(ingestion, "approval_requested")),
        "approved_ready_count": _int_or(metadata.get("approved_ready_count"), 0),
        "rejected_ready_count": _int_or(metadata.get("rejected_ready_count"), 0),
        "needs_more_evidence_ready_count": _int_or(metadata.get("needs_more_evidence_ready_count"), 0),
        "duplicate_identity_count": _int_or(metadata.get("duplicate_identity_count"), 0),
        "missing_identity_count": _int_or(metadata.get("missing_identity_count"), 0),
        "suggested_copy_risk_count": _int_or(metadata.get("suggested_copy_risk_count"), _true_count(ingestion, "suggested_copy_risk")),
        "no_universe_export": _bool_from_metadata(metadata, "no_universe_export", True),
        "no_data_raw_write": _bool_from_metadata(metadata, "no_data_raw_write", True)
        and not _bool_from_metadata(metadata, "would_write_data_raw", False),
        "no_data_processed_write": _bool_from_metadata(metadata, "no_data_processed_write", True)
        and not _bool_from_metadata(metadata, "would_write_data_processed", False),
        "no_current_candidates_generated": _bool_from_metadata(metadata, "no_current_candidates_generated", True)
        and not _bool_from_metadata(metadata, "current_candidates_executed", False),
        "no_snapshot_built": _bool_from_metadata(metadata, "no_snapshot_built", True)
        and not _bool_from_metadata(metadata, "snapshot_manifest_built", False),
        "no_forward_labels": _bool_from_metadata(metadata, "no_forward_labels", True)
        and not _bool_from_metadata(metadata, "forward_returns_computed", False),
        "no_live_trading": _bool_from_metadata(metadata, "no_live_trading", True)
        and not _bool_from_metadata(metadata, "live_trading_enabled", False),
        "no_broker_api": _bool_from_metadata(metadata, "no_broker_api", True)
        and not _bool_from_metadata(metadata, "broker_api_invoked", False),
        "no_order_placement": _bool_from_metadata(metadata, "no_order_placement", True)
        and not _bool_from_metadata(metadata, "order_placement_enabled", False),
        "no_message_sent": _bool_from_metadata(metadata, "no_message_sent", True)
        and not _bool_from_metadata(metadata, "message_sent", False),
        "ingestion_only": _bool_from_metadata(metadata, "ingestion_only", True),
        "report_path": str(report),
        "ingestion_csv_path": str(ingestion_csv),
        "review_updates_path": str(review_updates),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _mtime_text(metadata_path),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        "artifact_type": "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
        "ingestion_id": artifact_dir.name,
        "status": status,
        "metadata_path": str(artifact_dir / "metadata.json"),
        "created_at": _mtime_text(artifact_dir),
    }


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = False if column.startswith("no_") or column == "ingestion_only" else 0 if column.endswith("_count") or column == "row_count" else ""
    for column in _bool_columns():
        output[column] = output[column].map(_is_true).astype(object)
    for column in _int_columns():
        output[column] = output[column].map(_int_or_zero)
    return output[PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_INDEX_COLUMNS].sort_values(
        ["created_at", "ingestion_id"], ascending=[False, False]
    ).reset_index(drop=True)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _status_from_counts(metadata: dict[str, Any]) -> str:
    ready = _int_or_zero(metadata.get("ready_for_review_update_count"))
    blocked = _int_or_zero(metadata.get("blocked_count"))
    if ready == 0:
        return "WARN"
    return "WARN" if blocked else "PASS"


def _int_or(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(fallback)


def _int_or_zero(value: Any) -> int:
    return _int_or(value, 0)


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_is_true).sum())


def _false_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int((~frame[column].map(_is_true)).sum())


def _bool_from_metadata(metadata: dict[str, Any], key: str, default: bool) -> bool:
    return _is_true(metadata.get(key, default))


def _bool_columns() -> list[str]:
    return [
        "no_universe_export",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "ingestion_only",
    ]


def _int_columns() -> list[str]:
    return [
        "row_count",
        "ready_for_review_update_count",
        "blocked_count",
        "approval_requested_count",
        "approved_ready_count",
        "rejected_ready_count",
        "needs_more_evidence_ready_count",
        "duplicate_identity_count",
        "missing_identity_count",
        "suggested_copy_risk_count",
    ]


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _string_or_empty(value).lower()
    return text in {"1", "true", "yes", "y", "是"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    return _string_or_empty(frame["created_at"].iloc[0]) or "1970-01-01T00:00:00+00:00"


def _mtime_text(path: Path) -> str:
    try:
        return pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat()
    except Exception:
        return "1970-01-01T00:00:00+00:00"


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows._"
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    return output[columns].to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    return "\n".join(f"- {warning}" for warning in warnings) if warnings else "No warnings."


def _safety_statement() -> str:
    return (
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
