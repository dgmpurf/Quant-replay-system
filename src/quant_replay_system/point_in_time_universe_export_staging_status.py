"""Status view for guarded PIT universe export staging artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.point_in_time_universe_export_staging_health import (
    check_pit_universe_export_staging_health,
)
from quant_replay_system.point_in_time_universe_export_staging_index import (
    scan_pit_universe_export_staging_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "export_readiness_id",
    "review_id",
    "export_ready_input_count",
    "staged_row_count",
    "blocked_count",
    "source_is_diagnostic",
    "no_ready_rows",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_staging_id",
    "status",
    "workflow_stage",
    "health_status",
    "export_readiness_id",
    "review_id",
    "export_ready_input_count",
    "staged_row_count",
    "blocked_count",
    "source_is_diagnostic",
    "no_ready_rows",
    "report_path",
    "next_manual_action",
]

NO_STAGING_STAGE = "NO_PIT_UNIVERSE_EXPORT_STAGING"
BLOCKED_NO_READY_STAGE = "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
BLOCKED_DIAGNOSTIC_STAGE = "PIT_UNIVERSE_EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE"
READY_STAGE = "PIT_UNIVERSE_EXPORT_STAGING_READY_FOR_REVIEW"
HEALTH_WARN_STAGE = "PIT_UNIVERSE_EXPORT_STAGING_HEALTH_WARN"
FAILED_STAGE = "PIT_UNIVERSE_EXPORT_STAGING_FAILED"


@dataclass(frozen=True)
class PitUniverseExportStagingStatusPaths:
    artifact_dir: Path
    pit_universe_export_staging_status_report: Path
    pit_universe_export_staging_status_csv: Path
    pit_universe_export_staging_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_export_staging_status_report": self.pit_universe_export_staging_status_report,
            "pit_universe_export_staging_status_csv": self.pit_universe_export_staging_status_csv,
            "pit_universe_export_staging_status_summary": self.pit_universe_export_staging_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseExportStagingStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_staging_id: str
    health_status: str
    export_readiness_id: str
    review_id: str
    export_ready_input_count: int
    staged_row_count: int
    blocked_count: int
    source_is_diagnostic: bool
    no_ready_rows: bool
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_pit_universe_export_staging_status(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_export_staging",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_export_staging/status",
) -> PitUniverseExportStagingStatusResult:
    index_frame = scan_pit_universe_export_staging_artifacts(root)
    health = check_pit_universe_export_staging_health(index_df=index_frame, output_dir=Path(output_dir) / "_health_probe")
    status_frame = build_pit_universe_export_staging_status_frame(index_frame, health_result=health)
    summary_frame = summarize_pit_universe_export_staging_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, 12)
    paths = resolve_pit_universe_export_staging_status_paths(output_dir, status_id)
    result = PitUniverseExportStagingStatusResult(
        status_id=status_id,
        status=_text(summary.get("status")) or "WARN",
        workflow_stage=_text(summary.get("workflow_stage")) or NO_STAGING_STAGE,
        latest_staging_id=_text(summary.get("latest_staging_id")),
        health_status=_text(summary.get("health_status")),
        export_readiness_id=_text(summary.get("export_readiness_id")),
        review_id=_text(summary.get("review_id")),
        export_ready_input_count=_to_int(summary.get("export_ready_input_count")),
        staged_row_count=_to_int(summary.get("staged_row_count")),
        blocked_count=_to_int(summary.get("blocked_count")),
        source_is_diagnostic=_to_bool(summary.get("source_is_diagnostic")),
        no_ready_rows=_to_bool(summary.get("no_ready_rows")),
        next_manual_action=_text(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _text(summary.get("workflow_stage")) or NO_STAGING_STAGE,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "broker_api_invoked": False,
            "message_sent": False,
            "pit_universe_export_staging_artifacts_only": True,
        },
    )
    write_pit_universe_export_staging_status_artifacts(result)
    return result


def build_pit_universe_export_staging_status_frame(index_frame: pd.DataFrame, *, health_result: Any) -> pd.DataFrame:
    latest = _latest_staging_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(_status_row(component="PIT_UNIVERSE_EXPORT_STAGING", status="MISSING", next_action="Run pit-universe-export-staging from export-readiness artifacts."))
    else:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_EXPORT_STAGING",
                status=_staging_component_status(latest),
                latest_artifact_id=_text(latest.get("staging_id")),
                report_path=_text(latest.get("report_path")),
                metadata_path=_text(latest.get("metadata_path")),
                export_readiness_id=_text(latest.get("export_readiness_id")),
                review_id=_text(latest.get("review_id")),
                export_ready_input_count=_to_int(latest.get("export_ready_input_count")),
                staged_row_count=_to_int(latest.get("staged_row_count")),
                blocked_count=_to_int(latest.get("blocked_count")),
                source_is_diagnostic=_to_bool(latest.get("source_is_diagnostic")),
                no_ready_rows=_to_bool(latest.get("no_ready_rows")),
                next_action=_staging_next_action(latest),
                notes="Latest guarded PIT universe export staging artifact.",
            )
        )
    rows.append(
        _status_row(
            component="PIT_UNIVERSE_EXPORT_STAGING_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("pit_universe_export_staging_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action="No staging health issues detected." if health_result.status == "PASS" else "Review staging health issues.",
            notes="In-memory health evaluation for PIT universe export staging artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_pit_universe_export_staging_status(index_frame: pd.DataFrame, *, health_result: Any) -> pd.DataFrame:
    latest = _latest_staging_row(index_frame)
    if latest is None:
        return pd.DataFrame([_summary_row(status="WARN", workflow_stage=NO_STAGING_STAGE, health_status="MISSING", next_manual_action="Run pit-universe-export-staging from export-readiness artifacts.")])
    staging_status = _text(latest.get("staging_status"))
    if health_result.status == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair PIT universe export staging artifacts before any accepted export planning."
    elif health_result.status == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review PIT universe export staging health warnings."
    elif staging_status == "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE":
        status = "WARN"
        stage = BLOCKED_DIAGNOSTIC_STAGE
        next_action = "Use only active non-diagnostic export-readiness artifacts for staging."
    elif _to_bool(latest.get("no_ready_rows")) or staging_status == "EXPORT_STAGING_BLOCKED_NO_READY_ROWS":
        status = "WARN"
        stage = BLOCKED_NO_READY_STAGE
        next_action = "Complete PIT universe review evidence before staging can create previews."
    elif _to_int(latest.get("staged_row_count")) > 0:
        status = "PASS"
        stage = READY_STAGE
        next_action = "Review staged PIT universe previews before any separate accepted export workflow."
    else:
        status = "WARN"
        stage = FAILED_STAGE
        next_action = "Review PIT universe export staging blockers."
    return pd.DataFrame(
        [
            _summary_row(
                latest_staging_id=_text(latest.get("staging_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                export_readiness_id=_text(latest.get("export_readiness_id")),
                review_id=_text(latest.get("review_id")),
                export_ready_input_count=_to_int(latest.get("export_ready_input_count")),
                staged_row_count=_to_int(latest.get("staged_row_count")),
                blocked_count=_to_int(latest.get("blocked_count")),
                source_is_diagnostic=_to_bool(latest.get("source_is_diagnostic")),
                no_ready_rows=_to_bool(latest.get("no_ready_rows")),
                report_path=_text(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_pit_universe_export_staging_status_paths(output_dir: str | Path, status_id: str) -> PitUniverseExportStagingStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return PitUniverseExportStagingStatusPaths(
        artifact_dir=artifact_dir,
        pit_universe_export_staging_status_report=artifact_dir / "pit_universe_export_staging_status_report.md",
        pit_universe_export_staging_status_csv=artifact_dir / "pit_universe_export_staging_status.csv",
        pit_universe_export_staging_status_summary=artifact_dir / "pit_universe_export_staging_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_export_staging_status_artifacts(result: PitUniverseExportStagingStatusResult) -> dict[str, Path]:
    paths = PitUniverseExportStagingStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.pit_universe_export_staging_status_csv, index=False)
    result.summary_frame.to_csv(paths.pit_universe_export_staging_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_staging_id": result.latest_staging_id,
        "health_status": result.health_status,
        "export_readiness_id": result.export_readiness_id,
        "review_id": result.review_id,
        "export_ready_input_count": result.export_ready_input_count,
        "staged_row_count": result.staged_row_count,
        "blocked_count": result.blocked_count,
        "source_is_diagnostic": result.source_is_diagnostic,
        "no_ready_rows": result.no_ready_rows,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, network/API, "
            "LLM/API, or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_export_staging_status_report.write_text(render_pit_universe_export_staging_status_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_export_staging_status_report(result: PitUniverseExportStagingStatusResult) -> str:
    return "\n".join(
        [
            "# PIT Universe Export Staging Status",
            "",
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
            "",
            result.summary_frame.to_markdown(index=False),
            "",
            result.status_frame.to_markdown(index=False),
            "",
            "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "- None",
        ]
    )


def _latest_staging_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    for column in ["created_at", "staging_id"]:
        if column not in frame:
            frame[column] = ""
    return frame.sort_values(["created_at", "staging_id"]).iloc[-1].to_dict()


def _staging_component_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("staged_row_count")) > 0:
        return "READY_FOR_REVIEW"
    if _to_bool(row.get("source_is_diagnostic")):
        return "BLOCKED_DIAGNOSTIC_SOURCE"
    if _to_bool(row.get("no_ready_rows")):
        return "BLOCKED_NO_READY_ROWS"
    return "BLOCKED"


def _staging_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("staged_row_count")) > 0:
        return "Review staged PIT universe previews before any accepted export workflow."
    if _to_bool(row.get("source_is_diagnostic")):
        return "Use active non-diagnostic export-readiness artifacts for staging."
    return "Complete PIT universe review evidence before staging can create previews."


def _status_warnings(index_frame: pd.DataFrame, health_result: Any, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No PIT universe export staging artifacts were found.")
    if _to_bool(summary.get("no_ready_rows")):
        warnings.append("Latest PIT universe export staging is blocked because no export-ready rows are available.")
    if _to_bool(summary.get("source_is_diagnostic")):
        warnings.append("Latest PIT universe export staging source is diagnostic scope.")
    if getattr(health_result, "status", "") == "FAIL":
        warnings.append("PIT universe export staging health failed.")
    return warnings


def _status_row(**kwargs: Any) -> dict[str, Any]:
    row = {column: "" for column in STATUS_COLUMNS}
    row.update(kwargs)
    for column in ["export_ready_input_count", "staged_row_count", "blocked_count", "issue_count", "warning_count", "error_count"]:
        row[column] = _to_int(row.get(column))
    for column in ["source_is_diagnostic", "no_ready_rows"]:
        row[column] = _to_bool(row.get(column))
    return row


def _summary_row(**kwargs: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(kwargs)
    for column in ["export_ready_input_count", "staged_row_count", "blocked_count"]:
        row[column] = _to_int(row.get(column))
    for column in ["source_is_diagnostic", "no_ready_rows"]:
        row[column] = _to_bool(row.get(column))
    return row


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STATUS_COLUMNS)
    output = frame.copy()
    for column in STATUS_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[STATUS_COLUMNS].reset_index(drop=True)


def _to_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
