"""Index report-only training result planning phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_result_planning import ARTIFACT_FILES
from quant_replay_system.training_result_planning import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.training_result_planning import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "training_result_planning_run_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_training_result_planning",
    "training_result_planning_executed",
    "training_result_planning_artifacts_created",
    "source_metric_extension_run_id",
    "source_metric_extension_status",
    "source_metric_extension_health_status",
    "source_metric_computation_run_id",
    "source_metric_computation_status",
    "source_metric_computation_health_status",
    "source_metric_evaluation_planning_run_id",
    "source_metric_evaluation_status",
    "source_metric_evaluation_health_status",
    "source_training_evaluation_run_id",
    "source_training_evaluation_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_run_id",
    "source_forward_return_label_status",
    "source_forward_return_label_health_status",
    "source_replay_decision_freeze_run_id",
    "source_replay_decision_freeze_status",
    "source_replay_decision_freeze_health_status",
    "metric_evidence_names_present",
    "metric_evidence_row_count",
    "planning_input_row_count",
    "eligible_planning_input_count",
    "quarantined_planning_input_count",
    "model_scope_rows_created",
    "limitations_created",
    "overfit_warnings_created",
    "health_plan_created",
    "status_plan_created",
    "input_index_row_count",
    "lineage_matrix_row_count",
    "model_scope_row_count",
    "overfit_warning_row_count",
    "health_plan_row_count",
    "status_plan_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "diagnostic_only",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "input_index_path",
    "metric_evidence_index_path",
    "lineage_matrix_path",
    "model_scope_path",
    "limitations_path",
    "overfit_warnings_path",
    "health_plan_path",
    "status_plan_path",
    "safety_flags_path",
    "recommended_next_task_path",
]

BOOL_COLUMNS = {
    "ready_for_training_result_planning",
    "training_result_planning_executed",
    "training_result_planning_artifacts_created",
    "model_scope_rows_created",
    "limitations_created",
    "overfit_warnings_created",
    "health_plan_created",
    "status_plan_created",
    "report_only",
    "diagnostic_only",
    *DOWNSTREAM_FALSE_FIELDS,
}

INT_COLUMNS = {
    "metric_evidence_row_count",
    "planning_input_row_count",
    "eligible_planning_input_count",
    "quarantined_planning_input_count",
    "input_index_row_count",
    "lineage_matrix_row_count",
    "model_scope_row_count",
    "overfit_warning_row_count",
    "health_plan_row_count",
    "status_plan_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class TrainingResultPlanningIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_training_result_planning_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingResultPlanningIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "training_result_planning_index.csv",
        "index_report": Path(output_dir) / "training_result_planning_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingResultPlanningIndexResult(
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
    write_training_result_planning_index(result)
    return result


def write_training_result_planning_index(result: TrainingResultPlanningIndexResult) -> dict[str, Path]:
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
                "# Training Result Planning Index",
                "",
                "Report-only index for training result planning phase 1. TRAINING_RESULT_PLANNING_ARTIFACTS_CREATED means planning artifacts only: not actual training_result, not weights, not model_version, not parameter_version, not thresholds, not predictions/probabilities/feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No training result planning artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Training result planning root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith(("index", "health", "status", "_")):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("training_result_planning_*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"training_result_planning_run_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read training result planning metadata: {metadata_path}")
            continue
        if _text(metadata.get("training_result_planning_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / ARTIFACT_FILES["safety_flags"]
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    metric_evidence_path = artifact_dir / ARTIFACT_FILES["metric_evidence_index"]
    metric_evidence = _read_csv(metric_evidence_path)
    metric_names = _text(metadata.get("metric_evidence_names_present"))
    if not metric_names and not metric_evidence.empty and "metric_name" in metric_evidence.columns:
        metric_names = ",".join(sorted(metric_evidence["metric_name"].dropna().astype(str).unique()))
    return {
        "training_result_planning_run_id": _text(metadata.get("training_result_planning_run_id")),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "ready_for_training_result_planning": _bool_prefer_metadata(metadata, safety, "ready_for_training_result_planning"),
        "training_result_planning_executed": _bool_prefer_metadata(metadata, safety, "training_result_planning_executed"),
        "training_result_planning_artifacts_created": _bool_prefer_metadata(metadata, safety, "training_result_planning_artifacts_created"),
        "source_metric_extension_run_id": _text(metadata.get("source_metric_extension_run_id")),
        "source_metric_extension_status": _text(metadata.get("source_metric_extension_status")),
        "source_metric_extension_health_status": _text(metadata.get("source_metric_extension_health_status")),
        "source_metric_computation_run_id": _text(metadata.get("source_metric_computation_run_id")),
        "source_metric_computation_status": _text(metadata.get("source_metric_computation_status")),
        "source_metric_computation_health_status": _text(metadata.get("source_metric_computation_health_status")),
        "source_metric_evaluation_planning_run_id": _text(metadata.get("source_metric_evaluation_planning_run_id")),
        "source_metric_evaluation_status": _text(metadata.get("source_metric_evaluation_status")),
        "source_metric_evaluation_health_status": _text(metadata.get("source_metric_evaluation_health_status")),
        "source_training_evaluation_run_id": _text(metadata.get("source_training_evaluation_run_id")),
        "source_training_evaluation_status": _text(metadata.get("source_training_evaluation_status")),
        "source_training_evaluation_health_status": _text(metadata.get("source_training_evaluation_health_status")),
        "source_forward_return_label_run_id": _text(metadata.get("source_forward_return_label_run_id")),
        "source_forward_return_label_status": _text(metadata.get("source_forward_return_label_status")),
        "source_forward_return_label_health_status": _text(metadata.get("source_forward_return_label_health_status")),
        "source_replay_decision_freeze_run_id": _text(metadata.get("source_replay_decision_freeze_run_id")),
        "source_replay_decision_freeze_status": _text(metadata.get("source_replay_decision_freeze_status")),
        "source_replay_decision_freeze_health_status": _text(metadata.get("source_replay_decision_freeze_health_status")),
        "metric_evidence_names_present": metric_names,
        "metric_evidence_row_count": max(_to_int(metadata.get("metric_evidence_row_count")), _row_count(metric_evidence_path)),
        "planning_input_row_count": _to_int(metadata.get("planning_input_row_count")),
        "eligible_planning_input_count": _to_int(metadata.get("eligible_planning_input_count")),
        "quarantined_planning_input_count": _to_int(metadata.get("quarantined_planning_input_count")),
        "model_scope_rows_created": _bool_prefer_metadata(metadata, safety, "model_scope_rows_created"),
        "limitations_created": _bool_prefer_metadata(metadata, safety, "limitations_created"),
        "overfit_warnings_created": _bool_prefer_metadata(metadata, safety, "overfit_warnings_created"),
        "health_plan_created": _bool_prefer_metadata(metadata, safety, "health_plan_created"),
        "status_plan_created": _bool_prefer_metadata(metadata, safety, "status_plan_created"),
        "input_index_row_count": _row_count(artifact_dir / ARTIFACT_FILES["input_index"]),
        "lineage_matrix_row_count": _row_count(artifact_dir / ARTIFACT_FILES["lineage_matrix"]),
        "model_scope_row_count": _row_count(artifact_dir / ARTIFACT_FILES["model_scope"]),
        "overfit_warning_row_count": _row_count(artifact_dir / ARTIFACT_FILES["overfit_warnings"]),
        "health_plan_row_count": _row_count(artifact_dir / ARTIFACT_FILES["health_plan"]),
        "status_plan_row_count": _row_count(artifact_dir / ARTIFACT_FILES["status_plan"]),
        **{field: _bool_any(merged, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": str(artifact_dir / ARTIFACT_FILES["report"]),
        "metadata_path": str(metadata_path),
        "input_index_path": str(artifact_dir / ARTIFACT_FILES["input_index"]),
        "metric_evidence_index_path": str(metric_evidence_path),
        "lineage_matrix_path": str(artifact_dir / ARTIFACT_FILES["lineage_matrix"]),
        "model_scope_path": str(artifact_dir / ARTIFACT_FILES["model_scope"]),
        "limitations_path": str(artifact_dir / ARTIFACT_FILES["limitations"]),
        "overfit_warnings_path": str(artifact_dir / ARTIFACT_FILES["overfit_warnings"]),
        "health_plan_path": str(artifact_dir / ARTIFACT_FILES["health_plan"]),
        "status_plan_path": str(artifact_dir / ARTIFACT_FILES["status_plan"]),
        "safety_flags_path": str(safety_path),
        "recommended_next_task_path": str(artifact_dir / ARTIFACT_FILES["recommended_next_task"]),
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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype={"symbol": "string"})
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _row_count(path: Path) -> int:
    return len(_read_csv(path))


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


def _bool_prefer_metadata(metadata: dict[str, Any], safety: dict[str, Any], field: str) -> bool:
    if field in metadata:
        return _to_bool(metadata.get(field))
    return _to_bool(safety.get(field))


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
