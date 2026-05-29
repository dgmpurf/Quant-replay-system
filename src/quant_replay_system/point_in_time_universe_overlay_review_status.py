"""Status view for reviewed PIT universe overlay artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.point_in_time_universe_overlay_review_health import (
    check_pit_universe_overlay_review_health,
)
from quant_replay_system.point_in_time_universe_overlay_review_index import (
    scan_pit_universe_overlay_review_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "approved_count",
    "valid_for_signal_date_count",
    "needs_more_evidence_count",
    "unresolved_survivorship_warning_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_review_id",
    "status",
    "workflow_stage",
    "health_status",
    "approved_count",
    "valid_for_signal_date_count",
    "needs_more_evidence_count",
    "unresolved_survivorship_warning_count",
    "report_path",
    "next_manual_action",
]

NO_REVIEW_STAGE = "NO_PIT_UNIVERSE_OVERLAY_REVIEWS"
NEEDS_MORE_EVIDENCE_STAGE = "PIT_UNIVERSE_OVERLAY_REVIEW_NEEDS_MORE_EVIDENCE"
HAS_APPROVED_ROWS_STAGE = "PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS"
ALL_APPROVED_STAGE = "PIT_UNIVERSE_OVERLAY_REVIEW_ALL_APPROVED"
HEALTH_WARN_STAGE = "PIT_UNIVERSE_OVERLAY_REVIEW_HEALTH_WARN"
FAILED_STAGE = "PIT_UNIVERSE_OVERLAY_REVIEW_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local reviewed PIT universe overlay artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseOverlayReviewStatusPaths:
    artifact_dir: Path
    pit_universe_overlay_review_status_report: Path
    pit_universe_overlay_review_status_csv: Path
    pit_universe_overlay_review_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_overlay_review_status_report": self.pit_universe_overlay_review_status_report,
            "pit_universe_overlay_review_status_csv": self.pit_universe_overlay_review_status_csv,
            "pit_universe_overlay_review_status_summary": self.pit_universe_overlay_review_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseOverlayReviewStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_review_id: str
    health_status: str
    approved_count: int
    valid_for_signal_date_count: int
    needs_more_evidence_count: int
    unresolved_survivorship_warning_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_pit_universe_overlay_review_status(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_review",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_review/status",
) -> PitUniverseOverlayReviewStatusResult:
    index_frame = scan_pit_universe_overlay_review_artifacts(root)
    health = check_pit_universe_overlay_review_health(
        index_df=index_frame,
        output_dir=Path(output_dir) / "_health_probe",
    )
    status_frame = build_pit_universe_overlay_review_status_frame(index_frame, health_result=health)
    summary_frame = summarize_pit_universe_overlay_review_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_pit_universe_overlay_review_status_paths(output_dir, status_id)
    result = PitUniverseOverlayReviewStatusResult(
        status_id=status_id,
        status=_string_or_empty(summary.get("status")) or "WARN",
        workflow_stage=_string_or_empty(summary.get("workflow_stage")) or NO_REVIEW_STAGE,
        latest_review_id=_string_or_empty(summary.get("latest_review_id")),
        health_status=_string_or_empty(summary.get("health_status")),
        approved_count=_to_int(summary.get("approved_count")),
        valid_for_signal_date_count=_to_int(summary.get("valid_for_signal_date_count")),
        needs_more_evidence_count=_to_int(summary.get("needs_more_evidence_count")),
        unresolved_survivorship_warning_count=_to_int(summary.get("unresolved_survivorship_warning_count")),
        next_manual_action=_string_or_empty(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string_or_empty(summary.get("workflow_stage")) or NO_REVIEW_STAGE,
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
            "pit_universe_overlay_review_artifacts_only": True,
        },
    )
    write_pit_universe_overlay_review_status_artifacts(result)
    return result


def build_pit_universe_overlay_review_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_review_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_OVERLAY_REVIEW",
                status="MISSING",
                next_action="Run pit-universe-overlay-review from a reviewed local update CSV.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_OVERLAY_REVIEW",
                status=_review_status(latest),
                latest_artifact_id=_string_or_empty(latest.get("review_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                approved_count=_to_int(latest.get("approved_count")),
                valid_for_signal_date_count=_to_int(latest.get("valid_for_signal_date_count")),
                needs_more_evidence_count=_to_int(latest.get("needs_more_evidence_count")),
                unresolved_survivorship_warning_count=_to_int(latest.get("unresolved_survivorship_warning_count")),
                next_action=_review_next_action(latest),
                notes="Latest local reviewed PIT universe overlay artifact.",
            )
        )
    rows.append(
        _status_row(
            component="PIT_UNIVERSE_OVERLAY_REVIEW_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("pit_universe_overlay_review_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="In-memory health evaluation for reviewed PIT universe overlay artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_pit_universe_overlay_review_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_review_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_REVIEW_STAGE,
                    health_status="MISSING",
                    next_manual_action="Run pit-universe-overlay-review with a local review update CSV.",
                )
            ]
        )
    approved_count = _to_int(latest.get("approved_count"))
    valid_count = _to_int(latest.get("valid_for_signal_date_count"))
    needs_more_count = _to_int(latest.get("needs_more_evidence_count")) + _to_int(
        latest.get("needs_manual_review_count")
    )
    unresolved_count = _to_int(latest.get("unresolved_survivorship_warning_count"))
    row_count = _to_int(latest.get("row_count"))
    if health_result.status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair PIT universe overlay review artifacts before snapshot preparation planning."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review PIT universe overlay review health warnings before snapshot preparation planning."
    elif approved_count > 0 and row_count > 0 and approved_count >= row_count:
        stage = ALL_APPROVED_STAGE
        status = "PASS"
        next_action = "Review approved PIT universe rows before separate snapshot preparation planning."
    elif approved_count > 0 or valid_count > 0:
        stage = HAS_APPROVED_ROWS_STAGE
        status = "WARN" if needs_more_count > 0 or unresolved_count > 0 else "PASS"
        next_action = "Review approved PIT universe rows before separate snapshot preparation planning."
    elif needs_more_count > 0 or unresolved_count > 0:
        stage = NEEDS_MORE_EVIDENCE_STAGE
        status = "WARN"
        next_action = "Resolve PIT universe overlay rows that need more evidence before snapshot preparation planning."
    else:
        stage = NEEDS_MORE_EVIDENCE_STAGE
        status = "WARN"
        next_action = "Resolve PIT universe overlay rows that need more evidence before snapshot preparation planning."
    return pd.DataFrame(
        [
            _summary_row(
                latest_review_id=_string_or_empty(latest.get("review_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                approved_count=approved_count,
                valid_for_signal_date_count=valid_count,
                needs_more_evidence_count=_to_int(latest.get("needs_more_evidence_count")),
                unresolved_survivorship_warning_count=unresolved_count,
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_pit_universe_overlay_review_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> PitUniverseOverlayReviewStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return PitUniverseOverlayReviewStatusPaths(
        artifact_dir=artifact_dir,
        pit_universe_overlay_review_status_report=artifact_dir / "pit_universe_overlay_review_status_report.md",
        pit_universe_overlay_review_status_csv=artifact_dir / "pit_universe_overlay_review_status.csv",
        pit_universe_overlay_review_status_summary=artifact_dir / "pit_universe_overlay_review_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_overlay_review_status_artifacts(
    result: PitUniverseOverlayReviewStatusResult,
) -> dict[str, Path]:
    paths = PitUniverseOverlayReviewStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.pit_universe_overlay_review_status_csv, index=False)
    result.summary_frame.to_csv(paths.pit_universe_overlay_review_status_summary, index=False)
    metadata = build_pit_universe_overlay_review_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_overlay_review_status_report.write_text(
        render_pit_universe_overlay_review_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_overlay_review_status_metadata(
    result: PitUniverseOverlayReviewStatusResult,
    paths: PitUniverseOverlayReviewStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_review_id": result.latest_review_id,
        "health_status": result.health_status,
        "approved_count": result.approved_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "needs_more_evidence_count": result.needs_more_evidence_count,
        "unresolved_survivorship_warning_count": result.unresolved_survivorship_warning_count,
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


def render_pit_universe_overlay_review_status_report(
    result: PitUniverseOverlayReviewStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Overlay Review Status",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This status view summarizes local reviewed PIT universe overlay artifacts only.",
            "",
            "Approved rows are PIT universe preparation evidence only. They do not imply candidates were generated.",
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


def _latest_review_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    for column in ["created_at", "review_id"]:
        if column not in frame:
            frame[column] = ""
    return frame.sort_values(["created_at", "review_id"]).iloc[-1].to_dict()


def _review_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_more_evidence_count")) > 0 or _to_int(row.get("needs_manual_review_count")) > 0:
        return "NEEDS_MORE_EVIDENCE"
    if _to_int(row.get("approved_count")) > 0:
        return "HAS_APPROVED_ROWS"
    return "WARN"


def _review_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_more_evidence_count")) > 0 or _to_int(row.get("unresolved_survivorship_warning_count")) > 0:
        return "Resolve PIT universe overlay rows that need more evidence before snapshot preparation planning."
    return "Review approved PIT universe rows before separate snapshot preparation planning."


def _health_next_action(status: str) -> str:
    normalized = _string_or_empty(status).upper()
    if normalized == "PASS":
        return "No PIT universe overlay review health issues detected."
    if normalized == "FAIL":
        return "Repair PIT universe overlay review health errors."
    if normalized == "WARN":
        return "Review PIT universe overlay review health warnings."
    return "Run pit-universe-overlay-review-health."


def _status_warnings(index_frame: pd.DataFrame, health_result: Any, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No PIT universe overlay review artifacts were found.")
    if _to_int(summary.get("needs_more_evidence_count")) > 0:
        warnings.append("Latest PIT universe overlay review still needs more evidence.")
    if _to_int(summary.get("unresolved_survivorship_warning_count")) > 0:
        warnings.append("Latest PIT universe overlay review has unresolved survivorship warnings.")
    if getattr(health_result, "status", "") == "FAIL":
        warnings.append("PIT universe overlay review health failed.")
    return warnings


def _status_row(
    *,
    component: str,
    status: str,
    latest_artifact_id: str = "",
    report_path: str = "",
    metadata_path: str = "",
    approved_count: int = 0,
    valid_for_signal_date_count: int = 0,
    needs_more_evidence_count: int = 0,
    unresolved_survivorship_warning_count: int = 0,
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
        "approved_count": int(approved_count),
        "valid_for_signal_date_count": int(valid_for_signal_date_count),
        "needs_more_evidence_count": int(needs_more_evidence_count),
        "unresolved_survivorship_warning_count": int(unresolved_survivorship_warning_count),
        "issue_count": int(issue_count),
        "warning_count": int(warning_count),
        "error_count": int(error_count),
        "next_action": next_action,
        "notes": notes,
    }


def _summary_row(
    *,
    latest_review_id: str = "",
    status: str,
    workflow_stage: str,
    health_status: str,
    approved_count: int = 0,
    valid_for_signal_date_count: int = 0,
    needs_more_evidence_count: int = 0,
    unresolved_survivorship_warning_count: int = 0,
    report_path: str = "",
    next_manual_action: str,
) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(
        {
            "latest_review_id": latest_review_id,
            "status": status,
            "workflow_stage": workflow_stage,
            "health_status": health_status,
            "approved_count": int(approved_count),
            "valid_for_signal_date_count": int(valid_for_signal_date_count),
            "needs_more_evidence_count": int(needs_more_evidence_count),
            "unresolved_survivorship_warning_count": int(unresolved_survivorship_warning_count),
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
