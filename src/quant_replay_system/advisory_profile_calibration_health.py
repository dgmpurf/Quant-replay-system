"""Local-only health checks for advisory profile calibration artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.advisory_profile_calibration import CALIBRATION_COLUMNS
from quant_replay_system.advisory_profile_calibration_index import (
    ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS,
    scan_advisory_profile_calibration_artifacts,
)
from quant_replay_system.config import AdvisoryProfileCalibrationHealthSettings, Settings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


ADVISORY_PROFILE_CALIBRATION_HEALTH_LIMITATIONS = [
    "Checks local advisory profile calibration artifacts referenced by the index only.",
    "Does not regenerate calibration results or repair artifacts.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
    "Does not validate strategy quality or convert review labels into orders.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "calibration_run_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_METADATA",
    "MISSING_CALIBRATION_CSV",
    "MISSING_SUMMARY_CSV",
    "MISSING_REPORT",
    "MISSING_REQUIRED_COLUMNS",
    "SYMBOL_FORMAT_ERROR",
    "DEMO_PROFILE_ACTION_UNSAFE",
    "REVIEW_LABEL_WITHOUT_MANUAL_CONFIRMATION",
    "AUTO_ORDER_ALLOWED",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "BROKER_OR_LIVE_TRADING_DETECTED",
    "MESSAGE_DELIVERY_DETECTED",
    "APPROVED_FOR_PAPER_DETECTED",
    "BLOCKED_WITHOUT_REASON",
    "STALE_OR_PARTIAL_CALIBRATION_RUN",
}

REQUIRED_PATH_FIELDS = [
    "metadata_path",
    "calibration_csv_path",
    "summary_csv_path",
    "report_path",
    "issues_csv_path",
]


@dataclass(frozen=True)
class AdvisoryProfileCalibrationHealthPaths:
    artifact_dir: Path
    advisory_profile_calibration_health_report: Path
    advisory_profile_calibration_health_issues: Path
    advisory_profile_calibration_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_profile_calibration_health_report": self.advisory_profile_calibration_health_report,
            "advisory_profile_calibration_health_issues": self.advisory_profile_calibration_health_issues,
            "advisory_profile_calibration_health_summary": self.advisory_profile_calibration_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AdvisoryProfileCalibrationHealthResult:
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


def check_advisory_profile_calibration_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | AdvisoryProfileCalibrationHealthSettings | dict[str, Any] | None = None,
) -> AdvisoryProfileCalibrationHealthResult:
    """Check indexed advisory profile calibration artifacts for file and safety health."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Advisory profile calibration health cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_advisory_profile_calibration_health_frame(index_frame, base_dir=base_dir)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_advisory_profile_calibration_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_advisory_profile_calibration_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_advisory_profile_calibration_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": checked_count,
        "strict": health_settings.strict,
        "config_version": health_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "advisory_profile_calibration_artifacts_only": True,
    }
    result = AdvisoryProfileCalibrationHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=ADVISORY_PROFILE_CALIBRATION_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_advisory_profile_calibration_health_artifacts(result)
    _ = project_settings
    return result


