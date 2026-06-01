"""Evidence completion templates for PIT universe overlay reviews.

This helper reads reviewed PIT universe overlay rows and optionally joins
non-authoritative base-universe hints. It writes report/template artifacts only;
it does not approve rows, export universe files, build snapshots, run
current-candidates, compute labels, mutate cache, or perform trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_overlay_review import REVIEW_OUTPUT_COLUMNS


HELPER_OUTPUT_COLUMNS = [
    "helper_id",
    "review_id",
    "signal_date",
    "symbol",
    "universe_name",
    "current_review_status",
    "current_valid_for_signal_date",
    "current_survivorship_bias_warning",
    "current_survivorship_bias_resolved",
    "missing_reviewer",
    "missing_reviewed_at",
    "missing_review_reason",
    "missing_evidence_source",
    "missing_evidence_path_or_reference",
    "missing_listed_date_evidence",
    "missing_is_active_evidence",
    "missing_survivorship_bias_resolution",
    "suggested_name",
    "suggested_instrument_type",
    "suggested_exchange",
    "suggested_industry",
    "suggested_min_lot",
    "suggested_t_plus_rule",
    "suggested_is_active",
    "suggested_is_st",
    "suggested_is_suspended",
    "suggested_source",
    "suggested_revision_id",
    "suggested_available_time",
    "hint_source_path",
    "hint_as_of_date",
    "hint_available_time",
    "hint_is_future_dated_for_signal_date",
    "hint_authoritative_for_pit",
    "next_review_action",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "evidence_completion_only",
]

HELPER_REQUIRED_INPUT_COLUMNS = [
    "review_id",
    "overlay_plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "include_flag",
    "review_status",
    "valid_for_signal_date",
    "survivorship_bias_warning",
    "survivorship_bias_resolved",
]

SAFETY_STATEMENT = (
    "No universe export, data/raw write, data/processed write, current-candidates generation, "
    "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
    "network/API, LLM/API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_evidence_completion_helper")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_universe_export: bool = False
    enable_data_raw_write: bool = False
    enable_data_processed_write: bool = False
    enable_current_candidates: bool = False
    enable_snapshot_build: bool = False
    enable_forward_labels: bool = False
    enable_cache_mutation: bool = False
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False
    enable_network_api: bool = False
    enable_llm_api: bool = False


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperRequest:
    review: Path
    base_universe: Path | None = None


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperRow:
    helper_id: str
    review_id: str
    signal_date: str
    symbol: str
    universe_name: str
    current_review_status: str
    current_valid_for_signal_date: bool
    current_survivorship_bias_warning: bool
    current_survivorship_bias_resolved: bool
    missing_reviewer: bool
    missing_reviewed_at: bool
    missing_review_reason: bool
    missing_evidence_source: bool
    missing_evidence_path_or_reference: bool
    missing_listed_date_evidence: bool
    missing_is_active_evidence: bool
    missing_survivorship_bias_resolution: bool
    suggested_name: str
    suggested_instrument_type: str
    suggested_exchange: str
    suggested_industry: str
    suggested_min_lot: str
    suggested_t_plus_rule: str
    suggested_is_active: str
    suggested_is_st: str
    suggested_is_suspended: str
    suggested_source: str
    suggested_revision_id: str
    suggested_available_time: str
    hint_source_path: str
    hint_as_of_date: str
    hint_available_time: str
    hint_is_future_dated_for_signal_date: bool
    hint_authoritative_for_pit: bool
    next_review_action: str
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    evidence_completion_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "helper_id": self.helper_id,
            "review_id": self.review_id,
            "signal_date": self.signal_date,
            "symbol": self.symbol,
            "universe_name": self.universe_name,
            "current_review_status": self.current_review_status,
            "current_valid_for_signal_date": self.current_valid_for_signal_date,
            "current_survivorship_bias_warning": self.current_survivorship_bias_warning,
            "current_survivorship_bias_resolved": self.current_survivorship_bias_resolved,
            "missing_reviewer": self.missing_reviewer,
            "missing_reviewed_at": self.missing_reviewed_at,
            "missing_review_reason": self.missing_review_reason,
            "missing_evidence_source": self.missing_evidence_source,
            "missing_evidence_path_or_reference": self.missing_evidence_path_or_reference,
            "missing_listed_date_evidence": self.missing_listed_date_evidence,
            "missing_is_active_evidence": self.missing_is_active_evidence,
            "missing_survivorship_bias_resolution": self.missing_survivorship_bias_resolution,
            "suggested_name": self.suggested_name,
            "suggested_instrument_type": self.suggested_instrument_type,
            "suggested_exchange": self.suggested_exchange,
            "suggested_industry": self.suggested_industry,
            "suggested_min_lot": self.suggested_min_lot,
            "suggested_t_plus_rule": self.suggested_t_plus_rule,
            "suggested_is_active": self.suggested_is_active,
            "suggested_is_st": self.suggested_is_st,
            "suggested_is_suspended": self.suggested_is_suspended,
            "suggested_source": self.suggested_source,
            "suggested_revision_id": self.suggested_revision_id,
            "suggested_available_time": self.suggested_available_time,
            "hint_source_path": self.hint_source_path,
            "hint_as_of_date": self.hint_as_of_date,
            "hint_available_time": self.hint_available_time,
            "hint_is_future_dated_for_signal_date": self.hint_is_future_dated_for_signal_date,
            "hint_authoritative_for_pit": self.hint_authoritative_for_pit,
            "next_review_action": self.next_review_action,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
            "evidence_completion_only": self.evidence_completion_only,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperArtifactPaths:
    artifact_dir: Path
    evidence_completion_template: Path
    gap_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "evidence_completion_template": self.evidence_completion_template,
            "gap_report": self.gap_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperResult:
    helper_id: str
    status: str
    request: PitUniverseEvidenceCompletionHelperRequest
    row_count: int
    needs_evidence_count: int
    rows_with_base_hints_count: int
    future_dated_hint_count: int
    authoritative_hint_count: int
    approved_count: int
    valid_for_signal_date_count: int
    template_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_pit_universe_review_for_evidence_completion(review: str | Path) -> pd.DataFrame:
    """Load reviewed PIT universe overlay rows while preserving symbols."""

    review_path = Path(review)
    if not review_path.exists():
        raise FileNotFoundError(f"Reviewed PIT universe overlay not found: {review_path}")
    frame = read_csv_preserve_symbol_columns(review_path, keep_default_na=False)
    missing = [column for column in HELPER_REQUIRED_INPUT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Reviewed PIT universe overlay missing required columns: {', '.join(missing)}")
    for column in REVIEW_OUTPUT_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output


def load_base_universe_hints(base_universe: str | Path | None) -> pd.DataFrame:
    """Load optional base-universe rows as non-authoritative symbol hints."""

    if base_universe is None:
        return pd.DataFrame()
    base_path = Path(base_universe)
    if not base_path.exists():
        raise FileNotFoundError(f"Base universe hints file not found: {base_path}")
    frame = read_csv_preserve_symbol_columns(base_path, keep_default_na=False)
    if "symbol" not in frame.columns:
        raise ValueError("Base universe hints missing required column: symbol")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    for column in [
        "name",
        "instrument_type",
        "exchange",
        "industry",
        "min_lot",
        "t_plus_rule",
        "is_active",
        "is_st",
        "is_suspended",
        "source",
        "revision_id",
        "available_time",
        "as_of_date",
    ]:
        if column not in output.columns:
            output[column] = ""
    output["_hint_sort_as_of_date"] = output["as_of_date"].map(_parse_date)
    output["_hint_sort_available_time"] = output["available_time"].map(_parse_datetime)
    sort_columns = ["symbol", "_hint_sort_as_of_date", "_hint_sort_available_time", "revision_id"]
    output = output.sort_values(sort_columns).drop_duplicates(subset=["symbol"], keep="last")
    return output.drop(columns=["_hint_sort_as_of_date", "_hint_sort_available_time"]).reset_index(drop=True)


def build_pit_universe_evidence_completion_helper(
    *,
    review: str | Path,
    base_universe: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: PitUniverseEvidenceCompletionHelperSettings | None = None,
) -> PitUniverseEvidenceCompletionHelperResult:
    """Build report-only PIT universe evidence completion templates."""

    resolved_settings = settings or PitUniverseEvidenceCompletionHelperSettings()
    if output_dir is not None:
        resolved_settings = PitUniverseEvidenceCompletionHelperSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_universe_export=resolved_settings.enable_universe_export,
            enable_data_raw_write=resolved_settings.enable_data_raw_write,
            enable_data_processed_write=resolved_settings.enable_data_processed_write,
            enable_current_candidates=resolved_settings.enable_current_candidates,
            enable_snapshot_build=resolved_settings.enable_snapshot_build,
            enable_forward_labels=resolved_settings.enable_forward_labels,
            enable_cache_mutation=resolved_settings.enable_cache_mutation,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_order_placement=resolved_settings.enable_order_placement,
            enable_message_delivery=resolved_settings.enable_message_delivery,
            enable_network_api=resolved_settings.enable_network_api,
            enable_llm_api=resolved_settings.enable_llm_api,
        )
    _assert_settings_safe(resolved_settings)

    request = PitUniverseEvidenceCompletionHelperRequest(
        review=Path(review),
        base_universe=Path(base_universe) if base_universe else None,
    )
    review_frame = load_pit_universe_review_for_evidence_completion(request.review)
    hint_frame = load_base_universe_hints(request.base_universe)
    helper_id = generate_pit_universe_evidence_completion_helper_id(request, review_frame, resolved_settings)
    hints_by_symbol = {
        normalize_symbol_value(row.get("symbol")): row
        for row in hint_frame.to_dict("records")
    }
    rows = [
        _build_helper_row(
            row,
            hint_row=hints_by_symbol.get(normalize_symbol_value(row.get("symbol"))),
            hint_source_path=str(request.base_universe or ""),
            helper_id=helper_id,
        ).as_dict()
        for row in review_frame.to_dict("records")
    ]
    template_frame = _finalize_template_frame(pd.DataFrame(rows, columns=HELPER_OUTPUT_COLUMNS))
    counts = _build_counts(template_frame)
    paths = resolve_pit_universe_evidence_completion_helper_paths(resolved_settings.output_dir, helper_id)
    result = PitUniverseEvidenceCompletionHelperResult(
        helper_id=helper_id,
        status="WARN" if counts["needs_evidence_count"] else "PASS",
        request=request,
        row_count=counts["row_count"],
        needs_evidence_count=counts["needs_evidence_count"],
        rows_with_base_hints_count=counts["rows_with_base_hints_count"],
        future_dated_hint_count=counts["future_dated_hint_count"],
        authoritative_hint_count=counts["authoritative_hint_count"],
        approved_count=counts["approved_count"],
        valid_for_signal_date_count=counts["valid_for_signal_date_count"],
        template_frame=template_frame,
        warnings=_build_warnings(counts, request),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_evidence_completion_artifacts(result)
    return result


def write_pit_universe_evidence_completion_artifacts(
    result: PitUniverseEvidenceCompletionHelperResult,
) -> dict[str, Path]:
    """Write evidence completion template, report, and metadata."""

    paths = PitUniverseEvidenceCompletionHelperArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.template_frame.to_csv(paths.evidence_completion_template, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_pit_universe_evidence_completion_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.gap_report.write_text(render_pit_universe_evidence_completion_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_evidence_completion_report(result: PitUniverseEvidenceCompletionHelperResult) -> str:
    """Render a human-readable evidence gap report."""

    lines = [
        f"# PIT Universe Evidence Completion Helper: {result.helper_id}",
        "",
        SAFETY_STATEMENT,
        "This is an evidence-completion-only artifact. It does not approve rows or export usable universe files.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Evidence Gaps",
        "",
        _markdown_table(result.template_frame, HELPER_OUTPUT_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_pit_universe_evidence_completion_metadata(
    result: PitUniverseEvidenceCompletionHelperResult,
) -> dict[str, Any]:
    return {
        "helper_id": result.helper_id,
        "status": result.status,
        "created_at": "2024-05-29T00:00:00",
        "review": str(result.request.review),
        "base_universe": str(result.request.base_universe or ""),
        "row_count": result.row_count,
        "needs_evidence_count": result.needs_evidence_count,
        "rows_with_base_hints_count": result.rows_with_base_hints_count,
        "future_dated_hint_count": result.future_dated_hint_count,
        "authoritative_hint_count": result.authoritative_hint_count,
        "approved_count": result.approved_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "Base universe values are hints only and are not point-in-time approval evidence.",
            "The helper does not approve rows, export universe files, or validate strategy performance.",
            "Human reviewers must provide evidence before later approval/export readiness workflows can proceed.",
        ],
    }


def generate_pit_universe_evidence_completion_helper_id(
    request: PitUniverseEvidenceCompletionHelperRequest,
    review_frame: pd.DataFrame,
    settings: PitUniverseEvidenceCompletionHelperSettings,
) -> str:
    payload = {
        "review": str(request.review),
        "base_universe": str(request.base_universe or ""),
        "config_version": settings.config_version,
        "rows": review_frame[
            [
                column
                for column in ["review_id", "signal_date", "symbol", "universe_name", "review_status"]
                if column in review_frame
            ]
        ].to_dict("records"),
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_pit_universe_evidence_completion_helper_paths(
    output_dir: str | Path,
    helper_id: str,
) -> PitUniverseEvidenceCompletionHelperArtifactPaths:
    artifact_dir = Path(output_dir) / helper_id
    return PitUniverseEvidenceCompletionHelperArtifactPaths(
        artifact_dir=artifact_dir,
        evidence_completion_template=artifact_dir / "pit_universe_evidence_completion_template.csv",
        gap_report=artifact_dir / "pit_universe_evidence_gap_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _build_helper_row(
    review_row: dict[str, Any],
    *,
    hint_row: dict[str, Any] | None,
    hint_source_path: str,
    helper_id: str,
) -> PitUniverseEvidenceCompletionHelperRow:
    has_hint = hint_row is not None
    hint = hint_row or {}
    signal_date = _parse_date(review_row.get("signal_date"))
    decision_time = pd.Timestamp(signal_date) + pd.Timedelta(hours=15, minutes=30) if signal_date is not None else None
    hint_as_of_date = _parse_date(hint.get("as_of_date"))
    hint_available_time = _parse_datetime(hint.get("available_time"))
    hint_is_future = False
    if signal_date is not None and hint_as_of_date is not None and hint_as_of_date > signal_date:
        hint_is_future = True
    if decision_time is not None and hint_available_time is not None and hint_available_time > decision_time:
        hint_is_future = True

    missing_reviewer = not _present(review_row.get("reviewer"))
    missing_reviewed_at = not _present(review_row.get("reviewed_at"))
    missing_review_reason = not _present(review_row.get("review_reason"))
    missing_evidence_source = not _present(review_row.get("evidence_source"))
    missing_evidence_path_or_reference = not (
        _present(review_row.get("evidence_path")) or _present(review_row.get("evidence_reference"))
    )
    missing_listed_date_evidence = not _present(review_row.get("listed_date_evidence"))
    missing_is_active_evidence = not _is_true(review_row.get("is_active_evidence"))
    missing_survivorship_bias_resolution = not _is_true(review_row.get("survivorship_bias_resolved"))
    needs_evidence = any(
        [
            missing_reviewer,
            missing_reviewed_at,
            missing_review_reason,
            missing_evidence_source,
            missing_evidence_path_or_reference,
            missing_listed_date_evidence,
            missing_is_active_evidence,
            missing_survivorship_bias_resolution,
        ]
    )

    return PitUniverseEvidenceCompletionHelperRow(
        helper_id=helper_id,
        review_id=_text(review_row.get("review_id")),
        signal_date=_date_text(review_row.get("signal_date")),
        symbol=normalize_symbol_value(review_row.get("symbol")),
        universe_name=_text(review_row.get("universe_name")),
        current_review_status=_text(review_row.get("review_status")).upper(),
        current_valid_for_signal_date=_is_true(review_row.get("valid_for_signal_date")),
        current_survivorship_bias_warning=_is_true(review_row.get("survivorship_bias_warning")),
        current_survivorship_bias_resolved=_is_true(review_row.get("survivorship_bias_resolved")),
        missing_reviewer=missing_reviewer,
        missing_reviewed_at=missing_reviewed_at,
        missing_review_reason=missing_review_reason,
        missing_evidence_source=missing_evidence_source,
        missing_evidence_path_or_reference=missing_evidence_path_or_reference,
        missing_listed_date_evidence=missing_listed_date_evidence,
        missing_is_active_evidence=missing_is_active_evidence,
        missing_survivorship_bias_resolution=missing_survivorship_bias_resolution,
        suggested_name=_text(hint.get("name")),
        suggested_instrument_type=_text(hint.get("instrument_type")),
        suggested_exchange=_text(hint.get("exchange")),
        suggested_industry=_text(hint.get("industry")),
        suggested_min_lot=_text(hint.get("min_lot")),
        suggested_t_plus_rule=_text(hint.get("t_plus_rule")),
        suggested_is_active=_text(hint.get("is_active")),
        suggested_is_st=_text(hint.get("is_st")),
        suggested_is_suspended=_text(hint.get("is_suspended")),
        suggested_source=_text(hint.get("source")),
        suggested_revision_id=_text(hint.get("revision_id")),
        suggested_available_time=_datetime_text(hint.get("available_time")),
        hint_source_path=hint_source_path if has_hint else "",
        hint_as_of_date=_date_text(hint.get("as_of_date")),
        hint_available_time=_datetime_text(hint.get("available_time")),
        hint_is_future_dated_for_signal_date=hint_is_future,
        hint_authoritative_for_pit=False,
        next_review_action=(
            "Fill reviewer, reviewed_at, evidence, listed-date, active-status, and survivorship-resolution fields."
            if needs_evidence
            else "Review row already has evidence; keep helper output as non-authoritative context."
        ),
    )


def _build_counts(frame: pd.DataFrame) -> dict[str, int]:
    row_count = int(len(frame))
    gap_columns = [
        "missing_reviewer",
        "missing_reviewed_at",
        "missing_review_reason",
        "missing_evidence_source",
        "missing_evidence_path_or_reference",
        "missing_listed_date_evidence",
        "missing_is_active_evidence",
        "missing_survivorship_bias_resolution",
    ]
    if frame.empty:
        needs_evidence_count = 0
    else:
        needs_evidence_count = int(frame[gap_columns].apply(lambda row: any(_is_true(value) for value in row), axis=1).sum())
    return {
        "row_count": row_count,
        "needs_evidence_count": needs_evidence_count,
        "rows_with_base_hints_count": int(frame["hint_source_path"].map(_present).sum()) if not frame.empty else 0,
        "future_dated_hint_count": _true_count(frame, "hint_is_future_dated_for_signal_date"),
        "authoritative_hint_count": _true_count(frame, "hint_authoritative_for_pit"),
        "approved_count": int((frame["current_review_status"] == "APPROVED_FOR_PIT_UNIVERSE").sum())
        if not frame.empty
        else 0,
        "valid_for_signal_date_count": _true_count(frame, "current_valid_for_signal_date"),
    }


def _build_warnings(
    counts: dict[str, int],
    request: PitUniverseEvidenceCompletionHelperRequest,
) -> list[str]:
    warnings = []
    if counts["needs_evidence_count"] > 0:
        warnings.append("Some PIT universe review rows still need human evidence completion.")
    if request.base_universe is None:
        warnings.append("No base universe hints were supplied.")
    if counts["future_dated_hint_count"] > 0:
        warnings.append("Some base-universe hints are future-dated for their signal dates and are non-authoritative.")
    if counts["authoritative_hint_count"] > 0:
        warnings.append("Unexpected authoritative hints detected; helper hints should remain non-authoritative.")
    return warnings


def _summary_dict(result: PitUniverseEvidenceCompletionHelperResult) -> dict[str, Any]:
    return {
        "helper_id": result.helper_id,
        "status": result.status,
        "row_count": result.row_count,
        "needs_evidence_count": result.needs_evidence_count,
        "rows_with_base_hints_count": result.rows_with_base_hints_count,
        "future_dated_hint_count": result.future_dated_hint_count,
        "authoritative_hint_count": result.authoritative_hint_count,
        "approved_count": result.approved_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "review": str(result.request.review),
        "base_universe": str(result.request.base_universe or ""),
    }


def _audit_metadata(
    request: PitUniverseEvidenceCompletionHelperRequest,
    settings: PitUniverseEvidenceCompletionHelperSettings,
) -> dict[str, Any]:
    return {
        "review": str(request.review),
        "base_universe": str(request.base_universe or ""),
        "config_version": settings.config_version,
        "evidence_completion_only": True,
        "no_universe_export": True,
        "universe_exported": False,
        "no_data_raw_write": True,
        "would_write_data_raw": False,
        "no_data_processed_write": True,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "current_candidates_executed": False,
        "no_snapshot_built": True,
        "snapshot_manifest_built": False,
        "no_forward_labels": True,
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


def _assert_settings_safe(settings: PitUniverseEvidenceCompletionHelperSettings) -> None:
    unsafe = {
        "enable_universe_export": settings.enable_universe_export,
        "enable_data_raw_write": settings.enable_data_raw_write,
        "enable_data_processed_write": settings.enable_data_processed_write,
        "enable_current_candidates": settings.enable_current_candidates,
        "enable_snapshot_build": settings.enable_snapshot_build,
        "enable_forward_labels": settings.enable_forward_labels,
        "enable_cache_mutation": settings.enable_cache_mutation,
        "enable_live_trading": settings.enable_live_trading,
        "enable_broker_api": settings.enable_broker_api,
        "enable_order_placement": settings.enable_order_placement,
        "enable_message_delivery": settings.enable_message_delivery,
        "enable_network_api": settings.enable_network_api,
        "enable_llm_api": settings.enable_llm_api,
    }
    enabled = [name for name, value in unsafe.items() if bool(value)]
    if enabled:
        raise ValueError(f"PIT universe evidence completion helper cannot enable unsafe behavior: {', '.join(enabled)}")


def _finalize_template_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in [
        "current_valid_for_signal_date",
        "current_survivorship_bias_warning",
        "current_survivorship_bias_resolved",
        "missing_reviewer",
        "missing_reviewed_at",
        "missing_review_reason",
        "missing_evidence_source",
        "missing_evidence_path_or_reference",
        "missing_listed_date_evidence",
        "missing_is_active_evidence",
        "missing_survivorship_bias_resolution",
        "hint_is_future_dated_for_signal_date",
        "hint_authoritative_for_pit",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "evidence_completion_only",
    ]:
        if column in output.columns:
            output[column] = output[column].map(_is_true).astype(object)
    return output[HELPER_OUTPUT_COLUMNS]


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
    timestamp = pd.Timestamp(parsed)
    if timestamp.tzinfo:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _parse_datetime(value: Any) -> pd.Timestamp | None:
    text = _text(value)
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    timestamp = pd.Timestamp(parsed)
    return timestamp.tz_localize(None) if timestamp.tzinfo else timestamp


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    return text in {"true", "1", "yes", "y", "t"}


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "|---|---|"]
    rows.extend(f"| {key} | {value} |" for key, value in values.items())
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    if frame.empty:
        return "_No rows._"
    available = [column for column in columns if column in frame.columns]
    preview = frame[available].head(max_rows).copy()
    header = "| " + " | ".join(available) + " |"
    separator = "| " + " | ".join("---" for _ in available) + " |"
    rows = [header, separator]
    for _, row in preview.iterrows():
        rows.append("| " + " | ".join(_markdown_cell(row.get(column)) for column in available) + " |")
    if len(frame) > max_rows:
        rows.append(f"\n_Showing {max_rows} of {len(frame)} rows._")
    return "\n".join(rows)


def _markdown_cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", " ")


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
