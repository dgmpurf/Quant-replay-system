"""Local-only health checks for edited paper-review update templates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import PaperReviewTemplateHealthSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.paper_review import REVIEW_REASON_CODES, REVIEW_STATUSES


PAPER_REVIEW_TEMPLATE_HEALTH_LIMITATIONS = [
    "Checks local review update templates only.",
    "Does not apply review updates or approve trades.",
    "Does not place live orders or call broker APIs.",
    "Decision-aware checks require the matching decisions.csv to be supplied.",
]

REQUIRED_REVIEW_TEMPLATE_COLUMNS = [
    "decision_id",
    "manual_review_status",
    "manual_review_notes",
    "reviewer_id",
    "review_reason_code",
]

HEALTH_COLUMNS = [
    "row_number",
    "decision_id",
    "symbol",
    "severity",
    "issue_code",
    "issue_message",
    "expected_value",
    "actual_value",
    "suggested_action",
]

ISSUE_CODES = {
    "MISSING_REQUIRED_COLUMN",
    "MISSING_DECISION_ID",
    "UNKNOWN_DECISION_ID",
    "DUPLICATE_DECISION_ID",
    "INVALID_MANUAL_REVIEW_STATUS",
    "BLANK_MANUAL_REVIEW_STATUS",
    "INVALID_REVIEW_REASON_CODE",
    "BLANK_REASON_FOR_REVIEWED_STATUS",
    "MISSING_REVIEWER_ID",
    "REJECTED_WITHOUT_NOTES",
    "MANUAL_OVERRIDE_WITHOUT_NOTES",
    "APPROVED_NON_PASS_RISK",
    "APPROVED_LOW_SCORE",
    "REJECTED_HIGH_SCORE",
    "WATCH_ONLY_HIGH_SCORE",
    "DECISIONS_NOT_PROVIDED",
}


@dataclass(frozen=True)
class PaperReviewTemplateHealthArtifactPaths:
    artifact_dir: Path
    review_template_health_report: Path
    review_template_health_issues: Path
    review_template_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "review_template_health_report": self.review_template_health_report,
            "review_template_health_issues": self.review_template_health_issues,
            "review_template_health_summary": self.review_template_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperReviewTemplateHealthResult:
    status: str
    update_row_count: int
    decision_row_count: int
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


def check_review_template_health(
    updates: pd.DataFrame | str | Path,
    decisions: pd.DataFrame | str | Path | None = None,
    *,
    settings: Settings | PaperReviewTemplateHealthSettings | dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> PaperReviewTemplateHealthResult:
    """Validate an edited review_updates_template.csv before paper-review-decisions applies it."""

    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Paper review template health check cannot enable live trading or broker API access")

    updates_frame = _load_frame(updates, label="Review updates")
    decisions_frame = _load_optional_frame(decisions, label="Paper decisions")
    health_frame = build_review_template_health_frame(
        updates_frame,
        decisions=decisions_frame,
        settings=health_settings,
    )
    summary_frame = summarize_review_template_health(
        health_frame,
        update_row_count=len(updates_frame),
        decision_row_count=0 if decisions_frame is None else len(decisions_frame),
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_review_template_health_check_id(
        updates_frame,
        settings=health_settings,
    )
    paths = resolve_review_template_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    warnings = _result_warnings(status, decisions_frame, health_settings)
    audit_metadata = {
        "health_check_id": health_check_id,
        "update_row_count": len(updates_frame),
        "decision_row_count": 0 if decisions_frame is None else len(decisions_frame),
        "decisions_supplied": decisions_frame is not None,
        "strict": health_settings.strict,
        "config_version": health_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "review_template_health_only": True,
    }
    result = PaperReviewTemplateHealthResult(
        status=status,
        update_row_count=len(updates_frame),
        decision_row_count=0 if decisions_frame is None else len(decisions_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=PAPER_REVIEW_TEMPLATE_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_review_template_health_artifacts(result)
    _ = project_settings
    return result


def build_review_template_health_frame(
    updates: pd.DataFrame,
    decisions: pd.DataFrame | None = None,
    *,
    settings: PaperReviewTemplateHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build a health issue frame for an edited review update template."""

    cfg = _coerce_health_settings(settings)
    updates_frame = updates.copy(deep=True)
    decisions_frame = decisions.copy(deep=True) if decisions is not None else None
    issues: list[dict[str, Any]] = []

    missing_columns = [column for column in REQUIRED_REVIEW_TEMPLATE_COLUMNS if column not in updates_frame.columns]
    for column in missing_columns:
        issues.append(
            _issue(
                row_number="",
                decision_id="",
                symbol="",
                severity="ERROR",
                issue_code="MISSING_REQUIRED_COLUMN",
                issue_message=f"Review update template is missing required column: {column}.",
                expected_value=column,
                actual_value="",
                suggested_action="Regenerate the template or add the missing column before applying reviews.",
            )
        )
        updates_frame[column] = ""

    if decisions_frame is None and cfg.require_decisions_for_id_validation:
        issues.append(
            _issue(
                row_number="",
                decision_id="",
                symbol="",
                severity="WARN",
                issue_code="DECISIONS_NOT_PROVIDED",
                issue_message="No decisions were supplied, so decision_id validation could not be performed.",
                expected_value="decisions.csv",
                actual_value="",
                suggested_action="Run the health check with --decisions for decision-aware validation.",
            )
        )

    known_decisions = _decision_lookup(decisions_frame)
    decision_ids = updates_frame["decision_id"].map(_string_or_empty)
    duplicate_mask = decision_ids[decision_ids != ""].duplicated(keep=False)

    for idx, row in updates_frame.iterrows():
        row_number = int(idx) + 2
        record = row.to_dict()
        decision_id = _string_or_empty(record.get("decision_id"))
        symbol = _string_or_empty(record.get("symbol"))
        status = _string_or_empty(record.get("manual_review_status")).upper()
        reason = _string_or_empty(record.get("review_reason_code")).upper()
        reviewer = _string_or_empty(record.get("reviewer_id"))
        notes = _string_or_empty(record.get("manual_review_notes"))
        decision = known_decisions.get(decision_id)
        if decision is not None:
            symbol = _string_or_empty(decision.get("symbol")) or symbol

        if not decision_id:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="ERROR",
                    issue_code="MISSING_DECISION_ID",
                    issue_message="Review update row is missing decision_id.",
                    expected_value="non-empty decision_id",
                    actual_value="",
                    suggested_action="Fill decision_id from decisions.csv or remove the row.",
                )
            )
        elif decisions_frame is not None and decision_id not in known_decisions:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="ERROR",
                    issue_code="UNKNOWN_DECISION_ID",
                    issue_message=f"decision_id is not present in the supplied decisions: {decision_id}.",
                    expected_value="decision_id from decisions.csv",
                    actual_value=decision_id,
                    suggested_action="Use a decision_id from the matching decisions.csv.",
                )
            )

        if bool(duplicate_mask.get(idx, False)):
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity=_configured_severity(cfg.duplicate_update_severity, cfg),
                    issue_code="DUPLICATE_DECISION_ID",
                    issue_message=f"Duplicate review update for decision_id: {decision_id}.",
                    expected_value="one update per decision_id",
                    actual_value=decision_id,
                    suggested_action="Keep exactly one review update per decision_id.",
                )
            )

        if not status:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity=_configured_severity(cfg.blank_status_severity, cfg),
                    issue_code="BLANK_MANUAL_REVIEW_STATUS",
                    issue_message="manual_review_status is blank.",
                    expected_value=", ".join(sorted(REVIEW_STATUSES)),
                    actual_value="",
                    suggested_action="Set a valid manual_review_status before applying reviews.",
                )
            )
        elif status not in REVIEW_STATUSES:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="ERROR",
                    issue_code="INVALID_MANUAL_REVIEW_STATUS",
                    issue_message=f"manual_review_status is invalid: {status}.",
                    expected_value=", ".join(sorted(REVIEW_STATUSES)),
                    actual_value=status,
                    suggested_action="Use one of the allowed review statuses.",
                )
            )

        if reason and reason not in REVIEW_REASON_CODES:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity=_configured_severity(cfg.invalid_reason_code_severity, cfg),
                    issue_code="INVALID_REVIEW_REASON_CODE",
                    issue_message=f"review_reason_code is not a known code: {reason}.",
                    expected_value=", ".join(sorted(REVIEW_REASON_CODES)),
                    actual_value=reason,
                    suggested_action="Use a supported review reason code or OTHER.",
                )
            )
        if status in {"APPROVED_FOR_PAPER", "REJECTED", "WATCH_ONLY"} and not reason:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="WARN",
                    issue_code="BLANK_REASON_FOR_REVIEWED_STATUS",
                    issue_message=f"review_reason_code is blank for {status}.",
                    expected_value="review reason code",
                    actual_value="",
                    suggested_action="Add a reason code for the reviewed decision.",
                )
            )

        if not reviewer:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity=_configured_severity(cfg.missing_reviewer_severity, cfg),
                    issue_code="MISSING_REVIEWER_ID",
                    issue_message="reviewer_id is blank.",
                    expected_value="reviewer_id",
                    actual_value="",
                    suggested_action="Fill reviewer_id for auditability.",
                )
            )
        if status == "REJECTED" and not notes:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="WARN",
                    issue_code="REJECTED_WITHOUT_NOTES",
                    issue_message="Rejected decision has blank manual_review_notes.",
                    expected_value="manual notes",
                    actual_value="",
                    suggested_action="Add notes explaining why the decision was rejected.",
                )
            )
        if reason == "MANUAL_OVERRIDE" and not notes:
            issues.append(
                _issue(
                    row_number=row_number,
                    decision_id=decision_id,
                    symbol=symbol,
                    severity="WARN",
                    issue_code="MANUAL_OVERRIDE_WITHOUT_NOTES",
                    issue_message="MANUAL_OVERRIDE reason is used without manual notes.",
                    expected_value="manual notes",
                    actual_value="",
                    suggested_action="Document the manual override rationale.",
                )
            )

        if decision is not None:
            _append_decision_aware_issues(
                issues,
                row_number=row_number,
                decision_id=decision_id,
                symbol=symbol,
                status=status,
                decision=decision,
                settings=cfg,
            )

    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_review_template_health(
    health_frame: pd.DataFrame,
    *,
    update_row_count: int,
    decision_row_count: int = 0,
) -> pd.DataFrame:
    """Summarize review template health issues."""

    frame = _finalize_health_frame(health_frame)
    issue_count = len(frame)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    info_count = int((frame["severity"] == "INFO").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else "WARN" if warning_count else "PASS"
    rows = [
        {
            "status": status,
            "update_row_count": update_row_count,
            "decision_row_count": decision_row_count,
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
                    "update_row_count": update_row_count,
                    "decision_row_count": decision_row_count,
                    "issue_count": len(group),
                    "error_count": int((group["severity"] == "ERROR").sum()),
                    "warning_count": int((group["severity"] == "WARN").sum()),
                    "info_count": int((group["severity"] == "INFO").sum()),
                    "issue_code": issue_code,
                }
            )
    return pd.DataFrame(rows)


def resolve_review_template_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> PaperReviewTemplateHealthArtifactPaths:
    """Resolve stable review template health artifact paths."""

    artifact_dir = Path(output_dir) / health_check_id
    return PaperReviewTemplateHealthArtifactPaths(
        artifact_dir=artifact_dir,
        review_template_health_report=artifact_dir / "review_template_health_report.md",
        review_template_health_issues=artifact_dir / "review_template_health_issues.csv",
        review_template_health_summary=artifact_dir / "review_template_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_review_template_health_artifacts(result: PaperReviewTemplateHealthResult) -> dict[str, Path]:
    """Write review template health issues, summary, report, and metadata."""

    paths = PaperReviewTemplateHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.health_frame, paths.review_template_health_issues)
    _export_dataframe(result.summary_frame, paths.review_template_health_summary)
    metadata = build_review_template_health_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.review_template_health_report.write_text(
        render_review_template_health_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_review_template_health_metadata(
    result: PaperReviewTemplateHealthResult,
    paths: PaperReviewTemplateHealthArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for review template health artifacts."""

    return {
        "health_check_id": result.health_check_id,
        "created_at": "1970-01-01T00:00:00+00:00",
        "status": result.status,
        "update_row_count": result.update_row_count,
        "decision_row_count": result.decision_row_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "config_summary": {
            "strict": bool(result.audit_metadata.get("strict", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "review_template_health_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_review_template_health_report(
    result: PaperReviewTemplateHealthResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown review template health report."""

    _ = metadata
    lines = [
        f"# Paper Review Template Health Check: {result.health_check_id}",
        "",
        "No broker or live trading integration was invoked. This health check validates local review template files only.",
        "",
        "## Health Summary",
        "",
        _markdown_table(
            result.summary_frame,
            [
                "status",
                "update_row_count",
                "decision_row_count",
                "issue_count",
                "error_count",
                "warning_count",
                "info_count",
                "issue_code",
            ],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.health_frame,
            [
                "row_number",
                "decision_id",
                "symbol",
                "severity",
                "issue_code",
                "issue_message",
                "suggested_action",
            ],
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


def write_review_template_health_report(
    result: PaperReviewTemplateHealthResult,
    path: str | Path | None = None,
) -> Path:
    """Write only the markdown review template health report."""

    paths = PaperReviewTemplateHealthArtifactPaths(**result.artifact_paths)
    report_path = Path(path) if path is not None else paths.review_template_health_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_review_template_health_report(result), encoding="utf-8")
    return report_path


def generate_review_template_health_check_id(
    updates: pd.DataFrame,
    *,
    settings: PaperReviewTemplateHealthSettings,
) -> str:
    """Generate a deterministic health-check id from update payload and settings."""

    frame = updates.copy(deep=True)
    for column in ["decision_id", "manual_review_status", "reviewer_id", "review_reason_code"]:
        if column not in frame.columns:
            frame[column] = ""
    payload = {
        "updates": _stable_records(frame[["decision_id", "manual_review_status", "reviewer_id", "review_reason_code"]]),
        "duplicate_update_severity": settings.duplicate_update_severity,
        "invalid_reason_code_severity": settings.invalid_reason_code_severity,
        "blank_status_severity": settings.blank_status_severity,
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def _append_decision_aware_issues(
    issues: list[dict[str, Any]],
    *,
    row_number: int,
    decision_id: str,
    symbol: str,
    status: str,
    decision: dict[str, Any],
    settings: PaperReviewTemplateHealthSettings,
) -> None:
    score = _float_or_none(decision.get("final_score"))
    risk_status = _string_or_empty(decision.get("risk_precheck_status")).upper()
    if status == "APPROVED_FOR_PAPER" and risk_status and risk_status != "PASS":
        issues.append(
            _issue(
                row_number=row_number,
                decision_id=decision_id,
                symbol=symbol,
                severity=_configured_severity(settings.approve_non_pass_risk_severity, settings),
                issue_code="APPROVED_NON_PASS_RISK",
                issue_message=f"Decision approved while risk_precheck_status is {risk_status}.",
                expected_value="PASS",
                actual_value=risk_status,
                suggested_action="Review the risk reason before approving for paper fills.",
            )
        )
    if status == "APPROVED_FOR_PAPER" and score is not None and score < settings.low_score_approval_threshold:
        issues.append(
            _issue(
                row_number=row_number,
                decision_id=decision_id,
                symbol=symbol,
                severity=_configured_severity(settings.low_score_approval_severity, settings),
                issue_code="APPROVED_LOW_SCORE",
                issue_message=f"Decision approved with final_score below {settings.low_score_approval_threshold}.",
                expected_value=f">= {settings.low_score_approval_threshold}",
                actual_value=score,
                suggested_action="Confirm that the approval is intentional.",
            )
        )
    if status == "REJECTED" and score is not None and score >= settings.high_score_threshold:
        issues.append(
            _issue(
                row_number=row_number,
                decision_id=decision_id,
                symbol=symbol,
                severity=_configured_severity(settings.rejected_high_score_severity, settings),
                issue_code="REJECTED_HIGH_SCORE",
                issue_message=f"High-score decision was rejected: final_score {score}.",
                expected_value=f"< {settings.high_score_threshold}",
                actual_value=score,
                suggested_action="Confirm rejection rationale is documented.",
            )
        )
    if status == "WATCH_ONLY" and score is not None and score >= settings.high_score_threshold:
        issues.append(
            _issue(
                row_number=row_number,
                decision_id=decision_id,
                symbol=symbol,
                severity=_configured_severity(settings.watch_high_score_severity, settings),
                issue_code="WATCH_ONLY_HIGH_SCORE",
                issue_message=f"High-score decision was set to WATCH_ONLY: final_score {score}.",
                expected_value=f"< {settings.high_score_threshold}",
                actual_value=score,
                suggested_action="Confirm watch-only rationale is intentional.",
            )
        )


def _decision_lookup(decisions: pd.DataFrame | None) -> dict[str, dict[str, Any]]:
    if decisions is None:
        return {}
    frame = decisions.copy(deep=True)
    if "decision_id" not in frame.columns:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict("records"):
        decision_id = _string_or_empty(row.get("decision_id"))
        if decision_id:
            rows[decision_id] = row
    return rows


def _result_warnings(
    status: str,
    decisions_frame: pd.DataFrame | None,
    settings: PaperReviewTemplateHealthSettings,
) -> list[str]:
    warnings: list[str] = []
    if status == "WARN":
        warnings.append("Review template health check produced warnings.")
    if decisions_frame is None:
        warnings.append("No decisions were supplied; unknown decision_id and decision-aware risk checks were skipped.")
    if settings.enable_live_trading or settings.enable_broker_api:
        warnings.append("Invalid live/broker setting detected.")
    return warnings


def _load_frame(value: pd.DataFrame | str | Path, *, label: str) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"{label} CSV not found: {path}")
    return read_csv_preserve_symbol_columns(path)


def _load_optional_frame(value: pd.DataFrame | str | Path | None, *, label: str) -> pd.DataFrame | None:
    if value is None:
        return None
    return _load_frame(value, label=label)


def _configured_severity(value: str, settings: PaperReviewTemplateHealthSettings) -> str:
    if settings.strict and str(value).upper() == "WARN":
        return "ERROR"
    return str(value).upper()


def _issue(
    *,
    row_number: int | str,
    decision_id: Any,
    symbol: Any,
    severity: str,
    issue_code: str,
    issue_message: str,
    expected_value: Any,
    actual_value: Any,
    suggested_action: str,
) -> dict[str, Any]:
    if issue_code not in ISSUE_CODES:
        raise ValueError(f"Unsupported review template health issue_code: {issue_code}")
    return {
        "row_number": row_number,
        "decision_id": _string_or_empty(decision_id),
        "symbol": _string_or_empty(symbol),
        "severity": str(severity).upper(),
        "issue_code": issue_code,
        "issue_message": issue_message,
        "expected_value": _string_or_empty(expected_value),
        "actual_value": _string_or_empty(actual_value),
        "suggested_action": suggested_action,
    }


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    health = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in health.columns:
            health[column] = ""
    if health.empty:
        return health[HEALTH_COLUMNS]
    return health[HEALTH_COLUMNS].sort_values(
        ["severity", "decision_id", "issue_code", "row_number"],
        na_position="last",
    ).reset_index(drop=True)


def _coerce_health_settings(
    settings: PaperReviewTemplateHealthSettings | dict[str, Any] | None,
) -> PaperReviewTemplateHealthSettings:
    if settings is None:
        return PaperReviewTemplateHealthSettings()
    if isinstance(settings, PaperReviewTemplateHealthSettings):
        return settings
    if isinstance(settings, dict):
        return PaperReviewTemplateHealthSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperReviewTemplateHealthSettings(**settings.model_dump())
    raise TypeError("settings must be PaperReviewTemplateHealthSettings, dict, or None")


def _resolve_settings(
    settings: Settings | PaperReviewTemplateHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, PaperReviewTemplateHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_review_template_health
    if isinstance(settings, Settings):
        return settings, settings.paper_review_template_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, PaperReviewTemplateHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.paper_review_template_health.model_dump())
        for key, value in settings.items():
            if key == "paper_review_template_health" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, PaperReviewTemplateHealthSettings(**payload)
    raise TypeError("settings must be Settings, PaperReviewTemplateHealthSettings, dict, or None")


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


def _stable_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    sort_columns = [column for column in ["decision_id", "manual_review_status", "reviewer_id"] if column in frame.columns]
    export = frame.copy(deep=True)
    if sort_columns:
        export = export.sort_values(sort_columns, na_position="last")
    return [_json_safe(record) for record in export.to_dict("records")]


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _float_or_none(value: Any) -> float | None:
    if not _present(value):
        return None
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


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


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
