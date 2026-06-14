"""Index report-only ACTIVE_REPLAY_INPUT_READY core artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/active_replay_input_ready_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "active_ready_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_to_emit_active_replay_input_ready",
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
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "precondition_gate_count",
    "authority_gate_count",
    "lineage_gate_count",
    "attestation_gate_count",
    "pit_source_evidence_gate_count",
    "taxonomy_gate_count",
    "leakage_side_effect_gate_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "issue_count",
    "blocker_count",
    "warning_count",
    "active_ready_report_path",
    "metadata_path",
]


@dataclass(frozen=True)
class ActiveReplayInputReadyIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_active_replay_input_ready_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveReplayInputReadyIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "active_replay_input_ready_index.csv",
        "index_report": Path(output_dir) / "active_replay_input_ready_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveReplayInputReadyIndexResult(
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
    write_active_replay_input_ready_index(result)
    return result


def write_active_replay_input_ready_index(result: ActiveReplayInputReadyIndexResult) -> dict[str, Path]:
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
                "# ACTIVE_REPLAY_INPUT_READY Index",
                "",
                "Report-only active-ready index. It does not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, create replay decisions, compute labels, train weights, create stock profiles, create buy-review eligibility, authorize trading, write data stores, call APIs, send messages, use broker integration, place orders, or mutate cache.",
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
        return [], [f"ACTIVE_REPLAY_INPUT_READY root does not exist: {root}"]
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
        "status": _text(metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage")),
        "ready_to_emit_active_replay_input_ready": _to_bool(
            metadata.get("ready_to_emit_active_replay_input_ready")
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
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "precondition_gate_count": _count_list(metadata, "precondition_results"),
        "authority_gate_count": _count_list(metadata, "authority_results"),
        "lineage_gate_count": _count_list(metadata, "lineage_results"),
        "attestation_gate_count": _count_list(metadata, "attestation_results"),
        "pit_source_evidence_gate_count": _count_list(metadata, "pit_source_evidence_results"),
        "taxonomy_gate_count": _count_list(metadata, "taxonomy_results"),
        "leakage_side_effect_gate_count": _count_list(metadata, "leakage_side_effect_results"),
        "overclaim_guard_pass_count": _to_int(metadata.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(metadata.get("overclaim_guard_total_count")),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "active_ready_report_path": _text(artifact_paths.get("active_ready_report")),
        "metadata_path": str(metadata_path),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column.startswith(("active_", "replay_", "forward_", "training")) else ""
    bool_columns = [
        column
        for column in INDEX_COLUMNS
        if column
        in {
            "ready_to_emit_active_replay_input_ready",
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
            "no_live_trading",
            "no_broker_api",
            "no_order_placement",
            "no_message_sent",
        }
    ]
    for column in bool_columns:
        frame[column] = frame[column].map(_to_bool).astype(object)
    return frame[INDEX_COLUMNS].sort_values(["generated_at", "active_ready_run_id"]).reset_index(drop=True)


def _count_list(metadata: dict[str, Any], key: str) -> int:
    value = metadata.get(key)
    return len(value) if isinstance(value, list) else 0


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


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
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "accepted"}
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
