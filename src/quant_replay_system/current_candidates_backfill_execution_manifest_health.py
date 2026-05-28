"""Health checks for current-candidates backfill execution manifest artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.current_candidates_backfill_execution_manifest import MANIFEST_COLUMNS
from quant_replay_system.current_candidates_backfill_execution_manifest_index import (
    EXECUTION_MANIFEST_INDEX_COLUMNS,
    scan_current_candidates_backfill_execution_manifest_artifacts,
)
from quant_replay_system.data import read_csv_preserve_symbol_columns


HEALTH_COLUMNS = [
    "artifact_type",
    "execution_manifest_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

HEALTH_LIMITATIONS = [
    "Checks local current-candidates backfill execution manifest artifacts only.",
    "Does not run current-candidates, build snapshot manifests, run data-pipeline, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestHealthPaths:
    artifact_dir: Path
    current_candidates_backfill_execution_manifest_health_report: Path
    current_candidates_backfill_execution_manifest_health_issues: Path
    current_candidates_backfill_execution_manifest_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidates_backfill_execution_manifest_health_report": (
                self.current_candidates_backfill_execution_manifest_health_report
            ),
            "current_candidates_backfill_execution_manifest_health_issues": (
                self.current_candidates_backfill_execution_manifest_health_issues
            ),
            "current_candidates_backfill_execution_manifest_health_summary": (
                self.current_candidates_backfill_execution_manifest_health_summary
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestHealthResult:
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


def check_current_candidates_backfill_execution_manifest_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest",
    output_dir: str | Path = "outputs/reports/current_candidates_backfill_execution_manifest/health",
) -> CurrentCandidatesBackfillExecutionManifestHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_current_candidates_backfill_execution_manifest_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_current_candidates_backfill_execution_manifest_health(
        health_frame,
        checked_artifact_count=len(index_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, length=12)
    paths = resolve_current_candidates_backfill_execution_manifest_health_paths(output_dir, health_check_id)
    result = CurrentCandidatesBackfillExecutionManifestHealthResult(
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
            "execution_manifest_artifacts_only": True,
        },
    )
    write_current_candidates_backfill_execution_manifest_health_artifacts(result)
    return result


def build_current_candidates_backfill_execution_manifest_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_string_or_empty(row.get("metadata_path"))), issues)
        manifest = _check_manifest_csv(row, Path(_string_or_empty(row.get("manifest_csv_path"))), issues)
        _check_report(row, Path(_string_or_empty(row.get("report_path"))), issues)
        if metadata is not None and manifest is not None:
            _check_manifest_contract(row, metadata, manifest, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_current_candidates_backfill_execution_manifest_health(
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


def resolve_current_candidates_backfill_execution_manifest_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> CurrentCandidatesBackfillExecutionManifestHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return CurrentCandidatesBackfillExecutionManifestHealthPaths(
        artifact_dir=artifact_dir,
        current_candidates_backfill_execution_manifest_health_report=(
            artifact_dir / "current_candidates_backfill_execution_manifest_health_report.md"
        ),
        current_candidates_backfill_execution_manifest_health_issues=(
            artifact_dir / "current_candidates_backfill_execution_manifest_health_issues.csv"
        ),
        current_candidates_backfill_execution_manifest_health_summary=(
            artifact_dir / "current_candidates_backfill_execution_manifest_health_summary.csv"
        ),
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidates_backfill_execution_manifest_health_artifacts(
    result: CurrentCandidatesBackfillExecutionManifestHealthResult,
) -> dict[str, Path]:
    paths = CurrentCandidatesBackfillExecutionManifestHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.current_candidates_backfill_execution_manifest_health_issues, index=False)
    result.summary_frame.to_csv(paths.current_candidates_backfill_execution_manifest_health_summary, index=False)
    metadata = build_current_candidates_backfill_execution_manifest_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidates_backfill_execution_manifest_health_report.write_text(
        render_current_candidates_backfill_execution_manifest_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidates_backfill_execution_manifest_health_metadata(
    result: CurrentCandidatesBackfillExecutionManifestHealthResult,
    paths: CurrentCandidatesBackfillExecutionManifestHealthPaths,
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
            "order placement, message delivery, or network/API call was invoked."
        ),
    }


def render_current_candidates_backfill_execution_manifest_health_report(
    result: CurrentCandidatesBackfillExecutionManifestHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "# Current-Candidates Backfill Execution Manifest Health",
            "",
            "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked. This health check reads local execution manifest artifacts only.",
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
                ["execution_manifest_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
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
            issue = _issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", f"Index CSV not found: {path}", "Run current-candidates-backfill-execution-manifest-index.")
            return _prepare_index_frame(pd.DataFrame()), str(path), [issue]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    frame = scan_current_candidates_backfill_execution_manifest_artifacts(root)
    return _prepare_index_frame(frame), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate the execution manifest artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate the execution manifest artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_manifest_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "manifest_csv_path", path, "ERROR", "MISSING_MANIFEST_CSV", "Execution manifest CSV is missing.", "Regenerate the execution manifest artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "manifest_csv_path", path, "ERROR", "MISSING_MANIFEST_CSV", f"Execution manifest CSV is unreadable: {exc}", "Regenerate the execution manifest artifact."))
        return None
    missing = [column for column in MANIFEST_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(_issue(row, "manifest_csv_path", path, "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns: {', '.join(missing)}", "Regenerate the execution manifest artifact with the current schema."))
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "Execution manifest report is missing.", "Regenerate the execution manifest artifact."))


def _check_manifest_contract(row: dict[str, Any], metadata: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    _check_safety_flags(row, metadata, manifest, issues)
    _check_plan_only(row, metadata, issues)
    _check_blocker_reasons(row, manifest, issues)


def _check_safety_flags(row: dict[str, Any], metadata: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    checks = [
        ("no_live_trading", "LIVE_TRADING_DETECTED"),
        ("no_broker_api", "BROKER_DETECTED"),
        ("no_order_placement", "ORDER_PLACEMENT_DETECTED"),
        ("no_message_sent", "MESSAGE_DELIVERY_DETECTED"),
    ]
    for field, code in checks:
        if not _to_bool(metadata.get(field, False)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{field}=true is missing from metadata.", "Regenerate the execution manifest with safety metadata."))
        if field in manifest.columns and (~manifest[field].map(_to_bool)).any():
            issues.append(_issue(row, "manifest_csv_path", row.get("manifest_csv_path"), "ERROR", code, f"A row does not have {field}=true.", "Regenerate the execution manifest with safety row fields."))
    if _to_bool(metadata.get("live_trading_enabled")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "LIVE_TRADING_DETECTED", "live_trading_enabled=true detected.", "Regenerate local-only execution manifest artifacts."))
    if _to_bool(metadata.get("broker_api_invoked")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "BROKER_DETECTED", "broker_api_invoked=true detected.", "Regenerate local-only execution manifest artifacts."))
    if _to_bool(metadata.get("order_placement_enabled")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "ORDER_PLACEMENT_DETECTED", "order_placement_enabled=true detected.", "Regenerate local-only execution manifest artifacts."))
    if _to_bool(metadata.get("message_delivery_enabled")) or _to_bool(metadata.get("message_sent")):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MESSAGE_DELIVERY_DETECTED", "Message delivery metadata detected.", "Regenerate local-only execution manifest artifacts."))


def _check_plan_only(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if not _to_bool(metadata.get("plan_only", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "PLAN_ONLY_FLAG_MISSING", "plan_only=true is missing from metadata.", "Regenerate as a manifest-only artifact."))
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
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "CANDIDATE_GENERATION_DETECTED", f"{flag}=true detected.", "Regenerate as a manifest-only artifact."))


def _check_blocker_reasons(row: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if manifest.empty or "readiness_status" not in manifest.columns:
        return
    blocked = manifest.loc[manifest["readiness_status"].astype(str).str.startswith("BLOCKED_")]
    if blocked.empty:
        return
    if "blocker_reason" not in blocked.columns or blocked["blocker_reason"].map(_string_or_empty).eq("").any():
        issues.append(_issue(row, "manifest_csv_path", row.get("manifest_csv_path"), "WARN", "BLOCKED_WITHOUT_REASON", "A blocked row is missing blocker_reason.", "Regenerate the execution manifest with explicit blocker reasons."))


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=EXECUTION_MANIFEST_INDEX_COLUMNS)
    output = frame.copy()
    for column in EXECUTION_MANIFEST_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[EXECUTION_MANIFEST_INDEX_COLUMNS].reset_index(drop=True)


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
        "artifact_type": "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST",
        "execution_manifest_id": _string_or_empty(row.get("execution_manifest_id")),
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
