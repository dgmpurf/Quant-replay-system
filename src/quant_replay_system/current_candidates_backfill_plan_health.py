"""Local-only health checks for current-candidates backfill plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.current_candidates_backfill_plan import PLAN_COLUMNS
from quant_replay_system.current_candidates_backfill_plan_index import (
    BACKFILL_PLAN_INDEX_COLUMNS,
    scan_current_candidates_backfill_plan_artifacts,
)
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


LEGACY_WARMUP_COLUMNS = {
    "warmup_trading_days",
    "warmup_available",
    "earliest_required_warmup_date",
    "first_available_market_date",
    "warmup_start_date",
    "warmup_reason",
    "candidate_generation_feasible",
    "candidate_generation_blocker",
}

HEALTH_COLUMNS = [
    "artifact_type",
    "plan_id",
    "issue_scope",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local current-candidates backfill plan artifacts only.",
    "Does not run current-candidates, build snapshot manifests, or compute forward-return labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanHealthPaths:
    artifact_dir: Path
    current_candidates_backfill_plan_health_report: Path
    current_candidates_backfill_plan_health_issues: Path
    current_candidates_backfill_plan_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_plan_health_report": self.current_candidates_backfill_plan_health_report,
            "current_candidates_backfill_plan_health_issues": self.current_candidates_backfill_plan_health_issues,
            "current_candidates_backfill_plan_health_summary": self.current_candidates_backfill_plan_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillPlanHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_current_candidates_backfill_plan_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/current_candidates_backfill_plan",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_plan/health",
) -> CurrentCandidatesBackfillPlanHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_current_candidates_backfill_plan_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    health_frame = _annotate_issue_scope(health_frame, index_frame)
    summary_frame = summarize_current_candidates_backfill_plan_health(
        health_frame,
        checked_artifact_count=len(index_frame),
        index_frame=index_frame,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_current_candidates_backfill_plan_health_paths(output_dir, health_check_id)
    result = CurrentCandidatesBackfillPlanHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=[],
        known_limitations=HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata={
            "index_source": index_source,
            "checked_artifact_count": len(index_frame),
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
    write_current_candidates_backfill_plan_health_artifacts(result)
    return result


def build_current_candidates_backfill_plan_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_string_or_empty(row.get("metadata_path"))), issues)
        plan = _check_plan_csv(row, Path(_string_or_empty(row.get("plan_csv_path"))), issues)
        _check_report(row, Path(_string_or_empty(row.get("report_path"))), issues)
        if metadata is not None and plan is not None:
            _check_plan_contract(row, metadata, plan, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_current_candidates_backfill_plan_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
    index_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    index = _prepare_index_frame(index_frame if index_frame is not None else pd.DataFrame())
    active_plan = _latest_warmup_aware_plan_row(index) or _latest_plan_row(index)
    active_plan_id = _string_or_empty(active_plan.get("plan_id")) if active_plan else ""
    latest_plan_is_warmup_aware = _to_bool(active_plan.get("warmup_aware")) if active_plan else False
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    active_frame = frame.loc[frame["plan_id"].astype(str) == active_plan_id] if active_plan_id and not frame.empty else frame.iloc[0:0]
    legacy_frame = frame.loc[frame["issue_scope"].astype(str) == "LEGACY_PLAN"] if not frame.empty else frame.iloc[0:0]
    active_plan_issue_count = len(active_frame)
    active_plan_error_count = int((active_frame["severity"] == "ERROR").sum()) if not active_frame.empty else 0
    active_plan_warning_count = int((active_frame["severity"] == "WARN").sum()) if not active_frame.empty else 0
    active_plan_health_status = (
        "FAIL" if active_plan_error_count else "WARN" if active_plan_warning_count else "PASS"
    )
    legacy_plan_count = int((~index["warmup_aware"].map(_to_bool)).sum()) if not index.empty else 0
    stale_plan_warning_count = int((legacy_frame["severity"] == "WARN").sum()) if not legacy_frame.empty else 0
    legacy_missing_warmup_count = int(
        ((legacy_frame["issue_code"] == "STALE_OR_PARTIAL_PLAN") & (legacy_frame["severity"] == "WARN")).sum()
    ) if not legacy_frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    common = {
        "latest_plan_id": active_plan_id,
        "latest_plan_is_warmup_aware": latest_plan_is_warmup_aware,
        "active_plan_health_status": active_plan_health_status,
        "active_plan_issue_count": active_plan_issue_count,
        "active_plan_error_count": active_plan_error_count,
        "active_plan_warning_count": active_plan_warning_count,
        "legacy_plan_count": legacy_plan_count,
        "stale_plan_warning_count": stale_plan_warning_count,
        "legacy_missing_warmup_count": legacy_missing_warmup_count,
    }
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
            **common,
        }
    ]
    if not frame.empty:
        for issue_code, group in frame.groupby("issue_code", dropna=False):
            rows.append(
                {
                    "status": status,
                    "checked_artifact_count": checked_artifact_count,
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "issue_code": issue_code,
                    **common,
                }
            )
    summary = pd.DataFrame(rows)
    if "latest_plan_is_warmup_aware" in summary.columns:
        summary["latest_plan_is_warmup_aware"] = summary["latest_plan_is_warmup_aware"].map(_to_bool).astype(object)
    return summary


def resolve_current_candidates_backfill_plan_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> CurrentCandidatesBackfillPlanHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return CurrentCandidatesBackfillPlanHealthPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_plan_health_report=artifact_dir / "current_candidates_backfill_plan_health_report.md",
        current_candidates_backfill_plan_health_issues=artifact_dir / "current_candidates_backfill_plan_health_issues.csv",
        current_candidates_backfill_plan_health_summary=artifact_dir / "current_candidates_backfill_plan_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_plan_health_artifacts(result: CurrentCandidatesBackfillPlanHealthResult) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillPlanHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.current_candidates_backfill_plan_health_issues, index=False)
    result.summary_frame.to_csv(paths.current_candidates_backfill_plan_health_summary, index=False)
    metadata = build_current_candidates_backfill_plan_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_plan_health_report.write_text(
        render_current_candidates_backfill_plan_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_plan_health_metadata(
    result: CurrentCandidatesBackfillPlanHealthResult,
    paths: CurrentCandidatesBackfillPlanHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "latest_plan_id": _summary_value(result.summary_frame, "latest_plan_id"),
        "latest_plan_is_warmup_aware": _summary_value(result.summary_frame, "latest_plan_is_warmup_aware"),
        "active_plan_health_status": _summary_value(result.summary_frame, "active_plan_health_status"),
        "active_plan_issue_count": _summary_value(result.summary_frame, "active_plan_issue_count"),
        "active_plan_error_count": _summary_value(result.summary_frame, "active_plan_error_count"),
        "active_plan_warning_count": _summary_value(result.summary_frame, "active_plan_warning_count"),
        "legacy_plan_count": _summary_value(result.summary_frame, "legacy_plan_count"),
        "stale_plan_warning_count": _summary_value(result.summary_frame, "stale_plan_warning_count"),
        "legacy_missing_warmup_count": _summary_value(result.summary_frame, "legacy_missing_warmup_count"),
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, or network/API call was invoked.",
    }


def render_current_candidates_backfill_plan_health_report(
    result: CurrentCandidatesBackfillPlanHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Current-Candidates Backfill Plan Health",
            "",
            "No live trading, broker API, order placement, message delivery, or network/API call was invoked. This health check reads local plan artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table(
                {
                    "health_check_id": result.health_check_id,
                    "status": result.status,
                    "checked_artifact_count": result.checked_artifact_count,
                    "issue_count": result.issue_count,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "latest_plan_id": _summary_value(result.summary_frame, "latest_plan_id"),
                    "active_plan_health_status": _summary_value(result.summary_frame, "active_plan_health_status"),
                    "active_plan_issue_count": _summary_value(result.summary_frame, "active_plan_issue_count"),
                    "active_plan_error_count": _summary_value(result.summary_frame, "active_plan_error_count"),
                    "legacy_plan_count": _summary_value(result.summary_frame, "legacy_plan_count"),
                    "stale_plan_warning_count": _summary_value(result.summary_frame, "stale_plan_warning_count"),
                    "legacy_missing_warmup_count": _summary_value(result.summary_frame, "legacy_missing_warmup_count"),
                }
            ),
            "",
            "## Issues",
            "",
            _markdown_table(result.health_frame, ["plan_id", "issue_scope", "severity", "issue_code", "path_field", "issue_message", "suggested_action"]),
            "",
        ]
    )


def _load_index(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path,
) -> tuple[pd.DataFrame, str, list[dict[str, Any]]]:
    if index_df is not None:
        return _prepare_index_frame(index_df), "in_memory", []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", f"Index CSV not found: {path}", "Run current-candidates-backfill-plan-index.")
            return _prepare_index_frame(pd.DataFrame()), str(path), [issue]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    frame = scan_current_candidates_backfill_plan_artifacts(root)
    return _prepare_index_frame(frame), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate the backfill plan artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate the backfill plan artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_plan_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "plan_csv_path", path, "ERROR", "MISSING_PLAN_CSV", "current_candidates_backfill_plan.csv is missing.", "Regenerate the backfill plan artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "plan_csv_path", path, "ERROR", "MISSING_PLAN_CSV", f"Plan CSV is unreadable: {exc}", "Regenerate the backfill plan artifact."))
        return None
    missing = [column for column in PLAN_COLUMNS if column not in frame.columns]
    hard_missing = [column for column in missing if column not in LEGACY_WARMUP_COLUMNS]
    warmup_missing = [column for column in missing if column in LEGACY_WARMUP_COLUMNS]
    if hard_missing:
        issues.append(_issue(row, "plan_csv_path", path, "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns: {', '.join(hard_missing)}", "Regenerate the backfill plan artifact with the current schema."))
    if warmup_missing:
        issues.append(
            _issue(
                row,
                "plan_csv_path",
                path,
                "WARN",
                "STALE_OR_PARTIAL_PLAN",
                f"Legacy plan is missing warmup feasibility columns: {', '.join(warmup_missing)}",
                "Regenerate the backfill plan with --warmup-trading-days before using it for execution planning.",
            )
        )
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "Plan report is missing.", "Regenerate the backfill plan artifact."))


def _check_plan_contract(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    _check_warmup(row, plan, issues)
    _check_forward_horizons(row, metadata, plan, issues)
    _check_symbols(row, plan, issues)
    _check_source_policy(row, metadata, plan, issues)
    _check_plan_only(row, metadata, issues)
    _check_safety_flags(row, metadata, plan, issues)


def _check_warmup(row: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "warmup_available" in plan.columns and (~plan["warmup_available"].map(_to_bool)).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "WARMUP_INFEASIBLE_SELECTED", "A selected plan row has warmup_available=false.", "Regenerate the plan with warmup-infeasible dates excluded."))
    if "candidate_generation_feasible" in plan.columns and (~plan["candidate_generation_feasible"].map(_to_bool)).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "WARMUP_INFEASIBLE_SELECTED", "A selected plan row is not candidate-generation feasible.", "Regenerate the plan with only feasible selected dates."))


def _check_forward_horizons(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    horizons = metadata.get("horizons") if isinstance(metadata.get("horizons"), list) else [1, 3, 5, 10]
    for horizon in horizons:
        column = f"forward_{int(horizon)}d_available"
        if column in plan.columns and (~plan[column].map(_to_bool)).any():
            issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "FORWARD_HORIZON_INFEASIBLE_SELECTED", f"A selected plan row has {column}=false.", "Regenerate the plan with forward-horizon-infeasible dates excluded."))


def _check_symbols(row: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "symbols" not in plan.columns:
        return
    for symbols in plan["symbols"].dropna().astype(str):
        for raw in symbols.split(";"):
            text = raw.strip()
            if not text:
                continue
            normalized = normalize_symbol_value(text)
            if normalized != text or not (text.isdigit() and len(text) == 6):
                issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "MISSING_REQUIRED_COLUMNS", f"Symbol '{text}' is not preserved as a six-digit string.", "Regenerate plan artifacts while preserving symbol text."))
                return


def _check_source_policy(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    source_policy = _string_or_empty(metadata.get("source_policy")) or _first_value(plan, "source_policy")
    if not source_policy:
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "WARN", "SOURCE_POLICY_MISSING", "source_policy is missing.", "Regenerate the plan with reviewed source policy guidance."))


def _check_plan_only(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if "plan_only" in metadata and not _to_bool(metadata.get("plan_only")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "PLAN_ONLY_FLAG_MISSING", "plan_only=false detected.", "Regenerate as a plan-only artifact."))
    if _to_bool(metadata.get("current_candidates_executed")) or _to_bool(metadata.get("data_pipeline_executed")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "PLAN_ONLY_FLAG_MISSING", "Metadata indicates candidate generation or data-pipeline execution.", "Regenerate as a plan-only artifact."))


def _check_safety_flags(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    checks = [
        ("no_live_trading", "LIVE_TRADING_DETECTED"),
        ("no_broker_api", "BROKER_DETECTED"),
        ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
        ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
    ]
    for field, code in checks:
        if not _to_bool(metadata.get(field, False)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field}=true is missing from metadata.", "Regenerate the plan with safety metadata."))
        if field in plan.columns and (~plan[field].map(_to_bool)).any():
            issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", code, f"A row does not have {field}=true.", "Regenerate the plan with safety row fields."))
    if _to_bool(metadata.get("live_trading_enabled")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "LIVE_TRADING_DETECTED", "live_trading_enabled=true detected.", "Regenerate local-only plan artifacts."))
    if _to_bool(metadata.get("broker_api_invoked")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "BROKER_DETECTED", "broker_api_invoked=true detected.", "Regenerate local-only plan artifacts."))
    if _to_bool(metadata.get("message_delivery_enabled")) or _to_bool(metadata.get("message_sent")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MESSAGE_DELIVERY_DETECTED", "Message delivery metadata detected.", "Regenerate local-only plan artifacts."))


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=BACKFILL_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in BACKFILL_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[BACKFILL_PLAN_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy()
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _issue(row: dict[str, Any], path_field: str, path_value: Any, severity: str, issue_code: str, issue_message: str, suggested_action: str) -> dict[str, Any]:
    return {
        "artifact_type": "CURRENT_CANDIDATES_BACKFILL_PLAN",
        "plan_id": _string_or_empty(row.get("plan_id")),
        "issue_scope": "",
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _annotate_issue_scope(health_frame: pd.DataFrame, index_frame: pd.DataFrame) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    if frame.empty:
        return frame
    index = _prepare_index_frame(index_frame)
    active_plan = _latest_warmup_aware_plan_row(index) or _latest_plan_row(index)
    active_plan_id = _string_or_empty(active_plan.get("plan_id")) if active_plan else ""
    output = frame.copy()
    output["issue_scope"] = output.apply(
        lambda row: _issue_scope_for_row(row, active_plan_id),
        axis=1,
    )
    return _finalize_health_frame(output)


def _issue_scope_for_row(row: pd.Series, active_plan_id: str) -> str:
    plan_id = _string_or_empty(row.get("plan_id"))
    if not active_plan_id:
        return "ACTIVE_PLAN"
    if plan_id == active_plan_id:
        return "ACTIVE_PLAN"
    return "LEGACY_PLAN"


def _latest_warmup_aware_plan_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    frame = _prepare_index_frame(index_frame)
    if frame.empty:
        return None
    warmup_frame = frame.loc[frame["warmup_aware"].map(_to_bool)]
    return _latest_plan_row(warmup_frame)


def _latest_plan_row(index_frame: pd.DataFrame) -> dict[str, Any] | None:
    if index_frame.empty:
        return None
    frame = _prepare_index_frame(index_frame).copy()
    frame["_sort_created_at"] = frame["created_at"].astype(str)
    frame["_sort_plan_id"] = frame["plan_id"].astype(str)
    return frame.sort_values(["_sort_created_at", "_sort_plan_id"]).iloc[-1].to_dict()


def _summary_value(summary_frame: pd.DataFrame, column: str) -> Any:
    if summary_frame.empty or column not in summary_frame.columns:
        return ""
    return summary_frame.iloc[0].get(column, "")


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return _string_or_empty(frame[column].iloc[0])


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


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 200) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)
