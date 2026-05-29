"""Report-only readiness checks for reviewed PIT universe overlay export.

This module validates whether reviewed PIT universe overlay rows are ready for a
later explicit universe export step. It writes readiness artifacts under reports
only; it does not create usable universe inputs, build snapshots, run
current-candidates, compute labels, mutate cache, or perform trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import (
    UNIVERSE_SNAPSHOT_SCHEMA,
    normalize_symbol_value,
    read_csv_preserve_symbol_columns,
)
from quant_replay_system.point_in_time_universe_overlay_review import REVIEW_OUTPUT_COLUMNS


READINESS_STATUSES = {
    "EXPORT_BLOCKED_NO_APPROVED_ROWS",
    "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE",
    "EXPORT_BLOCKED_UNRESOLVED_SURVIVORSHIP",
    "EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS",
    "EXPORT_BLOCKED_INVALID_PIT_DATES",
    "EXPORT_READY_FOR_DRY_RUN",
    "EXPORT_READY_REVIEW_ONLY",
}

READINESS_OUTPUT_COLUMNS = [
    "export_readiness_id",
    "review_id",
    "signal_date",
    "symbol",
    "universe_name",
    "review_status",
    "include_flag",
    "valid_for_signal_date",
    "export_ready",
    "export_readiness_status",
    "export_blocker_reason",
    "required_column_missing_count",
    "missing_required_columns",
    "reviewer",
    "reviewed_at",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "survivorship_bias_warning",
    "survivorship_bias_resolved",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "export_readiness_only",
]

SAFETY_STATEMENT = (
    "No universe export, data/raw write, data/processed write, current-candidates generation, "
    "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
    "LLM/API, external API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_overlay_export_readiness")
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
    enable_external_api: bool = False
    enable_llm_api: bool = False


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessRequest:
    review: Path


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessRow:
    export_readiness_id: str
    review_id: str
    signal_date: str
    symbol: str
    universe_name: str
    review_status: str
    include_flag: bool
    valid_for_signal_date: bool
    export_ready: bool
    export_readiness_status: str
    export_blocker_reason: str
    required_column_missing_count: int
    missing_required_columns: str
    reviewer: str
    reviewed_at: str
    evidence_source: str
    evidence_path: str
    evidence_reference: str
    survivorship_bias_warning: bool
    survivorship_bias_resolved: bool
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    export_readiness_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "export_readiness_id": self.export_readiness_id,
            "review_id": self.review_id,
            "signal_date": self.signal_date,
            "symbol": self.symbol,
            "universe_name": self.universe_name,
            "review_status": self.review_status,
            "include_flag": self.include_flag,
            "valid_for_signal_date": self.valid_for_signal_date,
            "export_ready": self.export_ready,
            "export_readiness_status": self.export_readiness_status,
            "export_blocker_reason": self.export_blocker_reason,
            "required_column_missing_count": self.required_column_missing_count,
            "missing_required_columns": self.missing_required_columns,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "evidence_source": self.evidence_source,
            "evidence_path": self.evidence_path,
            "evidence_reference": self.evidence_reference,
            "survivorship_bias_warning": self.survivorship_bias_warning,
            "survivorship_bias_resolved": self.survivorship_bias_resolved,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
            "export_readiness_only": self.export_readiness_only,
        }


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessArtifactPaths:
    artifact_dir: Path
    readiness_csv: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "readiness_csv": self.readiness_csv,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseOverlayExportReadinessResult:
    export_readiness_id: str
    status: str
    readiness_status: str
    request: PitUniverseOverlayExportReadinessRequest
    row_count: int
    approved_count: int
    export_ready_count: int
    blocked_count: int
    no_approved_rows: bool
    missing_required_columns_count: int
    unresolved_survivorship_warning_count: int
    duplicate_key_count: int
    invalid_pit_date_count: int
    readiness_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_pit_universe_overlay_review_for_export_readiness(review: str | Path) -> pd.DataFrame:
    """Load a reviewed PIT universe overlay CSV while preserving symbols."""

    review_path = Path(review)
    if not review_path.exists():
        raise FileNotFoundError(f"Reviewed PIT universe overlay not found: {review_path}")
    frame = read_csv_preserve_symbol_columns(review_path, keep_default_na=False)
    missing = [column for column in REVIEW_OUTPUT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Reviewed PIT universe overlay missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output


def build_pit_universe_overlay_export_readiness(
    *,
    review: str | Path,
    output_dir: str | Path | None = None,
    settings: PitUniverseOverlayExportReadinessSettings | None = None,
) -> PitUniverseOverlayExportReadinessResult:
    """Build report-only PIT universe overlay export readiness artifacts."""

    resolved_settings = settings or PitUniverseOverlayExportReadinessSettings()
    if output_dir is not None:
        resolved_settings = PitUniverseOverlayExportReadinessSettings(
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
            enable_external_api=resolved_settings.enable_external_api,
            enable_llm_api=resolved_settings.enable_llm_api,
        )
    _assert_settings_safe(resolved_settings)

    request = PitUniverseOverlayExportReadinessRequest(review=Path(review))
    review_frame = load_pit_universe_overlay_review_for_export_readiness(request.review)
    export_readiness_id = generate_pit_universe_overlay_export_readiness_id(
        request,
        review_frame,
        resolved_settings,
    )
    rows = [
        evaluate_pit_universe_overlay_export_row(row.to_dict(), export_readiness_id=export_readiness_id).as_dict()
        for _, row in review_frame.iterrows()
    ]
    readiness_frame = _finalize_readiness_frame(pd.DataFrame(rows, columns=READINESS_OUTPUT_COLUMNS))
    readiness_frame, duplicate_key_count = _mark_duplicate_export_ready_rows(readiness_frame)
    counts = _build_counts(readiness_frame)
    readiness_status = _aggregate_readiness_status(counts)
    status = "PASS" if readiness_status in {"EXPORT_READY_FOR_DRY_RUN", "EXPORT_READY_REVIEW_ONLY"} else "WARN"
    paths = resolve_pit_universe_overlay_export_readiness_paths(
        resolved_settings.output_dir,
        export_readiness_id,
    )
    result = PitUniverseOverlayExportReadinessResult(
        export_readiness_id=export_readiness_id,
        status=status,
        readiness_status=readiness_status,
        request=request,
        row_count=len(readiness_frame),
        approved_count=counts["approved_count"],
        export_ready_count=counts["export_ready_count"],
        blocked_count=counts["blocked_count"],
        no_approved_rows=counts["approved_count"] == 0,
        missing_required_columns_count=counts["missing_required_columns_count"],
        unresolved_survivorship_warning_count=counts["unresolved_survivorship_warning_count"],
        duplicate_key_count=duplicate_key_count,
        invalid_pit_date_count=counts["invalid_pit_date_count"],
        readiness_frame=readiness_frame,
        warnings=_build_warnings(counts, readiness_status),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_overlay_export_readiness_artifacts(result)
    return result


def evaluate_pit_universe_overlay_export_row(
    row: dict[str, Any],
    *,
    export_readiness_id: str,
) -> PitUniverseOverlayExportReadinessRow:
    """Evaluate one reviewed row for report-only export readiness."""

    missing_required_columns = _missing_universe_columns(row)
    blockers: list[str] = []
    status = "EXPORT_READY_FOR_DRY_RUN"
    export_ready = True

    review_status = _text(row.get("review_status")).upper()
    if review_status != "APPROVED_FOR_PIT_UNIVERSE":
        blockers.append("review_status must be APPROVED_FOR_PIT_UNIVERSE before export readiness")
        return PitUniverseOverlayExportReadinessRow(
            export_readiness_id=export_readiness_id,
            review_id=_text(row.get("review_id")),
            signal_date=_date_text(row.get("signal_date")),
            symbol=normalize_symbol_value(row.get("symbol")),
            universe_name=_text(row.get("universe_name")),
            review_status=review_status,
            include_flag=_is_true(row.get("include_flag")),
            valid_for_signal_date=_is_true(row.get("valid_for_signal_date")),
            export_ready=False,
            export_readiness_status="EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE",
            export_blocker_reason="; ".join(blockers),
            required_column_missing_count=len(missing_required_columns),
            missing_required_columns=",".join(missing_required_columns),
            reviewer=_text(row.get("reviewer")),
            reviewed_at=_text(row.get("reviewed_at")),
            evidence_source=_text(row.get("evidence_source")),
            evidence_path=_text(row.get("evidence_path")),
            evidence_reference=_text(row.get("evidence_reference")),
            survivorship_bias_warning=_is_true(row.get("survivorship_bias_warning")),
            survivorship_bias_resolved=_is_true(row.get("survivorship_bias_resolved")),
        )
    if not _is_true(row.get("valid_for_signal_date")):
        blockers.append("valid_for_signal_date must be true")
        status = "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"
        export_ready = False
    if not _is_true(row.get("include_flag")):
        blockers.append("include_flag must be true")
        status = "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"
        export_ready = False
    evidence_blockers = _evidence_blockers(row)
    if evidence_blockers:
        blockers.extend(evidence_blockers)
        status = "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"
        export_ready = False
    if _is_true(row.get("survivorship_bias_warning")) and not _is_true(row.get("survivorship_bias_resolved")):
        blockers.append("survivorship_bias_warning is unresolved")
        status = "EXPORT_BLOCKED_UNRESOLVED_SURVIVORSHIP"
        export_ready = False
    date_blockers = _pit_date_blockers(row)
    if date_blockers:
        blockers.extend(date_blockers)
        status = "EXPORT_BLOCKED_INVALID_PIT_DATES"
        export_ready = False
    if missing_required_columns:
        blockers.append(f"missing required universe columns: {', '.join(missing_required_columns)}")
        if export_ready:
            status = "EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS"
        export_ready = False

    return PitUniverseOverlayExportReadinessRow(
        export_readiness_id=export_readiness_id,
        review_id=_text(row.get("review_id")),
        signal_date=_date_text(row.get("signal_date")),
        symbol=normalize_symbol_value(row.get("symbol")),
        universe_name=_text(row.get("universe_name")),
        review_status=review_status,
        include_flag=_is_true(row.get("include_flag")),
        valid_for_signal_date=_is_true(row.get("valid_for_signal_date")),
        export_ready=export_ready,
        export_readiness_status=status,
        export_blocker_reason="; ".join(blockers),
        required_column_missing_count=len(missing_required_columns),
        missing_required_columns=",".join(missing_required_columns),
        reviewer=_text(row.get("reviewer")),
        reviewed_at=_text(row.get("reviewed_at")),
        evidence_source=_text(row.get("evidence_source")),
        evidence_path=_text(row.get("evidence_path")),
        evidence_reference=_text(row.get("evidence_reference")),
        survivorship_bias_warning=_is_true(row.get("survivorship_bias_warning")),
        survivorship_bias_resolved=_is_true(row.get("survivorship_bias_resolved")),
    )


def write_pit_universe_overlay_export_readiness_artifacts(
    result: PitUniverseOverlayExportReadinessResult,
) -> dict[str, Path]:
    """Write readiness CSV, metadata, and markdown report under outputs/reports."""

    paths = PitUniverseOverlayExportReadinessArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.readiness_frame.to_csv(paths.readiness_csv, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_pit_universe_overlay_export_readiness_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_pit_universe_overlay_export_readiness_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_overlay_export_readiness_report(
    result: PitUniverseOverlayExportReadinessResult,
) -> str:
    """Render a human-readable export readiness report."""

    lines = [
        f"# PIT Universe Overlay Export Readiness: {result.export_readiness_id}",
        "",
        SAFETY_STATEMENT,
        "This is a readiness-only artifact. It does not export usable universe files or write to data/raw or data/processed.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Readiness Rows",
        "",
        _markdown_table(result.readiness_frame, READINESS_OUTPUT_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_pit_universe_overlay_export_readiness_metadata(
    result: PitUniverseOverlayExportReadinessResult,
) -> dict[str, Any]:
    return {
        "export_readiness_id": result.export_readiness_id,
        "status": result.status,
        "readiness_status": result.readiness_status,
        "created_at": "2024-05-29T00:00:00",
        "review": str(result.request.review),
        "row_count": result.row_count,
        "approved_count": result.approved_count,
        "export_ready_count": result.export_ready_count,
        "blocked_count": result.blocked_count,
        "no_approved_rows": result.no_approved_rows,
        "missing_required_columns_count": result.missing_required_columns_count,
        "unresolved_survivorship_warning_count": result.unresolved_survivorship_warning_count,
        "duplicate_key_count": result.duplicate_key_count,
        "invalid_pit_date_count": result.invalid_pit_date_count,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "This workflow reports export readiness only and does not write usable universe files.",
            "APPROVED_FOR_PIT_UNIVERSE rows still require a later explicit export workflow before snapshot preparation.",
            "Readiness does not validate strategy performance or permit trading automation.",
        ],
    }


def generate_pit_universe_overlay_export_readiness_id(
    request: PitUniverseOverlayExportReadinessRequest,
    review_frame: pd.DataFrame,
    settings: PitUniverseOverlayExportReadinessSettings,
) -> str:
    payload = {
        "review": str(request.review),
        "config_version": settings.config_version,
        "rows": review_frame[
            [column for column in ["review_id", "signal_date", "symbol", "universe_name", "review_status"] if column in review_frame]
        ].to_dict("records"),
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_pit_universe_overlay_export_readiness_paths(
    output_dir: str | Path,
    export_readiness_id: str,
) -> PitUniverseOverlayExportReadinessArtifactPaths:
    artifact_dir = Path(output_dir) / export_readiness_id
    return PitUniverseOverlayExportReadinessArtifactPaths(
        artifact_dir=artifact_dir,
        readiness_csv=artifact_dir / "pit_universe_overlay_export_readiness.csv",
        report=artifact_dir / "pit_universe_overlay_export_readiness_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _missing_universe_columns(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    nullable_columns = {"listed_date", "delisted_date"}
    for column in UNIVERSE_SNAPSHOT_SCHEMA:
        if column not in row:
            missing.append(column)
            continue
        if column not in nullable_columns and not _present(row.get(column)):
            missing.append(column)
    return missing


def _evidence_blockers(row: dict[str, Any]) -> list[str]:
    blockers = []
    for column in ["reviewer", "reviewed_at", "evidence_source"]:
        if not _present(row.get(column)):
            blockers.append(f"{column} is required")
    if not (_present(row.get("evidence_path")) or _present(row.get("evidence_reference"))):
        blockers.append("evidence_path or evidence_reference is required")
    return blockers


def _pit_date_blockers(row: dict[str, Any]) -> list[str]:
    blockers = []
    signal_date = _parse_date(row.get("signal_date"))
    listed_date = _parse_date(row.get("listed_date"))
    delisted_date = _parse_date(row.get("delisted_date"))
    as_of_date = _parse_date(row.get("as_of_date"))
    available_time = _parse_datetime(row.get("available_time"))
    decision_time = pd.Timestamp(signal_date) + pd.Timedelta(hours=15, minutes=30) if signal_date is not None else None
    if signal_date is None:
        blockers.append("signal_date is invalid")
    if listed_date is not None and signal_date is not None and listed_date > signal_date:
        blockers.append("listed_date must be on or before signal_date")
    if delisted_date is not None and signal_date is not None and delisted_date < signal_date:
        blockers.append("delisted_date must be blank or on/after signal_date")
    if as_of_date is not None and signal_date is not None and as_of_date > signal_date:
        blockers.append("as_of_date must be on or before signal_date")
    if available_time is not None and decision_time is not None and available_time > decision_time:
        blockers.append("available_time must be on or before signal decision time")
    return blockers


def _mark_duplicate_export_ready_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if frame.empty:
        return frame, 0
    output = frame.copy()
    ready_mask = output["export_ready"].map(_is_true)
    duplicate_mask = output.loc[ready_mask, ["signal_date", "symbol", "universe_name"]].duplicated(keep=False)
    duplicate_indices = output.loc[ready_mask].index[duplicate_mask]
    if len(duplicate_indices) == 0:
        return output, 0
    for index in duplicate_indices:
        reason = _text(output.at[index, "export_blocker_reason"])
        duplicate_reason = "Duplicate export-ready key signal_date+symbol+universe_name"
        output.at[index, "export_ready"] = False
        output.at[index, "export_readiness_status"] = "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"
        output.at[index, "export_blocker_reason"] = (
            f"{reason}; {duplicate_reason}" if reason else duplicate_reason
        )
    return _finalize_readiness_frame(output), int(len(duplicate_indices))


def _build_counts(frame: pd.DataFrame) -> dict[str, int]:
    approved_count = int((frame["review_status"] == "APPROVED_FOR_PIT_UNIVERSE").sum()) if not frame.empty else 0
    export_ready_count = _true_count(frame, "export_ready")
    row_count = int(len(frame))
    return {
        "row_count": row_count,
        "approved_count": approved_count,
        "export_ready_count": export_ready_count,
        "blocked_count": row_count - export_ready_count,
        "missing_required_columns_count": int((frame["required_column_missing_count"].astype(int) > 0).sum()) if not frame.empty else 0,
        "unresolved_survivorship_warning_count": int(
            (frame["survivorship_bias_warning"].map(_is_true) & ~frame["survivorship_bias_resolved"].map(_is_true)).sum()
        )
        if not frame.empty
        else 0,
        "invalid_pit_date_count": int((frame["export_readiness_status"] == "EXPORT_BLOCKED_INVALID_PIT_DATES").sum())
        if not frame.empty
        else 0,
    }


def _aggregate_readiness_status(counts: dict[str, int]) -> str:
    if counts["approved_count"] == 0:
        return "EXPORT_BLOCKED_NO_APPROVED_ROWS"
    if counts["export_ready_count"] > 0 and counts["blocked_count"] == 0:
        return "EXPORT_READY_FOR_DRY_RUN"
    if counts["export_ready_count"] > 0:
        return "EXPORT_READY_REVIEW_ONLY"
    if counts["unresolved_survivorship_warning_count"] > 0:
        return "EXPORT_BLOCKED_UNRESOLVED_SURVIVORSHIP"
    if counts["invalid_pit_date_count"] > 0:
        return "EXPORT_BLOCKED_INVALID_PIT_DATES"
    if counts["missing_required_columns_count"] > 0:
        return "EXPORT_BLOCKED_MISSING_REQUIRED_COLUMNS"
    return "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE"


def _build_warnings(counts: dict[str, int], readiness_status: str) -> list[str]:
    warnings = []
    if readiness_status == "EXPORT_BLOCKED_NO_APPROVED_ROWS":
        warnings.append("No reviewed PIT universe rows are approved for export readiness.")
    if counts["export_ready_count"] == 0:
        warnings.append("No rows are export-ready; no universe export should be attempted.")
    if counts["unresolved_survivorship_warning_count"] > 0:
        warnings.append("Some rows still have unresolved survivorship-bias warnings.")
    if counts["missing_required_columns_count"] > 0:
        warnings.append("Some rows are missing required current-candidates universe columns.")
    return warnings


def _summary_dict(result: PitUniverseOverlayExportReadinessResult) -> dict[str, Any]:
    return {
        "export_readiness_id": result.export_readiness_id,
        "status": result.status,
        "readiness_status": result.readiness_status,
        "row_count": result.row_count,
        "approved_count": result.approved_count,
        "export_ready_count": result.export_ready_count,
        "blocked_count": result.blocked_count,
        "missing_required_columns_count": result.missing_required_columns_count,
        "unresolved_survivorship_warning_count": result.unresolved_survivorship_warning_count,
        "duplicate_key_count": result.duplicate_key_count,
        "review": str(result.request.review),
    }


def _audit_metadata(
    request: PitUniverseOverlayExportReadinessRequest,
    settings: PitUniverseOverlayExportReadinessSettings,
) -> dict[str, Any]:
    return {
        "review": str(request.review),
        "config_version": settings.config_version,
        "export_readiness_only": True,
        "universe_exported": False,
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "current_candidates_executed": False,
        "no_snapshot_built": True,
        "snapshot_manifest_built": False,
        "snapshot_manifests_built": False,
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


def _assert_settings_safe(settings: PitUniverseOverlayExportReadinessSettings) -> None:
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
        "enable_external_api": settings.enable_external_api,
        "enable_llm_api": settings.enable_llm_api,
    }
    enabled = [name for name, value in unsafe.items() if bool(value)]
    if enabled:
        raise ValueError(f"PIT universe overlay export readiness cannot enable unsafe behavior: {', '.join(enabled)}")


def _finalize_readiness_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in [
        "include_flag",
        "valid_for_signal_date",
        "export_ready",
        "survivorship_bias_warning",
        "survivorship_bias_resolved",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "export_readiness_only",
    ]:
        if column in output.columns:
            output[column] = output[column].astype(object)
    return output[READINESS_OUTPUT_COLUMNS]


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