def build_advisory_profile_calibration_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "ADVISORY_PROFILE_CALIBRATION":
            continue
        resolved_paths = {field: _resolve_artifact_path(row.get(field), base_path) for field in REQUIRED_PATH_FIELDS}
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues)
        calibration = _check_calibration_csv(row, resolved_paths["calibration_csv_path"], issues)
        _check_summary_csv(row, resolved_paths["summary_csv_path"], issues)
        _check_markdown(row, "report_path", resolved_paths["report_path"], "MISSING_REPORT", issues)
        _check_issues_csv(row, resolved_paths["issues_csv_path"], issues)
        if metadata is not None and calibration is not None:
            _check_calibration_contract(row, metadata, calibration, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_advisory_profile_calibration_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "checked_artifact_count": checked_artifact_count,
            "issue_count": issue_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
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
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_advisory_profile_calibration_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> AdvisoryProfileCalibrationHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return AdvisoryProfileCalibrationHealthPaths(
        artifact_dir=artifact_dir,
        advisory_profile_calibration_health_report=artifact_dir / "advisory_profile_calibration_health_report.md",
        advisory_profile_calibration_health_issues=artifact_dir / "advisory_profile_calibration_health_issues.csv",
        advisory_profile_calibration_health_summary=artifact_dir / "advisory_profile_calibration_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_profile_calibration_health_artifacts(result: AdvisoryProfileCalibrationHealthResult) -> dict[str, Path]:
    paths = AdvisoryProfileCalibrationHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.advisory_profile_calibration_health_issues)
    _export_dataframe(result.summary_frame, paths.advisory_profile_calibration_health_summary)
    metadata = build_advisory_profile_calibration_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_profile_calibration_health_report.write_text(
        render_advisory_profile_calibration_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_profile_calibration_health_metadata(
    result: AdvisoryProfileCalibrationHealthResult,
    paths: AdvisoryProfileCalibrationHealthPaths,
) -> dict[str, Any]:
    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "config_summary": {
            "index_source": result.audit_metadata.get("index_source", ""),
            "strict": bool(result.audit_metadata.get("strict", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "advisory_profile_calibration_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_advisory_profile_calibration_health_report(
    result: AdvisoryProfileCalibrationHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"health_check_id": result.health_check_id}
    lines = [
        "# Advisory Profile Calibration Artifact Health",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This health check reads local calibration artifacts only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "health_check_id": meta.get("health_check_id", ""),
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
            ["calibration_run_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
            max_rows=200,
        ),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_advisory_profile_calibration_health_check_id(
    index_df: pd.DataFrame,
    *,
    index_source: str,
    settings: AdvisoryProfileCalibrationHealthSettings,
) -> str:
    payload = {
        "index_source": index_source,
        "rows": index_df.to_dict("records") if index_df is not None else [],
        "strict": settings.strict,
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: AdvisoryProfileCalibrationHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    load_issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "in_memory", None, warnings, load_issues
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            load_issues.append(
                _issue(
                    {},
                    "metadata_path",
                    path,
                    "ERROR",
                    "MISSING_METADATA",
                    f"Advisory profile calibration index CSV not found: {path}",
                    "Run advisory-profile-calibration-index before health check.",
                )
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, load_issues
        frame = pd.read_csv(path, keep_default_na=False)
        return _prepare_index_frame(frame), str(path), path.parent, warnings, load_issues
    effective_root = Path(root) if root is not None else settings.root_dir
    frame = scan_advisory_profile_calibration_artifacts(effective_root)
    return _prepare_index_frame(frame), str(effective_root), effective_root, warnings, load_issues


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate advisory-profile-calibration artifacts."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate advisory-profile-calibration artifacts."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_calibration_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "calibration_csv_path", path, "ERROR", "MISSING_CALIBRATION_CSV", "advisory_profile_calibration.csv is missing.", "Regenerate advisory-profile-calibration artifacts."))
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "calibration_csv_path", path, "ERROR", "MISSING_CALIBRATION_CSV", f"advisory_profile_calibration.csv is unreadable: {exc}", "Regenerate advisory-profile-calibration artifacts."))
        return None
    missing = [column for column in CALIBRATION_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(
            _issue(
                row,
                "calibration_csv_path",
                path,
                "ERROR",
                "MISSING_REQUIRED_COLUMNS",
                f"Missing required columns: {', '.join(missing)}",
                "Regenerate advisory-profile-calibration artifacts with the current schema.",
            )
        )
    return frame


def _check_summary_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, "summary_csv_path", path, "ERROR", "MISSING_SUMMARY_CSV", "advisory_profile_calibration_summary.csv is missing.", "Regenerate advisory-profile-calibration artifacts."))
        return
    try:
        pd.read_csv(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "summary_csv_path", path, "ERROR", "MISSING_SUMMARY_CSV", f"summary CSV is unreadable: {exc}", "Regenerate advisory-profile-calibration artifacts."))


def _check_markdown(row: dict[str, Any], field: str, path: Path, code: str, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(_issue(row, field, path, "ERROR", code, f"{path.name} is missing.", "Regenerate advisory-profile-calibration artifacts."))


def _check_issues_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> None:
    if not path.exists():
        issues.append(
            _issue(
                row,
                "issues_csv_path",
                path,
                "WARN",
                "STALE_OR_PARTIAL_CALIBRATION_RUN",
                "advisory_profile_calibration_issues.csv is missing.",
                "Regenerate advisory-profile-calibration artifacts if row-level issues need audit.",
            )
        )
        return
    try:
        pd.read_csv(path, keep_default_na=False)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                "issues_csv_path",
                path,
                "WARN",
                "STALE_OR_PARTIAL_CALIBRATION_RUN",
                f"issues CSV is unreadable: {exc}",
                "Regenerate advisory-profile-calibration artifacts if row-level issues need audit.",
            )
        )


