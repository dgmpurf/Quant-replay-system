"""Report-only reviewer no-hit acceptance contract fixture.

This fixture creates deterministic synthetic no-hit acceptance contract rows for
the selected 2024-04-02 / etf_core historical replay sample. It does not accept
no-hit context as evidence and does not authorize PIT approval, replay, labels,
models, stock profiles, buy-review, or trading.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "REVIEWER_NO_HIT_ACCEPTANCE_FIXTURE_CREATED_REPORT_ONLY"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = "reviewer_no_hit_acceptance_fixture_blocked_by_unsafe_output_root"
WORKFLOW_STAGE = "HISTORICAL_REPLAY_REVIEWER_NO_HIT_ACCEPTANCE_FIXTURE_CREATED_REPORT_ONLY"
WORKFLOW_NAME = "historical_replay_reviewer_no_hit_acceptance_fixture"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/historical_replay_reviewer_no_hit_acceptance_fixture_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Mixed STOCK/ETF Universe Profile Policy Planning for legacy etf_core Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "reviewer_no_hit_acceptance_rows": "reviewer_no_hit_acceptance_rows.csv",
    "required_fields": "reviewer_no_hit_acceptance_required_fields.csv",
    "status_vocabulary": "reviewer_no_hit_acceptance_status_vocabulary.csv",
    "blocker_vocabulary": "reviewer_no_hit_acceptance_blocker_vocabulary.csv",
    "policy_matrix": "reviewer_no_hit_acceptance_policy_matrix.csv",
    "safety_flags": "reviewer_no_hit_acceptance_safety_flags.json",
    "report": "reviewer_no_hit_acceptance_fixture_report.md",
}

SAFETY_FALSE_FIELDS = [
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
    "no_hit_contract_fixture_only": True,
    "no_hit_context_accepted": False,
}

REQUIRED_NO_HIT_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict",
    "no_hit_review_needed",
    "no_hit_source_family",
    "no_hit_evidence_family",
    "no_hit_query_window_start",
    "no_hit_query_window_end",
    "no_hit_query_window_timezone",
    "no_hit_query_terms",
    "no_hit_query_method",
    "no_hit_result",
    "no_hit_result_reference",
    "no_hit_acceptance_status",
    "no_hit_reviewer_required",
    "reviewer_id_or_alias",
    "reviewer_role",
    "reviewer_scope",
    "reviewer_private_identity_disclosed",
    "no_hit_acceptance_rationale",
    "no_hit_limitation_note",
    "no_hit_decision_time_policy",
    "no_hit_conflict_policy",
    "no_hit_downstream_use_policy",
    "no_hit_context_accepted",
    "no_hit_used_as_source_reliability_score",
    "no_hit_used_as_official_evidence",
    "no_hit_used_as_pit_approval",
    "blocker_reason",
    "row_ready_for_review_context_only",
]

STATUS_VOCABULARY = [
    "not_accepted",
    "proposed_for_review_context_only",
    "rejected_by_scope",
    "rejected_by_missing_query_window",
    "rejected_by_post_decision_source",
    "rejected_by_conflicting_hit",
    "rejected_by_missing_reviewer_scope",
    "accepted_for_review_context_only_not_evidence",
    "accepted_for_manual_followup_only_not_pit_approved",
]

BLOCKER_VOCABULARY = [
    "blocker_missing_no_hit_source_family",
    "blocker_missing_no_hit_evidence_family",
    "blocker_missing_no_hit_query_window",
    "blocker_missing_no_hit_timezone",
    "blocker_missing_no_hit_query_terms",
    "blocker_missing_no_hit_result_reference",
    "blocker_missing_reviewer_alias",
    "blocker_missing_reviewer_role",
    "blocker_missing_reviewer_scope",
    "blocker_private_reviewer_identity_disclosed",
    "blocker_post_decision_query_window",
    "blocker_post_decision_source_reference",
    "blocker_conflicting_hit_found",
    "blocker_no_hit_used_as_source_reliability_score",
    "blocker_no_hit_used_as_official_evidence",
    "blocker_no_hit_used_as_pit_approval",
    "blocker_no_hit_used_to_override_source_lineage",
    "blocker_no_hit_used_to_override_survivorship",
    "blocker_no_hit_used_to_override_profile_conflict",
    "blocker_forbidden_downstream_flag",
]

DEFAULT_ROW_BLOCKERS = [
    "blocker_missing_no_hit_query_window",
    "blocker_missing_no_hit_timezone",
    "blocker_missing_no_hit_result_reference",
    "blocker_missing_reviewer_alias",
    "blocker_missing_reviewer_role",
    "blocker_missing_reviewer_scope",
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
class HistoricalReplayReviewerNoHitAcceptanceFixtureResult:
    run_id: str
    status: str
    health_status: str
    workflow_stage: str
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]


def run_historical_replay_reviewer_no_hit_acceptance_fixture(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    historical_decision_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayReviewerNoHitAcceptanceFixtureResult:
    """Create deterministic synthetic reviewer no-hit acceptance fixture artifacts."""

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

    rows = _no_hit_rows(run_id, historical_decision_date, universe_name)
    required_fields = _required_field_rows()
    status_rows = _status_rows()
    blocker_rows = _blocker_rows()
    policy_rows = _policy_rows()
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
    _write_csv(paths["reviewer_no_hit_acceptance_rows"], rows, REQUIRED_NO_HIT_FIELDS)
    _write_csv(paths["required_fields"], required_fields, ["field_name", "required", "default_value", "blocker_if_missing", "notes"])
    _write_csv(paths["status_vocabulary"], status_rows, ["status", "allowed_for_current_fixture_rows", "meaning", "forbidden_interpretation"])
    _write_csv(paths["blocker_vocabulary"], blocker_rows, ["blocker", "category", "meaning"])
    _write_csv(paths["policy_matrix"], policy_rows, ["policy_area", "rule", "default_behavior", "forbidden_interpretation"])
    _write_json(paths["safety_flags"], _safety_flags())
    paths["report"].write_text(_report(metadata), encoding="utf-8")

    return HistoricalReplayReviewerNoHitAcceptanceFixtureResult(
        run_id=run_id,
        status=STATUS_CREATED,
        health_status="PASS",
        workflow_stage=WORKFLOW_STAGE,
        artifact_paths=paths,
        metadata=metadata,
    )


def _no_hit_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    return [
        {
            "template_row_id": f"{run_id}_{symbol}_reviewer_no_hit",
            "historical_decision_date": decision_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "legacy_universe_label": universe_name,
            "recommended_profile": recommended_profile,
            "profile_conflict": _bool_text(profile_conflict),
            "no_hit_review_needed": "true",
            "no_hit_source_family": "official_manual_evidence_collection_template",
            "no_hit_evidence_family": "reviewer_no_hit_handoff",
            "no_hit_query_window_start": "missing",
            "no_hit_query_window_end": "missing",
            "no_hit_query_window_timezone": "missing",
            "no_hit_query_terms": "template_placeholder_only",
            "no_hit_query_method": "template_placeholder_only",
            "no_hit_result": "missing",
            "no_hit_result_reference": "missing",
            "no_hit_acceptance_status": "not_accepted",
            "no_hit_reviewer_required": "true",
            "reviewer_id_or_alias": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "reviewer_private_identity_disclosed": "no",
            "no_hit_acceptance_rationale": "missing",
            "no_hit_limitation_note": "template_placeholder_only",
            "no_hit_decision_time_policy": "not_reviewed",
            "no_hit_conflict_policy": "not_reviewed",
            "no_hit_downstream_use_policy": "context_only_not_evidence",
            "no_hit_context_accepted": "false",
            "no_hit_used_as_source_reliability_score": "false",
            "no_hit_used_as_official_evidence": "false",
            "no_hit_used_as_pit_approval": "false",
            "blocker_reason": ";".join(DEFAULT_ROW_BLOCKERS),
            "row_ready_for_review_context_only": "false",
        }
        for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS
    ]


def _required_field_rows() -> list[dict[str, str]]:
    defaults = _no_hit_rows("example", "2024-04-02", "etf_core")[0]
    rows = []
    for field in REQUIRED_NO_HIT_FIELDS:
        rows.append(
            {
                "field_name": field,
                "required": "true",
                "default_value": defaults.get(field, ""),
                "blocker_if_missing": "true" if field in _blocker_required_fields() else "false",
                "notes": _field_note(field),
            }
        )
    return rows


def _blocker_required_fields() -> set[str]:
    return {
        "no_hit_source_family",
        "no_hit_evidence_family",
        "no_hit_query_window_start",
        "no_hit_query_window_end",
        "no_hit_query_window_timezone",
        "no_hit_query_terms",
        "no_hit_result_reference",
        "reviewer_id_or_alias",
        "reviewer_role",
        "reviewer_scope",
    }


def _field_note(field: str) -> str:
    if field == "no_hit_context_accepted":
        return "Default false; reviewer no-hit context cannot close evidence gaps or become official evidence."
    if field.startswith("no_hit_used_as_"):
        return "Must remain false; no-hit context is not a substitute for source lineage or PIT approval."
    if field == "reviewer_private_identity_disclosed":
        return "Must be no; public artifacts use aliases only."
    return "Synthetic contract fixture field; current rows are not accepted."


def _status_rows() -> list[dict[str, str]]:
    meanings = {
        "not_accepted": "Current fixture default; no reviewer no-hit context has been accepted.",
        "proposed_for_review_context_only": "Future reviewer handoff proposal only.",
        "rejected_by_scope": "Rejected because reviewer scope does not cover the claim.",
        "rejected_by_missing_query_window": "Rejected because no-hit query timing is missing.",
        "rejected_by_post_decision_source": "Rejected because timing is after the historical decision.",
        "rejected_by_conflicting_hit": "Rejected because a conflicting hit exists.",
        "rejected_by_missing_reviewer_scope": "Rejected because reviewer authority is missing.",
        "accepted_for_review_context_only_not_evidence": "Future bounded reviewer context only; still not official evidence.",
        "accepted_for_manual_followup_only_not_pit_approved": "Future manual follow-up only; no PIT approval.",
    }
    return [
        {
            "status": status,
            "allowed_for_current_fixture_rows": _bool_text(status == "not_accepted"),
            "meaning": meanings[status],
            "forbidden_interpretation": "not official evidence, not PIT approval, not replay readiness, not buy-review, not trading",
        }
        for status in STATUS_VOCABULARY
    ]


def _blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker": blocker,
            "category": _blocker_category(blocker),
            "meaning": "Blocks reviewer no-hit context from any evidence or downstream interpretation.",
        }
        for blocker in BLOCKER_VOCABULARY
    ]


def _blocker_category(blocker: str) -> str:
    if "reviewer" in blocker:
        return "reviewer_authority"
    if "query" in blocker or "timezone" in blocker:
        return "no_hit_query"
    if "downstream" in blocker or "used_as" in blocker or "override" in blocker:
        return "forbidden_downstream"
    if "source" in blocker:
        return "source_lineage"
    return "reviewer_no_hit_acceptance"


def _policy_rows() -> list[dict[str, str]]:
    return [
        {
            "policy_area": "context_boundary",
            "rule": "reviewer no-hit context cannot close evidence gaps",
            "default_behavior": "context_only_not_evidence",
            "forbidden_interpretation": "no official evidence acceptance or PIT approval",
        },
        {
            "policy_area": "identity_boundary",
            "rule": "reviewer private identity must not be disclosed",
            "default_behavior": "alias_required_missing_by_default",
            "forbidden_interpretation": "no private reviewer identity in public artifacts",
        },
        {
            "policy_area": "query_boundary",
            "rule": "missing query window, timezone, terms, or result reference blocks acceptance",
            "default_behavior": "all current rows carry blockers",
            "forbidden_interpretation": "not a completed no-hit search",
        },
        {
            "policy_area": "downstream_boundary",
            "rule": "no-hit context cannot override source lineage, survivorship, profile conflict, or PIT issues",
            "default_behavior": "all downstream safety flags remain false",
            "forbidden_interpretation": "no replay input, buy-review, performance validation, or trading",
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
    not_accepted_count = sum(row["no_hit_acceptance_status"] == "not_accepted" for row in rows)
    accepted_context_count = sum(_truthy_text(row.get("no_hit_context_accepted")) for row in rows)
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
        "no_hit_row_count": len(rows),
        "not_accepted_count": not_accepted_count,
        "accepted_context_count": accepted_context_count,
        "row_with_blocker_count": sum(bool(row["blocker_reason"]) for row in rows),
        "profile_conflict_count": sum(row[3] for row in SELECTED_ROWS),
        "survivorship_warning_count": len(SELECTED_ROWS),
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
            "# Historical Replay Reviewer No-Hit Acceptance Fixture Report",
            "",
            "This fixture is report-only, diagnostic-only, local-only, and synthetic-only.",
            "It records a reviewer no-hit acceptance contract surface only.",
            "Current no-hit rows are not accepted and cannot serve as official evidence.",
            "No row authorizes PIT approval, replay execution, buy-review, trading, or protected data writes.",
            "",
            f"- Run id: `{metadata['run_id']}`",
            f"- Historical decision date: `{metadata['historical_decision_date']}`",
            f"- Universe: `{metadata['universe_name']}`",
            f"- No-hit rows: `{metadata['no_hit_row_count']}`",
            f"- Not accepted rows: `{metadata['not_accepted_count']}`",
            f"- Accepted context rows: `{metadata['accepted_context_count']}`",
            f"- Rows with blockers: `{metadata['row_with_blocker_count']}`",
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
