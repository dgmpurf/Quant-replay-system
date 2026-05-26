"""Signal advisory artifacts and local alert previews from current candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import Settings, SignalAdvisorySettings, load_settings
from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


ADVISORY_ACTIONS = {
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
    "DEMO_ONLY",
}

SIGNAL_ADVISORY_LIMITATIONS = [
    "Signals are advisory artifacts only; they are not orders.",
    "Every signal requires manual confirmation before any human action.",
    "No live trading, broker API, automated order placement, or message delivery is implemented.",
    "Demo current-candidate inputs remain workflow validation only and are not strategy recommendations.",
    "Future alert delivery should consume these local artifacts without changing trading state.",
]

SIGNAL_COLUMNS = [
    "signal_id",
    "signal_run_id",
    "signal_date",
    "decision_date",
    "symbol",
    "name",
    "instrument_type",
    "source_candidate_run_id",
    "selection_profile",
    "demo_mode",
    "not_strategy_recommendation",
    "advisory_action",
    "original_score_action",
    "original_candidate_action",
    "final_score",
    "confidence_level",
    "reason_summary",
    "score_breakdown",
    "entry_condition",
    "exit_condition",
    "invalidation_condition",
    "valid_until",
    "risk_notes",
    "data_source_notes",
    "snapshot_manifest_path",
    "candidates_path",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "alert_title",
    "alert_body",
]


@dataclass(frozen=True)
class SignalAdvisoryInput:
    candidates_path: Path
    candidate_report_path: Path | None = None
    metadata_path: Path | None = None


@dataclass(frozen=True)
class SignalAdvisorySignal:
    signal_id: str
    signal_run_id: str
    signal_date: str
    decision_date: str
    symbol: str
    name: str
    instrument_type: str
    source_candidate_run_id: str
    selection_profile: str
    demo_mode: bool
    not_strategy_recommendation: bool
    advisory_action: str
    original_score_action: str
    original_candidate_action: str
    final_score: float | None
    confidence_level: str
    reason_summary: str
    score_breakdown: str
    entry_condition: str
    exit_condition: str
    invalidation_condition: str
    valid_until: str
    risk_notes: str
    data_source_notes: str
    snapshot_manifest_path: str
    candidates_path: str
    requires_manual_confirmation: bool
    auto_order_allowed: bool
    no_live_trading: bool
    no_broker_api: bool
    alert_title: str
    alert_body: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_run_id": self.signal_run_id,
            "signal_date": self.signal_date,
            "decision_date": self.decision_date,
            "symbol": self.symbol,
            "name": self.name,
            "instrument_type": self.instrument_type,
            "source_candidate_run_id": self.source_candidate_run_id,
            "selection_profile": self.selection_profile,
            "demo_mode": self.demo_mode,
            "not_strategy_recommendation": self.not_strategy_recommendation,
            "advisory_action": self.advisory_action,
            "original_score_action": self.original_score_action,
            "original_candidate_action": self.original_candidate_action,
            "final_score": self.final_score,
            "confidence_level": self.confidence_level,
            "reason_summary": self.reason_summary,
            "score_breakdown": self.score_breakdown,
            "entry_condition": self.entry_condition,
            "exit_condition": self.exit_condition,
            "invalidation_condition": self.invalidation_condition,
            "valid_until": self.valid_until,
            "risk_notes": self.risk_notes,
            "data_source_notes": self.data_source_notes,
            "snapshot_manifest_path": self.snapshot_manifest_path,
            "candidates_path": self.candidates_path,
            "requires_manual_confirmation": self.requires_manual_confirmation,
            "auto_order_allowed": self.auto_order_allowed,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "alert_title": self.alert_title,
            "alert_body": self.alert_body,
        }


@dataclass(frozen=True)
class SignalAdvisoryArtifactPaths:
    artifact_dir: Path
    signals: Path
    signal_alert_preview: Path
    signal_advisory_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "signals": self.signals,
            "signal_alert_preview": self.signal_alert_preview,
            "signal_advisory_report": self.signal_advisory_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SignalAdvisoryResult:
    signal_run_id: str
    signal_date: pd.Timestamp
    decision_date: pd.Timestamp
    source_candidate_run_id: str
    candidates_path: Path
    candidate_report_path: Path | None
    metadata_path: Path | None
    snapshot_manifest_path: str
    signal_count: int
    advisory_action_counts: dict[str, int]
    signals: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]
    source_metadata: dict[str, Any]


def build_signal_advisory_from_candidates(
    candidates_path: str | Path,
    *,
    candidate_report_path: str | Path | None = None,
    metadata_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | SignalAdvisorySettings | str | Path | None = None,
) -> SignalAdvisoryResult:
    """Build local advisory signal artifacts from a current-candidates CSV."""

    project_settings, advisory_settings = _resolve_settings(settings)
    if advisory_settings.enable_live_trading or advisory_settings.enable_broker_api:
        raise ValueError("Signal advisory cannot enable live trading or broker API access")
    if advisory_settings.enable_alert_delivery:
        raise ValueError("Signal advisory v0.1 renders local previews only; alert delivery must remain disabled")
    if advisory_settings.auto_order_allowed:
        raise ValueError("Signal advisory cannot allow automatic order placement")
    if output_dir is not None:
        advisory_settings = advisory_settings.model_copy(update={"output_dir": Path(output_dir)})

    signal_input = SignalAdvisoryInput(
        candidates_path=Path(candidates_path),
        candidate_report_path=_optional_existing_path(candidate_report_path),
        metadata_path=_optional_existing_path(metadata_path),
    )
    _assert_input_files(signal_input)

    candidates = read_csv_preserve_symbol_columns(signal_input.candidates_path)
    candidates = _prepare_candidates_frame(candidates)
    source_metadata, inferred_metadata_path = _load_source_metadata(signal_input)
    inferred_report_path = _infer_candidate_report_path(signal_input)
    metadata_source_path = signal_input.metadata_path or inferred_metadata_path
    report_path = signal_input.candidate_report_path or inferred_report_path

    decision_date = _resolve_decision_date(candidates, source_metadata)
    signal_date = decision_date
    source_candidate_run_id = _resolve_source_candidate_run_id(candidates, source_metadata, signal_input.candidates_path)
    snapshot_manifest_path = _resolve_snapshot_manifest_path(source_metadata)
    signal_run_id = generate_signal_advisory_run_id(
        candidates,
        decision_date=decision_date,
        source_candidate_run_id=source_candidate_run_id,
        config_version=advisory_settings.config_version,
    )
    paths = resolve_signal_advisory_artifact_paths(advisory_settings.output_dir, signal_run_id)
    signals = _build_signal_frame(
        candidates,
        signal_run_id=signal_run_id,
        signal_date=signal_date,
        decision_date=decision_date,
        source_candidate_run_id=source_candidate_run_id,
        snapshot_manifest_path=snapshot_manifest_path,
        candidates_path=signal_input.candidates_path,
        settings=advisory_settings,
        source_metadata=source_metadata,
    )
    action_counts = _action_counts(signals)
    warnings = _build_warnings(signals, source_metadata)
    audit_metadata = _build_audit_metadata(
        signal_run_id=signal_run_id,
        signal_date=signal_date,
        decision_date=decision_date,
        candidates_path=signal_input.candidates_path,
        candidate_report_path=report_path,
        metadata_path=metadata_source_path,
        snapshot_manifest_path=snapshot_manifest_path,
        source_candidate_run_id=source_candidate_run_id,
        signals=signals,
        action_counts=action_counts,
        settings=advisory_settings,
        source_metadata=source_metadata,
    )
    result = SignalAdvisoryResult(
        signal_run_id=signal_run_id,
        signal_date=signal_date,
        decision_date=decision_date,
        source_candidate_run_id=source_candidate_run_id,
        candidates_path=signal_input.candidates_path,
        candidate_report_path=report_path,
        metadata_path=metadata_source_path,
        snapshot_manifest_path=snapshot_manifest_path,
        signal_count=len(signals),
        advisory_action_counts=action_counts,
        signals=signals,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=SIGNAL_ADVISORY_LIMITATIONS,
        audit_metadata=audit_metadata,
        source_metadata=source_metadata,
    )
    if project_settings.signal_advisory.write_artifacts and advisory_settings.write_artifacts:
        write_signal_advisory_artifacts(result)
    return result


def classify_signal_action(
    row: pd.Series | dict[str, Any],
    *,
    selection_profile: str | None = None,
    demo_mode: bool | None = None,
    not_strategy_recommendation: bool | None = None,
) -> str:
    """Classify a candidate row into an advisory action bucket."""

    profile = str(selection_profile or _row_get(row, "selection_profile", "") or "").strip().lower()
    is_demo = _to_bool(demo_mode)
    if demo_mode is None:
        is_demo = _to_bool(_row_get(row, "demo_mode", False))
    not_strategy = _to_bool(not_strategy_recommendation)
    if not_strategy_recommendation is None:
        not_strategy = _to_bool(_row_get(row, "not_strategy_recommendation", False))

    if profile == "demo" or is_demo or not_strategy:
        return "DEMO_ONLY"

    original_score_action = _normalize_action(_row_get(row, "score_action", ""))
    original_candidate_action = _normalize_action(_row_get(row, "action", ""))
    risk_status = _normalize_action(_row_get(row, "risk_precheck_status", ""))
    action = original_score_action or original_candidate_action

    if risk_status == "BLOCK" or action == "BLOCKED":
        return "BLOCKED"
    if action in {"PAPER_TRADE", "LIVE_CANDIDATE_SMALL", "STRONG_CANDIDATE_REVIEW_REQUIRED", "BUY", "PAPER_BUY"}:
        return "REVIEW_BUY_CANDIDATE"
    if action in {"SELL", "PAPER_SELL"}:
        return "REVIEW_SELL_CANDIDATE"
    if action in {"OBSERVE", "WATCH"}:
        return "WATCH"
    if action in {"HOLD"}:
        return "HOLD_REVIEW"
    return "NO_ACTION"


def render_signal_advisory_report(result: SignalAdvisoryResult) -> str:
    """Render a markdown report for a signal advisory run."""

    demo_only_count = int(result.advisory_action_counts.get("DEMO_ONLY", 0))
    lines = [
        f"# Signal Advisory Report: {result.signal_run_id}",
        "",
        "Signals are advisory artifacts only. They are not orders, approvals, or automated execution instructions.",
        "No broker API, live trading integration, automated order placement, or message delivery was invoked.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "signal_run_id": result.signal_run_id,
                "signal_date": result.signal_date.date(),
                "decision_date": result.decision_date.date(),
                "source_candidate_run_id": result.source_candidate_run_id,
                "signal_count": result.signal_count,
                "demo_only_count": demo_only_count,
                "candidates_path": result.candidates_path,
                "snapshot_manifest_path": result.snapshot_manifest_path,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
            }
        ),
        "",
        "## Advisory Action Counts",
        "",
        _dict_table(result.advisory_action_counts),
        "",
        "## Safety Contract",
        "",
        _dict_table(
            {
                "signals_are_orders": False,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "message_delivery_enabled": False,
                "message_sent": False,
                "demo_candidates_are_strategy_recommendations": False,
            }
        ),
        "",
        "## Signal Table",
        "",
        _markdown_table(
            result.signals,
            [
                "symbol",
                "name",
                "instrument_type",
                "advisory_action",
                "original_score_action",
                "original_candidate_action",
                "final_score",
                "confidence_level",
                "selection_profile",
                "demo_mode",
                "not_strategy_recommendation",
                "valid_until",
                "reason_summary",
            ],
        ),
        "",
        "## Alert Preview",
        "",
        "The following preview is local text only. No SMS, email, Telegram, WeChat, webhook, or broker message was sent.",
        "",
        render_alert_preview_messages(result),
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


def write_signal_advisory_artifacts(result: SignalAdvisoryResult) -> dict[str, Path]:
    """Write signal advisory CSV, markdown previews, report, and metadata."""

    paths = SignalAdvisoryArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.signals, paths.signals)
    metadata = build_signal_advisory_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.signal_alert_preview.write_text(render_alert_preview_messages(result), encoding="utf-8")
    paths.signal_advisory_report.write_text(render_signal_advisory_report(result), encoding="utf-8")
    return paths.as_dict()


def render_alert_preview_messages(result: SignalAdvisoryResult) -> str:
    """Render local-only alert preview messages."""

    if result.signals.empty:
        return "_No signal preview messages._"
    lines = [
        "## Local Alert Preview Messages",
        "",
        "No message was sent. These previews require manual confirmation and never permit auto-order placement.",
        "",
    ]
    for index, record in enumerate(result.signals.to_dict("records"), start=1):
        lines.extend(
            [
                f"### Preview {index}: {record.get('alert_title', '')}",
                "",
                str(record.get("alert_body", "")),
                "",
            ]
        )
    return "\n".join(lines)


def build_signal_advisory_metadata(
    result: SignalAdvisoryResult,
    paths: SignalAdvisoryArtifactPaths,
) -> dict[str, Any]:
    """Build metadata.json content for signal advisory artifacts."""

    return {
        "signal_run_id": result.signal_run_id,
        "created_at": result.signal_date.isoformat(),
        "signal_date": result.signal_date,
        "decision_date": result.decision_date,
        "source_candidate_run_id": result.source_candidate_run_id,
        "signal_count": result.signal_count,
        "advisory_action_counts": result.advisory_action_counts,
        "selection_profile": result.audit_metadata.get("selection_profile", ""),
        "demo_mode": result.audit_metadata.get("demo_mode", False),
        "not_strategy_recommendation": result.audit_metadata.get("not_strategy_recommendation", False),
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "alert_delivery_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "signals_are_orders": False,
        "candidates_path": str(result.candidates_path),
        "candidate_report_path": str(result.candidate_report_path or ""),
        "source_metadata_path": str(result.metadata_path or ""),
        "snapshot_manifest_path": result.snapshot_manifest_path,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
    }


def generate_signal_advisory_run_id(
    candidates: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp,
    source_candidate_run_id: str,
    config_version: str,
) -> str:
    """Generate a deterministic signal advisory run id."""

    payload = {
        "decision_date": str(_normalize_date(decision_date).date()),
        "source_candidate_run_id": source_candidate_run_id,
        "candidate_digest": _frame_digest(candidates),
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_signal_advisory_artifact_paths(
    output_dir: str | Path,
    signal_run_id: str,
) -> SignalAdvisoryArtifactPaths:
    """Resolve stable artifact paths for a signal advisory run."""

    artifact_dir = Path(output_dir) / signal_run_id
    return SignalAdvisoryArtifactPaths(
        artifact_dir=artifact_dir,
        signals=artifact_dir / "signals.csv",
        signal_alert_preview=artifact_dir / "signal_alert_preview.md",
        signal_advisory_report=artifact_dir / "signal_advisory_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _build_signal_frame(
    candidates: pd.DataFrame,
    *,
    signal_run_id: str,
    signal_date: pd.Timestamp,
    decision_date: pd.Timestamp,
    source_candidate_run_id: str,
    snapshot_manifest_path: str,
    candidates_path: Path,
    settings: SignalAdvisorySettings,
    source_metadata: dict[str, Any],
) -> pd.DataFrame:
    signals = [
        _signal_from_candidate_row(
            row,
            row_index=index,
            signal_run_id=signal_run_id,
            signal_date=signal_date,
            decision_date=decision_date,
            source_candidate_run_id=source_candidate_run_id,
            snapshot_manifest_path=snapshot_manifest_path,
            candidates_path=candidates_path,
            settings=settings,
            source_metadata=source_metadata,
        )
        for index, row in candidates.reset_index(drop=True).iterrows()
    ]
    frame = pd.DataFrame([signal.as_dict() for signal in signals], columns=SIGNAL_COLUMNS)
    if frame.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)
    return frame[SIGNAL_COLUMNS]


def _signal_from_candidate_row(
    row: pd.Series,
    *,
    row_index: int,
    signal_run_id: str,
    signal_date: pd.Timestamp,
    decision_date: pd.Timestamp,
    source_candidate_run_id: str,
    snapshot_manifest_path: str,
    candidates_path: Path,
    settings: SignalAdvisorySettings,
    source_metadata: dict[str, Any],
) -> SignalAdvisorySignal:
    symbol = normalize_symbol_value(_row_get(row, "symbol", ""))
    name = _text(_row_get(row, "name", ""))
    instrument_type = _text(_row_get(row, "instrument_type", ""))
    selection_profile = _resolve_row_or_metadata(row, source_metadata, "selection_profile", "default")
    demo_mode = _to_bool(_resolve_row_or_metadata(row, source_metadata, "demo_mode", False))
    not_strategy = _to_bool(_resolve_row_or_metadata(row, source_metadata, "not_strategy_recommendation", False))
    advisory_action = classify_signal_action(
        row,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
    )
    original_score_action = _text(_row_get(row, "score_action", ""))
    original_candidate_action = _text(_row_get(row, "action", ""))
    final_score = _to_float(_row_get(row, "final_score", None))
    confidence = _confidence_level(final_score, settings)
    valid_until = _valid_until(decision_date, settings.default_validity_days)
    reason_summary = _reason_summary(
        advisory_action=advisory_action,
        final_score=final_score,
        original_score_action=original_score_action,
        original_candidate_action=original_candidate_action,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
    )
    risk_notes = _risk_notes(row)
    data_source_notes = _data_source_notes(
        candidates_path=candidates_path,
        source_candidate_run_id=source_candidate_run_id,
        snapshot_manifest_path=snapshot_manifest_path,
    )
    signal_id = _hash_payload(
        {
            "signal_run_id": signal_run_id,
            "row_index": row_index,
            "symbol": symbol,
            "decision_date": str(decision_date.date()),
            "advisory_action": advisory_action,
        },
        length=12,
    )
    alert_title = f"{symbol} {advisory_action} preview"
    alert_body = _alert_body(
        symbol=symbol,
        name=name,
        advisory_action=advisory_action,
        final_score=final_score,
        confidence=confidence,
        reason_summary=reason_summary,
        risk_notes=risk_notes,
        valid_until=valid_until,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
    )
    return SignalAdvisorySignal(
        signal_id=signal_id,
        signal_run_id=signal_run_id,
        signal_date=str(signal_date.date()),
        decision_date=str(decision_date.date()),
        symbol=symbol,
        name=name,
        instrument_type=instrument_type,
        source_candidate_run_id=source_candidate_run_id,
        selection_profile=selection_profile,
        demo_mode=demo_mode,
        not_strategy_recommendation=not_strategy,
        advisory_action=advisory_action,
        original_score_action=original_score_action,
        original_candidate_action=original_candidate_action,
        final_score=final_score,
        confidence_level=confidence,
        reason_summary=reason_summary,
        score_breakdown=_text(_row_get(row, "score_breakdown", "")),
        entry_condition=_entry_condition(advisory_action, demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        exit_condition=_exit_condition(advisory_action, demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        invalidation_condition=_invalidation_condition(demo_mode=demo_mode, not_strategy_recommendation=not_strategy),
        valid_until=valid_until,
        risk_notes=risk_notes,
        data_source_notes=data_source_notes,
        snapshot_manifest_path=snapshot_manifest_path,
        candidates_path=str(candidates_path),
        requires_manual_confirmation=True,
        auto_order_allowed=False,
        no_live_trading=True,
        no_broker_api=True,
        alert_title=alert_title,
        alert_body=alert_body,
    )


def _prepare_candidates_frame(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = frame.copy(deep=True)
    if "symbol" not in candidates.columns:
        raise ValueError("candidates.csv must include a symbol column")
    candidates["symbol"] = candidates["symbol"].map(normalize_symbol_value)
    return candidates.reset_index(drop=True)


def _assert_input_files(signal_input: SignalAdvisoryInput) -> None:
    if not signal_input.candidates_path.exists():
        raise FileNotFoundError(f"Candidates CSV not found: {signal_input.candidates_path}")
    if signal_input.candidate_report_path is not None and not signal_input.candidate_report_path.exists():
        raise FileNotFoundError(f"Candidate report not found: {signal_input.candidate_report_path}")
    if signal_input.metadata_path is not None and not signal_input.metadata_path.exists():
        raise FileNotFoundError(f"Candidate metadata not found: {signal_input.metadata_path}")


def _load_source_metadata(signal_input: SignalAdvisoryInput) -> tuple[dict[str, Any], Path | None]:
    metadata_path = signal_input.metadata_path
    if metadata_path is None:
        sibling = signal_input.candidates_path.parent / "metadata.json"
        if sibling.exists():
            metadata_path = sibling
    if metadata_path is None:
        return {}, None
    return json.loads(metadata_path.read_text(encoding="utf-8")), metadata_path


def _infer_candidate_report_path(signal_input: SignalAdvisoryInput) -> Path | None:
    sibling = signal_input.candidates_path.parent / "current_candidates_report.md"
    if sibling.exists():
        return sibling
    return None


def _optional_existing_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value)


def _resolve_decision_date(candidates: pd.DataFrame, metadata: dict[str, Any]) -> pd.Timestamp:
    for value in [
        metadata.get("decision_date"),
        (metadata.get("audit_metadata") or {}).get("decision_date"),
    ]:
        if _present(value):
            return _normalize_date(value)
    if "decision_date" in candidates.columns and not candidates.empty:
        value = candidates["decision_date"].dropna().astype(str).iloc[0]
        if _present(value):
            return _normalize_date(value)
    return pd.Timestamp.utcnow().tz_localize(None).normalize()


def _resolve_source_candidate_run_id(candidates: pd.DataFrame, metadata: dict[str, Any], candidates_path: Path) -> str:
    for value in [metadata.get("run_id"), (metadata.get("audit_metadata") or {}).get("run_id")]:
        if _present(value):
            return str(value)
    for column in ["current_candidate_run_id", "source_run_id"]:
        if column in candidates.columns and not candidates.empty:
            values = candidates[column].dropna().astype(str)
            if not values.empty and _present(values.iloc[0]):
                return values.iloc[0]
    folder_name = candidates_path.parent.name
    if "_" in folder_name:
        return folder_name.rsplit("_", 1)[-1]
    return "UNKNOWN_CANDIDATE_RUN"


def _resolve_snapshot_manifest_path(metadata: dict[str, Any]) -> str:
    audit = metadata.get("audit_metadata") or {}
    config_summary = metadata.get("config_summary") or {}
    preflight = config_summary.get("snapshot_quality_preflight") or {}
    for value in [
        audit.get("snapshot_quality_manifest_path"),
        preflight.get("snapshot_quality_manifest_path"),
        metadata.get("snapshot_manifest_path"),
    ]:
        if _present(value):
            return str(value)
    return ""


def _resolve_row_or_metadata(row: pd.Series, metadata: dict[str, Any], key: str, default: Any) -> Any:
    value = _row_get(row, key, None)
    if _present(value):
        return value
    for source in [metadata, metadata.get("audit_metadata") or {}, metadata.get("config_summary") or {}]:
        value = source.get(key)
        if _present(value):
            return value
    return default


def _action_counts(signals: pd.DataFrame) -> dict[str, int]:
    counts = {action: 0 for action in sorted(ADVISORY_ACTIONS)}
    if "advisory_action" in signals.columns:
        for key, value in signals["advisory_action"].value_counts(dropna=False).sort_index().items():
            counts[str(key)] = int(value)
    return counts


def _build_warnings(signals: pd.DataFrame, source_metadata: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if signals.empty:
        warnings.append("No advisory signals were generated from the candidates file.")
    if int((signals.get("advisory_action") == "DEMO_ONLY").sum()) > 0:
        warnings.append(
            "Demo current-candidate inputs generated DEMO_ONLY advisory signals; "
            "these are workflow validation artifacts and not strategy recommendations."
        )
    source_warnings = source_metadata.get("warnings") or []
    for warning in source_warnings:
        warnings.append(f"Source candidate warning: {warning}")
    return warnings


def _build_audit_metadata(
    *,
    signal_run_id: str,
    signal_date: pd.Timestamp,
    decision_date: pd.Timestamp,
    candidates_path: Path,
    candidate_report_path: Path | None,
    metadata_path: Path | None,
    snapshot_manifest_path: str,
    source_candidate_run_id: str,
    signals: pd.DataFrame,
    action_counts: dict[str, int],
    settings: SignalAdvisorySettings,
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    selection_profile = _first_non_empty(signals, "selection_profile")
    demo_mode = bool(signals["demo_mode"].map(_to_bool).any()) if "demo_mode" in signals.columns else False
    not_strategy = (
        bool(signals["not_strategy_recommendation"].map(_to_bool).any())
        if "not_strategy_recommendation" in signals.columns
        else False
    )
    return {
        "signal_run_id": signal_run_id,
        "signal_date": signal_date,
        "decision_date": decision_date,
        "source_candidate_run_id": source_candidate_run_id,
        "selection_profile": selection_profile,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy,
        "signal_count": len(signals),
        "advisory_action_counts": action_counts,
        "candidates_path": str(candidates_path),
        "candidate_report_path": str(candidate_report_path or ""),
        "source_metadata_path": str(metadata_path or ""),
        "snapshot_manifest_path": snapshot_manifest_path,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "alert_delivery_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "signals_are_orders": False,
        "source_demo_mode": source_metadata.get("demo_mode", (source_metadata.get("audit_metadata") or {}).get("demo_mode")),
        "config_summary": {
            "config_version": settings.config_version,
            "output_dir": settings.output_dir,
            "default_validity_days": settings.default_validity_days,
            "medium_confidence_score": settings.medium_confidence_score,
            "high_confidence_score": settings.high_confidence_score,
            "enable_alert_delivery": settings.enable_alert_delivery,
            "enable_live_trading": settings.enable_live_trading,
            "enable_broker_api": settings.enable_broker_api,
            "auto_order_allowed": settings.auto_order_allowed,
        },
    }


def _confidence_level(final_score: float | None, settings: SignalAdvisorySettings) -> str:
    if final_score is None:
        return "UNKNOWN"
    if final_score >= settings.high_confidence_score:
        return "HIGH_REVIEW"
    if final_score >= settings.medium_confidence_score:
        return "MEDIUM_REVIEW"
    return "LOW_REVIEW"


def _reason_summary(
    *,
    advisory_action: str,
    final_score: float | None,
    original_score_action: str,
    original_candidate_action: str,
    demo_mode: bool,
    not_strategy_recommendation: bool,
) -> str:
    score_text = "" if final_score is None else f"{final_score:.2f}"
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return (
            "Demo profile workflow validation only; not a strategy recommendation. "
            f"Original score action={original_score_action or 'UNKNOWN'}, "
            f"candidate action={original_candidate_action or 'UNKNOWN'}, final_score={score_text}."
        )
    return (
        "Manual research review required before any action. "
        f"Advisory action={advisory_action}, original score action={original_score_action or 'UNKNOWN'}, "
        f"candidate action={original_candidate_action or 'UNKNOWN'}, final_score={score_text}."
    )


def _entry_condition(advisory_action: str, *, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return "No entry condition; demo signal is workflow validation only and requires manual review."
    return "Manual reviewer must confirm strategy, data quality, risk, timing, and execution assumptions before any action."


def _exit_condition(advisory_action: str, *, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY":
        return "No exit condition; no position or order is created by this signal."
    return "Manual reviewer must define exit criteria before any paper or future execution action."


def _invalidation_condition(*, demo_mode: bool, not_strategy_recommendation: bool) -> str:
    if demo_mode or not_strategy_recommendation:
        return "Invalid outside local demo validation context or if source candidate artifacts change."
    return "Invalid if newer data, quality checks, risk review, or manual research contradicts this advisory artifact."


def _valid_until(decision_date: pd.Timestamp, validity_days: int) -> str:
    return str((_normalize_date(decision_date) + pd.Timedelta(days=int(validity_days))).date())


def _risk_notes(row: pd.Series) -> str:
    status = _text(_row_get(row, "risk_precheck_status", "UNKNOWN")) or "UNKNOWN"
    reason = _text(_row_get(row, "risk_precheck_reason", ""))
    return (
        f"risk_precheck_status={status}; risk_precheck_reason={reason or 'not provided'}; "
        "manual confirmation required; auto-order disabled."
    )


def _data_source_notes(*, candidates_path: Path, source_candidate_run_id: str, snapshot_manifest_path: str) -> str:
    return (
        f"source_candidate_run_id={source_candidate_run_id}; candidates_path={candidates_path}; "
        f"snapshot_manifest_path={snapshot_manifest_path or 'not provided'}."
    )


def _alert_body(
    *,
    symbol: str,
    name: str,
    advisory_action: str,
    final_score: float | None,
    confidence: str,
    reason_summary: str,
    risk_notes: str,
    valid_until: str,
    demo_mode: bool,
    not_strategy_recommendation: bool,
) -> str:
    score_text = "UNKNOWN" if final_score is None else f"{final_score:.2f}"
    demo_text = (
        "Demo/workflow validation only; not a strategy recommendation. "
        if demo_mode or not_strategy_recommendation or advisory_action == "DEMO_ONLY"
        else ""
    )
    return (
        f"{symbol} {name} | action={advisory_action} | score={score_text} | confidence={confidence}. "
        f"{demo_text}{reason_summary} Risk: {risk_notes} Valid until {valid_until}. "
        "Manual confirmation required. No auto-order. No live trading or broker API."
    )


def _normalize_action(value: Any) -> str:
    return str(value or "").strip().upper()


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


def _resolve_settings(
    settings: Settings | SignalAdvisorySettings | str | Path | None,
) -> tuple[Settings, SignalAdvisorySettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.signal_advisory
    if isinstance(settings, Settings):
        return settings, settings.signal_advisory
    if isinstance(settings, SignalAdvisorySettings):
        project = load_settings(Path("config/default.yaml"))
        return project.model_copy(update={"signal_advisory": settings}), settings
    project = load_settings(Path(settings))
    return project, project.signal_advisory


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
