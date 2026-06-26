"""Index view for report-only event structured schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.event_structured_schema_fixture import (
    EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED,
    FORBIDDEN_METADATA_FALSE_FLAGS,
)


NO_EVENT_STRUCTURED_SCHEMA_FIXTURE = "NO_EVENT_STRUCTURED_SCHEMA_FIXTURE"
EVENT_STRUCTURED_SCHEMA_FIXTURE_INVALID = "EVENT_STRUCTURED_SCHEMA_FIXTURE_INVALID"

VIEW_DIR_NAMES = {"index", "health", "status"}

PATH_COLUMNS = [
    "metadata_path",
    "schema_fields_path",
    "fixture_rows_path",
    "type_matrix_path",
    "direction_matrix_path",
    "pit_lineage_matrix_path",
    "source_quality_matrix_path",
    "validation_summary_path",
    "limitations_path",
    "recommended_next_task_path",
]

INDEX_COLUMNS = [
    "event_structured_schema_fixture_id",
    "created_at",
    "artifact_path",
    "latest_artifact_path",
    "status",
    "workflow_stage",
    "health_status",
    "expected_artifacts",
    "event_count",
    "validation_issue_count",
    "event_structured_schema_fixture_created",
    "event_structured_rows_created",
    "report_only",
    "diagnostic_only",
    *FORBIDDEN_METADATA_FALSE_FLAGS,
    *PATH_COLUMNS,
]


@dataclass(frozen=True)
class EventStructuredSchemaFixtureIndexResult:
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


def build_event_structured_schema_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1/index",
) -> EventStructuredSchemaFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "event_structured_schema_fixture_index.csv",
        "index_report": Path(output_dir) / "event_structured_schema_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = EventStructuredSchemaFixtureIndexResult(
        artifact_count=len(frame),
        latest_run_id=_text(latest.get("event_structured_schema_fixture_id")),
        latest_status=_text(latest.get("status")) or "NO_INPUT",
        latest_workflow_stage=_text(latest.get("workflow_stage")) or NO_EVENT_STRUCTURED_SCHEMA_FIXTURE,
        latest_health_status=_text(latest.get("health_status")) or "PASS",
        latest_artifact_path=_text(latest.get("latest_artifact_path")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_event_structured_schema_fixture_index(result)
    return result


def write_event_structured_schema_fixture_index(result: EventStructuredSchemaFixtureIndexResult) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Event Structured Schema Fixture Index",
                "",
                "Report-only event structured schema fixture index. It does not create production event ingestion, active event libraries, real raw document ingestion, real source adapters, factor observations, production company exposure mapping, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, buy-review eligibility, performance validation, broker/API behavior, orders, messages, or trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- latest_status: {result.latest_status}",
                f"- latest_workflow_stage: {result.latest_workflow_stage}",
                f"- latest_health_status: {result.latest_health_status}",
                f"- latest_artifact_path: {result.latest_artifact_path}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No event structured schema fixture artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
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
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Event structured schema fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "event_structured_schema_fixture_metadata.json"
        if not metadata_path.exists():
            warnings.append(f"Missing event structured fixture metadata: {metadata_path}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read event structured fixture metadata {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in VIEW_DIR_NAMES and not path.name.startswith("_")
    )


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    status = _text(metadata.get("status"))
    health_status = _derived_health_status(metadata)
    artifact_path = str(artifact_dir)
    return {
        "event_structured_schema_fixture_id": _text(metadata.get("event_structured_schema_fixture_id")) or artifact_dir.name,
        "created_at": _artifact_mtime(artifact_dir),
        "artifact_path": artifact_path,
        "latest_artifact_path": artifact_path,
        "status": status,
        "workflow_stage": EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED
        if status == "PASS" and health_status == "PASS"
        else EVENT_STRUCTURED_SCHEMA_FIXTURE_INVALID,
        "health_status": health_status,
        "expected_artifacts": 10,
        "event_count": _to_int(metadata.get("event_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "event_structured_schema_fixture_created": _to_bool(metadata.get("event_structured_schema_fixture_created")),
        "event_structured_rows_created": _to_bool(metadata.get("event_structured_rows_created")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        **{flag: _to_bool(metadata.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        "metadata_path": str(metadata_path),
        "schema_fields_path": str(Path(artifact_paths.get("schema_fields") or artifact_dir / "event_structured_schema_fields.csv")),
        "fixture_rows_path": str(Path(artifact_paths.get("fixture_rows") or artifact_dir / "event_structured_fixture_rows.csv")),
        "type_matrix_path": str(Path(artifact_paths.get("type_matrix") or artifact_dir / "event_structured_type_matrix.csv")),
        "direction_matrix_path": str(Path(artifact_paths.get("direction_matrix") or artifact_dir / "event_structured_direction_matrix.csv")),
        "pit_lineage_matrix_path": str(
            Path(artifact_paths.get("pit_lineage_matrix") or artifact_dir / "event_structured_pit_lineage_matrix.csv")
        ),
        "source_quality_matrix_path": str(
            Path(artifact_paths.get("source_quality_matrix") or artifact_dir / "event_structured_source_quality_matrix.csv")
        ),
        "validation_summary_path": str(
            Path(artifact_paths.get("validation_summary") or artifact_dir / "event_structured_validation_summary.csv")
        ),
        "limitations_path": str(Path(artifact_paths.get("limitations") or artifact_dir / "event_structured_limitations.md")),
        "recommended_next_task_path": str(Path(artifact_paths.get("recommended_next_task") or artifact_dir / "recommended_next_task.md")),
    }


def _derived_health_status(metadata: dict[str, Any]) -> str:
    if _text(metadata.get("status")) != "PASS":
        return "FAIL"
    required_true = [
        "event_structured_schema_fixture_created",
        "event_structured_rows_created",
        "report_only",
        "diagnostic_only",
    ]
    if any(not _to_bool(metadata.get(flag)) for flag in required_true):
        return "FAIL"
    if _to_int(metadata.get("event_count")) != 10:
        return "FAIL"
    if _to_int(metadata.get("validation_issue_count")) != 0:
        return "FAIL"
    if any(_to_bool(metadata.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS):
        return "FAIL"
    return "PASS"


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "event_structured_schema_fixture_id"]).iloc[-1].to_dict()


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
        "event_structured_schema_fixture_views_created": True,
        **{flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
    }


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
