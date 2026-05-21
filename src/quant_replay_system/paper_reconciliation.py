"""Reconcile manual paper fills against paper-trading decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import (
    PaperReconciliationSettings,
    PaperTradingSettings,
    Settings,
    load_settings,
)


RECONCILIATION_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Reconciliation checks manual hypothetical fills, not broker confirmations.",
    "Cash and oversell checks are simplified and single-currency.",
    "Corporate actions, dividends, financing, and complete exchange fee schedules are not modeled.",
]

REQUIRED_FILL_COLUMNS = [
    "fill_id",
    "decision_id",
    "symbol",
    "side",
    "fill_date",
    "fill_price",
    "quantity",
    "gross_notional",
    "fees",
    "slippage",
    "net_cash_flow",
    "fill_source",
    "manual_notes",
]

ISSUE_CODES = {
    "UNKNOWN_DECISION_ID",
    "SYMBOL_MISMATCH",
    "DECISION_NOT_APPROVED",
    "INVALID_SIDE",
    "NON_POSITIVE_QUANTITY",
    "NON_POSITIVE_FILL_PRICE",
    "GROSS_NOTIONAL_MISMATCH",
    "BUY_CASH_FLOW_SIGN_ERROR",
    "SELL_CASH_FLOW_SIGN_ERROR",
    "OVERSELL",
    "NEGATIVE_CASH",
    "DUPLICATE_FILL_ID",
    "MISSING_REQUIRED_COLUMN",
}


@dataclass(frozen=True)
class PaperReconciliationArtifactPaths:
    artifact_dir: Path
    reconciliation_report: Path
    reconciliation_issues: Path
    reconciliation_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "reconciliation_report": self.reconciliation_report,
            "reconciliation_issues": self.reconciliation_issues,
            "reconciliation_summary": self.reconciliation_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperReconciliationResult:
    status: str
    issue_count: int
    error_count: int
    warning_count: int
    reconciliation_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    reconciliation_id: str
    audit_metadata: dict[str, Any]


def reconcile_paper_fills(
    decisions: pd.DataFrame | str | Path,
    fills: pd.DataFrame | str | Path,
    settings: Settings | PaperTradingSettings | PaperReconciliationSettings | dict[str, Any] | None = None,
    initial_cash: float | None = None,
) -> PaperReconciliationResult:
    """Reconcile paper fills against decisions and write optional artifacts."""

    project_settings, paper_settings, reconciliation_settings = _resolve_settings(settings)
    if paper_settings.enable_live_trading or paper_settings.enable_broker_api:
        raise ValueError("Paper reconciliation cannot enable live trading or broker API access")
    if reconciliation_settings.enable_live_trading or reconciliation_settings.enable_broker_api:
        raise ValueError("Paper reconciliation cannot enable live trading or broker API access")

    decisions_frame = _prepare_decisions(_load_frame(decisions))
    fills_raw = _load_frame(fills)
    cash = float(initial_cash if initial_cash is not None else paper_settings.initial_paper_cash)
    reconciliation_frame = build_reconciliation_frame(
        decisions_frame,
        fills_raw,
        paper_settings=paper_settings,
        reconciliation_settings=reconciliation_settings,
        initial_cash=cash,
    )
    summary_frame = summarize_reconciliation(reconciliation_frame)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    reconciliation_id = generate_reconciliation_id(
        decisions_frame,
        fills_raw,
        config_version=reconciliation_settings.config_version,
    )
    paths = resolve_reconciliation_artifact_paths(reconciliation_settings.output_dir, reconciliation_id)
    warnings = []
    if fills_raw.empty:
        warnings.append("No fills supplied for reconciliation.")
    audit_metadata = {
        "reconciliation_id": reconciliation_id,
        "decision_rows": len(decisions_frame),
        "fill_rows": len(fills_raw),
        "status": status,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    result = PaperReconciliationResult(
        status=status,
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        reconciliation_frame=reconciliation_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=RECONCILIATION_LIMITATIONS,
        reconciliation_id=reconciliation_id,
        audit_metadata=audit_metadata,
    )
    if reconciliation_settings.write_artifacts:
        write_reconciliation_artifacts(result)
    return result


def build_reconciliation_frame(
    decisions: pd.DataFrame,
    fills: pd.DataFrame,
    *,
    paper_settings: PaperTradingSettings | dict[str, Any] | None = None,
    reconciliation_settings: PaperReconciliationSettings | dict[str, Any] | None = None,
    initial_cash: float | None = None,
) -> pd.DataFrame:
    """Build one row per reconciliation issue."""

    paper_cfg = _coerce_paper_settings(paper_settings)
    reconciliation_cfg = _coerce_reconciliation_settings(reconciliation_settings)
    decision_frame = _prepare_decisions(decisions)
    fills_raw = fills.copy(deep=True) if fills is not None else pd.DataFrame()
    issues: list[dict[str, Any]] = []

    missing_columns = [column for column in REQUIRED_FILL_COLUMNS if column not in fills_raw.columns]
    for column in missing_columns:
        issues.append(
            _issue(
                severity="ERROR",
                issue_code="MISSING_REQUIRED_COLUMN",
                issue_message=f"Missing required fill column: {column}",
                expected_value=column,
                suggested_action="Add the missing column to the fills CSV/template.",
            )
        )

    fills_frame = _prepare_fills_for_checks(fills_raw)
    if fills_frame.empty:
        return _finalize_issues(pd.DataFrame(issues))

    decision_by_id = {
        str(row["decision_id"]): row
        for row in decision_frame.to_dict("records")
        if _present(row.get("decision_id"))
    }

    if "fill_id" in fills_frame.columns:
        duplicated = fills_frame.loc[
            fills_frame["fill_id"].notna()
            & (fills_frame["fill_id"].astype(str).str.strip() != "")
            & fills_frame["fill_id"].duplicated(keep=False)
        ]
        for _, row in duplicated.iterrows():
            issues.append(
                _issue_from_row(
                    row,
                    severity=reconciliation_cfg.duplicate_fill_id_severity,
                    issue_code="DUPLICATE_FILL_ID",
                    issue_message="Duplicate fill_id found.",
                    expected_value="unique fill_id",
                    actual_value=row.get("fill_id"),
                    suggested_action="Ensure each manual fill row has a unique fill_id.",
                )
            )

    for idx, row in fills_frame.iterrows():
        decision_id = str(row.get("decision_id", "")).strip()
        decision = decision_by_id.get(decision_id)
        if decision is None:
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="UNKNOWN_DECISION_ID",
                    issue_message="Fill decision_id does not exist in decisions.",
                    expected_value="known decision_id",
                    actual_value=decision_id,
                    suggested_action="Correct decision_id or regenerate the decision log.",
                )
            )
        else:
            expected_symbol = str(decision.get("symbol", "")).strip()
            actual_symbol = str(row.get("symbol", "")).strip()
            if expected_symbol and actual_symbol != expected_symbol:
                issues.append(
                    _issue_from_row(
                        row,
                        severity="ERROR",
                        issue_code="SYMBOL_MISMATCH",
                        issue_message="Fill symbol does not match decision symbol.",
                        expected_value=expected_symbol,
                        actual_value=actual_symbol,
                        suggested_action="Correct either the fill symbol or decision_id.",
                    )
                )
            status = str(decision.get("manual_review_status", "")).strip()
            if paper_cfg.require_approved_decision_for_fills and status != "APPROVED_FOR_PAPER":
                issues.append(
                    _issue_from_row(
                        row,
                        severity="ERROR",
                        issue_code="DECISION_NOT_APPROVED",
                        issue_message=f"Fill references a {status or 'UNKNOWN'} decision.",
                        expected_value="APPROVED_FOR_PAPER",
                        actual_value=status,
                        suggested_action="Approve the decision for paper trading or remove the fill.",
                    )
                )

        side = str(row.get("side", "")).upper().strip()
        if side not in {"BUY", "SELL"}:
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="INVALID_SIDE",
                    issue_message="Fill side must be BUY or SELL.",
                    expected_value="BUY or SELL",
                    actual_value=row.get("side"),
                    suggested_action="Correct the side value.",
                )
            )

        quantity = _to_float(row.get("quantity"))
        if quantity is None or quantity <= 0:
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="NON_POSITIVE_QUANTITY",
                    issue_message="Fill quantity must be positive.",
                    expected_value="quantity > 0",
                    actual_value=row.get("quantity"),
                    suggested_action="Correct the quantity.",
                )
            )

        fill_price = _to_float(row.get("fill_price"))
        if fill_price is None or fill_price <= 0:
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="NON_POSITIVE_FILL_PRICE",
                    issue_message="Fill price must be positive.",
                    expected_value="fill_price > 0",
                    actual_value=row.get("fill_price"),
                    suggested_action="Correct the fill price.",
                )
            )

        gross_notional = _to_float(row.get("gross_notional"))
        if quantity is not None and fill_price is not None and quantity > 0 and fill_price > 0:
            expected_gross = quantity * fill_price
            if gross_notional is None or abs(gross_notional - expected_gross) > max(0.01, abs(expected_gross) * 0.0001):
                issues.append(
                    _issue_from_row(
                        row,
                        severity="ERROR",
                        issue_code="GROSS_NOTIONAL_MISMATCH",
                        issue_message="gross_notional does not match fill_price * quantity.",
                        expected_value=expected_gross,
                        actual_value=row.get("gross_notional"),
                        suggested_action="Recalculate gross_notional.",
                    )
                )

        net_cash_flow = _to_float(row.get("net_cash_flow"))
        if side == "BUY" and (net_cash_flow is None or net_cash_flow >= 0):
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="BUY_CASH_FLOW_SIGN_ERROR",
                    issue_message="BUY net_cash_flow must be negative.",
                    expected_value="< 0",
                    actual_value=row.get("net_cash_flow"),
                    suggested_action="Make BUY net_cash_flow negative.",
                )
            )
        if side == "SELL" and (net_cash_flow is None or net_cash_flow <= 0):
            issues.append(
                _issue_from_row(
                    row,
                    severity="ERROR",
                    issue_code="SELL_CASH_FLOW_SIGN_ERROR",
                    issue_message="SELL net_cash_flow must be positive.",
                    expected_value="> 0",
                    actual_value=row.get("net_cash_flow"),
                    suggested_action="Make SELL net_cash_flow positive.",
                )
            )

    if not paper_cfg.allow_short_selling:
        issues.extend(_oversell_issues(fills_frame))
    if paper_cfg.prevent_negative_cash:
        issues.extend(
            _negative_cash_issues(
                fills_frame,
                initial_cash=float(initial_cash if initial_cash is not None else paper_cfg.initial_paper_cash),
                severity=reconciliation_cfg.negative_cash_severity,
            )
        )

    return _finalize_issues(pd.DataFrame(issues))


def summarize_reconciliation(reconciliation_frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize reconciliation issue rows."""

    frame = _finalize_issues(reconciliation_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
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
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def generate_reconciliation_id(
    decisions: pd.DataFrame,
    fills: pd.DataFrame,
    *,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic reconciliation id."""

    decision_frame = _prepare_decisions(decisions)
    fill_frame = fills.copy(deep=True) if fills is not None else pd.DataFrame()
    payload = {
        "decision_ids": sorted(str(value) for value in decision_frame.get("decision_id", pd.Series(dtype="object")).dropna().unique()),
        "fill_ids": sorted(str(value) for value in fill_frame.get("fill_id", pd.Series(dtype="object")).dropna().unique()),
        "symbols": sorted(
            set(str(value) for value in decision_frame.get("symbol", pd.Series(dtype="object")).dropna().unique())
            | set(str(value) for value in fill_frame.get("symbol", pd.Series(dtype="object")).dropna().unique())
        ),
        "config_version": config_version,
    }
    return _hash_payload(payload, length=10)


def resolve_reconciliation_artifact_paths(
    output_dir: str | Path,
    reconciliation_id: str,
) -> PaperReconciliationArtifactPaths:
    """Resolve stable artifact paths for reconciliation."""

    artifact_dir = Path(output_dir) / reconciliation_id
    return PaperReconciliationArtifactPaths(
        artifact_dir=artifact_dir,
        reconciliation_report=artifact_dir / "reconciliation_report.md",
        reconciliation_issues=artifact_dir / "reconciliation_issues.csv",
        reconciliation_summary=artifact_dir / "reconciliation_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_reconciliation_report(result: PaperReconciliationResult, path: str | Path | None = None) -> Path:
    """Write only the markdown reconciliation report."""

    paths = PaperReconciliationArtifactPaths(**result.artifact_paths)
    report_path = Path(path) if path is not None else paths.reconciliation_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_reconciliation_report(result), encoding="utf-8")
    return report_path


def write_reconciliation_artifacts(result: PaperReconciliationResult) -> dict[str, Path]:
    """Write reconciliation report, CSVs, and metadata."""

    paths = PaperReconciliationArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.reconciliation_frame, paths.reconciliation_issues)
    _export_dataframe(result.summary_frame, paths.reconciliation_summary)
    metadata = build_reconciliation_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.reconciliation_report.write_text(render_reconciliation_report(result), encoding="utf-8")
    return paths.as_dict()


def build_reconciliation_metadata(
    result: PaperReconciliationResult,
    paths: PaperReconciliationArtifactPaths,
) -> dict[str, Any]:
    """Build reconciliation metadata."""

    return {
        "reconciliation_id": result.reconciliation_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": result.status,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }


def render_reconciliation_report(result: PaperReconciliationResult) -> str:
    """Render reconciliation markdown."""

    lines = [
        f"# Paper Fill Reconciliation: {result.reconciliation_id}",
        "",
        "No broker or live trading integration was invoked. This report reconciles local manual paper fills only.",
        "",
        "## Summary",
        "",
        _markdown_table(result.summary_frame, ["status", "issue_count", "error_count", "warning_count", "info_count", "issue_code"]),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.reconciliation_frame,
            [
                "fill_id",
                "decision_id",
                "symbol",
                "side",
                "severity",
                "issue_code",
                "issue_message",
                "expected_value",
                "actual_value",
                "suggested_action",
            ],
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


def _resolve_settings(
    settings: Settings | PaperTradingSettings | PaperReconciliationSettings | dict[str, Any] | None,
) -> tuple[Settings, PaperTradingSettings, PaperReconciliationSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_trading, project.paper_reconciliation
    if isinstance(settings, Settings):
        return settings, settings.paper_trading, settings.paper_reconciliation
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, PaperTradingSettings):
        return project, settings, project.paper_reconciliation
    if isinstance(settings, PaperReconciliationSettings):
        return project, project.paper_trading, settings
    if isinstance(settings, dict):
        paper_payload = dict(project.paper_trading.model_dump())
        reconciliation_payload = dict(project.paper_reconciliation.model_dump())
        for key, value in settings.items():
            if key == "paper_trading" and isinstance(value, dict):
                paper_payload.update(value)
            elif key == "paper_reconciliation" and isinstance(value, dict):
                reconciliation_payload.update(value)
            elif key in paper_payload:
                paper_payload[key] = value
            elif key in reconciliation_payload:
                reconciliation_payload[key] = value
        return project, PaperTradingSettings(**paper_payload), PaperReconciliationSettings(**reconciliation_payload)
    raise TypeError("settings must be Settings, PaperTradingSettings, PaperReconciliationSettings, dict, or None")


def _coerce_paper_settings(settings: PaperTradingSettings | dict[str, Any] | None) -> PaperTradingSettings:
    if settings is None:
        return PaperTradingSettings()
    if isinstance(settings, PaperTradingSettings):
        return settings
    if isinstance(settings, dict):
        return PaperTradingSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperTradingSettings(**settings.model_dump())
    raise TypeError("paper_settings must be PaperTradingSettings, dict, or None")


def _coerce_reconciliation_settings(
    settings: PaperReconciliationSettings | dict[str, Any] | None,
) -> PaperReconciliationSettings:
    if settings is None:
        return PaperReconciliationSettings()
    if isinstance(settings, PaperReconciliationSettings):
        return settings
    if isinstance(settings, dict):
        return PaperReconciliationSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperReconciliationSettings(**settings.model_dump())
    raise TypeError("reconciliation_settings must be PaperReconciliationSettings, dict, or None")


def _load_frame(value: pd.DataFrame | str | Path) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)


def _prepare_decisions(decisions: pd.DataFrame) -> pd.DataFrame:
    frame = decisions.copy(deep=True)
    if frame.empty:
        return frame
    if "decision_date" in frame.columns:
        frame["decision_date"] = pd.to_datetime(frame["decision_date"], errors="coerce").dt.normalize()
    for column in ["decision_id", "symbol", "manual_review_status"]:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame.reset_index(drop=True)


def _prepare_fills_for_checks(fills: pd.DataFrame) -> pd.DataFrame:
    frame = fills.copy(deep=True)
    for column in REQUIRED_FILL_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    if frame.empty:
        return frame
    if "fill_date" in frame.columns:
        frame["fill_date"] = pd.to_datetime(frame["fill_date"], errors="coerce")
    for column in ["fill_price", "quantity", "gross_notional", "fees", "slippage", "net_cash_flow"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.reset_index(drop=True)


def _oversell_issues(fills: pd.DataFrame) -> list[dict[str, Any]]:
    issues = []
    positions: dict[str, float] = {}
    for _, row in fills.sort_values(["fill_date", "fill_id"], na_position="last").iterrows():
        side = str(row.get("side", "")).upper().strip()
        symbol = str(row.get("symbol", "")).strip()
        quantity = _to_float(row.get("quantity"))
        if not symbol or quantity is None or quantity <= 0:
            continue
        if side == "BUY":
            positions[symbol] = positions.get(symbol, 0.0) + quantity
        elif side == "SELL":
            available = positions.get(symbol, 0.0)
            if quantity > available + 1e-9:
                issues.append(
                    _issue_from_row(
                        row,
                        severity="ERROR",
                        issue_code="OVERSELL",
                        issue_message="SELL quantity exceeds available paper position.",
                        expected_value=f"<= {available:g}",
                        actual_value=quantity,
                        suggested_action="Reduce the sell quantity or add the missing prior buy fill.",
                    )
                )
            else:
                positions[symbol] = available - quantity
    return issues


def _negative_cash_issues(fills: pd.DataFrame, *, initial_cash: float, severity: str) -> list[dict[str, Any]]:
    issues = []
    cash = float(initial_cash)
    for _, row in fills.sort_values(["fill_date", "fill_id"], na_position="last").iterrows():
        net_cash_flow = _to_float(row.get("net_cash_flow"))
        if net_cash_flow is None:
            continue
        cash += net_cash_flow
        if cash < -1e-9:
            issues.append(
                _issue_from_row(
                    row,
                    severity=severity,
                    issue_code="NEGATIVE_CASH",
                    issue_message="Paper cash would become negative after this fill.",
                    expected_value="cash >= 0",
                    actual_value=cash,
                    suggested_action="Reduce buy quantity, add cash, or correct the fill ledger.",
                )
            )
    return issues


def _issue_from_row(
    row: pd.Series,
    *,
    severity: str,
    issue_code: str,
    issue_message: str,
    expected_value: Any = "",
    actual_value: Any = "",
    suggested_action: str = "",
) -> dict[str, Any]:
    return _issue(
        fill_id=row.get("fill_id", ""),
        decision_id=row.get("decision_id", ""),
        symbol=row.get("symbol", ""),
        side=row.get("side", ""),
        severity=severity,
        issue_code=issue_code,
        issue_message=issue_message,
        expected_value=expected_value,
        actual_value=actual_value,
        suggested_action=suggested_action,
    )


def _issue(
    *,
    fill_id: Any = "",
    decision_id: Any = "",
    symbol: Any = "",
    side: Any = "",
    severity: str,
    issue_code: str,
    issue_message: str,
    expected_value: Any = "",
    actual_value: Any = "",
    suggested_action: str = "",
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported reconciliation issue_code: {issue_code}")
    return {
        "fill_id": "" if not _present(fill_id) else str(fill_id),
        "decision_id": "" if not _present(decision_id) else str(decision_id),
        "symbol": "" if not _present(symbol) else str(symbol),
        "side": "" if not _present(side) else str(side),
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "expected_value": "" if expected_value is None else expected_value,
        "actual_value": "" if actual_value is None else actual_value,
        "suggested_action": suggested_action,
    }


def _finalize_issues(frame: pd.DataFrame) -> pd.DataFrame:
    issues = frame.copy(deep=True)
    for column in _issue_columns():
        if column not in issues.columns:
            issues[column] = pd.NA
    if issues.empty:
        return issues[_issue_columns()]
    return issues[_issue_columns()].sort_values(["severity", "issue_code", "fill_id"], na_position="last").reset_index(drop=True)


def _issue_columns() -> list[str]:
    return [
        "fill_id",
        "decision_id",
        "symbol",
        "side",
        "severity",
        "issue_code",
        "issue_message",
        "expected_value",
        "actual_value",
        "suggested_action",
    ]


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


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
