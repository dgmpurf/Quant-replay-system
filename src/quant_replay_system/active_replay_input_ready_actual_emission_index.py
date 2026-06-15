"""Index report-only actual ACTIVE_REPLAY_INPUT_READY marker emission artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/active_replay_input_ready_actual_emission_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "actual_emission_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "active_replay_input_ready_marker_emitted",
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "replay_execution_allowed",
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
    "marker_file_exists",
    "marker_only_semantics_confirmed",
    "issue_count",
    "blocker_count",
    "warning_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "report_path",
    "metadata_path",
    "marker_path",
]


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_actual_active_replay_input_ready_emission_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActualActiveReplayInputReadyEmissionIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "active_replay_input_ready_actual_emission_index.csv",
        "index_report": Path(output_dir) / "active_replay_input_ready_actual_emission_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActualActiveReplayInputReadyEmissionIndexResult(
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
    write_actual_active_replay_input_ready_emission_index(result)
    return result


def write_actual_active_replay_input_ready_emission_index(
    result: ActualActiveReplayInputReadyEmissionIndexResult,
) -> dict[str, Path]:
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
                "# Actual ACTIVE_REPLAY_INPUT_READY Emission Index",
                "",
                "Report-only marker-emission index. ACTIVE_REPLAY_INPUT_READY here is marker-only and not active replay input, replay, replay decisions, labels, training, stock_profile, buy-review eligibility, broker/order/message/API/cache/data side effects, or trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No actual marker-emission artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Actual emission root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "actual_emission_metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read actual emission metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("actual_emission_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    marker_path = Path(_text(artifact_paths.get("marker")) or str(artifact_dir / "active_replay_input_ready_marker.json"))
    marker_payload = _read_json(marker_path)
    return {
        "actual_emission_run_id": _text(metadata.get("actual_emission_run_id")),
        "generated_at": _text(metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "status": _text(metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "active_replay_input_ready_marker_emitted": _to_bool(
            metadata.get("active_replay_input_ready_marker_emitted")
        ),
        "active_replay_input_ready": _to_bool(metadata.get("active_replay_input_ready")),
        "active_replay_input": _to_bool(metadata.get("active_replay_input")),
        "active_ready_emitted": _to_bool(metadata.get("active_ready_emitted")),
        "replay_execution_allowed": _to_bool(metadata.get("replay_execution_allowed")),
        "replay_decisions_exist": _to_bool(metadata.get("replay_decisions_exist")),
        "forward_labels_allowed": _to_bool(metadata.get("forward_labels_allowed")),
        "forward_labels_exist": _to_bool(metadata.get("forward_labels_exist")),
        "training_allowed": _to_bool(metadata.get("training_allowed")),
        "weights_trained": _to_bool(metadata.get("weights_trained")),
        "stock_profile_allowed": _to_bool(metadata.get("stock_profile_allowed")),
        "active_stock_profile_exists": _to_bool(metadata.get("active_stock_profile_exists")),
        "buy_review_allowed": _to_bool(metadata.get("buy_review_allowed")),
        "real_buy_review_eligible": _to_bool(metadata.get("real_buy_review_eligible")),
        "trading_allowed": _to_bool(metadata.get("trading_allowed")),
        "order_placed": _to_bool(metadata.get("order_placed")),
        "broker_api_called": _to_bool(metadata.get("broker_api_called")),
        "message_sent": _to_bool(metadata.get("message_sent")),
        "llm_api_called": _to_bool(metadata.get("llm_api_called")),
        "external_api_called": _to_bool(metadata.get("external_api_called")),
        "cache_mutated": _to_bool(metadata.get("cache_mutated")),
        "data_raw_written": _to_bool(metadata.get("data_raw_written")),
        "data_processed_written": _to_bool(metadata.get("data_processed_written")),
        "data_cache_written": _to_bool(metadata.get("data_cache_written")),
        "current_candidates_run": _to_bool(metadata.get("current_candidates_run")),
        "snapshot_built": _to_bool(metadata.get("snapshot_built")),
        "signal_semantics_changed": _to_bool(metadata.get("signal_semantics_changed")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "marker_file_exists": marker_path.exists(),
        "marker_only_semantics_confirmed": _marker_only_semantics_confirmed(marker_payload),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "overclaim_guard_pass_count": _to_int(metadata.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(metadata.get("overclaim_guard_total_count")),
        "report_path": _text(artifact_paths.get("report")) or str(artifact_dir / "actual_emission_report.md"),
        "metadata_path": str(metadata_path),
        "marker_path": str(marker_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in _BOOL_COLUMNS else "" if column not in _INT_COLUMNS else 0
    return frame[INDEX_COLUMNS].sort_values(["generated_at", "actual_emission_run_id"]).reset_index(drop=True)


def _marker_only_semantics_confirmed(payload: dict[str, Any]) -> bool:
    statement = _text(payload.get("safety_statement")).lower()
    return (
        "marker-only" in statement
        and "not active replay input" in statement
        and not _to_bool(payload.get("active_replay_input"))
        and not _to_bool(payload.get("replay_execution_allowed"))
        and not _to_bool(payload.get("trading_allowed"))
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.is_dir():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "accepted"}
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


_BOOL_COLUMNS = {
    "active_replay_input_ready_marker_emitted",
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "replay_execution_allowed",
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
    "marker_file_exists",
    "marker_only_semantics_confirmed",
}
_INT_COLUMNS = {
    "issue_count",
    "blocker_count",
    "warning_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
}


__all__ = [
    "DEFAULT_ROOT",
    "DEFAULT_OUTPUT_DIR",
    "ActualActiveReplayInputReadyEmissionIndexResult",
    "build_actual_active_replay_input_ready_emission_index",
    "write_actual_active_replay_input_ready_emission_index",
]
