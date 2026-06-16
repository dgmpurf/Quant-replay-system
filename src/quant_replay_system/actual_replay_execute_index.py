"""Index report-only actual replay execution artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/actual_replay_execute_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "actual_replay_execution_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_active_input_creation_run_id",
    "source_real_replay_precheck_run_id",
    "ready_for_actual_replay_execution",
    "actual_replay_executed",
    "replay_execution_started",
    "replay_execution_completed",
    "replay_decisions_created",
    "replay_decisions_exist",
    "replay_decision_artifact_path",
    "forward_labels_allowed",
    "forward_labels_exist",
    "training_allowed",
    "weights_trained",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "buy_review_allowed",
    "real_buy_review_eligible",
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
    "input_snapshot_path",
    "safety_flags_path",
    "observation_snapshot_path",
    "evidence_bundle_index_path",
]

BOOL_COLUMNS = {
    "ready_for_actual_replay_execution",
    "actual_replay_executed",
    "replay_execution_started",
    "replay_execution_completed",
    "replay_decisions_created",
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "training_allowed",
    "weights_trained",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "buy_review_allowed",
    "real_buy_review_eligible",
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
INT_COLUMNS = {"issue_count", "blocker_count", "warning_count"}


@dataclass(frozen=True)
class ActualReplayExecuteIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_actual_replay_execute_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActualReplayExecuteIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "actual_replay_execute_index.csv",
        "index_report": Path(output_dir) / "actual_replay_execute_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActualReplayExecuteIndexResult(
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
    write_actual_replay_execute_index(result)
    return result


def write_actual_replay_execute_index(result: ActualReplayExecuteIndexResult) -> dict[str, Path]:
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
                "# Actual Replay Execution Index",
                "",
                "Report-only index. `ACTUAL_REPLAY_EXECUTED` means execution artifacts only; it is not replay_decision creation, not labels, not training, not stock_profile, not buy-review eligibility, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No actual replay execution artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Actual replay execution root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "actual_replay_execution_metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read actual replay execution metadata: {metadata_path}")
            continue
        if _text(metadata.get("actual_replay_execution_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    input_snapshot_path = Path(
        _text(artifact_paths.get("input_snapshot")) or str(artifact_dir / "actual_replay_execution_input_snapshot.json")
    )
    safety_flags_path = Path(
        _text(artifact_paths.get("safety_flags")) or str(artifact_dir / "actual_replay_safety_flags.json")
    )
    input_snapshot = _read_json(input_snapshot_path)
    safety = _read_json(safety_flags_path)
    merged = {**input_snapshot, **metadata, **safety}
    return {
        "actual_replay_execution_run_id": _text(metadata.get("actual_replay_execution_run_id")),
        "generated_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_active_input_creation_run_id": _text(merged.get("source_active_input_creation_run_id")),
        "source_real_replay_precheck_run_id": _text(merged.get("source_real_replay_precheck_run_id")),
        "ready_for_actual_replay_execution": _bool_any(input_snapshot, metadata, safety, "ready_for_actual_replay_execution"),
        "actual_replay_executed": _bool_any(input_snapshot, metadata, safety, "actual_replay_executed"),
        "replay_execution_started": _bool_any(input_snapshot, metadata, safety, "replay_execution_started"),
        "replay_execution_completed": _bool_any(input_snapshot, metadata, safety, "replay_execution_completed"),
        "replay_decisions_created": _bool_any(input_snapshot, metadata, safety, "replay_decisions_created"),
        "replay_decisions_exist": _bool_any(input_snapshot, metadata, safety, "replay_decisions_exist"),
        "replay_decision_artifact_path": _text(
            input_snapshot.get("replay_decision_artifact_path")
            or metadata.get("replay_decision_artifact_path")
            or safety.get("replay_decision_artifact_path")
        ),
        "forward_labels_allowed": _bool_any(input_snapshot, metadata, safety, "forward_labels_allowed"),
        "forward_labels_exist": _bool_any(input_snapshot, metadata, safety, "forward_labels_exist"),
        "training_allowed": _bool_any(input_snapshot, metadata, safety, "training_allowed"),
        "weights_trained": _bool_any(input_snapshot, metadata, safety, "weights_trained"),
        "stock_profile_allowed": _bool_any(input_snapshot, metadata, safety, "stock_profile_allowed"),
        "active_stock_profile_exists": _bool_any(input_snapshot, metadata, safety, "active_stock_profile_exists"),
        "buy_review_allowed": _bool_any(input_snapshot, metadata, safety, "buy_review_allowed"),
        "real_buy_review_eligible": _bool_any(input_snapshot, metadata, safety, "real_buy_review_eligible"),
        "trading_allowed": _bool_any(input_snapshot, metadata, safety, "trading_allowed"),
        "order_placed": _bool_any(input_snapshot, metadata, safety, "order_placed"),
        "broker_api_called": _bool_any(input_snapshot, metadata, safety, "broker_api_called"),
        "message_sent": _bool_any(input_snapshot, metadata, safety, "message_sent"),
        "llm_api_called": _bool_any(input_snapshot, metadata, safety, "llm_api_called"),
        "external_api_called": _bool_any(input_snapshot, metadata, safety, "external_api_called"),
        "cache_mutated": _bool_any(input_snapshot, metadata, safety, "cache_mutated"),
        "data_raw_written": _bool_any(input_snapshot, metadata, safety, "data_raw_written"),
        "data_processed_written": _bool_any(input_snapshot, metadata, safety, "data_processed_written"),
        "data_cache_written": _bool_any(input_snapshot, metadata, safety, "data_cache_written"),
        "current_candidates_run": _bool_any(input_snapshot, metadata, safety, "current_candidates_run"),
        "snapshot_built": _bool_any(input_snapshot, metadata, safety, "snapshot_built"),
        "signal_semantics_changed": _bool_any(input_snapshot, metadata, safety, "signal_semantics_changed"),
        "report_only": _bool_any(input_snapshot, metadata, safety, "report_only"),
        "diagnostic_only": _bool_any(input_snapshot, metadata, safety, "diagnostic_only"),
        "issue_count": _to_int(merged.get("issue_count")),
        "blocker_count": _to_int(merged.get("blocker_count")),
        "warning_count": _to_int(merged.get("warning_count")),
        "report_path": _text(artifact_paths.get("report")) or str(artifact_dir / "actual_replay_execution_report.md"),
        "metadata_path": str(metadata_path),
        "input_snapshot_path": str(input_snapshot_path),
        "safety_flags_path": str(safety_flags_path),
        "observation_snapshot_path": _text(artifact_paths.get("observation_snapshot"))
        or str(artifact_dir / "actual_replay_observation_snapshot.csv"),
        "evidence_bundle_index_path": _text(artifact_paths.get("evidence_bundle_index"))
        or str(artifact_dir / "actual_replay_evidence_bundle_index.csv"),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in BOOL_COLUMNS else 0 if column in INT_COLUMNS else ""
    return frame[INDEX_COLUMNS].sort_values(["generated_at", "actual_replay_execution_run_id"]).reset_index(drop=True)


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


def _bool_any(first: dict[str, Any], second: dict[str, Any], third: dict[str, Any], field: str) -> bool:
    return any(_to_bool(payload.get(field)) for payload in [first, second, third])


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
