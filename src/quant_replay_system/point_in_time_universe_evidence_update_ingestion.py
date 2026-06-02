"""Report-only ingestion validation for PIT universe evidence updates.

This module validates reviewer-completed PIT universe evidence update CSVs and
writes report artifacts under outputs/reports only. It does not apply approvals,
export universe files, build snapshots, run current-candidates, compute labels,
mutate cache, or perform trading workflows.
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
from quant_replay_system.point_in_time_universe_evidence_review_worklist import (
    WORKLIST_OUTPUT_COLUMNS,
)
from quant_replay_system.point_in_time_universe_overlay_review import (
    REVIEW_STATUSES,
    REVIEW_UPDATE_COLUMNS,
)


IDENTITY_COLUMNS = ["signal_date", "symbol", "universe_name"]
REQUIRED_COMPLETED_UPDATE_COLUMNS = [*IDENTITY_COLUMNS, "review_status"]
COMPLETED_UPDATE_COLUMNS = [
    "signal_date",
    "symbol",
    "universe_name",
    "review_status",
    "include_flag",
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
]
REQUIRED_APPROVAL_EVIDENCE_COLUMNS = [
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "listed_date_evidence",
    "is_active_evidence",
]
REQUIRED_APPROVAL_UNIVERSE_COLUMNS = [
    "as_of_date",
    "name",
    "instrument_type",
    "exchange",
    "listed_date",
    "is_active",
    "is_st",
    "is_suspended",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
]
SUGGESTED_FIELD_PAIRS = [
    ("name", "suggested_name"),
    ("instrument_type", "suggested_instrument_type"),
    ("exchange", "suggested_exchange"),
    ("industry", "suggested_industry"),
    ("min_lot", "suggested_min_lot"),
    ("t_plus_rule", "suggested_t_plus_rule"),
    ("is_active", "suggested_is_active"),
    ("is_st", "suggested_is_st"),
    ("is_suspended", "suggested_is_suspended"),
    ("source", "suggested_source"),
    ("revision_id", "suggested_revision_id"),
    ("available_time", "suggested_available_time"),
]

INGESTION_OUTPUT_COLUMNS = [
    "ingestion_id",
    "signal_date",
    "symbol",
    "universe_name",
    "input_review_status",
    "normalized_review_status",
    "include_flag",
    "ingestion_status",
    "ingestion_blocker_reason",
    "ready_for_review_update",
    "approval_requested",
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
    "suggested_copy_risk",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "ingestion_only",
]

SAFETY_STATEMENT = (
    "No approval was applied, no universe export, data/raw write, data/processed write, "
    "current-candidates generation, snapshot build, forward labels, live trading, broker API, "
    "order placement, message delivery, network/API, LLM/API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_evidence_update_ingestion")
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
class PitUniverseEvidenceUpdateIngestionRequest:
    completed_updates: Path
    worklist: Path | None


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionRow:
    values: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {column: self.values.get(column, "") for column in INGESTION_OUTPUT_COLUMNS}


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionArtifactPaths:
    artifact_dir: Path
    ingestion_csv: Path
    review_updates: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "ingestion_csv": self.ingestion_csv,
            "review_updates": self.review_updates,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceUpdateIngestionResult:
    ingestion_id: str
    status: str
    request: PitUniverseEvidenceUpdateIngestionRequest
    row_count: int
    ready_for_review_update_count: int
    blocked_count: int
    approval_requested_count: int
    approved_ready_count: int
    rejected_ready_count: int
    needs_more_evidence_ready_count: int
    duplicate_identity_count: int
    missing_identity_count: int
    suggested_copy_risk_count: int
    ingestion_frame: pd.DataFrame
    review_updates_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_completed_pit_universe_evidence_updates(path: str | Path) -> pd.DataFrame:
    update_path = Path(path)
    if not update_path.exists():
        raise FileNotFoundError(f"PIT universe completed update CSV not found: {update_path}")
    frame = read_csv_preserve_symbol_columns(update_path, keep_default_na=False)
    missing = [column for column in REQUIRED_COMPLETED_UPDATE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"PIT universe completed updates missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    for column in COMPLETED_UPDATE_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output[COMPLETED_UPDATE_COLUMNS].copy()


def load_pit_universe_worklist_for_update_ingestion(path: str | Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=WORKLIST_OUTPUT_COLUMNS)
    worklist_path = Path(path)
    if not worklist_path.exists():
        raise FileNotFoundError(f"PIT universe evidence worklist CSV not found: {worklist_path}")
    frame = read_csv_preserve_symbol_columns(worklist_path, keep_default_na=False)
    missing = [column for column in IDENTITY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"PIT universe evidence worklist missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    for column in WORKLIST_OUTPUT_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    for _, suggested in SUGGESTED_FIELD_PAIRS:
        if suggested not in output.columns:
            output[suggested] = ""
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output


def build_pit_universe_evidence_update_ingestion(
    *,
    completed_updates: str | Path,
    worklist: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: PitUniverseEvidenceUpdateIngestionSettings | None = None,
) -> PitUniverseEvidenceUpdateIngestionResult:
    resolved_settings = settings or PitUniverseEvidenceUpdateIngestionSettings()
    if output_dir is not None:
        resolved_settings = PitUniverseEvidenceUpdateIngestionSettings(
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

    request = PitUniverseEvidenceUpdateIngestionRequest(
        completed_updates=Path(completed_updates),
        worklist=Path(worklist) if worklist else None,
    )
    updates_frame = load_completed_pit_universe_evidence_updates(request.completed_updates)
    worklist_frame = load_pit_universe_worklist_for_update_ingestion(request.worklist)
    duplicate_mask = _identity_duplicate_mask(updates_frame)
    worklist_map = {_row_key(row): row for row in worklist_frame.to_dict("records")}
    ingestion_id = generate_pit_universe_evidence_update_ingestion_id(request, updates_frame, resolved_settings)
    rows = [
        validate_pit_universe_evidence_update_row(
            row.to_dict(),
            ingestion_id=ingestion_id,
            duplicate_identity=bool(duplicate_mask.iloc[position]) if len(duplicate_mask) else False,
            worklist_row=worklist_map.get(_row_key(row.to_dict()), {}),
            require_worklist_match=not worklist_frame.empty,
        ).as_dict()
        for position, row in updates_frame.iterrows()
    ]
    ingestion_frame = _finalize_ingestion_frame(pd.DataFrame(rows, columns=INGESTION_OUTPUT_COLUMNS))
    review_updates_frame = _clean_review_updates_frame(ingestion_frame)
    counts = _build_counts(ingestion_frame)
    status = "PASS" if counts["ready_for_review_update_count"] > 0 and counts["blocked_count"] == 0 else "WARN"
    paths = resolve_pit_universe_evidence_update_ingestion_paths(
        resolved_settings.output_dir,
        ingestion_id,
    )
    result = PitUniverseEvidenceUpdateIngestionResult(
        ingestion_id=ingestion_id,
        status=status,
        request=request,
        row_count=counts["row_count"],
        ready_for_review_update_count=counts["ready_for_review_update_count"],
        blocked_count=counts["blocked_count"],
        approval_requested_count=counts["approval_requested_count"],
        approved_ready_count=counts["approved_ready_count"],
        rejected_ready_count=counts["rejected_ready_count"],
        needs_more_evidence_ready_count=counts["needs_more_evidence_ready_count"],
        duplicate_identity_count=counts["duplicate_identity_count"],
        missing_identity_count=counts["missing_identity_count"],
        suggested_copy_risk_count=counts["suggested_copy_risk_count"],
        ingestion_frame=ingestion_frame,
        review_updates_frame=review_updates_frame,
        warnings=_build_warnings(counts),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_evidence_update_ingestion_artifacts(result)
    return result


def validate_pit_universe_evidence_update_row(
    row: dict[str, Any],
    *,
    ingestion_id: str,
    duplicate_identity: bool = False,
    worklist_row: dict[str, Any] | None = None,
    require_worklist_match: bool = False,
) -> PitUniverseEvidenceUpdateIngestionRow:
    blockers: list[str] = []
    status = "UPDATE_READY_FOR_REVIEW_APPLY"
    input_status = _text(row.get("review_status"))
    normalized_status = input_status.upper()
    approval_requested = normalized_status == "APPROVED_FOR_PIT_UNIVERSE"
    missing_identity = [column for column in IDENTITY_COLUMNS if not _present(row.get(column))]
    suggested_copy_risk = _suggested_copy_risk(row, worklist_row or {})

    if missing_identity:
        status = "UPDATE_BLOCKED_MISSING_IDENTITY"
        blockers.append(f"missing identity fields: {', '.join(missing_identity)}")
    elif duplicate_identity:
        status = "UPDATE_BLOCKED_DUPLICATE_IDENTITY"
        blockers.append("duplicate signal_date+symbol+universe_name")
    elif require_worklist_match and not worklist_row:
        status = "UPDATE_BLOCKED_MISSING_IDENTITY"
        blockers.append("identity key not found in supplied worklist")
    elif normalized_status not in REVIEW_STATUSES:
        status = "UPDATE_BLOCKED_INVALID_STATUS"
        blockers.append("invalid review_status")
    elif approval_requested:
        status, blockers = _approval_status_and_blockers(row, suggested_copy_risk)
    elif normalized_status == "REJECTED":
        status, blockers = _rejected_status_and_blockers(row)
    elif normalized_status == "NEEDS_MORE_EVIDENCE":
        status, blockers = _needs_more_evidence_status_and_blockers(row)
    elif normalized_status == "NEEDS_MANUAL_REVIEW":
        status = "UPDATE_BLOCKED_INVALID_STATUS"
        blockers.append("NEEDS_MANUAL_REVIEW row is not a clean review update")

    ready = status == "UPDATE_READY_FOR_REVIEW_APPLY"
    values = {
        "ingestion_id": ingestion_id,
        "signal_date": _date_text(row.get("signal_date")),
        "symbol": normalize_symbol_value(row.get("symbol")),
        "universe_name": _text(row.get("universe_name")),
        "input_review_status": input_status,
        "normalized_review_status": normalized_status,
        "include_flag": _is_true(row.get("include_flag")),
        "ingestion_status": status,
        "ingestion_blocker_reason": "; ".join(blockers),
        "ready_for_review_update": ready,
        "approval_requested": approval_requested,
        "suggested_copy_risk": suggested_copy_risk,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "ingestion_only": True,
    }
    for column in COMPLETED_UPDATE_COLUMNS:
        if column not in {"signal_date", "symbol", "universe_name", "review_status", "include_flag"}:
            values[column] = _text(row.get(column))
    return PitUniverseEvidenceUpdateIngestionRow(values)


def write_pit_universe_evidence_update_ingestion_artifacts(
    result: PitUniverseEvidenceUpdateIngestionResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceUpdateIngestionArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.ingestion_frame.to_csv(paths.ingestion_csv, index=False)
    result.review_updates_frame.to_csv(paths.review_updates, index=False)
    paths.report.write_text(render_pit_universe_evidence_update_ingestion_report(result), encoding="utf-8")
    paths.metadata.write_text(
        json.dumps(_json_safe(build_pit_universe_evidence_update_ingestion_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_pit_universe_evidence_update_ingestion_report(
    result: PitUniverseEvidenceUpdateIngestionResult,
) -> str:
    status_counts = result.ingestion_frame["ingestion_status"].value_counts().to_dict()
    lines = [
        f"# PIT Universe Evidence Update Ingestion: {result.ingestion_id}",
        "",
        SAFETY_STATEMENT,
        "This is an ingestion-validation artifact only. It does not apply approvals or rerun overlay review.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Status Counts",
        "",
        _dict_table(status_counts),
        "",
        "## Clean Review Updates",
        "",
        f"Rows written for later manual pit-universe-overlay-review use: {len(result.review_updates_frame)}",
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_pit_universe_evidence_update_ingestion_metadata(
    result: PitUniverseEvidenceUpdateIngestionResult,
) -> dict[str, Any]:
    return {
        **_summary_dict(result),
        "completed_updates": str(result.request.completed_updates),
        "worklist": str(result.request.worklist) if result.request.worklist else "",
        "config_version": "v0.1",
        "approval_applied": False,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "cache_mutated": False,
        "network_api_called": False,
        "llm_api_called": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "ingestion_only": True,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
    }


def resolve_pit_universe_evidence_update_ingestion_paths(
    output_dir: str | Path,
    ingestion_id: str,
) -> PitUniverseEvidenceUpdateIngestionArtifactPaths:
    artifact_dir = Path(output_dir) / ingestion_id
    return PitUniverseEvidenceUpdateIngestionArtifactPaths(
        artifact_dir=artifact_dir,
        ingestion_csv=artifact_dir / "pit_universe_evidence_update_ingestion.csv",
        review_updates=artifact_dir / "pit_universe_review_updates.csv",
        report=artifact_dir / "pit_universe_evidence_update_ingestion_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def generate_pit_universe_evidence_update_ingestion_id(
    request: PitUniverseEvidenceUpdateIngestionRequest,
    frame: pd.DataFrame,
    settings: PitUniverseEvidenceUpdateIngestionSettings,
) -> str:
    payload = {
        "completed_updates": str(request.completed_updates),
        "worklist": str(request.worklist) if request.worklist else "",
        "rows": frame.astype(str).to_dict("records"),
        "config_version": settings.config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _approval_status_and_blockers(row: dict[str, Any], suggested_copy_risk: bool) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if suggested_copy_risk:
        blockers.append("authoritative fields appear copied from non-authoritative suggested_* hints without evidence support")
        return "UPDATE_BLOCKED_SUGGESTED_HINT_COPY_RISK", blockers

    if not _present(row.get("reviewer")):
        blockers.append("missing reviewer")
        return "UPDATE_BLOCKED_MISSING_REVIEWER", blockers

    evidence_missing = [column for column in REQUIRED_APPROVAL_EVIDENCE_COLUMNS if not _present(row.get(column))]
    if not (_present(row.get("evidence_path")) or _present(row.get("evidence_reference"))):
        evidence_missing.append("evidence_path or evidence_reference")
    if not _is_true(row.get("include_flag")):
        evidence_missing.append("include_flag=true")
    if evidence_missing:
        blockers.append(f"missing approval evidence: {', '.join(evidence_missing)}")
        return "UPDATE_BLOCKED_MISSING_EVIDENCE", blockers

    if not _is_true(row.get("survivorship_bias_resolved")):
        blockers.append("survivorship_bias_resolved must be true")
        return "UPDATE_BLOCKED_UNRESOLVED_SURVIVORSHIP", blockers

    missing_metadata = [column for column in REQUIRED_APPROVAL_UNIVERSE_COLUMNS if not _present(row.get(column))]
    if missing_metadata:
        blockers.append(f"missing required universe metadata: {', '.join(missing_metadata)}")
        return "UPDATE_BLOCKED_MISSING_UNIVERSE_METADATA", blockers

    date_blockers = _pit_date_blockers(row)
    if date_blockers:
        return "UPDATE_BLOCKED_INVALID_PIT_DATES", date_blockers
    return "UPDATE_READY_FOR_REVIEW_APPLY", []


def _rejected_status_and_blockers(row: dict[str, Any]) -> tuple[str, list[str]]:
    missing = [column for column in ["reviewer", "reviewed_at", "review_reason"] if not _present(row.get(column))]
    if "reviewer" in missing:
        return "UPDATE_BLOCKED_MISSING_REVIEWER", ["missing reviewer"]
    if missing:
        return "UPDATE_BLOCKED_MISSING_EVIDENCE", [f"missing rejected-row review fields: {', '.join(missing)}"]
    return "UPDATE_READY_FOR_REVIEW_APPLY", []


def _needs_more_evidence_status_and_blockers(row: dict[str, Any]) -> tuple[str, list[str]]:
    reviewer_supplied = _present(row.get("reviewer")) or _present(row.get("reviewed_at"))
    if reviewer_supplied and not _present(row.get("review_reason")):
        return "UPDATE_BLOCKED_MISSING_EVIDENCE", ["missing review_reason for NEEDS_MORE_EVIDENCE row"]
    if not reviewer_supplied and not _present(row.get("review_reason")):
        return "UPDATE_BLOCKED_MISSING_EVIDENCE", ["missing review_reason for NEEDS_MORE_EVIDENCE row"]
    return "UPDATE_READY_FOR_REVIEW_APPLY", []


def _pit_date_blockers(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    signal_date = _parse_date(row.get("signal_date"))
    listed_date = _parse_date(row.get("listed_date"))
    listed_evidence = _parse_date(row.get("listed_date_evidence"))
    delisted_date = _parse_date(row.get("delisted_date"))
    delisted_evidence = _parse_date(row.get("delisted_date_evidence"))
    as_of_date = _parse_date(row.get("as_of_date"))
    available_time = _parse_datetime(row.get("available_time"))
    decision_time = pd.Timestamp(signal_date) + pd.Timedelta(hours=15, minutes=30) if signal_date is not None else None
    if signal_date is None:
        blockers.append("invalid signal_date")
    if listed_date is not None and signal_date is not None and listed_date > signal_date:
        blockers.append("listed_date must be on or before signal_date")
    if listed_evidence is not None and signal_date is not None and listed_evidence > signal_date:
        blockers.append("listed_date_evidence must be on or before signal_date")
    if delisted_date is not None and signal_date is not None and delisted_date < signal_date:
        blockers.append("delisted_date must be blank or on/after signal_date")
    if delisted_evidence is not None and signal_date is not None and delisted_evidence < signal_date:
        blockers.append("delisted_date_evidence must be blank or on/after signal_date")
    if as_of_date is not None and signal_date is not None and as_of_date > signal_date:
        blockers.append("as_of_date must be on or before signal_date")
    if available_time is None:
        blockers.append("invalid available_time")
    elif decision_time is not None and available_time > decision_time:
        blockers.append("available_time must be on or before signal decision time")
    return blockers


def _suggested_copy_risk(row: dict[str, Any], worklist_row: dict[str, Any]) -> bool:
    if not worklist_row:
        return False
    if _text(row.get("review_status")).upper() != "APPROVED_FOR_PIT_UNIVERSE":
        return False
    copied = [
        field
        for field, suggested in SUGGESTED_FIELD_PAIRS
        if _present(row.get(field))
        and _present(worklist_row.get(suggested))
        and _text(row.get(field)).lower() == _text(worklist_row.get(suggested)).lower()
    ]
    if not copied:
        return False
    has_review_evidence = (
        _present(row.get("review_reason"))
        and _present(row.get("evidence_source"))
        and (_present(row.get("evidence_path")) or _present(row.get("evidence_reference")))
    )
    return not has_review_evidence


def _identity_duplicate_mask(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=bool)
    keys = frame[IDENTITY_COLUMNS].astype(str).agg("|".join, axis=1)
    return keys.duplicated(keep=False)


def _clean_review_updates_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=REVIEW_UPDATE_COLUMNS)
    ready = frame[frame["ready_for_review_update"].map(_is_true)].copy()
    rows = []
    for row in ready.to_dict("records"):
        clean_row = {column: row.get(column, "") for column in REVIEW_UPDATE_COLUMNS}
        clean_row["review_status"] = row.get("normalized_review_status", "")
        rows.append(clean_row)
    return pd.DataFrame(rows, columns=REVIEW_UPDATE_COLUMNS)


def _finalize_ingestion_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INGESTION_OUTPUT_COLUMNS)
    output = frame.copy(deep=True)
    for column in ["signal_date", "listed_date", "delisted_date", "listed_date_evidence", "delisted_date_evidence", "as_of_date"]:
        if column in output.columns:
            output[column] = output[column].map(_date_text)
    if "available_time" in output.columns:
        output["available_time"] = output["available_time"].map(_datetime_text)
    for column in _bool_columns():
        if column in output.columns:
            output[column] = output[column].map(_is_true).astype(object)
    if "symbol" in output.columns:
        output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output[INGESTION_OUTPUT_COLUMNS].reset_index(drop=True)


def _build_counts(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "row_count": int(len(frame)),
        "ready_for_review_update_count": _true_count(frame, "ready_for_review_update"),
        "blocked_count": int((~frame["ready_for_review_update"].map(_is_true)).sum()) if not frame.empty else 0,
        "approval_requested_count": _true_count(frame, "approval_requested"),
        "approved_ready_count": int(
            (
                frame["ready_for_review_update"].map(_is_true)
                & (frame["normalized_review_status"] == "APPROVED_FOR_PIT_UNIVERSE")
            ).sum()
        )
        if not frame.empty
        else 0,
        "rejected_ready_count": int(
            (frame["ready_for_review_update"].map(_is_true) & (frame["normalized_review_status"] == "REJECTED")).sum()
        )
        if not frame.empty
        else 0,
        "needs_more_evidence_ready_count": int(
            (
                frame["ready_for_review_update"].map(_is_true)
                & (frame["normalized_review_status"] == "NEEDS_MORE_EVIDENCE")
            ).sum()
        )
        if not frame.empty
        else 0,
        "duplicate_identity_count": int((frame["ingestion_status"] == "UPDATE_BLOCKED_DUPLICATE_IDENTITY").sum())
        if not frame.empty
        else 0,
        "missing_identity_count": int((frame["ingestion_status"] == "UPDATE_BLOCKED_MISSING_IDENTITY").sum())
        if not frame.empty
        else 0,
        "suggested_copy_risk_count": _true_count(frame, "suggested_copy_risk"),
    }


def _summary_dict(result: PitUniverseEvidenceUpdateIngestionResult) -> dict[str, Any]:
    return {
        "ingestion_id": result.ingestion_id,
        "status": result.status,
        "row_count": result.row_count,
        "ready_for_review_update_count": result.ready_for_review_update_count,
        "blocked_count": result.blocked_count,
        "approval_requested_count": result.approval_requested_count,
        "approved_ready_count": result.approved_ready_count,
        "rejected_ready_count": result.rejected_ready_count,
        "needs_more_evidence_ready_count": result.needs_more_evidence_ready_count,
        "duplicate_identity_count": result.duplicate_identity_count,
        "missing_identity_count": result.missing_identity_count,
        "suggested_copy_risk_count": result.suggested_copy_risk_count,
    }


def _audit_metadata(
    request: PitUniverseEvidenceUpdateIngestionRequest,
    settings: PitUniverseEvidenceUpdateIngestionSettings,
) -> dict[str, Any]:
    return {
        "completed_updates": str(request.completed_updates),
        "worklist": str(request.worklist) if request.worklist else "",
        "config_version": settings.config_version,
        "approval_applied": False,
        "universe_exported": False,
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "cache_mutated": False,
        "network_api_called": False,
        "llm_api_called": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "ingestion_only": True,
    }


def _build_warnings(counts: dict[str, int]) -> list[str]:
    warnings: list[str] = []
    if counts["blocked_count"]:
        warnings.append("Some PIT universe evidence update rows are blocked and excluded from clean review updates.")
    if counts["approval_requested_count"] and counts["approved_ready_count"] < counts["approval_requested_count"]:
        warnings.append("Some approval-request rows did not pass ingestion validation.")
    if counts["suggested_copy_risk_count"]:
        warnings.append("Some approval-request rows appear to copy non-authoritative suggested hints without evidence.")
    if counts["ready_for_review_update_count"] == 0:
        warnings.append("No clean review updates are ready for later manual pit-universe-overlay-review use.")
    return warnings


def _dict_table(values: dict[str, Any]) -> str:
    if not values:
        return "| field | value |\n|---|---|\n"
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def _row_key(row: dict[str, Any]) -> str:
    return "|".join(_text(row.get(column)) for column in IDENTITY_COLUMNS)


def _bool_columns() -> list[str]:
    return [
        "include_flag",
        "is_active",
        "is_st",
        "is_suspended",
        "is_active_evidence",
        "survivorship_bias_resolved",
        "ready_for_review_update",
        "approval_requested",
        "suggested_copy_risk",
        "no_universe_export",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "ingestion_only",
    ]


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].map(_is_true).sum())


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text


def _present(value: Any) -> bool:
    return bool(_text(value))


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    return text in {"1", "true", "yes", "y", "是"}


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
    return pd.Timestamp(parsed)


def _date_text(value: Any) -> str:
    parsed = _parse_date(value)
    return "" if parsed is None else parsed.strftime("%Y-%m-%d")


def _datetime_text(value: Any) -> str:
    parsed = _parse_datetime(value)
    return "" if parsed is None else parsed.strftime("%Y-%m-%d %H:%M:%S")


def _assert_settings_safe(settings: PitUniverseEvidenceUpdateIngestionSettings) -> None:
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
    enabled = [name for name, value in unsafe.items() if value]
    if enabled:
        raise ValueError(f"PIT universe evidence update ingestion is report-only; unsafe settings enabled: {', '.join(enabled)}")
