"""Index view for report-only replay decision schema fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.replay_decision_schema_fixture import (
    FORBIDDEN_METADATA_FALSE_FLAGS,
    REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
)


NO_REPLAY_DECISION_SCHEMA_FIXTURE = "NO_REPLAY_DECISION_SCHEMA_FIXTURE"
REPLAY_DECISION_SCHEMA_FIXTURE_INVALID = "REPLAY_DECISION_SCHEMA_FIXTURE_INVALID"

VIEW_DIR_NAMES = {"index", "health", "status"}

CONTEXT_METADATA_FLAGS = ["replay_evidence_bundle_schema_fixture_used"]

PATH_COLUMNS = [
    "metadata_path",
    "schema_fields_path",
    "fixture_rows_path",
    "evidence_bundle_matrix_path",
    "pit_admissibility_matrix_path",
    "freeze_matrix_path",
    "label_exclusion_matrix_path",
    "quality_compliance_matrix_path",
    "risk_veto_matrix_path",
    "forbidden_output_guard_matrix_path",
    "validation_summary_path",
    "limitations_path",
    "recommended_next_task_path",
]

INDEX_COLUMNS = [
    "replay_decision_schema_fixture_id",
    "created_at",
    "artifact_path",
    "latest_artifact_path",
    "status",
    "workflow_stage",
    "health_status",
    "expected_artifacts",
    "decision_count",
    "validation_issue_count",
    "replay_decision_schema_fixture_created",
    "replay_decision_rows_created",
    "report_only",
    "diagnostic_only",
    *CONTEXT_METADATA_FLAGS,
    *FORBIDDEN_METADATA_FALSE_FLAGS,
    *PATH_COLUMNS,
]


@dataclass(frozen=True)
class ReplayDecisionSchemaFixtureIndexResult:
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


def build_replay_decision_schema_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1/index",
) -> ReplayDecisionSchemaFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    latest = _latest_row(frame)
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "replay_decision_schema_fixture_index.csv",
        "index_report": Path(output_dir) / "replay_decision_schema_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = ReplayDecisionSchemaFixtureIndexResult(
        artifact_count=len(frame),
        latest_run_id=_text(latest.get("replay_decision_schema_fixture_id")),
        latest_status=_text(latest.get("status")) or "NO_INPUT",
        latest_workflow_stage=_text(latest.get("workflow_stage")) or NO_REPLAY_DECISION_SCHEMA_FIXTURE,
        latest_health_status=_text(latest.get("health_status")) or "PASS",
        latest_artifact_path=_text(latest.get("latest_artifact_path")),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_replay_decision_schema_fixture_index(result)
    return result


def write_replay_decision_schema_fixture_index(result: ReplayDecisionSchemaFixtureIndexResult) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Replay Decision Schema Fixture Index",
                "",
                "Report-only replay decision schema fixture index. It does not create real replay decisions, real replay evidence bundle consumption, forward labels, future labels joined, signal_score inputs, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, broker/API behavior, orders, messages, current-candidates, snapshots, signal_semantics mutation, or trading.",
                "",
                f"- artifact_count: {result.artifact_count}",
                f"- latest_run_id: {result.latest_run_id}",
                f"- latest_status: {result.latest_status}",
                f"- latest_workflow_stage: {result.latest_workflow_stage}",
                f"- latest_health_status: {result.latest_health_status}",
                f"- latest_artifact_path: {result.latest_artifact_path}",
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
        return [], [f"Replay decision schema fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in _candidate_dirs(root):
        metadata_path = artifact_dir / "replay_decision_schema_fixture_metadata.json"
        if not metadata_path.exists():
            warnings.append(f"Missing replay decision fixture metadata: {metadata_path}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read replay decision fixture metadata {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name not in VIEW_DIR_NAMES
        and not path.name.startswith("_")
        and (path / "replay_decision_schema_fixture_metadata.json").exists()
    )


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status = _text(metadata.get("status"))
    health_status = _derived_health_status(metadata)
    artifact_path = str(artifact_dir)
    return {
        "replay_decision_schema_fixture_id": _text(metadata.get("replay_decision_schema_fixture_id")) or artifact_dir.name,
        "created_at": _artifact_mtime(artifact_dir),
        "artifact_path": artifact_path,
        "latest_artifact_path": artifact_path,
        "status": status,
        "workflow_stage": REPLAY_DECISION_SCHEMA_FIXTURE_CREATED
        if status == "PASS" and health_status == "PASS"
        else REPLAY_DECISION_SCHEMA_FIXTURE_INVALID,
        "health_status": health_status,
        "expected_artifacts": 13,
        "decision_count": _to_int(metadata.get("decision_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "replay_decision_schema_fixture_created": _to_bool(metadata.get("replay_decision_schema_fixture_created")),
        "replay_decision_rows_created": _to_bool(metadata.get("replay_decision_rows_created")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        **{flag: _context_flag_value(artifact_dir, metadata, flag) for flag in CONTEXT_METADATA_FLAGS},
        **{flag: _to_bool(metadata.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS},
        **_artifact_paths(artifact_dir, metadata_path),
    }


def _context_flag_value(artifact_dir: Path, metadata: dict[str, Any], flag: str) -> bool:
    if flag in metadata:
        return _to_bool(metadata.get(flag))
    rows_path = artifact_dir / "replay_decision_fixture_rows.csv"
    if not rows_path.exists():
        return False
    try:
        rows = pd.read_csv(rows_path, dtype=str).fillna("")
    except Exception:
        return False
    if flag not in rows:
        return False
    return bool(rows[flag].map(_to_bool).any())


def _artifact_paths(artifact_dir: Path, metadata_path: Path) -> dict[str, str]:
    return {
        "metadata_path": str(metadata_path),
        "schema_fields_path": str(artifact_dir / "replay_decision_schema_fields.csv"),
        "fixture_rows_path": str(artifact_dir / "replay_decision_fixture_rows.csv"),
        "evidence_bundle_matrix_path": str(artifact_dir / "replay_decision_evidence_bundle_matrix.csv"),
        "pit_admissibility_matrix_path": str(artifact_dir / "replay_decision_pit_admissibility_matrix.csv"),
        "freeze_matrix_path": str(artifact_dir / "replay_decision_freeze_matrix.csv"),
        "label_exclusion_matrix_path": str(artifact_dir / "replay_decision_label_exclusion_matrix.csv"),
        "quality_compliance_matrix_path": str(artifact_dir / "replay_decision_quality_compliance_matrix.csv"),
        "risk_veto_matrix_path": str(artifact_dir / "replay_decision_risk_veto_matrix.csv"),
        "forbidden_output_guard_matrix_path": str(artifact_dir / "replay_decision_forbidden_output_guard_matrix.csv"),
        "validation_summary_path": str(artifact_dir / "replay_decision_validation_summary.csv"),
        "limitations_path": str(artifact_dir / "replay_decision_limitations.md"),
        "recommended_next_task_path": str(artifact_dir / "recommended_next_task.md"),
    }


def _derived_health_status(metadata: dict[str, Any]) -> str:
    if _text(metadata.get("status")) != "PASS":
        return "FAIL"
    required_true = ["replay_decision_schema_fixture_created", "replay_decision_rows_created", "report_only", "diagnostic_only"]
    if any(not _to_bool(metadata.get(flag)) for flag in required_true):
        return "FAIL"
    if _to_int(metadata.get("decision_count")) != 10:
        return "FAIL"
    if _to_int(metadata.get("validation_issue_count")) != 0:
        return "FAIL"
    if any(_to_bool(metadata.get(flag)) for flag in FORBIDDEN_METADATA_FALSE_FLAGS):
        return "FAIL"
    return "PASS"


def _latest_row(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}
    return frame.sort_values(["created_at", "replay_decision_schema_fixture_id"]).iloc[-1].to_dict()


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
        "replay_decision_schema_fixture_views_created": True,
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
