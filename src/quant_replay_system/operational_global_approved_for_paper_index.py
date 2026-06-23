"""Index report-only Operational Global APPROVED_FOR_PAPER planning artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.operational_global_approved_for_paper import (
    ARTIFACT_FILES,
    DEFAULT_OUTPUT_DIR as DEFAULT_ROOT,
    DOWNSTREAM_FALSE_FIELDS,
)


DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "index"

CORE_FALSE_FIELDS = [
    "operational_global_approved_for_paper_granted",
    "global_approved_for_paper",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
]

CREATED_FLAG_FIELDS = [
    "operational_global_approved_for_paper_metadata_created",
    "operational_global_approved_for_paper_manifest_review_created",
    "operational_global_approved_for_paper_lineage_matrix_created",
    "operational_global_approved_for_paper_health_gate_results_created",
    "operational_global_approved_for_paper_forbidden_output_guard_created",
    "operational_global_approved_for_paper_side_effect_guard_created",
    "operational_global_approved_for_paper_overclaim_guard_created",
    "operational_global_approved_for_paper_limitations_created",
    "operational_global_approved_for_paper_revocation_plan_created",
]

INDEX_COLUMNS = [
    "operational_global_approved_for_paper_id",
    "created_at",
    "artifact_path",
    "status",
    "workflow_stage",
    "health_status",
    "ready_for_operational_global_approved_for_paper_review",
    "operational_global_approved_for_paper_executed",
    "operational_global_approved_for_paper_planning_artifacts_created",
    *CREATED_FLAG_FIELDS,
    *CORE_FALSE_FIELDS,
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "research_governed",
    "diagnostic_output",
    "blocker_count",
    "warning_count",
    *[f"{key}_path" for key in ARTIFACT_FILES],
]

BOOL_COLUMNS = {
    "ready_for_operational_global_approved_for_paper_review",
    "operational_global_approved_for_paper_executed",
    "operational_global_approved_for_paper_planning_artifacts_created",
    *CREATED_FLAG_FIELDS,
    *CORE_FALSE_FIELDS,
    *DOWNSTREAM_FALSE_FIELDS,
    "report_only",
    "research_governed",
    "diagnostic_output",
}

INT_COLUMNS = {"blocker_count", "warning_count"}


@dataclass(frozen=True)
class OperationalGlobalApprovedForPaperIndexResult:
    artifact_count: int
    latest_run_id: str
    latest_status: str
    latest_workflow_stage: str
    latest_health_status: str
    latest_artifact_path: str
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_operational_global_approved_for_paper_index(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> OperationalGlobalApprovedForPaperIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "operational_global_approved_for_paper_index.csv",
        "index_report": Path(output_dir) / "operational_global_approved_for_paper_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = OperationalGlobalApprovedForPaperIndexResult(
        artifact_count=len(frame),
        latest_run_id=_text(latest.get("operational_global_approved_for_paper_id")) if latest else "",
        latest_status=_text(latest.get("status")) if latest else "",
        latest_workflow_stage=_text(latest.get("workflow_stage")) if latest else "",
        latest_health_status=_text(latest.get("health_status")) if latest else "",
        latest_artifact_path=_text(latest.get("artifact_path")) if latest else "",
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
    write_operational_global_approved_for_paper_index(result)
    return result


def write_operational_global_approved_for_paper_index(
    result: OperationalGlobalApprovedForPaperIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "index_id": _hash_payload(result.index_frame.to_dict("records")),
                "artifact_count": result.artifact_count,
                "latest_run_id": result.latest_run_id,
                "latest_status": result.latest_status,
                "latest_workflow_stage": result.latest_workflow_stage,
                "latest_health_status": result.latest_health_status,
                "latest_artifact_path": result.latest_artifact_path,
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
                "# Operational Global APPROVED_FOR_PAPER Index",
                "",
                _safety_statement(),
                "",
                f"- artifact_count: {result.artifact_count}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- latest_status: {result.latest_status}",
                "",
                _frame_to_markdown(result.index_frame)
                if not result.index_frame.empty
                else "No Operational Global APPROVED_FOR_PAPER planning artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Operational Global APPROVED_FOR_PAPER root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / ARTIFACT_FILES["operational_global_approved_for_paper_metadata"]
        if not metadata_path.exists():
            if any(artifact_dir.glob("operational_global_approved_for_paper*")):
                rows.append(_row_from_metadata(artifact_dir, {"operational_global_approved_for_paper_id": artifact_dir.name}))
            continue
        metadata = _read_json(metadata_path)
        if not metadata:
            warnings.append(f"Could not read Operational Global APPROVED_FOR_PAPER metadata: {metadata_path}")
            rows.append(_row_from_metadata(artifact_dir, {"operational_global_approved_for_paper_id": artifact_dir.name}))
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status = _text(metadata.get("status"))
    created = _to_bool(metadata.get("operational_global_approved_for_paper_planning_artifacts_created"))
    return {
        "operational_global_approved_for_paper_id": _text(
            metadata.get("operational_global_approved_for_paper_id") or artifact_dir.name
        ),
        "created_at": _text(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": str(artifact_dir),
        "status": status,
        "workflow_stage": _text(metadata.get("workflow_stage")) or status,
        "health_status": _text(metadata.get("health_status")),
        "ready_for_operational_global_approved_for_paper_review": _to_bool(
            metadata.get("ready_for_operational_global_approved_for_paper_review")
        ),
        "operational_global_approved_for_paper_executed": _to_bool(
            metadata.get("operational_global_approved_for_paper_executed")
        ),
        "operational_global_approved_for_paper_planning_artifacts_created": created,
        **{
            field: _to_bool(metadata.get(field)) or (artifact_dir / ARTIFACT_FILES[_artifact_key_from_created_flag(field)]).exists()
            for field in CREATED_FLAG_FIELDS
        },
        **{field: _to_bool(metadata.get(field)) for field in CORE_FALSE_FIELDS},
        **{field: _to_bool(metadata.get(field)) for field in DOWNSTREAM_FALSE_FIELDS},
        "report_only": _to_bool(metadata.get("report_only")),
        "research_governed": _to_bool(metadata.get("research_governed")),
        "diagnostic_output": _to_bool(metadata.get("diagnostic_output")),
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


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    latest = frame.sort_values(["created_at", "operational_global_approved_for_paper_id"]).iloc[-1]
    return latest.to_dict()


def _gate_blocker_count(artifact_dir: Path) -> int:
    gate_path = artifact_dir / ARTIFACT_FILES["operational_global_approved_for_paper_health_gate_results"]
    frame = _read_csv(gate_path)
    if frame.empty or "status" not in frame.columns:
        return 0
    return int(frame["status"].astype(str).str.contains("BLOCKED|INVALID|FAIL", case=False, regex=True).sum())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str)
    except (pd.errors.ParserError, OSError):
        return pd.DataFrame()


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


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(float(_text(value)))
    except ValueError:
        return 0


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _safety_statement() -> str:
    return (
        "Operational Global APPROVED_FOR_PAPER artifact views are report-only planning context. "
        "They do not grant operational global APPROVED_FOR_PAPER, real buy-review eligibility, "
        "buy_review_allowed, strategy performance validation, current-candidates, snapshots, "
        "signal_semantics mutation, active stock_profile, promoted/production model, active thresholds, "
        "advisory predictions, active probabilities, broker/order/message/API behavior, or trading."
    )
