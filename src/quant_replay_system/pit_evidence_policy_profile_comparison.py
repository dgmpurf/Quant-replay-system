"""Report-only PIT evidence policy profile comparison.

This workflow compares the existing strict PIT checklist result with an opt-in
EOD/post-close low-budget policy profile. It writes comparison artifacts only
and never applies approvals or mutates active evidence workflows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PROFILE_NAME = "EOD_POST_CLOSE_LOW_BUDGET_PIT"
REVIEWED_NO_HIT_PROFILE_NAME = "EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT"
REFERENCE_PROFILE_NAME = "STRICT_PIT"
SAFETY_STATEMENT = (
    "No approval applied, PIT review, export-readiness, staging, universe export, active mutation, "
    "data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, "
    "live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked."
)

COMPARISON_COLUMNS = [
    "comparison_id",
    "symbol",
    "signal_date",
    "recommended_future_universe",
    "profile_name",
    "strict_status",
    "eod_low_budget_status",
    "reviewed_no_hit_status",
    "strict_blockers",
    "relaxed_blockers",
    "no_hit_relaxed_context",
    "remaining_blockers",
    "available_time",
    "decision_time",
    "available_time_within_decision_time",
    "official_quotation_presence_supported",
    "same_day_market_cache_used_as_support",
    "active_context_supported_by_cache",
    "suspension_context_supported_by_cache",
    "no_hit_context_supported",
    "no_hit_not_delisted_context_supported",
    "no_hit_no_suspension_context_supported",
    "no_hit_no_st_context_supported",
    "reviewer_acceptance_required",
    "reviewer_acceptance_present",
    "source_coverage_required",
    "source_coverage_documented",
    "query_window_documented",
    "not_delisted_still_required",
    "st_no_st_still_required",
    "survivorship_still_required",
    "survivorship_rationale_required",
    "checklist_pass_under_strict",
    "checklist_pass_under_eod_low_budget",
    "checklist_pass_under_reviewed_no_hit_support",
    "approval_candidate_preview_only",
    "should_apply_approval",
    "no_pit_review_run",
    "no_export_readiness_run",
    "no_staging_run",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "comparison_only",
]

SUMMARY_COLUMNS = [
    "comparison_id",
    "status",
    "reference_profile_name",
    "profile_name",
    "profile_is_opt_in",
    "strict_default_unchanged",
    "row_count",
    "strict_checklist_pass_count",
    "eod_low_budget_checklist_pass_count",
    "reviewed_no_hit_support_pass_count",
    "no_hit_context_supported_count",
    "reviewer_acceptance_required_count",
    "relaxed_blocker_count",
    "remaining_blocked_count",
    "approval_candidate_preview_count",
]


@dataclass(frozen=True)
class PitEvidencePolicyProfileComparisonResult:
    comparison_id: str
    status: str
    reference_profile_name: str
    profile_name: str
    profile_is_opt_in: bool
    strict_default_unchanged: bool
    row_count: int
    strict_checklist_pass_count: int
    eod_low_budget_checklist_pass_count: int
    reviewed_no_hit_support_pass_count: int
    no_hit_context_supported_count: int
    reviewer_acceptance_required_count: int
    relaxed_blocker_count: int
    remaining_blocked_count: int
    comparison_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    relaxed_blocker_frame: pd.DataFrame
    remaining_blocker_frame: pd.DataFrame
    policy_snapshot_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def build_pit_evidence_policy_profile_comparison(
    *,
    validator: str | Path,
    completed_updates: str | Path,
    policy_audit: str | Path,
    profile: str = PROFILE_NAME,
    decision_policy: str = "EOD_POST_CLOSE",
    decision_time: str | None = None,
    output_dir: str | Path = "outputs/reports/pit_evidence_policy_profile_comparison",
) -> PitEvidencePolicyProfileComparisonResult:
    validator_dir = Path(validator)
    updates_path = Path(completed_updates)
    policy_audit_dir = Path(policy_audit)
    validation = _read_validator_validation(validator_dir)
    updates = read_csv_preserve_symbol_columns(updates_path, keep_default_na=False)
    policy_snapshot = _read_policy_snapshot(policy_audit_dir)
    comparison_id = _comparison_id(
        {
            "validator": validator_dir,
            "completed_updates": updates_path,
            "policy_audit": policy_audit_dir,
            "profile": profile,
            "decision_policy": decision_policy,
            "decision_time": decision_time or "",
        }
    )
    validation_by_key = {_key(row): row for row in validation.to_dict("records")}
    no_hit_policy_available = _no_hit_policy_available(policy_audit_dir)
    rows = [
        _compare_row(
            comparison_id=comparison_id,
            update=row,
            strict=validation_by_key.get(_key(row), {}),
            profile=profile,
            decision_policy=decision_policy,
            decision_time=decision_time,
            no_hit_policy_available=no_hit_policy_available,
        )
        for row in updates.to_dict("records")
    ]
    comparison_frame = _finalize(pd.DataFrame(rows), COMPARISON_COLUMNS)
    relaxed_frame = _relaxed_matrix(comparison_frame)
    remaining_frame = _remaining_matrix(comparison_frame)
    summary_frame = _summary(comparison_id, profile, comparison_frame)
    status = _string(summary_frame.iloc[0].get("status")) if not summary_frame.empty else "WARN"
    paths = _paths(output_dir, comparison_id)
    result = PitEvidencePolicyProfileComparisonResult(
        comparison_id=comparison_id,
        status=status,
        reference_profile_name=REFERENCE_PROFILE_NAME,
        profile_name=profile,
        profile_is_opt_in=True,
        strict_default_unchanged=True,
        row_count=len(comparison_frame),
        strict_checklist_pass_count=_true_count(comparison_frame, "checklist_pass_under_strict"),
        eod_low_budget_checklist_pass_count=_true_count(comparison_frame, "checklist_pass_under_eod_low_budget"),
        reviewed_no_hit_support_pass_count=_true_count(comparison_frame, "checklist_pass_under_reviewed_no_hit_support"),
        no_hit_context_supported_count=_true_count(comparison_frame, "no_hit_context_supported"),
        reviewer_acceptance_required_count=_true_count(comparison_frame, "reviewer_acceptance_required"),
        relaxed_blocker_count=len(relaxed_frame),
        remaining_blocked_count=int((~comparison_frame[_active_pass_column(profile)].map(_bool)).sum())
        if not comparison_frame.empty
        else 0,
        comparison_frame=comparison_frame,
        summary_frame=summary_frame,
        relaxed_blocker_frame=relaxed_frame,
        remaining_blocker_frame=remaining_frame,
        policy_snapshot_frame=policy_snapshot,
        artifact_paths=paths,
        audit_metadata={
            "validator": str(validator_dir),
            "completed_updates": str(updates_path),
            "policy_audit": str(policy_audit_dir),
            "decision_policy": decision_policy,
            "decision_time": decision_time or "",
            "reference_profile_name": REFERENCE_PROFILE_NAME,
            "profile_is_opt_in": True,
            "reviewed_no_hit_profile_name": REVIEWED_NO_HIT_PROFILE_NAME,
            "reviewed_no_hit_profile_is_opt_in": profile.upper() == REVIEWED_NO_HIT_PROFILE_NAME,
            "no_hit_policy_available": no_hit_policy_available,
            "strict_default_unchanged": True,
            "approval_applied": False,
            "pit_review_run": False,
            "export_readiness_run": False,
            "export_staging_run": False,
            "universe_exported": False,
            "active_worklist_mutated": False,
            "no_data_raw_write": True,
            "no_data_processed_write": True,
            "no_current_candidates_generated": True,
            "no_snapshot_built": True,
            "no_forward_labels": True,
            "cache_mutated": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_order_placement": True,
            "no_message_sent": True,
            "comparison_only": True,
            "approval_updates_created": False,
        },
    )
    _write_artifacts(result)
    return result


def _compare_row(
    *,
    comparison_id: str,
    update: dict[str, Any],
    strict: dict[str, Any],
    profile: str,
    decision_policy: str,
    decision_time: str | None,
    no_hit_policy_available: bool,
) -> dict[str, Any]:
    signal_date = _string(update.get("signal_date"))
    available_time = _string(update.get("available_time"))
    effective_decision_time = _decision_time(signal_date, decision_policy, decision_time)
    available_ok = _available_time_ok(available_time, effective_decision_time)
    local_cache = "local_market_cache" in " ".join(
        [_string(update.get("evidence_source")), _string(update.get("evidence_path")), _string(update.get("evidence_reference")), _string(update.get("source"))]
    ).lower()
    strict_pass = _bool(strict.get("checklist_pass"))
    strict_status = _string(strict.get("checklist_status")) or "STRICT_VALIDATION_MISSING"
    strict_blockers = _string(strict.get("blocker_reason"))
    relaxed: list[str] = []
    if _bool(strict.get("pit_timing_blocker")) and available_ok and decision_policy.upper() == "EOD_POST_CLOSE":
        relaxed.append("PIT_TIMING_BLOCKED")
    remaining = _remaining_blockers(strict, update, relaxed, local_cache)
    eod_pass = strict_pass or (not remaining and not _bool(strict.get("survivorship_blocker")))
    profile_is_reviewed_no_hit = profile.upper() == REVIEWED_NO_HIT_PROFILE_NAME
    reviewer_acceptance_present = _reviewer_acceptance_present(update)
    source_coverage_documented = profile_is_reviewed_no_hit and no_hit_policy_available
    query_window_documented = source_coverage_documented
    official_quotation_presence_supported = local_cache and available_ok
    no_hit_context_supported = (
        profile_is_reviewed_no_hit
        and official_quotation_presence_supported
        and source_coverage_documented
        and query_window_documented
        and reviewer_acceptance_present
    )
    no_hit_context = _no_hit_relaxed_context(update, no_hit_context_supported)
    reviewed_remaining = _reviewed_no_hit_remaining_blockers(
        remaining=remaining,
        update=update,
        no_hit_context_supported=no_hit_context_supported,
        source_coverage_documented=source_coverage_documented,
        query_window_documented=query_window_documented,
        reviewer_acceptance_present=reviewer_acceptance_present,
    )
    reviewed_pass = strict_pass or (profile_is_reviewed_no_hit and not reviewed_remaining)
    return {
        "comparison_id": comparison_id,
        "symbol": _string(update.get("symbol")),
        "signal_date": signal_date,
        "recommended_future_universe": _string(update.get("universe_name")),
        "profile_name": profile,
        "strict_status": strict_status,
        "eod_low_budget_status": "EOD_LOW_BUDGET_PASS_PREVIEW" if eod_pass else "EOD_LOW_BUDGET_BLOCKED",
        "reviewed_no_hit_status": "REVIEWED_NO_HIT_PASS_PREVIEW" if reviewed_pass else "REVIEWED_NO_HIT_BLOCKED",
        "strict_blockers": strict_blockers,
        "relaxed_blockers": ", ".join(relaxed),
        "no_hit_relaxed_context": ", ".join(no_hit_context),
        "remaining_blockers": "; ".join(reviewed_remaining if profile_is_reviewed_no_hit else remaining),
        "available_time": available_time,
        "decision_time": effective_decision_time,
        "available_time_within_decision_time": available_ok,
        "official_quotation_presence_supported": official_quotation_presence_supported,
        "same_day_market_cache_used_as_support": local_cache and available_ok,
        "active_context_supported_by_cache": local_cache and available_ok and bool(_string(update.get("is_suspended"))),
        "suspension_context_supported_by_cache": local_cache and available_ok and bool(_string(update.get("is_suspended"))),
        "no_hit_context_supported": no_hit_context_supported,
        "no_hit_not_delisted_context_supported": no_hit_context_supported,
        "no_hit_no_suspension_context_supported": no_hit_context_supported,
        "no_hit_no_st_context_supported": no_hit_context_supported and _string(update.get("universe_name")) == "stock_core",
        "reviewer_acceptance_required": profile_is_reviewed_no_hit,
        "reviewer_acceptance_present": reviewer_acceptance_present,
        "source_coverage_required": profile_is_reviewed_no_hit,
        "source_coverage_documented": source_coverage_documented,
        "query_window_documented": query_window_documented,
        "not_delisted_still_required": not strict_pass and not no_hit_context_supported,
        "st_no_st_still_required": _string(update.get("universe_name")) == "stock_core" and not strict_pass and not no_hit_context_supported,
        "survivorship_still_required": not _bool(update.get("survivorship_bias_resolved")),
        "survivorship_rationale_required": profile_is_reviewed_no_hit,
        "checklist_pass_under_strict": strict_pass,
        "checklist_pass_under_eod_low_budget": eod_pass,
        "checklist_pass_under_reviewed_no_hit_support": reviewed_pass,
        "approval_candidate_preview_only": eod_pass or reviewed_pass,
        "should_apply_approval": False,
        "no_pit_review_run": True,
        "no_export_readiness_run": True,
        "no_staging_run": True,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "comparison_only": True,
    }


def _remaining_blockers(strict: dict[str, Any], update: dict[str, Any], relaxed: list[str], local_cache: bool) -> list[str]:
    remaining: list[str] = []
    missing = [item.strip() for item in _string(strict.get("missing_required_fields")).split(",") if item.strip()]
    for field in missing:
        if field == "available_time" and "PIT_TIMING_BLOCKED" in relaxed:
            continue
        remaining.append(f"missing {field}")
    if _bool(strict.get("pit_timing_blocker")) and "PIT_TIMING_BLOCKED" not in relaxed:
        remaining.append("PIT timing blocked")
    if _bool(strict.get("survivorship_blocker")):
        remaining.append("survivorship unresolved")
    if _bool(strict.get("stock_st_blocker")):
        remaining.append("stock ST/no-ST evidence missing")
    if not _string(update.get("as_of_date")):
        remaining.append("as_of_date requires accepted EOD evidence snapshot")
    if not _string(update.get("is_active")):
        remaining.append("is_active requires reviewed EOD/local-source policy")
    if not _bool(update.get("survivorship_bias_resolved")):
        remaining.append("survivorship_bias_resolved remains false")
    if _string(update.get("universe_name")) == "stock_core" and not _string(update.get("is_st")):
        remaining.append("stock ST/no-ST remains required")
    if not local_cache and "PIT_TIMING_BLOCKED" in relaxed:
        remaining.append("same-day market cache support missing")
    return sorted(set(remaining))


def _reviewed_no_hit_remaining_blockers(
    *,
    remaining: list[str],
    update: dict[str, Any],
    no_hit_context_supported: bool,
    source_coverage_documented: bool,
    query_window_documented: bool,
    reviewer_acceptance_present: bool,
) -> list[str]:
    reviewed_remaining = list(remaining)
    if no_hit_context_supported:
        relaxable_fragments = [
            "not-delisted",
            "not_delisted",
            "ST/no-ST",
            "stock ST/no-ST",
            "suspension",
            "is_active requires reviewed EOD/local-source policy",
        ]
        reviewed_remaining = [
            item
            for item in reviewed_remaining
            if not any(fragment.lower() in item.lower() for fragment in relaxable_fragments)
        ]
    if not reviewer_acceptance_present:
        reviewed_remaining.append("reviewer acceptance missing for reviewed no-hit support")
    if not source_coverage_documented:
        reviewed_remaining.append("official no-hit source coverage not documented")
    if not query_window_documented:
        reviewed_remaining.append("official no-hit query window not documented")
    if not _bool(update.get("survivorship_bias_resolved")):
        reviewed_remaining.append("survivorship-bias rationale still required")
    return sorted(set(reviewed_remaining))


def _no_hit_relaxed_context(update: dict[str, Any], supported: bool) -> list[str]:
    if not supported:
        return []
    contexts = ["NOT_DELISTED_CONTEXT", "NO_SUSPENSION_CONTEXT"]
    if _string(update.get("universe_name")) == "stock_core":
        contexts.append("NO_ST_CONTEXT")
    return contexts


def _reviewer_acceptance_present(update: dict[str, Any]) -> bool:
    return all(
        _string(update.get(field))
        for field in ["reviewer", "reviewed_at", "review_reason", "evidence_source"]
    ) and bool(_string(update.get("evidence_reference")) or _string(update.get("evidence_path")))


def _read_validator_validation(validator_dir: Path) -> pd.DataFrame:
    path = validator_dir / "pit_evidence_checklist_validation.csv"
    if not path.exists():
        raise FileNotFoundError(f"Strict validator validation CSV not found: {path}")
    return read_csv_preserve_symbol_columns(path, keep_default_na=False)


def _read_policy_snapshot(policy_audit_dir: Path) -> pd.DataFrame:
    path = policy_audit_dir / "policy_profile_field_rules.csv"
    if path.exists():
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    return pd.DataFrame([{"field_name": "profile", "eod_post_close_low_budget_rule": "Policy audit file not found."}])


def _no_hit_policy_available(policy_audit_dir: Path) -> bool:
    return all(
        (policy_audit_dir / name).exists()
        for name in [
            "source_coverage_requirements.csv",
            "no_hit_inference_rules.csv",
            "blocker_decision_matrix.csv",
        ]
    )


def _relaxed_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        for blocker in [item.strip() for item in _string(row.get("relaxed_blockers")).split(",") if item.strip()]:
            rows.append({"comparison_id": row["comparison_id"], "signal_date": row["signal_date"], "symbol": row["symbol"], "blocker": blocker})
    return pd.DataFrame(rows, columns=["comparison_id", "signal_date", "symbol", "blocker"])


def _remaining_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        for blocker in [item.strip() for item in _string(row.get("remaining_blockers")).split(";") if item.strip()]:
            rows.append({"comparison_id": row["comparison_id"], "signal_date": row["signal_date"], "symbol": row["symbol"], "blocker": blocker})
    return pd.DataFrame(rows, columns=["comparison_id", "signal_date", "symbol", "blocker"])


def _summary(comparison_id: str, profile: str, frame: pd.DataFrame) -> pd.DataFrame:
    eod_pass = _true_count(frame, "checklist_pass_under_eod_low_budget")
    reviewed_pass = _true_count(frame, "checklist_pass_under_reviewed_no_hit_support")
    active_pass_column = _active_pass_column(profile)
    remaining = int((~frame[active_pass_column].map(_bool)).sum()) if not frame.empty else 0
    status = "PASS" if _true_count(frame, active_pass_column) and remaining == 0 else "WARN"
    return pd.DataFrame(
        [
            {
                "comparison_id": comparison_id,
                "status": status,
                "reference_profile_name": REFERENCE_PROFILE_NAME,
                "profile_name": profile,
                "profile_is_opt_in": True,
                "strict_default_unchanged": True,
                "row_count": len(frame),
                "strict_checklist_pass_count": _true_count(frame, "checklist_pass_under_strict"),
                "eod_low_budget_checklist_pass_count": eod_pass,
                "reviewed_no_hit_support_pass_count": reviewed_pass,
                "no_hit_context_supported_count": _true_count(frame, "no_hit_context_supported"),
                "reviewer_acceptance_required_count": _true_count(frame, "reviewer_acceptance_required"),
                "relaxed_blocker_count": int(frame["relaxed_blockers"].map(lambda x: bool(_string(x))).sum()) if not frame.empty else 0,
                "remaining_blocked_count": remaining,
                "approval_candidate_preview_count": _true_count(frame, active_pass_column),
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_artifacts(result: PitEvidencePolicyProfileComparisonResult) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result.comparison_frame.to_csv(result.artifact_paths["comparison_csv"], index=False)
    result.summary_frame.to_csv(result.artifact_paths["summary_csv"], index=False)
    result.relaxed_blocker_frame.to_csv(result.artifact_paths["relaxed_blocker_matrix"], index=False)
    result.remaining_blocker_frame.to_csv(result.artifact_paths["remaining_blocker_matrix"], index=False)
    result.policy_snapshot_frame.to_csv(result.artifact_paths["policy_snapshot"], index=False)
    metadata = {
        "comparison_id": result.comparison_id,
        "status": result.status,
        "reference_profile_name": result.reference_profile_name,
        "profile_name": result.profile_name,
        "profile_is_opt_in": result.profile_is_opt_in,
        "strict_default_unchanged": result.strict_default_unchanged,
        "row_count": result.row_count,
        "strict_checklist_pass_count": result.strict_checklist_pass_count,
        "eod_low_budget_checklist_pass_count": result.eod_low_budget_checklist_pass_count,
        "reviewed_no_hit_support_pass_count": result.reviewed_no_hit_support_pass_count,
        "no_hit_context_supported_count": result.no_hit_context_supported_count,
        "reviewer_acceptance_required_count": result.reviewer_acceptance_required_count,
        "relaxed_blocker_count": result.relaxed_blocker_count,
        "remaining_blocked_count": result.remaining_blocked_count,
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
        **result.audit_metadata,
    }
    result.artifact_paths["metadata"].write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")


def _render_report(result: PitEvidencePolicyProfileComparisonResult) -> str:
    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    return "\n".join(
        [
            "# PIT Evidence Policy Profile Comparison",
            "",
            SAFETY_STATEMENT,
            "",
            "## Summary",
            "",
            _dict_table(summary),
            "",
            "## Interpretation",
            "",
            "STRICT_PIT remains the reference/default profile. EOD_POST_CLOSE_LOW_BUDGET_PIT is opt-in and comparison-only.",
            "EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT is also opt-in and treats official no-hit evidence as reviewer-accepted supporting context only.",
            "Rows that pass this comparison are approval-candidate previews only; this workflow does not apply approval.",
            "",
        ]
    )


def _paths(output_dir: str | Path, comparison_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / comparison_id
    return {
        "artifact_dir": artifact_dir,
        "comparison_csv": artifact_dir / "pit_evidence_policy_profile_comparison.csv",
        "summary_csv": artifact_dir / "pit_evidence_policy_profile_summary.csv",
        "relaxed_blocker_matrix": artifact_dir / "relaxed_blocker_matrix.csv",
        "remaining_blocker_matrix": artifact_dir / "remaining_blocker_matrix.csv",
        "policy_snapshot": artifact_dir / "eod_post_close_policy_profile_snapshot.csv",
        "report": artifact_dir / "report.md",
        "metadata": artifact_dir / "metadata.json",
    }


def _decision_time(signal_date: str, decision_policy: str, decision_time: str | None) -> str:
    if not signal_date:
        return ""
    if decision_time and len(decision_time) > 8:
        return decision_time
    time_text = decision_time or ("16:00:00" if decision_policy.upper() == "EOD_POST_CLOSE" else "09:30:00")
    return f"{signal_date} {time_text}"


def _available_time_ok(available_time: str, decision_time: str) -> bool:
    available = _timestamp(available_time)
    decision = _timestamp(decision_time)
    return bool(available is not None and decision is not None and available <= decision)


def _timestamp(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed)


def _key(row: dict[str, Any]) -> str:
    return "|".join([_string(row.get("signal_date")), _string(row.get("symbol")), _string(row.get("universe_name"))])


def _finalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=columns)
    output = frame.copy()
    for column in columns:
        if column not in output.columns:
            output[column] = ""
    for column in [
        "available_time_within_decision_time",
        "same_day_market_cache_used_as_support",
        "active_context_supported_by_cache",
        "suspension_context_supported_by_cache",
        "official_quotation_presence_supported",
        "no_hit_context_supported",
        "no_hit_not_delisted_context_supported",
        "no_hit_no_suspension_context_supported",
        "no_hit_no_st_context_supported",
        "reviewer_acceptance_required",
        "reviewer_acceptance_present",
        "source_coverage_required",
        "source_coverage_documented",
        "query_window_documented",
        "not_delisted_still_required",
        "st_no_st_still_required",
        "survivorship_still_required",
        "survivorship_rationale_required",
        "checklist_pass_under_strict",
        "checklist_pass_under_eod_low_budget",
        "checklist_pass_under_reviewed_no_hit_support",
        "approval_candidate_preview_only",
        "should_apply_approval",
        "no_pit_review_run",
        "no_export_readiness_run",
        "no_staging_run",
        "no_universe_export",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "comparison_only",
    ]:
        if column in output.columns:
            output[column] = output[column].map(_bool).astype(object)
    return output[columns].reset_index(drop=True)


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_bool).sum())


def _active_pass_column(profile: str) -> str:
    if profile.upper() == REVIEWED_NO_HIT_PROFILE_NAME:
        return "checklist_pass_under_reviewed_no_hit_support"
    return "checklist_pass_under_eod_low_budget"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _string(value).lower() in {"1", "true", "yes", "y"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _comparison_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


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


def _dict_table(values: dict[str, Any]) -> str:
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)
