"""Local-only index for reviewed replacement worklist acceptance artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


INDEX_COLUMNS = [
    "artifact_type",
    "acceptance_id",
    "status",
    "replacement_plan_id",
    "source_split_plan_id",
    "source_policy_audit_id",
    "source_worklist_id",
    "accepted_by",
    "accepted_at",
    "acceptance_reason",
    "acceptance_acknowledged",
    "row_count",
    "stock_core_row_count",
    "etf_core_row_count",
    "mixed_demo_core_row_count",
    "profile_conflict_count",
    "active_worklist_mutated",
    "no_approval_applied",
    "no_rejection_applied",
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
    "acceptance_only",
    "report_path",
    "acceptance_csv_path",
    "stock_core_worklist_path",
    "etf_core_worklist_path",
    "mixed_demo_core_worklist_path",
    "stock_core_template_path",
    "etf_core_template_path",
    "mixed_demo_core_template_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class ReviewedReplacementWorklistAcceptanceIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_reviewed_replacement_worklist_acceptance_index(
    *,
    root: str | Path = "outputs/reports/reviewed_replacement_worklist_acceptance",
    output_dir: str | Path = "outputs/reports/reviewed_replacement_worklist_acceptance/index",
    include_missing_metadata: bool = False,
) -> ReviewedReplacementWorklistAcceptanceIndexResult:
    rows, warnings = _scan_rows(Path(root), include_missing_metadata=include_missing_metadata)
    frame = _finalize(pd.DataFrame(rows))
    artifact_dir = Path(output_dir)
    paths = {
        "artifact_dir": artifact_dir,
        "reviewed_replacement_worklist_acceptance_index_csv": artifact_dir
        / "reviewed_replacement_worklist_acceptance_index.csv",
        "reviewed_replacement_worklist_acceptance_index_report": artifact_dir
        / "reviewed_replacement_worklist_acceptance_index_report.md",
        "metadata": artifact_dir / "metadata.json",
    }
    result = ReviewedReplacementWorklistAcceptanceIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_safe_audit_metadata(root, len(frame)),
    )
    write_reviewed_replacement_worklist_acceptance_index(result)
    return result


def scan_reviewed_replacement_worklist_acceptance_artifacts(
    root: str | Path = "outputs/reports/reviewed_replacement_worklist_acceptance",
) -> pd.DataFrame:
    rows, _warnings = _scan_rows(Path(root), include_missing_metadata=False)
    return _finalize(pd.DataFrame(rows))


def write_reviewed_replacement_worklist_acceptance_index(
    result: ReviewedReplacementWorklistAcceptanceIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["reviewed_replacement_worklist_acceptance_index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths["reviewed_replacement_worklist_acceptance_index_report"].write_text(
        "\n".join(
            [
                "# Reviewed Replacement Worklist Acceptance Index",
                "",
                "No approval, rejection, active worklist mutation, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No rows.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Reviewed replacement worklist acceptance root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        if not _text(metadata.get("acceptance_id")):
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    acceptance_csv = Path(
        output_files.get("reviewed_replacement_worklist_acceptance")
        or artifact_dir / "reviewed_replacement_worklist_acceptance.csv"
    )
    frame = _read_csv(acceptance_csv)
    return {
        "artifact_type": "REVIEWED_REPLACEMENT_WORKLIST_ACCEPTANCE",
        "acceptance_id": _text(metadata.get("acceptance_id")) or artifact_dir.name,
        "status": _text(metadata.get("status")) or "PASS",
        "replacement_plan_id": _text(metadata.get("replacement_plan_id")),
        "source_split_plan_id": _text(metadata.get("source_split_plan_id")),
        "source_policy_audit_id": _text(metadata.get("source_policy_audit_id")),
        "source_worklist_id": _text(metadata.get("source_worklist_id")),
        "accepted_by": _text(metadata.get("accepted_by")),
        "accepted_at": _text(metadata.get("accepted_at")),
        "acceptance_reason": _text(metadata.get("acceptance_reason")),
        "acceptance_acknowledged": _to_bool(metadata.get("acceptance_acknowledged")),
        "row_count": _to_int(metadata.get("row_count", len(frame))),
        "stock_core_row_count": _to_int(metadata.get("stock_core_row_count", _equals_count(frame, "future_universe_name", "stock_core"))),
        "etf_core_row_count": _to_int(metadata.get("etf_core_row_count", _equals_count(frame, "future_universe_name", "etf_core"))),
        "mixed_demo_core_row_count": _to_int(metadata.get("mixed_demo_core_row_count", _equals_count(frame, "future_universe_name", "mixed_demo_core"))),
        "profile_conflict_count": _to_int(metadata.get("profile_conflict_count", _true_count(frame, "profile_conflict"))),
        "active_worklist_mutated": _to_bool(metadata.get("active_worklist_mutated")),
        "no_approval_applied": _to_bool(metadata.get("no_approval_applied")),
        "no_rejection_applied": _to_bool(metadata.get("no_rejection_applied")),
        "no_universe_export": _to_bool(metadata.get("no_universe_export")),
        "no_data_raw_write": _to_bool(metadata.get("no_data_raw_write")),
        "no_data_processed_write": _to_bool(metadata.get("no_data_processed_write")),
        "no_current_candidates_generated": _to_bool(metadata.get("no_current_candidates_generated")),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built")),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "acceptance_only": _to_bool(metadata.get("acceptance_only")),
        "report_path": str(Path(output_files.get("report") or artifact_dir / "report.md")),
        "acceptance_csv_path": str(acceptance_csv),
        "stock_core_worklist_path": str(Path(output_files.get("accepted_replacement_worklist_stock_core") or artifact_dir / "accepted_replacement_worklist_stock_core.csv")),
        "etf_core_worklist_path": str(Path(output_files.get("accepted_replacement_worklist_etf_core") or artifact_dir / "accepted_replacement_worklist_etf_core.csv")),
        "mixed_demo_core_worklist_path": str(Path(output_files.get("accepted_replacement_worklist_mixed_demo_core") or artifact_dir / "accepted_replacement_worklist_mixed_demo_core.csv")),
        "stock_core_template_path": str(Path(output_files.get("accepted_update_template_stock_core") or artifact_dir / "accepted_update_template_stock_core.csv")),
        "etf_core_template_path": str(Path(output_files.get("accepted_update_template_etf_core") or artifact_dir / "accepted_update_template_etf_core.csv")),
        "mixed_demo_core_template_path": str(Path(output_files.get("accepted_update_template_mixed_demo_core") or artifact_dir / "accepted_update_template_mixed_demo_core.csv")),
        "metadata_path": str(metadata_path),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in INDEX_COLUMNS}
    row.update({"artifact_type": "REVIEWED_REPLACEMENT_WORKLIST_ACCEPTANCE", "acceptance_id": artifact_dir.name, "status": status})
    return row


def _safe_audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "current_candidates_executed": False,
        "snapshot_manifest_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "broker_api_invoked": False,
        "message_sent": False,
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = "" if not column.endswith("_count") else 0
    return frame.loc[:, INDEX_COLUMNS].sort_values(["created_at", "acceptance_id"]).reset_index(drop=True)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if not frame.empty and "created_at" in frame and str(frame["created_at"].iloc[-1]).strip():
        return str(frame["created_at"].iloc[-1])
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _equals_count(frame: pd.DataFrame, column: str, value: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int((frame[column].astype(str) == value).sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
