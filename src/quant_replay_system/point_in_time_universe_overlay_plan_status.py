"""Status view for point-in-time universe overlay plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.point_in_time_universe_overlay_plan_health import (
    check_point_in_time_universe_overlay_plan_health,
)
from quant_replay_system.point_in_time_universe_overlay_plan_index import (
    scan_point_in_time_universe_overlay_plan_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "row_count",
    "needs_manual_review_count",
    "valid_for_signal_date_count",
    "survivorship_bias_warning_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_overlay_plan_id",
    "status",
    "workflow_stage",
    "health_status",
    "row_count",
    "signal_date_count",
    "symbol_count",
    "needs_manual_review_count",
    "valid_for_signal_date_count",
    "survivorship_bias_warning_count",
    "report_path",
    "next_manual_action",
]

NO_PLAN_STAGE = "NO_PIT_UNIVERSE_OVERLAY_PLAN"
NEEDS_REVIEW_STAGE = "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
READY_STAGE = "PIT_UNIVERSE_OVERLAY_PLAN_READY_FOR_REVIEW"
HEALTH_WARN_STAGE = "PIT_UNIVERSE_OVERLAY_PLAN_HEALTH_WARN"
FAILED_STAGE = "PIT_UNIVERSE_OVERLAY_PLAN_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local point-in-time universe overlay plan artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanStatusPaths:
    artifact_dir: Path
    point_in_time_universe_overlay_plan_status_report: Path
    point_in_time_universe_overlay_plan_status_csv: Path
    point_in_time_universe_overlay_plan_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "point_in_time_universe_overlay_plan_status_report": self.point_in_time_universe_overlay_plan_status_report,
            "point_in_time_universe_overlay_plan_status_csv": self.point_in_time_universe_overlay_plan_status_csv,
            "point_in_time_universe_overlay_plan_status_summary": self.point_in_time_universe_overlay_plan_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_overlay_plan_id: str
    health_status: str
    row_count: int
    needs_manual_review_count: int
    valid_for_signal_date_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_point_in_time_universe_overlay_plan_status(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_plan",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_plan/status",
) -> PointInTimeUniverseOverlayPlanStatusResult:
    index_frame = scan_point_in_time_universe_overlay_plan_artifacts(root)
    health = check_point_in_time_universe_overlay_plan_health(
        index_df=index_frame,
        output_dir=Path(output_dir) / "_health_probe",
    )
    status_frame = build_point_in_time_universe_overlay_plan_status_frame(index_frame, health_result=health)
    summary_frame = summarize_point_in_time_universe_overlay_plan_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_point_in_time_universe_overlay_plan_status_paths(output_dir, status_id)
    result = PointInTimeUniverseOverlayPlanStatusResult(
        status_id=status_id,
        status=_string_or_empty(summary.get("status")) or "WARN",
        workflow_stage=_string_or_empty(summary.get("workflow_stage")) or NO_PLAN_STAGE,
        latest_overlay_plan_id=_string_or_empty(summary.get("latest_overlay_plan_id")),
        health_status=_string_or_empty(summary.get("health_status")),
        row_count=_to_int(summary.get("row_count")),
        needs_manual_review_count=_to_int(summary.get("needs_manual_review_count")),
        valid_for_signal_date_count=_to_int(summary.get("valid_for_signal_date_count")),
        next_manual_action=_string_or_empty(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string_or_empty(summary.get("workflow_stage")) or NO_PLAN_STAGE,
            "current_candidates_executed": False,
            "data_pipeline_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "pit_universe_overlay_plan_artifacts_only": True,
        },
    )
    write_point_in_time_universe_overlay_plan_status_artifacts(result)
    return result


def build_point_in_time_universe_overlay_plan_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_plan_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_OVERLAY_PLAN",
                status="MISSING",
                next_action="Run pit-universe-overlay-plan from a blocked execution manifest.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_OVERLAY_PLAN",
                status=_plan_status(latest),
                latest_artifact_id=_string_or_empty(latest.get("overlay_plan_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                row_count=_to_int(latest.get("row_count")),
                needs_manual_review_count=_to_int(latest.get("needs_manual_review_count")),
                valid_for_signal_date_count=_to_int(latest.get("valid_for_signal_date_count")),
                survivorship_bias_warning_count=_to_int(latest.get("survivorship_bias_warning_count")),
                next_action=_plan_next_action(latest),
                notes="Latest local PIT universe overlay plan artifact.",
            )
        )
    rows.append(
        _status_row(
            component="PIT_UNIVERSE_OVERLAY_PLAN_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("point_in_time_universe_overlay_plan_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="In-memory health evaluation for PIT universe overlay plan artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_point_in_time_universe_overlay_plan_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_plan_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_PLAN_STAGE,
                    health_status="MISSING",
                    next_manual_action="Run pit-universe-overlay-plan from BLOCKED_UNIVERSE_AS_OF execution manifest rows.",
                )
            ]
        )
    if health_result.status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair PIT universe overlay plan artifacts before manual PIT universe review."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review PIT universe overlay plan health warnings before manual review."
    elif _to_int(latest.get("needs_manual_review_count")) > 0:
        stage = NEEDS_REVIEW_STAGE
        status = "WARN"
        next_action = "Complete manual review for point-in-time universe rows; generated rows are not valid for execution yet."
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review PIT-valid overlay rows before any separate snapshot preparation step."
    return pd.DataFrame(
        [
            _summary_row(
                latest_overlay_plan_id=_string_or_empty(latest.get("overlay_plan_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                row_count=_to_int(latest.get("row_count")),
                signal_date_count=_to_int(latest.get("signal_date_count")),
                symbol_count=_to_int(latest.get("symbol_count")),
                needs_manual_review_count=_to_int(latest.get("needs_manual_review_count")),
                valid_for_signal_date_count=_to_int(latest.get("valid_for_signal_date_count")),
                survivorship_bias_warning_count=_to_int(latest.get("survivorship_bias_warning_count")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_point_in_time_universe_overlay_plan_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> PointInTimeUniverseOverlayPlanStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return PointInTimeUniverseOverlayPlanStatusPaths(
        artifact_dir=artifact_dir,
        point_in_time_universe_overlay_plan_status_report=artifact_dir / "point_in_time_universe_overlay_plan_status_report.md",
        point_in_time_universe_overlay_plan_status_csv=artifact_dir / "point_in_time_universe_overlay_plan_status.csv",
        point_in_time_universe_overlay_plan_status_summary=artifact_dir / "point_in_time_universe_overlay_plan_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_point_in_time_universe_overlay_plan_status_artifacts(
    result: PointInTimeUniverseOverlayPlanStatusResult,
) -> dict[str, Path]:
    paths = PointInTimeUniverseOverlayPlanStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.point_in_time_universe_overlay_plan_status_csv, index=False)
    result.summary_frame.to_csv(paths.point_in_time_universe_overlay_plan_status_summary, index=False)
    metadata = build_point_in_time_universe_overlay_plan_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.point_in_time_universe_overlay_plan_status_report.write_text(
        render_point_in_time_universe_overlay_plan_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_point_in_time_universe_overlay_plan_status_metadata(
    result: PointInTimeUniverseOverlayPlanStatusResult,
    paths: PointInTimeUniverseOverlayPlanStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_overlay_plan_id": result.latest_overlay_plan_id,
        "health_status": result.health_status,
        "row_count": result.row_count,
        "needs_manual_review_count": result.needs_manual_review_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
            "order placement, message delivery, LLM API, or external API was invoked."
        ),
    }


def render_point_in_time_universe_overlay_plan_status_report(
    result: PointInTimeUniverseOverlayPlanStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Point-in-Time Universe Overlay Plan Status",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This status view summarizes local PIT universe overlay plan artifacts only.",
            "",
            "## Summary",
            "",
            _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
            "",
            "## Components",
            "",
            _markdown_table(result.status_frame, STATUS_COLUMNS),
            "",
            "## Warnings",
            "",
            _warnings_section(result.warnings),
            "",
        ]
    )


def _latest_plan_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    for column in ["created_at", "overlay_plan_id"]:
        if column not in frame:
            frame[column] = ""
    return frame.sort_values(["created_at", "overlay_plan_id"]).iloc[-1].to_dict()


def _plan_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_manual_review_count")) > 0:
        return "NEEDS_REVIEW"
    if _to_int(row.get("valid_for_signal_date_count")) > 0:
        return "READY_FOR_REVIEW"
    return "WARN"


def _plan_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_manual_review_count")) > 0:
        return "Complete manual review for point-in-time universe rows before snapshot preparation."
    return "Review PIT universe overlay plan before any later snapshot preparation step."


def _health_next_action(status: str) -> str:
    normalized = _string_or_empty(status).upper()
    if normalized == "PASS":
        return "No PIT universe overlay plan health issues detected."
    if normalized == "FAIL":
        return "Repair PIT universe overlay plan health errors."
    if normalized == "WARN":
        return "Review PIT universe overlay plan health warnings."
    return "Run pit-universe-overlay-plan-health."


def _status_warnings(index_frame: pd.DataFrame, health_result: Any, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No PIT universe overlay plan artifacts were found.")
    if _to_int(summary.get("needs_manual_review_count")) > 0:
        warnings.append("Latest PIT universe overlay plan still requires manual review.")
    if getattr(health_result, "status", "") == "FAIL":
        warnings.append("PIT universe overlay plan health failed.")
    return warnings


def _status_row(
    *,
    component: str,
    status: str,
    latest_artifact_id: str = "",
    report_path: str = "",
    metadata_path: str = "",
    row_count: int = 0,
    needs_manual_review_count: int = 0,
    valid_for_signal_date_count: int = 0,
    survivorship_bias_warning_count: int = 0,
    issue_count: int = 0,
    warning_count: int = 0,
    error_count: int = 0,
    next_action: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "latest_artifact_id": latest_artifact_id,
        "report_path": report_path,
        "metadata_path": metadata_path,
        "row_count": int(row_count),
        "needs_manual_review_count": int(needs_manual_review_count),
        "valid_for_signal_date_count": int(valid_for_signal_date_count),
        "survivorship_bias_warning_count": int(survivorship_bias_warning_count),
        "issue_count": int(issue_count),
        "warning_count": int(warning_count),
        "error_count": int(error_count),
        "next_action": next_action,
        "notes": notes,
    }


def _summary_row(
    *,
    latest_overlay_plan_id: str = "",
    status: str,
    workflow_stage: str,
    health_status: str,
    row_count: int = 0,
    signal_date_count: int = 0,
    symbol_count: int = 0,
    needs_manual_review_count: int = 0,
    valid_for_signal_date_count: int = 0,
    survivorship_bias_warning_count: int = 0,
    report_path: str = "",
    next_manual_action: str,
) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(
        {
            "latest_overlay_plan_id": latest_overlay_plan_id,
            "status": status,
            "workflow_stage": workflow_stage,
            "health_status": health_status,
            "row_count": int(row_count),
            "signal_date_count": int(signal_date_count),
            "symbol_count": int(symbol_count),
            "needs_manual_review_count": int(needs_manual_review_count),
            "valid_for_signal_date_count": int(valid_for_signal_date_count),
            "survivorship_bias_warning_count": int(survivorship_bias_warning_count),
            "report_path": report_path,
            "next_manual_action": next_manual_action,
        }
    )
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


def _string_or_empty(value: Any) -> str:
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
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)
