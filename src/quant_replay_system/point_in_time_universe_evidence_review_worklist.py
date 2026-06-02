"""Reviewer worklists for completing PIT universe evidence.

This module reads PIT universe evidence-helper and review artifacts, then writes
row, symbol, and date worklists under reports only. It does not approve rows,
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

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


WORKLIST_OUTPUT_COLUMNS = [
    "worklist_id",
    "review_id",
    "helper_id",
    "signal_date",
    "symbol",
    "universe_name",
    "current_review_status",
    "current_valid_for_signal_date",
    "survivorship_bias_warning",
    "survivorship_bias_resolved",
    "suggested_name",
    "suggested_instrument_type",
    "suggested_exchange",
    "suggested_industry",
    "suggested_min_lot",
    "suggested_t_plus_rule",
    "suggested_is_active",
    "suggested_is_st",
    "suggested_is_suspended",
    "hint_available_time",
    "hint_is_future_dated_for_signal_date",
    "hint_authoritative_for_pit",
    "missing_reviewer",
    "missing_reviewed_at",
    "missing_review_reason",
    "missing_evidence_source",
    "missing_evidence_path_or_reference",
    "missing_listed_date_evidence",
    "missing_is_active_evidence",
    "missing_survivorship_bias_resolution",
    "missing_required_universe_metadata",
    "required_next_evidence_fields",
    "suggested_next_review_action",
    "reviewer",
    "reviewed_at",
    "review_reason",
    "evidence_source",
    "evidence_path",
    "evidence_reference",
    "listed_date_evidence",
    "delisted_date_evidence",
    "is_active_evidence",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "worklist_only",
]

UPDATE_TEMPLATE_COLUMNS = [
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

SYMBOL_SUMMARY_COLUMNS = [
    "worklist_id",
    "review_id",
    "helper_id",
    "symbol",
    "universe_name",
    "row_count",
    "signal_date_count",
    "first_signal_date",
    "last_signal_date",
    "needs_evidence_count",
    "future_dated_hint_count",
    "authoritative_hint_count",
    "suggested_name",
    "suggested_instrument_type",
    "suggested_exchange",
    "suggested_source",
    "suggested_next_review_action",
]

DATE_SUMMARY_COLUMNS = [
    "worklist_id",
    "review_id",
    "helper_id",
    "signal_date",
    "universe_name",
    "row_count",
    "symbol_count",
    "needs_evidence_count",
    "future_dated_hint_count",
    "authoritative_hint_count",
    "valid_for_signal_date_count",
    "suggested_next_review_action",
]

HELPER_REQUIRED_COLUMNS = [
    "helper_id",
    "review_id",
    "signal_date",
    "symbol",
    "universe_name",
    "current_review_status",
    "current_valid_for_signal_date",
    "current_survivorship_bias_warning",
    "current_survivorship_bias_resolved",
]

REVIEW_REQUIRED_COLUMNS = [
    "review_id",
    "signal_date",
    "symbol",
    "universe_name",
    "review_status",
    "valid_for_signal_date",
]

REQUIRED_UNIVERSE_METADATA_COLUMNS = [
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

EVIDENCE_GAP_COLUMNS = [
    "missing_reviewer",
    "missing_reviewed_at",
    "missing_review_reason",
    "missing_evidence_source",
    "missing_evidence_path_or_reference",
    "missing_listed_date_evidence",
    "missing_is_active_evidence",
    "missing_survivorship_bias_resolution",
]

SAFETY_STATEMENT = (
    "No universe export, data/raw write, data/processed write, current-candidates generation, "
    "snapshot build, forward labels, live trading, broker API, order placement, message delivery, "
    "network/API, LLM/API, or cache mutation was invoked."
)


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_evidence_review_worklist")
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
class PitUniverseEvidenceReviewWorklistRequest:
    helper: Path
    review: Path


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistRow:
    values: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {column: self.values.get(column, "") for column in WORKLIST_OUTPUT_COLUMNS}


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistArtifactPaths:
    artifact_dir: Path
    worklist_csv: Path
    symbol_summary: Path
    date_summary: Path
    update_template: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "worklist_csv": self.worklist_csv,
            "symbol_summary": self.symbol_summary,
            "date_summary": self.date_summary,
            "update_template": self.update_template,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceReviewWorklistResult:
    worklist_id: str
    status: str
    request: PitUniverseEvidenceReviewWorklistRequest
    row_count: int
    symbol_count: int
    signal_date_count: int
    needs_manual_review_count: int
    needs_evidence_count: int
    future_dated_hint_count: int
    authoritative_hint_count: int
    approved_count: int
    valid_for_signal_date_count: int
    worklist_frame: pd.DataFrame
    symbol_summary_frame: pd.DataFrame
    date_summary_frame: pd.DataFrame
    update_template_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_pit_universe_evidence_helper_for_worklist(helper: str | Path) -> pd.DataFrame:
    helper_path = Path(helper)
    if not helper_path.exists():
        raise FileNotFoundError(f"PIT universe evidence helper template not found: {helper_path}")
    frame = read_csv_preserve_symbol_columns(helper_path, keep_default_na=False)
    missing = [column for column in HELPER_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"PIT universe evidence helper missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    for column in _helper_optional_columns():
        if column not in output.columns:
            output[column] = ""
    return output


def load_pit_universe_review_for_worklist(review: str | Path) -> pd.DataFrame:
    review_path = Path(review)
    if not review_path.exists():
        raise FileNotFoundError(f"Reviewed PIT universe overlay not found: {review_path}")
    frame = read_csv_preserve_symbol_columns(review_path, keep_default_na=False)
    missing = [column for column in REVIEW_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Reviewed PIT universe overlay missing required columns: {', '.join(missing)}")
    output = frame.copy(deep=True)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    for column in _review_optional_columns():
        if column not in output.columns:
            output[column] = ""
    return output


def build_pit_universe_evidence_review_worklist(
    *,
    helper: str | Path,
    review: str | Path,
    output_dir: str | Path | None = None,
    settings: PitUniverseEvidenceReviewWorklistSettings | None = None,
) -> PitUniverseEvidenceReviewWorklistResult:
    resolved_settings = settings or PitUniverseEvidenceReviewWorklistSettings()
    if output_dir is not None:
        resolved_settings = PitUniverseEvidenceReviewWorklistSettings(
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

    request = PitUniverseEvidenceReviewWorklistRequest(helper=Path(helper), review=Path(review))
    helper_frame = load_pit_universe_evidence_helper_for_worklist(request.helper)
    review_frame = load_pit_universe_review_for_worklist(request.review)
    merged = _merge_helper_and_review(helper_frame, review_frame)
    worklist_id = generate_pit_universe_evidence_review_worklist_id(request, merged, resolved_settings)
    worklist_frame = _finalize_worklist_frame(
        pd.DataFrame(
            [_build_worklist_row(row, worklist_id=worklist_id).as_dict() for row in merged.to_dict("records")],
            columns=WORKLIST_OUTPUT_COLUMNS,
        )
    )
    symbol_summary = build_pit_universe_evidence_review_symbol_summary(worklist_frame)
    date_summary = build_pit_universe_evidence_review_date_summary(worklist_frame)
    update_template = build_pit_universe_evidence_review_update_template(worklist_frame)
    counts = _build_counts(worklist_frame)
    paths = resolve_pit_universe_evidence_review_worklist_paths(resolved_settings.output_dir, worklist_id)
    result = PitUniverseEvidenceReviewWorklistResult(
        worklist_id=worklist_id,
        status="WARN" if counts["needs_evidence_count"] > 0 else "PASS",
        request=request,
        row_count=counts["row_count"],
        symbol_count=counts["symbol_count"],
        signal_date_count=counts["signal_date_count"],
        needs_manual_review_count=counts["needs_manual_review_count"],
        needs_evidence_count=counts["needs_evidence_count"],
        future_dated_hint_count=counts["future_dated_hint_count"],
        authoritative_hint_count=counts["authoritative_hint_count"],
        approved_count=counts["approved_count"],
        valid_for_signal_date_count=counts["valid_for_signal_date_count"],
        worklist_frame=worklist_frame,
        symbol_summary_frame=symbol_summary,
        date_summary_frame=date_summary,
        update_template_frame=update_template,
        warnings=_build_warnings(counts),
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_pit_universe_evidence_review_worklist_artifacts(result)
    return result


def build_pit_universe_evidence_review_symbol_summary(worklist_frame: pd.DataFrame) -> pd.DataFrame:
    if worklist_frame.empty:
        return pd.DataFrame(columns=SYMBOL_SUMMARY_COLUMNS)
    rows = []
    for (symbol, universe_name), group in worklist_frame.groupby(["symbol", "universe_name"], sort=True):
        rows.append(
            {
                "worklist_id": _first(group, "worklist_id"),
                "review_id": _first(group, "review_id"),
                "helper_id": _first(group, "helper_id"),
                "symbol": symbol,
                "universe_name": universe_name,
                "row_count": int(len(group)),
                "signal_date_count": int(group["signal_date"].nunique()),
                "first_signal_date": str(group["signal_date"].min()),
                "last_signal_date": str(group["signal_date"].max()),
                "needs_evidence_count": int(
                    (
                        group[EVIDENCE_GAP_COLUMNS].apply(lambda row: any(_is_true(value) for value in row), axis=1)
                        | group["missing_required_universe_metadata"].map(_is_true)
                    ).sum()
                ),
                "future_dated_hint_count": _true_count(group, "hint_is_future_dated_for_signal_date"),
                "authoritative_hint_count": _true_count(group, "hint_authoritative_for_pit"),
                "suggested_name": _first(group, "suggested_name"),
                "suggested_instrument_type": _first(group, "suggested_instrument_type"),
                "suggested_exchange": _first(group, "suggested_exchange"),
                "suggested_source": "",
                "suggested_next_review_action": "Collect symbol-level PIT evidence, then apply row-level review updates per signal date.",
            }
        )
    return pd.DataFrame(rows, columns=SYMBOL_SUMMARY_COLUMNS)


def build_pit_universe_evidence_review_date_summary(worklist_frame: pd.DataFrame) -> pd.DataFrame:
    if worklist_frame.empty:
        return pd.DataFrame(columns=DATE_SUMMARY_COLUMNS)
    rows = []
    for (signal_date, universe_name), group in worklist_frame.groupby(["signal_date", "universe_name"], sort=True):
        rows.append(
            {
                "worklist_id": _first(group, "worklist_id"),
                "review_id": _first(group, "review_id"),
                "helper_id": _first(group, "helper_id"),
                "signal_date": signal_date,
                "universe_name": universe_name,
                "row_count": int(len(group)),
                "symbol_count": int(group["symbol"].nunique()),
                "needs_evidence_count": int(group[EVIDENCE_GAP_COLUMNS].apply(lambda row: any(_is_true(value) for value in row), axis=1).sum()),
                "future_dated_hint_count": _true_count(group, "hint_is_future_dated_for_signal_date"),
                "authoritative_hint_count": _true_count(group, "hint_authoritative_for_pit"),
                "valid_for_signal_date_count": _true_count(group, "current_valid_for_signal_date"),
                "suggested_next_review_action": "Review PIT evidence for every symbol on this signal date before snapshot preparation.",
            }
        )
    return pd.DataFrame(rows, columns=DATE_SUMMARY_COLUMNS)


def build_pit_universe_evidence_review_update_template(worklist_frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in worklist_frame.to_dict("records"):
        rows.append(
            {
                "signal_date": row.get("signal_date", ""),
                "symbol": normalize_symbol_value(row.get("symbol")),
                "universe_name": row.get("universe_name", ""),
                "review_status": "",
                "include_flag": "",
                "reviewer": row.get("reviewer", ""),
                "reviewed_at": row.get("reviewed_at", ""),
                "review_reason": row.get("review_reason", ""),
                "evidence_source": row.get("evidence_source", ""),
                "evidence_path": row.get("evidence_path", ""),
                "evidence_reference": row.get("evidence_reference", ""),
                "listed_date": "",
                "delisted_date": "",
                "is_active": "",
                "is_st": "",
                "is_suspended": "",
                "listed_date_evidence": row.get("listed_date_evidence", ""),
                "delisted_date_evidence": row.get("delisted_date_evidence", ""),
                "is_active_evidence": row.get("is_active_evidence", ""),
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
    return pd.DataFrame(rows, columns=UPDATE_TEMPLATE_COLUMNS)


def write_pit_universe_evidence_review_worklist_artifacts(
    result: PitUniverseEvidenceReviewWorklistResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceReviewWorklistArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.worklist_frame.to_csv(paths.worklist_csv, index=False)
    result.symbol_summary_frame.to_csv(paths.symbol_summary, index=False)
    result.date_summary_frame.to_csv(paths.date_summary, index=False)
    result.update_template_frame.to_csv(paths.update_template, index=False)
    paths.report.write_text(render_pit_universe_evidence_review_worklist_report(result), encoding="utf-8")
    paths.metadata.write_text(
        json.dumps(_json_safe(build_pit_universe_evidence_review_worklist_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_pit_universe_evidence_review_worklist_report(result: PitUniverseEvidenceReviewWorklistResult) -> str:
    lines = [
        f"# PIT Universe Evidence Review Worklist: {result.worklist_id}",
        "",
        SAFETY_STATEMENT,
        "This is a worklist-only artifact. It does not approve PIT rows or export usable universe files.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Worklist Rules",
        "",
        "- `suggested_*` columns are non-authoritative hints.",
        "- `hint_authoritative_for_pit` must remain false.",
        "- `APPROVED_FOR_PIT_UNIVERSE` must be supplied only by a later explicit reviewer update.",
        "- `valid_for_signal_date=true` is never set by this worklist.",
        "",
        "## Symbol Summary",
        "",
        _markdown_table(result.symbol_summary_frame, SYMBOL_SUMMARY_COLUMNS),
        "",
        "## Date Summary",
        "",
        _markdown_table(result.date_summary_frame, DATE_SUMMARY_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_pit_universe_evidence_review_worklist_metadata(
    result: PitUniverseEvidenceReviewWorklistResult,
) -> dict[str, Any]:
    return {
        "worklist_id": result.worklist_id,
        "status": result.status,
        "created_at": "2024-05-29T00:00:00",
        "helper_id": result.worklist_frame["helper_id"].iloc[0] if not result.worklist_frame.empty else "",
        "review_id": result.worklist_frame["review_id"].iloc[0] if not result.worklist_frame.empty else "",
        "row_count": result.row_count,
        "symbol_count": result.symbol_count,
        "signal_date_count": result.signal_date_count,
        "needs_manual_review_count": result.needs_manual_review_count,
        "needs_evidence_count": result.needs_evidence_count,
        "future_dated_hint_count": result.future_dated_hint_count,
        "authoritative_hint_count": result.authoritative_hint_count,
        "approved_count": result.approved_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "update_template_path": str(result.artifact_paths["update_template"]),
        "warnings": result.warnings,
        "safety_statement": SAFETY_STATEMENT,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "Worklist rows are not approvals.",
            "Base universe hints remain non-authoritative and may be future-dated.",
            "Human reviewers must provide evidence before approval, export readiness, staging, or snapshot preparation can proceed.",
        ],
    }


def generate_pit_universe_evidence_review_worklist_id(
    request: PitUniverseEvidenceReviewWorklistRequest,
    merged_frame: pd.DataFrame,
    settings: PitUniverseEvidenceReviewWorklistSettings,
) -> str:
    payload = {
        "helper": str(request.helper),
        "review": str(request.review),
        "config_version": settings.config_version,
        "rows": merged_frame[
            [column for column in ["signal_date", "symbol", "universe_name", "current_review_status"] if column in merged_frame]
        ].to_dict("records"),
    }
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def resolve_pit_universe_evidence_review_worklist_paths(
    output_dir: str | Path,
    worklist_id: str,
) -> PitUniverseEvidenceReviewWorklistArtifactPaths:
    artifact_dir = Path(output_dir) / worklist_id
    return PitUniverseEvidenceReviewWorklistArtifactPaths(
        artifact_dir=artifact_dir,
        worklist_csv=artifact_dir / "pit_universe_evidence_review_worklist.csv",
        symbol_summary=artifact_dir / "pit_universe_evidence_review_symbol_summary.csv",
        date_summary=artifact_dir / "pit_universe_evidence_review_date_summary.csv",
        update_template=artifact_dir / "pit_universe_evidence_review_update_template.csv",
        report=artifact_dir / "pit_universe_evidence_review_worklist_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _merge_helper_and_review(helper_frame: pd.DataFrame, review_frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["signal_date", "symbol", "universe_name"]
    helper = helper_frame.copy()
    review = review_frame.copy()
    helper["symbol"] = helper["symbol"].map(normalize_symbol_value)
    review["symbol"] = review["symbol"].map(normalize_symbol_value)
    review_columns = [
        "signal_date",
        "symbol",
        "universe_name",
        "reviewer",
        "reviewed_at",
        "review_reason",
        "evidence_source",
        "evidence_path",
        "evidence_reference",
        "listed_date_evidence",
        "delisted_date_evidence",
        "is_active_evidence",
        *REQUIRED_UNIVERSE_METADATA_COLUMNS,
    ]
    review_subset = review[[column for column in review_columns if column in review.columns]].copy()
    return helper.merge(review_subset, how="left", on=keys, suffixes=("", "_review"))


def _build_worklist_row(row: dict[str, Any], *, worklist_id: str) -> PitUniverseEvidenceReviewWorklistRow:
    missing_required_universe_metadata = any(not _present(row.get(column)) for column in REQUIRED_UNIVERSE_METADATA_COLUMNS)
    required_next_fields = _required_next_fields(row, missing_required_universe_metadata)
    values = {
        "worklist_id": worklist_id,
        "review_id": _text(row.get("review_id")),
        "helper_id": _text(row.get("helper_id")),
        "signal_date": _date_text(row.get("signal_date")),
        "symbol": normalize_symbol_value(row.get("symbol")),
        "universe_name": _text(row.get("universe_name")),
        "current_review_status": _text(row.get("current_review_status")).upper(),
        "current_valid_for_signal_date": _is_true(row.get("current_valid_for_signal_date")) and False,
        "survivorship_bias_warning": _is_true(row.get("current_survivorship_bias_warning")),
        "survivorship_bias_resolved": _is_true(row.get("current_survivorship_bias_resolved")) and False,
        "suggested_name": _text(row.get("suggested_name")),
        "suggested_instrument_type": _text(row.get("suggested_instrument_type")),
        "suggested_exchange": _text(row.get("suggested_exchange")),
        "suggested_industry": _text(row.get("suggested_industry")),
        "suggested_min_lot": _text(row.get("suggested_min_lot")),
        "suggested_t_plus_rule": _text(row.get("suggested_t_plus_rule")),
        "suggested_is_active": _text(row.get("suggested_is_active")),
        "suggested_is_st": _text(row.get("suggested_is_st")),
        "suggested_is_suspended": _text(row.get("suggested_is_suspended")),
        "hint_available_time": _text(row.get("hint_available_time")),
        "hint_is_future_dated_for_signal_date": _is_true(row.get("hint_is_future_dated_for_signal_date")),
        "hint_authoritative_for_pit": False,
        "missing_reviewer": _is_true(row.get("missing_reviewer")),
        "missing_reviewed_at": _is_true(row.get("missing_reviewed_at")),
        "missing_review_reason": _is_true(row.get("missing_review_reason")),
        "missing_evidence_source": _is_true(row.get("missing_evidence_source")),
        "missing_evidence_path_or_reference": _is_true(row.get("missing_evidence_path_or_reference")),
        "missing_listed_date_evidence": _is_true(row.get("missing_listed_date_evidence")),
        "missing_is_active_evidence": _is_true(row.get("missing_is_active_evidence")),
        "missing_survivorship_bias_resolution": _is_true(row.get("missing_survivorship_bias_resolution")),
        "missing_required_universe_metadata": missing_required_universe_metadata,
        "required_next_evidence_fields": ",".join(required_next_fields),
        "suggested_next_review_action": _suggested_action(required_next_fields),
        "reviewer": _text(row.get("reviewer")),
        "reviewed_at": _text(row.get("reviewed_at")),
        "review_reason": _text(row.get("review_reason")),
        "evidence_source": _text(row.get("evidence_source")),
        "evidence_path": _text(row.get("evidence_path")),
        "evidence_reference": _text(row.get("evidence_reference")),
        "listed_date_evidence": _text(row.get("listed_date_evidence")),
        "delisted_date_evidence": _text(row.get("delisted_date_evidence")),
        "is_active_evidence": _text(row.get("is_active_evidence")),
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }
    return PitUniverseEvidenceReviewWorklistRow(values=values)


def _required_next_fields(row: dict[str, Any], missing_required_universe_metadata: bool) -> list[str]:
    fields: list[str] = []
    mapping = {
        "missing_reviewer": "reviewer",
        "missing_reviewed_at": "reviewed_at",
        "missing_review_reason": "review_reason",
        "missing_evidence_source": "evidence_source",
        "missing_evidence_path_or_reference": "evidence_path_or_reference",
        "missing_listed_date_evidence": "listed_date_evidence",
        "missing_is_active_evidence": "is_active_evidence",
        "missing_survivorship_bias_resolution": "survivorship_bias_resolved",
    }
    for flag, field in mapping.items():
        if _is_true(row.get(flag)):
            fields.append(field)
    if missing_required_universe_metadata:
        fields.append("required_universe_metadata")
    return fields


def _suggested_action(fields: list[str]) -> str:
    if not fields:
        return "Review existing evidence manually; this worklist does not approve rows."
    return "Fill reviewer/evidence/PIT metadata fields manually; suggested hints are non-authoritative."


def _build_counts(frame: pd.DataFrame) -> dict[str, int]:
    row_count = int(len(frame))
    needs_evidence_count = (
        int(
            (
                frame[EVIDENCE_GAP_COLUMNS].apply(lambda row: any(_is_true(value) for value in row), axis=1)
                | frame["missing_required_universe_metadata"].map(_is_true)
            ).sum()
        )
        if not frame.empty
        else 0
    )
    return {
        "row_count": row_count,
        "symbol_count": int(frame["symbol"].nunique()) if not frame.empty else 0,
        "signal_date_count": int(frame["signal_date"].nunique()) if not frame.empty else 0,
        "needs_manual_review_count": int((frame["current_review_status"] == "NEEDS_MANUAL_REVIEW").sum())
        if not frame.empty
        else 0,
        "needs_evidence_count": needs_evidence_count,
        "future_dated_hint_count": _true_count(frame, "hint_is_future_dated_for_signal_date"),
        "authoritative_hint_count": _true_count(frame, "hint_authoritative_for_pit"),
        "approved_count": int((frame["current_review_status"] == "APPROVED_FOR_PIT_UNIVERSE").sum())
        if not frame.empty
        else 0,
        "valid_for_signal_date_count": _true_count(frame, "current_valid_for_signal_date"),
    }


def _build_warnings(counts: dict[str, int]) -> list[str]:
    warnings = []
    if counts["needs_evidence_count"] > 0:
        warnings.append("Some PIT universe rows still need reviewer evidence and PIT universe metadata.")
    if counts["future_dated_hint_count"] > 0:
        warnings.append("Some suggested hints are future-dated and must remain non-authoritative.")
    if counts["authoritative_hint_count"] > 0:
        warnings.append("Unexpected authoritative hints detected; worklist hints must remain non-authoritative.")
    if counts["approved_count"] > 0 or counts["valid_for_signal_date_count"] > 0:
        warnings.append("Input already contains approved or valid rows; worklist does not create those states.")
    return warnings


def _audit_metadata(
    request: PitUniverseEvidenceReviewWorklistRequest,
    settings: PitUniverseEvidenceReviewWorklistSettings,
) -> dict[str, Any]:
    return {
        "helper": str(request.helper),
        "review": str(request.review),
        "config_version": settings.config_version,
        "worklist_only": True,
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


def _summary_dict(result: PitUniverseEvidenceReviewWorklistResult) -> dict[str, Any]:
    return {
        "worklist_id": result.worklist_id,
        "status": result.status,
        "row_count": result.row_count,
        "symbol_count": result.symbol_count,
        "signal_date_count": result.signal_date_count,
        "needs_manual_review_count": result.needs_manual_review_count,
        "needs_evidence_count": result.needs_evidence_count,
        "future_dated_hint_count": result.future_dated_hint_count,
        "authoritative_hint_count": result.authoritative_hint_count,
        "approved_count": result.approved_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "helper": str(result.request.helper),
        "review": str(result.request.review),
    }


def _helper_optional_columns() -> list[str]:
    return [
        *EVIDENCE_GAP_COLUMNS,
        "suggested_name",
        "suggested_instrument_type",
        "suggested_exchange",
        "suggested_industry",
        "suggested_min_lot",
        "suggested_t_plus_rule",
        "suggested_is_active",
        "suggested_is_st",
        "suggested_is_suspended",
        "hint_available_time",
        "hint_is_future_dated_for_signal_date",
        "hint_authoritative_for_pit",
    ]


def _review_optional_columns() -> list[str]:
    return [
        "reviewer",
        "reviewed_at",
        "review_reason",
        "evidence_source",
        "evidence_path",
        "evidence_reference",
        "listed_date_evidence",
        "delisted_date_evidence",
        "is_active_evidence",
        *REQUIRED_UNIVERSE_METADATA_COLUMNS,
    ]


def _finalize_worklist_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in WORKLIST_OUTPUT_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    bool_columns = [
        "current_valid_for_signal_date",
        "survivorship_bias_warning",
        "survivorship_bias_resolved",
        "hint_is_future_dated_for_signal_date",
        "hint_authoritative_for_pit",
        *EVIDENCE_GAP_COLUMNS,
        "missing_required_universe_metadata",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "worklist_only",
    ]
    for column in bool_columns:
        output[column] = output[column].map(_is_true).astype(object)
    output["symbol"] = output["symbol"].map(normalize_symbol_value)
    return output[WORKLIST_OUTPUT_COLUMNS]


def _assert_settings_safe(settings: PitUniverseEvidenceReviewWorklistSettings) -> None:
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
        raise ValueError(f"PIT universe evidence review worklist cannot enable unsafe behavior: {', '.join(enabled)}")


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_is_true).sum())


def _first(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    for value in frame[column].tolist():
        text = _text(value)
        if text:
            return text
    return ""


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
    text = _text(value)
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return text
    return pd.Timestamp(parsed).strftime("%Y-%m-%d")


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
    preview = frame[available].head(max_rows)
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
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
