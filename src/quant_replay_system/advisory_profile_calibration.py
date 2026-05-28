"""Local advisory profile threshold calibration analysis."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


CALIBRATION_LABELS = [
    "REVIEW_BUY_CANDIDATE",
    "WATCH",
    "NO_ACTION",
    "BLOCKED",
    "DEMO_ONLY",
]

CALIBRATION_COLUMNS = [
    "calibration_run_id",
    "source_row_index",
    "symbol",
    "name",
    "instrument_type",
    "profile",
    "simulated_advisory_label",
    "final_score",
    "reviewed_buy_min_score",
    "watch_min_score",
    "risk_precheck_status",
    "risk_precheck_reason",
    "score_action",
    "action",
    "selection_profile",
    "demo_mode",
    "not_strategy_recommendation",
    "snapshot_quality_status",
    "data_quality_status",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
    "calibration_only",
    "not_trading_recommendation",
    "reason_summary",
    "issue_codes",
]

CALIBRATION_ISSUE_COLUMNS = [
    "calibration_run_id",
    "source_row_index",
    "symbol",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

CALIBRATION_SUMMARY_COLUMNS = [
    "calibration_run_id",
    "status",
    "input_path",
    "input_type",
    "profile",
    "row_count",
    "symbol_count",
    "final_score_min",
    "final_score_median",
    "final_score_max",
    "review_buy_candidate_count",
    "watch_count",
    "no_action_count",
    "blocked_count",
    "demo_only_count",
    "issue_count",
    "risk_precheck_status_counts",
    "score_action_counts",
    "action_counts",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
]


@dataclass(frozen=True)
class AdvisoryProfileDefinition:
    name: str
    reviewed_buy_min_score: float
    watch_min_score: float
    require_data_quality_pass: bool = True
    require_snapshot_quality_pass: bool = True


@dataclass(frozen=True)
class AdvisoryProfileCalibrationSettings:
    output_dir: Path = Path("outputs/reports/advisory_profile_calibration")
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_message_delivery: bool = False
    auto_order_allowed: bool = False


@dataclass(frozen=True)
class AdvisoryProfileCalibrationInput:
    input_path: Path
    input_type: str
    frame: pd.DataFrame


@dataclass(frozen=True)
class AdvisoryProfileCalibrationIssue:
    calibration_run_id: str
    source_row_index: int
    symbol: str
    severity: str
    issue_code: str
    issue_message: str
    suggested_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "calibration_run_id": self.calibration_run_id,
            "source_row_index": self.source_row_index,
            "symbol": self.symbol,
            "severity": self.severity,
            "issue_code": self.issue_code,
            "issue_message": self.issue_message,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True)
class AdvisoryProfileCalibrationResult:
    calibration_run_id: str
    status: str
    input_path: Path
    input_type: str
    profile: str
    profile_definition: AdvisoryProfileDefinition
    row_count: int
    symbol_count: int
    score_distribution: dict[str, float | None]
    label_counts: dict[str, int]
    risk_precheck_status_counts: dict[str, int]
    score_action_counts: dict[str, int]
    action_counts: dict[str, int]
    calibration_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    issues_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_advisory_profile_calibration_input(
    input_path: str | Path,
    *,
    input_type: str,
) -> AdvisoryProfileCalibrationInput:
    """Load a candidate/scored CSV while preserving symbol strings."""

    normalized_type = _normalize_input_type(input_type)
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Calibration input not found: {path}")
    frame = read_csv_preserve_symbol_columns(path)
    return AdvisoryProfileCalibrationInput(input_path=path, input_type=normalized_type, frame=frame)


def evaluate_advisory_profile_thresholds(
    calibration_input: AdvisoryProfileCalibrationInput,
    *,
    profile: str,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | AdvisoryProfileCalibrationSettings | str | Path | None = None,
) -> AdvisoryProfileCalibrationResult:
    """Evaluate one local profile against input rows without mutating the input frame."""

    profile_definition = _profile_definition(profile)
    resolved_settings = _resolve_settings(settings, output_dir=output_dir)
    _assert_settings_safe(resolved_settings)
    source_frame = calibration_input.frame.copy(deep=True)
    calibration_run_id = generate_advisory_profile_calibration_run_id(
        source_frame,
        input_path=calibration_input.input_path,
        input_type=calibration_input.input_type,
        profile=profile_definition.name,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
        settings=resolved_settings,
    )
    rows: list[dict[str, Any]] = []
    issues: list[AdvisoryProfileCalibrationIssue] = []
    for source_row_index, (_, row) in enumerate(source_frame.iterrows()):
        output_row, row_issues = _evaluate_row(
            row.to_dict(),
            source_row_index=source_row_index,
            calibration_run_id=calibration_run_id,
            profile=profile_definition,
            snapshot_quality_status_override=snapshot_quality_status,
            data_quality_status_override=data_quality_status,
        )
        rows.append(output_row)
        issues.extend(row_issues)

    calibration_frame = build_advisory_profile_calibration_table(rows)
    issues_frame = _issue_frame(issues)
    label_counts = _label_counts(calibration_frame)
    warnings = _build_warnings(calibration_frame, issues_frame)
    status = "WARN" if warnings or not issues_frame.empty or label_counts.get("DEMO_ONLY", 0) else "PASS"
    summary_frame = _summary_frame(
        calibration_run_id=calibration_run_id,
        status=status,
        calibration_input=calibration_input,
        profile=profile_definition.name,
        calibration_frame=calibration_frame,
        issues_frame=issues_frame,
    )
    artifact_paths = resolve_advisory_profile_calibration_artifact_paths(
        resolved_settings.output_dir,
        calibration_run_id,
    ).as_dict()
    result = AdvisoryProfileCalibrationResult(
        calibration_run_id=calibration_run_id,
        status=status,
        input_path=calibration_input.input_path,
        input_type=calibration_input.input_type,
        profile=profile_definition.name,
        profile_definition=profile_definition,
        row_count=len(calibration_frame),
        symbol_count=_symbol_count(calibration_frame),
        score_distribution=_score_distribution(calibration_frame),
        label_counts=label_counts,
        risk_precheck_status_counts=_value_counts(calibration_frame, "risk_precheck_status"),
        score_action_counts=_value_counts(calibration_frame, "score_action"),
        action_counts=_value_counts(calibration_frame, "action"),
        calibration_frame=calibration_frame,
        summary_frame=summary_frame,
        issues_frame=issues_frame,
        warnings=warnings,
        artifact_paths=artifact_paths,
        audit_metadata=_audit_metadata(resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_advisory_profile_calibration_artifacts(result)
    return result


def run_advisory_profile_calibration(
    input_path: str | Path,
    *,
    input_type: str,
    profile: str,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | AdvisoryProfileCalibrationSettings | str | Path | None = None,
) -> AdvisoryProfileCalibrationResult:
    """Load input rows and evaluate a local advisory profile calibration."""

    calibration_input = load_advisory_profile_calibration_input(input_path, input_type=input_type)
    return evaluate_advisory_profile_thresholds(
        calibration_input,
        profile=profile,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
        output_dir=output_dir,
        settings=settings,
    )


def build_advisory_profile_calibration_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the stable calibration output table."""

    if not rows:
        return pd.DataFrame(columns=CALIBRATION_COLUMNS)
    return pd.DataFrame(rows, columns=CALIBRATION_COLUMNS)


