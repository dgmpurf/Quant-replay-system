"""Local-only health checks for single-symbol advisory artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SingleSymbolAdvisoryHealthSettings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.single_symbol_advisory import SINGLE_SYMBOL_ADVISORY_COLUMNS
from quant_replay_system.single_symbol_advisory_index import (
    SINGLE_SYMBOL_ADVISORY_INDEX_COLUMNS,
    scan_single_symbol_advisory_artifacts,
)


SINGLE_SYMBOL_ADVISORY_HEALTH_LIMITATIONS = [
    "Checks local single-symbol advisory artifacts referenced by the index only.",
    "Does not regenerate advisory reviews or alert previews.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
    "Does not validate strategy quality or approve demo outputs as recommendations.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "advisory_run_id",
    "symbol",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_METADATA",
    "MISSING_ADVISORY_JSON",
    "MISSING_ADVISORY_CSV",
    "MISSING_REPORT",
    "MISSING_ALERT_PREVIEW",
    "MISSING_REQUIRED_FIELDS",
    "SYMBOL_FORMAT_ERROR",
    "AUTO_ORDER_ALLOWED",
    "MISSING_MANUAL_CONFIRMATION",
    "DEMO_ACTION_UNSAFE",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "MESSAGE_DELIVERY_DETECTED",
    "NOT_FOUND_WITH_RECOMMENDATION",
    "STALE_OR_PARTIAL_ADVISORY",
}

REQUIRED_PATH_FIELDS = [
    "metadata_path",
    "advisory_json_path",
    "advisory_csv_path",
    "report_path",
    "alert_preview_path",
]

DEMO_SAFE_ACTIONS = {"DEMO_ONLY", "WATCH", "BLOCKED", "NO_ACTION"}
NOT_FOUND_SAFE_ACTIONS = {"NO_ACTION", ""}
UNSAFE_RECOMMENDATION_ACTIONS = {"REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE", "BUY", "SELL"}


@dataclass(frozen=True)
class SingleSymbolAdvisoryHealthPaths:
    artifact_dir: Path
    single_symbol_advisory_health_report: Path
    single_symbol_advisory_health_issues: Path
    single_symbol_advisory_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_health_report": self.single_symbol_advisory_health_report,
            "single_symbol_advisory_health_issues": self.single_symbol_advisory_health_issues,
            "single_symbol_advisory_health_summary": self.single_symbol_advisory_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryHealthResult:
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


def check_single_symbol_advisory_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | SingleSymbolAdvisoryHealthSettings | dict[str, Any] | None = None,
) -> SingleSymbolAdvisoryHealthResult:
    """Check indexed single-symbol advisory artifacts for safety and file health."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory health check cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_single_symbol_advisory_health_frame(
        index_frame,
        base_dir=base_dir,
        settings=health_settings,
    )
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_single_symbol_advisory_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_single_symbol_advisory_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_single_symbol_advisory_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": checked_count,
        "strict": health_settings.strict,
        "require_alert_preview": health_settings.require_alert_preview,
        "missing_alert_preview_severity": health_settings.missing_alert_preview_severity,
        "config_version": health_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "single_symbol_advisory_artifacts_only": True,
    }
    result = SingleSymbolAdvisoryHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=SINGLE_SYMBOL_ADVISORY_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_single_symbol_advisory_health_artifacts(result)
    _ = project_settings
    return result


