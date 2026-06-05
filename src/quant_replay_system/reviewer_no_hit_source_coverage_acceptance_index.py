"""Index reviewer no-hit source coverage acceptance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "artifact_type",
    "acceptance_id",
    "status",
    "enrichment_id",
    "source_packet_id",
    "policy_comparison_id",
    "row_count",
    "accepted_count",
    "rejected_count",
    "needs_more_evidence_count",
    "needs_review_count",
    "reviewer_acceptance_required_count",
    "accepted_supporting_context_count",
    "survivorship_rationale_required_count",
    "checklist_pass_count",
    "remaining_blocked_count",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "active_worklist_mutated",
    "no_clean_review_updates_created",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "cache_mutated",
    "acceptance_only",
    "report_path",
    "acceptance_csv_path",
    "template_csv_path",
    "summary_csv_path",
    "metadata_path",
    "created_at",
]


def scan_reviewer_no_hit_source_coverage_acceptance_artifacts(
    root: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance",
) -> pd.DataFrame:
    root = Path(root)
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        metadata = _load_json(metadata_path)
        if not metadata:
            continue
        outputs = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
        rows.append(
            {
                "artifact_type": "REVIEWER_NO_HIT_SOURCE_COVERAGE_ACCEPTANCE",
                "acceptance_id": _string(metadata.get("acceptance_id")) or artifact_dir.name,
                "status": _string(metadata.get("status")) or "WARN",
                "enrichment_id": _string(metadata.get("enrichment_id")),
                "source_packet_id": _string(metadata.get("source_packet_id")),
                "policy_comparison_id": _string(metadata.get("policy_comparison_id")),
                "row_count": _int(metadata.get("row_count")),
                "accepted_count": _int(metadata.get("accepted_count")),
                "rejected_count": _int(metadata.get("rejected_count")),
                "needs_more_evidence_count": _int(metadata.get("needs_more_evidence_count")),
                "needs_review_count": _int(metadata.get("needs_review_count")),
                "reviewer_acceptance_required_count": _int(metadata.get("reviewer_acceptance_required_count")),
                "accepted_supporting_context_count": _int(metadata.get("accepted_supporting_context_count")),
                "survivorship_rationale_required_count": _int(metadata.get("survivorship_rationale_required_count")),
                "checklist_pass_count": _int(metadata.get("checklist_pass_count")),
                "remaining_blocked_count": _int(metadata.get("remaining_blocked_count")),
                "approval_applied": _bool(metadata.get("approval_applied")),
                "pit_review_run": _bool(metadata.get("pit_review_run")),
                "export_readiness_run": _bool(metadata.get("export_readiness_run")),
                "export_staging_run": _bool(metadata.get("export_staging_run")),
                "universe_exported": _bool(metadata.get("universe_exported")),
                "active_worklist_mutated": _bool(metadata.get("active_worklist_mutated")),
                "no_clean_review_updates_created": _bool(metadata.get("no_clean_review_updates_created", True)),
                "no_data_raw_write": _bool(metadata.get("no_data_raw_write", True)),
                "no_data_processed_write": _bool(metadata.get("no_data_processed_write", True)),
                "no_current_candidates_generated": _bool(metadata.get("no_current_candidates_generated", True)),
                "no_snapshot_built": _bool(metadata.get("no_snapshot_built", True)),
                "no_forward_labels": _bool(metadata.get("no_forward_labels", True)),
                "cache_mutated": _bool(metadata.get("cache_mutated")),
                "acceptance_only": _bool(metadata.get("acceptance_only")),
                "report_path": str(_output_path(artifact_dir, outputs.get("report"), "report.md")),
                "acceptance_csv_path": str(_output_path(artifact_dir, outputs.get("acceptance_csv"), "reviewer_no_hit_source_coverage_acceptance.csv")),
                "template_csv_path": str(_output_path(artifact_dir, outputs.get("template_csv"), "reviewer_no_hit_acceptance_template.csv")),
                "summary_csv_path": str(_output_path(artifact_dir, outputs.get("summary_csv"), "reviewer_no_hit_source_coverage_acceptance_summary.csv")),
                "metadata_path": str(metadata_path),
                "created_at": _string(metadata.get("created_at")) or _mtime(metadata_path),
            }
        )
    return _finalize(pd.DataFrame(rows))


def build_reviewer_no_hit_source_coverage_acceptance_index(
    *,
    root: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance",
    output_dir: str | Path = "outputs/reports/reviewer_no_hit_source_coverage_acceptance/index",
) -> dict[str, Any]:
    frame = scan_reviewer_no_hit_source_coverage_acceptance_artifacts(root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_csv = output_dir / "reviewer_no_hit_source_coverage_acceptance_index.csv"
    report = output_dir / "reviewer_no_hit_source_coverage_acceptance_index_report.md"
    metadata = output_dir / "metadata.json"
    frame.to_csv(index_csv, index=False)
    metadata.write_text(json.dumps({"artifact_count": len(frame), "approval_applied": False, "universe_exported": False}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# Reviewer No-Hit Source Coverage Acceptance Index\n\nartifact_count: {len(frame)}\n", encoding="utf-8")
    return {"artifact_count": len(frame), "index_frame": frame, "artifact_paths": {"artifact_dir": output_dir, "index_csv": index_csv, "report": report, "metadata": metadata}}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].sort_values(["created_at", "acceptance_id"], ascending=[False, False]).reset_index(drop=True)


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
