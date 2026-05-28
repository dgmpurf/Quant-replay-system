"""Local-only status view for current-candidates backfill plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.current_candidates_backfill_plan_health import check_current_candidates_backfill_plan_health
from quant_replay_system.current_candidates_backfill_plan_index import scan_current_candidates_backfill_plan_artifacts


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "selected_date_count",
    "issue_count",
    "warning_count",
    "error_count",
    "next_action",
    "notes",
]

SUMMARY_COLUMNS = [
    "latest_plan_id",
    "status",
    "workflow_stage",
    "health_status",
    "overall_health_status",
    "selected_date_count",
    "first_signal_date",
    "last_signal_date",
    "warmup_trading_days",
    "warmup_feasible_count",
    "forward_1d_available_count",
    "forward_3d_available_count",
    "forward_5d_available_count",
    "forward_10d_available_count",
    "latest_plan_is_warmup_aware",
    "legacy_plan_count",
    "stale_plan_warning_count",
    "active_plan_issue_count",
    "active_plan_error_count",
    "active_plan_warning_count",
    "legacy_missing_warmup_count",
    "report_path",
    "next_manual_action",
]

NO_PLAN_STAGE = "NO_CURRENT_CANDIDATES_BACKFILL_PLAN"
READY_STAGE = "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
HEALTH_WARN_STAGE = "CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH_WARN"
FAILED_STAGE = "CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED"

STATUS_LIMITATIONS = [
    "Summarizes local current-candidates backfill plan artifacts only.",
    "Does not run current-candidates, build snapshots, compute forward labels, or mutate cache.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanStatusPaths:
    artifact_dir: Path
    current_candidates_backfill_plan_status_report: Path
    current_candidates_backfill_plan_status_csv: Path
    current_candidates_backfill_plan_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_plan_status_report": self.current_candidates_backfill_plan_status_report,
            "current_candidates_backfill_plan_status_csv": self.current_candidates_backfill_plan_status_csv,
            "current_candidates_backfill_plan_status_summary": self.current_candidates_backfill_plan_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_plan_id: str
    health_status: str
    selected_date_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_current_candidates_backfill_plan_status(
    *,
    root: str | Path = "outputs/reports/current_candidates_backfill_plan",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_plan/status",
) -> CurrentCandidatesBackfillPlanStatusResult:
    index_frame = scan_current_candidates_backfill_plan_artifacts(root)
    health = check_current_candidates_backfill_plan_health(index_df=index_frame, output_dir=Path(output_dir) / "_health_probe")
    status_frame = build_current_candidates_backfill_plan_status_frame(index_frame, health_result=health)
    summary_frame = summarize_current_candidates_backfill_plan_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, length=12)
    paths = resolve_current_candidates_backfill_plan_status_paths(output_dir, status_id)
    result = CurrentCandidatesBackfillPlanStatusResult(
        status_id=status_id,
        status=_string_or_empty(summary.get("status")) or "WARN",
        workflow_stage=_string_or_empty(summary.get("workflow_stage")) or NO_PLAN_STAGE,
        latest_plan_id=_string_or_empty(summary.get("latest_plan_id")),
        health_status=_string_or_empty(summary.get("health_status")),
        selected_date_count=_to_int(summary.get("selected_date_count")),
        next_manual_action=_string_or_empty(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health),
        known_limitations=STATUS_LIMITATIONS,
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _string_or_empty(summary.get("workflow_stage")) or NO_PLAN_STAGE,
            "current_candidates_executed": False,
            "data_pipeline_executed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "plan_artifacts_only": True,
        },
    )
    write_current_candidates_backfill_plan_status_artifacts(result)
    return result


def build_current_candidates_backfill_plan_status_frame(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    health_summary = _health_summary(health_result)
    latest = _latest_active_plan_row(index_frame, health_summary)
    active_health_status = _string_or_empty(health_summary.get("active_plan_health_status")) or health_result.status
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(_status_row(component="CURRENT_CANDIDATES_BACKFILL_PLAN", status="MISSING", next_action="Run current-candidates-backfill-plan."))
    else:
        rows.append(
            _status_row(
                component="CURRENT_CANDIDATES_BACKFILL_PLAN",
                status=_string_or_empty(latest.get("status")) or "PASS",
                latest_artifact_id=_string_or_empty(latest.get("plan_id")),
                report_path=_string_or_empty(latest.get("report_path")),
                metadata_path=_string_or_empty(latest.get("metadata_path")),
                selected_date_count=_to_int(latest.get("selected_date_count")),
                next_action="Review the backfill plan before candidate generation.",
                notes="Latest local plan artifact.",
            )
        )
    rows.append(
        _status_row(
            component="CURRENT_CANDIDATES_BACKFILL_PLAN_HEALTH",
            status=active_health_status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("current_candidates_backfill_plan_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=_to_int(health_summary.get("active_plan_issue_count")),
            warning_count=_to_int(health_summary.get("active_plan_warning_count")),
            error_count=_to_int(health_summary.get("active_plan_error_count")),
            next_action=_health_next_action(active_health_status if len(index_frame) else "MISSING"),
            notes=(
                "In-memory active-plan health evaluation; "
                f"overall_health_status={health_result.status}; "
                f"legacy_plan_count={_to_int(health_summary.get('legacy_plan_count'))}; "
                f"stale_plan_warning_count={_to_int(health_summary.get('stale_plan_warning_count'))}"
            ),
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_current_candidates_backfill_plan_status(index_frame: pd.DataFrame, *, health_result) -> pd.DataFrame:
    health_summary = _health_summary(health_result)
    latest = _latest_active_plan_row(index_frame, health_summary)
    if latest is None:
        return pd.DataFrame(
            [
                _summary_row(
                    status="WARN",
                    workflow_stage=NO_PLAN_STAGE,
                    health_status="MISSING",
                    next_manual_action="Run current-candidates-backfill-plan before multi-date candidate generation.",
                )
            ]
        )
    active_health_status = _string_or_empty(health_summary.get("active_plan_health_status")) or health_result.status
    if active_health_status == "FAIL":
        stage = FAILED_STAGE
        status = "FAIL"
        next_action = "Repair current-candidates backfill plan artifacts before any backfill execution."
    elif active_health_status == "WARN":
        stage = HEALTH_WARN_STAGE
        status = "WARN"
        next_action = "Review current-candidates backfill plan health warnings before execution."
    else:
        stage = READY_STAGE
        status = "PASS"
        next_action = "Review the backfill plan, source policy, warmup coverage, and forward horizons before candidate generation."
    summary = pd.DataFrame(
        [
            _summary_row(
                latest_plan_id=_string_or_empty(latest.get("plan_id")),
                status=status,
                workflow_stage=stage,
                health_status=active_health_status,
                overall_health_status=health_result.status,
                selected_date_count=_to_int(latest.get("selected_date_count")),
                first_signal_date=_string_or_empty(latest.get("first_signal_date")),
                last_signal_date=_string_or_empty(latest.get("last_signal_date")),
                warmup_trading_days=_to_int(latest.get("warmup_trading_days")),
                warmup_feasible_count=_to_int(latest.get("warmup_feasible_count")),
                forward_1d_available_count=_to_int(latest.get("forward_1d_available_count")),
                forward_3d_available_count=_to_int(latest.get("forward_3d_available_count")),
                forward_5d_available_count=_to_int(latest.get("forward_5d_available_count")),
                forward_10d_available_count=_to_int(latest.get("forward_10d_available_count")),
                latest_plan_is_warmup_aware=_to_bool(latest.get("warmup_aware")),
                legacy_plan_count=_to_int(health_summary.get("legacy_plan_count")),
                stale_plan_warning_count=_to_int(health_summary.get("stale_plan_warning_count")),
                active_plan_issue_count=_to_int(health_summary.get("active_plan_issue_count")),
                active_plan_error_count=_to_int(health_summary.get("active_plan_error_count")),
                active_plan_warning_count=_to_int(health_summary.get("active_plan_warning_count")),
                legacy_missing_warmup_count=_to_int(health_summary.get("legacy_missing_warmup_count")),
                report_path=_string_or_empty(latest.get("report_path")),
                next_manual_action=next_action,
            )
        ]
    )
    summary["latest_plan_is_warmup_aware"] = summary["latest_plan_is_warmup_aware"].map(_to_bool).astype(object)
    return summary


def resolve_current_candidates_backfill_plan_status_paths(
    output_dir: str | Path,
    status_id: str,
) -> CurrentCandidatesBackfillPlanStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return CurrentCandidatesBackfillPlanStatusPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_plan_status_report=artifact_dir / "current_candidates_backfill_plan_status_report.md",
        current_candidates_backfill_plan_status_csv=artifact_dir / "current_candidates_backfill_plan_status.csv",
        current_candidates_backfill_plan_status_summary=artifact_dir / "current_candidates_backfill_plan_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_plan_status_artifacts(result: CurrentCandidatesBackfillPlanStatusResult) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillPlanStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.current_candidates_backfill_plan_status_csv, index=False)
    result.summary_frame.to_csv(paths.current_candidates_backfill_plan_status_summary, index=False)
    metadata = build_current_candidates_backfill_plan_status_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_plan_status_report.write_text(
        render_current_candidates_backfill_plan_status_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_plan_status_metadata(
    result: CurrentCandidatesBackfillPlanStatusResult,
    paths: CurrentCandidatesBackfillPlanStatusPaths,
) -> dict[str, Any]:
    return {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_plan_id": result.latest_plan_id,
        "health_status": result.health_status,
        "selected_date_count": result.selected_date_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, or network/API call was invoked.",
    }


def render_current_candidates_backfill_plan_status_report(
    result: CurrentCandidatesBackfillPlanStatusResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Current-Candidates Backfill Plan Status",
            "",
            "No live trading, broker API, order placement, message delivery, or network/API call was invoked. This status view summarizes local plan artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table(
                {
                    "status_id": result.status_id,
                    "status": result.status,
                    "workflow_stage": result.workflow_stage,
                    "latest_plan_id": result.latest_plan_id,
                    "health_status": result.health_status,
                    "selected_date_count": result.selected_date_count,
                    "legacy_plan_count": _summary_value(result.summary_frame, "legacy_plan_count"),
                    "stale_plan_warning_count": _summary_value(result.summary_frame, "stale_plan_warning_count"),
                    "active_plan_issue_count": _summary_value(result.summary_frame, "active_plan_issue_count"),
                    "next_manual_action": result.next_manual_action,
                }
            ),
            "",
            "## Components",
            "",
            _markdown_table(result.status_frame, ["component", "status", "latest_artifact_id", "issue_count", "warning_count", "error_count", "next_action"]),
            "",
            "## Latest Plan Summary",
            "",
            _markdown_table(result.summary_frame, SUMMARY_COLUMNS),
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
    if "created_at" not in frame.columns:
        frame["created_at"] = ""
    frame["_sort_created_at"] = frame["created_at"].astype(str)
    frame["_sort_plan_id"] = frame.get("plan_id", "").astype(str)
    return frame.sort_values(["_sort_created_at", "_sort_plan_id"]).iloc[-1].to_dict()


def _latest_active_plan_row(index_frame: pd.DataFrame, health_summary: dict[str, Any]) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    if "warmup_aware" not in frame.columns:
        frame["warmup_aware"] = ""
    warmup_frame = frame.loc[frame["warmup_aware"].map(_to_bool)]
    if not warmup_frame.empty:
        latest_plan_id = _string_or_empty(health_summary.get("latest_plan_id"))
        if latest_plan_id:
            matched = warmup_frame.loc[warmup_frame["plan_id"].astype(str) == latest_plan_id]
            if not matched.empty:
                return matched.iloc[-1].to_dict()
        return _latest_plan_row(warmup_frame)
    return _latest_plan_row(frame)


def _health_summary(health_result) -> dict[str, Any]:
    summary_frame = getattr(health_result, "summary_frame", pd.DataFrame())
    if summary_frame is None or summary_frame.empty:
        return {}
    return summary_frame.iloc[0].to_dict()


def _summary_value(summary_frame: pd.DataFrame, column: str) -> Any:
    if summary_frame.empty or column not in summary_frame.columns:
        return ""
    return summary_frame.iloc[0].get(column, "")


def _status_warnings(index_frame: pd.DataFrame, health_result) -> list[str]:
    warnings: list[str] = []
    health_summary = _health_summary(health_result)
    active_health_status = _string_or_empty(health_summary.get("active_plan_health_status")) or health_result.status
    if index_frame.empty:
        warnings.append("No current-candidates backfill plan artifacts were found.")
    if active_health_status == "WARN":
        warnings.append("Active current-candidates backfill plan health warnings are present.")
    if active_health_status == "FAIL":
        warnings.append("Active current-candidates backfill plan health failures are present.")
    return warnings


def _health_next_action(status: str) -> str:
    if status == "PASS":
        return "Health passed; review plan manually before candidate generation."
    if status == "WARN":
        return "Review backfill plan health warnings before execution."
    if status == "FAIL":
        return "Repair backfill plan artifacts before execution."
    return "Run current-candidates-backfill-plan-index and current-candidates-backfill-plan-health."


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


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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
