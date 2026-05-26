"""Local-only health checks for signal advisory artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import Settings, SignalAdvisoryHealthSettings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.signal_advisory import SIGNAL_COLUMNS
from quant_replay_system.signal_advisory_index import (
    SIGNAL_ADVISORY_INDEX_COLUMNS,
    scan_signal_advisory_artifacts,
)


SIGNAL_ADVISORY_HEALTH_LIMITATIONS = [
    "Checks local signal advisory artifacts referenced by the index only.",
    "Does not regenerate candidates, signals, or alert previews.",
    "Does not send messages, place orders, call brokers, or enable live trading.",
    "Does not validate strategy quality or approve demo signals as recommendations.",
]

HEALTH_COLUMNS = [
    "artifact_type",
    "signal_run_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_METADATA",
    "MISSING_SIGNALS_CSV",
    "MISSING_REPORT",
    "MISSING_ALERT_PREVIEW",
    "MISSING_REQUIRED_COLUMNS",
    "SYMBOL_FORMAT_ERROR",
    "AUTO_ORDER_ALLOWED",
    "MISSING_MANUAL_CONFIRMATION",
    "DEMO_SIGNAL_ACTION_UNSAFE",
    "MISSING_NO_LIVE_TRADING_STATEMENT",
    "MESSAGE_DELIVERY_DETECTED",
    "STALE_OR_PARTIAL_SIGNAL_RUN",
}

REQUIRED_PATH_FIELDS = [
    "metadata_path",
    "signals_csv_path",
    "report_path",
    "alert_preview_path",
]

DEMO_SAFE_ACTIONS = {"DEMO_ONLY", "WATCH"}


@dataclass(frozen=True)
class SignalAdvisoryHealthPaths:
    artifact_dir: Path
    signal_advisory_health_report: Path
    signal_advisory_health_issues: Path
    signal_advisory_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "signal_advisory_health_report": self.signal_advisory_health_report,
            "signal_advisory_health_issues": self.signal_advisory_health_issues,
            "signal_advisory_health_summary": self.signal_advisory_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SignalAdvisoryHealthResult:
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


def check_signal_advisory_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | SignalAdvisoryHealthSettings | dict[str, Any] | None = None,
) -> SignalAdvisoryHealthResult:
    """Check indexed signal advisory artifacts for safety and file health."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Signal advisory health check cannot enable live trading or broker API access")

    index_frame, index_source, base_dir, load_warnings, load_issues = _load_index_for_health(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
    )
    checked_count = len(index_frame)
    health_frame = build_signal_advisory_health_frame(
        index_frame,
        base_dir=base_dir,
        settings=health_settings,
    )
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_signal_advisory_health(health_frame, checked_artifact_count=checked_count)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_signal_advisory_health_check_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_signal_advisory_health_paths(
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
        "signal_advisory_artifacts_only": True,
    }
    result = SignalAdvisoryHealthResult(
        status=status,
        checked_artifact_count=checked_count,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=SIGNAL_ADVISORY_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_signal_advisory_health_artifacts(result)
    _ = project_settings
    return result


def build_signal_advisory_health_frame(
    index_df: pd.DataFrame,
    *,
    base_dir: str | Path | None = None,
    settings: SignalAdvisoryHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build one issue row per signal advisory artifact problem."""

    cfg = _coerce_health_settings(settings)
    index_frame = _prepare_index_frame(index_df)
    base_path = Path(base_dir) if base_dir is not None else None
    issues: list[dict[str, Any]] = []

    for row in index_frame.to_dict("records"):
        if _string_or_empty(row.get("artifact_type")).upper() != "SIGNAL_ADVISORY":
            continue
        resolved_paths = {
            field: _resolve_artifact_path(row.get(field), base_path)
            for field in REQUIRED_PATH_FIELDS
        }
        metadata = _check_metadata(row, resolved_paths["metadata_path"], issues, cfg)
        signals = _check_signals(row, resolved_paths["signals_csv_path"], issues, cfg)
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
        if metadata is not None and signals is not None:
            _check_signal_contract(row, metadata, signals, issues, cfg)

    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_signal_advisory_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
) -> pd.DataFrame:
    """Summarize signal advisory health issues."""

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


def resolve_signal_advisory_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> SignalAdvisoryHealthPaths:
    """Resolve stable signal advisory health artifact paths."""

    artifact_dir = Path(output_dir) / health_check_id
    return SignalAdvisoryHealthPaths(
        artifact_dir=artifact_dir,
        signal_advisory_health_report=artifact_dir / "signal_advisory_health_report.md",
        signal_advisory_health_issues=artifact_dir / "signal_advisory_health_issues.csv",
        signal_advisory_health_summary=artifact_dir / "signal_advisory_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_signal_advisory_health_artifacts(result: SignalAdvisoryHealthResult) -> dict[str, Path]:
    """Write signal advisory health issues, summary, report, and metadata."""

    paths = SignalAdvisoryHealthPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.signal_advisory_health_issues)
    _export_dataframe(result.summary_frame, paths.signal_advisory_health_summary)
    metadata = build_signal_advisory_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.signal_advisory_health_report.write_text(
        render_signal_advisory_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_signal_advisory_health_metadata(
    result: SignalAdvisoryHealthResult,
    paths: SignalAdvisoryHealthPaths,
) -> dict[str, Any]:
    """Build metadata for signal advisory health artifacts."""

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
        "signal_advisory_artifacts_only": True,
        "no_live_trading_statement": "No live trading, broker API, order placement, or message delivery was invoked.",
    }


def render_signal_advisory_health_report(
    result: SignalAdvisoryHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render signal advisory health markdown."""

    _ = metadata
    lines = [
        f"# Signal Advisory Artifact Health Check: {result.health_check_id}",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked. This health check validates local signal advisory artifacts only.",
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
            ["artifact_type", "signal_run_id", "path_field", "severity", "issue_code", "issue_message", "suggested_action"],
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


def generate_signal_advisory_health_check_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: SignalAdvisoryHealthSettings,
) -> str:
    """Generate a deterministic health-check id from index identity and settings."""

    frame = _prepare_index_frame(index_frame)
    payload = {
        "index_source": index_source,
        "signal_run_ids": sorted(str(value) for value in frame.get("signal_run_id", pd.Series(dtype="object")).dropna()),
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
    settings: SignalAdvisoryHealthSettings,
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    issues: list[dict[str, Any]] = []
    if index_df is not None:
        return _prepare_index_frame(index_df), "dataframe", None, warnings, issues
    if index_path is not None:
        return _load_index_path(Path(index_path), warnings, issues)
    if root is not None:
        root_path = Path(root)
        return scan_signal_advisory_artifacts(root_path), str(root_path), None, warnings, issues
    if settings.index_path.exists():
        return _load_index_path(settings.index_path, warnings, issues)
    warnings.append(f"Index path not found; scanning root instead: {settings.index_path}")
    return scan_signal_advisory_artifacts(settings.root_dir), str(settings.root_dir), None, warnings, issues


def _load_index_path(
    path: Path,
    warnings: list[str],
    issues: list[dict[str, Any]],
) -> tuple[pd.DataFrame, str, Path | None, list[str], list[dict[str, Any]]]:
    try:
        frame = pd.read_csv(path, dtype={"signal_run_id": str})
    except Exception as exc:
        issues.append(
            _issue(
                {"artifact_type": "", "signal_run_id": ""},
                path_field="index_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message=f"Could not read signal advisory index CSV: {exc}",
                suggested_action="Regenerate signal-advisory-index.",
            )
        )
        return _prepare_index_frame(pd.DataFrame()), str(path), path.parent, warnings, issues
    return _prepare_index_frame(frame), str(path), path.parent, warnings, issues


def _check_metadata(
    row: dict[str, Any],
    path: Path | None,
    issues: list[dict[str, Any]],
    cfg: SignalAdvisoryHealthSettings,
) -> dict[str, Any] | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_METADATA",
                issue_message="Signal advisory metadata.json is missing.",
                suggested_action="Rerun signal-advisory for this candidates artifact.",
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
                issue_message=f"Signal advisory metadata.json is unreadable: {exc}",
                suggested_action="Regenerate the signal advisory artifact.",
            )
        )
        _ = cfg
        return None


def _check_signals(
    row: dict[str, Any],
    path: Path | None,
    issues: list[dict[str, Any]],
    cfg: SignalAdvisoryHealthSettings,
) -> pd.DataFrame | None:
    if path is None or not path.exists():
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_SIGNALS_CSV",
                issue_message="signals.csv is missing.",
                suggested_action="Rerun signal-advisory.",
            )
        )
        return None
    try:
        signals = read_csv_preserve_symbol_columns(path)
    except Exception as exc:
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_SIGNALS_CSV",
                issue_message=f"signals.csv is unreadable: {exc}",
                suggested_action="Regenerate the signal advisory artifact.",
            )
        )
        return None
    missing = [column for column in SIGNAL_COLUMNS if column not in signals.columns]
    if missing:
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                path_value=path,
                severity="ERROR",
                issue_code="MISSING_REQUIRED_COLUMNS",
                issue_message=f"signals.csv is missing required columns: {', '.join(missing)}",
                suggested_action="Regenerate signals.csv with the current signal advisory contract.",
            )
        )
    _ = cfg
    return signals


