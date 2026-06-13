"""Index report-only active replay input active-ready artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "active_ready_run_id",
    "generated_at",
    "artifact_path",
    "acceptance_artifact_path",
    "acceptance_health_artifact_path",
    "acceptance_status_artifact_path",
    "active_ready_request_manifest_path",
    "active_ready_authority_manifest_path",
    "pit_coverage_manifest_path",
    "source_coverage_manifest_path",
    "evidence_coverage_manifest_path",
    "taxonomy_compliance_manifest_path",
    "leakage_review_manifest_path",
    "side_effect_review_manifest_path",
    "overclaim_review_manifest_path",
    "status",
    "workflow_stage",
    "ready_for_final_review",
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "approval_applied",
    "order_placed",
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
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "precondition_count",
    "passed_precondition_count",
    "blocked_precondition_count",
    "authority_gate_count",
    "passed_authority_gate_count",
    "blocked_authority_gate_count",
    "lineage_gate_count",
    "passed_lineage_gate_count",
    "blocked_lineage_gate_count",
    "pit_coverage_gate_count",
    "passed_pit_coverage_gate_count",
    "blocked_pit_coverage_gate_count",
    "source_coverage_gate_count",
    "passed_source_coverage_gate_count",
    "blocked_source_coverage_gate_count",
    "evidence_coverage_gate_count",
    "passed_evidence_coverage_gate_count",
    "blocked_evidence_coverage_gate_count",
    "taxonomy_gate_count",
    "passed_taxonomy_gate_count",
    "blocked_taxonomy_gate_count",
    "issue_count",
    "blocker_count",
    "warning_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "active_ready_report_path",
    "metadata_path",
]


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_active_replay_input_active_ready_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/active_replay_input_active_ready_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/active_replay_input_active_ready_v0_1/index",
) -> ActiveReplayInputActiveReadyIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "active_replay_input_active_ready_index.csv",
        "index_report": Path(output_dir) / "active_replay_input_active_ready_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputActiveReadyIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_active_replay_input_active_ready_index(result)
    return result


def write_active_replay_input_active_ready_index(
    result: ActiveReplayInputActiveReadyIndexResult,
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
                "# Active Replay Input Active-Ready Index",
                "",
                "Report-only active-ready index. No active replay input, replay, current-candidates, snapshots, forward labels, training, active stock profiles, research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No active-ready artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Active-ready root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "active_ready_metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read active-ready metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("active_ready_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    return {
        "active_ready_run_id": _text(metadata.get("active_ready_run_id")),
        "generated_at": _text(metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "acceptance_artifact_path": _text(metadata.get("acceptance_artifact_path")),
        "acceptance_health_artifact_path": _text(metadata.get("acceptance_health_artifact_path")),
        "acceptance_status_artifact_path": _text(metadata.get("acceptance_status_artifact_path")),
        "active_ready_request_manifest_path": _text(metadata.get("active_ready_request_manifest_path")),
        "active_ready_authority_manifest_path": _text(metadata.get("active_ready_authority_manifest_path")),
        "pit_coverage_manifest_path": _text(metadata.get("pit_coverage_manifest_path")),
        "source_coverage_manifest_path": _text(metadata.get("source_coverage_manifest_path")),
        "evidence_coverage_manifest_path": _text(metadata.get("evidence_coverage_manifest_path")),
        "taxonomy_compliance_manifest_path": _text(metadata.get("taxonomy_compliance_manifest_path")),
        "leakage_review_manifest_path": _text(metadata.get("leakage_review_manifest_path")),
        "side_effect_review_manifest_path": _text(metadata.get("side_effect_review_manifest_path")),
        "overclaim_review_manifest_path": _text(metadata.get("overclaim_review_manifest_path")),
        "status": _text(metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "ready_for_final_review": _to_bool(metadata.get("ready_for_final_review")),
        "active_replay_input_ready": _to_bool(metadata.get("active_replay_input_ready")),
        "active_replay_input": _to_bool(metadata.get("active_replay_input")),
        "active_ready_emitted": _to_bool(metadata.get("active_ready_emitted")),
        "forward_labels_exist": _to_bool(metadata.get("forward_labels_exist")),
        "weights_trained": _to_bool(metadata.get("weights_trained")),
        "active_stock_profile_exists": _to_bool(metadata.get("active_stock_profile_exists")),
        "real_buy_review_eligible": _to_bool(metadata.get("real_buy_review_eligible")),
        "approval_applied": _to_bool(metadata.get("approval_applied")),
        "order_placed": _to_bool(metadata.get("order_placed")),
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
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "precondition_count": _to_int(metadata.get("precondition_count")),
        "passed_precondition_count": _to_int(metadata.get("passed_precondition_count")),
        "blocked_precondition_count": _to_int(metadata.get("blocked_precondition_count")),
        "authority_gate_count": _to_int(metadata.get("authority_gate_count")),
        "passed_authority_gate_count": _to_int(metadata.get("passed_authority_gate_count")),
        "blocked_authority_gate_count": _to_int(metadata.get("blocked_authority_gate_count")),
        "lineage_gate_count": _to_int(metadata.get("lineage_gate_count")),
        "passed_lineage_gate_count": _to_int(metadata.get("passed_lineage_gate_count")),
        "blocked_lineage_gate_count": _to_int(metadata.get("blocked_lineage_gate_count")),
        "pit_coverage_gate_count": _to_int(metadata.get("pit_coverage_gate_count")),
        "passed_pit_coverage_gate_count": _to_int(metadata.get("passed_pit_coverage_gate_count")),
        "blocked_pit_coverage_gate_count": _to_int(metadata.get("blocked_pit_coverage_gate_count")),
        "source_coverage_gate_count": _to_int(metadata.get("source_coverage_gate_count")),
        "passed_source_coverage_gate_count": _to_int(metadata.get("passed_source_coverage_gate_count")),
        "blocked_source_coverage_gate_count": _to_int(metadata.get("blocked_source_coverage_gate_count")),
        "evidence_coverage_gate_count": _to_int(metadata.get("evidence_coverage_gate_count")),
        "passed_evidence_coverage_gate_count": _to_int(metadata.get("passed_evidence_coverage_gate_count")),
        "blocked_evidence_coverage_gate_count": _to_int(metadata.get("blocked_evidence_coverage_gate_count")),
        "taxonomy_gate_count": _to_int(metadata.get("taxonomy_gate_count")),
        "passed_taxonomy_gate_count": _to_int(metadata.get("passed_taxonomy_gate_count")),
        "blocked_taxonomy_gate_count": _to_int(metadata.get("blocked_taxonomy_gate_count")),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "overclaim_guard_pass_count": _to_int(metadata.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(metadata.get("overclaim_guard_total_count")),
        "active_ready_report_path": _text(artifact_paths.get("active_ready_report"))
        or str(artifact_dir / "active_ready_report.md"),
        "metadata_path": str(metadata_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "root": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "ActiveReplayInputActiveReadyIndexResult",
    "build_active_replay_input_active_ready_index",
    "write_active_replay_input_active_ready_index",
]
