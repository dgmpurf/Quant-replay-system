"""Index report-only Paper Workflow Phase 1 artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.paper_workflow_phase1 import ARTIFACT_FILES
from quant_replay_system.paper_workflow_phase1 import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.paper_workflow_phase1 import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

SOURCE_FIELDS = [
    "source_stock_profile_run_id",
    "source_stock_profile_status",
    "source_stock_profile_health_status",
    "source_active_model_run_id",
    "source_active_model_status",
    "source_active_model_health_status",
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
]

INDEX_COLUMNS = [
    "paper_workflow_run_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_paper_workflow_phase1",
    "paper_workflow_phase1_executed",
    "paper_workflow_phase1_report_only_artifacts_created",
    "paper_workflow_metadata_created",
    "paper_workflow_input_index_created",
    "paper_workflow_lineage_matrix_created",
    "paper_candidate_review_context_created",
    "paper_decision_draft_created",
    "paper_review_queue_created",
    "paper_workflow_limitations_created",
    "paper_workflow_overfit_warnings_created",
    "paper_workflow_safety_flags_created",
    *SOURCE_FIELDS,
    "model_weight_reference_id",
    "model_version_id",
    "parameter_version_id",
    "candidate_review_context_row_count",
    "paper_decision_draft_row_count",
    "paper_review_queue_row_count",
    "overfit_warning_row_count",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "research_governed",
    "diagnostic_output",
    "issue_count",
    "blocker_count",
    "warning_count",
    *[f"{key}_path" for key in ARTIFACT_FILES],
]

BOOL_COLUMNS = {
    "ready_for_paper_workflow_phase1",
    "paper_workflow_phase1_executed",
    "paper_workflow_phase1_report_only_artifacts_created",
    "paper_workflow_metadata_created",
    "paper_workflow_input_index_created",
    "paper_workflow_lineage_matrix_created",
    "paper_candidate_review_context_created",
    "paper_decision_draft_created",
    "paper_review_queue_created",
    "paper_workflow_limitations_created",
    "paper_workflow_overfit_warnings_created",
    "paper_workflow_safety_flags_created",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "research_governed",
    "diagnostic_output",
}

INT_COLUMNS = {
    "candidate_review_context_row_count",
    "paper_decision_draft_row_count",
    "paper_review_queue_row_count",
    "overfit_warning_row_count",
    "issue_count",
    "blocker_count",
    "warning_count",
}


@dataclass(frozen=True)
class PaperWorkflowPhase1IndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_paper_workflow_phase1_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> PaperWorkflowPhase1IndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "paper_workflow_phase1_index.csv",
        "index_report": Path(output_dir) / "paper_workflow_phase1_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = PaperWorkflowPhase1IndexResult(
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
    write_paper_workflow_phase1_index(result)
    return result


def write_paper_workflow_phase1_index(result: PaperWorkflowPhase1IndexResult) -> dict[str, Path]:
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
                "# Paper Workflow Phase 1 Index",
                "",
                _safety_statement(),
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No paper workflow phase 1 artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Paper workflow phase 1 root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if _is_view_artifact_dir(artifact_dir.name):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["paper_workflow_metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("paper*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"paper_workflow_run_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read paper workflow metadata: {metadata_path}")
            continue
        if _text(metadata.get("paper_workflow_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    safety_path = artifact_dir / ARTIFACT_FILES["paper_workflow_safety_flags"]
    safety = _read_json(safety_path)
    merged = {**metadata, **safety}
    blocker_count = _to_int(metadata.get("blocker_count")) or _gate_blocker_count(artifact_dir)
    return {
        "paper_workflow_run_id": _text(metadata.get("paper_workflow_run_id") or artifact_dir.name),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": _text(metadata.get("execution_status") or metadata.get("status")),
        "workflow_stage": _text(metadata.get("workflow_stage") or metadata.get("status")),
        "ready_for_paper_workflow_phase1": _bool_prefer_metadata(metadata, safety, "ready_for_paper_workflow_phase1"),
        "paper_workflow_phase1_executed": _bool_prefer_metadata(metadata, safety, "paper_workflow_phase1_executed"),
        "paper_workflow_phase1_report_only_artifacts_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_phase1_report_only_artifacts_created"),
        "paper_workflow_metadata_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_metadata_created"),
        "paper_workflow_input_index_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_input_index_created") or (artifact_dir / ARTIFACT_FILES["paper_workflow_input_index"]).exists(),
        "paper_workflow_lineage_matrix_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_lineage_matrix_created") or (artifact_dir / ARTIFACT_FILES["paper_workflow_lineage_matrix"]).exists(),
        "paper_candidate_review_context_created": _bool_prefer_metadata(metadata, safety, "paper_candidate_review_context_created") or (artifact_dir / ARTIFACT_FILES["paper_candidate_review_context"]).exists(),
        "paper_decision_draft_created": _bool_prefer_metadata(metadata, safety, "paper_decision_draft_created") or (artifact_dir / ARTIFACT_FILES["paper_decision_draft"]).exists(),
        "paper_review_queue_created": _bool_prefer_metadata(metadata, safety, "paper_review_queue_created") or (artifact_dir / ARTIFACT_FILES["paper_review_queue"]).exists(),
        "paper_workflow_limitations_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_limitations_created") or (artifact_dir / ARTIFACT_FILES["paper_workflow_limitations"]).exists(),
        "paper_workflow_overfit_warnings_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_overfit_warnings_created") or (artifact_dir / ARTIFACT_FILES["paper_workflow_overfit_warnings"]).exists(),
        "paper_workflow_safety_flags_created": _bool_prefer_metadata(metadata, safety, "paper_workflow_safety_flags_created") or safety_path.exists(),
        **{field: _text(metadata.get(field)) for field in SOURCE_FIELDS},
        "model_weight_reference_id": _text(metadata.get("model_weight_reference_id")),
        "model_version_id": _text(metadata.get("model_version_id")),
        "parameter_version_id": _text(metadata.get("parameter_version_id")),
        "candidate_review_context_row_count": _row_count(artifact_dir / ARTIFACT_FILES["paper_candidate_review_context"]),
        "paper_decision_draft_row_count": _row_count(artifact_dir / ARTIFACT_FILES["paper_decision_draft"]),
        "paper_review_queue_row_count": _row_count(artifact_dir / ARTIFACT_FILES["paper_review_queue"]),
        "overfit_warning_row_count": _row_count(artifact_dir / ARTIFACT_FILES["paper_workflow_overfit_warnings"]),
        **{field: _bool_any(merged, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _bool_any(merged, "report_only"),
        "research_governed": _bool_any(merged, "research_governed"),
        "diagnostic_output": _bool_any(merged, "diagnostic_output"),
        "issue_count": 0,
        "blocker_count": blocker_count,
        "warning_count": _to_int(metadata.get("warning_count")),
        **_artifact_path_columns(artifact_dir),
    }


def _artifact_path_columns(artifact_dir: Path) -> dict[str, str]:
    return {f"{key}_path": str(artifact_dir / filename) for key, filename in ARTIFACT_FILES.items()}


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
        "paper_workflow_precondition_results",
        "paper_workflow_approval_results",
        "paper_workflow_upstream_lineage_results",
        "paper_workflow_stock_profile_input_results",
        "paper_workflow_existing_paper_context_results",
        "paper_workflow_leakage_guard_results",
        "paper_workflow_side_effect_guard_results",
        "paper_workflow_overclaim_guard_results",
    ]:
        frame = _read_csv(artifact_dir / ARTIFACT_FILES[key])
        if "status" in frame.columns:
            count += int((frame["status"].fillna("").astype(str).str.contains("BLOCKED|FAIL", regex=True)).sum())
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


def _safety_statement() -> str:
    return (
        "Paper Workflow Phase 1 is report-only artifact creation only. "
        "PAPER_WORKFLOW_PHASE1_REPORT_ONLY_ARTIFACTS_CREATED means metadata, lineage, "
        "review-context, decision draft, review queue, limitations, overfit warning, safety, "
        "and gate artifacts only; it does not create APPROVED_FOR_PAPER, does not create "
        "real buy-review eligibility, does not validate strategy performance, does not integrate "
        "current-candidates, does not build snapshots, does not mutate signal_semantics, does not "
        "create active stock_profile, does not create promoted model, does not create production "
        "model, does not create active thresholds, does not create advisory predictions, does not "
        "create active probabilities, and does not authorize broker/order/message/API/trading."
    )
