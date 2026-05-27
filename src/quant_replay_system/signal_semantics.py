"""Deterministic advisory semantics policy for local scored/candidate rows."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SignalSemanticsSettings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


SIGNAL_SEMANTICS_ACTIONS = [
    "DEMO_ONLY",
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
]

SIGNAL_SEMANTICS_COLUMNS = [
    "semantics_run_id",
    "source_row_index",
    "symbol",
    "name",
    "instrument_type",
    "advisory_action",
    "source_action",
    "score_action",
    "final_score",
    "risk_precheck_status",
    "risk_precheck_reason",
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
    "reason_summary",
    "score_breakdown",
    "supporting_factors",
    "issue_codes",
]

SIGNAL_SEMANTICS_ISSUE_COLUMNS = [
    "semantics_run_id",
    "source_row_index",
    "symbol",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]

SIGNAL_SEMANTICS_LIMITATIONS = [
    "Signal semantics v0.1 maps local artifact rows to advisory labels only.",
    "Advisory labels are not orders, paper approvals, broker instructions, or message delivery triggers.",
    "Demo inputs remain DEMO_ONLY or conservative validation labels and are not strategy recommendations.",
    "Non-demo REVIEW_BUY_CANDIDATE and REVIEW_SELL_CANDIDATE labels are structural review labels only.",
    "Manual confirmation is required and auto-order remains disabled for every row.",
]


@dataclass(frozen=True)
class SignalSemanticsInput:
    input_path: Path
    input_type: str = "candidates"
    metadata_path: Path | None = None
    profile: str | None = None
    snapshot_quality_status: str | None = None
    data_quality_status: str | None = None


@dataclass(frozen=True)
class SignalSemanticsDecision:
    semantics_run_id: str
    source_row_index: int
    symbol: str
    name: str
    instrument_type: str
    advisory_action: str
    source_action: str
    score_action: str
    final_score: float | None
    risk_precheck_status: str
    risk_precheck_reason: str
    selection_profile: str
    demo_mode: bool
    not_strategy_recommendation: bool
    snapshot_quality_status: str
    data_quality_status: str
    requires_manual_confirmation: bool
    auto_order_allowed: bool
    no_live_trading: bool
    no_broker_api: bool
    no_message_sent: bool
    reason_summary: str
    score_breakdown: str
    supporting_factors: str
    issue_codes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "semantics_run_id": self.semantics_run_id,
            "source_row_index": self.source_row_index,
            "symbol": self.symbol,
            "name": self.name,
            "instrument_type": self.instrument_type,
            "advisory_action": self.advisory_action,
            "source_action": self.source_action,
            "score_action": self.score_action,
            "final_score": self.final_score,
            "risk_precheck_status": self.risk_precheck_status,
            "risk_precheck_reason": self.risk_precheck_reason,
            "selection_profile": self.selection_profile,
            "demo_mode": self.demo_mode,
            "not_strategy_recommendation": self.not_strategy_recommendation,
            "snapshot_quality_status": self.snapshot_quality_status,
            "data_quality_status": self.data_quality_status,
            "requires_manual_confirmation": self.requires_manual_confirmation,
            "auto_order_allowed": self.auto_order_allowed,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_message_sent": self.no_message_sent,
            "reason_summary": self.reason_summary,
            "score_breakdown": self.score_breakdown,
            "supporting_factors": self.supporting_factors,
            "issue_codes": ";".join(self.issue_codes),
        }


@dataclass(frozen=True)
class SignalSemanticsIssue:
    semantics_run_id: str
    source_row_index: int
    symbol: str
    severity: str
    issue_code: str
    issue_message: str
    suggested_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "semantics_run_id": self.semantics_run_id,
            "source_row_index": self.source_row_index,
            "symbol": self.symbol,
            "severity": self.severity,
            "issue_code": self.issue_code,
            "issue_message": self.issue_message,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True)
class SignalSemanticsArtifactPaths:
    artifact_dir: Path
    signal_semantics: Path
    signal_semantics_report: Path
    signal_semantics_issues: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "signal_semantics": self.signal_semantics,
            "signal_semantics_report": self.signal_semantics_report,
            "signal_semantics_issues": self.signal_semantics_issues,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SignalSemanticsResult:
    semantics_run_id: str
    status: str
    input_path: Path
    input_type: str
    metadata_path: Path | None
    profile: str
    row_count: int
    action_counts: dict[str, int]
    decisions: pd.DataFrame
    issues: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]
    source_metadata: dict[str, Any]


def run_signal_semantics(
    input_path: str | Path,
    *,
    input_type: str = "candidates",
    metadata_path: str | Path | None = None,
    profile: str | None = None,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | SignalSemanticsSettings | str | Path | None = None,
) -> SignalSemanticsResult:
    """Run the local deterministic signal semantics policy on a CSV artifact."""

    project_settings, semantics_settings = _resolve_settings(settings)
    _assert_settings_safe(semantics_settings)
    if output_dir is not None:
        semantics_settings = semantics_settings.model_copy(update={"output_dir": Path(output_dir)})

    semantics_input = SignalSemanticsInput(
        input_path=Path(input_path),
        input_type=_normalize_input_type(input_type),
        metadata_path=_optional_path(metadata_path),
        profile=profile,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
    )
    if not semantics_input.input_path.exists():
        raise FileNotFoundError(f"Signal semantics input not found: {semantics_input.input_path}")
    if semantics_input.metadata_path is not None and not semantics_input.metadata_path.exists():
        raise FileNotFoundError(f"Signal semantics metadata not found: {semantics_input.metadata_path}")

    frame = read_csv_preserve_symbol_columns(semantics_input.input_path, keep_default_na=False)
    source_metadata = _load_json_or_empty(semantics_input.metadata_path)
    semantics_run_id = generate_signal_semantics_run_id(
        frame,
        input_path=semantics_input.input_path,
        input_type=semantics_input.input_type,
        profile=semantics_input.profile,
        snapshot_quality_status=semantics_input.snapshot_quality_status,
        data_quality_status=semantics_input.data_quality_status,
        config_version=semantics_settings.config_version,
    )
    paths = resolve_signal_semantics_artifact_paths(semantics_settings.output_dir, semantics_run_id)
    result = evaluate_signal_semantics_frame(
        frame,
        settings=semantics_settings,
        semantics_run_id=semantics_run_id,
        input_path=semantics_input.input_path,
        input_type=semantics_input.input_type,
        metadata_path=semantics_input.metadata_path,
        profile=semantics_input.profile,
        snapshot_quality_status=semantics_input.snapshot_quality_status,
        data_quality_status=semantics_input.data_quality_status,
        source_metadata=source_metadata,
        artifact_paths=paths.as_dict(),
    )
    if project_settings.signal_semantics.write_artifacts and semantics_settings.write_artifacts:
        write_signal_semantics_artifacts(result)
    return result


def classify_signal_semantics_action(
    row: pd.Series | dict[str, Any],
    *,
    settings: SignalSemanticsSettings | None = None,
    selection_profile: str | None = None,
    demo_mode: bool | None = None,
    not_strategy_recommendation: bool | None = None,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
) -> str:
    """Classify one row into a safe advisory semantics label."""

    cfg = settings or load_settings(Path("config/default.yaml")).signal_semantics
    action, _issues = _classify_action_and_issues(
        row,
        settings=cfg,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy_recommendation,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
    )
    return action


def evaluate_signal_semantics_frame(
    frame: pd.DataFrame,
    *,
    settings: SignalSemanticsSettings | None = None,
    semantics_run_id: str | None = None,
    input_path: str | Path = "",
    input_type: str = "candidates",
    metadata_path: str | Path | None = None,
    profile: str | None = None,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
    source_metadata: dict[str, Any] | None = None,
    artifact_paths: dict[str, Path] | None = None,
) -> SignalSemanticsResult:
    """Evaluate a DataFrame with deterministic advisory semantics rules."""

    cfg = settings or load_settings(Path("config/default.yaml")).signal_semantics
    _assert_settings_safe(cfg)
    source_metadata = source_metadata or {}
    input_path_obj = Path(input_path) if input_path else Path("")
    metadata_path_obj = _optional_path(metadata_path)
    run_id = semantics_run_id or generate_signal_semantics_run_id(
        frame,
        input_path=input_path_obj,
        input_type=input_type,
        profile=profile,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
        config_version=cfg.config_version,
    )
    paths = (
        {key: Path(value) for key, value in artifact_paths.items()}
        if artifact_paths is not None
        else resolve_signal_semantics_artifact_paths(cfg.output_dir, run_id).as_dict()
    )

    decisions: list[SignalSemanticsDecision] = []
    issues: list[SignalSemanticsIssue] = []
    for row_number, row in enumerate(frame.to_dict("records")):
        decision, row_issues = _build_decision(
            row,
            source_row_index=row_number,
            semantics_run_id=run_id,
            settings=cfg,
            profile_override=profile,
            snapshot_quality_status_override=snapshot_quality_status,
            data_quality_status_override=data_quality_status,
            source_metadata=source_metadata,
        )
        decisions.append(decision)
        issues.extend(row_issues)

    decisions_frame = _decision_frame(decisions)
    issues_frame = _issue_frame(issues)
    action_counts = _action_counts(decisions_frame)
    warnings = _build_warnings(decisions_frame, issues_frame)
    status = "WARN" if not issues_frame.empty or warnings else "PASS"
    effective_profile = _effective_profile(profile, source_metadata, decisions_frame)
    audit_metadata = _build_audit_metadata(
        semantics_run_id=run_id,
        status=status,
        input_path=input_path_obj,
        input_type=_normalize_input_type(input_type),
        metadata_path=metadata_path_obj,
        profile=effective_profile,
        row_count=len(decisions_frame),
        action_counts=action_counts,
        decisions=decisions_frame,
        issues=issues_frame,
        warnings=warnings,
        settings=cfg,
        source_metadata=source_metadata,
    )
    return SignalSemanticsResult(
        semantics_run_id=run_id,
        status=status,
        input_path=input_path_obj,
        input_type=_normalize_input_type(input_type),
        metadata_path=metadata_path_obj,
        profile=effective_profile,
        row_count=len(decisions_frame),
        action_counts=action_counts,
        decisions=decisions_frame,
        issues=issues_frame,
        artifact_paths=paths,
        warnings=warnings,
        known_limitations=SIGNAL_SEMANTICS_LIMITATIONS,
        audit_metadata=audit_metadata,
        source_metadata=source_metadata,
    )


def build_signal_semantics_report(result: SignalSemanticsResult) -> str:
    """Build the markdown signal semantics report."""

    return render_signal_semantics_report(result)


def render_signal_semantics_report(result: SignalSemanticsResult) -> str:
    """Render a local markdown report for a signal semantics run."""

    lines = [
        f"# Signal Advisory Semantics Report: {result.semantics_run_id}",
        "",
        "Signal semantics maps local candidate/scored rows to advisory labels. It is not trading advice, an order, or a broker instruction.",
        "No live trading, broker API, automated order placement, message delivery, or paper approval was invoked.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "semantics_run_id": result.semantics_run_id,
                "status": result.status,
                "input_path": result.input_path,
                "input_type": result.input_type,
                "profile": result.profile,
                "row_count": result.row_count,
                "issue_count": len(result.issues),
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ),
        "",
        "## Advisory Action Counts",
        "",
        _dict_table(result.action_counts),
        "",
        "## Safety Contract",
        "",
        _dict_table(
            {
                "advisory_labels_are_orders": False,
                "review_buy_candidate_is_buy_instruction": False,
                "demo_outputs_are_strategy_recommendations": False,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "message_delivery_enabled": False,
                "message_sent": False,
                "approved_for_paper_applied": False,
            }
        ),
        "",
        "## Decisions",
        "",
        _markdown_table(
            result.decisions,
            [
                "symbol",
                "name",
                "instrument_type",
                "advisory_action",
                "final_score",
                "score_action",
                "source_action",
                "risk_precheck_status",
                "selection_profile",
                "demo_mode",
                "not_strategy_recommendation",
                "snapshot_quality_status",
                "data_quality_status",
                "reason_summary",
            ],
        ),
        "",
        "## Issues",
        "",
        _markdown_table(
            result.issues,
            ["source_row_index", "symbol", "severity", "issue_code", "issue_message", "suggested_action"],
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


def write_signal_semantics_artifacts(result: SignalSemanticsResult) -> dict[str, Path]:
    """Write CSV, issue CSV, markdown report, and metadata artifacts."""

    paths = SignalSemanticsArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.decisions, paths.signal_semantics)
    _export_dataframe(result.issues, paths.signal_semantics_issues)
    paths.signal_semantics_report.write_text(render_signal_semantics_report(result), encoding="utf-8")
    paths.metadata.write_text(
        json.dumps(_json_safe(build_signal_semantics_metadata(result, paths)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_signal_semantics_metadata(
    result: SignalSemanticsResult,
    paths: SignalSemanticsArtifactPaths,
) -> dict[str, Any]:
    """Build metadata.json for a signal semantics artifact."""

    return {
        "semantics_run_id": result.semantics_run_id,
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "status": result.status,
        "input_path": str(result.input_path),
        "input_type": result.input_type,
        "metadata_path": str(result.metadata_path or ""),
        "profile": result.profile,
        "row_count": result.row_count,
        "issue_count": len(result.issues),
        "warning_count": len(result.warnings),
        "action_counts": result.action_counts,
        "blocked_count": int(result.action_counts.get("BLOCKED", 0)),
        "demo_only_count": int(result.action_counts.get("DEMO_ONLY", 0)),
        "watch_count": int(result.action_counts.get("WATCH", 0)),
        "review_buy_candidate_count": int(result.action_counts.get("REVIEW_BUY_CANDIDATE", 0)),
        "review_sell_candidate_count": int(result.action_counts.get("REVIEW_SELL_CANDIDATE", 0)),
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "outputs": {key: str(value) for key, value in paths.as_dict().items()},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
    }


def generate_signal_semantics_run_id(
    frame: pd.DataFrame,
    *,
    input_path: Path,
    input_type: str,
    profile: str | None,
    snapshot_quality_status: str | None,
    data_quality_status: str | None,
    config_version: str,
) -> str:
    """Generate a deterministic id from input rows and policy context."""

    payload = {
        "input_path": str(input_path),
        "input_type": _normalize_input_type(input_type),
        "profile": profile or "",
        "snapshot_quality_status": snapshot_quality_status or "",
        "data_quality_status": data_quality_status or "",
        "config_version": config_version,
        "row_count": len(frame),
        "frame_digest": _frame_digest(frame),
    }
    return _hash_payload(payload, length=12)


def resolve_signal_semantics_artifact_paths(output_dir: str | Path, semantics_run_id: str) -> SignalSemanticsArtifactPaths:
    """Resolve stable artifact paths for one signal semantics run."""

    artifact_dir = Path(output_dir) / semantics_run_id
    return SignalSemanticsArtifactPaths(
        artifact_dir=artifact_dir,
        signal_semantics=artifact_dir / "signal_semantics.csv",
        signal_semantics_report=artifact_dir / "signal_semantics_report.md",
        signal_semantics_issues=artifact_dir / "signal_semantics_issues.csv",
        metadata=artifact_dir / "metadata.json",
    )


def _build_decision(
    row: dict[str, Any],
    *,
    source_row_index: int,
    semantics_run_id: str,
    settings: SignalSemanticsSettings,
    profile_override: str | None,
    snapshot_quality_status_override: str | None,
    data_quality_status_override: str | None,
    source_metadata: dict[str, Any],
) -> tuple[SignalSemanticsDecision, list[SignalSemanticsIssue]]:
    symbol = normalize_symbol_value(_row_get(row, "symbol", ""))
    selection_profile = _resolve_selection_profile(row, source_metadata, profile_override)
    demo_mode = _resolve_demo_mode(row, source_metadata, selection_profile)
    not_strategy = _resolve_not_strategy(row, source_metadata, demo_mode)
    snapshot_status = _normalize_status(
        snapshot_quality_status_override
        or _row_get(row, "snapshot_quality_status", "")
        or _metadata_lookup(source_metadata, "snapshot_quality_status")
    )
    data_status = _normalize_status(
        data_quality_status_override
        or _row_get(row, "data_quality_status", "")
        or _metadata_lookup(source_metadata, "data_quality_status")
    )
    advisory_action, issue_specs = _classify_action_and_issues(
        row,
        settings=settings,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
        snapshot_quality_status=snapshot_status,
        data_quality_status=data_status,
    )
    issues = [
        SignalSemanticsIssue(
            semantics_run_id=semantics_run_id,
            source_row_index=source_row_index,
            symbol=symbol,
            severity=spec["severity"],
            issue_code=spec["issue_code"],
            issue_message=spec["issue_message"],
            suggested_action=spec["suggested_action"],
        )
        for spec in issue_specs
    ]
    final_score = _to_float(_row_get(row, "final_score", ""))
    source_action = _normalize_action(_row_get(row, "action", _row_get(row, "original_candidate_action", "")))
    score_action = _normalize_action(_row_get(row, "score_action", _row_get(row, "original_score_action", "")))
    risk_status = _normalize_action(_row_get(row, "risk_precheck_status", ""))
    decision = SignalSemanticsDecision(
        semantics_run_id=semantics_run_id,
        source_row_index=source_row_index,
        symbol=symbol,
        name=_text(_row_get(row, "name", "")),
        instrument_type=_text(_row_get(row, "instrument_type", "")),
        advisory_action=advisory_action,
        source_action=source_action,
        score_action=score_action,
        final_score=final_score,
        risk_precheck_status=risk_status,
        risk_precheck_reason=_text(_row_get(row, "risk_precheck_reason", "")),
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
        snapshot_quality_status=snapshot_status,
        data_quality_status=data_status,
        requires_manual_confirmation=True,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        no_message_sent=True,
        reason_summary=_reason_summary(
            advisory_action=advisory_action,
            final_score=final_score,
            source_action=source_action,
            score_action=score_action,
            risk_status=risk_status,
            demo_mode=demo_mode,
            not_strategy_recommendation=not_strategy,
            issue_codes=[spec["issue_code"] for spec in issue_specs],
        ),
        score_breakdown=_text(_row_get(row, "score_breakdown", "")),
        supporting_factors=_supporting_factors(row),
        issue_codes=[spec["issue_code"] for spec in issue_specs],
    )
    return decision, issues


def _classify_action_and_issues(
    row: pd.Series | dict[str, Any],
    *,
    settings: SignalSemanticsSettings,
    selection_profile: str | None = None,
    demo_mode: bool | None = None,
    not_strategy_recommendation: bool | None = None,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    issue_specs: list[dict[str, str]] = []
    symbol = normalize_symbol_value(_row_get(row, "symbol", ""))
    if not symbol:
        issue_specs.append(_issue_spec("ERROR", "MISSING_SYMBOL", "Symbol is missing.", "Fix the source artifact symbol."))
        return "BLOCKED", issue_specs
    if not _valid_symbol(symbol):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "INVALID_SYMBOL",
                f"Symbol '{symbol}' is not a six-digit local China-market symbol.",
                "Review the source artifact symbol before using this row.",
            )
        )
        return "BLOCKED", issue_specs

    risk_status = _normalize_action(_row_get(row, "risk_precheck_status", ""))
    score_action = _normalize_action(_row_get(row, "score_action", _row_get(row, "original_score_action", "")))
    source_action = _normalize_action(_row_get(row, "action", _row_get(row, "original_candidate_action", "")))
    final_score = _to_float(_row_get(row, "final_score", ""))
    snapshot_status = _normalize_status(snapshot_quality_status or _row_get(row, "snapshot_quality_status", ""))
    data_status = _normalize_status(data_quality_status or _row_get(row, "data_quality_status", ""))

    if risk_status in {"BLOCK", "BLOCKED", "FAIL", "REJECT", "REJECTED"}:
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "RISK_BLOCKED",
                f"risk_precheck_status={risk_status or 'UNKNOWN'} blocks advisory review.",
                "Review risk precheck before considering this symbol.",
            )
        )
        return "BLOCKED", issue_specs
    if score_action == "BLOCKED" or source_action == "BLOCKED":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "SCORE_BLOCKED",
                "Source action or score action is BLOCKED.",
                "Review score/risk context before considering this symbol.",
            )
        )
        return "BLOCKED", issue_specs
    if _explicit_false(_row_get(row, "market_data_available", "")):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "MARKET_DATA_UNAVAILABLE",
                "market_data_available=false.",
                "Regenerate or repair local market data before review.",
            )
        )
        return "BLOCKED", issue_specs
    if _explicit_false(_row_get(row, "execution_data_available", "")):
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "EXECUTION_DATA_UNAVAILABLE",
                "execution_data_available=false.",
                "Regenerate or repair execution context before review.",
            )
        )
        return "BLOCKED", issue_specs
    if settings.require_snapshot_quality_pass and snapshot_status == "FAIL":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "SNAPSHOT_QUALITY_FAILED",
                "snapshot_quality_status=FAIL.",
                "Fix snapshot quality before using this row.",
            )
        )
        return "BLOCKED", issue_specs
    if settings.require_data_quality_pass and data_status == "FAIL":
        issue_specs.append(
            _issue_spec(
                "ERROR",
                "DATA_QUALITY_FAILED",
                "data_quality_status=FAIL.",
                "Fix data quality before using this row.",
            )
        )
        return "BLOCKED", issue_specs

    profile = str(selection_profile or _row_get(row, "selection_profile", "") or "").strip().lower()
    is_demo = _to_bool(demo_mode) if demo_mode is not None else _to_bool(_row_get(row, "demo_mode", False))
    not_strategy = (
        _to_bool(not_strategy_recommendation)
        if not_strategy_recommendation is not None
        else _to_bool(_row_get(row, "not_strategy_recommendation", False))
    )
    if profile == "demo" or is_demo or not_strategy:
        if not settings.allow_review_buy_for_demo:
            return "DEMO_ONLY", issue_specs

    action = score_action or source_action
    if action == "NO_TRADE":
        return "NO_ACTION", issue_specs
    if action in {"SELL", "PAPER_SELL", "REVIEW_SELL_CANDIDATE"}:
        return "REVIEW_SELL_CANDIDATE", issue_specs
    if action in {"HOLD", "HOLD_REVIEW"}:
        return "HOLD_REVIEW", issue_specs
    if snapshot_status == "WARN" or data_status == "WARN":
        issue_specs.append(
            _issue_spec(
                "WARN",
                "QUALITY_CAVEAT",
                "Quality status is WARN; keep this as watch/review context only.",
                "Review data and snapshot caveats before considering a buy/sell review label.",
            )
        )
        return "WATCH", issue_specs
    risk_is_positive = risk_status in {"PASS", "OK"}
    if final_score is not None and final_score >= settings.reviewed_buy_min_score and not risk_is_positive:
        issue_specs.append(
            _issue_spec(
                "WARN",
                "MISSING_RISK_PRECHECK_PASS",
                "High score row does not expose risk_precheck_status=PASS/OK.",
                "Keep the row conservative until risk precheck status is explicit.",
            )
        )
        return "WATCH", issue_specs
    if (
        final_score is not None
        and final_score >= settings.reviewed_buy_min_score
        and risk_is_positive
        and action not in {"NO_TRADE", "BLOCKED"}
    ):
        return "REVIEW_BUY_CANDIDATE", issue_specs
    if final_score is not None and final_score >= settings.watch_min_score:
        return "WATCH", issue_specs
    if action in {"OBSERVE", "WATCH"}:
        return "WATCH", issue_specs
    return "NO_ACTION", issue_specs


def _decision_frame(decisions: list[SignalSemanticsDecision]) -> pd.DataFrame:
    if not decisions:
        return pd.DataFrame(columns=SIGNAL_SEMANTICS_COLUMNS)
    return pd.DataFrame([decision.as_dict() for decision in decisions], columns=SIGNAL_SEMANTICS_COLUMNS)


def _issue_frame(issues: list[SignalSemanticsIssue]) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=SIGNAL_SEMANTICS_ISSUE_COLUMNS)
    return pd.DataFrame([issue.as_dict() for issue in issues], columns=SIGNAL_SEMANTICS_ISSUE_COLUMNS)


def _build_audit_metadata(
    *,
    semantics_run_id: str,
    status: str,
    input_path: Path,
    input_type: str,
    metadata_path: Path | None,
    profile: str,
    row_count: int,
    action_counts: dict[str, int],
    decisions: pd.DataFrame,
    issues: pd.DataFrame,
    warnings: list[str],
    settings: SignalSemanticsSettings,
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    demo_mode = bool(decisions["demo_mode"].map(_to_bool).any()) if "demo_mode" in decisions.columns else False
    not_strategy = (
        bool(decisions["not_strategy_recommendation"].map(_to_bool).any())
        if "not_strategy_recommendation" in decisions.columns
        else False
    )
    return {
        "semantics_run_id": semantics_run_id,
        "status": status,
        "input_path": str(input_path),
        "input_type": input_type,
        "metadata_path": str(metadata_path or ""),
        "profile": profile,
        "selection_profile": _first_non_empty(decisions, "selection_profile") or profile,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy,
        "row_count": row_count,
        "action_counts": action_counts,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "approved_for_paper_applied": False,
        "strategy_recommendation_claimed": False,
        "source_metadata_keys": sorted(source_metadata.keys()),
        "config_summary": {
            "config_version": settings.config_version,
            "output_dir": str(settings.output_dir),
            "reviewed_buy_min_score": settings.reviewed_buy_min_score,
            "watch_min_score": settings.watch_min_score,
            "require_snapshot_quality_pass": settings.require_snapshot_quality_pass,
            "require_data_quality_pass": settings.require_data_quality_pass,
            "allow_review_buy_for_demo": settings.allow_review_buy_for_demo,
            "allow_auto_order": settings.allow_auto_order,
            "enable_live_trading": settings.enable_live_trading,
            "enable_broker_api": settings.enable_broker_api,
            "enable_message_delivery": settings.enable_message_delivery,
        },
    }


def _build_warnings(decisions: pd.DataFrame, issues: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if not decisions.empty and int((decisions["advisory_action"] == "DEMO_ONLY").sum()) == len(decisions):
        warnings.append("All rows are DEMO_ONLY; this is workflow validation only and not strategy advice.")
    if not issues.empty:
        warnings.append(f"Signal semantics recorded {len(issues)} row-level issue(s); blocked rows remain non-actionable.")
    return warnings


def _action_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = {action: 0 for action in SIGNAL_SEMANTICS_ACTIONS}
    if frame.empty or "advisory_action" not in frame.columns:
        return counts
    observed = frame["advisory_action"].value_counts().to_dict()
    for action, count in observed.items():
        counts[str(action)] = int(count)
    return counts


def _reason_summary(
    *,
    advisory_action: str,
    final_score: float | None,
    source_action: str,
    score_action: str,
    risk_status: str,
    demo_mode: bool,
    not_strategy_recommendation: bool,
    issue_codes: list[str],
) -> str:
    score_text = "UNKNOWN" if final_score is None else f"{final_score:.2f}"
    if advisory_action == "BLOCKED":
        return (
            f"Blocked by semantics policy; issues={','.join(issue_codes) or 'policy_block'}; "
            f"risk_precheck_status={risk_status or 'UNKNOWN'}; final_score={score_text}."
        )
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return (
            "Demo/not-strategy artifact; semantics policy keeps this as workflow validation only. "
            f"source_action={source_action or 'UNKNOWN'}; score_action={score_action or 'UNKNOWN'}; "
            f"final_score={score_text}."
        )
    if advisory_action == "REVIEW_BUY_CANDIDATE":
        return (
            "Non-demo structural review-buy candidate; manual confirmation required and auto-order disabled. "
            f"source_action={source_action or 'UNKNOWN'}; score_action={score_action or 'UNKNOWN'}; "
            f"final_score={score_text}."
        )
    if advisory_action == "REVIEW_SELL_CANDIDATE":
        return "Explicit non-demo sell-review structure only; manual confirmation required and auto-order disabled."
    if advisory_action == "WATCH":
        return (
            "Watch/review context only; threshold or quality caveat does not support a stronger label. "
            f"final_score={score_text}."
        )
    if advisory_action == "NO_ACTION":
        return "Conservative fallback; source row does not support a review action."
    return "Review-only advisory context; manual confirmation required."


def _supporting_factors(row: dict[str, Any]) -> str:
    keys = [
        "technical_score",
        "liquidity_score",
        "expectation_score",
        "reality_score",
        "sentiment_score",
        "score_reason",
        "source",
        "upstream",
        "source_policy",
    ]
    values = {key: _row_get(row, key, "") for key in keys if _present(_row_get(row, key, ""))}
    return json.dumps(_json_safe(values), sort_keys=True) if values else ""


def _resolve_selection_profile(row: dict[str, Any], metadata: dict[str, Any], override: str | None) -> str:
    value = (
        override
        or _row_get(row, "selection_profile", "")
        or _metadata_lookup(metadata, "selection_profile")
        or "default"
    )
    return str(value).strip().lower() or "default"


def _resolve_demo_mode(row: dict[str, Any], metadata: dict[str, Any], selection_profile: str) -> bool:
    if selection_profile == "demo":
        return True
    if _present(_row_get(row, "demo_mode", "")):
        return _to_bool(_row_get(row, "demo_mode", False))
    return _to_bool(_metadata_lookup(metadata, "demo_mode"))


def _resolve_not_strategy(row: dict[str, Any], metadata: dict[str, Any], demo_mode: bool) -> bool:
    if demo_mode:
        return True
    if _present(_row_get(row, "not_strategy_recommendation", "")):
        return _to_bool(_row_get(row, "not_strategy_recommendation", False))
    return _to_bool(_metadata_lookup(metadata, "not_strategy_recommendation"))


def _metadata_lookup(metadata: dict[str, Any], key: str) -> Any:
    if key in metadata:
        return metadata.get(key)
    audit = metadata.get("audit_metadata")
    if isinstance(audit, dict) and key in audit:
        return audit.get(key)
    config = metadata.get("config_summary")
    if isinstance(config, dict) and key in config:
        return config.get(key)
    return ""


def _effective_profile(profile: str | None, metadata: dict[str, Any], decisions: pd.DataFrame) -> str:
    if profile:
        return str(profile).strip().lower()
    frame_profile = _first_non_empty(decisions, "selection_profile")
    if frame_profile:
        return frame_profile.strip().lower()
    metadata_profile = _metadata_lookup(metadata, "selection_profile")
    return str(metadata_profile or "default").strip().lower()


def _assert_settings_safe(settings: SignalSemanticsSettings) -> None:
    if settings.enable_live_trading or settings.enable_broker_api:
        raise ValueError("Signal semantics cannot enable live trading or broker API access")
    if settings.enable_message_delivery:
        raise ValueError("Signal semantics does not send messages")
    if settings.allow_auto_order:
        raise ValueError("Signal semantics cannot allow automatic order placement")
    if settings.allow_review_buy_for_demo:
        raise ValueError("Signal semantics cannot allow review-buy labels for demo artifacts")


def _normalize_input_type(value: str) -> str:
    normalized = str(value or "candidates").strip().lower()
    allowed = {"candidates", "scored", "scored_dataset", "signals", "factor_dataset"}
    if normalized not in allowed:
        raise ValueError(f"input_type must be one of: {', '.join(sorted(allowed))}")
    return "scored" if normalized == "scored_dataset" else normalized


def _optional_path(value: str | Path | None) -> Path | None:
    return None if value is None else Path(value)


def _load_json_or_empty(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_action(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_status(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"PASS", "OK"}:
        return "PASS"
    if text in {"WARN", "WARNING"}:
        return "WARN"
    if text in {"FAIL", "FAILED", "ERROR"}:
        return "FAIL"
    return text


def _row_get(row: pd.Series | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(row, pd.Series):
        return row.get(key, default)
    return row.get(key, default)


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


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def _explicit_false(value: Any) -> bool:
    if value is None or not _present(value):
        return False
    if isinstance(value, bool):
        return not value
    return str(value).strip().lower() in {"false", "0", "no", "n"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _present(value: Any) -> bool:
    return _text(value) != ""


def _valid_symbol(symbol: str) -> bool:
    return bool(re.match(r"^\d{6}$", symbol))


def _issue_spec(severity: str, issue_code: str, issue_message: str, suggested_action: str) -> dict[str, str]:
    return {
        "severity": severity,
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _resolve_settings(
    settings: Settings | SignalSemanticsSettings | str | Path | None,
) -> tuple[Settings, SignalSemanticsSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.signal_semantics
    if isinstance(settings, Settings):
        return settings, settings.signal_semantics
    if isinstance(settings, SignalSemanticsSettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"signal_semantics": settings}), settings
    project = load_settings(Path(settings))
    return project, project.signal_semantics


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    values = frame[column].dropna().astype(str)
    for value in values:
        if value.strip():
            return value.strip()
    return ""


def _frame_digest(frame: pd.DataFrame) -> str:
    records = _json_safe(frame.to_dict("records"))
    return _hash_payload({"records": records}, length=16)


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


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


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6g}"
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.DataFrame):
        return [_json_safe(record) for record in value.to_dict("records")]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
