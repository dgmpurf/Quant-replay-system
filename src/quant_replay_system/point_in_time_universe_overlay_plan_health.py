"""Health checks for point-in-time universe overlay plan artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_overlay_plan import OVERLAY_PLAN_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_plan_index import (
    PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS,
    scan_point_in_time_universe_overlay_plan_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "overlay_plan_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local point-in-time universe overlay plan artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanHealthPaths:
    artifact_dir: Path
    point_in_time_universe_overlay_plan_health_report: Path
    point_in_time_universe_overlay_plan_health_issues: Path
    point_in_time_universe_overlay_plan_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "point_in_time_universe_overlay_plan_health_report": self.point_in_time_universe_overlay_plan_health_report,
            "point_in_time_universe_overlay_plan_health_issues": self.point_in_time_universe_overlay_plan_health_issues,
            "point_in_time_universe_overlay_plan_health_summary": self.point_in_time_universe_overlay_plan_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanHealthResult:
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


def check_point_in_time_universe_overlay_plan_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/point_in_time_universe_overlay_plan",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_overlay_plan/health",
) -> PointInTimeUniverseOverlayPlanHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_point_in_time_universe_overlay_plan_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_point_in_time_universe_overlay_plan_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_point_in_time_universe_overlay_plan_health_paths(output_dir, health_check_id)
    result = PointInTimeUniverseOverlayPlanHealthResult(
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
    write_point_in_time_universe_overlay_plan_health_artifacts(result)
    return result


def build_point_in_time_universe_overlay_plan_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_string_or_empty(row.get("metadata_path"))), issues)
        plan = _check_csv(
            row,
            Path(_string_or_empty(row.get("plan_csv_path"))),
            issues,
            path_field="plan_csv_path",
            missing_code="MISSING_PLAN_CSV",
        )
        template = _check_csv(
            row,
            Path(_string_or_empty(row.get("template_csv_path"))),
            issues,
            path_field="template_csv_path",
            missing_code="MISSING_TEMPLATE_CSV",
        )
        _check_report(row, Path(_string_or_empty(row.get("report_path"))), issues)
        if metadata is not None and plan is not None:
            _check_plan_contract(row, metadata, plan, issues)
        if template is not None:
            _check_required_columns(row, template, issues, path_field="template_csv_path")
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_point_in_time_universe_overlay_plan_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
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
                }
            )
    return pd.DataFrame(rows)


def resolve_point_in_time_universe_overlay_plan_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PointInTimeUniverseOverlayPlanHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return PointInTimeUniverseOverlayPlanHealthPaths(
        artifact_dir=artifact_dir,
        point_in_time_universe_overlay_plan_health_report=artifact_dir / "point_in_time_universe_overlay_plan_health_report.md",
        point_in_time_universe_overlay_plan_health_issues=artifact_dir / "point_in_time_universe_overlay_plan_health_issues.csv",
        point_in_time_universe_overlay_plan_health_summary=artifact_dir / "point_in_time_universe_overlay_plan_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_point_in_time_universe_overlay_plan_health_artifacts(
    result: PointInTimeUniverseOverlayPlanHealthResult,
) -> dict[str, Path]:
    paths = PointInTimeUniverseOverlayPlanHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.point_in_time_universe_overlay_plan_health_issues, index=False)
    result.summary_frame.to_csv(paths.point_in_time_universe_overlay_plan_health_summary, index=False)
    metadata = build_point_in_time_universe_overlay_plan_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.point_in_time_universe_overlay_plan_health_report.write_text(
        render_point_in_time_universe_overlay_plan_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_point_in_time_universe_overlay_plan_health_metadata(
    result: PointInTimeUniverseOverlayPlanHealthResult,
    paths: PointInTimeUniverseOverlayPlanHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
            "order placement, message delivery, LLM API, or external API was invoked."
        ),
    }


def render_point_in_time_universe_overlay_plan_health_report(
    result: PointInTimeUniverseOverlayPlanHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Point-in-Time Universe Overlay Plan Health",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This health check reads local PIT universe overlay plan artifacts only.",
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
                }
            ),
            "",
            "## Issues",
            "",
            _markdown_table(
                result.health_frame,
                ["overlay_plan_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
            ),
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
            issue = _issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", f"Index CSV not found: {path}", "Run pit-universe-overlay-plan-index.")
            return _prepare_index_frame(pd.DataFrame()), str(path), [issue]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    frame = scan_point_in_time_universe_overlay_plan_artifacts(root)
    return _prepare_index_frame(frame), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate the PIT universe overlay plan artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate the PIT universe overlay plan artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_csv(
    row: dict[str, Any],
    path: Path,
    issues: list[dict[str, Any]],
    *,
    path_field: str,
    missing_code: str,
) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, path_field, path, "ERROR", missing_code, f"{path_field} is missing.", "Regenerate the PIT universe overlay plan artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, path_field, path, "ERROR", missing_code, f"{path_field} is unreadable: {exc}", "Regenerate the PIT universe overlay plan artifact."))
        return None
    _check_required_columns(row, frame, issues, path_field=path_field)
    return frame


def _check_required_columns(row: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]], *, path_field: str) -> None:
    missing = [column for column in OVERLAY_PLAN_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(_issue(row, path_field, row.get(path_field), "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns: {', '.join(missing)}", "Regenerate the PIT universe overlay plan artifact with the current schema."))


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "PIT universe overlay plan report is missing.", "Regenerate the PIT universe overlay plan artifact."))


def _check_plan_contract(row: dict[str, Any], metadata: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    _check_safety_flags(row, metadata, plan, issues)
    _check_plan_only(row, metadata, issues)
    _check_manual_review(row, plan, issues)
    _check_auto_approval(row, plan, issues)
    _check_survivorship_warnings(row, plan, issues)


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
    if _to_bool(metadata.get("order_placement_enabled")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "ORDER_PLACEMENT_DETECTED", "order_placement_enabled=true detected.", "Regenerate local-only plan artifacts."))
    if _to_bool(metadata.get("message_delivery_enabled")) or _to_bool(metadata.get("message_sent")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MESSAGE_DELIVERY_DETECTED", "Message delivery metadata detected.", "Regenerate local-only plan artifacts."))


def _check_plan_only(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if not _to_bool(metadata.get("plan_only", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "PLAN_ONLY_FLAG_MISSING", "plan_only=true is missing from metadata.", "Regenerate as a plan/template-only artifact."))
    executed_flags = [
        "current_candidates_executed",
        "data_pipeline_executed",
        "snapshot_manifest_built",
        "snapshot_manifests_built",
        "forward_returns_computed",
        "cache_mutated",
        "network_api_called",
        "external_api_called",
        "llm_api_called",
    ]
    for flag in executed_flags:
        if _to_bool(metadata.get(flag)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "CANDIDATE_GENERATION_DETECTED", f"{flag}=true detected.", "Regenerate as a plan/template-only artifact."))


def _check_manual_review(row: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "review_status" not in plan.columns or plan["review_status"].map(_string_or_empty).eq("").any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "REVIEW_STATUS_MISSING", "review_status is missing on at least one row.", "Regenerate the template with review_status."))
    if "manual_review_required" not in plan.columns or (~plan["manual_review_required"].map(_to_bool)).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "MANUAL_REVIEW_REQUIRED_MISSING", "manual_review_required=true is missing on at least one row.", "Regenerate the template with manual review flags."))


def _check_auto_approval(row: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if plan.empty or "include_flag" not in plan.columns:
        return
    include_true = plan["include_flag"].map(_to_bool)
    reviewed = plan.get("review_status", pd.Series([""] * len(plan))).map(_string_or_empty).str.upper().eq("REVIEWED_PIT_VALID")
    valid = plan.get("valid_for_signal_date", pd.Series([False] * len(plan))).map(_to_bool)
    if (include_true & ~(reviewed & valid)).any():
        issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "AUTO_APPROVAL_DETECTED", "include_flag=true appears before reviewed PIT-valid approval.", "Clear include_flag or complete an explicit reviewed approval workflow."))


def _check_survivorship_warnings(row: dict[str, Any], plan: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    required = {"signal_date", "base_universe_as_of_date", "base_universe_available_time", "survivorship_bias_warning"}
    if not required.issubset(plan.columns):
        return
    for _, plan_row in plan.iterrows():
        if _future_derived(plan_row) and not _to_bool(plan_row.get("survivorship_bias_warning")):
            issues.append(_issue(row, "plan_csv_path", row.get("plan_csv_path"), "ERROR", "MISSING_SURVIVORSHIP_WARNING", "A row derived from a future universe is missing survivorship_bias_warning=true.", "Regenerate the template or restore the warning before review."))
            return


def _future_derived(plan_row: pd.Series) -> bool:
    signal = pd.to_datetime(plan_row.get("signal_date"), errors="coerce")
    as_of = pd.to_datetime(plan_row.get("base_universe_as_of_date"), errors="coerce")
    available = pd.to_datetime(plan_row.get("base_universe_available_time"), errors="coerce")
    if pd.isna(signal) or pd.isna(as_of) or pd.isna(available):
        return True
    decision = signal.normalize() + pd.Timedelta(hours=15, minutes=30)
    return bool(as_of.normalize() > signal.normalize() or available > decision)


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[PIT_UNIVERSE_OVERLAY_PLAN_INDEX_COLUMNS].reset_index(drop=True)


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
        "artifact_type": "PIT_UNIVERSE_OVERLAY_PLAN",
        "overlay_plan_id": _string_or_empty(row.get("overlay_plan_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


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
