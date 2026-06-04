"""Health checks for reviewed replacement worklist activation artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.reviewed_replacement_worklist_activation import ACTIVATION_COLUMNS
from quant_replay_system.reviewed_replacement_worklist_activation_index import (
    build_reviewed_replacement_worklist_activation_index,
)


HEALTH_COLUMNS = ["activation_id", "status", "severity", "issue_code", "message", "artifact_path"]


@dataclass(frozen=True)
class ReviewedReplacementWorklistActivationHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def check_reviewed_replacement_worklist_activation_health(
    *,
    root: str | Path = "outputs/reports/reviewed_replacement_worklist_activation",
    index_path: str | Path | None = None,
    output_dir: str | Path = "outputs/reports/reviewed_replacement_worklist_activation/health",
) -> ReviewedReplacementWorklistActivationHealthResult:
    if index_path:
        index_frame = read_csv_preserve_symbol_columns(index_path, keep_default_na=False)
    else:
        index_frame = build_reviewed_replacement_worklist_activation_index(root=root).index_frame
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        issues.extend(_issues_for_row(row))
    health_frame = _finalize(pd.DataFrame(issues))
    error_count = int((health_frame["severity"] == "ERROR").sum()) if not health_frame.empty else 0
    warning_count = int((health_frame["severity"] == "WARNING").sum()) if not health_frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    health_id = _hash_payload({"rows": health_frame.to_dict("records"), "root": str(root)})
    artifact_dir = Path(output_dir) / health_id
    paths = {
        "artifact_dir": artifact_dir,
        "reviewed_replacement_worklist_activation_health_csv": artifact_dir
        / "reviewed_replacement_worklist_activation_health.csv",
        "reviewed_replacement_worklist_activation_health_report": artifact_dir
        / "reviewed_replacement_worklist_activation_health_report.md",
        "metadata": artifact_dir / "metadata.json",
    }
    result = ReviewedReplacementWorklistActivationHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=len(health_frame),
        error_count=error_count,
        warning_count=warning_count,
        health_frame=health_frame,
        artifact_paths=paths,
        warnings=[],
        audit_metadata=_safe_audit_metadata(root, len(index_frame)),
    )
    _write(result)
    return result


def _issues_for_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    activation_id = _text(row.get("activation_id"))
    metadata_path = Path(_text(row.get("metadata_path")))
    activation_csv_path = Path(_text(row.get("activation_csv_path")))
    report_path = Path(_text(row.get("report_path")))
    for path, code in [
        (metadata_path, "MISSING_METADATA"),
        (activation_csv_path, "MISSING_ACTIVATION_CSV"),
        (report_path, "MISSING_REPORT"),
        (Path(_text(row.get("stock_core_worklist_path"))), "MISSING_STOCK_CORE_WORKLIST"),
        (Path(_text(row.get("etf_core_worklist_path"))), "MISSING_ETF_CORE_WORKLIST"),
        (Path(_text(row.get("mixed_demo_core_worklist_path"))), "MISSING_MIXED_DEMO_CORE_WORKLIST"),
        (Path(_text(row.get("stock_core_template_path"))), "MISSING_STOCK_CORE_TEMPLATE"),
        (Path(_text(row.get("etf_core_template_path"))), "MISSING_ETF_CORE_TEMPLATE"),
        (Path(_text(row.get("mixed_demo_core_template_path"))), "MISSING_MIXED_DEMO_CORE_TEMPLATE"),
    ]:
        if not _text(path) or not path.exists():
            issues.append(_issue(activation_id, "ERROR", code, f"Required artifact is missing: {path}", path))
    if activation_csv_path.exists():
        frame = read_csv_preserve_symbol_columns(activation_csv_path, keep_default_na=False)
        missing = sorted(set(ACTIVATION_COLUMNS) - set(frame.columns))
        if missing:
            issues.append(_issue(activation_id, "ERROR", "MISSING_REQUIRED_COLUMNS", ", ".join(missing), activation_csv_path))
        if "active_worklist_mutated" in frame and frame["active_worklist_mutated"].map(_to_bool).any():
            issues.append(_issue(activation_id, "ERROR", "ACTIVE_WORKLIST_MUTATION_DETECTED", "activation rows claim active worklist mutation.", activation_csv_path))
        if "no_approval_applied" in frame and (~frame["no_approval_applied"].map(_to_bool)).any():
            issues.append(_issue(activation_id, "ERROR", "APPROVAL_APPLIED_DETECTED", "activation rows indicate approval was applied.", activation_csv_path))
        if "no_rejection_applied" in frame and (~frame["no_rejection_applied"].map(_to_bool)).any():
            issues.append(_issue(activation_id, "ERROR", "REJECTION_APPLIED_DETECTED", "activation rows indicate rejection was applied.", activation_csv_path))
        if "valid_for_signal_date" in frame and frame["valid_for_signal_date"].map(_to_bool).any():
            issues.append(_issue(activation_id, "ERROR", "PIT_ROW_VALIDATION_DETECTED", "activation rows claim valid PIT rows.", activation_csv_path))
    if not _to_bool(row.get("activation_acknowledged")):
        issues.append(_issue(activation_id, "ERROR", "ACTIVATION_ACKNOWLEDGEMENT_MISSING", "activation acknowledgement flag is missing.", metadata_path))
    if not _text(row.get("activated_by")) or not _text(row.get("activated_at")) or not _text(row.get("activation_reason")):
        issues.append(_issue(activation_id, "ERROR", "ACTIVATION_METADATA_MISSING", "activated_by, activated_at, and activation_reason are required.", metadata_path))
    if _to_bool(row.get("active_worklist_mutated")):
        issues.append(_issue(activation_id, "ERROR", "ACTIVE_WORKLIST_MUTATION_DETECTED", "Metadata claims active worklist mutation.", metadata_path))
    false_flag_issues = {
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
        "activation_only": "ACTIVATION_ONLY_FLAG_MISSING",
    }
    for field, code in false_flag_issues.items():
        if not _to_bool(row.get(field)):
            issues.append(_issue(activation_id, "ERROR", code, f"Safety flag {field} is not true.", metadata_path))
    return issues


def _write(result: ReviewedReplacementWorklistActivationHealthResult) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths["reviewed_replacement_worklist_activation_health_csv"], index=False)
    paths["reviewed_replacement_worklist_activation_health_report"].write_text(
        "\n".join(
            [
                "# Reviewed Replacement Worklist Activation Health",
                "",
                f"- status: {result.status}",
                f"- checked_artifact_count: {result.checked_artifact_count}",
                f"- issue_count: {result.issue_count}",
                f"- error_count: {result.error_count}",
                f"- warning_count: {result.warning_count}",
                "",
                result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "health_id": paths["artifact_dir"].name,
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _issue(activation_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, Any]:
    return {
        "activation_id": activation_id,
        "status": "FAIL" if severity == "ERROR" else "WARN",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _safe_audit_metadata(root: str | Path, checked_count: int) -> dict[str, Any]:
    return {
        "root_dir": str(root),
        "checked_artifact_count": checked_count,
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
    }


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    for column in HEALTH_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame.loc[:, HEALTH_COLUMNS]


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value




