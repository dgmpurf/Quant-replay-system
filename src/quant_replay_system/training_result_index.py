"""Index report-only actual training_result phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.training_result import ARTIFACT_FILES
from quant_replay_system.training_result import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.training_result import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "training_result_run_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_training_result",
    "training_result_executed",
    "training_result_created",
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
    "metric_evidence_names_present",
    "metric_evidence_reference_count",
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "limitations_created",
    "overfit_warnings_created",
    "input_index_row_count",
    "metric_evidence_reference_row_count",
    "lineage_matrix_row_count",
    "overfit_warning_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "diagnostic_only",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "rows_path",
    "status_json_path",
    "input_index_path",
    "metric_evidence_reference_path",
    "lineage_matrix_path",
    "limitations_path",
    "overfit_warnings_path",
    "safety_flags_path",
    "precondition_results_path",
    "approval_results_path",
    "input_lineage_results_path",
    "metric_evidence_results_path",
    "leakage_guard_results_path",
    "side_effect_guard_results_path",
    "overclaim_guard_results_path",
    "recommended_next_task_path",
]

BOOL_COLUMNS = {
    "ready_for_training_result",
    "training_result_executed",
    "training_result_created",
    "limitations_created",
    "overfit_warnings_created",
    "report_only",
    "diagnostic_only",
    *DOWNSTREAM_FALSE_FIELDS,
}

INT_COLUMNS = {
    "metric_evidence_reference_count",
    "training_result_row_count",
    "eligible_training_result_row_count",
    "quarantined_training_result_row_count",
    "input_index_row_count",
    "metric_evidence_reference_row_count",
    "lineage_matrix_row_count",
    "overfit_warning_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class TrainingResultIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_training_result_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> TrainingResultIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "training_result_index.csv",
        "index_report": Path(output_dir) / "training_result_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = TrainingResultIndexResult(
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
    write_training_result_index(result)
    return result


def write_training_result_index(result: TrainingResultIndexResult) -> dict[str, Path]:
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
                "# Actual Training Result Index",
                "",
                "Report-only index for actual training_result phase 1 artifacts. TRAINING_RESULT_CREATED means report-only actual training_result artifacts only: not weights, not model_version, not parameter_version, not thresholds, not predictions/probabilities/feature importance, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No training_result artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Training result root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if _is_view_artifact_dir(artifact_dir.name):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("training_result_*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"training_result_run_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read training_result metadata: {metadata_path}")
            continue
        if _text(metadata.get("training_result_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / ARTIFACT_FILES["safety_flags"]
    safety = _read_json(safety_path)
    status_path = artifact_dir / ARTIFACT_FILES["status_json"]
    status_json = _read_json(status_path)
    merged = {**metadata, **status_json, **safety}
    rows_path = artifact_dir / ARTIFACT_FILES["rows"]
    input_index_path = artifact_dir / ARTIFACT_FILES["input_index"]
    metric_reference_path = artifact_dir / ARTIFACT_FILES["metric_evidence_reference"]
    lineage_path = artifact_dir / ARTIFACT_FILES["lineage_matrix"]
    warnings_path = artifact_dir / ARTIFACT_FILES["overfit_warnings"]
    metric_evidence = _read_csv(metric_reference_path)
    metric_names = _text(metadata.get("metric_evidence_names_present") or status_json.get("metric_evidence_names_present"))
    if not metric_names and not metric_evidence.empty and "metric_name" in metric_evidence.columns:
        metric_names = ",".join(sorted(metric_evidence["metric_name"].dropna().astype(str).unique()))
    return {
        "training_result_run_id": _text(metadata.get("training_result_run_id") or status_json.get("training_result_run_id") or artifact_dir.name),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status") or status_json.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or status_json.get("workflow_stage") or metadata.get("status") or status_json.get("status")),
        "ready_for_training_result": _bool_prefer_metadata(metadata, safety, "ready_for_training_result"),
        "training_result_executed": _bool_prefer_metadata(metadata, safety, "training_result_executed"),
        "training_result_created": _bool_prefer_metadata(metadata, safety, "training_result_created"),
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
        "metric_evidence_names_present": metric_names,
        "metric_evidence_reference_count": max(_to_int(metadata.get("metric_evidence_reference_count")), _row_count(metric_reference_path)),
        "training_result_row_count": max(_to_int(metadata.get("training_result_row_count")), _row_count(rows_path)),
        "eligible_training_result_row_count": _to_int(metadata.get("eligible_training_result_row_count")),
        "quarantined_training_result_row_count": _to_int(metadata.get("quarantined_training_result_row_count")),
        "limitations_created": _bool_prefer_metadata(metadata, safety, "limitations_created"),
        "overfit_warnings_created": _bool_prefer_metadata(metadata, safety, "overfit_warnings_created"),
        "input_index_row_count": _row_count(input_index_path),
        "metric_evidence_reference_row_count": _row_count(metric_reference_path),
        "lineage_matrix_row_count": _row_count(lineage_path),
        "overfit_warning_row_count": _row_count(warnings_path),
        **{field: _bool_any(merged, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": str(artifact_dir / ARTIFACT_FILES["report"]),
        "metadata_path": str(metadata_path),
        "rows_path": str(rows_path),
        "status_json_path": str(status_path),
        "input_index_path": str(input_index_path),
        "metric_evidence_reference_path": str(metric_reference_path),
        "lineage_matrix_path": str(lineage_path),
        "limitations_path": str(artifact_dir / ARTIFACT_FILES["limitations"]),
        "overfit_warnings_path": str(warnings_path),
        "safety_flags_path": str(safety_path),
        "precondition_results_path": str(artifact_dir / ARTIFACT_FILES["precondition_results"]),
        "approval_results_path": str(artifact_dir / ARTIFACT_FILES["approval_results"]),
        "input_lineage_results_path": str(artifact_dir / ARTIFACT_FILES["input_lineage_results"]),
        "metric_evidence_results_path": str(artifact_dir / ARTIFACT_FILES["metric_evidence_results"]),
        "leakage_guard_results_path": str(artifact_dir / ARTIFACT_FILES["leakage_guard_results"]),
        "side_effect_guard_results_path": str(artifact_dir / ARTIFACT_FILES["side_effect_guard_results"]),
        "overclaim_guard_results_path": str(artifact_dir / ARTIFACT_FILES["overclaim_guard_results"]),
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
