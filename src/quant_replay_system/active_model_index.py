"""Index research-governed active model phase 1 report-only artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.active_model import ARTIFACT_FILES
from quant_replay_system.active_model import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.active_model import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "active_model_run_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_active_model",
    "active_model_executed",
    "active_model_artifacts_created",
    "active_model_pointer_created",
    "active_model_registry_entry_created",
    "active_parameter_pointer_created",
    "active_model_activation_status_created",
    "active_model_rollback_plan_created",
    "active_model_input_index_created",
    "active_model_lineage_matrix_created",
    "active_model_limitations_created",
    "active_model_overfit_warnings_created",
    "active_model_safety_flags_created",
    "source_model_workflow_run_id",
    "source_model_weight_versioning_status",
    "source_model_weight_versioning_health_status",
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
    "model_weight_reference_id",
    "model_version_id",
    "parameter_version_id",
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_names_present",
    "metric_evidence_reference_count",
    "input_index_row_count",
    "lineage_matrix_row_count",
    "overfit_warning_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "research_governed",
    "diagnostic_output",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "active_model_pointer_path",
    "active_model_registry_entry_path",
    "active_parameter_pointer_path",
    "active_model_activation_status_path",
    "active_model_rollback_plan_path",
    "active_model_input_index_path",
    "active_model_lineage_matrix_path",
    "active_model_limitations_path",
    "active_model_overfit_warnings_path",
    "active_model_safety_flags_path",
    "active_model_precondition_results_path",
    "active_model_approval_results_path",
    "active_model_input_lineage_results_path",
    "active_model_model_weight_versioning_input_results_path",
    "active_model_metric_evidence_results_path",
    "active_model_leakage_guard_results_path",
    "active_model_side_effect_guard_results_path",
    "active_model_overclaim_guard_results_path",
    "recommended_next_task_path",
]

BOOL_COLUMNS = {
    "ready_for_active_model",
    "active_model_executed",
    "active_model_artifacts_created",
    "active_model_pointer_created",
    "active_model_registry_entry_created",
    "active_parameter_pointer_created",
    "active_model_activation_status_created",
    "active_model_rollback_plan_created",
    "active_model_input_index_created",
    "active_model_lineage_matrix_created",
    "active_model_limitations_created",
    "active_model_overfit_warnings_created",
    "active_model_safety_flags_created",
    "research_governed",
    "diagnostic_output",
    *DOWNSTREAM_FALSE_FIELDS,
}

INT_COLUMNS = {
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "metric_evidence_reference_count",
    "input_index_row_count",
    "lineage_matrix_row_count",
    "overfit_warning_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class ActiveModelIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_active_model_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> ActiveModelIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "active_model_index.csv",
        "index_report": Path(output_dir) / "active_model_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ActiveModelIndexResult(
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
    write_active_model_index(result)
    return result


def write_active_model_index(result: ActiveModelIndexResult) -> dict[str, Path]:
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
                "# Active Model Index",
                "",
                "Report-only index for research-governed Active Model Phase 1 artifacts. "
                "ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED means diagnostics metadata, pointer, "
                "registry, parameter, activation, rollback, lineage, limitations, warning, and safety artifacts only: "
                "not promoted model, not production model, not active thresholds, not advisory predictions, "
                "not active probabilities, not stock_profile, not paper approval, not performance validation, "
                "not current-candidates, not snapshots, not signal semantics mutation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No active model artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Active model root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if _is_view_artifact_dir(artifact_dir.name):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["active_model_metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("active_model*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"active_model_run_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read active model metadata: {metadata_path}")
            continue
        if _text(metadata.get("active_model_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / ARTIFACT_FILES["active_model_safety_flags"]
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    metric_names = _text(metadata.get("metric_evidence_names_present"))
    metric_results = _read_csv(artifact_dir / ARTIFACT_FILES["active_model_metric_evidence_results"])
    if not metric_names and not metric_results.empty and "gate_name" in metric_results.columns:
        metric_names = ",".join(sorted(metric_results["gate_name"].dropna().astype(str).unique()))
    blocker_count = _to_int(metadata.get("blocker_count"))
    if blocker_count == 0:
        blocker_count = _gate_blocker_count(artifact_dir)
    return {
        "active_model_run_id": _text(metadata.get("active_model_run_id") or artifact_dir.name),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("status")),
        "ready_for_active_model": _bool_prefer_metadata(metadata, safety, "ready_for_active_model"),
        "active_model_executed": _bool_prefer_metadata(metadata, safety, "active_model_executed"),
        "active_model_artifacts_created": _bool_prefer_metadata(metadata, safety, "active_model_artifacts_created"),
        "active_model_pointer_created": _bool_prefer_metadata(metadata, safety, "active_model_pointer_created") or (artifact_dir / ARTIFACT_FILES["active_model_pointer"]).exists(),
        "active_model_registry_entry_created": _bool_prefer_metadata(metadata, safety, "active_model_registry_entry_created") or (artifact_dir / ARTIFACT_FILES["active_model_registry_entry"]).exists(),
        "active_parameter_pointer_created": _bool_prefer_metadata(metadata, safety, "active_parameter_pointer_created") or (artifact_dir / ARTIFACT_FILES["active_parameter_pointer"]).exists(),
        "active_model_activation_status_created": _bool_prefer_metadata(metadata, safety, "active_model_activation_status_created") or (artifact_dir / ARTIFACT_FILES["active_model_activation_status"]).exists(),
        "active_model_rollback_plan_created": _bool_prefer_metadata(metadata, safety, "active_model_rollback_plan_created") or (artifact_dir / ARTIFACT_FILES["active_model_rollback_plan"]).exists(),
        "active_model_input_index_created": _bool_prefer_metadata(metadata, safety, "active_model_input_index_created") or (artifact_dir / ARTIFACT_FILES["active_model_input_index"]).exists(),
        "active_model_lineage_matrix_created": _bool_prefer_metadata(metadata, safety, "active_model_lineage_matrix_created") or (artifact_dir / ARTIFACT_FILES["active_model_lineage_matrix"]).exists(),
        "active_model_limitations_created": _bool_prefer_metadata(metadata, safety, "active_model_limitations_created") or (artifact_dir / ARTIFACT_FILES["active_model_limitations"]).exists(),
        "active_model_overfit_warnings_created": _bool_prefer_metadata(metadata, safety, "active_model_overfit_warnings_created") or (artifact_dir / ARTIFACT_FILES["active_model_overfit_warnings"]).exists(),
        "active_model_safety_flags_created": _bool_prefer_metadata(metadata, safety, "active_model_safety_flags_created") or safety_path.exists(),
        "source_model_workflow_run_id": _text(metadata.get("source_model_workflow_run_id")),
        "source_model_weight_versioning_status": _text(metadata.get("source_model_weight_versioning_status")),
        "source_model_weight_versioning_health_status": _text(metadata.get("source_model_weight_versioning_health_status")),
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
        "model_weight_reference_id": _text(metadata.get("model_weight_reference_id")),
        "model_version_id": _text(metadata.get("model_version_id")),
        "parameter_version_id": _text(metadata.get("parameter_version_id")),
        "training_result_row_count": _to_int(metadata.get("training_result_row_count")),
        "eligible_training_result_row_count": _to_int(metadata.get("eligible_training_result_row_count")),
        "quarantined_training_result_row_count": _to_int(metadata.get("quarantined_training_result_row_count")),
        "metric_evidence_names_present": metric_names,
        "metric_evidence_reference_count": max(_to_int(metadata.get("metric_evidence_reference_count")), _row_count(artifact_dir / ARTIFACT_FILES["active_model_metric_evidence_results"])),
        "input_index_row_count": _row_count(artifact_dir / ARTIFACT_FILES["active_model_input_index"]),
        "lineage_matrix_row_count": _row_count(artifact_dir / ARTIFACT_FILES["active_model_lineage_matrix"]),
        "overfit_warning_row_count": _row_count(artifact_dir / ARTIFACT_FILES["active_model_overfit_warnings"]),
        **{field: _bool_any(merged, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "research_governed": _bool_any(merged, "research_governed"),
        "diagnostic_output": _bool_any(merged, "diagnostic_output"),
        "issue_count": 0,
        "blocker_count": blocker_count,
        "warning_count": _to_int(metadata.get("warning_count")),
        **_artifact_path_columns(artifact_dir, metadata_path),
    }


def _artifact_path_columns(artifact_dir: Path, metadata_path: Path) -> dict[str, str]:
    return {
        "report_path": str(artifact_dir / ARTIFACT_FILES["report"]),
        "metadata_path": str(metadata_path),
        "active_model_pointer_path": str(artifact_dir / ARTIFACT_FILES["active_model_pointer"]),
        "active_model_registry_entry_path": str(artifact_dir / ARTIFACT_FILES["active_model_registry_entry"]),
        "active_parameter_pointer_path": str(artifact_dir / ARTIFACT_FILES["active_parameter_pointer"]),
        "active_model_activation_status_path": str(artifact_dir / ARTIFACT_FILES["active_model_activation_status"]),
        "active_model_rollback_plan_path": str(artifact_dir / ARTIFACT_FILES["active_model_rollback_plan"]),
        "active_model_input_index_path": str(artifact_dir / ARTIFACT_FILES["active_model_input_index"]),
        "active_model_lineage_matrix_path": str(artifact_dir / ARTIFACT_FILES["active_model_lineage_matrix"]),
        "active_model_limitations_path": str(artifact_dir / ARTIFACT_FILES["active_model_limitations"]),
        "active_model_overfit_warnings_path": str(artifact_dir / ARTIFACT_FILES["active_model_overfit_warnings"]),
        "active_model_safety_flags_path": str(artifact_dir / ARTIFACT_FILES["active_model_safety_flags"]),
        "active_model_precondition_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_precondition_results"]),
        "active_model_approval_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_approval_results"]),
        "active_model_input_lineage_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_input_lineage_results"]),
        "active_model_model_weight_versioning_input_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_model_weight_versioning_input_results"]),
        "active_model_metric_evidence_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_metric_evidence_results"]),
        "active_model_leakage_guard_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_leakage_guard_results"]),
        "active_model_side_effect_guard_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_side_effect_guard_results"]),
        "active_model_overclaim_guard_results_path": str(artifact_dir / ARTIFACT_FILES["active_model_overclaim_guard_results"]),
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
        "active_model_precondition_results",
        "active_model_approval_results",
        "active_model_input_lineage_results",
        "active_model_model_weight_versioning_input_results",
        "active_model_metric_evidence_results",
        "active_model_leakage_guard_results",
        "active_model_side_effect_guard_results",
        "active_model_overclaim_guard_results",
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
