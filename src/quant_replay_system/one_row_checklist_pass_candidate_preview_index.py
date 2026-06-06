"""Index for one-row checklist-pass candidate preview artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "artifact_type",
    "preview_id",
    "status",
    "target_signal_date",
    "target_symbol",
    "target_universe_name",
    "preview_row_count",
    "reusable_context_field_count",
    "strict_requirement_gap_count",
    "row_checklist_pass_candidate",
    "checklist_pass_candidate_count",
    "remaining_blocked_count",
    "clean_review_updates_created",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "preview_only",
    "report_path",
    "preview_csv_path",
    "strict_requirement_gap_matrix_path",
    "context_field_reuse_assessment_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class OneRowChecklistPassCandidatePreviewIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_one_row_checklist_pass_candidate_preview_index(
    *,
    root: str | Path = "outputs/reports/one_row_checklist_pass_candidate_preview",
    output_dir: str | Path = "outputs/reports/one_row_checklist_pass_candidate_preview/index",
) -> OneRowChecklistPassCandidatePreviewIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "one_row_checklist_pass_candidate_preview_index.csv",
        "index_report": Path(output_dir) / "one_row_checklist_pass_candidate_preview_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = OneRowChecklistPassCandidatePreviewIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_safe_audit_metadata(root, len(frame)),
    )
    write_one_row_checklist_pass_candidate_preview_index(result)
    return result


def write_one_row_checklist_pass_candidate_preview_index(
    result: OneRowChecklistPassCandidatePreviewIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "artifact_count": result.artifact_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths["index_report"].write_text(
        "\n".join(
            [
                "# One-Row Checklist-Pass Candidate Preview Index",
                "",
                "Report-only index; no approval, clean review updates, PIT review/export/staging, data writes, current-candidates, snapshots, labels, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No rows.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"One-row checklist-pass candidate preview root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("preview_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    return {
        "artifact_type": "ONE_ROW_CHECKLIST_PASS_CANDIDATE_PREVIEW",
        "preview_id": _text(metadata.get("preview_id")) or artifact_dir.name,
        "status": _text(metadata.get("status")),
        "target_signal_date": _text(metadata.get("signal_date")),
        "target_symbol": _text(metadata.get("symbol")),
        "target_universe_name": _text(metadata.get("universe_name")),
        "preview_row_count": _to_int(metadata.get("preview_row_count")),
        "reusable_context_field_count": _to_int(metadata.get("reusable_context_field_count")),
        "strict_requirement_gap_count": _to_int(metadata.get("strict_requirement_gap_count")),
        "row_checklist_pass_candidate": _to_bool(metadata.get("row_checklist_pass_candidate")),
        "checklist_pass_candidate_count": _to_int(metadata.get("checklist_pass_candidate_count")),
        "remaining_blocked_count": _to_int(metadata.get("remaining_blocked_count")),
        "clean_review_updates_created": _to_bool(metadata.get("clean_review_updates_created")),
        "approval_applied": _to_bool(metadata.get("approval_applied")),
        "pit_review_run": _to_bool(metadata.get("pit_review_run")),
        "export_readiness_run": _to_bool(metadata.get("export_readiness_run")),
        "export_staging_run": _to_bool(metadata.get("export_staging_run")),
        "universe_exported": _to_bool(metadata.get("universe_exported")),
        "no_data_raw_write": _to_bool(metadata.get("no_data_raw_write")),
        "no_data_processed_write": _to_bool(metadata.get("no_data_processed_write")),
        "no_current_candidates_generated": _to_bool(metadata.get("no_current_candidates_generated")),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built")),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels")),
        "preview_only": _to_bool(metadata.get("preview_only")),
        "report_path": str(Path(output_files.get("report") or artifact_dir / "report.md")),
        "preview_csv_path": str(
            Path(output_files.get("preview_csv") or artifact_dir / "one_row_checklist_pass_candidate_preview.csv")
        ),
        "strict_requirement_gap_matrix_path": str(
            Path(output_files.get("strict_requirement_gap_matrix") or artifact_dir / "strict_requirement_gap_matrix.csv")
        ),
        "context_field_reuse_assessment_path": str(
            Path(output_files.get("context_field_reuse_assessment") or artifact_dir / "context_field_reuse_assessment.csv")
        ),
        "metadata_path": str(metadata_path),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS]


def _safe_audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "approval_applied": False,
        "clean_review_updates_created": False,
        "pit_review_run": False,
        "export_readiness_run": False,
        "export_staging_run": False,
        "universe_exported": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "cache_mutated": False,
    }


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


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
