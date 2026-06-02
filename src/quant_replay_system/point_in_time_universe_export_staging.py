"""Guarded outputs-only staging for PIT universe export-ready rows."""

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


STAGING_STATUSES = {
    "EXPORT_STAGING_BLOCKED_NO_READY_ROWS",
    "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE",
    "EXPORT_STAGING_BLOCKED_READINESS_HEALTH",
    "EXPORT_STAGING_BLOCKED_DUPLICATES",
    "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS",
    "EXPORT_STAGING_READY_FOR_REVIEW",
    "EXPORT_STAGING_DRY_RUN_CREATED",
    "EXPORT_STAGING_FAILED",
}

STAGING_UNIVERSE_DETAIL_COLUMNS = [column for column in UNIVERSE_SNAPSHOT_SCHEMA if column != "symbol"]

STAGING_OUTPUT_COLUMNS = [
    "staging_id",
    "export_readiness_id",
    "review_id",
    "signal_date",
    "symbol",
    "universe_name",
    "export_ready",
    "staging_status",
    "staging_blocker_reason",
    *STAGING_UNIVERSE_DETAIL_COLUMNS,
    "reviewer",
    "reviewed_at",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "source_export_readiness_path",
    "source_is_diagnostic",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "staging_only",
]

SAFETY_STATEMENT = (
    "No data/raw write, data/processed write, current-candidates generation, snapshot build, "
    "forward labels, live trading, broker API, order placement, message delivery, network/API, "
    "LLM/API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitUniverseExportStagingSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_export_staging")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    allow_diagnostic_source: bool = False
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
class PitUniverseExportStagingRequest:
    export_readiness: Path


@dataclass(frozen=True)
class PitUniverseExportStagingRow:
    staging_id: str
    export_readiness_id: str
    review_id: str
    signal_date: str
    symbol: str
    universe_name: str
    export_ready: bool
    staging_status: str
    staging_blocker_reason: str
    as_of_date: str
    name: str
    instrument_type: str
    exchange: str
    listed_date: str
    delisted_date: str
    is_active: str
    is_st: str
    is_suspended: str
    industry: str
    min_lot: str
    t_plus_rule: str
    available_time: str
    revision_id: str
    source: str
    reviewer: str
    reviewed_at: str
    evidence_source: str
    evidence_path: str
    evidence_reference: str
    source_export_readiness_path: str
    source_is_diagnostic: bool
    no_data_raw_write: bool = True
    no_data_processed_write: bool = True
    no_current_candidates_generated: bool = True
    no_snapshot_built: bool = True
    no_forward_labels: bool = True
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    staging_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            column: getattr(self, column)
            for column in STAGING_OUTPUT_COLUMNS
        }


@dataclass(frozen=True)
class PitUniverseExportStagingArtifactPaths:
    artifact_dir: Path
    staging_csv: Path
    report: Path
    metadata: Path
    combined_preview_csv: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "staging_csv": self.staging_csv,
            "report": self.report,
            "metadata": self.metadata,
            "combined_preview_csv": self.combined_preview_csv,
        }