def build_single_symbol_advisory_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: SingleSymbolAdvisoryHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    cfg = _coerce_health_settings(settings)
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []
    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "SINGLE_SYMBOL_ADVISORY":
            continue
        resolved_paths = {field: _resolve_artifact_path(row.get(field), base_path) for field in REQUIRED_PATH_FIELDS}
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues)
        advisory_json = _check_json(row, resolved_paths["advisory_json_path"], issues)
        advisory_csv = _check_csv(row, resolved_paths["advisory_csv_path"], issues)
        _check_markdown(row, "report_path", resolved_paths["report_path"], "MISSING_REPORT", issues, cfg)
        if cfg.require_alert_preview:
            _check_markdown(
                row,
                "alert_preview_path",
                resolved_paths["alert_preview_path"],
                "MISSING_ALERT_PREVIEW",
                issues,
                cfg,
                severity=cfg.missing_alert_preview_severity,
            )
        if metadata is not None and advisory_csv is not None:
            _check_advisory_contract(row, metadata, advisory_csv, advisory_json, issues)
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_single_symbol_advisory_health(
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


def resolve_single_symbol_advisory_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> SingleSymbolAdvisoryHealthPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return SingleSymbolAdvisoryHealthPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_health_report=artifact_dir / "single_symbol_advisory_health_report.md",
        single_symbol_advisory_health_issues=artifact_dir / "single_symbol_advisory_health_issues.csv",
        single_symbol_advisory_health_summary=artifact_dir / "single_symbol_advisory_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_single_symbol_advisory_health_artifacts(result: SingleSymbolAdvisoryHealthResult) -> dict[str, Path]:
    paths = SingleSymbolAdvisoryHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.single_symbol_advisory_health_issues, index=False)
    result.summary_frame.to_csv(paths.single_symbol_advisory_health_summary, index=False)
    metadata = build_single_symbol_advisory_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.single_symbol_advisory_health_report.write_text(
        render_single_symbol_advisory_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_single_symbol_advisory_health_metadata(
    result: SingleSymbolAdvisoryHealthResult,
    paths: SingleSymbolAdvisoryHealthPaths,
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
            "require_alert_preview": bool(result.audit_metadata.get("require_alert_preview", True)),
            "missing_alert_preview_severity": result.audit_metadata.get("missing_alert_preview_severity", ""),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "single_symbol_advisory_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_single_symbol_advisory_health_report(
    result: SingleSymbolAdvisoryHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    _ = metadata
    lines = [
        f"# Single-Symbol Advisory Artifact Health Check: {result.health_check_id}",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This health check validates local single-symbol advisory artifacts only.",
        "",
        "## Health Summary",
        "",
        _markdown_table(
            result.summary_frame,
            ["status", "checked_artifact_count", "issue_count", "error_count", "warning_count", "info_count", "issue_code"],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.health_frame,
            ["artifact_type", "advisory_run_id", "symbol", "path_field", "severity", "issue_code", "issue_message", "suggested_action"],
            max_rows=100,
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_single_symbol_advisory_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: SingleSymbolAdvisoryHealthSettings,
) -> str:
    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "advisory_run_ids": sorted(str(value) for value in frame.get("advisory_run_id", pd.Series(dtype="object")).dropna()),
        "strict": settings.strict,
        "require_alert_preview": settings.require_alert_preview,
        "missing_alert_preview_severity": settings.missing_alert_preview_severity,
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def _load_index_for_health(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: SingleSymbolAdvisoryHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_single_symbol_advisory_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_single_symbol_advisory_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


def _load_index_path(
    path: Path,
    warnings: list[str],
    issues: list[dict[str, Any]],
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    try:
        frame = pd.read_csv(path, dtype={"advisory_run_id": str, "symbol": str})
    except Exception as exc:
        issues.append(
            _issue(
                {"artifact_type": "", "advisory_run_id": "", "symbol": ""},
                path_field="index_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message=f"Could not read single-symbol advisory index CSV: {exc}",
                suggested_action="Regenerate single-symbol-advisory-index.",
            )
        )
        return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _check_metadata(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message="Single-symbol advisory metadata.json is missing.",
                suggested_action="Rerun single-symbol-advisory.",
            )
        )
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message=f"Single-symbol advisory metadata.json is unreadable: {exc}",
                suggested_action="Regenerate the advisory artifact.",
            )
        )
        return None


def _check_json(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="advisory_json_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ADVISORY_JSON",
                issue_message="single_symbol_advisory.json is missing.",
                suggested_action="Rerun single-symbol-advisory.",
            )
        )
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(
            _issue(
                row,
                path_field="advisory_json_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ADVISORY_JSON",
                issue_message=f"single_symbol_advisory.json is unreadable: {exc}",
                suggested_action="Regenerate the advisory artifact.",
            )
        )
        return None


def _check_csv(row: dict[str, Any], path: Path | None, issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ADVISORY_CSV",
                issue_message="single_symbol_advisory.csv is missing.",
                suggested_action="Rerun single-symbol-advisory.",
            )
        )
        return None
    try:
        frame = read_csv_preserve_symbol_columns(path)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_ADVISORY_CSV",
                issue_message=f"single_symbol_advisory.csv is unreadable: {exc}",
                suggested_action="Regenerate the advisory artifact.",
            )
        )
        return None
    missing = [column for column in SINGLE_SYMBOL_ADVISORY_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_REQUIRED_FIELDS",
                issue_message=f"single_symbol_advisory.csv is missing required columns: {', '.join(missing)}",
                suggested_action="Regenerate CSV with the current single-symbol advisory contract.",
            )
        )
    return frame


def _check_markdown(
    row: dict[str, Any],
    field: str,
    path: Path | None,
    issue_code: str,
    issues: list[dict[str, Any]],
    cfg: SingleSymbolAdvisoryHealthSettings,
    *,
    severity: str = "ERROR",
) -> None:
    if path is not None and path.exists():
        return
    issues.append(
        _issue(
            row,
            path_field=field,
            path_value=path,
            severity=_severity(severity, cfg),
            issue_code=issue_code,
            issue_message=f"{field} is missing.",
            suggested_action="Regenerate single-symbol advisory artifacts.",
        )
    )


