"""Index report-only metric/evaluation phase 1 structural planning artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_evaluation import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.metric_evaluation import FORBIDDEN_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "metric_evaluation_run_id",
    "generated_at",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_training_evaluation_run_id",
    "source_training_evaluation_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_run_id",
    "source_replay_decision_freeze_run_id",
    "training_evaluation_dataset_artifacts_created",
    "training_evaluation_sample_row_count",
    "training_evaluation_label_row_count",
    "symbol_count",
    "label_name_set",
    "ready_for_metric_evaluation_planning_artifacts",
    "metric_evaluation_executed",
    "metric_evaluation_planning_artifacts_created",
    "metric_evaluation_input_index_created",
    "metric_definitions_created",
    "sample_scope_created",
    "denominator_rules_created",
    "health_status_plan_created",
    "research_status_plan_created",
    "metric_definition_count",
    "sample_scope_row_count",
    "denominator_rule_count",
    "metrics_computed",
    "metric_result_rows_created",
    "metric_evaluation_results_created",
    "evaluation_execution_completed",
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
    "approval_applied",
    "clean_review_updates_created",
    "report_only",
    "diagnostic_only",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "input_index_path",
    "metric_definitions_path",
    "sample_scope_path",
    "denominator_rules_path",
    "health_status_plan_path",
    "research_status_plan_path",
    "safety_flags_path",
]

BOOL_COLUMNS = {
    "training_evaluation_dataset_artifacts_created",
    "ready_for_metric_evaluation_planning_artifacts",
    "metric_evaluation_executed",
    "metric_evaluation_planning_artifacts_created",
    "metric_evaluation_input_index_created",
    "metric_definitions_created",
    "sample_scope_created",
    "denominator_rules_created",
    "health_status_plan_created",
    "research_status_plan_created",
    "approval_applied",
    "clean_review_updates_created",
    "report_only",
    "diagnostic_only",
    *FORBIDDEN_FALSE_FIELDS,
}

INT_COLUMNS = {
    "training_evaluation_sample_row_count",
    "training_evaluation_label_row_count",
    "symbol_count",
    "metric_definition_count",
    "sample_scope_row_count",
    "denominator_rule_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class MetricEvaluationIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_metric_evaluation_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricEvaluationIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "metric_evaluation_index.csv",
        "index_report": Path(output_dir) / "metric_evaluation_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MetricEvaluationIndexResult(
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
    write_metric_evaluation_index(result)
    return result


def write_metric_evaluation_index(result: MetricEvaluationIndexResult) -> dict[str, Path]:
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
                "# Metric / Evaluation Index",
                "",
                "Report-only metric/evaluation phase 1 index. METRIC_EVALUATION_PLANNING_ARTIFACTS_CREATED means structural planning artifacts only: not computed metrics, not result rows, not training_result, not weights, not model_version, not thresholds, not predictions, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No metric/evaluation artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Metric/evaluation root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = _first_existing(artifact_dir / "metric_evaluation_metadata.json", artifact_dir / "metadata.json")
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read metric/evaluation metadata: {metadata_path}")
            continue
        if _text(metadata.get("metric_evaluation_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = _first_existing(artifact_dir / "metric_evaluation_safety_flags.json", artifact_dir / "safety_flags.json")
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    for field in BOOL_COLUMNS:
        if _bool_any(metadata, field) or _bool_any(safety, field):
            merged[field] = True
    metric_definitions_path = artifact_dir / "metric_evaluation_metric_definitions.csv"
    sample_scope_path = artifact_dir / "metric_evaluation_sample_scope.csv"
    denominator_rules_path = artifact_dir / "metric_evaluation_denominator_rules.csv"
    return {
        "metric_evaluation_run_id": _text(metadata.get("metric_evaluation_run_id")),
        "generated_at": _text(metadata.get("generated_at") or metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "created_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_training_evaluation_run_id": _text(metadata.get("source_training_evaluation_run_id")),
        "source_training_evaluation_status": _text(metadata.get("source_training_evaluation_status")),
        "source_training_evaluation_health_status": _text(metadata.get("source_training_evaluation_health_status")),
        "source_forward_return_label_run_id": _text(metadata.get("source_forward_return_label_run_id")),
        "source_replay_decision_freeze_run_id": _text(metadata.get("source_replay_decision_freeze_run_id")),
        "training_evaluation_dataset_artifacts_created": _bool_any(merged, "training_evaluation_dataset_artifacts_created"),
        "training_evaluation_sample_row_count": _to_int(metadata.get("training_evaluation_sample_row_count")),
        "training_evaluation_label_row_count": _to_int(metadata.get("training_evaluation_label_row_count")),
        "symbol_count": _to_int(metadata.get("symbol_count")),
        "label_name_set": _text(metadata.get("label_name_set")),
        "ready_for_metric_evaluation_planning_artifacts": _bool_any(merged, "ready_for_metric_evaluation_planning_artifacts"),
        "metric_evaluation_executed": _bool_any(merged, "metric_evaluation_executed"),
        "metric_evaluation_planning_artifacts_created": _bool_any(merged, "metric_evaluation_planning_artifacts_created"),
        "metric_evaluation_input_index_created": _bool_any(merged, "metric_evaluation_input_index_created"),
        "metric_definitions_created": _bool_any(merged, "metric_definitions_created"),
        "sample_scope_created": _bool_any(merged, "sample_scope_created"),
        "denominator_rules_created": _bool_any(merged, "denominator_rules_created"),
        "health_status_plan_created": _bool_any(merged, "health_status_plan_created"),
        "research_status_plan_created": _bool_any(merged, "research_status_plan_created"),
        "metric_definition_count": _to_int(metadata.get("metric_definition_count")) or _row_count(metric_definitions_path),
        "sample_scope_row_count": _to_int(metadata.get("sample_scope_row_count")) or _row_count(sample_scope_path),
        "denominator_rule_count": _to_int(metadata.get("denominator_rule_count")) or _row_count(denominator_rules_path),
        **{field: _bool_any(merged, field) for field in FORBIDDEN_FALSE_FIELDS},
        "approval_applied": _bool_any(merged, "approval_applied"),
        "clean_review_updates_created": _bool_any(merged, "clean_review_updates_created"),
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": str(artifact_dir / "metric_evaluation_report.md"),
        "metadata_path": str(metadata_path),
        "input_index_path": str(artifact_dir / "metric_evaluation_input_index.csv"),
        "metric_definitions_path": str(metric_definitions_path),
        "sample_scope_path": str(sample_scope_path),
        "denominator_rules_path": str(denominator_rules_path),
        "health_status_plan_path": str(artifact_dir / "metric_evaluation_health_status_plan.csv"),
        "research_status_plan_path": str(artifact_dir / "metric_evaluation_research_status_plan.json"),
        "safety_flags_path": str(safety_path),
    }


def _row_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(pd.read_csv(path, dtype={"symbol": "string"}))
    except Exception:
        return 0


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
