"""Index PIT evidence policy profile comparison artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "artifact_type",
    "comparison_id",
    "status",
    "reference_profile_name",
    "profile_name",
    "profile_is_opt_in",
    "strict_default_unchanged",
    "row_count",
    "strict_checklist_pass_count",
    "eod_low_budget_checklist_pass_count",
    "relaxed_blocker_count",
    "remaining_blocked_count",
    "approval_applied",
    "pit_review_run",
    "export_readiness_run",
    "export_staging_run",
    "universe_exported",
    "active_worklist_mutated",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "comparison_only",
    "report_path",
    "comparison_csv_path",
    "summary_csv_path",
    "metadata_path",
    "created_at",
]


def scan_pit_evidence_policy_profile_comparison_artifacts(
    root: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison",
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
                "artifact_type": "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON",
                "comparison_id": _string(metadata.get("comparison_id")) or artifact_dir.name,
                "status": _string(metadata.get("status")) or "WARN",
                "reference_profile_name": _string(metadata.get("reference_profile_name")),
                "profile_name": _string(metadata.get("profile_name")),
                "profile_is_opt_in": _bool(metadata.get("profile_is_opt_in")),
                "strict_default_unchanged": _bool(metadata.get("strict_default_unchanged")),
                "row_count": _int(metadata.get("row_count")),
                "strict_checklist_pass_count": _int(metadata.get("strict_checklist_pass_count")),
                "eod_low_budget_checklist_pass_count": _int(metadata.get("eod_low_budget_checklist_pass_count")),
                "relaxed_blocker_count": _int(metadata.get("relaxed_blocker_count")),
                "remaining_blocked_count": _int(metadata.get("remaining_blocked_count")),
                "approval_applied": _bool(metadata.get("approval_applied")),
                "pit_review_run": _bool(metadata.get("pit_review_run")),
                "export_readiness_run": _bool(metadata.get("export_readiness_run")),
                "export_staging_run": _bool(metadata.get("export_staging_run")),
                "universe_exported": _bool(metadata.get("universe_exported")),
                "active_worklist_mutated": _bool(metadata.get("active_worklist_mutated")),
                "no_data_raw_write": _bool(metadata.get("no_data_raw_write", True)),
                "no_data_processed_write": _bool(metadata.get("no_data_processed_write", True)),
                "no_current_candidates_generated": _bool(metadata.get("no_current_candidates_generated", True)),
                "comparison_only": _bool(metadata.get("comparison_only")),
                "report_path": str(_output_path(artifact_dir, outputs.get("report"), "report.md")),
                "comparison_csv_path": str(_output_path(artifact_dir, outputs.get("comparison_csv"), "pit_evidence_policy_profile_comparison.csv")),
                "summary_csv_path": str(_output_path(artifact_dir, outputs.get("summary_csv"), "pit_evidence_policy_profile_summary.csv")),
                "metadata_path": str(metadata_path),
                "created_at": _string(metadata.get("created_at")) or _mtime(metadata_path),
            }
        )
    return _finalize(pd.DataFrame(rows))


def build_pit_evidence_policy_profile_comparison_index(
    *,
    root: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison",
    output_dir: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison/index",
) -> dict[str, Any]:
    frame = scan_pit_evidence_policy_profile_comparison_artifacts(root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_csv = output_dir / "pit_evidence_policy_profile_comparison_index.csv"
    report = output_dir / "pit_evidence_policy_profile_comparison_index_report.md"
    metadata = output_dir / "metadata.json"
    frame.to_csv(index_csv, index=False)
    metadata.write_text(json.dumps({"artifact_count": len(frame), "approval_applied": False, "universe_exported": False}, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(f"# PIT Evidence Policy Profile Comparison Index\n\nartifact_count: {len(frame)}\n", encoding="utf-8")
    return {"artifact_count": len(frame), "index_frame": frame, "artifact_paths": {"artifact_dir": output_dir, "index_csv": index_csv, "report": report, "metadata": metadata}}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].sort_values(["created_at", "comparison_id"], ascending=[False, False]).reset_index(drop=True)


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