def _check_calibration_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    calibration: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    _check_metadata_safety(row, metadata, issues)
    _check_calibration_safety(row, calibration, issues)
    _check_demo_actions(row, metadata, calibration, issues)
    _check_review_manual_confirmation(row, calibration, issues)
    _check_symbols(row, calibration, issues)
    _check_blocked_reasons(row, calibration, issues)


def _check_metadata_safety(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if _to_bool(metadata.get("auto_order_allowed", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "AUTO_ORDER_ALLOWED", "auto_order_allowed=true detected.", "Regenerate artifacts with auto-order disabled."))
    if not _to_bool(metadata.get("no_live_trading", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MISSING_NO_LIVE_TRADING_STATEMENT", "no_live_trading=true is missing.", "Regenerate artifacts with no-live safety metadata."))
    if not _to_bool(metadata.get("no_broker_api", False)) or _to_bool(metadata.get("live_trading_enabled", False)) or _to_bool(metadata.get("broker_api_invoked", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "BROKER_OR_LIVE_TRADING_DETECTED", "Broker or live-trading metadata was detected.", "Regenerate local-only calibration artifacts."))
    if not _to_bool(metadata.get("no_message_sent", False)) or _to_bool(metadata.get("message_delivery_enabled", False)) or _to_bool(metadata.get("message_sent", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MESSAGE_DELIVERY_DETECTED", "Message delivery metadata was detected.", "Regenerate local-only calibration artifacts."))
    if _to_bool(metadata.get("approved_for_paper_applied", False)):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "APPROVED_FOR_PAPER_DETECTED", "APPROVED_FOR_PAPER metadata was detected.", "Do not use calibration artifacts to apply paper approval."))


def _check_calibration_safety(row: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "auto_order_allowed" in frame.columns and frame["auto_order_allowed"].map(_to_bool).any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "AUTO_ORDER_ALLOWED", "auto_order_allowed=true found in calibration CSV.", "Regenerate artifacts with auto-order disabled."))
    if "no_live_trading" in frame.columns and (~frame["no_live_trading"].map(_to_bool)).any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "MISSING_NO_LIVE_TRADING_STATEMENT", "A row does not have no_live_trading=true.", "Regenerate local-only calibration artifacts."))
    if "no_broker_api" in frame.columns and (~frame["no_broker_api"].map(_to_bool)).any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "BROKER_OR_LIVE_TRADING_DETECTED", "A row does not have no_broker_api=true.", "Regenerate local-only calibration artifacts."))
    if "no_message_sent" in frame.columns and (~frame["no_message_sent"].map(_to_bool)).any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "MESSAGE_DELIVERY_DETECTED", "A row does not have no_message_sent=true.", "Regenerate local-only calibration artifacts."))


