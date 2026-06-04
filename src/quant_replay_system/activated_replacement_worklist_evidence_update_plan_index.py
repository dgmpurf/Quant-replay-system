"""Index for activated replacement worklist evidence update plan artifacts."""

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
    "plan_id",
    "status",
    "activation_id",
    "acceptance_id",
    "replacement_plan_id",
    "source_split_plan_id",
    "source_policy_audit_id",
    "source_worklist_id",
    "row_count",
    "stock_core_row_count",
    "etf_core_row_count",
    "mixed_demo_core_row_count",
    "stock_core_first_batch_row_count",
    "etf_core_first_batch_row_count",
    "approved_count",
    "rejected_count",
    "include_flag_true_count",
    "valid_for_signal_date_count",
    "clean_review_updates_created",
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
    "evidence_update_planning_only",
    "report_path",
    "plan_csv_path",
    "stock_core_worklist_path",
    "etf_core_worklist_path",
    "mixed_demo_core_worklist_path",
    "stock_core_template_path",
    "etf_core_template_path",
    "mixed_demo_core_template_path",
    "stock_core_first_batch_path",
    "etf_core_first_batch_path",
    "metadata_path",
    "created_at",
]


@dataclass(frozen=True)
class ActivatedReplacementWorklistEvidenceUpdatePlanIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_activated_replacement_worklist_evidence_update_plan_index(
    *,
    root: str | Path = "outputs/reports/activated_replacement_worklist_evidence_update_plan",
    output_dir: str | Path = "outputs/reports/activated_replacement_worklist_evidence_update_plan/index",
) -> ActivatedReplacementWorklistEvidenceUpdatePlanIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows))
    artifact_dir = Path(output_dir)
    paths = {
        "artifact_dir": artifact_dir,
        "index_csv": artifact_dir / "activated_replacement_worklist_evidence_update_plan_index.csv",
        "index_report": artifact_dir / "activated_replacement_worklist_evidence_update_plan_index_report.md",
        "metadata": artifact_dir / "metadata.json",
    }
    result = ActivatedReplacementWorklistEvidenceUpdatePlanIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_safe_audit_metadata(root, len(frame)),
    )
    write_activated_replacement_worklist_evidence_update_plan_index(result)
    return result


def write_activated_replacement_worklist_evidence_update_plan_index(
    result: ActivatedReplacementWorklistEvidenceUpdatePlanIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    metadata = {
        "index_id": _hash_payload(result.index_frame.to_dict("records")),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "warnings": result.warnings,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Activated Replacement Worklist Evidence Update Plan Index",
                "",
                "No approval, rejection, active mutation, export, data write, current-candidates generation, snapshot build, forward labels, live trading, broker API, orders, messages, network/API, LLM/API, or cache mutation was invoked.",
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
        return [], [f"Activated replacement worklist evidence update plan root does not exist: {root}"]
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
        if _text(metadata.get("plan_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    return {
        "artifact_type": "ACTIVATED_REPLACEMENT_WORKLIST_EVIDENCE_UPDATE_PLAN",
        "plan_id": _text(metadata.get("plan_id")) or artifact_dir.name,
        "status": _text(metadata.get("status")) or "PASS",
        "activation_id": _text(metadata.get("activation_id")),
        "acceptance_id": _text(metadata.get("acceptance_id")),
        "replacement_plan_id": _text(metadata.get("replacement_plan_id")),
        "source_split_plan_id": _text(metadata.get("source_split_plan_id")),
        "source_policy_audit_id": _text(metadata.get("source_policy_audit_id")),
        "source_worklist_id": _text(metadata.get("source_worklist_id")),
        "row_count": _to_int(metadata.get("row_count")),
        "stock_core_row_count": _to_int(metadata.get("stock_core_row_count")),
        "etf_core_row_count": _to_int(metadata.get("etf_core_row_count")),
        "mixed_demo_core_row_count": _to_int(metadata.get("mixed_demo_core_row_count")),
        "stock_core_first_batch_row_count": _to_int(metadata.get("stock_core_first_batch_row_count")),
        "etf_core_first_batch_row_count": _to_int(metadata.get("etf_core_first_batch_row_count")),
        "approved_count": _to_int(metadata.get("approved_count")),
        "rejected_count": _to_int(metadata.get("rejected_count")),
        "include_flag_true_count": _to_int(metadata.get("include_flag_true_count")),
        "valid_for_signal_date_count": _to_int(metadata.get("valid_for_signal_date_count")),
        "clean_review_updates_created": _to_bool(metadata.get("clean_review_updates_created")),
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
        "evidence_update_planning_only": _to_bool(metadata.get("evidence_update_planning_only")),
        "report_path": str(Path(output_files.get("report") or artifact_dir / "report.md")),
        "plan_csv_path": str(Path(output_files.get("plan_csv") or artifact_dir / "activated_replacement_worklist_evidence_update_plan.csv")),
        "stock_core_worklist_path": str(Path(output_files.get("stock_core_evidence_worklist") or artifact_dir / "stock_core_evidence_worklist.csv")),
        "etf_core_worklist_path": str(Path(output_files.get("etf_core_evidence_worklist") or artifact_dir / "etf_core_evidence_worklist.csv")),
        "mixed_demo_core_worklist_path": str(Path(output_files.get("mixed_demo_core_evidence_worklist") or artifact_dir / "mixed_demo_core_evidence_worklist.csv")),
        "stock_core_template_path": str(Path(output_files.get("stock_core_update_template") or artifact_dir / "stock_core_update_template.csv")),
        "etf_core_template_path": str(Path(output_files.get("etf_core_update_template") or artifact_dir / "etf_core_update_template.csv")),
        "mixed_demo_core_template_path": str(Path(output_files.get("mixed_demo_core_update_template") or artifact_dir / "mixed_demo_core_update_template.csv")),
        "stock_core_first_batch_path": str(Path(output_files.get("stock_core_first_batch_package") or artifact_dir / "stock_core_first_batch_package.csv")),
        "etf_core_first_batch_path": str(Path(output_files.get("etf_core_first_batch_package") or artifact_dir / "etf_core_first_batch_package.csv")),
        "metadata_path": str(metadata_path),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


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
            frame[column] = 0 if column.endswith("_count") else ""
    return frame.loc[:, INDEX_COLUMNS].sort_values(["created_at", "plan_id"]).reset_index(drop=True)


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if not frame.empty and str(frame["created_at"].iloc[-1]).strip():
        return str(frame["created_at"].iloc[-1])
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


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
