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
    "strict_blockers",
    "relaxed_blockers",
    "remaining_blockers",
    "available_time",
    "decision_time",
    "available_time_within_decision_time",
    "same_day_market_cache_used_as_support",
    "active_context_supported_by_cache",
    "suspension_context_supported_by_cache",
    "not_delisted_still_required",
    "st_no_st_still_required",
    "survivorship_still_required",
    "checklist_pass_under_strict",
    "checklist_pass_under_eod_low_budget",
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
    rows = [
        _compare_row(
            comparison_id=comparison_id,
            update=row,
            strict=validation_by_key.get(_key(row), {}),
            profile=profile,
            decision_policy=decision_policy,
            decision_time=decision_time,
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
        relaxed_blocker_count=len(relaxed_frame),
        remaining_blocked_count=int((~comparison_frame["checklist_pass_under_eod_low_budget"].map(_bool)).sum())
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
    return {
        "comparison_id": comparison_id,
        "symbol": _string(update.get("symbol")),
        "signal_date": signal_date,
        "recommended_future_universe": _string(update.get("universe_name")),
        "profile_name": profile,
        "strict_status": strict_status,
        "eod_low_budget_status": "EOD_LOW_BUDGET_PASS_PREVIEW" if eod_pass else "EOD_LOW_BUDGET_BLOCKED",
        "strict_blockers": strict_blockers,
        "relaxed_blockers": ", ".join(relaxed),
        "remaining_blockers": "; ".join(remaining),
        "available_time": available_time,
        "decision_time": effective_decision_time,
        "available_time_within_decision_time": available_ok,
        "same_day_market_cache_used_as_support": local_cache and available_ok,
        "active_context_supported_by_cache": local_cache and available_ok and bool(_string(update.get("is_suspended"))),
        "suspension_context_supported_by_cache": local_cache and available_ok and bool(_string(update.get("is_suspended"))),
        "not_delisted_still_required": not strict_pass,
        "st_no_st_still_required": _string(update.get("universe_name")) == "stock_core" and not strict_pass,
        "survivorship_still_required": not _bool(update.get("survivorship_bias_resolved")),
        "checklist_pass_under_strict": strict_pass,
        "checklist_pass_under_eod_low_budget": eod_pass,
        "approval_candidate_preview_only": eod_pass,
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
    remaining = int((~frame["checklist_pass_under_eod_low_budget"].map(_bool)).sum()) if not frame.empty else 0
    status = "PASS" if eod_pass and remaining == 0 else "WARN"
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
                "relaxed_blocker_count": int(frame["relaxed_blockers"].map(lambda x: bool(_string(x))).sum()) if not frame.empty else 0,
                "remaining_blocked_count": remaining,
                "approval_candidate_preview_count": eod_pass,
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
        "not_delisted_still_required",
        "st_no_st_still_required",
        "survivorship_still_required",
        "checklist_pass_under_strict",
        "checklist_pass_under_eod_low_budget",
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