def _check_demo_actions(row: dict[str, Any], metadata: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    demo_metadata = str(metadata.get("profile", "")).lower() == "demo"
    if "demo_mode" in frame.columns:
        demo_metadata = demo_metadata or frame["demo_mode"].map(_to_bool).any()
    if "selection_profile" in frame.columns:
        demo_metadata = demo_metadata or frame["selection_profile"].astype(str).str.lower().eq("demo").any()
    if "not_strategy_recommendation" in frame.columns:
        demo_metadata = demo_metadata or frame["not_strategy_recommendation"].map(_to_bool).any()
    if not demo_metadata or "simulated_advisory_label" not in frame.columns:
        return
    unsafe = frame["simulated_advisory_label"].astype(str).str.upper().isin(
        {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE"}
    )
    if unsafe.any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "DEMO_PROFILE_ACTION_UNSAFE", "Demo calibration includes buy/sell review labels.", "Regenerate calibration so demo rows remain DEMO_ONLY/WATCH/NO_ACTION/BLOCKED."))


def _check_review_manual_confirmation(row: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "simulated_advisory_label" not in frame.columns or "requires_manual_confirmation" not in frame.columns:
        return
    review_rows = frame["simulated_advisory_label"].astype(str).str.upper().isin(
        {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE"}
    )
    missing_confirmation = review_rows & (~frame["requires_manual_confirmation"].map(_to_bool))
    if missing_confirmation.any():
        issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "REVIEW_LABEL_WITHOUT_MANUAL_CONFIRMATION", "A review label lacks requires_manual_confirmation=true.", "Regenerate calibration with manual confirmation required."))


def _check_symbols(row: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "symbol" not in frame.columns:
        return
    for raw in frame["symbol"].dropna().astype(str):
        text = raw.strip()
        if not text:
            continue
        normalized = normalize_symbol_value(text)
        if normalized != text or not (text.isdigit() and len(text) == 6):
            issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "ERROR", "SYMBOL_FORMAT_ERROR", f"Symbol '{text}' is not preserved as a six-digit string.", "Regenerate artifacts while preserving symbol columns as text."))
            return


def _check_blocked_reasons(row: dict[str, Any], frame: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "simulated_advisory_label" not in frame.columns:
        return
    blocked = frame.loc[frame["simulated_advisory_label"].astype(str).str.upper() == "BLOCKED"].copy()
    if blocked.empty:
        return
    for record in blocked.to_dict("records"):
        reason = " ".join(
            str(record.get(key, "")).strip()
            for key in ["reason_summary", "issue_codes", "risk_precheck_reason"]
            if str(record.get(key, "")).strip()
        )
        if not reason:
            issues.append(_issue(row, "calibration_csv_path", row.get("calibration_csv_path"), "WARN", "BLOCKED_WITHOUT_REASON", "A BLOCKED row has no reason or issue code.", "Regenerate calibration with blocked reason context."))
            return


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS)
    output = frame.copy()
    for column in ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[ADVISORY_PROFILE_CALIBRATION_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy()
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _resolve_artifact_path(value: Any, base_dir: Path | None) -> Path:
    path = Path(str(value or ""))
    if path.is_absolute() or path.exists() or base_dir is None:
        return path
    candidate = base_dir / path
    return candidate if candidate.exists() else path


def _issue(
    row: dict[str, Any],
    path_field: str,
    path_value: Any,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "ADVISORY_PROFILE_CALIBRATION",
        "calibration_run_id": _string_or_empty(row.get("calibration_run_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _resolve_settings(
    settings: Settings | AdvisoryProfileCalibrationHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, AdvisoryProfileCalibrationHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.advisory_profile_calibration_health
    if isinstance(settings, Settings):
        return settings, settings.advisory_profile_calibration_health
    if isinstance(settings, AdvisoryProfileCalibrationHealthSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"advisory_profile_calibration_health": settings}), settings
    project = load_settings(Path("config/default.yaml"))
    updated = project.advisory_profile_calibration_health.model_copy(update=settings)
    return project.model_copy(update={"advisory_profile_calibration_health": updated}), updated


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _format_markdown_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("|", "\\|")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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
