"""Index report-only replay decision freeze artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/replay_decision_freeze_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "replay_decision_freeze_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_actual_replay_execution_run_id",
    "source_active_input_creation_run_id",
    "source_real_replay_precheck_run_id",
    "actual_replay_execution_status",
    "actual_replay_execution_health_status",
    "actual_replay_executed",
    "ready_for_replay_decision_freeze",
    "replay_decision_freeze_executed",
    "replay_decision_frozen",
    "replay_decision_artifacts_created",
    "replay_decisions_created",
    "replay_decisions_exist",
    "replay_decision_artifact_path",
    "decision_row_count",
    "decision_label_set",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "report_only",
    "diagnostic_only",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "replay_decision_rows_path",
    "replay_decision_evidence_index_path",
    "safety_flags_path",
]

BOOL_COLUMNS = {
    "actual_replay_executed",
    "ready_for_replay_decision_freeze",
    "replay_decision_freeze_executed",
    "replay_decision_frozen",
    "replay_decision_artifacts_created",
    "replay_decisions_created",
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "report_only",
    "diagnostic_only",
}
INT_COLUMNS = {"decision_row_count", "issue_count", "blocker_count", "warning_count"}


@dataclass(frozen=True)
class ReplayDecisionFreezeIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_replay_decision_freeze_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ReplayDecisionFreezeIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "replay_decision_freeze_index.csv",
        "index_report": Path(output_dir) / "replay_decision_freeze_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplayDecisionFreezeIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata={
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "root": str(root),
            "artifact_count": len(frame),
            "report_only": True,
            "diagnostic_only": True,
        },
    )
    write_replay_decision_freeze_index(result)
    return result


def write_replay_decision_freeze_index(result: ReplayDecisionFreezeIndexResult) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "index_id": _hash_payload(result.index_frame.to_dict("records")),
                "artifact_count": result.artifact_count,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Replay Decision Freeze Index",
                "",
                "Report-only index. `REPLAY_DECISION_FROZEN` means frozen decision-time review rows only; it is not forward labels, not training, not stock_profile, not buy-review eligibility, not paper approval, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No replay decision freeze artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Replay decision freeze root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "replay_decision_metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read replay decision freeze metadata: {metadata_path}")
            continue
        if _text(metadata.get("replay_decision_freeze_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    rows_path = Path(_text(artifact_paths.get("replay_decision_rows")) or str(artifact_dir / "replay_decision_rows.csv"))
    evidence_path = Path(
        _text(artifact_paths.get("replay_decision_evidence_index"))
        or str(artifact_dir / "replay_decision_evidence_index.csv")
    )
    safety_path = Path(_text(artifact_paths.get("safety_flags")) or str(artifact_dir / "replay_decision_safety_flags.json"))
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    decision_info = _decision_info(rows_path)
    return {
        "replay_decision_freeze_run_id": _text(metadata.get("replay_decision_freeze_run_id")),
        "generated_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_actual_replay_execution_run_id": _text(metadata.get("source_actual_replay_execution_run_id")),
        "source_active_input_creation_run_id": _text(metadata.get("source_active_input_creation_run_id")),
        "source_real_replay_precheck_run_id": _text(metadata.get("source_real_replay_precheck_run_id")),
        "actual_replay_execution_status": _text(metadata.get("actual_replay_execution_status")),
        "actual_replay_execution_health_status": _text(metadata.get("actual_replay_execution_health_status")),
        "actual_replay_executed": _bool_any(metadata, safety, "actual_replay_executed"),
        "ready_for_replay_decision_freeze": _bool_any(metadata, safety, "ready_for_replay_decision_freeze"),
        "replay_decision_freeze_executed": _bool_any(metadata, safety, "replay_decision_freeze_executed"),
        "replay_decision_frozen": _bool_any(metadata, safety, "replay_decision_frozen"),
        "replay_decision_artifacts_created": _bool_any(metadata, safety, "replay_decision_artifacts_created"),
        "replay_decisions_created": _bool_any(metadata, safety, "replay_decisions_created"),
        "replay_decisions_exist": _bool_any(metadata, safety, "replay_decisions_exist"),
        "replay_decision_artifact_path": _text(metadata.get("replay_decision_artifact_path")),
        "decision_row_count": decision_info["count"],
        "decision_label_set": decision_info["labels"],
        "forward_labels_allowed": _bool_any(metadata, safety, "forward_labels_allowed"),
        "forward_labels_exist": _bool_any(metadata, safety, "forward_labels_exist"),
        "forward_return_labels_created": _bool_any(metadata, safety, "forward_return_labels_created"),
        "training_allowed": _bool_any(metadata, safety, "training_allowed"),
        "weights_trained": _bool_any(metadata, safety, "weights_trained"),
        "training_result_created": _bool_any(metadata, safety, "training_result_created"),
        "stock_profile_allowed": _bool_any(metadata, safety, "stock_profile_allowed"),
        "active_stock_profile_exists": _bool_any(metadata, safety, "active_stock_profile_exists"),
        "stock_profile_created": _bool_any(metadata, safety, "stock_profile_created"),
        "buy_review_allowed": _bool_any(metadata, safety, "buy_review_allowed"),
        "real_buy_review_eligible": _bool_any(metadata, safety, "real_buy_review_eligible"),
        "approved_for_paper": _bool_any(metadata, safety, "approved_for_paper"),
        "trading_allowed": _bool_any(metadata, safety, "trading_allowed"),
        "order_placed": _bool_any(metadata, safety, "order_placed"),
        "broker_api_called": _bool_any(metadata, safety, "broker_api_called"),
        "message_sent": _bool_any(metadata, safety, "message_sent"),
        "llm_api_called": _bool_any(metadata, safety, "llm_api_called"),
        "external_api_called": _bool_any(metadata, safety, "external_api_called"),
        "cache_mutated": _bool_any(metadata, safety, "cache_mutated"),
        "data_raw_written": _bool_any(metadata, safety, "data_raw_written"),
        "data_processed_written": _bool_any(metadata, safety, "data_processed_written"),
        "data_cache_written": _bool_any(metadata, safety, "data_cache_written"),
        "current_candidates_run": _bool_any(metadata, safety, "current_candidates_run"),
        "snapshot_built": _bool_any(metadata, safety, "snapshot_built"),
        "signal_semantics_changed": _bool_any(metadata, safety, "signal_semantics_changed"),
        "report_only": _bool_any(metadata, safety, "report_only"),
        "diagnostic_only": _bool_any(metadata, safety, "diagnostic_only"),
        "issue_count": _to_int(merged.get("issue_count")),
        "blocker_count": _to_int(merged.get("blocker_count")),
        "warning_count": _to_int(merged.get("warning_count")),
        "report_path": _text(artifact_paths.get("report")) or str(artifact_dir / "replay_decision_freeze_report.md"),
        "metadata_path": str(metadata_path),
        "replay_decision_rows_path": str(rows_path),
        "replay_decision_evidence_index_path": str(evidence_path),
        "safety_flags_path": str(safety_path),
    }


def _decision_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"count": 0, "labels": ""}
    try:
        frame = pd.read_csv(path, dtype={"symbol": "string"})
    except Exception:
        return {"count": 0, "labels": ""}
    labels = ""
    if "decision_label" in frame.columns and not frame.empty:
        labels = ";".join(sorted(str(value) for value in frame["decision_label"].dropna().unique()))
    return {"count": len(frame), "labels": labels}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in BOOL_COLUMNS else 0 if column in INT_COLUMNS else ""
    return frame[INDEX_COLUMNS].sort_values(["generated_at", "replay_decision_freeze_run_id"]).reset_index(drop=True)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.is_dir():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass"}
    return False


def _bool_any(first: dict[str, Any], second: dict[str, Any], field: str) -> bool:
    return any(_to_bool(payload.get(field)) for payload in [first, second])


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
