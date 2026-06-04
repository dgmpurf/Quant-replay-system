"""Index local PIT evidence checklist validator artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


INDEX_COLUMNS = [
    "artifact_type",
    "validator_id",
    "status",
    "row_count",
    "checklist_pass_count",
    "blocked_count",
    "stock_core_blocked_count",
    "etf_core_blocked_count",
    "no_approval_applied",
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
    "checklist_validation_only",
    "report_path",
    "validation_csv_path",
    "summary_csv_path",
    "missing_evidence_matrix_path",
    "approval_candidate_preview_path",
    "metadata_path",
    "created_at",
]


def scan_pit_evidence_checklist_validator_artifacts(
    root: str | Path = "outputs/reports/pit_evidence_checklist_validator",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    root = Path(root)
    if not root.exists():
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _load_json(metadata_path)
        if not metadata:
            continue
        output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
        rows.append(
            {
                "artifact_type": "PIT_EVIDENCE_CHECKLIST_VALIDATOR",
                "validator_id": _string(metadata.get("validator_id")) or artifact_dir.name,
                "status": _string(metadata.get("status")) or "WARN",
                "row_count": _int(metadata.get("row_count")),
                "checklist_pass_count": _int(metadata.get("checklist_pass_count")),
                "blocked_count": _int(metadata.get("blocked_count")),
                "stock_core_blocked_count": _int(metadata.get("stock_core_blocked_count")),
                "etf_core_blocked_count": _int(metadata.get("etf_core_blocked_count")),
                "no_approval_applied": _bool(metadata.get("no_approval_applied", True)),
                "no_universe_export": _bool(metadata.get("no_universe_export", True)),
                "no_data_raw_write": _bool(metadata.get("no_data_raw_write", True)) and not _bool(metadata.get("would_write_data_raw")),
                "no_data_processed_write": _bool(metadata.get("no_data_processed_write", True)) and not _bool(metadata.get("would_write_data_processed")),
                "no_current_candidates_generated": _bool(metadata.get("no_current_candidates_generated", True)) and not _bool(metadata.get("current_candidates_executed")),
                "no_snapshot_built": _bool(metadata.get("no_snapshot_built", True)) and not _bool(metadata.get("snapshot_manifest_built")),
                "no_forward_labels": _bool(metadata.get("no_forward_labels", True)) and not _bool(metadata.get("forward_returns_computed")),
                "no_live_trading": _bool(metadata.get("no_live_trading", True)) and not _bool(metadata.get("live_trading_enabled")),
                "no_broker_api": _bool(metadata.get("no_broker_api", True)) and not _bool(metadata.get("broker_api_invoked")),
                "no_order_placement": _bool(metadata.get("no_order_placement", True)) and not _bool(metadata.get("order_placement_enabled")),
                "no_message_sent": _bool(metadata.get("no_message_sent", True)) and not _bool(metadata.get("message_sent")),
                "checklist_validation_only": _bool(metadata.get("checklist_validation_only", True)),
                "report_path": str(output_files.get("report") or artifact_dir / "report.md"),
                "validation_csv_path": str(output_files.get("validation_csv") or artifact_dir / "pit_evidence_checklist_validation.csv"),
                "summary_csv_path": str(output_files.get("summary_csv") or artifact_dir / "pit_evidence_checklist_validation_summary.csv"),
                "missing_evidence_matrix_path": str(output_files.get("missing_evidence_matrix") or artifact_dir / "missing_evidence_matrix.csv"),
                "approval_candidate_preview_path": str(output_files.get("approval_candidate_preview") or artifact_dir / "approval_candidate_preview.csv"),
                "metadata_path": str(metadata_path),
                "created_at": _string(metadata.get("created_at")) or _mtime(metadata_path),
            }
        )
    return _finalize(pd.DataFrame(rows))


def build_pit_evidence_checklist_validator_index(
    *,
    root: str | Path = "outputs/reports/pit_evidence_checklist_validator",
    output_dir: str | Path = "outputs/reports/pit_evidence_checklist_validator/index",
) -> dict[str, Any]:
    frame = scan_pit_evidence_checklist_validator_artifacts(root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "pit_evidence_checklist_validator_index.csv"
    report_path = output_dir / "pit_evidence_checklist_validator_index_report.md"
    metadata_path = output_dir / "metadata.json"
    frame.to_csv(csv_path, index=False)
    metadata = {
        "artifact_count": len(frame),
        "output_files": {"index_csv": str(csv_path), "report": str(report_path), "metadata": str(metadata_path)},
        "approval_applied": False,
        "universe_exported": False,
        "checklist_validation_artifacts_only": True,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "# PIT Evidence Checklist Validator Index\n\n"
        "No approval applied, no universe export, no data/raw or data/processed write, no current-candidates, no snapshot, no forward labels.\n\n"
        f"artifact_count: {len(frame)}\n",
        encoding="utf-8",
    )
    return {"artifact_count": len(frame), "index_frame": frame, "artifact_paths": {"artifact_dir": output_dir, "index_csv": csv_path, "report": report_path, "metadata": metadata_path}}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].sort_values(["created_at", "validator_id"], ascending=[False, False]).reset_index(drop=True)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _mtime(path: Path) -> str:
    try:
        return pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat()
    except Exception:
        return "1970-01-01T00:00:00+00:00"