@dataclass(frozen=True)
class AdvisoryProfileCalibrationArtifactPaths:
    artifact_dir: Path
    advisory_profile_calibration: Path
    advisory_profile_calibration_summary: Path
    advisory_profile_calibration_issues: Path
    advisory_profile_calibration_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "advisory_profile_calibration": self.advisory_profile_calibration,
            "advisory_profile_calibration_summary": self.advisory_profile_calibration_summary,
            "advisory_profile_calibration_issues": self.advisory_profile_calibration_issues,
            "advisory_profile_calibration_report": self.advisory_profile_calibration_report,
            "metadata": self.metadata,
        }


def resolve_advisory_profile_calibration_artifact_paths(
    output_dir: str | Path,
    calibration_run_id: str,
) -> AdvisoryProfileCalibrationArtifactPaths:
    artifact_dir = Path(output_dir) / calibration_run_id
    return AdvisoryProfileCalibrationArtifactPaths(
        artifact_dir=artifact_dir,
        advisory_profile_calibration=artifact_dir / "advisory_profile_calibration.csv",
        advisory_profile_calibration_summary=artifact_dir / "advisory_profile_calibration_summary.csv",
        advisory_profile_calibration_issues=artifact_dir / "advisory_profile_calibration_issues.csv",
        advisory_profile_calibration_report=artifact_dir / "advisory_profile_calibration_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_advisory_profile_calibration_artifacts(result: AdvisoryProfileCalibrationResult) -> dict[str, Path]:
    """Write calibration CSV, summary, issues, report, and metadata artifacts."""

    paths = AdvisoryProfileCalibrationArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.calibration_frame, paths.advisory_profile_calibration)
    _export_dataframe(result.summary_frame, paths.advisory_profile_calibration_summary)
    _export_dataframe(result.issues_frame, paths.advisory_profile_calibration_issues)
    metadata = build_advisory_profile_calibration_metadata(result)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.advisory_profile_calibration_report.write_text(
        render_advisory_profile_calibration_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_advisory_profile_calibration_metadata(result: AdvisoryProfileCalibrationResult) -> dict[str, Any]:
    return {
        "calibration_run_id": result.calibration_run_id,
        "status": result.status,
        "created_at": "",
        "input_path": str(result.input_path),
        "input_type": result.input_type,
        "profile": result.profile,
        "profile_definition": {
            "reviewed_buy_min_score": result.profile_definition.reviewed_buy_min_score,
            "watch_min_score": result.profile_definition.watch_min_score,
            "require_data_quality_pass": result.profile_definition.require_data_quality_pass,
            "require_snapshot_quality_pass": result.profile_definition.require_snapshot_quality_pass,
        },
        "row_count": result.row_count,
        "symbol_count": result.symbol_count,
        "score_distribution": result.score_distribution,
        "label_counts": result.label_counts,
        "risk_precheck_status_counts": result.risk_precheck_status_counts,
        "score_action_counts": result.score_action_counts,
        "action_counts": result.action_counts,
        "issue_count": int(len(result.issues_frame)),
        "warnings": result.warnings,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "llm_api_called": False,
        "approved_for_paper_applied": False,
        "calibration_only": True,
        "not_trading_recommendation": True,
        "known_limitations": [
            "Advisory profile calibration analyzes local artifact thresholds only.",
            "Simulated labels are not orders, paper approvals, broker instructions, or message delivery triggers.",
            "Non-demo REVIEW_BUY_CANDIDATE labels are structural calibration labels only.",
        ],
    }


def render_advisory_profile_calibration_report(result: AdvisoryProfileCalibrationResult) -> str:
    lines = [
        f"# Advisory Profile Calibration Report: {result.calibration_run_id}",
        "",
        "No live trading, broker API, order placement, or message delivery was invoked.",
        "This report analyzes local profile thresholds only. It is not a strategy recommendation.",
        "",
        "## Summary",
        "",
        _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
        "",
        "## Profile Definition",
        "",
        _dict_table(
            {
                "profile": result.profile_definition.name,
                "reviewed_buy_min_score": result.profile_definition.reviewed_buy_min_score,
                "watch_min_score": result.profile_definition.watch_min_score,
                "require_data_quality_pass": result.profile_definition.require_data_quality_pass,
                "require_snapshot_quality_pass": result.profile_definition.require_snapshot_quality_pass,
            }
        ),
        "",
        "## Simulated Labels",
        "",
        _markdown_table(
            result.calibration_frame,
            [
                "symbol",
                "simulated_advisory_label",
                "final_score",
                "risk_precheck_status",
                "score_action",
                "action",
                "issue_codes",
            ],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(result.issues_frame, CALIBRATION_ISSUE_COLUMNS),
        "",
        "## Safety",
        "",
        _dict_table(
            {
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
                "calibration_only": True,
            }
        ),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def generate_advisory_profile_calibration_run_id(
    frame: pd.DataFrame,
    *,
    input_path: Path,
    input_type: str,
    profile: str,
    snapshot_quality_status: str | None,
    data_quality_status: str | None,
    settings: AdvisoryProfileCalibrationSettings,
) -> str:
    payload = {
        "frame_digest": _frame_digest(frame),
        "input_path": str(input_path),
        "input_type": input_type,
        "profile": profile,
        "snapshot_quality_status": snapshot_quality_status or "",
        "data_quality_status": data_quality_status or "",
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def _evaluate_row(
    row: dict[str, Any],
    *,
    source_row_index: int,
    calibration_run_id: str,
    profile: AdvisoryProfileDefinition,
    snapshot_quality_status_override: str | None,
    data_quality_status_override: str | None,
) -> tuple[dict[str, Any], list[AdvisoryProfileCalibrationIssue]]:
    symbol = normalize_symbol_value(_row_get(row, "symbol", ""))
    final_score = _to_float(_row_get(row, "final_score", ""))
    risk_status = _normalize_status(_row_get(row, "risk_precheck_status", ""))
    score_action = _normalize_action(_row_get(row, "score_action", ""))
    source_action = _normalize_action(_row_get(row, "action", ""))
    selection_profile = _text(_row_get(row, "selection_profile", ""))
    demo_mode = _to_bool(_row_get(row, "demo_mode", False))
    not_strategy = _to_bool(_row_get(row, "not_strategy_recommendation", False))
    snapshot_status = _normalize_status(snapshot_quality_status_override or _row_get(row, "snapshot_quality_status", ""))
    data_status = _normalize_status(data_quality_status_override or _row_get(row, "data_quality_status", ""))
    issue_specs = _classify_issue_specs(
        row,
        symbol=symbol,
        profile=profile,
        risk_status=risk_status,
        score_action=score_action,
        source_action=source_action,
        snapshot_quality_status=snapshot_status,
        data_quality_status=data_status,
    )
    if issue_specs:
        label = "BLOCKED"
    elif selection_profile.strip().lower() == "demo" or demo_mode or not_strategy:
        label = "DEMO_ONLY"
    elif score_action == "NO_TRADE" or source_action == "NO_TRADE":
        label = "NO_ACTION"
    elif final_score is not None and final_score >= profile.reviewed_buy_min_score:
        label = "REVIEW_BUY_CANDIDATE"
    elif final_score is not None and final_score >= profile.watch_min_score:
        label = "WATCH"
    else:
        label = "NO_ACTION"
    issues = [
        AdvisoryProfileCalibrationIssue(
            calibration_run_id=calibration_run_id,
            source_row_index=source_row_index,
            symbol=symbol,
            severity=spec["severity"],
            issue_code=spec["issue_code"],
            issue_message=spec["issue_message"],
            suggested_action=spec["suggested_action"],
        )
        for spec in issue_specs
    ]
    issue_codes = [spec["issue_code"] for spec in issue_specs]
    return (
        {
            "calibration_run_id": calibration_run_id,
            "source_row_index": source_row_index,
            "symbol": symbol,
            "name": _text(_row_get(row, "name", "")),
            "instrument_type": _text(_row_get(row, "instrument_type", "")),
            "profile": profile.name,
            "simulated_advisory_label": label,
            "final_score": final_score,
            "reviewed_buy_min_score": profile.reviewed_buy_min_score,
            "watch_min_score": profile.watch_min_score,
            "risk_precheck_status": risk_status,
            "risk_precheck_reason": _text(_row_get(row, "risk_precheck_reason", "")),
            "score_action": score_action,
            "action": source_action,
            "selection_profile": selection_profile,
            "demo_mode": demo_mode,
            "not_strategy_recommendation": not_strategy,
            "snapshot_quality_status": snapshot_status,
            "data_quality_status": data_status,
            "requires_manual_confirmation": True,
            "auto_order_allowed": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_message_sent": True,
            "calibration_only": True,
            "not_trading_recommendation": True,
            "reason_summary": _reason_summary(label, final_score, profile, issue_codes),
            "issue_codes": ";".join(issue_codes),
        },
        issues,
    )


def _classify_issue_specs(
    row: dict[str, Any],
    *,
    symbol: str,
    profile: AdvisoryProfileDefinition,
    risk_status: str,
    score_action: str,
    source_action: str,
    snapshot_quality_status: str,
    data_quality_status: str,
) -> list[dict[str, str]]:
    issue_specs: list[dict[str, str]] = []
    if not symbol:
        issue_specs.append(_issue_spec("ERROR", "MISSING_SYMBOL", "Symbol is missing.", "Fix source artifact symbol."))
        return issue_specs
    if not re.match(r"^\d{6}$", symbol):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "INVALID_SYMBOL",
                f"Symbol '{symbol}' is not a six-digit local symbol.",
                "Review symbol before calibration.",
            )
        )
        return issue_specs
    if risk_status in {"BLOCK", "BLOCKED", "FAIL", "REJECT", "REJECTED"}:
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "RISK_BLOCKED",
                f"risk_precheck_status={risk_status or 'UNKNOWN'} blocks calibration label.",
                "Review risk precheck before considering this row.",
            )
        )
    if score_action == "BLOCKED" or source_action == "BLOCKED":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "SCORE_BLOCKED",
                "score_action/action is BLOCKED.",
                "Review score/risk context before considering this row.",
            )
        )
    if profile.require_snapshot_quality_pass and snapshot_quality_status == "FAIL":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "SNAPSHOT_QUALITY_FAILED",
                "snapshot_quality_status=FAIL.",
                "Fix snapshot quality before calibration review.",
            )
        )
    if profile.require_data_quality_pass and data_quality_status == "FAIL":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "DATA_QUALITY_FAILED",
                "data_quality_status=FAIL.",
                "Fix data quality before calibration review.",
            )
        )
    if _explicit_false(_row_get(row, "market_data_available", "")):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "MARKET_DATA_UNAVAILABLE",
                "market_data_available=false.",
                "Regenerate or repair local market data before calibration.",
            )
        )
    if _explicit_false(_row_get(row, "execution_data_available", "")):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "EXECUTION_DATA_UNAVAILABLE",
                "execution_data_available=false.",
                "Regenerate or repair execution context before calibration.",
            )
        )
    return issue_specs


