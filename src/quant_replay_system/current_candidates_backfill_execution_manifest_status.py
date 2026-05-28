"""Status view for current-candidates backfill execution manifest artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.current_candidates_backfill_execution_manifest_health import (
    check_current_candidates_backfill_execution_manifest_health,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_index import (
    scan_current_candidates_backfill_execution_manifest_artifacts,
)


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "row_count",
    "ready_count",
    "blocked_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_execution_manifest_id",
    "status",
    "workflow_stage",
    "health_status",
    "row_count",
    "ready_count",
    "blocked_count",
    "blocked_missing_snapshot_count",
    "blocked_snapshot_quality_count",
    "blocked_universe_as_of_count",
    "blocked_plan_infeasible_count",
    "reviewed_execution_required_count",
    "report_path",
    "next_manual_action",
]

NO_MANIFEST_STAGE = "NO_CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST"
READY_STAGE = "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_READY_FOR_REVIEW"
BLOCKED_STAGE = "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED"
HEALTH_WARN_STAGE = "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_HEALTH_WARN"
FAILED_STAGE = "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local current-candidates backfill execution manifest artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestStatusPaths:
    artifact_dir: Path
    current_candidates_backfill_execution_manifest_status_report: Path
    current_candidates_backfill_execution_manifest_status_csv: Path
    current_candidates_backfill_execution_manifest_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_execution_manifest_status_report": (
                self.current_candidates_backfill_execution_manifest_status_report
            ),
            "current_candidates_backfill_execution_manifest_status_csv": (
                self.current_candidates_backfill_execution_manifest_status_csv
            ),
            "current_candidates_backfill_execution_manifest_status_summary": (
                self.current_candidates_backfill_execution_manifest_status_summary
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_execution_manifest_id: str
    health_status: str
    row_count: int
    ready_count: int
    blocked_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_current_candidates_backfill_execution_manifest_status(
    *,
    root: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest/status",
) -> CurrentCandidatesBackfillExecutionManifestStatusResult:
    index_frame = scan_current_candidates_backfill_execution_manifest_artifacts(root)
    health = check_current_candidates_backfill_execution_manifest_health(
        index_df=index_frame,
        output_dir=Path(output_dir) / "_health_probe",
    )
    status_frame = build_current_candidates_backfill_execution_manifest_status_frame(index_frame, health_result=health)
    summary_frame = summarize_current_candidates_backfill_execution_manifest_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_current_candidates_backfill_execution_manifest_status_paths(output_dir, status_id)
    result = CurrentCandidatesBackfillExecutionManifestStatusResult(
        status_id=status_id,
        status=_string_or_empty(summary.get("status")) or "WARN",
        workflow_stage=_string_or_empty(summary.get("workflow_stage")) or NO_MANIFEST_STAGE,
        latest_execution_manifest_id=_string_or_empty(summary.get("latest_execution_manifest_id")),
        health_status=_string_or_empty(summary.get("health_status")),
        row_count=_to_int(summary.get("row_count")),
        ready_count=_to_int(summary.get("ready_count")),
        blocked_count=_to_int(summary.get("blocked_count")),
        next_manual_action=_string_or_empty(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string_or_empty(summary.get("workflow_stage")) or NO_MANIFEST_STAGE,
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
            "execution_manifest_artifacts_only": True,
        },
    )
    write_current_candidates_backfill_execution_manifest_status_artifacts(result)
    return result


def build_current_candidates_backfill_execution_manifest_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_manifest_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(
            _status_row(
                component="CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
                status="MISSING",
                next_action="Run current-candidates-backfill-execution-manifest.",
            )
        )
    else:
        rows.append(
            _status_row(
                component="CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
                status=_manifest_status(latest),
                latest_artifact_id=_string_or_empty(latest.get("execution_manifest_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                row_count=_to_int(latest.get("row_count")),
                ready_count=_to_int(latest.get("ready_count")),
                blocked_count=_to_int(latest.get("blocked_count")),
                next_action=_manifest_next_action(latest),
                notes="Latest local execution-readiness manifest artifact.",
            )
        )
    rows.append(
        _status_row(
            component="CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("current_candidates_backfill_execution_manifest_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action=_health_next_action(health_result.status if len(index_frame) else "MISSING"),
            notes="In-memory health evaluation for execution manifest artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_current_candidates_backfill_execution_manifest_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    latest = _latest_manifest_row(index_frame)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_MANIFEST_STAGE,
                    health_status="MISSING",
                    next_manual_action="Run current-candidates-backfill-execution-manifest after reviewing a warmup-aware backfill plan.",
                )
            ]
        )
    if health_result.status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair execution manifest artifacts before reviewed candidate generation."
    elif health_result.status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review execution manifest health warnings before using readiness output."
    elif _to_int(latest.get("blocked_count")) > 0:
        stage = BLOCKED_STAGE
        status = "WARN"
        next_action = "Resolve blocked signal-date inputs before candidate generation; no current-candidates were run."
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review READY_FOR_REVIEW signal dates manually before any separate candidate generation step."
    summary = pd.DataFrame(
        [
            _summary_row(
                latest_execution_manifest_id=_string_or_empty(latest.get("execution_manifest_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                row_count=_to_int(latest.get("row_count")),
                ready_count=_to_int(latest.get("ready_count")),
                blocked_count=_to_int(latest.get("blocked_count")),
                blocked_missing_snapshot_count=_to_int(latest.get("blocked_missing_snapshot_count")),
                blocked_snapshot_quality_count=_to_int(latest.get("blocked_snapshot_quality_count")),
                blocked_universe_as_of_count=_to_int(latest.get("blocked_universe_as_of_count")),
                blocked_plan_infeasible_count=_to_int(latest.get("blocked_plan_infeasible_count")),
                reviewed_execution_required_count=_to_int(latest.get("reviewed_execution_required_count")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )
    return summary


def resolve_current_candidates_backfill_execution_manifest_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> CurrentCandidatesBackfillExecutionManifestStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return CurrentCandidatesBackfillExecutionManifestStatusPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_execution_manifest_status_report=(
            artifact_dir / "current_candidates_backfill_execution_manifest_status_report.md"
        ),
        current_candidates_backfill_execution_manifest_status_csv=(
            artifact_dir / "current_candidates_backfill_execution_manifest_status.csv"
        ),
        current_candidates_backfill_execution_manifest_status_summary=(
            artifact_dir / "current_candidates_backfill_execution_manifest_status_summary.csv"
        ),
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_execution_manifest_status_artifacts(
    result: CurrentCandidatesBackfillExecutionManifestStatusResult,
) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillExecutionManifestStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.current_candidates_backfill_execution_manifest_status_csv, index=False)
    result.summary_frame.to_csv(paths.current_candidates_backfill_execution_manifest_status_summary, index=False)
    metadata = build_current_candidates_backfill_execution_manifest_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_execution_manifest_status_report.write_text(
        render_current_candidates_backfill_execution_manifest_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_execution_manifest_status_metadata(
    result: CurrentCandidatesBackfillExecutionManifestStatusResult,
    paths: CurrentCandidatesBackfillExecutionManifestStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_execution_manifest_id": result.latest_execution_manifest_id,
        "health_status": result.health_status,
        "row_count": result.row_count,
        "ready_count": result.ready_count,
        "blocked_count": result.blocked_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
            "order placement, message delivery, or network/API call was invoked."
        ),
    }


def render_current_candidates_backfill_execution_manifest_status_report(
    result: CurrentCandidatesBackfillExecutionManifestStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Current-Candidates Backfill Execution Manifest Status",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked. This status view summarizes local execution manifest artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table(
                {
                    "status_id": result.status_id,
                    "status": result.status,
                    "workflow_stage": result.workflow_stage,
                    "latest_execution_manifest_id": result.latest_execution_manifest_id,
                    "health_status": result.health_status,
                    "row_count": result.row_count,
                    "ready_count": result.ready_count,
                    "blocked_count": result.blocked_count,
                    "next_manual_action": result.next_manual_action,
                }
            ),
            "",
            "## Components",
            "",
            _markdown_table(result.status_frame, ["component", "status", "latest_artifact_id", "issue_count", "warning_count", "error_count", "next_action"]),
            "",
            "## Latest Manifest Summary",
            "",
            _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
            "",
            "## Warnings",
            "",
            _warnings_section(result.warnings),
            "",
        ]
    )


def _latest_manifest_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    if "created_at" not in frame.columns:
        frame["created_at"] = ""
    frame["_sort_created_at"] = frame["created_at"].astype(str)
    frame["_sort_manifest_id"] = frame.get("execution_manifest_id", "").astype(str)
    return frame.sort_values(["_sort_created_at", "_sort_manifest_id"]).iloc[-1].to_dict()


def _manifest_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("blocked_count")) > 0:
        return "WARN"
    return _string_or_empty(row.get("status")) or "PASS"


def _manifest_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("blocked_count")) > 0:
        return "Resolve blocked readiness rows before candidate generation."
    return "Review READY_FOR_REVIEW rows manually before any separate candidate generation."


def _status_warnings(index_frame: pd.DataFrame, health_result, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No current-candidates backfill execution manifest artifacts were found.")
    if health_result.status == "WARN":
        warnings.append("Execution manifest health warnings are present.")
    if health_result.status == "FAIL":
        warnings.append("Execution manifest health failures are present.")
    if _to_int(summary.get("blocked_count")) > 0:
        warnings.append("Latest execution manifest has blocked signal-date rows.")
    return warnings


def _health_next_action(status: str) -> str:
    if status == "PASS":
        return "Health passed; review readiness rows manually before candidate generation."
    if status == "WARN":
        return "Review execution manifest health warnings."
    if status == "FAIL":
        return "Repair execution manifest artifacts before candidate generation."
    return "Run current-candidates-backfill-execution-manifest-index and health."


def _status_row(**updates: Any) -> dict[str, Any]:
    row = {column: "" for column in STATUS_COLUMNS}
    row.update(updates)
    return row


def _summary_row(**updates: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(updates)
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


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 100) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)
