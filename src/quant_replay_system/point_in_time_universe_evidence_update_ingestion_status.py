"""Status view for PIT universe evidence update ingestion artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.point_in_time_universe_evidence_update_ingestion_health import (
    check_pit_universe_evidence_update_ingestion_health,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_index import (
    scan_pit_universe_evidence_update_ingestion_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "row_count",
    "ready_for_review_update_count",
    "blocked_count",
    "approval_requested_count",
    "approved_ready_count",
    "duplicate_identity_count",
    "suggested_copy_risk_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_ingestion_id",
    "status",
    "workflow_stage",
    "health_status",
    "row_count",
    "ready_for_review_update_count",
    "blocked_count",
    "approval_requested_count",
    "approved_ready_count",
    "duplicate_identity_count",
    "suggested_copy_risk_count",
    "report_path",
    "review_updates_path",
    "next_manual_action",
]

NO_INGESTION_STAGE = "NO_PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION"
NO_READY_STAGE = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
PARTIAL_READY_STAGE = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_PARTIAL_READY"
READY_STAGE = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_READY_FOR_REVIEW_APPLY"
HEALTH_WARN_STAGE = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_HEALTH_WARN"
FAILED_STAGE = "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local PIT universe evidence update ingestion artifacts only.",
    "Does not apply approvals, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionStatusPaths:
    artifact_dir: Path
    pit_universe_evidence_update_ingestion_status_report: Path
    pit_universe_evidence_update_ingestion_status_csv: Path
    pit_universe_evidence_update_ingestion_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_update_ingestion_status_report": self.pit_universe_evidence_update_ingestion_status_report,
            "pit_universe_evidence_update_ingestion_status_csv": self.pit_universe_evidence_update_ingestion_status_csv,
            "pit_universe_evidence_update_ingestion_status_summary": self.pit_universe_evidence_update_ingestion_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_ingestion_id: str
    health_status: str
    row_count: int
    ready_for_review_update_count: int
    blocked_count: int
    approval_requested_count: int
    approved_ready_count: int
    duplicate_identity_count: int
    suggested_copy_risk_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_pit_universe_evidence_update_ingestion_status(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_update_ingestion/status",
) -> PitUniverseEvidenceUpdateIngestionStatusResult:
    index_frame = scan_pit_universe_evidence_update_ingestion_artifacts(root)
    health = check_pit_universe_evidence_update_ingestion_health(
        index_df=index_frame,
        output_dir=Path(output_dir) / "_health_probe",
    )
    status_frame = build_pit_universe_evidence_update_ingestion_status_frame(index_frame, health_result=health)
    summary_frame = summarize_pit_universe_evidence_update_ingestion_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_pit_universe_evidence_update_ingestion_status_paths(output_dir, status_id)
    result = PitUniverseEvidenceUpdateIngestionStatusResult(
        status_id=status_id,
        status=_string(summary.get("status")) or "WARN",
        workflow_stage=_string(summary.get("workflow_stage")) or NO_INGESTION_STAGE,
        latest_ingestion_id=_string(summary.get("latest_ingestion_id")),
        health_status=_string(summary.get("health_status")),
        row_count=_int(summary.get("row_count")),
        ready_for_review_update_count=_int(summary.get("ready_for_review_update_count")),
        blocked_count=_int(summary.get("blocked_count")),
        approval_requested_count=_int(summary.get("approval_requested_count")),
        approved_ready_count=_int(summary.get("approved_ready_count")),
        duplicate_identity_count=_int(summary.get("duplicate_identity_count")),
        suggested_copy_risk_count=_int(summary.get("suggested_copy_risk_count")),
        next_manual_action=_string(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string(summary.get("workflow_stage")) or NO_INGESTION_STAGE,
            "approval_applied": False,
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
            "pit_universe_evidence_update_ingestion_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_update_ingestion_status_artifacts(result)
    return result


def build_pit_universe_evidence_update_ingestion_status_frame(
    index_frame: pd.DataFrame,
    *,
    health_result,
) -> pd.DataFrame:
    latest = _latest_ingestion_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
                status="MISSING",
                next_action="Run pit-universe-evidence-update-ingestion after reviewer-completed worklist updates.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION",
                status=_ingestion_status(latest),
                latest_artifact_id=_string(latest.get("ingestion_id")),
                report_path=_string(latest.get("report_path")),
                metadata_path=_string(latest.get("metadata_path")),
                row_count=_int(latest.get("row_count")),
                ready_for_review_update_count=_int(latest.get("ready_for_review_update_count")),
                blocked_count=_int(latest.get("blocked_count")),
                approval_requested_count=_int(latest.get("approval_requested_count")),
                approved_ready_count=_int(latest.get("approved_ready_count")),
                duplicate_identity_count=_int(latest.get("duplicate_identity_count")),
                suggested_copy_risk_count=_int(latest.get("suggested_copy_risk_count")),
                next_action=_ingestion_next_action(latest),
                notes="Latest local PIT universe evidence update ingestion artifact.",
            )
        )
    rows.append(
        _status_row(
            component="PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("pit_universe_evidence_update_ingestion_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="In-memory health evaluation for PIT universe evidence update ingestion artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_pit_universe_evidence_update_ingestion_status(
    index_frame: pd.DataFrame,
    *,
    health_result,
) -> pd.DataFrame:
    latest = _latest_ingestion_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_INGESTION_STAGE,
                    health_status="MISSING",
                    next_manual_action="Run pit-universe-evidence-update-ingestion after reviewer-completed worklist updates.",
                )
            ]
        )
    ready = _int(latest.get("ready_for_review_update_count"))
    blocked = _int(latest.get("blocked_count"))
    row_count = _int(latest.get("row_count"))
    if health_result.status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair PIT universe evidence update ingestion artifacts before using clean review updates."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review PIT universe evidence update ingestion health warnings before using clean review updates."
    elif row_count == 0 or ready == 0:
        stage = NO_READY_STAGE
        status = "WARN"
        next_action = "Reviewer has not completed usable PIT universe evidence update rows yet."
    elif blocked > 0:
        stage = PARTIAL_READY_STAGE
        status = "WARN"
        next_action = "Review clean review_updates artifact manually before a separate pit-universe-overlay-review run."
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review clean review_updates artifact manually before a separate pit-universe-overlay-review run."
    return pd.DataFrame(
        [
            _summary_row(
                latest_ingestion_id=_string(latest.get("ingestion_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                row_count=row_count,
                ready_for_review_update_count=ready,
                blocked_count=blocked,
                approval_requested_count=_int(latest.get("approval_requested_count")),
                approved_ready_count=_int(latest.get("approved_ready_count")),
                duplicate_identity_count=_int(latest.get("duplicate_identity_count")),
                suggested_copy_risk_count=_int(latest.get("suggested_copy_risk_count")),
                report_path=_string(latest.get("report_path")),
                review_updates_path=_string(latest.get("review_updates_path")),
                next_manual_action=next_action,
            )
        ]
    )


def resolve_pit_universe_evidence_update_ingestion_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> PitUniverseEvidenceUpdateIngestionStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return PitUniverseEvidenceUpdateIngestionStatusPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_update_ingestion_status_report=artifact_dir
        / "pit_universe_evidence_update_ingestion_status_report.md",
        pit_universe_evidence_update_ingestion_status_csv=artifact_dir
        / "pit_universe_evidence_update_ingestion_status.csv",
        pit_universe_evidence_update_ingestion_status_summary=artifact_dir
        / "pit_universe_evidence_update_ingestion_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_update_ingestion_status_artifacts(
    result: PitUniverseEvidenceUpdateIngestionStatusResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceUpdateIngestionStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.pit_universe_evidence_update_ingestion_status_csv, index=False)
    result.summary_frame.to_csv(paths.pit_universe_evidence_update_ingestion_status_summary, index=False)
    metadata = build_pit_universe_evidence_update_ingestion_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_update_ingestion_status_report.write_text(
        render_pit_universe_evidence_update_ingestion_status_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_update_ingestion_status_metadata(
    result: PitUniverseEvidenceUpdateIngestionStatusResult,
    paths: PitUniverseEvidenceUpdateIngestionStatusPaths,
) -> dict[str, Any]:
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_ingestion_id": result.latest_ingestion_id,
        "health_status": result.health_status,
        "row_count": result.row_count,
        "ready_for_review_update_count": result.ready_for_review_update_count,
        "blocked_count": result.blocked_count,
        "approval_requested_count": result.approval_requested_count,
        "approved_ready_count": result.approved_ready_count,
        "duplicate_identity_count": result.duplicate_identity_count,
        "suggested_copy_risk_count": result.suggested_copy_risk_count,
        "next_manual_action": result.next_manual_action,
        "report_path": _string(summary.get("report_path")),
        "review_updates_path": _string(summary.get("review_updates_path")),
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": _safety_statement(),
    }


def render_pit_universe_evidence_update_ingestion_status_report(
    result: PitUniverseEvidenceUpdateIngestionStatusResult,
) -> str:
    return "\n".join(
        [
            "# PIT Universe Evidence Update Ingestion Status",
            "",
            _safety_statement(),
            "",
            "## Summary",
            "",
            _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
            "",
            "## Components",
            "",
            _markdown_table(result.status_frame, STATUS_COLUMNS),
            "",
        ]
    )


def _latest_ingestion_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    return frame.sort_values(["created_at", "ingestion_id"], ascending=[False, False]).iloc[0].to_dict()


def _ingestion_status(row: dict[str, Any]) -> str:
    ready = _int(row.get("ready_for_review_update_count"))
    blocked = _int(row.get("blocked_count"))
    if ready == 0:
        return "WARN"
    return "WARN" if blocked else "READY"


def _ingestion_next_action(row: dict[str, Any]) -> str:
    ready = _int(row.get("ready_for_review_update_count"))
    blocked = _int(row.get("blocked_count"))
    if ready == 0:
        return "Reviewer has not completed usable PIT universe evidence update rows yet."
    if blocked:
        return "Review clean review_updates artifact manually before a separate pit-universe-overlay-review run."
    return "Clean review_updates artifact is ready for manual review before separate pit-universe-overlay-review."


def _health_next_action(status: str) -> str:
    if status == "FAIL":
        return "Repair PIT universe evidence update ingestion artifacts before using clean review updates."
    if status == "WARN":
        return "Review PIT universe evidence update ingestion health warnings before using clean review updates."
    if status == "MISSING":
        return "Run pit-universe-evidence-update-ingestion-health."
    return "Health checks passed for PIT universe evidence update ingestion artifacts."


def _status_warnings(index_frame: pd.DataFrame, health_result, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No PIT universe evidence update ingestion artifacts found.")
    if health_result.status in {"WARN", "FAIL"}:
        warnings.append(f"PIT universe evidence update ingestion health status is {health_result.status}.")
    if _int(summary.get("ready_for_review_update_count")) == 0:
        warnings.append("Latest PIT universe evidence update ingestion has no clean review updates ready.")
    return warnings


def _status_row(**values: Any) -> dict[str, Any]:
    return {column: values.get(column, "") for column in STATUS_COLUMNS}


def _summary_row(**values: Any) -> dict[str, Any]:
    return {column: values.get(column, "") for column in SUMMARY_COLUMNS}


def _finalize_status_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STATUS_COLUMNS)
    output = frame.copy()
    for column in STATUS_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[STATUS_COLUMNS].reset_index(drop=True)


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows._"
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    return output[columns].to_markdown(index=False)


def _safety_statement() -> str:
    return (
        "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, "
        "snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, "
        "external API, or cache mutation was invoked."
    )
