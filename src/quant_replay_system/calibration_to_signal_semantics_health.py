"""Local-only health checks for calibration-to-signal-semantics proposal artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.calibration_to_signal_semantics import PROPOSAL_COLUMNS, SUMMARY_COLUMNS
from quant_replay_system.calibration_to_signal_semantics_index import (
    CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS,
    scan_calibration_to_signal_semantics_artifacts,
)


CALIBRATION_TO_SEMANTICS_HEALTH_LIMITATIONS = [
    "Checks local calibration-to-signal-semantics proposal artifacts referenced by the index only.",
    "Does not regenerate proposal reports or repair artifacts.",
    "Does not change signal semantics defaults, write config, or validate strategy performance.",
    "Does not send messages, place orders, call brokers, call APIs, or enable live trading.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "proposal_run_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

REQUIRED_PATH_FIELDS = ["metadata_path", "report_path", "summary_csv_path", "proposals_csv_path"]

REQUIRED_METADATA_FIELDS = [
    "proposal_run_id",
    "status",
    "proposal_categories",
    "defaults_changed",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
]


@dataclass(frozen=True)
class CalibrationToSemanticsHealthSettings:
    index_path: Path = Path("outputs/reports/calibration_to_signal_semantics/index/calibration_to_signal_semantics_index.csv")
    root_dir: Path = Path("outputs/reports/calibration_to_signal_semantics")
    output_dir: Path = Path("outputs/reports/calibration_to_signal_semantics/health")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False


@dataclass(frozen=True)
class CalibrationToSemanticsHealthPaths:
    artifact_dir: Path
    calibration_to_signal_semantics_health_report: Path
    calibration_to_signal_semantics_health_issues: Path
    calibration_to_signal_semantics_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "calibration_to_signal_semantics_health_report": self.calibration_to_signal_semantics_health_report,
            "calibration_to_signal_semantics_health_issues": self.calibration_to_signal_semantics_health_issues,
            "calibration_to_signal_semantics_health_summary": self.calibration_to_signal_semantics_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CalibrationToSemanticsHealthResult:
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


def check_calibration_to_signal_semantics_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: CalibrationToSemanticsHealthSettings | dict[str, Any] | None = None,
) -> CalibrationToSemanticsHealthResult:
    resolved = _resolve_settings(settings)
    if resolved.enable_live_trading or resolved.enable_broker_api:
        raise ValueError("Calibration-to-semantics health cannot enable live trading or broker API access")
    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=resolved,
    )
    checked_count = len(index_frame)
    health_frame = build_calibration_to_signal_semantics_health_frame(index_frame, base_dir=base_dir)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_calibration_to_signal_semantics_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_calibration_to_signal_semantics_health_check_id(
        index_frame,
        index_source=index_source,
        settings=resolved,
    )
    paths = resolve_calibration_to_signal_semantics_health_paths(
        Path(output_dir) if output_dir is not None else resolved.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": checked_count,
        "strict": resolved.strict,
        "config_version": resolved.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
    }
    result = CalibrationToSemanticsHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=CALIBRATION_TO_SEMANTICS_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if resolved.write_artifacts:
        write_calibration_to_signal_semantics_health_artifacts(result)
    return result


def build_calibration_to_signal_semantics_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
) -> pd.DataFrame:
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL":
            continue
        resolved_paths = {field: _resolve_artifact_path(row.get(field), base_path) for field in REQUIRED_PATH_FIELDS}
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues)
        summary = _check_summary_csv(row, resolved_paths["summary_csv_path"], issues)
        proposals = _check_proposals_csv(row, resolved_paths["proposals_csv_path"], issues)
        report_text = _check_report(row, resolved_paths["report_path"], issues)
        if metadata is not None and summary is not None and proposals is not None and report_text is not None:
            _check_proposal_contract(row, metadata, summary, proposals, report_text, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_calibration_to_signal_semantics_health(
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


def resolve_calibration_to_signal_semantics_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> CalibrationToSemanticsHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return CalibrationToSemanticsHealthPaths(
        artifact_dir=artifact_dir,
        calibration_to_signal_semantics_health_report=artifact_dir / "calibration_to_signal_semantics_health_report.md",
        calibration_to_signal_semantics_health_issues=artifact_dir / "calibration_to_signal_semantics_health_issues.csv",
        calibration_to_signal_semantics_health_summary=artifact_dir / "calibration_to_signal_semantics_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_calibration_to_signal_semantics_health_artifacts(result: CalibrationToSemanticsHealthResult) -> dict[str, Path]:
    paths = CalibrationToSemanticsHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.calibration_to_signal_semantics_health_issues)
    _export_dataframe(result.summary_frame, paths.calibration_to_signal_semantics_health_summary)
    metadata = build_calibration_to_signal_semantics_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.calibration_to_signal_semantics_health_report.write_text(
        render_calibration_to_signal_semantics_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_calibration_to_signal_semantics_health_metadata(
    result: CalibrationToSemanticsHealthResult,
    paths: CalibrationToSemanticsHealthPaths,
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
        "external_api_called": False,
        "llm_api_called": False,
        "config_mutated": False,
        "proposal_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
    }


def render_calibration_to_signal_semantics_health_report(
    result: CalibrationToSemanticsHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"health_check_id": result.health_check_id}
    lines = [
        "# Calibration-to-Signal Semantics Proposal Artifact Health",
        "",
        "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked. This health check reads local proposal artifacts only.",
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
            ["proposal_run_id", "severity", "issue_code", "path_field", "issue_message", "suggested_action"],
            max_rows=200,
        ),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_calibration_to_signal_semantics_health_check_id(
    index_df: pd.DataFrame,
    *,
    index_source: str,
    settings: CalibrationToSemanticsHealthSettings,
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
    settings: CalibrationToSemanticsHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    load_issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "in_memory", None, warnings, load_issues
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            load_issues.append(_issue({}, "metadata_path", path, "ERROR", "MISSING_METADATA", f"Proposal index CSV not found: {path}", "Run calibration-to-signal-semantics-index before health check."))
            return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, load_issues
        frame = pd.read_csv(path, keep_default_na=False)
        return _prepare_index_frame(frame), str(path), path.parent, warnings, load_issues
    effective_root = Path(root) if root is not None else settings.root_dir
    frame = scan_calibration_to_signal_semantics_artifacts(effective_root)
    return _prepare_index_frame(frame), str(effective_root), effective_root, warnings, load_issues


def _check_metadata(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", "metadata.json is missing.", "Regenerate calibration-to-signal-semantics artifacts."))
        return None
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue(row, "metadata_path", path, "ERROR", "MISSING_METADATA", f"metadata.json is unreadable: {exc}", "Regenerate calibration-to-signal-semantics artifacts."))
        return None
    return metadata if isinstance(metadata, dict) else {}


def _check_summary_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "summary_csv_path", path, "ERROR", "MISSING_SUMMARY_CSV", "calibration_to_signal_semantics_summary.csv is missing.", "Regenerate proposal artifacts."))
        return None
    try:
        frame = pd.read_csv(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "summary_csv_path", path, "ERROR", "MISSING_SUMMARY_CSV", f"summary CSV is unreadable: {exc}", "Regenerate proposal artifacts."))
        return None
    missing = [column for column in _required_summary_columns() if column not in frame.columns]
    if missing:
        issues.append(_issue(row, "summary_csv_path", path, "ERROR", "MISSING_REQUIRED_FIELDS", f"Missing required summary fields: {', '.join(missing)}", "Regenerate proposal artifacts with the current schema."))
    return frame


def _check_proposals_csv(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if not path.exists():
        issues.append(_issue(row, "proposals_csv_path", path, "ERROR", "MISSING_PROPOSALS_CSV", "calibration_to_signal_semantics_proposals.csv is missing.", "Regenerate proposal artifacts."))
        return None
    try:
        frame = pd.read_csv(path, keep_default_na=False)
    except Exception as exc:
        issues.append(_issue(row, "proposals_csv_path", path, "ERROR", "MISSING_PROPOSALS_CSV", f"proposals CSV is unreadable: {exc}", "Regenerate proposal artifacts."))
        return None
    missing = [column for column in PROPOSAL_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(_issue(row, "proposals_csv_path", path, "ERROR", "MISSING_REQUIRED_FIELDS", f"Missing required proposal fields: {', '.join(missing)}", "Regenerate proposal artifacts with the current schema."))
    return frame


def _check_report(row: dict[str, Any], path: Path, issues: list[dict[str, Any]]) -> str | None:
    if not path.exists():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "calibration_to_signal_semantics_report.md is missing.", "Regenerate proposal artifacts."))
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", f"report is unreadable: {exc}", "Regenerate proposal artifacts."))
        return None
    if not text.strip():
        issues.append(_issue(row, "report_path", path, "ERROR", "MISSING_REPORT", "report is empty.", "Regenerate proposal artifacts."))
    return text


def _check_proposal_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    summary: pd.DataFrame,
    proposals: pd.DataFrame,
    report_text: str,
    issues: list[dict[str, Any]],
) -> None:
    _check_required_metadata(row, metadata, issues)
    _check_defaults(row, metadata, summary, proposals, issues)
    categories = _categories(metadata, proposals)
    if not categories:
        issues.append(_issue(row, "proposals_csv_path", row.get("proposals_csv_path"), "ERROR", "MISSING_REQUIRED_FIELDS", "Proposal categories are empty.", "Regenerate proposal artifacts."))
    if "REQUIRE_MORE_EVIDENCE" not in categories or "REQUIRE_MORE_EVIDENCE" not in report_text:
        issues.append(_issue(row, "proposals_csv_path", row.get("proposals_csv_path"), "ERROR", "MISSING_MORE_EVIDENCE_WARNING", "REQUIRE_MORE_EVIDENCE is missing from proposals or report.", "Regenerate proposal with more-evidence warning."))
    if "DO_NOT_EXPAND_BUY_REVIEW_YET" not in categories or "DO_NOT_EXPAND_BUY_REVIEW_YET" not in report_text:
        issues.append(_issue(row, "proposals_csv_path", row.get("proposals_csv_path"), "ERROR", "UNSAFE_BUY_REVIEW_EXPANSION", "DO_NOT_EXPAND_BUY_REVIEW_YET is missing from proposals or report.", "Regenerate proposal without buy-review expansion."))
    _check_claims(row, report_text, issues)
    _check_safety(row, metadata, report_text, issues)


def _check_required_metadata(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MISSING_REQUIRED_FIELDS", f"Missing required metadata fields: {', '.join(missing)}", "Regenerate proposal artifacts with current metadata schema."))


def _check_defaults(
    row: dict[str, Any],
    metadata: dict[str, Any],
    summary: pd.DataFrame,
    proposals: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    summary_defaults_changed = False
    if not summary.empty and "defaults_changed" in summary.columns:
        summary_defaults_changed = summary["defaults_changed"].map(_to_bool).any()
    proposal_defaults_changed = False
    if "changes_defaults" in proposals.columns:
        proposal_defaults_changed = proposals["changes_defaults"].map(_to_bool).any()
    if (
        _to_bool(metadata.get("defaults_changed", False))
        or _to_bool(metadata.get("signal_semantics_defaults_changed", False))
        or _to_bool(metadata.get("config_mutated", False))
        or summary_defaults_changed
        or proposal_defaults_changed
    ):
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "DEFAULTS_CHANGED", "Proposal artifact indicates defaults/config changed.", "Regenerate as report-only proposal without config/default changes."))


def _check_claims(row: dict[str, Any], report_text: str, issues: list[dict[str, Any]]) -> None:
    text = report_text.lower()
    strategy_claims = [
        "strategy performance is validated",
        "validated strategy performance",
        "proves strategy performance",
        "validated market edge",
        "profit guarantee",
    ]
    if any(claim in text for claim in strategy_claims):
        issues.append(_issue(row, "report_path", row.get("report_path"), "ERROR", "STRATEGY_PERFORMANCE_CLAIM_DETECTED", "Report claims strategy performance validation.", "Rewrite proposal as design evidence only."))
    trading_claims = [
        "approved for live trading",
        "approved for real trading",
        "trading approval granted",
        "approved for automatic trading",
        "approved for broker execution",
    ]
    if any(claim in text for claim in trading_claims):
        issues.append(_issue(row, "report_path", row.get("report_path"), "ERROR", "TRADING_APPROVAL_DETECTED", "Report claims trading approval.", "Rewrite proposal so it does not approve trading."))


def _check_safety(row: dict[str, Any], metadata: dict[str, Any], report_text: str, issues: list[dict[str, Any]]) -> None:
    unsafe = (
        not _to_bool(metadata.get("no_live_trading", False))
        or not _to_bool(metadata.get("no_broker_api", False))
        or not _to_bool(metadata.get("no_message_sent", False))
        or _to_bool(metadata.get("auto_order_allowed", False))
        or _to_bool(metadata.get("message_sent", False))
        or _to_bool(metadata.get("live_trading_enabled", False))
        or _to_bool(metadata.get("broker_api_invoked", False))
        or _to_bool(metadata.get("message_delivery_enabled", False))
        or _to_bool(metadata.get("external_api_called", False))
        or _to_bool(metadata.get("llm_api_called", False))
        or _to_bool(metadata.get("approved_for_paper_applied", False))
    )
    safety_text = report_text.lower()
    missing_text = not (
        "no live trading" in safety_text
        and "broker" in safety_text
        and ("order placement" in safety_text or "auto_order_allowed" in safety_text)
        and ("message delivery" in safety_text or "no_message_sent" in safety_text)
    )
    if unsafe or missing_text:
        issues.append(_issue(row, "metadata_path", row.get("metadata_path"), "ERROR", "MISSING_SAFETY_STATEMENT", "Safety metadata or report safety language is missing/unsafe.", "Regenerate proposal with no-live/no-broker/no-order/no-message safety language."))


def _categories(metadata: dict[str, Any], proposals: pd.DataFrame) -> set[str]:
    categories: set[str] = set()
    raw = metadata.get("proposal_categories")
    if isinstance(raw, list):
        categories.update(str(item).strip() for item in raw if str(item).strip())
    if "category" in proposals.columns:
        categories.update(str(item).strip() for item in proposals["category"].dropna().astype(str) if str(item).strip())
    return categories


def _required_summary_columns() -> list[str]:
    return [
        column
        for column in SUMMARY_COLUMNS
        if column
        in {
            "proposal_run_id",
            "status",
            "calibration_run_count",
            "observed_review_buy_candidate_count",
            "observed_watch_count",
            "observed_blocked_count",
            "defaults_changed",
            "auto_order_allowed",
            "no_live_trading",
            "no_broker_api",
            "no_message_sent",
        }
    ]


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS)
    output = frame.copy()
    for column in CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[CALIBRATION_TO_SEMANTICS_INDEX_COLUMNS].reset_index(drop=True)


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
        "artifact_type": "CALIBRATION_TO_SIGNAL_SEMANTICS_PROPOSAL",
        "proposal_run_id": _string_or_empty(row.get("proposal_run_id")),
        "path_field": path_field,
        "path_value": str(path_value or ""),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _resolve_settings(settings: CalibrationToSemanticsHealthSettings | dict[str, Any] | None) -> CalibrationToSemanticsHealthSettings:
    if settings is None:
        return CalibrationToSemanticsHealthSettings()
    if isinstance(settings, CalibrationToSemanticsHealthSettings):
        return settings
    return CalibrationToSemanticsHealthSettings(**{**CalibrationToSemanticsHealthSettings().__dict__, **settings})


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
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in frame.loc[:, available].head(max_rows).to_dict("records"):
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
