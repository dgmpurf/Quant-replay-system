"""Single-symbol advisory review from local candidate and signal artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, SignalSemanticsSettings, SingleSymbolAdvisorySettings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.signal_semantics import build_signal_semantics_provenance, classify_signal_semantics_action


SINGLE_SYMBOL_ADVISORY_COLUMNS = [
    "advisory_run_id",
    "status",
    "symbol",
    "advisory_date",
    "source_artifact_path",
    "source_candidate_run_id",
    "found_in_candidates",
    "found_in_scored_dataset",
    "selection_profile",
    "demo_mode",
    "not_strategy_recommendation",
    "current_action",
    "score_action",
    "final_score",
    "advisory_action",
    "semantics_policy_source",
    "semantics_policy_version",
    "semantics_classifier",
    "semantics_settings_profile",
    "semantics_action",
    "semantics_reason",
    "semantics_manual_confirmation_required",
    "semantics_auto_order_allowed",
    "semantics_no_live_trading",
    "semantics_no_broker_api",
    "reason_summary",
    "supporting_factors",
    "risk_notes",
    "data_quality_notes",
    "entry_condition",
    "exit_condition",
    "invalidation_condition",
    "valid_until",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
]

SINGLE_SYMBOL_KNOWN_LIMITATIONS = [
    "Single-symbol advisory v0.1 uses local artifacts only.",
    "Advisory output is not an order, paper approval, or broker instruction.",
    "Demo artifacts remain workflow validation only and are not strategy recommendations.",
    "No message delivery, live trading, broker API, or automated order placement is implemented.",
    "Non-demo advisory labels are structural review labels and still require manual confirmation.",
]


@dataclass(frozen=True)
class SingleSymbolAdvisoryRequest:
    symbol: str
    candidates_path: Path | None = None
    scored_dataset_path: Path | None = None
    factor_dataset_path: Path | None = None
    signals_path: Path | None = None
    metadata_path: Path | None = None
    snapshot_manifest_path: Path | None = None
    advisory_date: str | pd.Timestamp | None = None
    alert_preview: bool = False


@dataclass(frozen=True)
class SingleSymbolAdvisoryIssue:
    severity: str
    category: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryArtifactPaths:
    artifact_dir: Path
    single_symbol_advisory_report: Path
    single_symbol_advisory_json: Path
    single_symbol_advisory_csv: Path
    metadata: Path
    alert_preview: Path | None = None

    def as_dict(self) -> dict[str, Path]:
        paths = {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_report": self.single_symbol_advisory_report,
            "single_symbol_advisory_json": self.single_symbol_advisory_json,
            "single_symbol_advisory_csv": self.single_symbol_advisory_csv,
            "metadata": self.metadata,
        }
        if self.alert_preview is not None:
            paths["alert_preview"] = self.alert_preview
        return paths


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerPaths:
    artifact_dir: Path
    single_symbol_advisory_answer: Path
    single_symbol_advisory_answer_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "single_symbol_advisory_answer": self.single_symbol_advisory_answer,
            "single_symbol_advisory_answer_json": self.single_symbol_advisory_answer_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SingleSymbolContext:
    symbol: str
    selected_row: dict[str, Any] | None
    selected_source_name: str
    source_artifact_path: Path | None
    found_in_candidates: bool
    found_in_scored_dataset: bool
    found_in_factor_dataset: bool
    found_in_signals: bool
    metadata: dict[str, Any]
    metadata_path: Path | None
    issues: list[SingleSymbolAdvisoryIssue]


@dataclass(frozen=True)
class SingleSymbolAdvisoryResult:
    advisory_run_id: str
    status: str
    symbol: str
    advisory_date: pd.Timestamp
    source_artifact_path: Path | None
    source_candidate_run_id: str
    found_in_candidates: bool
    found_in_scored_dataset: bool
    found_in_factor_dataset: bool
    found_in_signals: bool
    selection_profile: str
    demo_mode: bool
    not_strategy_recommendation: bool
    current_action: str
    score_action: str
    final_score: float | None
    advisory_action: str
    semantics_policy_source: str
    semantics_policy_version: str
    semantics_classifier: str
    semantics_settings_profile: str
    semantics_action: str
    semantics_reason: str
    semantics_manual_confirmation_required: bool
    semantics_auto_order_allowed: bool
    semantics_no_live_trading: bool
    semantics_no_broker_api: bool
    reason_summary: str
    supporting_factors: str
    risk_notes: str
    data_quality_notes: str
    entry_condition: str
    exit_condition: str
    invalidation_condition: str
    valid_until: str
    requires_manual_confirmation: bool
    auto_order_allowed: bool
    no_live_trading: bool
    no_broker_api: bool
    no_message_sent: bool
    alert_preview_requested: bool
    artifact_paths: dict[str, Path]
    issues: list[SingleSymbolAdvisoryIssue]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]
    source_row: dict[str, Any] | None

    def as_record(self) -> dict[str, Any]:
        return {
            "advisory_run_id": self.advisory_run_id,
            "status": self.status,
            "symbol": self.symbol,
            "advisory_date": str(self.advisory_date.date()),
            "source_artifact_path": str(self.source_artifact_path or ""),
            "source_candidate_run_id": self.source_candidate_run_id,
            "found_in_candidates": self.found_in_candidates,
            "found_in_scored_dataset": self.found_in_scored_dataset,
            "selection_profile": self.selection_profile,
            "demo_mode": self.demo_mode,
            "not_strategy_recommendation": self.not_strategy_recommendation,
            "current_action": self.current_action,
            "score_action": self.score_action,
            "final_score": self.final_score,
            "advisory_action": self.advisory_action,
            "semantics_policy_source": self.semantics_policy_source,
            "semantics_policy_version": self.semantics_policy_version,
            "semantics_classifier": self.semantics_classifier,
            "semantics_settings_profile": self.semantics_settings_profile,
            "semantics_action": self.semantics_action,
            "semantics_reason": self.semantics_reason,
            "semantics_manual_confirmation_required": self.semantics_manual_confirmation_required,
            "semantics_auto_order_allowed": self.semantics_auto_order_allowed,
            "semantics_no_live_trading": self.semantics_no_live_trading,
            "semantics_no_broker_api": self.semantics_no_broker_api,
            "reason_summary": self.reason_summary,
            "supporting_factors": self.supporting_factors,
            "risk_notes": self.risk_notes,
            "data_quality_notes": self.data_quality_notes,
            "entry_condition": self.entry_condition,
            "exit_condition": self.exit_condition,
            "invalidation_condition": self.invalidation_condition,
            "valid_until": self.valid_until,
            "requires_manual_confirmation": self.requires_manual_confirmation,
            "auto_order_allowed": self.auto_order_allowed,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_message_sent": self.no_message_sent,
        }


@dataclass(frozen=True)
class SingleSymbolAdvisoryAnswerResult:
    answer_run_id: str
    advisory_run_id: str
    symbol: str
    status: str
    advisory_action: str
    semantics_policy_source: str
    semantics_policy_version: str
    semantics_classifier: str
    semantics_settings_profile: str
    semantics_action: str
    semantics_reason: str
    semantics_manual_confirmation_required: bool
    semantics_auto_order_allowed: bool
    semantics_no_live_trading: bool
    semantics_no_broker_api: bool
    question: str
    answer_style: str
    short_answer: str
    answer_body: str
    requires_manual_confirmation: bool
    auto_order_allowed: bool
    no_live_trading: bool
    no_broker_api: bool
    no_message_sent: bool
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def build_single_symbol_advisory(
    symbol: str,
    *,
    candidates_path: str | Path | None = None,
    scored_dataset_path: str | Path | None = None,
    factor_dataset_path: str | Path | None = None,
    signals_path: str | Path | None = None,
    metadata_path: str | Path | None = None,
    snapshot_manifest_path: str | Path | None = None,
    advisory_date: str | pd.Timestamp | None = None,
    alert_preview: bool = False,
    output_dir: str | Path | None = None,
    settings: Settings | SingleSymbolAdvisorySettings | str | Path | None = None,
) -> SingleSymbolAdvisoryResult:
    """Build a local single-symbol advisory artifact from existing local CSV artifacts."""

    project_settings, advisory_settings = _resolve_settings(settings)
    if advisory_settings.enable_live_trading or advisory_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory cannot enable live trading or broker API access")
    if advisory_settings.enable_alert_delivery:
        raise ValueError("Single-symbol advisory renders local previews only; alert delivery must remain disabled")
    if advisory_settings.auto_order_allowed:
        raise ValueError("Single-symbol advisory cannot allow automatic order placement")
    if output_dir is not None:
        advisory_settings = advisory_settings.model_copy(update={"output_dir": Path(output_dir)})

    request = SingleSymbolAdvisoryRequest(
        symbol=normalize_symbol_value(symbol),
        candidates_path=_optional_path(candidates_path),
        scored_dataset_path=_optional_path(scored_dataset_path),
        factor_dataset_path=_optional_path(factor_dataset_path),
        signals_path=_optional_path(signals_path),
        metadata_path=_optional_path(metadata_path),
        snapshot_manifest_path=_optional_path(snapshot_manifest_path),
        advisory_date=advisory_date,
        alert_preview=alert_preview,
    )
    _assert_source_input(request)
    context = load_single_symbol_context(request)
    date = _resolve_advisory_date(request, context)
    row = context.selected_row
    status = "READY" if row is not None else "NOT_FOUND"
    source_candidate_run_id = _resolve_source_candidate_run_id(row, context)
    selection_profile = _resolve_value(row, context.metadata, "selection_profile", "")
    demo_mode = _resolve_bool(row, context.metadata, "demo_mode", False) or selection_profile.lower() == "demo"
    not_strategy = _resolve_bool(row, context.metadata, "not_strategy_recommendation", False) or demo_mode
    current_action = _resolve_action(row, ["action", "original_candidate_action", "current_action"])
    score_action = _resolve_action(row, ["score_action", "original_score_action"])
    final_score = _to_float(_row_get(row, "final_score", None) if row is not None else None)
    advisory_action = (
        classify_single_symbol_advisory_action(
            row or {},
            selection_profile=selection_profile,
            demo_mode=demo_mode,
            not_strategy_recommendation=not_strategy,
            snapshot_quality_status=_resolve_quality_status(row, context.metadata, "snapshot_quality_status"),
            data_quality_status=_resolve_quality_status(row, context.metadata, "data_quality_status"),
            semantics_settings=project_settings.signal_semantics,
        )
        if row is not None
        else "NO_ACTION"
    )
    valid_until = _valid_until(date, advisory_settings.default_validity_days)
    reason_summary = _reason_summary(
        status=status,
        advisory_action=advisory_action,
        score_action=score_action,
        current_action=current_action,
        final_score=final_score,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
        source_artifact_path=context.source_artifact_path,
    )
    semantics_provenance = build_signal_semantics_provenance(
        advisory_action=advisory_action,
        reason=reason_summary,
        settings=project_settings.signal_semantics,
        settings_profile=selection_profile or ("not_found" if status == "NOT_FOUND" else None),
    )
    supporting_factors = _supporting_factors(row)
    risk_notes = _risk_notes(row, advisory_action=advisory_action)
    snapshot_manifest_text = _resolve_snapshot_manifest_text(request, context)
    data_quality_notes = _data_quality_notes(context=context, snapshot_manifest_path=snapshot_manifest_text)
    advisory_run_id = generate_single_symbol_advisory_run_id(
        symbol=request.symbol,
        advisory_date=date,
        source_artifact_path=context.source_artifact_path,
        source_candidate_run_id=source_candidate_run_id,
        status=status,
        config_version=advisory_settings.config_version,
    )
    paths = resolve_single_symbol_advisory_artifact_paths(
        advisory_settings.output_dir,
        advisory_run_id,
        include_alert_preview=alert_preview,
    )
    result = SingleSymbolAdvisoryResult(
        advisory_run_id=advisory_run_id,
        status=status,
        symbol=request.symbol,
        advisory_date=date,
        source_artifact_path=context.source_artifact_path,
        source_candidate_run_id=source_candidate_run_id,
        found_in_candidates=context.found_in_candidates,
        found_in_scored_dataset=context.found_in_scored_dataset,
        found_in_factor_dataset=context.found_in_factor_dataset,
        found_in_signals=context.found_in_signals,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
        current_action=current_action,
        score_action=score_action,
        final_score=final_score,
        advisory_action=advisory_action,
        semantics_policy_source=semantics_provenance["semantics_policy_source"],
        semantics_policy_version=semantics_provenance["semantics_policy_version"],
        semantics_classifier=semantics_provenance["semantics_classifier"],
        semantics_settings_profile=semantics_provenance["semantics_settings_profile"],
        semantics_action=semantics_provenance["semantics_action"],
        semantics_reason=semantics_provenance["semantics_reason"],
        semantics_manual_confirmation_required=semantics_provenance["semantics_manual_confirmation_required"],
        semantics_auto_order_allowed=semantics_provenance["semantics_auto_order_allowed"],
        semantics_no_live_trading=semantics_provenance["semantics_no_live_trading"],
        semantics_no_broker_api=semantics_provenance["semantics_no_broker_api"],
        reason_summary=reason_summary,
        supporting_factors=supporting_factors,
        risk_notes=risk_notes,
        data_quality_notes=data_quality_notes,
        entry_condition=_entry_condition(advisory_action, demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        exit_condition=_exit_condition(advisory_action, demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        invalidation_condition=_invalidation_condition(status=status, demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        valid_until=valid_until,
        requires_manual_confirmation=True,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        no_message_sent=True,
        alert_preview_requested=alert_preview,
        artifact_paths=paths.as_dict(),
        issues=context.issues,
        known_limitations=SINGLE_SYMBOL_KNOWN_LIMITATIONS,
        audit_metadata=_build_audit_metadata(
            request=request,
            context=context,
            advisory_settings=advisory_settings,
            status=status,
            advisory_action=advisory_action,
            advisory_date=date,
            valid_until=valid_until,
            source_candidate_run_id=source_candidate_run_id,
            snapshot_manifest_path=snapshot_manifest_text,
        ),
        source_row=row,
    )
    if project_settings.single_symbol_advisory.write_artifacts and advisory_settings.write_artifacts:
        write_single_symbol_advisory_artifacts(result)
    return result


def load_single_symbol_context(request: SingleSymbolAdvisoryRequest) -> SingleSymbolContext:
    """Load local artifacts and find the requested symbol without numeric coercion."""

    symbol = normalize_symbol_value(request.symbol)
    metadata, metadata_path = _load_metadata(request)
    issues: list[SingleSymbolAdvisoryIssue] = []
    selected_row: dict[str, Any] | None = None
    selected_source_name = ""
    source_artifact_path: Path | None = None
    found = {
        "candidates": False,
        "scored_dataset": False,
        "factor_dataset": False,
        "signals": False,
    }
    for source_name, path in [
        ("candidates", request.candidates_path),
        ("scored_dataset", request.scored_dataset_path),
        ("factor_dataset", request.factor_dataset_path),
        ("signals", request.signals_path),
    ]:
        if path is None:
            continue
        frame = _load_symbol_frame(path, source_name)
        matches = _matching_symbol_rows(frame, symbol)
        if matches.empty:
            continue
        found[source_name] = True
        if selected_row is None:
            selected_row = matches.iloc[0].to_dict()
            selected_source_name = source_name
            source_artifact_path = path
    if selected_row is None:
        issues.append(
            SingleSymbolAdvisoryIssue(
                severity="INFO",
                category="SYMBOL_NOT_FOUND",
                message=f"Symbol {symbol} was not present in the provided local artifact inputs.",
            )
        )
    return SingleSymbolContext(
        symbol=symbol,
        selected_row=selected_row,
        selected_source_name=selected_source_name,
        source_artifact_path=source_artifact_path,
        found_in_candidates=found["candidates"],
        found_in_scored_dataset=found["scored_dataset"],
        found_in_factor_dataset=found["factor_dataset"],
        found_in_signals=found["signals"],
        metadata=metadata,
        metadata_path=metadata_path,
        issues=issues,
    )


def classify_single_symbol_advisory_action(
    row: pd.Series | dict[str, Any],
    *,
    selection_profile: str | None = None,
    demo_mode: bool | None = None,
    not_strategy_recommendation: bool | None = None,
    snapshot_quality_status: str | None = None,
    data_quality_status: str | None = None,
    semantics_settings: SignalSemanticsSettings | None = None,
) -> str:
    """Classify one local source row via the shared signal semantics policy."""

    return classify_signal_semantics_action(
        row,
        settings=semantics_settings,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy_recommendation,
        snapshot_quality_status=snapshot_quality_status,
        data_quality_status=data_quality_status,
    )


def render_single_symbol_advisory_report(result: SingleSymbolAdvisoryResult) -> str:
    """Render a markdown report for a single-symbol advisory review."""

    lines = [
        f"# Single-Symbol Advisory Review: {result.symbol}",
        "",
        "This advisory artifact is not an order, approval, or broker instruction.",
        "No live trading, broker API, automated order placement, or message delivery was invoked.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "advisory_run_id": result.advisory_run_id,
                "status": result.status,
                "symbol": result.symbol,
                "advisory_date": result.advisory_date.date(),
                "advisory_action": result.advisory_action,
                "final_score": result.final_score,
                "selection_profile": result.selection_profile,
                "demo_mode": result.demo_mode,
                "not_strategy_recommendation": result.not_strategy_recommendation,
                "source_artifact_path": result.source_artifact_path or "",
                "valid_until": result.valid_until,
            }
        ),
        "",
        "## Answer",
        "",
        f"- Advisory action: `{result.advisory_action}`",
        f"- Reason: {result.reason_summary}",
        f"- Supporting factors: {result.supporting_factors or 'not provided'}",
        f"- Risk notes: {result.risk_notes}",
        f"- Data-quality notes: {result.data_quality_notes}",
        f"- Entry condition: {result.entry_condition}",
        f"- Exit condition: {result.exit_condition}",
        f"- Invalidation condition: {result.invalidation_condition}",
        "",
        "## Safety Contract",
        "",
        _dict_table(
            {
                "requires_manual_confirmation": result.requires_manual_confirmation,
                "auto_order_allowed": result.auto_order_allowed,
                "no_live_trading": result.no_live_trading,
                "no_broker_api": result.no_broker_api,
                "no_message_sent": result.no_message_sent,
                "approved_for_paper_applied": False,
            }
        ),
        "",
        "## Issues",
        "",
        _issues_section(result.issues),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    if result.alert_preview_requested:
        lines.extend(["## Alert Preview", "", render_single_symbol_alert_preview(result), ""])
    return "\n".join(str(line) for line in lines)


def write_single_symbol_advisory_artifacts(result: SingleSymbolAdvisoryResult) -> dict[str, Path]:
    """Write report, CSV, JSON, metadata, and optional local alert preview."""

    paths = SingleSymbolAdvisoryArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    record = result.as_record()
    _export_records([record], paths.single_symbol_advisory_csv)
    paths.single_symbol_advisory_json.write_text(
        json.dumps(_json_safe(_build_result_payload(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_single_symbol_advisory_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.single_symbol_advisory_report.write_text(render_single_symbol_advisory_report(result), encoding="utf-8")
    if paths.alert_preview is not None:
        paths.alert_preview.write_text(render_single_symbol_alert_preview(result), encoding="utf-8")
    return paths.as_dict()


def render_single_symbol_alert_preview(result: SingleSymbolAdvisoryResult) -> str:
    """Render a local-only alert preview for one symbol."""

    score_text = "UNKNOWN" if result.final_score is None else f"{result.final_score:.2f}"
    lines = [
        "# Local Alert Preview",
        "",
        "No message was sent. Manual confirmation is required. No auto-order is allowed.",
        "",
        f"## {result.symbol}: {result.advisory_action}",
        "",
        f"- Score: {score_text}",
        f"- Reason: {result.reason_summary}",
        f"- Risk: {result.risk_notes}",
        f"- Valid until: {result.valid_until}",
        f"- Data quality: {result.data_quality_notes}",
        f"- Requires manual confirmation: {result.requires_manual_confirmation}",
        f"- Auto-order allowed: {result.auto_order_allowed}",
        f"- No live trading: {result.no_live_trading}",
        f"- No broker API: {result.no_broker_api}",
    ]
    return "\n".join(lines)


def build_single_symbol_advisory_answer(
    result: SingleSymbolAdvisoryResult,
    *,
    question: str | None = None,
    answer_style: str = "concise",
    output_dir: str | Path | None = None,
    settings: Settings | SingleSymbolAdvisorySettings | str | Path | None = None,
) -> SingleSymbolAdvisoryAnswerResult:
    """Render and write a deterministic question-style local advisory answer."""

    project_settings, advisory_settings = _resolve_settings(settings)
    if advisory_settings.enable_live_trading or advisory_settings.enable_broker_api:
        raise ValueError("Single-symbol advisory answer cannot enable live trading or broker API access")
    if advisory_settings.enable_alert_delivery:
        raise ValueError("Single-symbol advisory answer does not deliver messages")
    if advisory_settings.auto_order_allowed:
        raise ValueError("Single-symbol advisory answer cannot allow automatic order placement")
    normalized_style = str(answer_style or "concise").strip().lower()
    if normalized_style not in {"concise", "detailed"}:
        raise ValueError("answer_style must be 'concise' or 'detailed'")
    effective_output_dir = Path(output_dir) if output_dir is not None else advisory_settings.answer_output_dir
    question_text = str(question or "").strip()
    answer_run_id = generate_single_symbol_advisory_answer_run_id(
        advisory_run_id=result.advisory_run_id,
        symbol=result.symbol,
        question=question_text,
        answer_style=normalized_style,
        config_version=advisory_settings.config_version,
    )
    paths = resolve_single_symbol_advisory_answer_paths(effective_output_dir, answer_run_id)
    short_answer = _question_style_short_answer(result)
    answer_body = render_single_symbol_advisory_answer(
        result,
        answer_run_id=answer_run_id,
        question=question_text,
        answer_style=normalized_style,
        short_answer=short_answer,
    )
    answer = SingleSymbolAdvisoryAnswerResult(
        answer_run_id=answer_run_id,
        advisory_run_id=result.advisory_run_id,
        symbol=result.symbol,
        status=result.status,
        advisory_action=result.advisory_action,
        semantics_policy_source=result.semantics_policy_source,
        semantics_policy_version=result.semantics_policy_version,
        semantics_classifier=result.semantics_classifier,
        semantics_settings_profile=result.semantics_settings_profile,
        semantics_action=result.semantics_action,
        semantics_reason=result.semantics_reason,
        semantics_manual_confirmation_required=result.semantics_manual_confirmation_required,
        semantics_auto_order_allowed=result.semantics_auto_order_allowed,
        semantics_no_live_trading=result.semantics_no_live_trading,
        semantics_no_broker_api=result.semantics_no_broker_api,
        question=question_text,
        answer_style=normalized_style,
        short_answer=short_answer,
        answer_body=answer_body,
        requires_manual_confirmation=result.requires_manual_confirmation,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        no_message_sent=True,
        artifact_paths=paths.as_dict(),
        audit_metadata={
            "answer_run_id_source": "single_symbol_advisory_answer_v0.1",
            "advisory_run_id": result.advisory_run_id,
            "symbol": result.symbol,
            "question": question_text,
            "answer_style": normalized_style,
            "status": result.status,
            "advisory_action": result.advisory_action,
            "semantics_policy_source": result.semantics_policy_source,
            "semantics_policy_version": result.semantics_policy_version,
            "semantics_classifier": result.semantics_classifier,
            "semantics_settings_profile": result.semantics_settings_profile,
            "semantics_action": result.semantics_action,
            "semantics_reason": result.semantics_reason,
            "semantics_manual_confirmation_required": result.semantics_manual_confirmation_required,
            "semantics_auto_order_allowed": result.semantics_auto_order_allowed,
            "semantics_no_live_trading": result.semantics_no_live_trading,
            "semantics_no_broker_api": result.semantics_no_broker_api,
            "demo_mode": result.demo_mode,
            "not_strategy_recommendation": result.not_strategy_recommendation,
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
            "external_api_called": False,
            "llm_api_called": False,
            "config_summary": {
                "config_version": advisory_settings.config_version,
                "answer_output_dir": str(effective_output_dir),
            },
        },
    )
    if project_settings.single_symbol_advisory.write_artifacts and advisory_settings.write_artifacts:
        write_single_symbol_advisory_answer_artifacts(answer, result)
    return answer


def render_single_symbol_advisory_answer(
    result: SingleSymbolAdvisoryResult,
    *,
    answer_run_id: str,
    question: str,
    answer_style: str,
    short_answer: str,
) -> str:
    """Render a local deterministic answer to a one-symbol review question."""

    score_text = "not available" if result.final_score is None else f"{result.final_score:.6f}"
    question_text = question or "Single-symbol advisory review"
    lines = [
        f"# Single-Symbol Advisory Answer: {result.symbol}",
        "",
        "This is a local deterministic rendering of a single-symbol advisory artifact. It is not LLM-generated.",
        "It is not an order, approval, broker instruction, or message-delivery workflow.",
        "",
        "## Question",
        "",
        question_text,
        "",
        "## Short Answer",
        "",
        short_answer,
        "",
        "## Advisory Context",
        "",
        f"- Symbol: `{result.symbol}`",
        f"- Advisory action: `{result.advisory_action}`",
        f"- Status: `{result.status}`",
        f"- Score: `{score_text}`",
        f"- Current action: `{result.current_action or 'UNKNOWN'}`",
        f"- Score action: `{result.score_action or 'UNKNOWN'}`",
        f"- Selection profile: `{result.selection_profile or 'UNKNOWN'}`",
        f"- Demo mode: `{result.demo_mode}`",
        f"- Not strategy recommendation: `{result.not_strategy_recommendation}`",
        "",
        "## Why",
        "",
        result.reason_summary,
        "",
        "## Risk And Data Caveats",
        "",
        f"- Risk notes: {result.risk_notes}",
        f"- Data/source caveats: {result.data_quality_notes}",
        "",
        "## Timing And Conditions",
        "",
        f"- Entry consideration: {result.entry_condition}",
        f"- Exit consideration: {result.exit_condition}",
        f"- Invalidation condition: {result.invalidation_condition}",
        f"- Valid until: `{result.valid_until}`",
        "",
        "## Safety",
        "",
        f"- Manual confirmation required: `{result.requires_manual_confirmation}`",
        "- Auto-order allowed: `False`",
        "- No live trading: `True`",
        "- No broker API: `True`",
        "- No message sent: `True`",
    ]
    if result.demo_mode or result.not_strategy_recommendation or result.advisory_action == "DEMO_ONLY":
        lines.extend(
            [
                "",
                "## Demo Boundary",
                "",
                "Demo-only review: this artifact is suitable for workflow validation, not a real trading recommendation.",
            ]
        )
    if result.status == "NOT_FOUND":
        lines.extend(
            [
                "",
                "## Missing Symbol Boundary",
                "",
                "I cannot review this symbol from the provided local artifact because it is not present. No recommendation was invented.",
            ]
        )
    if answer_style == "detailed":
        lines.extend(
            [
                "",
                "## Supporting Factors",
                "",
                result.supporting_factors or "No supporting factor details were available in the source row.",
                "",
                "## Source",
                "",
                f"- Advisory run id: `{result.advisory_run_id}`",
                f"- Answer run id: `{answer_run_id}`",
                f"- Source artifact path: `{result.source_artifact_path or ''}`",
                f"- Source candidate run id: `{result.source_candidate_run_id}`",
            ]
        )
    return "\n".join(lines)


def write_single_symbol_advisory_answer_artifacts(
    answer: SingleSymbolAdvisoryAnswerResult,
    advisory: SingleSymbolAdvisoryResult,
) -> dict[str, Path]:
    """Write local question-style answer markdown, JSON, and metadata."""

    paths = SingleSymbolAdvisoryAnswerPaths(**answer.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    paths.single_symbol_advisory_answer.write_text(answer.answer_body, encoding="utf-8")
    payload = _single_symbol_advisory_answer_payload(answer, advisory)
    paths.single_symbol_advisory_answer_json.write_text(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_single_symbol_advisory_answer_metadata(answer, advisory, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def build_single_symbol_advisory_answer_metadata(
    answer: SingleSymbolAdvisoryAnswerResult,
    advisory: SingleSymbolAdvisoryResult,
    paths: SingleSymbolAdvisoryAnswerPaths,
) -> dict[str, Any]:
    """Build metadata.json for a question-style advisory answer."""

    return {
        "answer_run_id": answer.answer_run_id,
        "created_at": advisory.advisory_date.isoformat(),
        "advisory_run_id": answer.advisory_run_id,
        "symbol": answer.symbol,
        "status": answer.status,
        "advisory_action": answer.advisory_action,
        "semantics_policy_source": answer.semantics_policy_source,
        "semantics_policy_version": answer.semantics_policy_version,
        "semantics_classifier": answer.semantics_classifier,
        "semantics_settings_profile": answer.semantics_settings_profile,
        "semantics_action": answer.semantics_action,
        "semantics_reason": answer.semantics_reason,
        "semantics_manual_confirmation_required": answer.semantics_manual_confirmation_required,
        "semantics_auto_order_allowed": answer.semantics_auto_order_allowed,
        "semantics_no_live_trading": answer.semantics_no_live_trading,
        "semantics_no_broker_api": answer.semantics_no_broker_api,
        "question": answer.question,
        "answer_style": answer.answer_style,
        "short_answer": answer.short_answer,
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
        "llm_api_called": False,
        "external_api_called": False,
        "demo_mode": advisory.demo_mode,
        "not_strategy_recommendation": advisory.not_strategy_recommendation,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "source_advisory_artifacts": {
            key: str(value) for key, value in advisory.artifact_paths.items() if key != "artifact_dir"
        },
        "audit_metadata": answer.audit_metadata,
    }


def build_single_symbol_advisory_metadata(
    result: SingleSymbolAdvisoryResult,
    paths: SingleSymbolAdvisoryArtifactPaths,
) -> dict[str, Any]:
    """Build metadata.json for a single-symbol advisory run."""

    return {
        "advisory_run_id": result.advisory_run_id,
        "created_at": result.advisory_date.isoformat(),
        "status": result.status,
        "symbol": result.symbol,
        "advisory_date": result.advisory_date,
        "source_artifact_path": str(result.source_artifact_path or ""),
        "source_candidate_run_id": result.source_candidate_run_id,
        "selection_profile": result.selection_profile,
        "demo_mode": result.demo_mode,
        "not_strategy_recommendation": result.not_strategy_recommendation,
        "advisory_action": result.advisory_action,
        "semantics_policy_source": result.semantics_policy_source,
        "semantics_policy_version": result.semantics_policy_version,
        "semantics_classifier": result.semantics_classifier,
        "semantics_settings_profile": result.semantics_settings_profile,
        "semantics_action": result.semantics_action,
        "semantics_reason": result.semantics_reason,
        "semantics_manual_confirmation_required": result.semantics_manual_confirmation_required,
        "semantics_auto_order_allowed": result.semantics_auto_order_allowed,
        "semantics_no_live_trading": result.semantics_no_live_trading,
        "semantics_no_broker_api": result.semantics_no_broker_api,
        "final_score": result.final_score,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "alert_delivery_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "issues": [issue.as_dict() for issue in result.issues],
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
    }


def generate_single_symbol_advisory_run_id(
    *,
    symbol: str,
    advisory_date: str | pd.Timestamp,
    source_artifact_path: Path | None,
    source_candidate_run_id: str,
    status: str,
    config_version: str,
) -> str:
    payload = {
        "symbol": normalize_symbol_value(symbol),
        "advisory_date": str(_normalize_date(advisory_date).date()),
        "source_artifact_path": str(source_artifact_path or ""),
        "source_candidate_run_id": source_candidate_run_id,
        "status": status,
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_single_symbol_advisory_artifact_paths(
    output_dir: str | Path,
    advisory_run_id: str,
    *,
    include_alert_preview: bool,
) -> SingleSymbolAdvisoryArtifactPaths:
    artifact_dir = Path(output_dir) / advisory_run_id
    return SingleSymbolAdvisoryArtifactPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_report=artifact_dir / "single_symbol_advisory_report.md",
        single_symbol_advisory_json=artifact_dir / "single_symbol_advisory.json",
        single_symbol_advisory_csv=artifact_dir / "single_symbol_advisory.csv",
        metadata=artifact_dir / "metadata.json",
        alert_preview=artifact_dir / "alert_preview.md" if include_alert_preview else None,
    )


def generate_single_symbol_advisory_answer_run_id(
    *,
    advisory_run_id: str,
    symbol: str,
    question: str,
    answer_style: str,
    config_version: str,
) -> str:
    payload = {
        "advisory_run_id": advisory_run_id,
        "symbol": normalize_symbol_value(symbol),
        "question": question,
        "answer_style": answer_style,
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_single_symbol_advisory_answer_paths(
    output_dir: str | Path,
    answer_run_id: str,
) -> SingleSymbolAdvisoryAnswerPaths:
    artifact_dir = Path(output_dir) / answer_run_id
    return SingleSymbolAdvisoryAnswerPaths(
        artifact_dir=artifact_dir,
        single_symbol_advisory_answer=artifact_dir / "single_symbol_advisory_answer.md",
        single_symbol_advisory_answer_json=artifact_dir / "single_symbol_advisory_answer.json",
        metadata=artifact_dir / "metadata.json",
    )


def _assert_source_input(request: SingleSymbolAdvisoryRequest) -> None:
    if request.candidates_path is None and request.scored_dataset_path is None and request.signals_path is None:
        raise ValueError("Provide at least one of --candidates, --scored-dataset, or --signals")
    for label, path in [
        ("candidates", request.candidates_path),
        ("scored dataset", request.scored_dataset_path),
        ("factor dataset", request.factor_dataset_path),
        ("signals", request.signals_path),
        ("metadata", request.metadata_path),
        ("snapshot manifest", request.snapshot_manifest_path),
    ]:
        if path is not None and not path.exists():
            raise FileNotFoundError(f"{label} path not found: {path}")


def _load_symbol_frame(path: Path, source_name: str) -> pd.DataFrame:
    frame = read_csv_preserve_symbol_columns(path)
    if "symbol" not in frame.columns:
        raise ValueError(f"{source_name} artifact must include a symbol column: {path}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output


def _matching_symbol_rows(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    normalized = normalize_symbol_value(symbol)
    return frame[frame["symbol"].map(normalize_symbol_value) == normalized].reset_index(drop=True)


def _load_metadata(request: SingleSymbolAdvisoryRequest) -> tuple[dict[str, Any], Path | None]:
    candidates = [
        request.metadata_path,
        _sibling_metadata(request.candidates_path),
        _sibling_metadata(request.scored_dataset_path),
        _sibling_metadata(request.factor_dataset_path),
        _sibling_metadata(request.signals_path),
    ]
    for path in candidates:
        if path is not None and path.exists():
            return json.loads(path.read_text(encoding="utf-8")), path
    return {}, None


def _sibling_metadata(path: Path | None) -> Path | None:
    if path is None:
        return None
    sibling = path.parent / "metadata.json"
    return sibling if sibling.exists() else None


def _resolve_advisory_date(
    request: SingleSymbolAdvisoryRequest,
    context: SingleSymbolContext,
) -> pd.Timestamp:
    if request.advisory_date is not None:
        return _normalize_date(request.advisory_date)
    row = context.selected_row
    for value in [
        _row_get(row, "decision_date", None),
        _row_get(row, "signal_date", None),
        context.metadata.get("decision_date"),
        context.metadata.get("signal_date"),
        (context.metadata.get("audit_metadata") or {}).get("decision_date"),
    ]:
        if _present(value):
            return _normalize_date(value)
    return pd.Timestamp.utcnow().tz_localize(None).normalize()


def _resolve_source_candidate_run_id(row: dict[str, Any] | None, context: SingleSymbolContext) -> str:
    for value in [
        _row_get(row, "current_candidate_run_id", None),
        _row_get(row, "source_candidate_run_id", None),
        _row_get(row, "source_run_id", None),
        context.metadata.get("run_id"),
        context.metadata.get("source_candidate_run_id"),
        (context.metadata.get("audit_metadata") or {}).get("run_id"),
        (context.metadata.get("audit_metadata") or {}).get("source_candidate_run_id"),
    ]:
        if _present(value):
            return str(value)
    if context.source_artifact_path is not None and "_" in context.source_artifact_path.parent.name:
        return context.source_artifact_path.parent.name.rsplit("_", 1)[-1]
    return "UNKNOWN_CANDIDATE_RUN"


def _resolve_value(row: dict[str, Any] | None, metadata: dict[str, Any], key: str, default: str) -> str:
    for value in [
        _row_get(row, key, None),
        metadata.get(key),
        (metadata.get("audit_metadata") or {}).get(key),
        (metadata.get("config_summary") or {}).get(key),
    ]:
        if _present(value):
            return str(value).strip()
    return default


def _resolve_bool(row: dict[str, Any] | None, metadata: dict[str, Any], key: str, default: bool) -> bool:
    for value in [
        _row_get(row, key, None),
        metadata.get(key),
        (metadata.get("audit_metadata") or {}).get(key),
        (metadata.get("config_summary") or {}).get(key),
    ]:
        if _present(value):
            return _to_bool(value)
    return default


def _resolve_quality_status(row: dict[str, Any] | None, metadata: dict[str, Any], key: str) -> str | None:
    value = _resolve_value(row, metadata, key, "")
    if _present(value):
        return value
    nested_key = key.removesuffix("_status")
    nested = metadata.get(nested_key)
    if isinstance(nested, dict):
        nested_value = nested.get("status")
        if _present(nested_value):
            return str(nested_value)
    return None


def _resolve_action(row: dict[str, Any] | None, keys: list[str]) -> str:
    for key in keys:
        value = _row_get(row, key, None)
        if _present(value):
            return str(value).strip().upper()
    return ""


def _resolve_snapshot_manifest_text(request: SingleSymbolAdvisoryRequest, context: SingleSymbolContext) -> str:
    for value in [
        request.snapshot_manifest_path,
        _row_get(context.selected_row, "snapshot_manifest_path", None),
        context.metadata.get("snapshot_manifest_path"),
        (context.metadata.get("audit_metadata") or {}).get("snapshot_quality_manifest_path"),
        ((context.metadata.get("config_summary") or {}).get("snapshot_quality_preflight") or {}).get(
            "snapshot_quality_manifest_path"
        ),
    ]:
        if _present(value):
            return str(value)
    return ""


def _reason_summary(
    *,
    status: str,
    advisory_action: str,
    score_action: str,
    current_action: str,
    final_score: float | None,
    demo_mode: bool,
    not_strategy_recommendation: bool,
    source_artifact_path: Path | None,
) -> str:
    if status == "NOT_FOUND":
        return "Symbol was not present in the provided local artifact; no recommendation was invented."
    score_text = "UNKNOWN" if final_score is None else f"{final_score:.2f}"
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return (
            "Demo workflow validation only; not a strategy recommendation. "
            f"Source action={current_action or 'UNKNOWN'}, score_action={score_action or 'UNKNOWN'}, "
            f"final_score={score_text}, source_artifact={source_artifact_path}."
        )
    if advisory_action == "BLOCKED":
        return (
            "Source artifact indicates a blocked or risk-blocked row; do not treat this as actionable until reviewed. "
            f"Source action={current_action or 'UNKNOWN'}, score_action={score_action or 'UNKNOWN'}, "
            f"final_score={score_text}."
        )
    return (
        "Manual research review required before any action. "
        f"Advisory action={advisory_action}, source action={current_action or 'UNKNOWN'}, "
        f"score_action={score_action or 'UNKNOWN'}, final_score={score_text}."
    )


def _supporting_factors(row: dict[str, Any] | None) -> str:
    if row is None:
        return ""
    score_breakdown = _row_get(row, "score_breakdown", "")
    if _present(score_breakdown):
        return str(score_breakdown)
    keys = [
        "technical_score",
        "liquidity_score",
        "expectation_score",
        "reality_score",
        "sentiment_score",
        "risk_penalty",
        "rank",
        "selection_reason",
        "score_reason",
    ]
    values = {key: _row_get(row, key, "") for key in keys if _present(_row_get(row, key, ""))}
    return json.dumps(_json_safe(values), sort_keys=True) if values else ""


def _risk_notes(row: dict[str, Any] | None, *, advisory_action: str) -> str:
    if row is None:
        return "Symbol was not found; no source risk context is available."
    status = _text(_row_get(row, "risk_precheck_status", "UNKNOWN")) or "UNKNOWN"
    reason = _text(_row_get(row, "risk_precheck_reason", "")) or _text(_row_get(row, "risk_notes", ""))
    return (
        f"risk_precheck_status={status}; risk_precheck_reason={reason or 'not provided'}; "
        f"advisory_action={advisory_action}; manual confirmation required; auto-order disabled."
    )


def _data_quality_notes(*, context: SingleSymbolContext, snapshot_manifest_path: str) -> str:
    if context.selected_row is not None and _present(_row_get(context.selected_row, "data_quality_notes", "")):
        return str(_row_get(context.selected_row, "data_quality_notes", "")).strip()
    return (
        "Uses local artifact rows only; "
        f"source_artifact={context.source_artifact_path or 'not found'}; "
        f"snapshot_manifest_path={snapshot_manifest_path or 'not provided'}."
    )


def _entry_condition(advisory_action: str, *, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if advisory_action == "BLOCKED":
        return "No entry condition; row is blocked until the risk/data issue is reviewed."
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return "No entry condition; demo advisory is workflow validation only."
    return "Manual reviewer must confirm strategy, data quality, risk, timing, and execution assumptions before any action."


def _exit_condition(advisory_action: str, *, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if advisory_action in {"BLOCKED", "DEMO_ONLY"} or demo_mode or not_strategy_recommendation:
        return "No exit condition; no position or order is created by this advisory artifact."
    return "Manual reviewer must define exit criteria before any paper or future execution action."


def _invalidation_condition(*, status: str, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if status == "NOT_FOUND":
        return "Invalid until the symbol appears in a local candidate, scored, or signal artifact."
    if demo_mode or not_strategy_recommendation:
        return "Invalid outside local demo validation context or if source artifacts change."
    return "Invalid if newer data, quality checks, risk review, or manual research contradicts this advisory artifact."


def _valid_until(advisory_date: pd.Timestamp, validity_days: int) -> str:
    return str((_normalize_date(advisory_date) + pd.Timedelta(days=int(validity_days))).date())


def _build_audit_metadata(
    *,
    request: SingleSymbolAdvisoryRequest,
    context: SingleSymbolContext,
    advisory_settings: SingleSymbolAdvisorySettings,
    status: str,
    advisory_action: str,
    advisory_date: pd.Timestamp,
    valid_until: str,
    source_candidate_run_id: str,
    snapshot_manifest_path: str,
) -> dict[str, Any]:
    return {
        "advisory_run_id_source": "single_symbol_advisory_v0.1",
        "requested_symbol": request.symbol,
        "status": status,
        "advisory_action": advisory_action,
        **build_signal_semantics_provenance(
            advisory_action=advisory_action,
            reason="Single-symbol advisory audit metadata records the shared semantics classifier used for the advisory action.",
            settings_profile=(context.metadata.get("selection_profile") or ""),
        ),
        "advisory_date": advisory_date,
        "valid_until": valid_until,
        "source_candidate_run_id": source_candidate_run_id,
        "candidates_path": str(request.candidates_path or ""),
        "scored_dataset_path": str(request.scored_dataset_path or ""),
        "factor_dataset_path": str(request.factor_dataset_path or ""),
        "signals_path": str(request.signals_path or ""),
        "metadata_path": str(context.metadata_path or ""),
        "snapshot_manifest_path": snapshot_manifest_path,
        "found_in_candidates": context.found_in_candidates,
        "found_in_scored_dataset": context.found_in_scored_dataset,
        "found_in_factor_dataset": context.found_in_factor_dataset,
        "found_in_signals": context.found_in_signals,
        "source_artifact_kind": context.selected_source_name,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "alert_delivery_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "approved_for_paper_applied": False,
        "config_summary": {
            "config_version": advisory_settings.config_version,
            "output_dir": str(advisory_settings.output_dir),
            "default_validity_days": advisory_settings.default_validity_days,
            "enable_alert_delivery": advisory_settings.enable_alert_delivery,
            "enable_live_trading": advisory_settings.enable_live_trading,
            "enable_broker_api": advisory_settings.enable_broker_api,
            "auto_order_allowed": advisory_settings.auto_order_allowed,
        },
    }


def _build_result_payload(result: SingleSymbolAdvisoryResult) -> dict[str, Any]:
    return {
        "record": result.as_record(),
        "found_in_factor_dataset": result.found_in_factor_dataset,
        "found_in_signals": result.found_in_signals,
        "alert_preview_requested": result.alert_preview_requested,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "issues": [issue.as_dict() for issue in result.issues],
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "source_row": result.source_row or {},
    }


def _single_symbol_advisory_answer_payload(
    answer: SingleSymbolAdvisoryAnswerResult,
    advisory: SingleSymbolAdvisoryResult,
) -> dict[str, Any]:
    return {
        "answer_run_id": answer.answer_run_id,
        "advisory_run_id": answer.advisory_run_id,
        "symbol": answer.symbol,
        "status": answer.status,
        "advisory_action": answer.advisory_action,
        "semantics_policy_source": answer.semantics_policy_source,
        "semantics_policy_version": answer.semantics_policy_version,
        "semantics_classifier": answer.semantics_classifier,
        "semantics_settings_profile": answer.semantics_settings_profile,
        "semantics_action": answer.semantics_action,
        "semantics_reason": answer.semantics_reason,
        "semantics_manual_confirmation_required": answer.semantics_manual_confirmation_required,
        "semantics_auto_order_allowed": answer.semantics_auto_order_allowed,
        "semantics_no_live_trading": answer.semantics_no_live_trading,
        "semantics_no_broker_api": answer.semantics_no_broker_api,
        "question": answer.question,
        "answer_style": answer.answer_style,
        "short_answer": answer.short_answer,
        "answer_body": answer.answer_body,
        "requires_manual_confirmation": answer.requires_manual_confirmation,
        "auto_order_allowed": answer.auto_order_allowed,
        "no_live_trading": answer.no_live_trading,
        "no_broker_api": answer.no_broker_api,
        "no_message_sent": answer.no_message_sent,
        "advisory_record": advisory.as_record(),
        "artifact_paths": {key: str(value) for key, value in answer.artifact_paths.items()},
        "audit_metadata": answer.audit_metadata,
    }


def _question_style_short_answer(result: SingleSymbolAdvisoryResult) -> str:
    if result.status == "NOT_FOUND":
        return (
            "I cannot review this symbol from the provided local artifact because it is not present; "
            "no recommendation was invented."
        )
    if result.advisory_action == "BLOCKED":
        return "The local artifact marks this symbol as blocked; review the risk/data issue before considering any action."
    if result.demo_mode or result.not_strategy_recommendation or result.advisory_action == "DEMO_ONLY":
        return "Demo-only review for workflow validation; do not treat this as a real trading recommendation."
    if result.advisory_action == "NO_ACTION":
        return "The local artifact does not support an action; wait or review manually with newer evidence."
    if result.advisory_action == "WATCH":
        return "Watch-only review; manual confirmation and fresher evidence are required before any action."
    if result.advisory_action == "REVIEW_BUY_CANDIDATE":
        return "Review-buy candidate only; manual confirmation is required and no automatic order is allowed."
    if result.advisory_action == "REVIEW_SELL_CANDIDATE":
        return "Review-sell candidate only; manual confirmation is required and no automatic order is allowed."
    if result.advisory_action == "HOLD_REVIEW":
        return "Hold-review context only; manual confirmation is required before changing any position state."
    return "Review-only advisory context; manual confirmation is required and no automatic order is allowed."


def _resolve_settings(
    settings: Settings | SingleSymbolAdvisorySettings | str | Path | None,
) -> tuple[Settings, SingleSymbolAdvisorySettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.single_symbol_advisory
    if isinstance(settings, Settings):
        return settings, settings.single_symbol_advisory
    if isinstance(settings, SingleSymbolAdvisorySettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"single_symbol_advisory": settings}), settings
    project = load_settings(Path(settings))
    return project, project.single_symbol_advisory


def _optional_path(value: str | Path | None) -> Path | None:
    return None if value is None else Path(value)


def _normalize_action(value: Any) -> str:
    return str(value or "").strip().upper()


def _row_get(row: pd.Series | dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if row is None:
        return default
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
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _issues_section(issues: list[SingleSymbolAdvisoryIssue]) -> str:
    if not issues:
        return "- None"
    return "\n".join(f"- {issue.severity} {issue.category}: {issue.message}" for issue in issues)


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


def _export_records(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records, columns=SINGLE_SYMBOL_ADVISORY_COLUMNS)
    frame.to_csv(path, index=False)


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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
