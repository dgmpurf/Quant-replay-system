"""Status view for universe profile split-worklist plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.universe_profile_split_worklist_plan_health import check_universe_profile_split_worklist_plan_health
from quant_replay_system.universe_profile_split_worklist_plan_index import scan_universe_profile_split_worklist_plan_artifacts


STATUS_COLUMNS = [
    "component",
    "status",
    "latest_artifact_id",
    "report_path",
    "metadata_path",
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "legacy_mixed_demo_row_count",
    "recommended_stock_core_count",
    "recommended_etf_core_count",
    "recommended_mixed_demo_core_count",
    "profile_conflict_count",
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
    "row_count",
    "stock_row_count",
    "etf_row_count",
    "legacy_mixed_demo_row_count",
    "recommended_stock_core_count",
    "recommended_etf_core_count",
    "recommended_mixed_demo_core_count",
    "profile_conflict_count",
    "report_path",
    "next_manual_action",
    "issue_count",
    "warning_count",
    "error_count",
]

NO_PLANS_STAGE = "NO_UNIVERSE_PROFILE_SPLIT_WORKLIST_PLANS"
READY_STAGE = "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_READY"
CONFLICTS_STAGE = "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS"
HEALTH_WARN_STAGE = "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HEALTH_WARN"
FAILED_STAGE = "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_FAILED"


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanStatusPaths:
    artifact_dir: Path
    universe_profile_split_worklist_plan_status_report: Path
    universe_profile_split_worklist_plan_status_csv: Path
    universe_profile_split_worklist_plan_status_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "universe_profile_split_worklist_plan_status_report": self.universe_profile_split_worklist_plan_status_report,
            "universe_profile_split_worklist_plan_status_csv": self.universe_profile_split_worklist_plan_status_csv,
            "universe_profile_split_worklist_plan_status_summary": self.universe_profile_split_worklist_plan_status_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanStatusResult:
    status_id: str
    status: str
    workflow_stage: str
    latest_plan_id: str
    health_status: str
    row_count: int
    stock_row_count: int
    etf_row_count: int
    legacy_mixed_demo_row_count: int
    recommended_stock_core_count: int
    recommended_etf_core_count: int
    recommended_mixed_demo_core_count: int
    profile_conflict_count: int
    next_manual_action: str
    status_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def run_universe_profile_split_worklist_plan_status(
    *,
    root: str | Path = "outputs/reports/universe_profile_split_worklist_plan",
    output_dir: str | Path = "outputs/reports/universe_profile_split_worklist_plan/status",
) -> UniverseProfileSplitWorklistPlanStatusResult:
    index_frame = scan_universe_profile_split_worklist_plan_artifacts(root)
    health = check_universe_profile_split_worklist_plan_health(index_df=index_frame, output_dir=Path(output_dir) / "_health_probe")
    status_frame = build_universe_profile_split_worklist_plan_status_frame(index_frame, health_result=health)
    summary_frame = summarize_universe_profile_split_worklist_plan_status(index_frame, health_result=health)
    summary = summary_frame.iloc[0].to_dict()
    status_id = _hash_payload({"rows": index_frame.to_dict("records"), "health": health.status}, 12)
    paths = resolve_universe_profile_split_worklist_plan_status_paths(output_dir, status_id)
    result = UniverseProfileSplitWorklistPlanStatusResult(
        status_id=status_id,
        status=_text(summary.get("status")) or "WARN",
        workflow_stage=_text(summary.get("workflow_stage")) or NO_PLANS_STAGE,
        latest_plan_id=_text(summary.get("latest_plan_id")),
        health_status=_text(summary.get("health_status")),
        row_count=_to_int(summary.get("row_count")),
        stock_row_count=_to_int(summary.get("stock_row_count")),
        etf_row_count=_to_int(summary.get("etf_row_count")),
        legacy_mixed_demo_row_count=_to_int(summary.get("legacy_mixed_demo_row_count")),
        recommended_stock_core_count=_to_int(summary.get("recommended_stock_core_count")),
        recommended_etf_core_count=_to_int(summary.get("recommended_etf_core_count")),
        recommended_mixed_demo_core_count=_to_int(summary.get("recommended_mixed_demo_core_count")),
        profile_conflict_count=_to_int(summary.get("profile_conflict_count")),
        next_manual_action=_text(summary.get("next_manual_action")),
        status_frame=status_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=_status_warnings(index_frame, health, summary),
        audit_metadata={
            "root_dir": str(root),
            "status_id": status_id,
            "workflow_stage": _text(summary.get("workflow_stage")) or NO_PLANS_STAGE,
            "active_worklist_mutated": False,
            "no_approval_applied": True,
            "no_rejection_applied": True,
            "no_universe_export": True,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "broker_api_invoked": False,
            "message_sent": False,
            "universe_profile_split_worklist_plan_artifacts_only": True,
        },
    )
    write_universe_profile_split_worklist_plan_status_artifacts(result)
    return result


def build_universe_profile_split_worklist_plan_status_frame(index_frame: pd.DataFrame, *, health_result: Any) -> pd.DataFrame:
    latest = _latest_plan_row(index_frame)
    rows: list[dict[str, Any]] = []
    if latest is None:
        rows.append(_status_row(component="UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN", status="MISSING", next_action="Run universe-profile-split-worklist-plan."))
    else:
        rows.append(
            _status_row(
                component="UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN",
                status=_plan_component_status(latest),
                latest_artifact_id=_text(latest.get("plan_id")),
                report_path=_text(latest.get("report_path")),
                metadata_path=_text(latest.get("metadata_path")),
                row_count=_to_int(latest.get("row_count")),
                stock_row_count=_to_int(latest.get("stock_row_count")),
                etf_row_count=_to_int(latest.get("etf_row_count")),
                legacy_mixed_demo_row_count=_to_int(latest.get("legacy_mixed_demo_row_count")),
                recommended_stock_core_count=_to_int(latest.get("recommended_stock_core_count")),
                recommended_etf_core_count=_to_int(latest.get("recommended_etf_core_count")),
                recommended_mixed_demo_core_count=_to_int(latest.get("recommended_mixed_demo_core_count")),
                profile_conflict_count=_to_int(latest.get("profile_conflict_count")),
                next_action=_plan_next_action(latest),
                notes="Latest universe profile split-worklist plan artifact.",
            )
        )
    rows.append(
        _status_row(
            component="UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HEALTH",
            status=health_result.status if len(index_frame) else "MISSING",
            latest_artifact_id=getattr(health_result, "health_check_id", ""),
            report_path=str(health_result.artifact_paths.get("universe_profile_split_worklist_plan_health_report", "")),
            metadata_path=str(health_result.artifact_paths.get("metadata", "")),
            issue_count=getattr(health_result, "issue_count", 0),
            warning_count=getattr(health_result, "warning_count", 0),
            error_count=getattr(health_result, "error_count", 0),
            next_action="No split-worklist plan health issues detected." if health_result.status == "PASS" else "Review split-worklist plan health issues.",
            notes="In-memory health evaluation for universe profile split-worklist plan artifacts.",
        )
    )
    return _finalize_status_frame(pd.DataFrame(rows))


def summarize_universe_profile_split_worklist_plan_status(index_frame: pd.DataFrame, *, health_result: Any) -> pd.DataFrame:
    latest = _latest_plan_row(index_frame)
    if latest is None:
        return pd.DataFrame([_summary_row(status="WARN", workflow_stage=NO_PLANS_STAGE, health_status="MISSING", next_manual_action="Run universe-profile-split-worklist-plan after universe-profile-policy-audit.")])
    profile_conflict_count = _to_int(latest.get("profile_conflict_count"))
    if health_result.status == "FAIL":
        status = "FAIL"
        stage = FAILED_STAGE
        next_action = "Repair split-worklist plan artifacts before using profile guidance."
    elif profile_conflict_count > 0:
        status = "WARN"
        stage = CONFLICTS_STAGE
        next_action = "Review profile conflicts; keep legacy etf_core as mixed/demo context and do not mutate active worklists."
    elif health_result.status == "WARN":
        status = "WARN"
        stage = HEALTH_WARN_STAGE
        next_action = "Review split-worklist plan health warnings."
    else:
        status = "PASS"
        stage = READY_STAGE
        next_action = "Split-worklist plan is ready as future profile guidance only."
    return pd.DataFrame(
        [
            _summary_row(
                latest_plan_id=_text(latest.get("plan_id")),
                status=status,
                workflow_stage=stage,
                health_status=health_result.status,
                row_count=_to_int(latest.get("row_count")),
                stock_row_count=_to_int(latest.get("stock_row_count")),
                etf_row_count=_to_int(latest.get("etf_row_count")),
                legacy_mixed_demo_row_count=_to_int(latest.get("legacy_mixed_demo_row_count")),
                recommended_stock_core_count=_to_int(latest.get("recommended_stock_core_count")),
                recommended_etf_core_count=_to_int(latest.get("recommended_etf_core_count")),
                recommended_mixed_demo_core_count=_to_int(latest.get("recommended_mixed_demo_core_count")),
                profile_conflict_count=profile_conflict_count,
                report_path=_text(latest.get("report_path")),
                next_manual_action=next_action,
                issue_count=getattr(health_result, "issue_count", 0),
                warning_count=getattr(health_result, "warning_count", 0),
                error_count=getattr(health_result, "error_count", 0),
            )
        ]
    )


def resolve_universe_profile_split_worklist_plan_status_paths(output_dir: str | Path, status_id: str) -> UniverseProfileSplitWorklistPlanStatusPaths:
    artifact_dir = Path(output_dir) / status_id
    return UniverseProfileSplitWorklistPlanStatusPaths(
        artifact_dir=artifact_dir,
        universe_profile_split_worklist_plan_status_report=artifact_dir / "universe_profile_split_worklist_plan_status_report.md",
        universe_profile_split_worklist_plan_status_csv=artifact_dir / "universe_profile_split_worklist_plan_status.csv",
        universe_profile_split_worklist_plan_status_summary=artifact_dir / "universe_profile_split_worklist_plan_status_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_universe_profile_split_worklist_plan_status_artifacts(result: UniverseProfileSplitWorklistPlanStatusResult) -> dict[str, Path]:
    paths = UniverseProfileSplitWorklistPlanStatusPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.status_frame.to_csv(paths.universe_profile_split_worklist_plan_status_csv, index=False)
    result.summary_frame.to_csv(paths.universe_profile_split_worklist_plan_status_summary, index=False)
    metadata = {
        "status_id": result.status_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "latest_plan_id": result.latest_plan_id,
        "health_status": result.health_status,
        "row_count": result.row_count,
        "stock_row_count": result.stock_row_count,
        "etf_row_count": result.etf_row_count,
        "legacy_mixed_demo_row_count": result.legacy_mixed_demo_row_count,
        "recommended_stock_core_count": result.recommended_stock_core_count,
        "recommended_etf_core_count": result.recommended_etf_core_count,
        "recommended_mixed_demo_core_count": result.recommended_mixed_demo_core_count,
        "profile_conflict_count": result.profile_conflict_count,
        "next_manual_action": result.next_manual_action,
        "summary": result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No approval, rejection, active worklist mutation, universe export, data/raw write, "
            "data/processed write, current-candidates generation, snapshot build, forward labels, "
            "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
            "or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.universe_profile_split_worklist_plan_status_report.write_text(render_universe_profile_split_worklist_plan_status_report(result), encoding="utf-8")
    return paths.as_dict()


def render_universe_profile_split_worklist_plan_status_report(result: UniverseProfileSplitWorklistPlanStatusResult) -> str:
    return "\n".join(
        [
            "# Universe Profile Split-Worklist Plan Status",
            "",
            "No approval, rejection, active worklist mutation, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
            "",
            result.summary_frame.to_markdown(index=False),
            "",
            result.status_frame.to_markdown(index=False),
            "",
            "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "- None",
        ]
    )


def _latest_plan_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = index_frame.copy()
    for column in ["created_at", "plan_id"]:
        if column not in frame:
            frame[column] = ""
    return frame.sort_values(["created_at", "plan_id"]).iloc[-1].to_dict()


def _plan_component_status(row: dict[str, Any]) -> str:
    if _to_int(row.get("profile_conflict_count")):
        return "WARN"
    return _text(row.get("status")) or "PASS"


def _plan_next_action(row: dict[str, Any]) -> str:
    if _to_int(row.get("profile_conflict_count")):
        return "Review profile conflicts before generating future split worklists; do not mutate active worklists."
    return "Use split guidance for future worklist planning only."


def _status_warnings(index_frame: pd.DataFrame, health: Any, summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if index_frame.empty:
        warnings.append("No universe profile split-worklist plan artifacts found.")
    if health.status != "PASS":
        warnings.append(f"Universe profile split-worklist plan health is {health.status}.")
    if _to_int(summary.get("profile_conflict_count")):
        warnings.append("Profile conflicts are present as planning context; do not treat as approval/rejection.")
    return warnings


def _status_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in STATUS_COLUMNS}
    row.update(values)
    return row


def _summary_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in SUMMARY_COLUMNS}
    row.update(values)
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
        if _text(value) == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
