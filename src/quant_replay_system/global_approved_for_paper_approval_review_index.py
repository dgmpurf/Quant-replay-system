"""Index report-only Global APPROVED_FOR_PAPER approval-review artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.global_approved_for_paper_approval_review import ARTIFACT_FILES
from quant_replay_system.global_approved_for_paper_approval_review import DEFAULT_OUTPUT_DIR as DEFAULT_ROOT
from quant_replay_system.global_approved_for_paper_approval_review import DOWNSTREAM_FALSE_FIELDS


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

SOURCE_FIELDS = [
    "source_approved_for_paper_phase1_run_id",
    "source_approved_for_paper_phase1_status",
    "source_approved_for_paper_phase1_health_status",
    "source_paper_workflow_phase1_run_id",
    "source_model_workflow_run_id",
]

CREATED_FLAG_FIELDS = [
    "global_approved_for_paper_approval_review_metadata_created",
    "global_approved_for_paper_approval_manifest_review_created",
    "global_approved_for_paper_lineage_matrix_created",
    "global_approved_for_paper_precondition_results_created",
    "global_approved_for_paper_forbidden_output_guard_created",
    "global_approved_for_paper_overclaim_guard_created",
    "global_approved_for_paper_side_effect_guard_created",
    "global_approved_for_paper_research_status_preview_created",
    "global_approved_for_paper_limitations_created",
]

INDEX_COLUMNS = [
    "global_approved_for_paper_approval_review_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "ready_for_global_approved_for_paper_approval_review",
    "global_approved_for_paper_approval_review_executed",
    "global_approved_for_paper_approval_review_report_only_artifacts_created",
    *CREATED_FLAG_FIELDS,
    "scoped_global_approved_for_paper_approval_review",
    "global_approved_for_paper",
    "global_approved_for_paper_scope",
    *SOURCE_FIELDS,
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
    "ready_for_global_approved_for_paper_approval_review",
    "global_approved_for_paper_approval_review_executed",
    "global_approved_for_paper_approval_review_report_only_artifacts_created",
    *CREATED_FLAG_FIELDS,
    "scoped_global_approved_for_paper_approval_review",
    "global_approved_for_paper",
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "research_governed",
    "diagnostic_output",
}

INT_COLUMNS = {"issue_count", "blocker_count", "warning_count"}


@dataclass(frozen=True)
class GlobalApprovedForPaperApprovalReviewIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_global_approved_for_paper_approval_review_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> GlobalApprovedForPaperApprovalReviewIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "global_approved_for_paper_approval_review_index.csv",
        "index_report": Path(output_dir) / "global_approved_for_paper_approval_review_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = GlobalApprovedForPaperApprovalReviewIndexResult(
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
    write_global_approved_for_paper_approval_review_index(result)
    return result


def write_global_approved_for_paper_approval_review_index(
    result: GlobalApprovedForPaperApprovalReviewIndexResult,
) -> dict[str, Path]:
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
                "# Global APPROVED_FOR_PAPER Approval Review Index",
                "",
                _safety_statement(),
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                _frame_to_markdown(result.index_frame)
                if not result.index_frame.empty
                else "No Global APPROVED_FOR_PAPER approval-review artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Global APPROVED_FOR_PAPER approval-review root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if _is_view_artifact_dir(artifact_dir.name):
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["global_approved_for_paper_approval_review_metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("global_approved_for_paper*")) or (artifact_dir / ARTIFACT_FILES["recommended_next_task"]).exists():
                rows.append(_row_from_metadata(artifact_dir, metadata_path, {"global_approved_for_paper_approval_review_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read Global APPROVED_FOR_PAPER approval-review metadata: {metadata_path}")
            continue
        if _text(metadata.get("global_approved_for_paper_approval_review_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    text_frame = frame.astype(object).where(pd.notna(frame), "").astype(str)
    columns = list(text_frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in text_frame.iterrows():
        values = [_markdown_cell(row.get(column, "")) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def _markdown_cell(value: Any) -> str:
    text = _text(value).replace("\r", " ").replace("\n", " ")
    return text.replace("|", "\\|")


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status = _text(metadata.get("execution_status") or metadata.get("status"))
    return {
        "global_approved_for_paper_approval_review_id": _text(
            metadata.get("global_approved_for_paper_approval_review_id") or artifact_dir.name
        ),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": status,
        "workflow_stage": _text(metadata.get("workflow_stage")) or status,
        "ready_for_global_approved_for_paper_approval_review": _bool_any(
            metadata, "ready_for_global_approved_for_paper_approval_review"
        ),
        "global_approved_for_paper_approval_review_executed": _bool_any(
            metadata, "global_approved_for_paper_approval_review_executed"
        ),
        "global_approved_for_paper_approval_review_report_only_artifacts_created": _bool_any(
            metadata, "global_approved_for_paper_approval_review_report_only_artifacts_created"
        ),
        **{
            field: _bool_any(metadata, field) or (artifact_dir / ARTIFACT_FILES[_artifact_key_from_created_flag(field)]).exists()
            for field in CREATED_FLAG_FIELDS
        },
        "scoped_global_approved_for_paper_approval_review": _bool_any(
            metadata, "scoped_global_approved_for_paper_approval_review"
        ),
        "global_approved_for_paper": _bool_any(metadata, "global_approved_for_paper"),
        "global_approved_for_paper_scope": _text(metadata.get("global_approved_for_paper_scope")),
        **{field: _text(metadata.get(field)) for field in SOURCE_FIELDS},
        **{field: _bool_any(metadata, field) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _bool_any(metadata, "report_only"),
        "research_governed": _bool_any(metadata, "research_governed"),
        "diagnostic_output": _bool_any(metadata, "diagnostic_output"),
        "issue_count": _gate_issue_count(artifact_dir),
        "blocker_count": _gate_blocker_count(artifact_dir),
        "warning_count": 0,
        **_artifact_path_columns(artifact_dir),
    }


def _artifact_key_from_created_flag(field: str) -> str:
    return field.removesuffix("_created")


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


def _gate_issue_count(artifact_dir: Path) -> int:
    return sum(_row_count_with_status(artifact_dir / ARTIFACT_FILES[key]) for key in _gate_keys())


def _gate_blocker_count(artifact_dir: Path) -> int:
    count = 0
    for key in _gate_keys():
        frame = _read_csv(artifact_dir / ARTIFACT_FILES[key])
        if "status" in frame.columns:
            count += int((frame["status"].fillna("").astype(str).str.contains("BLOCKED|FAIL", regex=True)).sum())
    return count


def _gate_keys() -> list[str]:
    return [
        "global_approved_for_paper_precondition_results",
        "global_approved_for_paper_forbidden_output_guard",
        "global_approved_for_paper_overclaim_guard",
        "global_approved_for_paper_side_effect_guard",
    ]


def _row_count_with_status(path: Path) -> int:
    frame = _read_csv(path)
    return len(frame) if "status" in frame.columns else 0


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
        return pd.read_csv(path, dtype=str)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


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


def _safety_statement() -> str:
    return (
        "Global APPROVED_FOR_PAPER approval-review artifacts are report-only governance context. "
        "They do not create global APPROVED_FOR_PAPER as an operational state, real buy-review eligibility, "
        "buy_review_allowed, strategy performance validation, current-candidates integration, snapshots, "
        "signal_semantics mutation, active stock_profile, promoted/production models, active thresholds, "
        "advisory predictions, active probabilities, broker/order/message/API behavior, or trading."
    )