def _check_advisory_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    advisory_csv: pd.DataFrame,
    advisory_json: dict[str, Any] | None,
    issues: list[dict[str, Any]],
) -> None:
    if advisory_json is not None:
        record = advisory_json.get("record") if isinstance(advisory_json.get("record"), dict) else {}
        missing_json_fields = [column for column in SINGLE_SYMBOL_ADVISORY_COLUMNS if column not in record]
        if missing_json_fields:
            issues.append(
                _issue(
                    row,
                    path_field="advisory_json_path",
                    severity="ERROR",
                    issue_code="MISSING_REQUIRED_FIELDS",
                    issue_message=f"single_symbol_advisory.json record is missing required fields: {', '.join(missing_json_fields)}",
                    suggested_action="Regenerate JSON with the current single-symbol advisory contract.",
                )
            )
    if advisory_csv.empty:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                severity="ERROR",
                issue_code="STALE_OR_PARTIAL_ADVISORY",
                issue_message="single_symbol_advisory.csv has no rows.",
                suggested_action="Regenerate the advisory artifact.",
            )
        )
        return
    record = advisory_csv.iloc[0].to_dict()
    _check_symbol_integrity(row, record, issues)
    _check_safety_flags(row, metadata, record, issues)
    _check_demo_safety(row, metadata, record, issues)
    _check_not_found_safety(row, metadata, record, issues)


def _check_symbol_integrity(row: dict[str, Any], record: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    symbol = _string_or_empty(record.get("symbol") or row.get("symbol"))
    normalized = normalize_symbol_value(symbol)
    if symbol.strip() != normalized and normalized.isdigit() and len(normalized) == 6:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                severity="ERROR",
                issue_code="SYMBOL_FORMAT_ERROR",
                issue_message=f"Advisory symbol appears to have lost leading-zero formatting: {symbol!r}.",
                suggested_action="Regenerate advisory artifacts preserving symbol columns as strings.",
            )
        )


def _check_safety_flags(
    row: dict[str, Any],
    metadata: dict[str, Any],
    record: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    if _to_bool(metadata.get("auto_order_allowed")) or _to_bool(record.get("auto_order_allowed")):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="AUTO_ORDER_ALLOWED",
                issue_message="Artifact allows automatic order placement.",
                suggested_action="Regenerate the artifact with auto_order_allowed=false.",
            )
        )
    if not _to_bool(metadata.get("requires_manual_confirmation", True)) or not _to_bool(record.get("requires_manual_confirmation", True)):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MISSING_MANUAL_CONFIRMATION",
                issue_message="Artifact does not require manual confirmation.",
                suggested_action="Regenerate the artifact with requires_manual_confirmation=true.",
            )
        )
    if not _to_bool(metadata.get("no_live_trading")) or not _to_bool(metadata.get("no_broker_api")):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MISSING_NO_LIVE_TRADING_STATEMENT",
                issue_message="metadata missing no_live_trading=true or no_broker_api=true.",
                suggested_action="Regenerate the artifact with explicit local-only safety flags.",
            )
        )
    if not _to_bool(record.get("no_live_trading")) or not _to_bool(record.get("no_broker_api")):
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                severity="ERROR",
                issue_code="MISSING_NO_LIVE_TRADING_STATEMENT",
                issue_message="CSV missing no_live_trading=true or no_broker_api=true.",
                suggested_action="Regenerate the artifact with explicit local-only safety flags.",
            )
        )
    if not _to_bool(metadata.get("no_message_sent")) or not _to_bool(record.get("no_message_sent")):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MESSAGE_DELIVERY_DETECTED",
                issue_message="Artifact does not assert no_message_sent=true.",
                suggested_action="Regenerate the artifact as local preview only.",
            )
        )
    if any(_to_bool(metadata.get(key)) for key in ["message_sent", "message_delivery_enabled", "alert_delivery_enabled"]):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MESSAGE_DELIVERY_DETECTED",
                issue_message="metadata indicates message delivery or message sending.",
                suggested_action="Do not use this artifact as local-only evidence; investigate delivery state.",
            )
        )