def _check_markdown(
    row: dict[str, Any],
    field: str,
    path: Path | None,
    issue_code: str,
    issues: list[dict[str, Any]],
    cfg: SignalAdvisoryHealthSettings,
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
            suggested_action="Regenerate signal advisory artifacts.",
        )
    )


def _check_signal_contract(
    row: dict[str, Any],
    metadata: dict[str, Any],
    signals: pd.DataFrame,
    issues: list[dict[str, Any]],
    cfg: SignalAdvisoryHealthSettings,
) -> None:
    signal_run_id = _string_or_empty(row.get("signal_run_id"))
    metadata_count = _to_int(metadata.get("signal_count"))
    if metadata_count is not None and metadata_count != len(signals):
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="WARN",
                issue_code="STALE_OR_PARTIAL_SIGNAL_RUN",
                issue_message=f"metadata signal_count={metadata_count} does not match signals.csv rows={len(signals)}.",
                suggested_action="Regenerate signal-advisory artifacts from the source candidates.csv.",
            )
        )

    if _to_bool(metadata.get("auto_order_allowed")):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="AUTO_ORDER_ALLOWED",
                issue_message="metadata sets auto_order_allowed=true.",
                suggested_action="Regenerate the artifact with auto_order_allowed=false.",
            )
        )
    if not _to_bool(metadata.get("requires_manual_confirmation", True)):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MISSING_MANUAL_CONFIRMATION",
                issue_message="metadata does not require manual confirmation.",
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
    if any(_to_bool(metadata.get(key)) for key in ["message_sent", "message_delivery_enabled", "alert_delivery_enabled"]):
        issues.append(
            _issue(
                row,
                path_field="metadata_path",
                severity="ERROR",
                issue_code="MESSAGE_DELIVERY_DETECTED",
                issue_message="metadata indicates message delivery or message sending.",
                suggested_action="Do not use this artifact as a local-only preview; investigate delivery state.",
            )
        )

    if signals is None or signals.empty:
        return
    _check_symbol_integrity(row, signals, issues)
    _check_signal_safety_columns(row, signals, issues)
    _check_demo_action_safety(row, metadata, signals, issues)
    _ = cfg, signal_run_id


