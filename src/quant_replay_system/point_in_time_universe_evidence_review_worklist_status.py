"""Status view for PIT universe evidence review worklist artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.point_in_time_universe_evidence_review_worklist_health import (
    check_pit_universe_evidence_review_worklist_health,
)
from quant_replay_system.point_in_time_universe_evidence_review_worklist_index import (
    scan_pit_universe_evidence_review_worklist_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "review_id",
    "helper_id",
    "row_count",
    "symbol_count",
    "signal_date_count",
    "needs_evidence_count",
    "future_dated_hint_count",
    "authoritative_hint_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_worklist_id",
    "status",
    "workflow_stage",
    "health_status",
    "review_id",
    "helper_id",
    "row_count",
    "symbol_count",
    "signal_date_count",
    "needs_evidence_count",
    "future_dated_hint_count",
    "authoritative_hint_count",
    "report_path",
    "next_manual_action",
]

NO_WORKLIST_STAGE = "NO_PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST"
READY_STAGE = "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_READY"
NEEDS_REVIEW_STAGE = "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_NEEDS_REVIEW"
HEALTH_WARN_STAGE = "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_HEALTH_WARN"
FAILED_STAGE = "PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local PIT universe evidence review worklist artifacts only.",
    "Does not approve rows, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistStatusPaths:
    artifact_dir: Path
    pit_universe_evidence_review_worklist_status_report: Path
    pit_universe_evidence_review_worklist_status_csv: Path
    pit_universe_evidence_review_worklist_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_review_worklist_status_report": (
                self.pit_universe_evidence_review_worklist_status_report
            ),
            "pit_universe_evidence_review_worklist_status_csv": (
                self.pit_universe_evidence_review_worklist_status_csv
            ),
            "pit_universe_evidence_review_worklist_status_summary": (
                self.pit_universe_evidence_review_worklist_status_summary
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_worklist_id: str
    health_status: str
    review_id: str
    helper_id: str
    row_count: int
    symbol_count: int
    signal_date_count: int
    needs_evidence_count: int
    future_dated_hint_count: int
    authoritative_hint_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_pit_universe_evidence_review_worklist_status(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_review_worklist",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_review_worklist/status",
) -> PitUniverseEvidenceReviewWorklistStatusResult:
    index_frame = scan_pit_universe_evidence_review_worklist_artifacts(root)
    health = check_pit_universe_evidence_review_worklist_health(
        index_df=index_frame,
        output_dir=Path(output_dir) / "_health_probe",
    )
    status_frame = build_pit_universe_evidence_review_worklist_status_frame(index_frame, health_result=health)
    summary_frame = summarize_pit_universe_evidence_review_worklist_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_pit_universe_evidence_review_worklist_status_paths(output_dir, status_id)
    result = PitUniverseEvidenceReviewWorklistStatusResult(
        status_id=status_id,
        status=_string_or_empty(summary.get("status")) or "WARN",
        workflow_stage=_string_or_empty(summary.get("workflow_stage")) or NO_WORKLIST_STAGE,
        latest_worklist_id=_string_or_empty(summary.get("latest_worklist_id")),
        health_status=_string_or_empty(summary.get("health_status")),
        review_id=_string_or_empty(summary.get("review_id")),
        helper_id=_string_or_empty(summary.get("helper_id")),
        row_count=_to_int(summary.get("row_count")),
        symbol_count=_to_int(summary.get("symbol_count")),
        signal_date_count=_to_int(summary.get("signal_date_count")),
        needs_evidence_count=_to_int(summary.get("needs_evidence_count")),
        future_dated_hint_count=_to_int(summary.get("future_dated_hint_count")),
        authoritative_hint_count=_to_int(summary.get("authoritative_hint_count")),
        next_manual_action=_string_or_empty(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string_or_empty(summary.get("workflow_stage")) or NO_WORKLIST_STAGE,
            "approved_rows_created": False,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
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
            "pit_universe_evidence_review_worklist_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_review_worklist_status_artifacts(result)
    return result


def build_pit_universe_evidence_review_worklist_status_frame(
    index_frame: pd.DataFrame,
    *,
    health_result,
) -> pd.DataFrame:
    latest = _latest_worklist_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST",
                status="MISSING",
                next_action="Run pit-universe-evidence-review-worklist from evidence helper and reviewed PIT universe rows.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST",
                status=_worklist_status(latest),
                latest_artifact_id=_string_or_empty(latest.get("worklist_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                review_id=_string_or_empty(latest.get("review_id")),
                helper_id=_string_or_empty(latest.get("helper_id")),
                row_count=_to_int(latest.get("row_count")),
                symbol_count=_to_int(latest.get("symbol_count")),
                signal_date_count=_to_int(latest.get("signal_date_count")),
                needs_evidence_count=_to_int(latest.get("needs_evidence_count")),
                future_dated_hint_count=_to_int(latest.get("future_dated_hint_count")),
                authoritative_hint_count=_to_int(latest.get("authoritative_hint_count")),
                next_action=_worklist_next_action(latest),
                notes="Latest local PIT universe evidence review worklist artifact.",
            )
        )
    rows.append(
        _status_row(
            component="PIT_UNIVERSE_EVIDENCE_REVIEW_WORKLIST_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("pit_universe_evidence_review_worklist_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="In-memory health evaluation for PIT universe evidence review worklist artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_pit_universe_evidence_review_worklist_status(
    index_frame: pd.DataFrame,
    *,
    health_result,
) -> pd.DataFrame:
    latest = _latest_worklist_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_WORKLIST_STAGE,
                    health_status="MISSING",
                    next_manual_action=(
                        "Run pit-universe-evidence-review-worklist from evidence helper and reviewed PIT universe rows."
                    ),
                )
            ]
        )
    needs_evidence_count = _to_int(latest.get("needs_evidence_count"))
    if health_result.status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair PIT universe evidence review worklist artifacts before using reviewer templates."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review PIT universe evidence review worklist health warnings before using reviewer templates."
    elif needs_evidence_count > 0:
        stage = NEEDS_REVIEW_STAGE
        status = "WARN"
        next_action = (
            "Complete PIT universe evidence fields manually; worklist hints are non-authoritative and do not approve rows."
        )
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review completed worklist manually, then rerun the PIT universe overlay review workflow."
    return pd.DataFrame(
        [
            _summary_row(
                latest_worklist_id=_string_or_empty(latest.get("worklist_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                review_id=_string_or_empty(latest.get("review_id")),
                helper_id=_string_or_empty(latest.get("helper_id")),
                row_count=_to_int(latest.get("row_count")),
                symbol_count=_to_int(latest.get("symbol_count")),
                signal_date_count=_to_int(latest.get("signal_date_count")),
                needs_evidence_count=needs_evidence_count,
                future_dated_hint_count=_to_int(latest.get("future_dated_hint_count")),
                authoritative_hint_count=_to_int(latest.get("authoritative_hint_count")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_pit_universe_evidence_review_worklist_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> PitUniverseEvidenceReviewWorklistStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return PitUniverseEvidenceReviewWorklistStatusPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_review_worklist_status_report=artifact_dir
        / "pit_universe_evidence_review_worklist_status_report.md",
        pit_universe_evidence_review_worklist_status_csv=artifact_dir
        / "pit_universe_evidence_review_worklist_status.csv",
        pit_universe_evidence_review_worklist_status_summary=artifact_dir
        / "pit_universe_evidence_review_worklist_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_review_worklist_status_artifacts(
    result: PitUniverseEvidenceReviewWorklistStatusResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceReviewWorklistStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.pit_universe_evidence_review_worklist_status_csv, index=False)
    result.summary_frame.to_csv(paths.pit_universe_evidence_review_worklist_status_summary, index=False)
    metadata = build_pit_universe_evidence_review_worklist_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_review_worklist_status_report.write_text(
        render_pit_universe_evidence_review_worklist_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_review_worklist_status_metadata(
    result: PitUniverseEvidenceReviewWorklistStatusResult,
    paths: PitUniverseEvidenceReviewWorklistStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_worklist_id": result.latest_worklist_id,
        "health_status": result.health_status,
        "review_id": result.review_id,
        "helper_id": result.helper_id,
        "row_count": result.row_count,
        "symbol_count": result.symbol_count,
        "signal_date_count": result.signal_date_count,
        "needs_evidence_count": result.needs_evidence_count,
        "future_dated_hint_count": result.future_dated_hint_count,
        "authoritative_hint_count": result.authoritative_hint_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": _safety_statement(),
    }


def render_pit_universe_evidence_review_worklist_status_report(
    result: PitUniverseEvidenceReviewWorklistStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Evidence Review Worklist Status",
            "",
            _safety_statement(),
            "",
            "Worklist hints remain non-authoritative context. They do not approve rows, export universe files, or make rows valid for signal dates.",
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


def _latest_worklist_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    for column in ["created_at", "worklist_id"]:
        if column not in frame:
            frame[column] = ""
    return frame.sort_values(["created_at", "worklist_id"]).iloc[-1].to_dict()


def _worklist_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_evidence_count")) > 0:
        return "NEEDS_REVIEW"
    return "READY"


def _worklist_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("needs_evidence_count")) > 0:
        return "Complete PIT universe evidence fields manually; worklist hints are non-authoritative and do not approve rows."
    return "Review completed worklist manually, then rerun the PIT universe overlay review workflow."


def _health_next_action(status: str) -> str:
    normalized = _string_or_empty(status).upper()
    if normalized == "PASS":
        return "No PIT universe evidence review worklist health issues detected."
    if normalized == "FAIL":
        return "Repair PIT universe evidence review worklist health errors."
    if normalized == "WARN":
        return "Review PIT universe evidence review worklist health warnings."
    return "Run pit-universe-evidence-review-worklist-health."


def _status_warnings(index_frame: pd.DataFrame, health_result: Any, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No PIT universe evidence review worklist artifacts were found.")
    if _to_int(summary.get("needs_evidence_count")) > 0:
        warnings.append("Latest PIT universe evidence review worklist rows still need evidence.")
    if _to_int(summary.get("future_dated_hint_count")) > 0:
        warnings.append("Latest PIT universe evidence review worklist contains future-dated non-authoritative hints.")
    if getattr(health_result, "status", "") == "FAIL":
        warnings.append("PIT universe evidence review worklist health failed.")
    return warnings


def _status_row(
    *,
    component: str,
    status: str,
    latest_artifact_id: str = "",
    report_path: str = "",
    metadata_path: str = "",
    review_id: str = "",
    helper_id: str = "",
    row_count: int = 0,
    symbol_count: int = 0,
    signal_date_count: int = 0,
    needs_evidence_count: int = 0,
    future_dated_hint_count: int = 0,
    authoritative_hint_count: int = 0,
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
        "review_id": review_id,
        "helper_id": helper_id,
        "row_count": int(row_count),
        "symbol_count": int(symbol_count),
        "signal_date_count": int(signal_date_count),
        "needs_evidence_count": int(needs_evidence_count),
        "future_dated_hint_count": int(future_dated_hint_count),
        "authoritative_hint_count": int(authoritative_hint_count),
        "issue_count": int(issue_count),
        "warning_count": int(warning_count),
        "error_count": int(error_count),
        "next_action": next_action,
        "notes": notes,
    }


def _summary_row(
    *,
    latest_worklist_id: str = "",
    status: str,
    workflow_stage: str,
    health_status: str,
    review_id: str = "",
    helper_id: str = "",
    row_count: int = 0,
    symbol_count: int = 0,
    signal_date_count: int = 0,
    needs_evidence_count: int = 0,
    future_dated_hint_count: int = 0,
    authoritative_hint_count: int = 0,
    report_path: str = "",
    next_manual_action: str,
) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(
        {
            "latest_worklist_id": latest_worklist_id,
            "status": status,
            "workflow_stage": workflow_stage,
            "health_status": health_status,
            "review_id": review_id,
            "helper_id": helper_id,
            "row_count": int(row_count),
            "symbol_count": int(symbol_count),
            "signal_date_count": int(signal_date_count),
            "needs_evidence_count": int(needs_evidence_count),
            "future_dated_hint_count": int(future_dated_hint_count),
            "authoritative_hint_count": int(authoritative_hint_count),
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


def _safety_statement() -> str:
    return (
        "No approval, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