def _profile_definition(profile: str) -> AdvisoryProfileDefinition:
    normalized = str(profile or "").strip().lower()
    aliases = {
        "reviewed_local_v0_conservative": "conservative",
        "reviewed_local_v0_balanced": "balanced",
        "reviewed_local_v0_experimental": "experimental",
    }
    normalized = aliases.get(normalized, normalized)
    definitions = {
        "conservative": AdvisoryProfileDefinition("conservative", reviewed_buy_min_score=75.0, watch_min_score=60.0),
        "balanced": AdvisoryProfileDefinition("balanced", reviewed_buy_min_score=70.0, watch_min_score=55.0),
        "experimental": AdvisoryProfileDefinition("experimental", reviewed_buy_min_score=65.0, watch_min_score=50.0),
    }
    if normalized not in definitions:
        raise ValueError(f"Unknown advisory profile calibration profile: {profile}")
    return definitions[normalized]


def _summary_frame(
    *,
    calibration_run_id: str,
    status: str,
    calibration_input: AdvisoryProfileCalibrationInput,
    profile: str,
    calibration_frame: pd.DataFrame,
    issues_frame: pd.DataFrame,
) -> pd.DataFrame:
    distribution = _score_distribution(calibration_frame)
    label_counts = _label_counts(calibration_frame)
    row = {
        "calibration_run_id": calibration_run_id,
        "status": status,
        "input_path": str(calibration_input.input_path),
        "input_type": calibration_input.input_type,
        "profile": profile,
        "row_count": len(calibration_frame),
        "symbol_count": _symbol_count(calibration_frame),
        "final_score_min": distribution["min"],
        "final_score_median": distribution["median"],
        "final_score_max": distribution["max"],
        "review_buy_candidate_count": label_counts.get("REVIEW_BUY_CANDIDATE", 0),
        "watch_count": label_counts.get("WATCH", 0),
        "no_action_count": label_counts.get("NO_ACTION", 0),
        "blocked_count": label_counts.get("BLOCKED", 0),
        "demo_only_count": label_counts.get("DEMO_ONLY", 0),
        "issue_count": len(issues_frame),
        "risk_precheck_status_counts": json.dumps(_value_counts(calibration_frame, "risk_precheck_status"), sort_keys=True),
        "score_action_counts": json.dumps(_value_counts(calibration_frame, "score_action"), sort_keys=True),
        "action_counts": json.dumps(_value_counts(calibration_frame, "action"), sort_keys=True),
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
    }
    return pd.DataFrame([row], columns=CALIBRATION_SUMMARY_COLUMNS)