def _check_symbol_integrity(row: dict[str, Any], signals: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "symbol" not in signals.columns:
        return
    for symbol in signals["symbol"].dropna().astype(str):
        normalized = normalize_symbol_value(symbol)
        if symbol.strip() != normalized and normalized.isdigit() and len(normalized) == 6:
            issues.append(
                _issue(
                    row,
                    path_field="signals_csv_path",
                    severity="ERROR",
                    issue_code="SYMBOL_FORMAT_ERROR",
                    issue_message=f"Signal symbol appears to have lost leading-zero formatting: {symbol!r}.",
                    suggested_action="Regenerate signals.csv preserving symbol columns as strings.",
                )
            )
            return


def _check_signal_safety_columns(row: dict[str, Any], signals: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "auto_order_allowed" in signals.columns and signals["auto_order_allowed"].map(_to_bool).any():
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="ERROR",
                issue_code="AUTO_ORDER_ALLOWED",
                issue_message="One or more signals set auto_order_allowed=true.",
                suggested_action="Regenerate signals with auto_order_allowed=false.",
            )
        )
    if "requires_manual_confirmation" in signals.columns and not signals["requires_manual_confirmation"].map(_to_bool).all():
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="ERROR",
                issue_code="MISSING_MANUAL_CONFIRMATION",
                issue_message="One or more signals do not require manual confirmation.",
                suggested_action="Regenerate signals with requires_manual_confirmation=true.",
            )
        )
    missing_no_live = False
    if "no_live_trading" in signals.columns and not signals["no_live_trading"].map(_to_bool).all():
        missing_no_live = True
    if "no_broker_api" in signals.columns and not signals["no_broker_api"].map(_to_bool).all():
        missing_no_live = True
    if missing_no_live:
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="ERROR",
                issue_code="MISSING_NO_LIVE_TRADING_STATEMENT",
                issue_message="One or more signals are missing no_live_trading=true or no_broker_api=true.",
                suggested_action="Regenerate signals with explicit local-only safety flags.",
            )
        )