def _check_demo_safety(row: dict[str, Any], metadata: dict[str, Any], record: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    demo = _to_bool(metadata.get("demo_mode")) or _to_bool(record.get("demo_mode"))
    not_strategy = _to_bool(metadata.get("not_strategy_recommendation")) or _to_bool(record.get("not_strategy_recommendation"))
    if not (demo or not_strategy):
        return
    action = _string_or_empty(record.get("advisory_action") or metadata.get("advisory_action")).upper()
    if action not in DEMO_SAFE_ACTIONS:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                severity="ERROR",
                issue_code="DEMO_ACTION_UNSAFE",
                issue_message=f"Demo/not-strategy single-symbol review uses unsafe advisory action: {action}.",
                suggested_action="Regenerate demo advisory as DEMO_ONLY, WATCH, BLOCKED, or NO_ACTION.",
            )
        )
    if demo and not (_to_bool(metadata.get("not_strategy_recommendation")) and _to_bool(record.get("not_strategy_recommendation"))):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="DEMO_ACTION_UNSAFE",
                issue_message="Demo single-symbol review is missing not_strategy_recommendation=true.",
                suggested_action="Regenerate demo advisory with not_strategy_recommendation=true.",
            )
        )


def _check_not_found_safety(row: dict[str, Any], metadata: dict[str, Any], record: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    status = _string_or_empty(record.get("status") or metadata.get("status")).upper()
    action = _string_or_empty(record.get("advisory_action") or metadata.get("advisory_action")).upper()
    if status != "NOT_FOUND":
        return
    if action not in NOT_FOUND_SAFE_ACTIONS or action in UNSAFE_RECOMMENDATION_ACTIONS:
        issues.append(
            _issue(
                row,
                path_field="advisory_csv_path",
                severity="ERROR",
                issue_code="NOT_FOUND_WITH_RECOMMENDATION",
                issue_message=f"NOT_FOUND review has recommendation-like advisory action: {action}.",
                suggested_action="Regenerate missing-symbol advisory as NOT_FOUND with NO_ACTION.",
            )
        )


def _resolve_artifact_path(value: Any, base_dir: Path | None) -> Path | None:
    if not _present(value):
        return None
    path = Path(str(value))
    if path.exists() or path.is_absolute() or base_dir is None:
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    return path


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in SINGLE_SYMBOL_ADVISORY_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[SINGLE_SYMBOL_ADVISORY_INDEX_COLUMNS]
    return index[SINGLE_SYMBOL_ADVISORY_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    issues = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in issues.columns:
            issues[column] = ""
    if issues.empty:
        return issues[HEALTH_COLUMNS]
    return issues[HEALTH_COLUMNS].sort_values(["severity", "issue_code", "advisory_run_id"], na_position="last").reset_index(drop=True)


def _issue(
    row: dict[str, Any],
    *,
    path_field: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
    path_value: Any = None,
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported single-symbol advisory health issue_code: {issue_code}")
    return {
        "artifact_type": _string_or_empty(row.get("artifact_type", "SINGLE_SYMBOL_ADVISORY")) or "SINGLE_SYMBOL_ADVISORY",
        "advisory_run_id": _string_or_empty(row.get("advisory_run_id", "")),
        "symbol": _string_or_empty(row.get("symbol", "")),
        "path_field": path_field,
        "path_value": _string_or_empty(path_value if path_value is not None else row.get(path_field, "")),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _severity(value: str, cfg: SingleSymbolAdvisoryHealthSettings) -> str:
    severity = str(value).upper()
    if cfg.strict and severity == "WARN":
        return "ERROR"
    return severity


def _coerce_health_settings(settings: SingleSymbolAdvisoryHealthSettings | dict[str, Any] | None) -> SingleSymbolAdvisoryHealthSettings:
    if settings is None:
        return SingleSymbolAdvisoryHealthSettings()
    if isinstance(settings, SingleSymbolAdvisoryHealthSettings):
        return settings
    if isinstance(settings, dict):
        return SingleSymbolAdvisoryHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return SingleSymbolAdvisoryHealthSettings(**settings.model_dump())
    raise TypeError("settings must be SingleSymbolAdvisoryHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | SingleSymbolAdvisoryHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, SingleSymbolAdvisoryHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.single_symbol_advisory_health
    if isinstance(settings, Settings):
        return settings, settings.single_symbol_advisory_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, SingleSymbolAdvisoryHealthSettings):
        return project.model_copy(update={"single_symbol_advisory_health": settings}), settings
    if isinstance(settings, dict):
        payload = dict(project.single_symbol_advisory_health.model_dump())
        payload.update(settings)
        health_settings = SingleSymbolAdvisoryHealthSettings(**payload)
        return project.model_copy(update={"single_symbol_advisory_health": health_settings}), health_settings
    raise TypeError("settings must be Settings, SingleSymbolAdvisoryHealthSettings, dict, or None")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string_or_empty(value).strip().lower() in {"true", "1", "yes", "y"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _present(value: Any) -> bool:
    return _string_or_empty(value).strip() != ""


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