def _issue_frame(issues: list[AdvisoryProfileCalibrationIssue]) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=CALIBRATION_ISSUE_COLUMNS)
    return pd.DataFrame([issue.as_dict() for issue in issues], columns=CALIBRATION_ISSUE_COLUMNS)


def _build_warnings(calibration_frame: pd.DataFrame, issues_frame: pd.DataFrame) -> list[str]:
    warnings = [
        "Advisory profile calibration is threshold analysis only and is not a trading recommendation.",
    ]
    if not calibration_frame.empty and int((calibration_frame["simulated_advisory_label"] == "DEMO_ONLY").sum()) > 0:
        warnings.append("Demo/not-strategy rows are marked DEMO_ONLY and are not non-demo advisory labels.")
    if not issues_frame.empty:
        warnings.append("One or more rows were blocked by calibration gates; review issues before using the profile.")
    return warnings


def _score_distribution(frame: pd.DataFrame) -> dict[str, float | None]:
    if frame.empty or "final_score" not in frame:
        return {"min": None, "median": None, "max": None}
    scores = pd.to_numeric(frame["final_score"], errors="coerce").dropna()
    if scores.empty:
        return {"min": None, "median": None, "max": None}
    return {"min": float(scores.min()), "median": float(scores.median()), "max": float(scores.max())}


