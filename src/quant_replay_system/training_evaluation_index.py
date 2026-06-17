"""Index report-only training/evaluation phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_evaluation import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "training_evaluation_run_id",
    "generated_at",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_forward_return_label_run_id",
    "source_forward_return_label_status",
    "source_forward_return_label_health_status",
    "source_replay_decision_freeze_run_id",
    "forward_labels_exist",
    "forward_return_labels_created",
    "label_row_count",
    "replay_decision_count",
    "symbol_count",
    "label_name_set",
    "ready_for_training_evaluation_dataset",
    "training_evaluation_executed",
    "training_evaluation_dataset_artifacts_created",
    "bounded_sample_rows_created",
    "label_coverage_report_created",
    "split_plan_created",
    "feature_plan_created",
    "label_plan_created",
    "dataset_sample_row_count",
    "max_sample_rows",
    "metrics_computed",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "model_version_created",
    "thresholds_optimized",
    "predictions_created",
    "calibrated_probabilities_created",
    "feature_importance_created",
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
    "dataset_index_path",
    "sample_rows_path",
    "label_coverage_report_path",
    "split_plan_path",
    "feature_plan_path",
    "label_plan_path",
    "safety_flags_path",
]

BOOL_COLUMNS = {
    "forward_labels_exist",
    "forward_return_labels_created",
    "ready_for_training_evaluation_dataset",
    "training_evaluation_executed",
    "training_evaluation_dataset_artifacts_created",
    "bounded_sample_rows_created",
    "label_coverage_report_created",
    "split_plan_created",
    "feature_plan_created",
    "label_plan_created",
    "metrics_computed",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "model_version_created",
    "thresholds_optimized",
    "predictions_created",
    "calibrated_probabilities_created",
    "feature_importance_created",
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
INT_COLUMNS = {
    "label_row_count",
    "replay_decision_count",
    "symbol_count",
    "dataset_sample_row_count",
    "max_sample_rows",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class TrainingEvaluationIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_training_evaluation_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingEvaluationIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "training_evaluation_index.csv",
        "index_report": Path(output_dir) / "training_evaluation_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingEvaluationIndexResult(
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
    write_training_evaluation_index(result)
    return result


def write_training_evaluation_index(result: TrainingEvaluationIndexResult) -> dict[str, Path]:
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
                "# Training / Evaluation Index",
                "",
                "Report-only training/evaluation phase 1 index. TRAINING_EVALUATION_DATASET_CREATED means dataset/planning artifacts only: not metrics, not training_result, not weights, not model_version, not thresholds, not predictions, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No training/evaluation artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Training/evaluation root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = _first_existing(artifact_dir / "training_evaluation_metadata.json", artifact_dir / "metadata.json")
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read training/evaluation metadata: {metadata_path}")
            continue
        run_id = _text(metadata.get("training_evaluation_run_id"))
        if run_id:
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = _first_existing(
        artifact_dir / "training_evaluation_safety_flags.json",
        artifact_dir / "safety_flags.json",
    )
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    for field in BOOL_COLUMNS:
        if _bool_any(metadata, field) or _bool_any(safety, field):
            merged[field] = True
    sample_info = _sample_info(artifact_dir / "training_evaluation_sample_rows.csv")
    label_info = _label_info(artifact_dir / "training_evaluation_label_coverage_report.csv")
    return {
        "training_evaluation_run_id": _text(metadata.get("training_evaluation_run_id")),
        "generated_at": _text(metadata.get("generated_at") or metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "created_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_forward_return_label_run_id": _text(metadata.get("source_forward_return_label_run_id")),
        "source_forward_return_label_status": _text(metadata.get("source_forward_return_label_status")),
        "source_forward_return_label_health_status": _text(metadata.get("source_forward_return_label_health_status")),
        "source_replay_decision_freeze_run_id": _text(metadata.get("source_replay_decision_freeze_run_id")),
        "forward_labels_exist": _bool_any(merged, "forward_labels_exist"),
        "forward_return_labels_created": _bool_any(merged, "forward_return_labels_created"),
        "label_row_count": _to_int(metadata.get("label_row_count")) or label_info["label_row_count"],
        "replay_decision_count": _to_int(metadata.get("replay_decision_count")),
        "symbol_count": _to_int(metadata.get("symbol_count")) or sample_info["symbol_count"],
        "label_name_set": _text(metadata.get("label_name_set")) or label_info["label_name_set"],
        "ready_for_training_evaluation_dataset": _bool_any(merged, "ready_for_training_evaluation_dataset"),
        "training_evaluation_executed": _bool_any(merged, "training_evaluation_executed"),
        "training_evaluation_dataset_artifacts_created": _bool_any(merged, "training_evaluation_dataset_artifacts_created"),
        "bounded_sample_rows_created": _bool_any(merged, "bounded_sample_rows_created"),
        "label_coverage_report_created": _bool_any(merged, "label_coverage_report_created"),
        "split_plan_created": _bool_any(merged, "split_plan_created"),
        "feature_plan_created": _bool_any(merged, "feature_plan_created"),
        "label_plan_created": _bool_any(merged, "label_plan_created"),
        "dataset_sample_row_count": _to_int(metadata.get("dataset_sample_row_count")) or sample_info["dataset_sample_row_count"],
        "max_sample_rows": _to_int(metadata.get("max_sample_rows")) or 50,
        "metrics_computed": _bool_any(merged, "metrics_computed"),
        "training_allowed": _bool_any(merged, "training_allowed"),
        "weights_trained": _bool_any(merged, "weights_trained"),
        "training_result_created": _bool_any(merged, "training_result_created"),
        "model_version_created": _bool_any(merged, "model_version_created"),
        "thresholds_optimized": _bool_any(merged, "thresholds_optimized"),
        "predictions_created": _bool_any(merged, "predictions_created"),
        "calibrated_probabilities_created": _bool_any(merged, "calibrated_probabilities_created"),
        "feature_importance_created": _bool_any(merged, "feature_importance_created"),
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
        "report_path": str(artifact_dir / "training_evaluation_report.md"),
        "metadata_path": str(metadata_path),
        "dataset_index_path": str(artifact_dir / "training_evaluation_dataset_index.csv"),
        "sample_rows_path": str(artifact_dir / "training_evaluation_sample_rows.csv"),
        "label_coverage_report_path": str(artifact_dir / "training_evaluation_label_coverage_report.csv"),
        "split_plan_path": str(artifact_dir / "training_evaluation_split_plan.csv"),
        "feature_plan_path": str(artifact_dir / "training_evaluation_feature_plan.csv"),
        "label_plan_path": str(artifact_dir / "training_evaluation_label_plan.csv"),
        "safety_flags_path": str(safety_path),
    }


def _sample_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"dataset_sample_row_count": 0, "symbol_count": 0}
    try:
        frame = pd.read_csv(path, dtype={"symbol": "string"})
    except Exception:
        return {"dataset_sample_row_count": 0, "symbol_count": 0}
    return {
        "dataset_sample_row_count": len(frame),
        "symbol_count": int(frame["symbol"].astype(str).str.zfill(6).nunique()) if "symbol" in frame.columns and not frame.empty else 0,
    }


def _label_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"label_row_count": 0, "label_name_set": ""}
    try:
        frame = pd.read_csv(path)
    except Exception:
        return {"label_row_count": 0, "label_name_set": ""}
    if frame.empty:
        return {"label_row_count": 0, "label_name_set": ""}
    return {
        "label_row_count": int(frame["row_count"].sum()) if "row_count" in frame.columns else len(frame),
        "label_name_set": ";".join(sorted(set(str(value) for value in frame.get("label_name", pd.Series(dtype=str)).dropna()))),
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
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
