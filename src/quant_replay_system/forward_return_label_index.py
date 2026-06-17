"""Index report-only forward return label artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path("outputs/reports/manual_diagnostics/forward_return_label_v0_1")
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "forward_return_label_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_replay_decision_freeze_run_id",
    "source_replay_decision_freeze_artifact_path",
    "replay_decision_freeze_status",
    "replay_decision_freeze_health_status",
    "replay_decision_frozen",
    "replay_decisions_exist",
    "ready_for_forward_return_label",
    "forward_return_label_executed",
    "forward_return_label_artifacts_created",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "forward_return_label_artifact_path",
    "label_row_count",
    "label_name_set",
    "symbol_count",
    "replay_decision_count",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
    "strategy_performance_validated",
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
    "forward_return_label_rows_path",
    "forward_return_label_price_input_index_path",
    "forward_return_label_benchmark_index_path",
    "forward_return_label_industry_index_path",
    "safety_flags_path",
]
BOOL_COLUMNS = {
    "replay_decision_frozen",
    "replay_decisions_exist",
    "ready_for_forward_return_label",
    "forward_return_label_executed",
    "forward_return_label_artifacts_created",
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
    "strategy_performance_validated",
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
INT_COLUMNS = {"label_row_count", "symbol_count", "replay_decision_count", "issue_count", "blocker_count", "warning_count"}


@dataclass(frozen=True)
class ForwardReturnLabelIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_forward_return_label_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ForwardReturnLabelIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "forward_return_label_index.csv",
        "index_report": Path(output_dir) / "forward_return_label_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ForwardReturnLabelIndexResult(
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
    write_forward_return_label_index(result)
    return result


def write_forward_return_label_index(result: ForwardReturnLabelIndexResult) -> dict[str, Path]:
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
                "# Forward Return Label Index",
                "",
                "Report-only index. `FORWARD_RETURN_LABELS_CREATED` means future outcome labels only; it is not training, not training_result, not stock_profile, not buy-review eligibility, not paper approval, not strategy performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No forward return label artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Forward return label root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = _first_existing(artifact_dir / "forward_return_label_metadata.json", artifact_dir / "metadata.json")
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read forward return label metadata: {metadata_path}")
            continue
        if _text(metadata.get("forward_return_label_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    rows_path = Path(_text(artifact_paths.get("forward_return_label_rows")) or str(artifact_dir / "forward_return_label_rows.csv"))
    safety_path = _first_existing(
        Path(_text(artifact_paths.get("forward_return_label_safety_flags")) or str(artifact_dir / "forward_return_label_safety_flags.json")),
        Path(_text(artifact_paths.get("safety_flags")) or str(artifact_dir / "safety_flags.json")),
    )
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    label_info = _label_info(rows_path)
    return {
        "forward_return_label_run_id": _text(metadata.get("forward_return_label_run_id")),
        "generated_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_replay_decision_freeze_run_id": _text(metadata.get("source_replay_decision_freeze_run_id")),
        "source_replay_decision_freeze_artifact_path": _text(metadata.get("source_replay_decision_freeze_artifact_path")),
        "replay_decision_freeze_status": _text(metadata.get("replay_decision_freeze_status")),
        "replay_decision_freeze_health_status": _text(metadata.get("replay_decision_freeze_health_status")),
        "replay_decision_frozen": _bool_any(merged, "replay_decision_frozen"),
        "replay_decisions_exist": _bool_any(merged, "replay_decisions_exist"),
        "ready_for_forward_return_label": _bool_any(merged, "ready_for_forward_return_label"),
        "forward_return_label_executed": _bool_any(merged, "forward_return_label_executed"),
        "forward_return_label_artifacts_created": _bool_any(merged, "forward_return_label_artifacts_created"),
        "forward_labels_allowed": _bool_any(merged, "forward_labels_allowed"),
        "forward_labels_exist": _bool_any(merged, "forward_labels_exist"),
        "forward_return_labels_created": _bool_any(merged, "forward_return_labels_created"),
        "forward_return_label_artifact_path": _text(metadata.get("forward_return_label_artifact_path")),
        "label_row_count": label_info["label_row_count"],
        "label_name_set": label_info["label_name_set"],
        "symbol_count": label_info["symbol_count"],
        "replay_decision_count": label_info["replay_decision_count"],
        "training_allowed": _bool_any(merged, "training_allowed"),
        "weights_trained": _bool_any(merged, "weights_trained"),
        "training_result_created": _bool_any(merged, "training_result_created"),
        "stock_profile_allowed": _bool_any(merged, "stock_profile_allowed"),
        "active_stock_profile_exists": _bool_any(merged, "active_stock_profile_exists"),
        "stock_profile_created": _bool_any(merged, "stock_profile_created"),
        "buy_review_allowed": _bool_any(merged, "buy_review_allowed"),
        "real_buy_review_eligible": _bool_any(merged, "real_buy_review_eligible"),
        "approved_for_paper": _bool_any(merged, "approved_for_paper"),
        "strategy_performance_validated": _bool_any(merged, "strategy_performance_validated"),
        "trading_allowed": _bool_any(merged, "trading_allowed"),
        "order_placed": _bool_any(merged, "order_placed"),
        "broker_api_called": _bool_any(merged, "broker_api_called"),
        "message_sent": _bool_any(merged, "message_sent"),
        "llm_api_called": _bool_any(merged, "llm_api_called"),
        "external_api_called": _bool_any(merged, "external_api_called"),
        "cache_mutated": _bool_any(merged, "cache_mutated"),
        "data_raw_written": _bool_any(merged, "data_raw_written"),
        "data_processed_written": _bool_any(merged, "data_processed_written"),
        "data_cache_written": _bool_any(merged, "data_cache_written"),
        "current_candidates_run": _bool_any(merged, "current_candidates_run"),
        "snapshot_built": _bool_any(merged, "snapshot_built"),
        "signal_semantics_changed": _bool_any(merged, "signal_semantics_changed"),
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": _text(artifact_paths.get("report")) or str(artifact_dir / "forward_return_label_report.md"),
        "metadata_path": str(metadata_path),
        "forward_return_label_rows_path": str(rows_path),
        "forward_return_label_price_input_index_path": _text(artifact_paths.get("forward_return_label_price_input_index")) or str(artifact_dir / "forward_return_label_price_input_index.csv"),
        "forward_return_label_benchmark_index_path": _text(artifact_paths.get("forward_return_label_benchmark_index")) or str(artifact_dir / "forward_return_label_benchmark_index.csv"),
        "forward_return_label_industry_index_path": _text(artifact_paths.get("forward_return_label_industry_index")) or str(artifact_dir / "forward_return_label_industry_index.csv"),
        "safety_flags_path": str(safety_path),
    }


def _label_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"label_row_count": 0, "label_name_set": "", "symbol_count": 0, "replay_decision_count": 0}
    try:
        frame = pd.read_csv(path, dtype={"symbol": "string"})
    except Exception:
        return {"label_row_count": 0, "label_name_set": "", "symbol_count": 0, "replay_decision_count": 0}
    if frame.empty:
        return {"label_row_count": 0, "label_name_set": "", "symbol_count": 0, "replay_decision_count": 0}
    return {
        "label_row_count": len(frame),
        "label_name_set": ";".join(sorted(set(str(value) for value in frame.get("label_name", pd.Series(dtype=str)).dropna()))),
        "symbol_count": int(frame["symbol"].astype(str).str.zfill(6).nunique()) if "symbol" in frame.columns else 0,
        "replay_decision_count": int(frame["replay_decision_id"].nunique()) if "replay_decision_id" in frame.columns else 0,
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = False if column in BOOL_COLUMNS else 0 if column in INT_COLUMNS else ""
    frame = frame[INDEX_COLUMNS].copy()
    for column in BOOL_COLUMNS:
        frame[column] = frame[column].map(_to_bool).astype(object)
    for column in INT_COLUMNS:
        frame[column] = frame[column].map(_to_int)
    return frame


def _first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[-1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _bool_any(payload: dict[str, Any], field: str) -> bool:
    return _to_bool(payload.get(field))


def _to_int(value: Any) -> int:
    try:
        if value is None or value == "" or pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
