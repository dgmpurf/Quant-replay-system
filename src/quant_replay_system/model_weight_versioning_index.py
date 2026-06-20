"""Index report-only model weights/versioning/threshold/prediction artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.model_weight_versioning import ARTIFACT_FILES
from quant_replay_system.model_weight_versioning import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.model_weight_versioning import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "model_workflow_run_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_model_weight_versioning",
    "model_weight_versioning_executed",
    "model_weight_versioning_research_artifacts_created",
    "source_training_result_run_id",
    "source_training_result_status",
    "source_training_result_health_status",
    "source_training_result_planning_run_id",
    "source_training_result_planning_status",
    "source_training_result_planning_health_status",
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
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_names_present",
    "metric_evidence_reference_count",
    "model_weights_reference_created",
    "model_version_metadata_created",
    "parameter_version_metadata_created",
    "threshold_plan_created",
    "prediction_rows_created",
    "probability_calibration_report_created",
    "feature_importance_report_created",
    "model_input_index_row_count",
    "model_lineage_matrix_row_count",
    "threshold_plan_row_count",
    "prediction_row_count",
    "feature_importance_row_count",
    "overfit_warning_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "diagnostic_only",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "model_weights_reference_path",
    "model_version_metadata_path",
    "parameter_version_metadata_path",
    "threshold_plan_path",
    "prediction_rows_path",
    "probability_calibration_report_path",
    "feature_importance_report_path",
    "model_input_index_path",
    "model_lineage_matrix_path",
    "model_limitations_path",
    "model_overfit_warnings_path",
    "model_safety_flags_path",
    "model_precondition_results_path",
    "model_approval_results_path",
    "model_input_lineage_results_path",
    "model_training_result_input_results_path",
    "model_metric_evidence_results_path",
    "model_leakage_guard_results_path",
    "model_side_effect_guard_results_path",
    "model_overclaim_guard_results_path",
    "recommended_next_task_path",
]

BOOL_COLUMNS = {
    "ready_for_model_weight_versioning",
    "model_weight_versioning_executed",
    "model_weight_versioning_research_artifacts_created",
    "model_weights_reference_created",
    "model_version_metadata_created",
    "parameter_version_metadata_created",
    "threshold_plan_created",
    "prediction_rows_created",
    "probability_calibration_report_created",
    "feature_importance_report_created",
    "report_only",
    "diagnostic_only",
    *DOWNSTREAM_FALSE_FIELDS,
}

INT_COLUMNS = {
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_reference_count",
    "model_input_index_row_count",
    "model_lineage_matrix_row_count",
    "threshold_plan_row_count",
    "prediction_row_count",
    "feature_importance_row_count",
    "overfit_warning_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class ModelWeightVersioningIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_model_weight_versioning_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ModelWeightVersioningIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "model_weight_versioning_index.csv",
        "index_report": Path(output_dir) / "model_weight_versioning_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ModelWeightVersioningIndexResult(
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
    write_model_weight_versioning_index(result)
    return result


def write_model_weight_versioning_index(result: ModelWeightVersioningIndexResult) -> dict[str, Path]:
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
                "# Model Weight Versioning Index",
                "",
                "Report-only index for model weights/versioning/threshold/prediction phase 1 artifacts. "
                "MODEL_WEIGHT_VERSIONING_RESEARCH_ARTIFACTS_CREATED means report-only research artifacts only: "
                "not active stock_profile, not buy-review, not paper approval, not performance validation, "
                "not executable trading model, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No model weight versioning artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Model weight versioning root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if _is_view_artifact_dir(artifact_dir.name):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["model_training_metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("model_*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"model_workflow_run_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read model weight versioning metadata: {metadata_path}")
            continue
        if _text(metadata.get("model_workflow_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / ARTIFACT_FILES["model_safety_flags"]
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    metric_results = _read_csv(artifact_dir / ARTIFACT_FILES["model_metric_evidence_results"])
    metric_names = _text(metadata.get("metric_evidence_names_present"))
    if not metric_names and not metric_results.empty and "gate_name" in metric_results.columns:
        metric_names = ",".join(sorted(metric_results["gate_name"].dropna().astype(str).unique()))
    blocker_count = _to_int(metadata.get("blocker_count"))
    if blocker_count == 0:
        blocker_count = _gate_blocker_count(artifact_dir)
    return {
        "model_workflow_run_id": _text(metadata.get("model_workflow_run_id") or artifact_dir.name),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("status")),
        "ready_for_model_weight_versioning": _bool_prefer_metadata(metadata, safety, "ready_for_model_weight_versioning"),
        "model_weight_versioning_executed": _bool_prefer_metadata(metadata, safety, "model_weight_versioning_executed"),
        "model_weight_versioning_research_artifacts_created": _bool_prefer_metadata(metadata, safety, "model_weight_versioning_research_artifacts_created"),
        "source_training_result_run_id": _text(metadata.get("source_training_result_run_id")),
        "source_training_result_status": _text(metadata.get("source_training_result_status")),
        "source_training_result_health_status": _text(metadata.get("source_training_result_health_status")),
        "source_training_result_planning_run_id": _text(metadata.get("source_training_result_planning_run_id")),
        "source_training_result_planning_status": _text(metadata.get("source_training_result_planning_status")),
        "source_training_result_planning_health_status": _text(metadata.get("source_training_result_planning_health_status")),
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
        "training_result_row_count": _to_int(metadata.get("training_result_row_count")),
        "eligible_training_result_row_count": _to_int(metadata.get("eligible_training_result_row_count")),
        "quarantined_training_result_row_count": _to_int(metadata.get("quarantined_training_result_row_count")),
        "metric_evidence_names_present": metric_names,
        "metric_evidence_reference_count": max(_to_int(metadata.get("metric_evidence_reference_count")), _row_count(artifact_dir / ARTIFACT_FILES["model_metric_evidence_results"])),
        "model_weights_reference_created": _bool_prefer_metadata(metadata, safety, "model_weights_reference_created") or (artifact_dir / ARTIFACT_FILES["model_weights_reference"]).exists(),
        "model_version_metadata_created": _bool_prefer_metadata(metadata, safety, "model_version_metadata_created") or (artifact_dir / ARTIFACT_FILES["model_version_metadata"]).exists(),
        "parameter_version_metadata_created": _bool_prefer_metadata(metadata, safety, "parameter_version_metadata_created") or (artifact_dir / ARTIFACT_FILES["parameter_version_metadata"]).exists(),
        "threshold_plan_created": _bool_prefer_metadata(metadata, safety, "threshold_plan_created") or (artifact_dir / ARTIFACT_FILES["threshold_plan"]).exists(),
        "prediction_rows_created": _bool_prefer_metadata(metadata, safety, "prediction_rows_created") or (artifact_dir / ARTIFACT_FILES["prediction_rows"]).exists(),
        "probability_calibration_report_created": _bool_prefer_metadata(metadata, safety, "probability_calibration_report_created") or (artifact_dir / ARTIFACT_FILES["probability_calibration_report"]).exists(),
        "feature_importance_report_created": _bool_prefer_metadata(metadata, safety, "feature_importance_report_created") or (artifact_dir / ARTIFACT_FILES["feature_importance_report"]).exists(),
        "model_input_index_row_count": _row_count(artifact_dir / ARTIFACT_FILES["model_input_index"]),
        "model_lineage_matrix_row_count": _row_count(artifact_dir / ARTIFACT_FILES["model_lineage_matrix"]),
        "threshold_plan_row_count": _row_count(artifact_dir / ARTIFACT_FILES["threshold_plan"]),
        "prediction_row_count": _row_count(artifact_dir / ARTIFACT_FILES["prediction_rows"]),
        "feature_importance_row_count": _row_count(artifact_dir / ARTIFACT_FILES["feature_importance_report"]),
        "overfit_warning_row_count": _row_count(artifact_dir / ARTIFACT_FILES["model_overfit_warnings"]),
        **{field: _bool_any(merged, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "issue_count": 0,
        "blocker_count": blocker_count,
        "warning_count": _to_int(metadata.get("warning_count")),
        **_artifact_path_columns(artifact_dir, metadata_path),
    }


def _artifact_path_columns(artifact_dir: Path, metadata_path: Path) -> dict[str, str]:
    return {
        "report_path": str(artifact_dir / ARTIFACT_FILES["report"]),
        "metadata_path": str(metadata_path),
        "model_weights_reference_path": str(artifact_dir / ARTIFACT_FILES["model_weights_reference"]),
        "model_version_metadata_path": str(artifact_dir / ARTIFACT_FILES["model_version_metadata"]),
        "parameter_version_metadata_path": str(artifact_dir / ARTIFACT_FILES["parameter_version_metadata"]),
        "threshold_plan_path": str(artifact_dir / ARTIFACT_FILES["threshold_plan"]),
        "prediction_rows_path": str(artifact_dir / ARTIFACT_FILES["prediction_rows"]),
        "probability_calibration_report_path": str(artifact_dir / ARTIFACT_FILES["probability_calibration_report"]),
        "feature_importance_report_path": str(artifact_dir / ARTIFACT_FILES["feature_importance_report"]),
        "model_input_index_path": str(artifact_dir / ARTIFACT_FILES["model_input_index"]),
        "model_lineage_matrix_path": str(artifact_dir / ARTIFACT_FILES["model_lineage_matrix"]),
        "model_limitations_path": str(artifact_dir / ARTIFACT_FILES["model_limitations"]),
        "model_overfit_warnings_path": str(artifact_dir / ARTIFACT_FILES["model_overfit_warnings"]),
        "model_safety_flags_path": str(artifact_dir / ARTIFACT_FILES["model_safety_flags"]),
        "model_precondition_results_path": str(artifact_dir / ARTIFACT_FILES["model_precondition_results"]),
        "model_approval_results_path": str(artifact_dir / ARTIFACT_FILES["model_approval_results"]),
        "model_input_lineage_results_path": str(artifact_dir / ARTIFACT_FILES["model_input_lineage_results"]),
        "model_training_result_input_results_path": str(artifact_dir / ARTIFACT_FILES["model_training_result_input_results"]),
        "model_metric_evidence_results_path": str(artifact_dir / ARTIFACT_FILES["model_metric_evidence_results"]),
        "model_leakage_guard_results_path": str(artifact_dir / ARTIFACT_FILES["model_leakage_guard_results"]),
        "model_side_effect_guard_results_path": str(artifact_dir / ARTIFACT_FILES["model_side_effect_guard_results"]),
        "model_overclaim_guard_results_path": str(artifact_dir / ARTIFACT_FILES["model_overclaim_guard_results"]),
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


def _is_view_artifact_dir(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in {"index", "health", "status"}
        or lowered.startswith(("index", "health", "status", "_"))
        or lowered.endswith(("_index", "_health", "_status"))
        or lowered.startswith(("cli_index", "cli_health", "cli_status"))
    )


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


def _gate_blocker_count(artifact_dir: Path) -> int:
    count = 0
    for key in [
        "model_precondition_results",
        "model_approval_results",
        "model_input_lineage_results",
        "model_training_result_input_results",
        "model_metric_evidence_results",
        "model_leakage_guard_results",
        "model_side_effect_guard_results",
        "model_overclaim_guard_results",
    ]:
        frame = _read_csv(artifact_dir / ARTIFACT_FILES[key])
        if "passed" in frame.columns:
            count += int((~frame["passed"].map(_to_bool)).sum())
    return count


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
