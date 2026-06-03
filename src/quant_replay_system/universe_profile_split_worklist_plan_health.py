"""Health checks for universe profile split-worklist plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.universe_profile_split_worklist_plan import PLAN_COLUMNS, REGISTRY_SNAPSHOT_COLUMNS, SUMMARY_COLUMNS
from quant_replay_system.universe_profile_split_worklist_plan_index import (
    UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS,
    scan_universe_profile_split_worklist_plan_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "plan_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanHealthPaths:
    artifact_dir: Path
    universe_profile_split_worklist_plan_health_report: Path
    universe_profile_split_worklist_plan_health_issues: Path
    universe_profile_split_worklist_plan_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "universe_profile_split_worklist_plan_health_report": self.universe_profile_split_worklist_plan_health_report,
            "universe_profile_split_worklist_plan_health_issues": self.universe_profile_split_worklist_plan_health_issues,
            "universe_profile_split_worklist_plan_health_summary": self.universe_profile_split_worklist_plan_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UniverseProfileSplitWorklistPlanHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_universe_profile_split_worklist_plan_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/universe_profile_split_worklist_plan",
    output_dir: str | Path = "outputs/reports/universe_profile_split_worklist_plan/health",
) -> UniverseProfileSplitWorklistPlanHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_universe_profile_split_worklist_plan_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_universe_profile_split_worklist_plan_health(health_frame, checked_artifact_count=len(index_frame))
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, 12)
    paths = resolve_universe_profile_split_worklist_plan_health_paths(output_dir, health_check_id)
    result = UniverseProfileSplitWorklistPlanHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        health_check_id=health_check_id,
        audit_metadata={
            "index_source": index_source,
            "checked_artifact_count": len(index_frame),
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
    write_universe_profile_split_worklist_plan_health_artifacts(result)
    return result


def build_universe_profile_split_worklist_plan_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_text(row.get("metadata_path"))), issues)
        plan = _check_csv(row, Path(_text(row.get("plan_csv_path"))), issues, PLAN_COLUMNS, "plan CSV")
        _check_csv(row, Path(_text(row.get("summary_csv_path"))), issues, SUMMARY_COLUMNS, "summary CSV")
        _check_registry_snapshot(row, Path(_text(row.get("registry_snapshot_path"))), issues)
        _check_report(row, Path(_text(row.get("report_path"))), issues)
        if metadata is not None and plan is not None:
            _check_safety_contract(row, metadata, plan, issues)
            _check_profile_context(row, metadata, plan, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_universe_profile_split_worklist_plan_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    return pd.DataFrame(
        [
            {
                "status": status,
                "checked_artifact_count": checked_artifact_count,
                "issue_count": len(frame),
                "error_count": error_count,
                "warning_count": warning_count,
            }
        ]
    )


def resolve_universe_profile_split_worklist_plan_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> UniverseProfileSplitWorklistPlanHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return UniverseProfileSplitWorklistPlanHealthPaths(
        artifact_dir=artifact_dir,
        universe_profile_split_worklist_plan_health_report=artifact_dir / "universe_profile_split_worklist_plan_health_report.md",
        universe_profile_split_worklist_plan_health_issues=artifact_dir / "universe_profile_split_worklist_plan_health_issues.csv",
        universe_profile_split_worklist_plan_health_summary=artifact_dir / "universe_profile_split_worklist_plan_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_universe_profile_split_worklist_plan_health_artifacts(
    result: UniverseProfileSplitWorklistPlanHealthResult,
) -> dict[str, Path]:
    paths = UniverseProfileSplitWorklistPlanHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.universe_profile_split_worklist_plan_health_issues, index=False)
    result.summary_frame.to_csv(paths.universe_profile_split_worklist_plan_health_summary, index=False)
    metadata = {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No approval, rejection, active worklist mutation, universe export, data/raw write, "
            "data/processed write, current-candidates generation, snapshot build, forward labels, "
            "live trading, broker API, order placement, message delivery, network/API, LLM/API, "
            "or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.universe_profile_split_worklist_plan_health_report.write_text(
        render_universe_profile_split_worklist_plan_health_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_universe_profile_split_worklist_plan_health_report(
    result: UniverseProfileSplitWorklistPlanHealthResult,
) -> str:
    return "\n".join(
        [
            "# Universe Profile Split-Worklist Plan Health",
            "",
            "No approval, rejection, active worklist mutation, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
            "",
            f"- status: {result.status}",
            f"- checked_artifact_count: {result.checked_artifact_count}",
            f"- issue_count: {result.issue_count}",
            f"- error_count: {result.error_count}",
            f"- warning_count: {result.warning_count}",
            "",
            result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
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
            return _prepare_index_frame(pd.DataFrame()), str(path), [
                _issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", "Index CSV not found.", "Run universe-profile-split-worklist-plan-index.")
            ]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    return _prepare_index_frame(scan_universe_profile_split_worklist_plan_artifacts(root)), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate split-worklist plan artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate split-worklist plan artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_csv(
    row: dict[str, Any],
    path: Path,
    issues: list[dict[str, Any]],
    required_columns: list[str],
    label: str,
) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, f"{label}_path", path, "ERROR", f"MISSING_{label.upper().replace(' ', '_')}", f"{label} is missing.", "Regenerate split-worklist plan artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, f"{label}_path", path, "ERROR", f"MISSING_{label.upper().replace(' ', '_')}", f"{label} is unreadable: {exc}", "Regenerate split-worklist plan artifact."))
        return None
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        issues.append(_issue(row, f"{label}_path", path, "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns in {label}: {', '.join(missing)}", "Regenerate split-worklist plan artifact with current schema."))
    return frame


def _check_registry_snapshot(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "registry_snapshot_path", path, "ERROR", "MISSING_REGISTRY_SNAPSHOT", "registry snapshot is missing.", "Regenerate split-worklist plan artifact."))
        return
    text = path.read_text(encoding="utf-8")
    for expected in REGISTRY_SNAPSHOT_COLUMNS:
        if expected == "profile_name":
            continue
        if expected not in text:
            issues.append(_issue(row, "registry_snapshot_path", path, "WARN", "REGISTRY_SNAPSHOT_PARTIAL", f"registry snapshot does not mention {expected}.", "Review registry snapshot."))


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "split-worklist plan report is missing.", "Regenerate split-worklist plan artifact."))


def _check_safety_contract(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if _to_bool(metadata.get("active_worklist_mutated")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "ACTIVE_WORKLIST_MUTATION_DETECTED", "active_worklist_mutated=true detected.", "Split plans must not mutate active worklists."))
    if "should_mutate_active_worklist" in plan.columns and plan["should_mutate_active_worklist"].map(_to_bool).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "ACTIVE_WORKLIST_MUTATION_DETECTED", "should_mutate_active_worklist=true detected.", "Regenerate split plan as report-only."))
    true_flags = {
        "no_approval_applied": "APPROVAL_APPLIED_DETECTED",
        "no_rejection_applied": "REJECTION_APPLIED_DETECTED",
        "no_universe_export": "UNIVERSE_EXPORT_DETECTED",
        "no_data_raw_write": "DATA_RAW_WRITE_DETECTED",
        "no_data_processed_write": "DATA_PROCESSED_WRITE_DETECTED",
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
        "no_live_trading": "LIVE_TRADING_DETECTED",
        "no_broker_api": "BROKER_DETECTED",
        "no_order_placement": "ORDER_PLACEMENT_DETECTED",
        "no_message_sent": "MESSAGE_DELIVERY_DETECTED",
        "plan_only": "PLAN_ONLY_FLAG_MISSING",
    }
    for flag, code in true_flags.items():
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{flag}=true is missing.", "Regenerate split-worklist plan artifact with safety metadata."))
        if flag in plan.columns and (~plan[flag].map(_to_bool)).any():
            issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", code, f"A row does not have {flag}=true.", "Regenerate split-worklist plan artifact with safety row fields."))
    if "should_approve" in plan.columns and plan["should_approve"].map(_to_bool).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "APPROVAL_APPLIED_DETECTED", "should_approve=true detected.", "Split plan must not approve rows."))
    if "should_reject" in plan.columns and plan["should_reject"].map(_to_bool).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "REJECTION_APPLIED_DETECTED", "should_reject=true detected.", "Split plan must not reject rows."))
    false_flags = {
        "current_candidates_executed": "CURRENT_CANDIDATES_GENERATED",
        "snapshot_manifest_built": "SNAPSHOT_BUILT",
        "forward_returns_computed": "FORWARD_LABELS_COMPUTED",
        "cache_mutated": "CACHE_MUTATION_DETECTED",
        "network_api_called": "NETWORK_OR_API_DETECTED",
        "external_api_called": "NETWORK_OR_API_DETECTED",
        "llm_api_called": "NETWORK_OR_API_DETECTED",
    }
    for flag, code in false_flags.items():
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{flag}=true detected.", "Regenerate split plan as report-only."))


def _check_profile_context(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    conflict_count = _to_int(metadata.get("profile_conflict_count", _true_count(plan, "profile_conflict")))
    if conflict_count > 0:
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "WARN", "PROFILE_CONFLICT_CONTEXT", "Profile conflicts are present as split-planning context.", "Review conflicts before generating future split worklists."))


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_INDEX_COLUMNS].reset_index(drop=True)


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
        "artifact_type": "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN",
        "plan_id": _text(row.get("plan_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


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