def _check_demo_action_safety(
    row: dict[str, Any],
    metadata: dict[str, Any],
    signals: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    metadata_demo = _to_bool(metadata.get("demo_mode")) or _to_bool(metadata.get("not_strategy_recommendation"))
    demo_mask = pd.Series([metadata_demo] * len(signals), index=signals.index)
    if "demo_mode" in signals.columns:
        demo_mask = demo_mask | signals["demo_mode"].map(_to_bool)
    if "not_strategy_recommendation" in signals.columns:
        demo_mask = demo_mask | signals["not_strategy_recommendation"].map(_to_bool)
    if not demo_mask.any():
        return
    actions = signals.loc[demo_mask, "advisory_action"].astype(str).str.upper() if "advisory_action" in signals.columns else pd.Series(dtype="object")
    unsafe = sorted(set(action for action in actions if action not in DEMO_SAFE_ACTIONS))
    if unsafe:
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="ERROR",
                issue_code="DEMO_SIGNAL_ACTION_UNSAFE",
                issue_message=f"Demo/not-strategy signals use unsafe advisory actions: {unsafe}.",
                suggested_action="Regenerate demo signals as DEMO_ONLY or WATCH only.",
            )
        )
    if "not_strategy_recommendation" in signals.columns and not signals.loc[demo_mask, "not_strategy_recommendation"].map(_to_bool).all():
        issues.append(
            _issue(
                row,
                path_field="signals_csv_path",
                severity="ERROR",
                issue_code="DEMO_SIGNAL_ACTION_UNSAFE",
                issue_message="Demo signals are missing not_strategy_recommendation=true.",
                suggested_action="Regenerate demo signals with not_strategy_recommendation=true.",
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
    for column in SIGNAL_ADVISORY_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[SIGNAL_ADVISORY_INDEX_COLUMNS]
    return index[SIGNAL_ADVISORY_INDEX_COLUMNS].reset_index(drop=True)


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    issues = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in issues.columns:
            issues[column] = ""
    if issues.empty:
        return issues[HEALTH_COLUMNS]
    return issues[HEALTH_COLUMNS].sort_values(["severity", "issue_code", "signal_run_id"], na_position="last").reset_index(drop=True)


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
        raise ValueError(f"Unsupported signal advisory health issue_code: {issue_code}")
    return {
        "artifact_type": _string_or_empty(row.get("artifact_type", "SIGNAL_ADVISORY")) or "SIGNAL_ADVISORY",
        "signal_run_id": _string_or_empty(row.get("signal_run_id", "")),
        "path_field": path_field,
        "path_value": _string_or_empty(path_value if path_value is not None else row.get(path_field, "")),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _severity(value: str, cfg: SignalAdvisoryHealthSettings) -> str:
    severity = str(value).upper()
    if cfg.strict and severity == "WARN":
        return "ERROR"
    return severity


def _coerce_health_settings(settings: SignalAdvisoryHealthSettings | dict[str, Any] | None) -> SignalAdvisoryHealthSettings:
    if settings is None:
        return SignalAdvisoryHealthSettings()
    if isinstance(settings, SignalAdvisoryHealthSettings):
        return settings
    if isinstance(settings, dict):
        return SignalAdvisoryHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return SignalAdvisoryHealthSettings(**settings.model_dump())
    raise TypeError("settings must be SignalAdvisoryHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | SignalAdvisoryHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, SignalAdvisoryHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.signal_advisory_health
    if isinstance(settings, Settings):
        return settings, settings.signal_advisory_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, SignalAdvisoryHealthSettings):
        return project.model_copy(update={"signal_advisory_health": settings}), settings
    if isinstance(settings, dict):
        payload = dict(project.signal_advisory_health.model_dump())
        payload.update(settings)
        health_settings = SignalAdvisoryHealthSettings(**payload)
        return project.model_copy(update={"signal_advisory_health": health_settings}), health_settings
    raise TypeError("settings must be Settings, SignalAdvisoryHealthSettings, dict, or None")


def _to_int(value: Any) -> int | None:
    if not _present(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _string_or_empty(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


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


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


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
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