@dataclass(frozen=True)
class PitUniverseExportStagingResult:
    staging_id: str
    status: str
    staging_status: str
    request: PitUniverseExportStagingRequest
    row_count: int
    export_ready_input_count: int
    staged_row_count: int
    blocked_count: int
    source_is_diagnostic: bool
    no_ready_rows: bool
    duplicate_key_count: int
    missing_required_columns_count: int
    staging_frame: pd.DataFrame
    staged_universe_frame: pd.DataFrame
    per_signal_date_paths: dict[str, Path]
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_pit_universe_export_readiness_for_staging(
    export_readiness: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a PIT universe export-readiness CSV and sibling metadata."""

    readiness_path = Path(export_readiness)
    if not readiness_path.exists():
        raise FileNotFoundError(f"PIT universe export-readiness CSV not found: {readiness_path}")
    frame = read_csv_preserve_symbol_columns(readiness_path, keep_default_na=False)
    if "symbol" in frame.columns:
        frame["symbol"] = frame["symbol"].map(normalize_symbol_value)
    metadata_path = readiness_path.parent / "metadata.json"
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_export_readiness_path"] = str(readiness_path)
    return frame, metadata


def build_pit_universe_export_staging(
    *,
    export_readiness: str | Path,
    output_dir: str | Path | None = None,
    allow_diagnostic_source: bool | None = None,
    settings: PitUniverseExportStagingSettings | None = None,
) -> PitUniverseExportStagingResult:
    """Build guarded report/staging artifacts under outputs/reports only."""

    resolved_settings = settings or PitUniverseExportStagingSettings()
    if output_dir is not None or allow_diagnostic_source is not None:
        resolved_settings = PitUniverseExportStagingSettings(
            output_dir=Path(output_dir) if output_dir is not None else resolved_settings.output_dir,
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            allow_diagnostic_source=(
                bool(allow_diagnostic_source)
                if allow_diagnostic_source is not None
                else resolved_settings.allow_diagnostic_source
            ),
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

    request = PitUniverseExportStagingRequest(export_readiness=Path(export_readiness))
    readiness_frame, metadata = load_pit_universe_export_readiness_for_staging(request.export_readiness)
    review_frame = _load_source_review_frame(metadata)
    merged_frame = _merge_review_metadata(readiness_frame, review_frame)
    staging_id = generate_pit_universe_export_staging_id(request, merged_frame, resolved_settings)
    source_is_diagnostic = _is_diagnostic_path(request.export_readiness)
    global_blocker = _global_blocker(metadata, source_is_diagnostic, resolved_settings)
    rows = [
        evaluate_pit_universe_export_staging_row(
            row.to_dict(),
            staging_id=staging_id,
            source_export_readiness_path=str(request.export_readiness),
            source_is_diagnostic=source_is_diagnostic,
            global_blocker=global_blocker,
        ).as_dict()
        for _, row in merged_frame.iterrows()
    ]
    staging_frame = _finalize_staging_frame(pd.DataFrame(rows, columns=STAGING_OUTPUT_COLUMNS))
    staging_frame, duplicate_key_count = _mark_duplicate_staging_rows(staging_frame)
    counts = _build_counts(staging_frame)
    staging_status = _aggregate_staging_status(
        counts,
        source_is_diagnostic=source_is_diagnostic,
        global_blocker=global_blocker,
    )
    if global_blocker:
        staging_frame = _force_global_status(staging_frame, staging_status, global_blocker)
        counts = _build_counts(staging_frame)
    status = "PASS" if counts["staged_row_count"] > 0 else "WARN"
    paths = resolve_pit_universe_export_staging_paths(resolved_settings.output_dir, staging_id)
    staged_universe_frame = _staged_universe_frame(staging_frame)
    per_signal_paths = _per_signal_date_paths(paths.artifact_dir, staged_universe_frame)
    result = PitUniverseExportStagingResult(
        staging_id=staging_id,
        status=status,
        staging_status=staging_status,
        request=request,
        row_count=len(staging_frame),
        export_ready_input_count=counts["export_ready_input_count"],
        staged_row_count=counts["staged_row_count"],
        blocked_count=counts["blocked_count"],
        source_is_diagnostic=source_is_diagnostic,
        no_ready_rows=counts["export_ready_input_count"] == 0,
        duplicate_key_count=duplicate_key_count,
        missing_required_columns_count=counts["missing_required_columns_count"],
        staging_frame=staging_frame,
        staged_universe_frame=staged_universe_frame,
        per_signal_date_paths=per_signal_paths,
        warnings=_build_warnings(staging_status, counts, source_is_diagnostic),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, metadata, resolved_settings, source_is_diagnostic),
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_export_staging_artifacts(result)
    return result


def evaluate_pit_universe_export_staging_row(
    row: dict[str, Any],
    *,
    staging_id: str,
    source_export_readiness_path: str,
    source_is_diagnostic: bool,
    global_blocker: str = "",
) -> PitUniverseExportStagingRow:
    """Evaluate one readiness row for outputs-only staging."""

    blockers: list[str] = []
    export_ready = _is_true(row.get("export_ready"))
    status = "EXPORT_STAGING_DRY_RUN_CREATED"
    if global_blocker:
        blockers.append(global_blocker)
        status = _status_for_global_blocker(global_blocker)
    elif not export_ready:
        blockers.append("row is not export_ready=true")
        status = "EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    else:
        missing = _missing_universe_columns(row)
        if missing:
            blockers.append(f"missing required universe columns: {', '.join(missing)}")
            status = "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS"
        date_blockers = _pit_date_blockers(row)
        if date_blockers:
            blockers.extend(date_blockers)
            status = "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS"
    return PitUniverseExportStagingRow(
        staging_id=staging_id,
        export_readiness_id=_text(row.get("export_readiness_id")),
        review_id=_text(row.get("review_id")),
        signal_date=_date_text(row.get("signal_date")),
        symbol=normalize_symbol_value(row.get("symbol")),
        universe_name=_text(row.get("universe_name")),
        export_ready=export_ready,
        staging_status=status,
        staging_blocker_reason="; ".join(blockers),
        as_of_date=_date_text(row.get("as_of_date")),
        name=_text(row.get("name")),
        instrument_type=_text(row.get("instrument_type")),
        exchange=_text(row.get("exchange")),
        listed_date=_date_text(row.get("listed_date")),
        delisted_date=_date_text(row.get("delisted_date")),
        is_active=_text(row.get("is_active")),
        is_st=_text(row.get("is_st")),
        is_suspended=_text(row.get("is_suspended")),
        industry=_text(row.get("industry")),
        min_lot=_text(row.get("min_lot")),
        t_plus_rule=_text(row.get("t_plus_rule")),
        available_time=_datetime_text(row.get("available_time")),
        revision_id=_text(row.get("revision_id")),
        source=_text(row.get("source")),
        reviewer=_text(row.get("reviewer")),
        reviewed_at=_text(row.get("reviewed_at")),
        evidence_source=_text(row.get("evidence_source")),
        evidence_path=_text(row.get("evidence_path")),
        evidence_reference=_text(row.get("evidence_reference")),
        source_export_readiness_path=source_export_readiness_path,
        source_is_diagnostic=source_is_diagnostic,
    )


def write_pit_universe_export_staging_artifacts(
    result: PitUniverseExportStagingResult,
) -> dict[str, Path]:
    """Write staging artifacts under outputs/reports only."""

    paths = PitUniverseExportStagingArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.staging_frame.to_csv(paths.staging_csv, index=False)
    result.staged_universe_frame.to_csv(paths.combined_preview_csv, index=False)
    for signal_date, path in result.per_signal_date_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        date_frame = result.staged_universe_frame.loc[
            result.staged_universe_frame["as_of_date"].astype(str) == str(signal_date)
        ].copy()
        date_frame.to_csv(path, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_pit_universe_export_staging_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_pit_universe_export_staging_report(result), encoding="utf-8")
    return paths.as_dict()


def render_pit_universe_export_staging_report(result: PitUniverseExportStagingResult) -> str:
    lines = [
        f"# PIT Universe Export Staging: {result.staging_id}",
        "",
        SAFETY_STATEMENT,
        "This is staging-only. Preview CSVs stay under outputs/reports and are not accepted universe files.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Staging Rows",
        "",
        _markdown_table(result.staging_frame, STAGING_OUTPUT_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_pit_universe_export_staging_metadata(result: PitUniverseExportStagingResult) -> dict[str, Any]:
    return {
        "staging_id": result.staging_id,
        "status": result.status,
        "staging_status": result.staging_status,
        "created_at": "2024-05-30T00:00:00",
        "export_readiness": str(result.request.export_readiness),
        "export_readiness_id": _first_value(result.staging_frame, "export_readiness_id"),
        "review_id": _first_value(result.staging_frame, "review_id"),
        "row_count": result.row_count,
        "export_ready_input_count": result.export_ready_input_count,
        "staged_row_count": result.staged_row_count,
        "blocked_count": result.blocked_count,
        "source_is_diagnostic": result.source_is_diagnostic,
        "no_ready_rows": result.no_ready_rows,
        "duplicate_key_count": result.duplicate_key_count,
        "missing_required_columns_count": result.missing_required_columns_count,
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        "per_signal_date_preview_paths": {
            signal_date: str(path)
            for signal_date, path in result.per_signal_date_paths.items()
        },
        **result.audit_metadata,
        "known_limitations": [
            "This workflow creates reviewable staging previews only.",
            "Staging previews are not accepted local universe inputs.",
            "A later explicit accept/export workflow is required before data/raw can be written.",
            "Staging does not validate strategy performance or authorize trading.",
        ],
    }


def generate_pit_universe_export_staging_id(
    request: PitUniverseExportStagingRequest,
    frame: pd.DataFrame,
    settings: PitUniverseExportStagingSettings,
) -> str:
    payload = {
        "export_readiness": str(request.export_readiness),
        "config_version": settings.config_version,
        "allow_diagnostic_source": settings.allow_diagnostic_source,
        "rows": frame[
            [column for column in ["export_readiness_id", "review_id", "signal_date", "symbol", "universe_name", "export_ready"] if column in frame]
        ].to_dict("records"),
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_pit_universe_export_staging_paths(
    output_dir: str | Path,
    staging_id: str,
) -> PitUniverseExportStagingArtifactPaths:
    artifact_dir = Path(output_dir) / staging_id
    return PitUniverseExportStagingArtifactPaths(
        artifact_dir=artifact_dir,
        staging_csv=artifact_dir / "pit_universe_export_staging.csv",
        report=artifact_dir / "pit_universe_export_staging_report.md",
        metadata=artifact_dir / "metadata.json",
        combined_preview_csv=artifact_dir / "staged_universe_combined_preview.csv",
    )


def _load_source_review_frame(metadata: dict[str, Any]) -> pd.DataFrame:
    review_path = _text(metadata.get("review"))
    if not review_path:
        return pd.DataFrame()
    path = Path(review_path)
    if not path.exists():
        return pd.DataFrame()
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    if "symbol" in frame.columns:
        frame["symbol"] = frame["symbol"].map(normalize_symbol_value)
    return frame


def _merge_review_metadata(readiness_frame: pd.DataFrame, review_frame: pd.DataFrame) -> pd.DataFrame:
    output = readiness_frame.copy(deep=True)
    for column in STAGING_OUTPUT_COLUMNS:
        if column not in output.columns and column not in {"staging_id", "staging_status", "staging_blocker_reason", "source_export_readiness_path", "source_is_diagnostic"}:
            output[column] = ""
    if review_frame.empty:
        return output
    keys = ["review_id", "signal_date", "symbol", "universe_name"]
    for key in keys:
        if key not in review_frame.columns or key not in output.columns:
            return output
    review_columns = [
        column
        for column in [
            *UNIVERSE_SNAPSHOT_SCHEMA,
            "reviewer",
            "reviewed_at",
            "evidence_source",
            "evidence_path",
            "evidence_reference",
        ]
        if column in review_frame.columns and column not in keys
    ]
    review_subset = review_frame[[*keys, *review_columns]].copy()
    merged = output.merge(review_subset, on=keys, how="left", suffixes=("", "_review"))
    for column in review_columns:
        review_column = f"{column}_review"
        if review_column in merged.columns:
            merged[column] = merged[review_column].where(merged[review_column].astype(str) != "", merged.get(column, ""))
            merged = merged.drop(columns=[review_column])
    return merged


def _global_blocker(
    metadata: dict[str, Any],
    source_is_diagnostic: bool,
    settings: PitUniverseExportStagingSettings,
) -> str:
    if source_is_diagnostic and not settings.allow_diagnostic_source:
        return "diagnostic export-readiness sources are blocked from active staging"
    unsafe = []
    for key, expected in {
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
    }.items():
        if key in metadata and bool(metadata.get(key)) is not expected:
            unsafe.append(key)
    if unsafe:
        return "readiness metadata has unsafe or non-staging-safe fields: " + ", ".join(unsafe)
    if _text(metadata.get("status")).upper() == "FAIL":
        return "readiness artifact status is FAIL"
    return ""


def _status_for_global_blocker(blocker: str) -> str:
    if "diagnostic" in blocker:
        return "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE"
    if "status is FAIL" in blocker or "unsafe" in blocker:
        return "EXPORT_STAGING_BLOCKED_READINESS_HEALTH"
    return "EXPORT_STAGING_FAILED"


def _mark_duplicate_staging_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if frame.empty:
        return frame, 0
    output = frame.copy()
    staged_mask = output["staging_status"].astype(str) == "EXPORT_STAGING_DRY_RUN_CREATED"
    duplicate_mask = output.loc[staged_mask, ["signal_date", "symbol", "universe_name"]].duplicated(keep=False)
    duplicate_indices = output.loc[staged_mask].index[duplicate_mask]
    for index in duplicate_indices:
        reason = _text(output.at[index, "staging_blocker_reason"])
        duplicate_reason = "Duplicate staging key signal_date+symbol+universe_name"
        output.at[index, "staging_status"] = "EXPORT_STAGING_BLOCKED_DUPLICATES"
        output.at[index, "staging_blocker_reason"] = f"{reason}; {duplicate_reason}" if reason else duplicate_reason
    return _finalize_staging_frame(output), int(len(duplicate_indices))


def _build_counts(frame: pd.DataFrame) -> dict[str, int]:
    staged_count = int((frame["staging_status"] == "EXPORT_STAGING_DRY_RUN_CREATED").sum()) if not frame.empty else 0
    export_ready_input_count = _true_count(frame, "export_ready")
    return {
        "row_count": int(len(frame)),
        "export_ready_input_count": export_ready_input_count,
        "staged_row_count": staged_count,
        "blocked_count": int(len(frame)) - staged_count,
        "missing_required_columns_count": int(
            (frame["staging_status"] == "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS").sum()
        )
        if not frame.empty
        else 0,
    }


def _aggregate_staging_status(
    counts: dict[str, int],
    *,
    source_is_diagnostic: bool,
    global_blocker: str,
) -> str:
    if global_blocker:
        return _status_for_global_blocker(global_blocker)
    if counts["export_ready_input_count"] == 0:
        return "EXPORT_STAGING_BLOCKED_NO_READY_ROWS"
    if counts["staged_row_count"] > 0:
        return "EXPORT_STAGING_DRY_RUN_CREATED"
    if counts["missing_required_columns_count"] > 0:
        return "EXPORT_STAGING_BLOCKED_MISSING_COLUMNS"
    if source_is_diagnostic:
        return "EXPORT_STAGING_READY_FOR_REVIEW"
    return "EXPORT_STAGING_FAILED"


def _force_global_status(frame: pd.DataFrame, status: str, blocker: str) -> pd.DataFrame:
    output = frame.copy()
    if output.empty:
        return output
    output["staging_status"] = status
    output["staging_blocker_reason"] = blocker
    return _finalize_staging_frame(output)


def _staged_universe_frame(staging_frame: pd.DataFrame) -> pd.DataFrame:
    if staging_frame.empty:
        return pd.DataFrame(columns=UNIVERSE_SNAPSHOT_SCHEMA)
    staged = staging_frame.loc[staging_frame["staging_status"] == "EXPORT_STAGING_DRY_RUN_CREATED"].copy()
    if staged.empty:
        return pd.DataFrame(columns=UNIVERSE_SNAPSHOT_SCHEMA)
    return staged[UNIVERSE_SNAPSHOT_SCHEMA].copy()


def _per_signal_date_paths(artifact_dir: Path, staged_frame: pd.DataFrame) -> dict[str, Path]:
    if staged_frame.empty or "as_of_date" not in staged_frame.columns:
        return {}
    signal_dates = sorted({str(value) for value in staged_frame["as_of_date"].tolist() if str(value)})
    return {
        signal_date: artifact_dir / f"staged_universe_{signal_date}_preview.csv"
        for signal_date in signal_dates
    }


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


def _pit_date_blockers(row: dict[str, Any]) -> list[str]:
    blockers = []
    signal_date = _parse_date(row.get("signal_date"))
    listed_date = _parse_date(row.get("listed_date"))
    delisted_date = _parse_date(row.get("delisted_date"))
    as_of_date = _parse_date(row.get("as_of_date"))
    available_time = _parse_datetime(row.get("available_time"))
    decision_time = pd.Timestamp(signal_date) + pd.Timedelta(hours=15, minutes=30) if signal_date is not None else None
    if as_of_date is not None and signal_date is not None and as_of_date > signal_date:
        blockers.append("as_of_date must be on or before signal_date")
    if listed_date is not None and signal_date is not None and listed_date > signal_date:
        blockers.append("listed_date must be on or before signal_date")
    if delisted_date is not None and signal_date is not None and delisted_date < signal_date:
        blockers.append("delisted_date must be blank or on/after signal_date")
    if available_time is not None and decision_time is not None and available_time > decision_time:
        blockers.append("available_time must be on or before signal decision time")
    return blockers


def _build_warnings(status: str, counts: dict[str, int], source_is_diagnostic: bool) -> list[str]:
    warnings: list[str] = []
    if status == "EXPORT_STAGING_BLOCKED_NO_READY_ROWS":
        warnings.append("No export_ready rows were available for staging.")
    if status == "EXPORT_STAGING_BLOCKED_DIAGNOSTIC_SOURCE":
        warnings.append("Diagnostic export-readiness sources are blocked from active staging.")
    if counts["staged_row_count"] > 0:
        warnings.append("Staging previews were created under outputs/reports only and are not accepted universe files.")
    if source_is_diagnostic:
        warnings.append("Source path is diagnostic/manual_diagnostics scope.")
    return warnings


def _summary_dict(result: PitUniverseExportStagingResult) -> dict[str, Any]:
    return {
        "staging_id": result.staging_id,
        "status": result.status,
        "staging_status": result.staging_status,
        "row_count": result.row_count,
        "export_ready_input_count": result.export_ready_input_count,
        "staged_row_count": result.staged_row_count,
        "blocked_count": result.blocked_count,
        "source_is_diagnostic": result.source_is_diagnostic,
        "no_ready_rows": result.no_ready_rows,
        "duplicate_key_count": result.duplicate_key_count,
        "missing_required_columns_count": result.missing_required_columns_count,
        "export_readiness": result.request.export_readiness,
    }


def _audit_metadata(
    request: PitUniverseExportStagingRequest,
    source_metadata: dict[str, Any],
    settings: PitUniverseExportStagingSettings,
    source_is_diagnostic: bool,
) -> dict[str, Any]:
    return {
        "export_readiness": str(request.export_readiness),
        "source_metadata_status": _text(source_metadata.get("status")),
        "source_readiness_status": _text(source_metadata.get("readiness_status")),
        "config_version": settings.config_version,
        "allow_diagnostic_source": settings.allow_diagnostic_source,
        "source_is_diagnostic": source_is_diagnostic,
        "active_staging_allowed": not source_is_diagnostic,
        "staging_only": True,
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
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
        "no_live_trading": True,
        "live_trading_enabled": False,
        "no_broker_api": True,
        "broker_api_invoked": False,
        "no_order_placement": True,
        "order_placement_enabled": False,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
    }


def _assert_settings_safe(settings: PitUniverseExportStagingSettings) -> None:
    unsafe = {
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
        raise ValueError(f"PIT universe export staging cannot enable unsafe behavior: {', '.join(enabled)}")


def _is_diagnostic_path(path: str | Path) -> bool:
    text = str(path).replace("\\", "/").lower()
    return "/manual_diagnostics/" in text or text.startswith("outputs/reports/manual_diagnostics/")


def _finalize_staging_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in STAGING_OUTPUT_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for column in [
        "export_ready",
        "source_is_diagnostic",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "staging_only",
    ]:
        output[column] = output[column].map(_is_true).astype(object)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output[STAGING_OUTPUT_COLUMNS]


def _first_value(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    return _text(frame.iloc[0].get(column))


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
