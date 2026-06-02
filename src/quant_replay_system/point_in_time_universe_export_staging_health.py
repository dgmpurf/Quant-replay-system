"""Health checks for guarded PIT universe export staging artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import UNIVERSE_SNAPSHOT_SCHEMA, read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_export_staging import STAGING_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_export_staging_index import (
    PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS,
    scan_pit_universe_export_staging_artifacts,
)


HEALTH_COLUMNS = [
    "artifact_type",
    "staging_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]


@dataclass(frozen=True)
class PitUniverseExportStagingHealthPaths:
    artifact_dir: Path
    pit_universe_export_staging_health_report: Path
    pit_universe_export_staging_health_issues: Path
    pit_universe_export_staging_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_export_staging_health_report": self.pit_universe_export_staging_health_report,
            "pit_universe_export_staging_health_issues": self.pit_universe_export_staging_health_issues,
            "pit_universe_export_staging_health_summary": self.pit_universe_export_staging_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseExportStagingHealthResult:
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


def check_pit_universe_export_staging_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path = "outputs/reports/point_in_time_universe_export_staging",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_export_staging/health",
) -> PitUniverseExportStagingHealthResult:
    index_frame, index_source, load_issues = _load_index(index_df=index_df, index_path=index_path, root=root)
    health_frame = build_pit_universe_export_staging_health_frame(index_frame)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_pit_universe_export_staging_health(health_frame, checked_artifact_count=len(index_frame))
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = _hash_payload({"rows": index_frame.to_dict("records"), "status": status}, 12)
    paths = resolve_pit_universe_export_staging_health_paths(output_dir, health_check_id)
    result = PitUniverseExportStagingHealthResult(
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
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "broker_api_invoked": False,
            "message_sent": False,
            "pit_universe_export_staging_artifacts_only": True,
        },
    )
    write_pit_universe_export_staging_health_artifacts(result)
    return result


def build_pit_universe_export_staging_health_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        metadata = _check_metadata(row, Path(_text(row.get("metadata_path"))), issues)
        staging = _check_csv(row, Path(_text(row.get("staging_csv_path"))), issues)
        _check_report(row, Path(_text(row.get("report_path"))), issues)
        if metadata is not None and staging is not None:
            _check_safety_contract(row, metadata, staging, issues)
            _check_staged_rows(row, staging, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_pit_universe_export_staging_health(health_frame: pd.DataFrame, *, checked_artifact_count: int) -> pd.DataFrame:
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


def resolve_pit_universe_export_staging_health_paths(output_dir: str | Path, health_check_id: str) -> PitUniverseExportStagingHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return PitUniverseExportStagingHealthPaths(
        artifact_dir=artifact_dir,
        pit_universe_export_staging_health_report=artifact_dir / "pit_universe_export_staging_health_report.md",
        pit_universe_export_staging_health_issues=artifact_dir / "pit_universe_export_staging_health_issues.csv",
        pit_universe_export_staging_health_summary=artifact_dir / "pit_universe_export_staging_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_export_staging_health_artifacts(result: PitUniverseExportStagingHealthResult) -> dict[str, Path]:
    paths = PitUniverseExportStagingHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.pit_universe_export_staging_health_issues, index=False)
    result.summary_frame.to_csv(paths.pit_universe_export_staging_health_summary, index=False)
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
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, network/API, "
            "LLM/API, or cache mutation was invoked."
        ),
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_export_staging_health_report.write_text(render_pit_universe_export_staging_health_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_export_staging_health_report(result: PitUniverseExportStagingHealthResult) -> str:
    return "\n".join(
        [
            "# PIT Universe Export Staging Health",
            "",
            "No data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, network/API, LLM/API, or cache mutation was invoked.",
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


def _load_index(*, index_df: pd.DataFrame | None, index_path: str | Path | None, root: str | Path) -> tuple[pd.DataFrame, str, list[dict[str, Any]]]:
    if index_df is not None:
        return _prepare_index_frame(index_df), "in_memory", []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            return _prepare_index_frame(pd.DataFrame()), str(path), [_issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", "Index CSV not found.", "Run pit-universe-export-staging-index.")]
        return _prepare_index_frame(pd.read_csv(path, keep_default_na=False)), str(path), []
    return _prepare_index_frame(scan_pit_universe_export_staging_artifacts(root)), str(root), []


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate staging artifact."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate staging artifact."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "staging_csv_path", path, "ERROR", "MISSING_STAGING_CSV", "staging CSV is missing.", "Regenerate staging artifact."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "staging_csv_path", path, "ERROR", "MISSING_STAGING_CSV", f"staging CSV is unreadable: {exc}", "Regenerate staging artifact."))
        return None
    missing = [column for column in STAGING_OUTPUT_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(_issue(row, "staging_csv_path", path, "ERROR", "MISSING_REQUIRED_COLUMNS", f"Missing required columns: {', '.join(missing)}", "Regenerate staging artifact with current schema."))
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "staging report is missing.", "Regenerate staging artifact."))


def _check_safety_contract(row: dict[str, Any], metadata: dict[str, Any], staging: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    false_flags = {
        "would_write_data_raw": "DATA_RAW_WRITE_DETECTED",
        "would_write_data_processed": "DATA_PROCESSED_WRITE_DETECTED",
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
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{flag}=true detected.", "Regenerate staging artifact as outputs-only."))
    true_flags = {
        "no_current_candidates_generated": "CURRENT_CANDIDATES_GENERATED",
        "no_snapshot_built": "SNAPSHOT_BUILT",
        "no_forward_labels": "FORWARD_LABELS_COMPUTED",
        "no_live_trading": "LIVE_TRADING_DETECTED",
        "no_broker_api": "BROKER_DETECTED",
        "no_order_placement": "ORDER_PLACEMENT_DETECTED",
        "no_message_sent": "MESSAGE_DELIVERY_DETECTED",
        "staging_only": "STAGING_ONLY_FLAG_MISSING",
    }
    for flag, code in true_flags.items():
        if not _to_bool(metadata.get(flag)):
            issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", code, f"{flag}=true is missing.", "Regenerate staging artifact with safety metadata."))
        if flag in staging.columns and (~staging[flag].map(_to_bool)).any():
            issues.append(_issue(row, "staging_csv_path", row.get("staging_csv_path"), "ERROR", code, f"A row does not have {flag}=true.", "Regenerate staging artifact with safety row fields."))


def _check_staged_rows(row: dict[str, Any], staging: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if staging.empty or "staging_status" not in staging.columns:
        return
    staged = staging.loc[staging["staging_status"].astype(str).eq("EXPORT_STAGING_DRY_RUN_CREATED")].copy()
    if staged.empty:
        return
    for column in UNIVERSE_SNAPSHOT_SCHEMA:
        if column not in staged.columns:
            issues.append(_issue(row, "staging_csv_path", row.get("staging_csv_path"), "ERROR", "STAGED_ROW_MISSING_UNIVERSE_COLUMNS", f"Staged rows missing universe column: {column}", "Regenerate staging artifact."))
            continue
        if column not in {"listed_date", "delisted_date"} and staged[column].map(_text).eq("").any():
            issues.append(_issue(row, "staging_csv_path", row.get("staging_csv_path"), "ERROR", "STAGED_ROW_MISSING_UNIVERSE_COLUMNS", f"Staged rows have blank required universe column: {column}", "Complete PIT metadata before staging."))


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[PIT_UNIVERSE_EXPORT_STAGING_INDEX_COLUMNS].reset_index(drop=True)


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
        "artifact_type": "PIT_UNIVERSE_EXPORT_STAGING",
        "staging_id": _text(row.get("staging_id")),
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
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


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
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
