"""Reviewed PIT universe overlay approval workflow.

This module applies local manual review updates to a PIT universe overlay
template. It only writes review artifacts under reports; it does not create
usable universe inputs, build snapshots, run current-candidates, or perform any
trading workflow.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_overlay_plan import OVERLAY_PLAN_COLUMNS


REVIEW_STATUSES = {
    "NEEDS_MANUAL_REVIEW",
    "APPROVED_FOR_PIT_UNIVERSE",
    "REJECTED",
    "NEEDS_MORE_EVIDENCE",
}

REVIEW_KEY_COLUMNS = ["signal_date", "symbol", "universe_name"]
REVIEW_UPDATE_COLUMNS = [
    *REVIEW_KEY_COLUMNS,
    "include_flag",
    "review_status",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "listed_date_evidence",
    "delisted_date_evidence",
    "is_active_evidence",
    "is_st",
    "is_suspended",
    "survivorship_bias_resolved",
]
REVIEW_UPDATE_UNIVERSE_METADATA_COLUMNS = [
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
]
REVIEW_UPDATE_COLUMNS = REVIEW_UPDATE_COLUMNS + REVIEW_UPDATE_UNIVERSE_METADATA_COLUMNS

REVIEW_OUTPUT_COLUMNS = [
    "review_id",
    "overlay_plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "include_flag",
    "review_status",
    "valid_for_signal_date",
    "blocker_reason",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "listed_date",
    "delisted_date",
    "is_active",
    "is_st",
    "is_suspended",
    "listed_date_evidence",
    "delisted_date_evidence",
    "is_active_evidence",
    "survivorship_bias_warning",
    "survivorship_bias_resolved",
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
    "manual_review_required",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "review_only",
]

SAFETY_STATEMENT = (
    "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
    "order placement, message delivery, LLM API, or external API was invoked."
)


@dataclass(frozen=True)
class PitUniverseOverlayReviewSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_overlay_review")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False
    enable_external_api: bool = False
    enable_llm_api: bool = False


@dataclass(frozen=True)
class PitUniverseOverlayReviewRequest:
    overlay_plan: Path
    review_updates: Path | None
    write_review_template_only: bool


@dataclass(frozen=True)
class PitUniverseOverlayReviewRow:
    review_id: str
    overlay_plan_id: str
    signal_date: str
    symbol: str
    universe_name: str
    include_flag: bool
    review_status: str
    valid_for_signal_date: bool
    blocker_reason: str
    reviewer: str
    reviewed_at: str
    review_reason: str
    evidence_source: str
    evidence_path: str
    evidence_reference: str
    listed_date: str
    delisted_date: str
    is_active: bool | str
    is_st: bool | str
    is_suspended: bool | str
    listed_date_evidence: str
    delisted_date_evidence: str
    is_active_evidence: bool | str
    as_of_date: str
    name: str
    instrument_type: str
    exchange: str
    industry: str
    min_lot: str
    t_plus_rule: str
    available_time: str
    revision_id: str
    source: str
    survivorship_bias_warning: bool
    survivorship_bias_resolved: bool
    manual_review_required: bool = True
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    review_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "overlay_plan_id": self.overlay_plan_id,
            "signal_date": self.signal_date,
            "symbol": self.symbol,
            "universe_name": self.universe_name,
            "include_flag": self.include_flag,
            "review_status": self.review_status,
            "valid_for_signal_date": self.valid_for_signal_date,
            "blocker_reason": self.blocker_reason,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "review_reason": self.review_reason,
            "evidence_source": self.evidence_source,
            "evidence_path": self.evidence_path,
            "evidence_reference": self.evidence_reference,
            "listed_date": self.listed_date,
            "delisted_date": self.delisted_date,
            "is_active": self.is_active,
            "is_st": self.is_st,
            "is_suspended": self.is_suspended,
            "listed_date_evidence": self.listed_date_evidence,
            "delisted_date_evidence": self.delisted_date_evidence,
            "is_active_evidence": self.is_active_evidence,
            "as_of_date": self.as_of_date,
            "name": self.name,
            "instrument_type": self.instrument_type,
            "exchange": self.exchange,
            "industry": self.industry,
            "min_lot": self.min_lot,
            "t_plus_rule": self.t_plus_rule,
            "available_time": self.available_time,
            "revision_id": self.revision_id,
            "source": self.source,
            "survivorship_bias_warning": self.survivorship_bias_warning,
            "survivorship_bias_resolved": self.survivorship_bias_resolved,
            "manual_review_required": self.manual_review_required,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
            "review_only": self.review_only,
        }


@dataclass(frozen=True)
class PitUniverseOverlayReviewArtifactPaths:
    artifact_dir: Path
    reviewed_overlay: Path
    review_template: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "reviewed_overlay": self.reviewed_overlay,
            "review_template": self.review_template,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseOverlayReviewResult:
    review_id: str
    status: str
    request: PitUniverseOverlayReviewRequest
    row_count: int
    approved_count: int
    rejected_count: int
    needs_more_evidence_count: int
    needs_manual_review_count: int
    valid_for_signal_date_count: int
    reviewed_frame: pd.DataFrame
    review_template_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_pit_universe_overlay_plan_for_review(path: str | Path) -> pd.DataFrame:
    """Load a PIT universe overlay plan while preserving symbol strings."""

    plan_path = Path(path)
    if not plan_path.exists():
        raise FileNotFoundError(f"PIT universe overlay plan not found: {plan_path}")
    frame = read_csv_preserve_symbol_columns(plan_path, keep_default_na=False)
    missing = [column for column in OVERLAY_PLAN_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"PIT universe overlay plan missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output


def load_pit_universe_overlay_review_updates(path: str | Path | None) -> pd.DataFrame:
    """Load local reviewer updates while preserving symbol strings."""

    if path is None:
        return pd.DataFrame(columns=REVIEW_UPDATE_COLUMNS)
    update_path = Path(path)
    if not update_path.exists():
        raise FileNotFoundError(f"PIT universe overlay review updates not found: {update_path}")
    frame = read_csv_preserve_symbol_columns(update_path, keep_default_na=False)
    missing = [column for column in REVIEW_KEY_COLUMNS + ["review_status"] if column not in frame.columns]
    if missing:
        raise ValueError(f"PIT universe overlay review updates missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    for column in REVIEW_UPDATE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in REVIEW_UPDATE_UNIVERSE_METADATA_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    output["review_status"] = output["review_status"].map(lambda value: _text(value).upper())
    invalid = sorted(set(output["review_status"]) - REVIEW_STATUSES)
    if invalid:
        raise ValueError(f"Invalid review_status: {', '.join(invalid)}")
    duplicated = output[REVIEW_KEY_COLUMNS].astype(str).agg("|".join, axis=1).duplicated(keep=False)
    if duplicated.any():
        duplicate_keys = sorted(output.loc[duplicated, REVIEW_KEY_COLUMNS].astype(str).agg("|".join, axis=1).unique())
        raise ValueError(f"Duplicate PIT universe overlay review updates: {', '.join(duplicate_keys)}")
    return output[REVIEW_UPDATE_COLUMNS].copy()


def validate_pit_universe_overlay_review_row(plan_row: dict[str, Any], update_row: dict[str, Any]) -> list[str]:
    """Return approval blockers for one merged review row."""

    status = _text(update_row.get("review_status")).upper()
    if status != "APPROVED_FOR_PIT_UNIVERSE":
        return []

    blockers: list[str] = []
    signal_date = _parse_date(plan_row.get("signal_date"))
    proposed_as_of = _parse_date(plan_row.get("proposed_as_of_date"))
    proposed_available = _parse_datetime(plan_row.get("proposed_available_time"))
    decision_time = pd.Timestamp(signal_date) + pd.Timedelta(hours=15, minutes=30) if signal_date is not None else None
    listed_date = _parse_date(update_row.get("listed_date_evidence"))
    delisted_date = _parse_date(update_row.get("delisted_date_evidence"))

    for column in ["reviewer", "reviewed_at", "review_reason", "evidence_source", "listed_date_evidence"]:
        if not _present(update_row.get(column)):
            blockers.append(f"missing {column}")
    if not (_present(update_row.get("evidence_path")) or _present(update_row.get("evidence_reference"))):
        blockers.append("missing evidence_path or evidence_reference")
    if not _is_true(update_row.get("include_flag")):
        blockers.append("include_flag must be true")
    if not _is_true(update_row.get("survivorship_bias_resolved")):
        blockers.append("survivorship_bias_resolved must be true")
    if _is_true(plan_row.get("survivorship_bias_warning")) and not _is_true(update_row.get("survivorship_bias_resolved")):
        blockers.append("future-derived survivorship_bias_warning is unresolved")
    if not _is_true(update_row.get("is_active_evidence")):
        blockers.append("is_active_evidence must be true")
    if signal_date is None:
        blockers.append("invalid signal_date")
    if proposed_as_of is None:
        blockers.append("invalid proposed_as_of_date")
    elif signal_date is not None and proposed_as_of > signal_date:
        blockers.append("proposed_as_of_date must be on or before signal_date")
    if proposed_available is None:
        blockers.append("invalid proposed_available_time")
    elif decision_time is not None and proposed_available > decision_time:
        blockers.append("proposed_available_time must be on or before signal decision time")
    if listed_date is None:
        blockers.append("invalid listed_date_evidence")
    elif signal_date is not None and listed_date > signal_date:
        blockers.append("listed_date must be on or before signal_date")
    if delisted_date is not None and signal_date is not None and delisted_date < signal_date:
        blockers.append("delisted_date must be blank or on/after signal_date")
    return blockers


def build_pit_universe_overlay_review(
    *,
    overlay_plan: str | Path,
    review_updates: str | Path | None = None,
    write_review_template_only: bool = False,
    output_dir: str | Path | None = None,
    settings: PitUniverseOverlayReviewSettings | None = None,
) -> PitUniverseOverlayReviewResult:
    """Apply local PIT universe overlay review updates and write review artifacts only."""

    resolved_settings = settings or PitUniverseOverlayReviewSettings()
    if output_dir is not None:
        resolved_settings = PitUniverseOverlayReviewSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_order_placement=resolved_settings.enable_order_placement,
            enable_message_delivery=resolved_settings.enable_message_delivery,
            enable_external_api=resolved_settings.enable_external_api,
            enable_llm_api=resolved_settings.enable_llm_api,
        )
    _assert_settings_safe(resolved_settings)

    request = PitUniverseOverlayReviewRequest(
        overlay_plan=Path(overlay_plan),
        review_updates=Path(review_updates) if review_updates else None,
        write_review_template_only=bool(write_review_template_only),
    )
    plan_frame = load_pit_universe_overlay_plan_for_review(request.overlay_plan)
    update_frame = (
        pd.DataFrame(columns=REVIEW_UPDATE_COLUMNS)
        if request.write_review_template_only
        else load_pit_universe_overlay_review_updates(request.review_updates)
    )
    _validate_updates_match_plan(plan_frame, update_frame)

    review_id = generate_pit_universe_overlay_review_id(request, plan_frame, update_frame, resolved_settings)
    update_map = {
        _row_key(row): row
        for row in update_frame.to_dict("records")
    }
    reviewed_rows = [
        _build_review_row(review_id, plan_row, update_map.get(_row_key(plan_row), {})).as_dict()
        for plan_row in plan_frame.to_dict("records")
    ]
    reviewed_frame = _finalize_reviewed_frame(pd.DataFrame(reviewed_rows, columns=REVIEW_OUTPUT_COLUMNS))
    template_frame = build_pit_universe_overlay_review_template(plan_frame)
    counts = _status_counts(reviewed_frame)
    valid_count = _true_count(reviewed_frame, "valid_for_signal_date")
    status = "PASS" if counts["approved"] > 0 and counts["needs_more_evidence"] == 0 else "WARN"
    if request.write_review_template_only or counts["approved"] == 0:
        status = "WARN"
    warnings = _build_warnings(request, reviewed_frame)
    paths = resolve_pit_universe_overlay_review_paths(resolved_settings.output_dir, review_id)
    audit_metadata = {
        "review_id": review_id,
        "overlay_plan": str(request.overlay_plan),
        "review_updates": str(request.review_updates) if request.review_updates else "",
        "write_review_template_only": request.write_review_template_only,
        "row_count": len(reviewed_frame),
        "approved_count": counts["approved"],
        "rejected_count": counts["rejected"],
        "needs_more_evidence_count": counts["needs_more_evidence"],
        "needs_manual_review_count": counts["needs_manual_review"],
        "valid_for_signal_date_count": valid_count,
        "review_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
        "snapshot_manifest_built": False,
        "snapshot_manifests_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "order_placement_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
    }
    result = PitUniverseOverlayReviewResult(
        review_id=review_id,
        status=status,
        request=request,
        row_count=len(reviewed_frame),
        approved_count=counts["approved"],
        rejected_count=counts["rejected"],
        needs_more_evidence_count=counts["needs_more_evidence"],
        needs_manual_review_count=counts["needs_manual_review"],
        valid_for_signal_date_count=valid_count,
        reviewed_frame=reviewed_frame,
        review_template_frame=template_frame,
        warnings=warnings,
        artifact_paths=paths.as_dict(),
        audit_metadata=audit_metadata,
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_overlay_review_artifacts(result)
    return result


def build_pit_universe_overlay_review_template(plan_frame: pd.DataFrame) -> pd.DataFrame:
    """Build a local reviewer update template from the overlay plan rows."""

    rows = []
    for row in plan_frame.to_dict("records"):
        rows.append(
            {
                "signal_date": _date_text(row.get("signal_date")),
                "symbol": normalize_symbol_value(row.get("symbol")),
                "universe_name": _text(row.get("universe_name")),
                "include_flag": "",
                "review_status": "NEEDS_MANUAL_REVIEW",
                "reviewer": "",
                "reviewed_at": "",
                "review_reason": "",
                "evidence_source": "",
                "evidence_path": "",
                "evidence_reference": "",
                "listed_date_evidence": "",
                "delisted_date_evidence": "",
                "is_active_evidence": "",
                "is_st": "",
                "is_suspended": "",
                "survivorship_bias_resolved": "",
                "as_of_date": "",
                "name": "",
                "instrument_type": "",
                "exchange": "",
                "industry": "",
                "min_lot": "",
                "t_plus_rule": "",
                "available_time": "",
                "revision_id": "",
                "source": "",
            }
        )
    return pd.DataFrame(rows, columns=REVIEW_UPDATE_COLUMNS)


def write_pit_universe_overlay_review_artifacts(result: PitUniverseOverlayReviewResult) -> None:
    """Write reviewed PIT universe overlay artifacts."""

    paths = PitUniverseOverlayReviewArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.reviewed_frame.to_csv(paths.reviewed_overlay, index=False)
    result.review_template_frame.to_csv(paths.review_template, index=False)
    metadata = build_pit_universe_overlay_review_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.report.write_text(render_pit_universe_overlay_review_report(result), encoding="utf-8")


def render_pit_universe_overlay_review_report(result: PitUniverseOverlayReviewResult) -> str:
    """Render a human-readable review report."""

    warning_lines = [f"- {warning}" for warning in result.warnings] if result.warnings else ["- None"]
    lines = [
        f"# Reviewed PIT Universe Overlay Review: {result.review_id}",
        "",
        "## Summary",
        "",
        f"- status: {result.status}",
        f"- row_count: {result.row_count}",
        f"- approved_count: {result.approved_count}",
        f"- rejected_count: {result.rejected_count}",
        f"- needs_more_evidence_count: {result.needs_more_evidence_count}",
        f"- needs_manual_review_count: {result.needs_manual_review_count}",
        f"- valid_for_signal_date_count: {result.valid_for_signal_date_count}",
        "",
        "## Safety",
        "",
        SAFETY_STATEMENT,
        "",
        "Approved rows are reviewed PIT-universe evidence only. They are not candidate generation,",
        "snapshot manifests, forward-return labels, trading recommendations, orders, or broker actions.",
        "",
        "## Warnings",
        "",
        *warning_lines,
    ]
    return "\n".join(lines)


def build_pit_universe_overlay_review_metadata(
    result: PitUniverseOverlayReviewResult,
    paths: PitUniverseOverlayReviewArtifactPaths,
) -> dict[str, Any]:
    return {
        **result.audit_metadata,
        "status": result.status,
        "created_at": "2024-05-29T00:00:00",
        "config_version": "v0.1",
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            "reviewed_overlay": str(paths.reviewed_overlay),
            "review_template": str(paths.review_template),
            "report": str(paths.report),
            "metadata": str(paths.metadata),
        },
    }


def generate_pit_universe_overlay_review_id(
    request: PitUniverseOverlayReviewRequest,
    plan_frame: pd.DataFrame,
    update_frame: pd.DataFrame,
    settings: PitUniverseOverlayReviewSettings,
) -> str:
    payload = {
        "overlay_plan": str(request.overlay_plan),
        "review_updates": str(request.review_updates) if request.review_updates else "",
        "write_review_template_only": request.write_review_template_only,
        "config_version": settings.config_version,
        "plan": plan_frame[REVIEW_KEY_COLUMNS].to_dict("records") if not plan_frame.empty else [],
        "updates": update_frame[REVIEW_UPDATE_COLUMNS].to_dict("records") if not update_frame.empty else [],
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_pit_universe_overlay_review_paths(
    output_dir: str | Path,
    review_id: str,
) -> PitUniverseOverlayReviewArtifactPaths:
    artifact_dir = Path(output_dir) / review_id
    return PitUniverseOverlayReviewArtifactPaths(
        artifact_dir=artifact_dir,
        reviewed_overlay=artifact_dir / "reviewed_pit_universe_overlay.csv",
        review_template=artifact_dir / "pit_universe_overlay_review_template.csv",
        report=artifact_dir / "pit_universe_overlay_review_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _build_review_row(
    review_id: str,
    plan_row: dict[str, Any],
    update_row: dict[str, Any],
) -> PitUniverseOverlayReviewRow:
    status = _text(update_row.get("review_status")).upper() if update_row else "NEEDS_MANUAL_REVIEW"
    if not status:
        status = "NEEDS_MANUAL_REVIEW"
    blockers = validate_pit_universe_overlay_review_row(plan_row, update_row)
    include_flag = _is_true(update_row.get("include_flag"))
    valid_for_signal_date = status == "APPROVED_FOR_PIT_UNIVERSE" and not blockers
    if status == "APPROVED_FOR_PIT_UNIVERSE" and blockers:
        status = "NEEDS_MORE_EVIDENCE"
        include_flag = False
    if status in {"NEEDS_MANUAL_REVIEW", "NEEDS_MORE_EVIDENCE", "REJECTED"}:
        valid_for_signal_date = False
        if status != "APPROVED_FOR_PIT_UNIVERSE":
            include_flag = False
    blocker_reason = "; ".join(blockers) if blockers else _default_blocker(status, plan_row, update_row)
    listed = _date_text(update_row.get("listed_date_evidence"))
    delisted = _date_text(update_row.get("delisted_date_evidence"))
    return PitUniverseOverlayReviewRow(
        review_id=review_id,
        overlay_plan_id=_text(plan_row.get("overlay_plan_id")),
        signal_date=_date_text(plan_row.get("signal_date")),
        symbol=normalize_symbol_value(plan_row.get("symbol")),
        universe_name=_text(plan_row.get("universe_name")),
        include_flag=include_flag,
        review_status=status,
        valid_for_signal_date=valid_for_signal_date,
        blocker_reason=blocker_reason,
        reviewer=_text(update_row.get("reviewer")),
        reviewed_at=_text(update_row.get("reviewed_at")),
        review_reason=_text(update_row.get("review_reason") or plan_row.get("review_reason")),
        evidence_source=_text(update_row.get("evidence_source")),
        evidence_path=_text(update_row.get("evidence_path")),
        evidence_reference=_text(update_row.get("evidence_reference")),
        listed_date=listed,
        delisted_date=delisted,
        is_active=_bool_or_empty(update_row.get("is_active_evidence")),
        is_st=_bool_or_empty(update_row.get("is_st")),
        is_suspended=_bool_or_empty(update_row.get("is_suspended")),
        listed_date_evidence=listed,
        delisted_date_evidence=delisted,
        is_active_evidence=_bool_or_empty(update_row.get("is_active_evidence")),
        as_of_date=_date_text(update_row.get("as_of_date")),
        name=_text(update_row.get("name")),
        instrument_type=_text(update_row.get("instrument_type")),
        exchange=_text(update_row.get("exchange")),
        industry=_text(update_row.get("industry")),
        min_lot=_text(update_row.get("min_lot")),
        t_plus_rule=_text(update_row.get("t_plus_rule")),
        available_time=_datetime_text(update_row.get("available_time")),
        revision_id=_text(update_row.get("revision_id")),
        source=_text(update_row.get("source")),
        survivorship_bias_warning=_is_true(plan_row.get("survivorship_bias_warning")),
        survivorship_bias_resolved=_is_true(update_row.get("survivorship_bias_resolved")),
    )


def _default_blocker(status: str, plan_row: dict[str, Any], update_row: dict[str, Any]) -> str:
    if status == "NEEDS_MANUAL_REVIEW":
        return _text(plan_row.get("blocker_reason")) or "Manual review is required before PIT approval."
    if status == "NEEDS_MORE_EVIDENCE":
        return _text(update_row.get("review_reason")) or "More PIT evidence is required before approval."
    if status == "REJECTED":
        return _text(update_row.get("review_reason")) or "Reviewer rejected this PIT universe row."
    return ""


def _validate_updates_match_plan(plan_frame: pd.DataFrame, update_frame: pd.DataFrame) -> None:
    if update_frame.empty:
        return
    plan_keys = set(plan_frame[REVIEW_KEY_COLUMNS].astype(str).agg("|".join, axis=1))
    update_keys = set(update_frame[REVIEW_KEY_COLUMNS].astype(str).agg("|".join, axis=1))
    unknown = sorted(update_keys - plan_keys)
    if unknown:
        raise ValueError(f"Review updates reference rows missing from overlay plan: {', '.join(unknown)}")


def _finalize_reviewed_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in [
        "include_flag",
        "valid_for_signal_date",
        "is_active",
        "is_st",
        "is_suspended",
        "is_active_evidence",
        "survivorship_bias_warning",
        "survivorship_bias_resolved",
        "manual_review_required",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "review_only",
    ]:
        if column in output.columns:
            output[column] = output[column].astype(object)
    return output


def _status_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = frame["review_status"].value_counts().to_dict() if "review_status" in frame.columns else {}
    return {
        "approved": int(counts.get("APPROVED_FOR_PIT_UNIVERSE", 0)),
        "rejected": int(counts.get("REJECTED", 0)),
        "needs_more_evidence": int(counts.get("NEEDS_MORE_EVIDENCE", 0)),
        "needs_manual_review": int(counts.get("NEEDS_MANUAL_REVIEW", 0)),
    }


def _build_warnings(request: PitUniverseOverlayReviewRequest, reviewed_frame: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if request.write_review_template_only:
        warnings.append("Review template only: no rows were approved.")
    if _true_count(reviewed_frame, "valid_for_signal_date") == 0:
        warnings.append("No rows are valid for signal date yet.")
    if int((reviewed_frame["review_status"] == "NEEDS_MORE_EVIDENCE").sum()) > 0:
        warnings.append("Some rows need more PIT evidence before approval.")
    return warnings


def _assert_settings_safe(settings: PitUniverseOverlayReviewSettings) -> None:
    unsafe = {
        "enable_live_trading": settings.enable_live_trading,
        "enable_broker_api": settings.enable_broker_api,
        "enable_order_placement": settings.enable_order_placement,
        "enable_message_delivery": settings.enable_message_delivery,
        "enable_external_api": settings.enable_external_api,
        "enable_llm_api": settings.enable_llm_api,
    }
    enabled = [name for name, value in unsafe.items() if bool(value)]
    if enabled:
        raise ValueError(f"PIT universe overlay review cannot enable unsafe behavior: {', '.join(enabled)}")


def _row_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            _date_text(row.get("signal_date")),
            normalize_symbol_value(row.get("symbol")),
            _text(row.get("universe_name")),
        ]
    )


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].map(_is_true).sum())


def _present(value: Any) -> bool:
    return _text(value) != ""


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "nat", "none", "null"}:
        return ""
    return text


def _date_text(value: Any) -> str:
    parsed = _parse_date(value)
    return "" if parsed is None else parsed.strftime("%Y-%m-%d")


def _datetime_text(value: Any) -> str:
    parsed = _parse_datetime(value)
    return "" if parsed is None else parsed.strftime("%Y-%m-%d %H:%M:%S")


def _parse_date(value: Any) -> pd.Timestamp | None:
    text = _text(value)
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).normalize()


def _parse_datetime(value: Any) -> pd.Timestamp | None:
    text = _text(value)
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).tz_localize(None) if pd.Timestamp(parsed).tzinfo else pd.Timestamp(parsed)


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    return text in {"true", "1", "yes", "y", "t"}


def _bool_or_empty(value: Any) -> bool | str:
    if not _present(value):
        return ""
    return _is_true(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
