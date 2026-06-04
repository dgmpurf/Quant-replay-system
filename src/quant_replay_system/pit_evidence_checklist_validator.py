"""Report-only strict PIT evidence checklist validation.

This validator evaluates completed or draft PIT universe evidence updates
against the local strict checklist. It writes report artifacts only and never
applies approvals, exports universe files, mutates cache, builds snapshots,
runs current-candidates, or performs trading workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import COMPLETED_UPDATE_COLUMNS


VALIDATION_COLUMNS = [
    "validator_id",
    "signal_date",
    "symbol",
    "universe_name",
    "profile",
    "review_status",
    "checklist_status",
    "checklist_pass",
    "blocked",
    "blocker_reason",
    "missing_required_fields",
    "unacceptable_source_fields",
    "pit_timing_blocker",
    "survivorship_blocker",
    "stock_st_blocker",
    "no_approval_applied",
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
    "checklist_validation_only",
]

SUMMARY_COLUMNS = [
    "validator_id",
    "status",
    "row_count",
    "checklist_pass_count",
    "blocked_count",
    "stock_core_blocked_count",
    "etf_core_blocked_count",
    "missing_evidence_count",
    "unacceptable_source_count",
    "pit_timing_blocked_count",
    "survivorship_blocked_count",
    "stock_st_blocked_count",
]

MISSING_MATRIX_COLUMNS = [
    "validator_id",
    "signal_date",
    "symbol",
    "universe_name",
    "field_name",
    "issue_code",
    "issue_message",
    "acceptable_sources",
    "notes",
]

APPROVAL_PREVIEW_COLUMNS = COMPLETED_UPDATE_COLUMNS + ["validator_id", "checklist_status"]

BOOLEAN_VALIDATION_COLUMNS = {
    "checklist_pass",
    "blocked",
    "pit_timing_blocker",
    "survivorship_blocker",
    "stock_st_blocker",
    "no_approval_applied",
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
    "checklist_validation_only",
}

SAFETY_STATEMENT = (
    "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
    "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitEvidenceChecklistValidatorSettings:
    output_dir: Path = Path("outputs/reports/pit_evidence_checklist_validator")
    config_version: str = "v0.1"
    write_artifacts: bool = True


@dataclass(frozen=True)
class PitEvidenceChecklistValidatorRequest:
    completed_updates: Path
    stock_checklist: Path
    etf_checklist: Path
    source_acceptance: Path | None = None


@dataclass(frozen=True)
class PitEvidenceChecklistValidatorResult:
    validator_id: str
    status: str
    row_count: int
    checklist_pass_count: int
    blocked_count: int
    stock_core_blocked_count: int
    etf_core_blocked_count: int
    validation_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    missing_evidence_frame: pd.DataFrame
    approval_candidate_preview_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def build_pit_evidence_checklist_validator(
    *,
    completed_updates: str | Path,
    stock_checklist: str | Path,
    etf_checklist: str | Path,
    source_acceptance: str | Path | None = None,
    output_dir: str | Path = "outputs/reports/pit_evidence_checklist_validator",
) -> PitEvidenceChecklistValidatorResult:
    request = PitEvidenceChecklistValidatorRequest(
        completed_updates=Path(completed_updates),
        stock_checklist=Path(stock_checklist),
        etf_checklist=Path(etf_checklist),
        source_acceptance=Path(source_acceptance) if source_acceptance else None,
    )
    updates = _read_updates(request.completed_updates)
    stock_rules = _read_checklist(request.stock_checklist)
    etf_rules = _read_checklist(request.etf_checklist)
    source_matrix = _read_source_matrix(request.source_acceptance)
    validator_id = _hash_payload(
        {
            "updates": request.completed_updates,
            "rows": updates.to_dict("records"),
            "stock_checklist": request.stock_checklist,
            "etf_checklist": request.etf_checklist,
        },
        length=12,
    )
    validation_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    for row in updates.to_dict("records"):
        profile = _profile(row)
        checklist = stock_rules if profile == "stock_core" else etf_rules
        validation, missing = _validate_row(validator_id, row, profile, checklist, source_matrix)
        validation_rows.append(validation)
        missing_rows.extend(missing)
    validation_frame = _finalize_frame(pd.DataFrame(validation_rows), VALIDATION_COLUMNS)
    missing_frame = _finalize_frame(pd.DataFrame(missing_rows), MISSING_MATRIX_COLUMNS)
    approval_preview = _approval_preview(updates, validation_frame, validator_id)
    summary_frame = _summary_frame(validator_id, validation_frame)
    summary = summary_frame.iloc[0].to_dict()
    paths = _resolve_paths(output_dir, validator_id)
    result = PitEvidenceChecklistValidatorResult(
        validator_id=validator_id,
        status=_string(summary.get("status")) or "WARN",
        row_count=_int(summary.get("row_count")),
        checklist_pass_count=_int(summary.get("checklist_pass_count")),
        blocked_count=_int(summary.get("blocked_count")),
        stock_core_blocked_count=_int(summary.get("stock_core_blocked_count")),
        etf_core_blocked_count=_int(summary.get("etf_core_blocked_count")),
        validation_frame=validation_frame,
        summary_frame=summary_frame,
        missing_evidence_frame=missing_frame,
        approval_candidate_preview_frame=approval_preview,
        artifact_paths=paths,
        warnings=[],
        known_limitations=[
            "Checklist validation is report-only and does not approve rows.",
            "Source acceptability is checked conservatively from field values and checklist text; it does not fetch or verify external documents.",
            "Post-close local cache timing remains blocked unless a later reviewed decision-time policy explicitly allows EOD/post-close evidence.",
        ],
        audit_metadata={
            "completed_updates": str(request.completed_updates),
            "stock_checklist": str(request.stock_checklist),
            "etf_checklist": str(request.etf_checklist),
            "source_acceptance": str(request.source_acceptance) if request.source_acceptance else "",
            "approval_applied": False,
            "pit_review_run": False,
            "export_readiness_run": False,
            "export_staging_run": False,
            "universe_exported": False,
            "active_worklist_mutated": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
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
            "checklist_validation_only": True,
        },
    )
    _write_artifacts(result)
    return result


def _validate_row(
    validator_id: str,
    row: dict[str, Any],
    profile: str,
    checklist: dict[str, dict[str, Any]],
    source_matrix: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    missing_fields: list[str] = []
    issue_rows: list[dict[str, Any]] = []

    def require(field: str, message: str | None = None) -> None:
        if not _string(row.get(field)):
            missing_fields.append(field)
            rule = checklist.get(field) or checklist.get("evidence_path_or_reference") or {}
            issue_rows.append(
                {
                    "validator_id": validator_id,
                    "signal_date": _string(row.get("signal_date")),
                    "symbol": _string(row.get("symbol")),
                    "universe_name": _string(row.get("universe_name")),
                    "field_name": field,
                    "issue_code": "MISSING_REQUIRED_EVIDENCE",
                    "issue_message": message or f"{field} is required for strict PIT approval.",
                    "acceptable_sources": _string(rule.get("acceptable_sources")),
                    "notes": _string(rule.get("notes")),
                }
            )

    for field in ["reviewer", "reviewed_at", "review_reason", "evidence_source", "listed_date", "listed_date_evidence"]:
        require(field)
    if not _string(row.get("evidence_path")) and not _string(row.get("evidence_reference")):
        require("evidence_path_or_reference", "evidence_path or evidence_reference is required.")
    for field in [
        "is_active",
        "is_active_evidence",
        "is_suspended",
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
    ]:
        require(field)
    if profile == "stock_core":
        require("is_st", "ST/no-ST evidence is required for stock_core rows.")

    unacceptable_fields = _unacceptable_source_fields(row, source_matrix)
    pit_timing_blocker = _pit_timing_blocked(row)
    survivorship_blocker = not _is_true(row.get("survivorship_bias_resolved"))
    stock_st_blocker = profile == "stock_core" and not _string(row.get("is_st"))

    for field in unacceptable_fields:
        issue_rows.append(_issue_row(validator_id, row, field, "UNACCEPTABLE_SOURCE", "Source is context-only or rejected."))
    if pit_timing_blocker:
        issue_rows.append(_issue_row(validator_id, row, "available_time", "PIT_TIMING_BLOCKED", "available_time is missing, future-dated, or post-close without reviewed EOD policy."))
    if survivorship_blocker:
        issue_rows.append(_issue_row(validator_id, row, "survivorship_bias_resolved", "SURVIVORSHIP_BLOCKED", "survivorship_bias_resolved must be true with evidence basis."))
    if stock_st_blocker:
        issue_rows.append(_issue_row(validator_id, row, "is_st", "ST_NO_ST_EVIDENCE_MISSING", "Stock rows require ST/no-ST evidence."))

    blockers: list[str] = []
    if missing_fields:
        blockers.append("missing evidence: " + ", ".join(sorted(set(missing_fields))))
    if unacceptable_fields:
        blockers.append("unacceptable/context-only source fields: " + ", ".join(sorted(set(unacceptable_fields))))
    if pit_timing_blocker:
        blockers.append("PIT timing blocked")
    if survivorship_blocker:
        blockers.append("survivorship unresolved")
    if stock_st_blocker:
        blockers.append("stock ST/no-ST evidence missing")

    if not blockers:
        status = "CHECKLIST_PASS_APPROVAL_CANDIDATE"
    elif unacceptable_fields:
        status = "CHECKLIST_BLOCKED_UNACCEPTABLE_SOURCE"
    elif pit_timing_blocker:
        status = "CHECKLIST_BLOCKED_PIT_TIMING"
    elif survivorship_blocker:
        status = "CHECKLIST_BLOCKED_SURVIVORSHIP"
    else:
        status = "CHECKLIST_BLOCKED_MISSING_EVIDENCE"

    return (
        {
            "validator_id": validator_id,
            "signal_date": _string(row.get("signal_date")),
            "symbol": _string(row.get("symbol")),
            "universe_name": _string(row.get("universe_name")),
            "profile": profile,
            "review_status": _string(row.get("review_status")),
            "checklist_status": status,
            "checklist_pass": status == "CHECKLIST_PASS_APPROVAL_CANDIDATE",
            "blocked": status != "CHECKLIST_PASS_APPROVAL_CANDIDATE",
            "blocker_reason": "; ".join(blockers),
            "missing_required_fields": ", ".join(sorted(set(missing_fields))),
            "unacceptable_source_fields": ", ".join(sorted(set(unacceptable_fields))),
            "pit_timing_blocker": pit_timing_blocker,
            "survivorship_blocker": survivorship_blocker,
            "stock_st_blocker": stock_st_blocker,
            **_safety_flags(),
        },
        issue_rows,
    )


def _unacceptable_source_fields(row: dict[str, Any], source_matrix: dict[str, str]) -> list[str]:
    evidence_text = " ".join(
        [_string(row.get("evidence_source")), _string(row.get("evidence_path")), _string(row.get("evidence_reference")), _string(row.get("source"))]
    ).lower()
    fields: list[str] = []
    rejected_markers = ["future-dated", "future_dated", "processed universe", "blog", "forum", "unknown"]
    if any(marker in evidence_text for marker in rejected_markers):
        fields.append("evidence_source")
    context_only = ["local_market_cache"] if not _string(row.get("is_active_evidence")) else []
    if context_only and "local_market_cache" in evidence_text:
        fields.append("is_active_evidence")
    _ = source_matrix
    return fields


def _pit_timing_blocked(row: dict[str, Any]) -> bool:
    signal_date = _date(_string(row.get("signal_date")))
    as_of_date = _date(_string(row.get("as_of_date")))
    available_text = _string(row.get("available_time"))
    available_date = _date(available_text)
    if signal_date is None:
        return True
    if as_of_date is None or as_of_date > signal_date:
        return True
    if available_date is None or available_date > signal_date:
        return True
    if "15:30" in available_text or "post" in available_text.lower():
        return True
    return False


def _approval_preview(updates: pd.DataFrame, validation: pd.DataFrame, validator_id: str) -> pd.DataFrame:
    if updates.empty or validation.empty:
        return pd.DataFrame(columns=APPROVAL_PREVIEW_COLUMNS)
    keys = ["signal_date", "symbol", "universe_name"]
    passed = validation.loc[validation["checklist_pass"].map(_is_true), keys + ["checklist_status"]]
    if passed.empty:
        return pd.DataFrame(columns=APPROVAL_PREVIEW_COLUMNS)
    preview = updates.merge(passed, on=keys, how="inner")
    preview["validator_id"] = validator_id
    return _finalize_frame(preview, APPROVAL_PREVIEW_COLUMNS)


def _summary_frame(validator_id: str, validation: pd.DataFrame) -> pd.DataFrame:
    row_count = len(validation)
    pass_count = _true_count(validation, "checklist_pass")
    blocked = _true_count(validation, "blocked")
    status = "PASS" if row_count and pass_count == row_count else "WARN" if row_count else "WARN"
    return pd.DataFrame(
        [
            {
                "validator_id": validator_id,
                "status": status,
                "row_count": row_count,
                "checklist_pass_count": pass_count,
                "blocked_count": blocked,
                "stock_core_blocked_count": int(((validation["profile"] == "stock_core") & validation["blocked"].map(_is_true)).sum()) if not validation.empty else 0,
                "etf_core_blocked_count": int(((validation["profile"] == "etf_core") & validation["blocked"].map(_is_true)).sum()) if not validation.empty else 0,
                "missing_evidence_count": int(validation["missing_required_fields"].map(lambda x: bool(_string(x))).sum()) if not validation.empty else 0,
                "unacceptable_source_count": int(validation["unacceptable_source_fields"].map(lambda x: bool(_string(x))).sum()) if not validation.empty else 0,
                "pit_timing_blocked_count": _true_count(validation, "pit_timing_blocker"),
                "survivorship_blocked_count": _true_count(validation, "survivorship_blocker"),
                "stock_st_blocked_count": _true_count(validation, "stock_st_blocker"),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_artifacts(result: PitEvidenceChecklistValidatorResult) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.validation_frame.to_csv(result.artifact_paths["validation_csv"], index=False)
    result.summary_frame.to_csv(result.artifact_paths["summary_csv"], index=False)
    result.missing_evidence_frame.to_csv(result.artifact_paths["missing_evidence_matrix"], index=False)
    result.approval_candidate_preview_frame.to_csv(result.artifact_paths["approval_candidate_preview"], index=False)
    metadata = {
        "validator_id": result.validator_id,
        "created_at": _mtime_text(artifact_dir),
        "status": result.status,
        "row_count": result.row_count,
        "checklist_pass_count": result.checklist_pass_count,
        "blocked_count": result.blocked_count,
        "stock_core_blocked_count": result.stock_core_blocked_count,
        "etf_core_blocked_count": result.etf_core_blocked_count,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        **_safety_flags(),
        "no_live_trading_statement": SAFETY_STATEMENT,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: PitEvidenceChecklistValidatorResult) -> str:
    return "\n".join(
        [
            "# PIT Evidence Checklist Validator",
            "",
            SAFETY_STATEMENT,
            "",
            "## Summary",
            "",
            _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
            "",
            "## Validation Rows",
            "",
            result.validation_frame[
                ["signal_date", "symbol", "universe_name", "checklist_status", "blocker_reason"]
            ].to_markdown(index=False)
            if not result.validation_frame.empty
            else "_No rows._",
            "",
            "## Interpretation",
            "",
            "A checklist pass is only an approval-candidate preview. This workflow does not set APPROVED_FOR_PIT_UNIVERSE and does not run PIT review.",
            "",
        ]
    )


def _resolve_paths(output_dir: str | Path, validator_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / validator_id
    return {
        "artifact_dir": artifact_dir,
        "validation_csv": artifact_dir / "pit_evidence_checklist_validation.csv",
        "summary_csv": artifact_dir / "pit_evidence_checklist_validation_summary.csv",
        "missing_evidence_matrix": artifact_dir / "missing_evidence_matrix.csv",
        "approval_candidate_preview": artifact_dir / "approval_candidate_preview.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _read_updates(path: Path) -> pd.DataFrame:
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    for column in COMPLETED_UPDATE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[COMPLETED_UPDATE_COLUMNS].copy()


def _read_checklist(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    return {str(row.get("field_name", "")).strip(): row for row in frame.to_dict("records")}


def _read_source_matrix(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    return {str(row.get("source_category", "")).strip().lower(): str(row.get("approval_acceptance", "")) for row in frame.to_dict("records")}


def _profile(row: dict[str, Any]) -> str:
    universe = _string(row.get("universe_name")).lower()
    if "stock" in universe:
        return "stock_core"
    if "etf" in universe:
        return "etf_core"
    instrument = _string(row.get("instrument_type")).upper()
    return "stock_core" if instrument == "STOCK" else "etf_core" if instrument == "ETF" else universe


def _issue_row(validator_id: str, row: dict[str, Any], field: str, code: str, message: str) -> dict[str, Any]:
    return {
        "validator_id": validator_id,
        "signal_date": _string(row.get("signal_date")),
        "symbol": _string(row.get("symbol")),
        "universe_name": _string(row.get("universe_name")),
        "field_name": field,
        "issue_code": code,
        "issue_message": message,
        "acceptable_sources": "",
        "notes": "",
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "no_approval_applied": True,
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
        "checklist_validation_only": True,
    }


def _date(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    try:
        return pd.Timestamp(value).normalize()
    except Exception:
        return None


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_is_true).sum())


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y"}


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text


def _finalize_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    for column in BOOLEAN_VALIDATION_COLUMNS.intersection(columns):
        output[column] = output[column].map(_is_true).astype(object)
    return output[columns].reset_index(drop=True)


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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


def _mtime_text(path: Path) -> str:
    try:
        return pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC").isoformat()
    except Exception:
        return "1970-01-01T00:00:00+00:00"
