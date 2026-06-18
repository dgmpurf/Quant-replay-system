"""Index report-only metric computation phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.metric_computation import ALLOWED_METRIC_SET
from quant_replay_system.metric_computation import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.metric_computation import FORBIDDEN_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

INDEX_COLUMNS = [
    "metric_computation_run_id",
    "generated_at",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "source_metric_evaluation_planning_run_id",
    "source_metric_evaluation_status",
    "source_metric_evaluation_health_status",
    "source_training_evaluation_run_id",
    "source_training_evaluation_status",
    "source_training_evaluation_health_status",
    "source_forward_return_label_run_id",
    "source_replay_decision_freeze_run_id",
    "allowed_metric_set",
    "requested_metric_set",
    "unsupported_metrics_requested",
    "sample_row_count",
    "eligible_sample_count",
    "quarantined_sample_count",
    "label_coverage_numerator",
    "label_coverage_denominator",
    "ready_for_metric_computation",
    "metric_computation_executed",
    "metric_computation_report_created",
    "metric_result_rows_created",
    "metric_summary_created",
    "metrics_computed",
    "metric_names_present",
    "result_row_count",
    "summary_row_count",
    *FORBIDDEN_FALSE_FIELDS,
    "report_only",
    "diagnostic_only",
    "issue_count",
    "blocker_count",
    "warning_count",
    "report_path",
    "metadata_path",
    "input_index_path",
    "metric_definitions_used_path",
    "sample_scope_used_path",
    "denominator_rules_used_path",
    "result_rows_path",
    "summary_path",
    "safety_flags_path",
]

BOOL_COLUMNS = {
    "unsupported_metrics_requested",
    "ready_for_metric_computation",
    "metric_computation_executed",
    "metric_computation_report_created",
    "metric_result_rows_created",
    "metric_summary_created",
    "metrics_computed",
    "report_only",
    "diagnostic_only",
    *FORBIDDEN_FALSE_FIELDS,
}

INT_COLUMNS = {
    "sample_row_count",
    "eligible_sample_count",
    "quarantined_sample_count",
    "label_coverage_numerator",
    "label_coverage_denominator",
    "result_row_count",
    "summary_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class MetricComputationIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_metric_computation_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> MetricComputationIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "metric_computation_index.csv",
        "index_report": Path(output_dir) / "metric_computation_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MetricComputationIndexResult(
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
    write_metric_computation_index(result)
    return result


def write_metric_computation_index(result: MetricComputationIndexResult) -> dict[str, Path]:
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
                "# Metric Computation Index",
                "",
                "Report-only metric computation phase 1 index. METRIC_COMPUTATION_REPORT_CREATED means bounded historical metric rows only: not strategy validation, not training_result, not weights, not model_version, not thresholds, not predictions, not stock_profile, not buy-review, not paper approval, not performance validation, and not trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No metric computation artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Metric computation root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metric_computation_metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read metric computation metadata: {metadata_path}")
            continue
        if _text(metadata.get("metric_computation_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / "metric_computation_safety_flags.json"
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    for field in BOOL_COLUMNS:
        if _bool_any(metadata, field) or _bool_any(safety, field):
            merged[field] = True
    result_rows_path = artifact_dir / "metric_computation_result_rows.csv"
    summary_path = artifact_dir / "metric_computation_summary.csv"
    result_rows = _read_csv(result_rows_path)
    metric_names = ""
    if not result_rows.empty and "metric_name" in result_rows.columns:
        metric_names = ",".join(str(name) for name in result_rows["metric_name"].dropna().astype(str).tolist())
    return {
        "metric_computation_run_id": _text(metadata.get("metric_computation_run_id")),
        "generated_at": _text(metadata.get("generated_at") or metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "created_at": _text(metadata.get("created_at") or metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("execution_status") or metadata.get("status")),
        "source_metric_evaluation_planning_run_id": _text(metadata.get("source_metric_evaluation_planning_run_id")),
        "source_metric_evaluation_status": _text(metadata.get("source_metric_evaluation_status")),
        "source_metric_evaluation_health_status": _text(metadata.get("source_metric_evaluation_health_status")),
        "source_training_evaluation_run_id": _text(metadata.get("source_training_evaluation_run_id")),
        "source_training_evaluation_status": _text(metadata.get("source_training_evaluation_status")),
        "source_training_evaluation_health_status": _text(metadata.get("source_training_evaluation_health_status")),
        "source_forward_return_label_run_id": _text(metadata.get("source_forward_return_label_run_id")),
        "source_replay_decision_freeze_run_id": _text(metadata.get("source_replay_decision_freeze_run_id")),
        "allowed_metric_set": _text(metadata.get("allowed_metric_set")) or ",".join(ALLOWED_METRIC_SET),
        "requested_metric_set": _text(metadata.get("requested_metric_set")),
        "unsupported_metrics_requested": _bool_prefer_metadata(metadata, safety, "unsupported_metrics_requested"),
        "sample_row_count": _to_int(metadata.get("sample_row_count")),
        "eligible_sample_count": _to_int(metadata.get("eligible_sample_count")),
        "quarantined_sample_count": _to_int(metadata.get("quarantined_sample_count")),
        "label_coverage_numerator": _to_int(metadata.get("label_coverage_numerator")),
        "label_coverage_denominator": _to_int(metadata.get("label_coverage_denominator")),
        "ready_for_metric_computation": _bool_prefer_metadata(metadata, safety, "ready_for_metric_computation"),
        "metric_computation_executed": _bool_prefer_metadata(metadata, safety, "metric_computation_executed"),
        "metric_computation_report_created": _bool_prefer_metadata(metadata, safety, "metric_computation_report_created"),
        "metric_result_rows_created": _bool_prefer_metadata(metadata, safety, "metric_result_rows_created"),
        "metric_summary_created": _bool_prefer_metadata(metadata, safety, "metric_summary_created"),
        "metrics_computed": _bool_prefer_metadata(metadata, safety, "metrics_computed"),
        "metric_names_present": metric_names,
        "result_row_count": _row_count(result_rows_path),
        "summary_row_count": _row_count(summary_path),
        **{field: _bool_any(merged, field) for field in FORBIDDEN_FALSE_FIELDS},
        "report_only": _bool_any(merged, "report_only"),
        "diagnostic_only": _bool_any(merged, "diagnostic_only"),
        "issue_count": _to_int(metadata.get("issue_count")),
        "blocker_count": _to_int(metadata.get("blocker_count")),
        "warning_count": _to_int(metadata.get("warning_count")),
        "report_path": str(artifact_dir / "metric_computation_report.md"),
        "metadata_path": str(metadata_path),
        "input_index_path": str(artifact_dir / "metric_computation_input_index.csv"),
        "metric_definitions_used_path": str(artifact_dir / "metric_computation_metric_definitions_used.csv"),
        "sample_scope_used_path": str(artifact_dir / "metric_computation_sample_scope_used.csv"),
        "denominator_rules_used_path": str(artifact_dir / "metric_computation_denominator_rules_used.csv"),
        "result_rows_path": str(result_rows_path),
        "summary_path": str(summary_path),
        "safety_flags_path": str(safety_path),
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
