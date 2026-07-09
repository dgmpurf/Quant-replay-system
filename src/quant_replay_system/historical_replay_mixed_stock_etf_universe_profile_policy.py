"""Report-only mixed STOCK/ETF universe profile policy contract fixture.

This fixture creates deterministic synthetic profile-policy rows for the
selected 2024-04-02 / etf_core historical replay sample. It does not resolve
profile conflicts, prove universe membership, validate stock_profile, accept
official evidence, approve PIT admissibility, create replay input, or authorize
buy-review or trading.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = "mixed_stock_etf_universe_profile_policy_blocked_by_unsafe_output_root"
WORKFLOW_STAGE = "HISTORICAL_REPLAY_MIXED_STOCK_ETF_UNIVERSE_PROFILE_POLICY_FIXTURE_CREATED_REPORT_ONLY"
WORKFLOW_NAME = "historical_replay_mixed_stock_etf_universe_profile_policy"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/"
    "historical_replay_mixed_stock_etf_universe_profile_policy_legacy_etf_core_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Mixed STOCK/ETF Universe Profile Policy Checkpoint Documentation Bundle Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "policy_rows": "mixed_stock_etf_universe_profile_policy_rows.csv",
    "required_fields": "mixed_stock_etf_universe_profile_policy_required_fields.csv",
    "status_vocabulary": "mixed_stock_etf_universe_profile_policy_status_vocabulary.csv",
    "blocker_vocabulary": "mixed_stock_etf_universe_profile_policy_blocker_vocabulary.csv",
    "policy_matrix": "mixed_stock_etf_universe_profile_policy_matrix.csv",
    "safety_flags": "mixed_stock_etf_universe_profile_policy_safety_flags.json",
    "report": "mixed_stock_etf_universe_profile_policy_report.md",
}

SAFETY_FALSE_FIELDS = [
    "profile_conflict_resolved",
    "universe_membership_approved",
    "stock_profile_validated",
    "official_source_hierarchy_approved",
    "official_evidence_collection_started",
    "official_evidence_collection_approved",
    "official_evidence_accepted",
    "official_evidence_closed",
    "official_status_evidence_closed",
    "pit_evidence_closed",
    "pit_admissibility_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "replay_decision_freeze_allowed",
    "forward_labels_created",
    "training_dataset_created",
    "metric_computation_performed",
    "model_training_performed",
    "stock_profile_validation_created",
    "paper_expansion_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "current_candidates_executed",
    "snapshot_built",
    "signal_semantics_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

POSITIVE_CONTEXT_FLAGS = {
    "report_only": True,
    "diagnostic_only": True,
    "local_only": True,
    "synthetic_only": True,
    "selected_sample_context_only": True,
    "mixed_stock_etf_profile_policy_fixture_only": True,
}

REQUIRED_PROFILE_POLICY_FIELDS = [
    "profile_policy_row_id",
    "historical_decision_date",
    "universe_name",
    "selected_symbol",
    "instrument_type",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict",
    "profile_policy_status",
    "universe_membership_evidence_required",
    "official_status_evidence_required",
    "st_policy_family_required",
    "etf_not_applicable_policy_required",
    "profile_policy_reviewer_required",
    "profile_policy_reviewer_alias",
    "profile_policy_reviewer_scope",
    "profile_policy_rationale",
    "profile_policy_limitation_note",
    "profile_policy_downstream_use_policy",
    "profile_policy_no_hit_override_allowed",
    "profile_policy_pit_approval_allowed",
    "profile_policy_replay_readiness_allowed",
    "profile_policy_buy_review_allowed",
    "profile_policy_trading_allowed",
    "no_hit_context_can_resolve_profile_conflict",
    "legacy_universe_label_is_universe_proof",
    "recommended_profile_is_stock_profile_validation",
    "same_day_quote_is_official_status_proof",
    "forward_return_used_in_decision_context",
    "universe_membership_approved",
    "official_status_evidence_accepted",
    "profile_conflict_resolved",
    "stock_profile_validated",
    "pit_admissibility_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "blocker_reason",
]

STATUS_VOCABULARY = [
    "unresolved_profile_conflict",
    "profile_aligned_context_only_not_universe_proof",
    "stock_profile_policy_required",
    "etf_profile_policy_required",
    "rejected_by_missing_instrument_type_evidence",
    "rejected_by_missing_universe_membership_evidence",
    "rejected_by_missing_official_status_evidence",
    "rejected_by_legacy_label_only",
    "accepted_for_policy_context_only_not_pit_approved",
]

BLOCKER_VOCABULARY = [
    "blocker_legacy_universe_label_used_as_universe_proof",
    "blocker_recommended_profile_used_as_stock_profile_validation",
    "blocker_profile_conflict_hidden_or_removed",
    "blocker_missing_instrument_type_evidence",
    "blocker_missing_universe_membership_evidence",
    "blocker_missing_official_status_evidence",
    "blocker_missing_stock_st_no_st_evidence",
    "blocker_missing_etf_st_not_applicable_policy",
    "blocker_no_hit_used_to_resolve_profile_conflict",
    "blocker_no_hit_used_as_universe_proof",
    "blocker_no_hit_used_as_official_evidence",
    "blocker_same_day_quote_used_as_status_proof",
    "blocker_forward_return_used_in_decision_context",
    "blocker_profile_policy_used_as_pit_approval",
    "blocker_profile_policy_used_as_replay_readiness",
    "blocker_profile_policy_used_as_buy_review",
    "blocker_profile_policy_used_as_trading_permission",
    "blocker_missing_profile_policy_reviewer_scope",
    "blocker_private_reviewer_identity_disclosed",
    "blocker_forbidden_downstream_flag",
]

STOCK_ROW_BLOCKERS = [
    "blocker_profile_conflict_hidden_or_removed",
    "blocker_missing_universe_membership_evidence",
    "blocker_missing_official_status_evidence",
    "blocker_missing_stock_st_no_st_evidence",
    "blocker_missing_profile_policy_reviewer_scope",
]
ETF_ROW_BLOCKERS = [
    "blocker_missing_universe_membership_evidence",
    "blocker_missing_official_status_evidence",
    "blocker_missing_etf_st_not_applicable_policy",
    "blocker_missing_profile_policy_reviewer_scope",
]

SELECTED_ROWS = [
    ("000001", "STOCK", "stock_core", True),
    ("000002", "STOCK", "stock_core", True),
    ("159915", "ETF", "etf_core", False),
    ("300750", "STOCK", "stock_core", True),
    ("510300", "ETF", "etf_core", False),
    ("600000", "STOCK", "stock_core", True),
    ("600519", "STOCK", "stock_core", True),
    ("601318", "STOCK", "stock_core", True),
    ("688981", "STOCK", "stock_core", True),
]

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


@dataclass(frozen=True)
class HistoricalReplayMixedStockEtfUniverseProfilePolicyResult:
    run_id: str
    status: str
    health_status: str
    workflow_stage: str
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]


def run_historical_replay_mixed_stock_etf_universe_profile_policy(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    historical_decision_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayMixedStockEtfUniverseProfilePolicyResult:
    """Create deterministic synthetic mixed STOCK/ETF profile-policy artifacts."""

    root_path = Path(root)
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    _validate_output_root(output_root)
    if run_id is None:
        run_id = _generate_run_id(root_path, historical_decision_date, universe_name)
    _validate_run_id(run_id)

    output_root_resolved = output_root.resolve()
    artifact_dir = (output_root / run_id).resolve()
    if not _is_relative_to(artifact_dir, output_root_resolved):
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: output path escapes requested root")

    rows = _policy_rows(run_id, historical_decision_date, universe_name)
    metadata = _metadata(
        run_id=run_id,
        historical_decision_date=historical_decision_date,
        universe_name=universe_name,
        rows=rows,
    )
    paths = _paths(artifact_dir)
    metadata["artifact_paths"] = {key: filename for key, filename in OUTPUT_FILES.items()}
    metadata["report_path"] = OUTPUT_FILES["report"]

    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["policy_rows"], rows, REQUIRED_PROFILE_POLICY_FIELDS)
    _write_csv(paths["required_fields"], _required_field_rows(), ["field_name", "required", "default_value", "blocker_if_missing", "notes"])
    _write_csv(paths["status_vocabulary"], _status_rows(), ["status", "allowed_for_current_fixture_rows", "meaning", "forbidden_interpretation"])
    _write_csv(paths["blocker_vocabulary"], _blocker_rows(), ["blocker", "category", "meaning"])
    _write_csv(paths["policy_matrix"], _policy_matrix_rows(), ["policy_area", "rule", "default_behavior", "forbidden_interpretation"])
    _write_json(paths["safety_flags"], _safety_flags())
    paths["report"].write_text(_report(metadata), encoding="utf-8")

    return HistoricalReplayMixedStockEtfUniverseProfilePolicyResult(
        run_id=run_id,
        status=STATUS_CREATED,
        health_status="PASS",
        workflow_stage=WORKFLOW_STAGE,
        artifact_paths=paths,
        metadata=metadata,
    )


def _policy_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS:
        is_stock = instrument_type == "STOCK"
        rows.append(
            {
                "profile_policy_row_id": f"{run_id}_{symbol}_mixed_profile_policy",
                "historical_decision_date": decision_date,
                "universe_name": universe_name,
                "selected_symbol": symbol,
                "instrument_type": instrument_type,
                "legacy_universe_label": universe_name,
                "recommended_profile": recommended_profile,
                "profile_conflict": _bool_text(profile_conflict),
                "profile_policy_status": (
                    "unresolved_profile_conflict"
                    if is_stock
                    else "profile_aligned_context_only_not_universe_proof"
                ),
                "universe_membership_evidence_required": "true",
                "official_status_evidence_required": "true",
                "st_policy_family_required": (
                    "stock_st_no_st_evidence_required" if is_stock else "false"
                ),
                "etf_not_applicable_policy_required": _bool_text(not is_stock),
                "profile_policy_reviewer_required": "true",
                "profile_policy_reviewer_alias": "missing",
                "profile_policy_reviewer_scope": "missing",
                "profile_policy_rationale": "missing",
                "profile_policy_limitation_note": "template_placeholder_only",
                "profile_policy_downstream_use_policy": "context_only_not_evidence",
                "profile_policy_no_hit_override_allowed": "false",
                "profile_policy_pit_approval_allowed": "false",
                "profile_policy_replay_readiness_allowed": "false",
                "profile_policy_buy_review_allowed": "false",
                "profile_policy_trading_allowed": "false",
                "no_hit_context_can_resolve_profile_conflict": "false",
                "legacy_universe_label_is_universe_proof": "false",
                "recommended_profile_is_stock_profile_validation": "false",
                "same_day_quote_is_official_status_proof": "false",
                "forward_return_used_in_decision_context": "false",
                "universe_membership_approved": "false",
                "official_status_evidence_accepted": "false",
                "profile_conflict_resolved": "false",
                "stock_profile_validated": "false",
                "pit_admissibility_approved": "false",
                "active_replay_input": "false",
                "replay_execution_allowed": "false",
                "buy_review_allowed": "false",
                "trading_allowed": "false",
                "blocker_reason": ";".join(STOCK_ROW_BLOCKERS if is_stock else ETF_ROW_BLOCKERS),
            }
        )
    return rows


def _required_field_rows() -> list[dict[str, str]]:
    defaults = _policy_rows("example", "2024-04-02", "etf_core")[0]
    return [
        {
            "field_name": field,
            "required": "true",
            "default_value": defaults.get(field, ""),
            "blocker_if_missing": "true" if field in _blocker_required_fields() else "false",
            "notes": _field_note(field),
        }
        for field in REQUIRED_PROFILE_POLICY_FIELDS
    ]


def _blocker_required_fields() -> set[str]:
    return {
        "selected_symbol",
        "instrument_type",
        "legacy_universe_label",
        "recommended_profile",
        "profile_conflict",
        "profile_policy_status",
        "universe_membership_evidence_required",
        "official_status_evidence_required",
        "profile_policy_reviewer_alias",
        "profile_policy_reviewer_scope",
        "blocker_reason",
    }


def _field_note(field: str) -> str:
    if field == "legacy_universe_label":
        return "Historical sample context only; not universe membership proof."
    if field == "recommended_profile":
        return "Policy hint only; not stock_profile validation."
    if field == "profile_conflict":
        return "Must remain visible; current fixture does not resolve conflicts."
    if field.endswith("_allowed") or field.endswith("_approved") or field in SAFETY_FALSE_FIELDS:
        return "Must remain false; no downstream approval is created."
    return "Synthetic report-only profile-policy field."


def _status_rows() -> list[dict[str, str]]:
    meanings = {
        "unresolved_profile_conflict": "STOCK row remains unresolved under legacy etf_core context.",
        "profile_aligned_context_only_not_universe_proof": "ETF row profile hint aligns with legacy context but does not prove universe membership.",
        "stock_profile_policy_required": "Future STOCK-specific profile policy is required.",
        "etf_profile_policy_required": "Future ETF-specific profile policy is required.",
        "rejected_by_missing_instrument_type_evidence": "Rejected because instrument type evidence is missing.",
        "rejected_by_missing_universe_membership_evidence": "Rejected because universe membership evidence is missing.",
        "rejected_by_missing_official_status_evidence": "Rejected because official status evidence is missing.",
        "rejected_by_legacy_label_only": "Rejected because legacy label alone was used as evidence.",
        "accepted_for_policy_context_only_not_pit_approved": "Future bounded context-only status; not evidence and not PIT approval.",
    }
    allowed_current = {"unresolved_profile_conflict", "profile_aligned_context_only_not_universe_proof"}
    return [
        {
            "status": status,
            "allowed_for_current_fixture_rows": _bool_text(status in allowed_current),
            "meaning": meanings[status],
            "forbidden_interpretation": "not universe proof, not official evidence, not stock_profile validation, not PIT approval, not replay readiness, not buy-review, not trading",
        }
        for status in STATUS_VOCABULARY
    ]


def _blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker": blocker,
            "category": _blocker_category(blocker),
            "meaning": "Blocks profile policy from evidence, PIT, replay, buy-review, or trading interpretation.",
        }
        for blocker in BLOCKER_VOCABULARY
    ]


def _blocker_category(blocker: str) -> str:
    if "universe" in blocker or "legacy" in blocker:
        return "universe_membership"
    if "stock" in blocker or "etf" in blocker or "profile" in blocker:
        return "profile_policy"
    if "no_hit" in blocker:
        return "no_hit_boundary"
    if "quote" in blocker or "forward_return" in blocker:
        return "pit_boundary"
    if "reviewer" in blocker:
        return "reviewer_authority"
    return "forbidden_downstream"


def _policy_matrix_rows() -> list[dict[str, str]]:
    return [
        {
            "policy_area": "legacy_label_boundary",
            "rule": "legacy_universe_label is context only",
            "default_behavior": "legacy_etf_core_visible_not_universe_proof",
            "forbidden_interpretation": "no universe membership approval",
        },
        {
            "policy_area": "recommended_profile_boundary",
            "rule": "recommended_profile is a policy hint only",
            "default_behavior": "stock_core_or_etf_core_route_hint_only",
            "forbidden_interpretation": "no stock_profile validation",
        },
        {
            "policy_area": "no_hit_boundary",
            "rule": "no-hit context cannot resolve profile conflict",
            "default_behavior": "no_hit_override_allowed_false",
            "forbidden_interpretation": "no no-hit evidence acceptance",
        },
        {
            "policy_area": "quotation_boundary",
            "rule": "same-day quote is not official status proof",
            "default_behavior": "official_status_evidence_required",
            "forbidden_interpretation": "no official evidence acceptance",
        },
        {
            "policy_area": "downstream_boundary",
            "rule": "profile policy remains report-only",
            "default_behavior": "all downstream safety flags remain false",
            "forbidden_interpretation": "no PIT approval, replay, buy-review, or trading",
        },
    ]


def _metadata(
    *,
    run_id: str,
    historical_decision_date: str,
    universe_name: str,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    safety = _safety_flags()
    profile_policy_accepted_count = sum(
        row["profile_policy_status"] == "accepted_for_policy_context_only_not_pit_approved"
        for row in rows
    )
    no_hit_row_count = len(rows)
    not_accepted_count = len(rows) - profile_policy_accepted_count
    return {
        **safety,
        "run_id": run_id,
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "runtime_status": STATUS_CREATED,
        "health_status": "PASS",
        "historical_decision_date": historical_decision_date,
        "universe_name": universe_name,
        "row_count": len(SELECTED_ROWS),
        "stock_row_count": sum(row[1] == "STOCK" for row in SELECTED_ROWS),
        "etf_row_count": sum(row[1] == "ETF" for row in SELECTED_ROWS),
        "profile_conflict_count": sum(row[3] for row in SELECTED_ROWS),
        "profile_aligned_context_count": sum(not row[3] for row in SELECTED_ROWS),
        "unresolved_profile_conflict_count": sum(
            row["profile_policy_status"] == "unresolved_profile_conflict" for row in rows
        ),
        "profile_policy_accepted_count": profile_policy_accepted_count,
        "no_hit_row_count": no_hit_row_count,
        "not_accepted_count": not_accepted_count,
        "accepted_context_count": profile_policy_accepted_count,
        "universe_membership_approved_count": sum(
            _truthy_text(row.get("universe_membership_approved")) for row in rows
        ),
        "official_status_evidence_accepted_count": sum(
            _truthy_text(row.get("official_status_evidence_accepted")) for row in rows
        ),
        "row_with_blocker_count": sum(bool(row["blocker_reason"]) for row in rows),
        "survivorship_warning_count": len(rows),
        "safety_true_count": sum(1 for field in SAFETY_FALSE_FIELDS if safety[field]),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }


def _safety_flags() -> dict[str, bool]:
    return {**{field: False for field in SAFETY_FALSE_FIELDS}, **POSITIVE_CONTEXT_FLAGS}


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _report(metadata: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Historical Replay Mixed STOCK/ETF Universe Profile Policy Fixture Report",
            "",
            "This fixture is report-only, diagnostic-only, local-only, and synthetic-only.",
            "It records mixed STOCK/ETF profile-policy contract rows only.",
            "Profile conflicts are not resolved, universe membership is not approved, and stock_profile is not validated.",
            "No row authorizes PIT approval, replay execution, buy-review, trading, or protected data writes.",
            "",
            f"- Run id: `{metadata['run_id']}`",
            f"- Historical decision date: `{metadata['historical_decision_date']}`",
            f"- Universe: `{metadata['universe_name']}`",
            f"- Row count: `{metadata['row_count']}`",
            f"- STOCK rows: `{metadata['stock_row_count']}`",
            f"- ETF rows: `{metadata['etf_row_count']}`",
            f"- Profile conflicts: `{metadata['profile_conflict_count']}`",
            f"- Profile policy accepted count: `{metadata['profile_policy_accepted_count']}`",
            f"- No-hit row count: `{metadata['no_hit_row_count']}`",
            f"- Not accepted count: `{metadata['not_accepted_count']}`",
            f"- Accepted context count: `{metadata['accepted_context_count']}`",
            f"- Universe membership approved count: `{metadata['universe_membership_approved_count']}`",
            f"- Survivorship warning count: `{metadata['survivorship_warning_count']}`",
            f"- Safety true count: `{metadata['safety_true_count']}`",
            f"- Recommended next task: `{RECOMMENDED_NEXT_TASK}`",
            "",
        ]
    )


def _validate_output_root(output_root: Path) -> None:
    parts = tuple(part.lower() for part in output_root.parts)
    for protected in PROTECTED_PATH_PARTS:
        for index in range(0, max(len(parts) - len(protected) + 1, 0)):
            if parts[index : index + len(protected)] == protected:
                raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: {output_root}")


def _validate_run_id(run_id: str) -> None:
    if any(part in run_id for part in ("..", "/", "\\")) or not run_id.strip():
        raise ValueError("invalid run_id")


def _generate_run_id(root: Path, decision_date: str, universe_name: str) -> str:
    digest = hashlib.sha256(f"{root}|{decision_date}|{universe_name}|{WORKFLOW_NAME}".encode("utf-8")).hexdigest()
    return digest[:12]


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _truthy_text(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
