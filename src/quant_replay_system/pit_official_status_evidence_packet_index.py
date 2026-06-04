"""Index PIT official status evidence packet artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "artifact_type",
    "packet_id",
    "status",
    "row_count",
    "evidence_packet_row_count",
    "strong_official_date_specific_count",
    "supporting_official_symbol_level_count",
    "supporting_local_eod_cache_count",
    "context_only_count",
    "missing_count",
    "checklist_pass_count",
    "blocked_count",
    "eod_low_budget_checklist_pass_count",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "active_worklist_mutated",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "cache_mutated",
    "packet_only",
    "report_path",
    "packet_csv_path",
    "source_coverage_summary_path",
    "per_symbol_date_status_evidence_path",
    "evidence_strength_matrix_path",
    "updated_draft_completed_updates_path",
    "metadata_path",
    "created_at",
]


def scan_pit_official_status_evidence_packet_artifacts(
    root: str | Path = "outputs/reports/pit_official_status_evidence_packet",
) -> pd.DataFrame:
    root = Path(root)
    rows: list[dict[str, Any]] = []
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
        outputs = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
        rows.append(
            {
                "artifact_type": "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET",
                "packet_id": _string(metadata.get("packet_id")) or artifact_dir.name,
                "status": _string(metadata.get("status")) or "WARN",
                "row_count": _int(metadata.get("row_count")),
                "evidence_packet_row_count": _int(metadata.get("evidence_packet_row_count")),
                "strong_official_date_specific_count": _int(metadata.get("strong_official_date_specific_count")),
                "supporting_official_symbol_level_count": _int(metadata.get("supporting_official_symbol_level_count")),
                "supporting_local_eod_cache_count": _int(metadata.get("supporting_local_eod_cache_count")),
                "context_only_count": _int(metadata.get("context_only_count")),
                "missing_count": _int(metadata.get("missing_count")),
                "checklist_pass_count": _int(metadata.get("checklist_pass_count")),
                "blocked_count": _int(metadata.get("blocked_count")),
                "eod_low_budget_checklist_pass_count": _int(metadata.get("eod_low_budget_checklist_pass_count")),
                "approval_applied": _bool(metadata.get("approval_applied")),
                "pit_review_run": _bool(metadata.get("pit_review_run")),
                "export_readiness_run": _bool(metadata.get("export_readiness_run")),
                "export_staging_run": _bool(metadata.get("export_staging_run")),
                "universe_exported": _bool(metadata.get("universe_exported")),
                "active_worklist_mutated": _bool(metadata.get("active_worklist_mutated")),
                "no_data_raw_write": _bool(metadata.get("no_data_raw_write", True)),
                "no_data_processed_write": _bool(metadata.get("no_data_processed_write", True)),
                "no_current_candidates_generated": _bool(metadata.get("no_current_candidates_generated", True)),
                "no_snapshot_built": _bool(metadata.get("no_snapshot_built", True)),
                "no_forward_labels": _bool(metadata.get("no_forward_labels", True)),
                "cache_mutated": _bool(metadata.get("cache_mutated")),
                "packet_only": _bool(metadata.get("packet_only")),
                "report_path": str(_output_path(artifact_dir, outputs.get("report"), "report.md")),
                "packet_csv_path": str(_output_path(artifact_dir, outputs.get("packet_csv"), "pit_official_status_evidence_packet.csv")),
                "source_coverage_summary_path": str(_output_path(artifact_dir, outputs.get("source_coverage_summary"), "source_coverage_summary.csv")),
                "per_symbol_date_status_evidence_path": str(
                    _output_path(artifact_dir, outputs.get("per_symbol_date_status_evidence"), "per_symbol_date_status_evidence.csv")
                ),
                "evidence_strength_matrix_path": str(_output_path(artifact_dir, outputs.get("evidence_strength_matrix"), "evidence_strength_matrix.csv")),
                "updated_draft_completed_updates_path": str(
                    _output_path(artifact_dir, outputs.get("updated_draft_completed_updates"), "updated_draft_completed_updates.csv")
                ),
                "metadata_path": str(metadata_path),
                "created_at": _string(metadata.get("created_at")) or _mtime(metadata_path),
            }
        )
    return _finalize(pd.DataFrame(rows))


def build_pit_official_status_evidence_packet_index(
    *,
    root: str | Path = "outputs/reports/pit_official_status_evidence_packet",
    output_dir: str | Path = "outputs/reports/pit_official_status_evidence_packet/index",
) -> dict[str, Any]:
    frame = scan_pit_official_status_evidence_packet_artifacts(root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_csv = output_dir / "pit_official_status_evidence_packet_index.csv"
    report = output_dir / "pit_official_status_evidence_packet_index_report.md"
    metadata = output_dir / "metadata.json"
    frame.to_csv(index_csv, index=False)
    metadata.write_text(json.dumps({"artifact_count": len(frame), "approval_applied": False, "universe_exported": False}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Official Status Evidence Packet Index\n\nartifact_count: {len(frame)}\n", encoding="utf-8")
    return {"artifact_count": len(frame), "index_frame": frame, "artifact_paths": {"artifact_dir": output_dir, "index_csv": index_csv, "report": report, "metadata": metadata}}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].sort_values(["created_at", "packet_id"], ascending=[False, False]).reset_index(drop=True)


def _output_path(artifact_dir: Path, value: Any, fallback: str) -> Path:
    text = _string(value)
    if not text:
        return artifact_dir / fallback
    path = Path(text)
    return path if path.is_absolute() or path.exists() else artifact_dir / text


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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
