"""Index report-only real replay execution precheck artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/real_replay_execute_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "real_replay_execution_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_real_replay_execution_review",
    "source_active_input_creation_run_id",
    "source_active_replay_input_artifact_path",
    "active_replay_input_created",
    "active_replay_input",
    "replay_as_of_date",
    "replay_calendar",
    "symbol_universe_ref",
    "pit_universe_ref",
    "source_registry_ref",
    "raw_document_store_ref",
    "factor_definition_ref",
    "factor_observation_ref",
    "event_structured_ref",
    "company_exposure_ref",
    "evidence_bundle_ref",
    "source_hash_coverage",
    "revision_id_coverage",
    "available_time_policy",
    "taxonomy_coverage",
    "future_labels_excluded",
    "deterministic_only",
    "replay_execution_started",
    "replay_execution_completed",
    "real_replay_executed",
    "replay_execution_allowed",
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
    "precheck_path",
    "overclaim_guard_results_path",
]

BOOL_COLUMNS = {
    "ready_for_real_replay_execution_review",
    "active_replay_input_created",
    "active_replay_input",
    "future_labels_excluded",
    "deterministic_only",
    "replay_execution_started",
    "replay_execution_completed",
    "real_replay_executed",
    "replay_execution_allowed",
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
class RealReplayExecuteIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_real_replay_execute_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> RealReplayExecuteIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "real_replay_execute_index.csv",
        "index_report": Path(output_dir) / "real_replay_execute_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = RealReplayExecuteIndexResult(
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
    write_real_replay_execute_index(result)
    return result


def write_real_replay_execute_index(result: RealReplayExecuteIndexResult) -> dict[str, Path]:
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
                "# Real Replay Execution Precheck Index",
                "",
                "Report-only index. `real-replay-execute` is pre-execution review-ready only; it is not replay execution, not replay decisions, not labels, not training, not stock_profile, not buy-review eligibility, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No real replay execution precheck artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Real replay execution precheck root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "real_replay_execution_metadata.json"
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read real replay execution metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("real_replay_execution_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    precheck_path = Path(
        _text(artifact_paths.get("precheck")) or str(artifact_dir / "real_replay_execution_precheck.json")
    )
    precheck = _read_json(precheck_path)
    return {
        "real_replay_execution_run_id": _text(metadata.get("real_replay_execution_run_id")),
        "generated_at": _text(metadata.get("generated_at")) or _text(precheck.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "status": _text(metadata.get("status") or precheck.get("execution_status")),
        "workflow_stage": _text(metadata.get("workflow_stage")) or _text(precheck.get("execution_status")),
        "ready_for_real_replay_execution_review": _bool_any(metadata, precheck, "ready_for_real_replay_execution_review"),
        "source_active_input_creation_run_id": _text(
            metadata.get("source_active_input_creation_run_id") or precheck.get("source_active_input_creation_run_id")
        ),
        "source_active_replay_input_artifact_path": _text(
            metadata.get("source_active_replay_input_artifact_path")
            or precheck.get("source_active_replay_input_artifact_path")
        ),
        "active_replay_input_created": _bool_any(metadata, precheck, "active_replay_input_created"),
        "active_replay_input": _bool_any(metadata, precheck, "active_replay_input"),
        "replay_as_of_date": _text(metadata.get("replay_as_of_date") or precheck.get("replay_as_of_date")),
        "replay_calendar": _text(metadata.get("replay_calendar") or precheck.get("replay_calendar")),
        "symbol_universe_ref": _text(precheck.get("symbol_universe_ref")),
        "pit_universe_ref": _text(precheck.get("pit_universe_ref")),
        "source_registry_ref": _text(precheck.get("source_registry_ref")),
        "raw_document_store_ref": _text(precheck.get("raw_document_store_ref")),
        "factor_definition_ref": _text(precheck.get("factor_definition_ref")),
        "factor_observation_ref": _text(precheck.get("factor_observation_ref")),
        "event_structured_ref": _text(precheck.get("event_structured_ref")),
        "company_exposure_ref": _text(precheck.get("company_exposure_ref")),
        "evidence_bundle_ref": _text(precheck.get("evidence_bundle_ref")),
        "source_hash_coverage": _text(precheck.get("source_hash_coverage")),
        "revision_id_coverage": _text(precheck.get("revision_id_coverage")),
        "available_time_policy": _text(precheck.get("available_time_policy")),
        "taxonomy_coverage": _text(precheck.get("taxonomy_coverage")),
        "future_labels_excluded": _bool_any(metadata, precheck, "future_labels_excluded"),
        "deterministic_only": _bool_any(metadata, precheck, "deterministic_only"),
        "replay_execution_started": _bool_any(metadata, precheck, "replay_execution_started"),
        "replay_execution_completed": _bool_any(metadata, precheck, "replay_execution_completed"),
        "real_replay_executed": _bool_any(metadata, precheck, "real_replay_executed"),
        "replay_execution_allowed": _bool_any(metadata, precheck, "replay_execution_allowed"),
        "replay_decisions_created": _bool_any(metadata, precheck, "replay_decisions_created"),
        "replay_decisions_exist": _bool_any(metadata, precheck, "replay_decisions_exist"),
        "replay_decision_artifact_path": _text(precheck.get("replay_decision_artifact_path")),
        "forward_labels_allowed": _bool_any(metadata, precheck, "forward_labels_allowed"),
        "forward_labels_exist": _bool_any(metadata, precheck, "forward_labels_exist"),
        "training_allowed": _bool_any(metadata, precheck, "training_allowed"),
        "weights_trained": _bool_any(metadata, precheck, "weights_trained"),
        "stock_profile_allowed": _bool_any(metadata, precheck, "stock_profile_allowed"),
        "active_stock_profile_exists": _bool_any(metadata, precheck, "active_stock_profile_exists"),
        "buy_review_allowed": _bool_any(metadata, precheck, "buy_review_allowed"),
        "real_buy_review_eligible": _bool_any(metadata, precheck, "real_buy_review_eligible"),
        "trading_allowed": _bool_any(metadata, precheck, "trading_allowed"),
        "order_placed": _bool_any(metadata, precheck, "order_placed"),
        "broker_api_called": _bool_any(metadata, precheck, "broker_api_called"),
        "message_sent": _bool_any(metadata, precheck, "message_sent"),
        "llm_api_called": _bool_any(metadata, precheck, "llm_api_called"),
        "external_api_called": _bool_any(metadata, precheck, "external_api_called"),
        "cache_mutated": _bool_any(metadata, precheck, "cache_mutated"),
        "data_raw_written": _bool_any(metadata, precheck, "data_raw_written"),
        "data_processed_written": _bool_any(metadata, precheck, "data_processed_written"),
        "data_cache_written": _bool_any(metadata, precheck, "data_cache_written"),
        "current_candidates_run": _bool_any(metadata, precheck, "current_candidates_run"),
        "snapshot_built": _bool_any(metadata, precheck, "snapshot_built"),
        "signal_semantics_changed": _bool_any(metadata, precheck, "signal_semantics_changed"),
        "report_only": _bool_all_present(metadata, precheck, "report_only"),
        "diagnostic_only": _bool_all_present(metadata, precheck, "diagnostic_only"),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": _text(artifact_paths.get("report")) or str(artifact_dir / "real_replay_execution_report.md"),
        "metadata_path": str(metadata_path),
        "precheck_path": str(precheck_path),
        "overclaim_guard_results_path": _text(artifact_paths.get("overclaim_guard_results"))
        or str(artifact_dir / "overclaim_guard_results.csv"),
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in BOOL_COLUMNS else 0 if column in INT_COLUMNS else ""
    return frame[INDEX_COLUMNS].sort_values(["generated_at", "real_replay_execution_run_id"]).reset_index(drop=True)


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


def _bool_any(metadata: dict[str, Any], precheck: dict[str, Any], field: str) -> bool:
    return _to_bool(metadata.get(field)) or _to_bool(precheck.get(field))


def _bool_all_present(metadata: dict[str, Any], precheck: dict[str, Any], field: str) -> bool:
    values = [payload[field] for payload in [metadata, precheck] if field in payload]
    return bool(values) and all(_to_bool(value) for value in values)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