def _label_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = {label: 0 for label in CALIBRATION_LABELS}
    if not frame.empty and "simulated_advisory_label" in frame:
        for label, count in frame["simulated_advisory_label"].astype(str).value_counts().items():
            counts[str(label)] = int(count)
    return counts


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame:
        return {}
    return {str(key): int(value) for key, value in frame[column].fillna("").astype(str).value_counts().items() if str(key)}


def _symbol_count(frame: pd.DataFrame) -> int:
    if frame.empty or "symbol" not in frame:
        return 0
    return int(frame["symbol"].fillna("").astype(str).loc[lambda series: series != ""].nunique())


def _reason_summary(
    label: str,
    final_score: float | None,
    profile: AdvisoryProfileDefinition,
    issue_codes: list[str],
) -> str:
    if issue_codes:
        return f"Blocked by calibration gates: {', '.join(issue_codes)}."
    if label == "DEMO_ONLY":
        return "Demo/not-strategy input is calibration-only and not a non-demo advisory label."
    if label == "REVIEW_BUY_CANDIDATE":
        return (
            f"Final score {final_score} meets {profile.name} review threshold "
            f"{profile.reviewed_buy_min_score}; manual review is still required."
        )
    if label == "WATCH":
        return f"Final score {final_score} meets watch threshold {profile.watch_min_score} but not buy-review threshold."
    return "Row did not meet review or watch thresholds."


def _audit_metadata(settings: AdvisoryProfileCalibrationSettings) -> dict[str, Any]:
    return {
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "llm_api_called": False,
        "approved_for_paper_applied": False,
        "output_dir": str(settings.output_dir),
        "config_version": settings.config_version,
    }


def _resolve_settings(
    settings: Settings | AdvisoryProfileCalibrationSettings | str | Path | None,
    *,
    output_dir: str | Path | None,
) -> AdvisoryProfileCalibrationSettings:
    if isinstance(settings, AdvisoryProfileCalibrationSettings):
        resolved = settings
    else:
        project_settings = load_settings(settings) if isinstance(settings, (str, Path)) else (
            settings if isinstance(settings, Settings) else load_settings(Path("config/default.yaml"))
        )
        resolved = getattr(project_settings, "advisory_profile_calibration", AdvisoryProfileCalibrationSettings())
    if output_dir is not None:
        resolved = AdvisoryProfileCalibrationSettings(
            output_dir=Path(output_dir),
            config_version=resolved.config_version,
            write_artifacts=resolved.write_artifacts,
            enable_live_trading=resolved.enable_live_trading,
            enable_broker_api=resolved.enable_broker_api,
            enable_message_delivery=resolved.enable_message_delivery,
            auto_order_allowed=resolved.auto_order_allowed,
        )
    return resolved


def _assert_settings_safe(settings: AdvisoryProfileCalibrationSettings) -> None:
    if settings.enable_live_trading:
        raise ValueError("Advisory profile calibration cannot enable live trading.")
    if settings.enable_broker_api:
        raise ValueError("Advisory profile calibration cannot enable broker API access.")
    if settings.enable_message_delivery:
        raise ValueError("Advisory profile calibration cannot enable message delivery.")
    if settings.auto_order_allowed:
        raise ValueError("Advisory profile calibration cannot allow auto-order.")


def _normalize_input_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "scored":
        normalized = "scored_dataset"
    if normalized not in {"candidates", "scored_dataset"}:
        raise ValueError(f"Unsupported advisory profile calibration input type: {value}")
    return normalized


def _normalize_action(value: Any) -> str:
    return _text(value).upper()


def _normalize_status(value: Any) -> str:
    return _text(value).upper()


def _row_get(row: dict[str, Any], key: str, default: Any = None) -> Any:
    return row.get(key, default)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _explicit_false(value: Any) -> bool:
    if isinstance(value, bool):
        return value is False
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    return str(value).strip().lower() in {"false", "0", "no", "n"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def _issue_spec(severity: str, issue_code: str, issue_message: str, suggested_action: str) -> dict[str, str]:
    return {
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _frame_digest(frame: pd.DataFrame) -> str:
    payload = frame.fillna("").astype(str).to_csv(index=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _dict_table(values: dict[str, Any]) -> str:
    if not values:
        return "_No values._"
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        lines.append(f"| `{key}` | `{_format_markdown_value(value)}` |")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    if frame.empty:
        return "_No rows._"
    available = [column for column in columns if column in frame.columns]
    if not available:
        return "_No display columns._"
    sample = frame.loc[:, available].head(max_rows)
    lines = ["| " + " | ".join(available) + " |", "| " + " | ".join("---" for _ in available) + " |"]
    for _, row in sample.iterrows():
        lines.append("| " + " | ".join(_format_markdown_value(row[column]) for column in available) + " |")
    return "\n".join(lines)


def _format_markdown_value(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""
    return text.replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value
