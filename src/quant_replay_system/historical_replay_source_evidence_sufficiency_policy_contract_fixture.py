"""Synthetic source/evidence sufficiency policy contract fixture.

The fixture materializes governance vocabulary and negative proof only. It
does not read evidence, apply sufficiency, approve PIT, create replay input,
or authorize any downstream workflow.
"""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_CREATED_REPORT_ONLY"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = (
    "source_evidence_sufficiency_policy_contract_fixture_blocked_by_unsafe_output_root"
)
WORKFLOW_STAGE = (
    "HISTORICAL_REPLAY_SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_"
    "CREATED_REPORT_ONLY"
)
WORKFLOW_NAME = "historical_replay_source_evidence_sufficiency_policy_contract_fixture"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/"
    "historical_replay_source_evidence_sufficiency_policy_contract_fixture_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Source / Evidence Sufficiency Policy Contract Fixture "
    "Tag And Source Readiness Planning Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "selected_rows": "source_evidence_sufficiency_policy_rows.csv",
    "evidence_family_contract": (
        "source_evidence_sufficiency_policy_evidence_family_contract.csv"
    ),
    "required_fields": "source_evidence_sufficiency_policy_required_fields.csv",
    "status_vocabulary": (
        "source_evidence_sufficiency_policy_status_vocabulary.csv"
    ),
    "blocker_vocabulary": (
        "source_evidence_sufficiency_policy_blocker_vocabulary.csv"
    ),
    "timing_revision_matrix": (
        "source_evidence_sufficiency_policy_timing_revision_matrix.csv"
    ),
    "stock_etf_matrix": "source_evidence_sufficiency_policy_stock_etf_matrix.csv",
    "safety_flags": "source_evidence_sufficiency_policy_safety_flags.json",
    "report": "source_evidence_sufficiency_policy_contract_fixture_report.md",
}

SAFETY_FALSE_FIELDS = [
    "evidence_collected",
    "evidence_read_from_external_sources",
    "evidence_template_filled",
    "evidence_sufficiency_applied_to_selected_rows",
    "evidence_accepted",
    "evidence_closed",
    "no_hit_accepted_as_evidence",
    "profile_conflict_resolved",
    "universe_membership_approved",
    "stock_profile_validated",
    "pit_admissibility_approved",
    "active_replay_input_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "replay_decision_freeze_allowed",
    "forward_labels_created",
    "future_labels_joined",
    "training_dataset_created",
    "metric_computation_performed",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "paper_expansion_allowed",
    "real_buy_review_approved",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "broker_api_called",
    "broker_api_approved",
    "order_placed",
    "order_placement_approved",
    "message_sent",
    "message_delivery_approved",
    "trading_allowed",
    "external_api_called",
    "llm_api_called",
    "current_candidates_executed",
    "snapshot_built",
    "signal_semantics_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "docs_project_sources_created",
]

POSITIVE_SCOPE_FLAGS = {
    "report_only": True,
    "diagnostic_only": True,
    "local_only": True,
    "synthetic_only": True,
}

SELECTED_ROW_FIELDS = [
    "row_id",
    "historical_decision_date",
    "decision_timezone",
    "legacy_universe_label",
    "symbol",
    "instrument_type",
    "recommended_profile",
    "profile_conflict",
    "profile_policy_status",
    "selected_row_blockers",
    "selected_row_sufficiency_candidate",
    "selected_row_evidence_accepted",
    "selected_row_evidence_closed",
    "selected_row_pit_admissible",
    "selected_row_replay_ready",
]

EVIDENCE_FAMILY_CONTRACT_FIELDS = [
    "contract_row_id",
    "row_id",
    "evidence_family_id",
    "evidence_family_name",
    "instrument_applicability",
    "not_applicable_policy_required",
    "purpose",
    "eligible_source_classes",
    "authoritative_source_class_policy",
    "required_structural_fields",
    "evidence_presence",
    "source_eligibility_context",
    "publish_time_required",
    "available_time_required",
    "effective_time_required",
    "timezone_required",
    "revision_id_required",
    "historical_version_required",
    "source_reference_required",
    "source_hash_policy",
    "permission_class_required",
    "corroboration_policy",
    "reviewer_scope_required",
    "no_hit_allowed_as_context_only",
    "insufficiency_blockers",
    "sufficiency_candidate",
    "evidence_accepted",
    "evidence_closed",
    "pit_admissible",
    "replay_ready",
]

STATUS_VOCABULARY = [
    "evidence_family_context_only",
    "evidence_family_missing_required_fields",
    "evidence_family_blocked_by_source_eligibility",
    "evidence_family_blocked_by_timing",
    "evidence_family_blocked_by_revision",
    "evidence_family_blocked_by_permission",
    "evidence_family_blocked_by_survivorship",
    "evidence_family_sufficiency_candidate_not_accepted",
    "row_has_sufficiency_candidates_not_closed",
    "row_blocked_by_missing_evidence",
    "row_blocked_by_profile_conflict",
    "row_blocked_by_universe_membership",
    "row_blocked_by_timing",
    "row_blocked_by_revision",
    "row_blocked_by_permission",
    "row_blocked_by_survivorship",
    "instrument_not_applicable_policy_context_only",
]

BLOCKER_VOCABULARY = [
    "blocker_missing_eligible_source_class",
    "blocker_missing_required_structural_fields",
    "blocker_missing_source_reference",
    "blocker_missing_publish_time",
    "blocker_missing_available_time",
    "blocker_missing_effective_time",
    "blocker_missing_timezone",
    "blocker_post_decision_evidence",
    "blocker_undated_evidence",
    "blocker_timezone_ambiguity",
    "blocker_missing_revision_id",
    "blocker_missing_historical_version",
    "blocker_superseded_evidence_unresolved",
    "blocker_missing_source_provenance",
    "blocker_unsafe_full_hash_disclosure",
    "blocker_missing_permission_class",
    "blocker_forbidden_or_restricted_permission",
    "blocker_missing_corroboration",
    "blocker_missing_reviewer_scope",
    "blocker_reviewer_private_identity_disclosed",
    "blocker_no_hit_misuse",
    "blocker_same_day_quotation_misuse",
    "blocker_current_webpage_used_as_historical_proof",
    "blocker_unresolved_profile_conflict",
    "blocker_missing_universe_membership_evidence",
    "blocker_missing_constituent_version_evidence",
    "blocker_missing_survivorship_rationale",
    "blocker_forbidden_downstream_flag",
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

COMMON_ROW_BLOCKERS = [
    "blocker_missing_required_structural_fields",
    "blocker_missing_universe_membership_evidence",
    "blocker_missing_available_time",
    "blocker_missing_revision_id",
    "blocker_missing_permission_class",
    "blocker_missing_survivorship_rationale",
]

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


def _family(
    family_id: str,
    name: str,
    purpose: str,
    sources: str,
    structural_fields: str,
    blockers: str,
    *,
    publish: bool = True,
    available: bool = True,
    effective: bool = True,
    timezone: bool = True,
    revision: bool = True,
    historical: bool = True,
    reference: bool = True,
    permission: bool = True,
    reviewer: bool = True,
    no_hit: bool = False,
    authority: str = "family_specific_authority_required",
    corroboration: str = "independent_corroboration_when_incomplete_or_conflicting",
) -> dict[str, Any]:
    return {
        "evidence_family_id": family_id,
        "evidence_family_name": name,
        "purpose": purpose,
        "eligible_source_classes": sources,
        "authoritative_source_class_policy": authority,
        "required_structural_fields": structural_fields,
        "publish_time_required": publish,
        "available_time_required": available,
        "effective_time_required": effective,
        "timezone_required": timezone,
        "revision_id_required": revision,
        "historical_version_required": historical,
        "source_reference_required": reference,
        "source_hash_policy": "preview_only_or_absent",
        "permission_class_required": permission,
        "corroboration_policy": corroboration,
        "reviewer_scope_required": reviewer,
        "no_hit_allowed_as_context_only": no_hit,
        "insufficiency_blockers": blockers,
    }


EVIDENCE_FAMILIES = [
    _family(
        "EF01",
        "instrument-type identity",
        "Distinguish STOCK from ETF.",
        "exchange_security_master;official_issuer_or_fund_disclosure",
        "symbol;market;instrument_type;source_id;source_type;source_reference",
        "blocker_missing_eligible_source_class;blocker_missing_required_structural_fields;"
        "blocker_missing_source_reference;blocker_missing_revision_id",
    ),
    _family(
        "EF02",
        "listed / active status",
        "Define date-specific listed or active context.",
        "exchange_listing_files;official_exchange_notices",
        "symbol;listed_status;covered_date;source_id;source_reference",
        "blocker_missing_eligible_source_class;blocker_missing_required_structural_fields;"
        "blocker_missing_source_reference;blocker_missing_available_time",
    ),
    _family(
        "EF03",
        "delisted / not-delisted status",
        "Reduce survivorship leakage.",
        "exchange_delisting_records;issuer_or_fund_notices",
        "symbol;delisting_status;covered_period;source_id;source_reference;limitation",
        "blocker_missing_historical_version;blocker_missing_survivorship_rationale;"
        "blocker_no_hit_misuse",
        no_hit=True,
    ),
    _family(
        "EF04",
        "STOCK ST / no-ST status",
        "Define special-treatment status for STOCK.",
        "exchange_disclosure_status;official_issuer_notice",
        "symbol;st_status;effective_period;announcement_id;source_reference",
        "blocker_missing_eligible_source_class;blocker_missing_effective_time;"
        "blocker_missing_revision_id;blocker_same_day_quotation_misuse",
    ),
    _family(
        "EF05",
        "ETF ST-not-applicable policy",
        "Define why STOCK ST status is not applicable to ETF.",
        "exchange_rules;etf_issuer_or_fund_policy",
        "instrument_type;policy_basis;effective_period;source_reference;limitation",
        "blocker_missing_eligible_source_class;blocker_missing_historical_version;"
        "blocker_current_webpage_used_as_historical_proof",
    ),
    _family(
        "EF06",
        "suspension / trading status",
        "Define date-specific suspension or trading restriction context.",
        "exchange_trading_status;official_suspension_notice",
        "symbol;session_date;trading_status;source_reference",
        "blocker_missing_source_reference;blocker_missing_available_time;"
        "blocker_same_day_quotation_misuse",
    ),
    _family(
        "EF07",
        "universe membership",
        "Define historical universe membership.",
        "official_index_or_provider_constituent_publication",
        "universe_id;symbol;membership_status;effective_date;constituent_version",
        "blocker_missing_universe_membership_evidence;"
        "blocker_missing_constituent_version_evidence;blocker_missing_available_time",
    ),
    _family(
        "EF08",
        "universe definition and constituent version",
        "Define methodology and exact constituent release.",
        "official_provider_methodology;official_constituent_publication",
        "universe_id;definition;methodology_version;constituent_version;effective_period",
        "blocker_missing_constituent_version_evidence;blocker_missing_historical_version;"
        "blocker_missing_corroboration",
    ),
    _family(
        "EF09",
        "source lineage / provenance",
        "Make every evidence reference traceable.",
        "source_registry;official_or_reviewed_reference",
        "source_id;source_name;source_type;reference_type;source_reference;parent_source",
        "blocker_missing_source_provenance;blocker_missing_source_reference;"
        "blocker_missing_permission_class",
        publish=False,
        effective=False,
    ),
    _family(
        "EF10",
        "publish_time / available_time / timezone",
        "Define the decision-time knowledge boundary.",
        "timestamped_official_publication;governed_archive",
        "decision_time;publish_time;available_time;effective_time;retrieval_time;"
        "archive_time;timezone",
        "blocker_undated_evidence;blocker_timezone_ambiguity;"
        "blocker_post_decision_evidence",
    ),
    _family(
        "EF11",
        "revision_id / effective version",
        "Identify original, revised, corrected, or restated versions.",
        "official_revision_history;governed_archive",
        "revision_id;revision_id_type;version_state;effective_time;supersedes",
        "blocker_missing_revision_id;blocker_missing_historical_version;"
        "blocker_superseded_evidence_unresolved",
    ),
    _family(
        "EF12",
        "permission_class / legality",
        "Define allowed review, retention, and disclosure use.",
        "source_terms;license;public_disclosure_policy;local_review_policy",
        "permission_class;allowed_use;retention_rule;disclosure_rule;legal_limitation",
        "blocker_missing_permission_class;blocker_forbidden_or_restricted_permission",
        publish=False,
        available=False,
        effective=True,
        historical=False,
        corroboration="legal_conflict_requires_separate_review",
    ),
    _family(
        "EF13",
        "survivorship rationale",
        "Explain why inclusion is not based only on later survival.",
        "historical_status_and_membership_sources",
        "warning_flag;source_ids;covered_period;rationale;limitation",
        "blocker_missing_historical_version;blocker_missing_universe_membership_evidence;"
        "blocker_missing_survivorship_rationale",
    ),
    _family(
        "EF14",
        "reviewer scope / quality / limitation",
        "Bound human review and expose limitations.",
        "governed_reviewer_attestation",
        "reviewer_alias;reviewer_role;reviewer_scope;reviewed_at;quality_status;limitation",
        "blocker_missing_reviewer_scope;blocker_reviewer_private_identity_disclosed",
        publish=False,
        available=False,
        effective=False,
        historical=False,
    ),
    _family(
        "EF15",
        "no-hit query context",
        "Record bounded query context without affirmative proof.",
        "reviewed_query_log",
        "source_family;evidence_family;query_terms;query_window;timezone;result_reference;"
        "reviewer_scope;limitation",
        "blocker_no_hit_misuse;blocker_post_decision_evidence;"
        "blocker_missing_source_reference;blocker_missing_reviewer_scope",
        no_hit=True,
        authority="context_only_never_affirmative_authority",
    ),
    _family(
        "EF16",
        "profile conflict context",
        "Preserve unresolved STOCK conflicts and ETF aligned context.",
        "fixture_lineage;future_policy_authority",
        "instrument_type;legacy_label;recommended_profile;profile_conflict;limitation",
        "blocker_unresolved_profile_conflict;"
        "blocker_missing_universe_membership_evidence",
        no_hit=False,
    ),
    _family(
        "EF17",
        "cross-source corroboration",
        "Compare independent eligible sources.",
        "independent_family_eligible_sources",
        "source_ids;fact_compared;agreement_or_conflict;timing;versions;rationale",
        "blocker_missing_corroboration;blocker_missing_source_provenance;"
        "blocker_timezone_ambiguity",
    ),
]


TIMING_RULES = [
    ("TIME01", "decision_timestamp", "decision_time;decision_timezone", "required", "blocker_missing_timezone"),
    ("TIME02", "publish_time", "publish_time", "required_by_family", "blocker_missing_publish_time"),
    ("TIME03", "available_time", "available_time", "required_by_family", "blocker_missing_available_time"),
    ("TIME04", "effective_time", "effective_time", "required_by_family", "blocker_missing_effective_time"),
    ("TIME05", "retrieval_time", "retrieval_time", "context_only", "blocker_missing_available_time"),
    ("TIME06", "archive_snapshot_time", "archive_time", "context_only", "blocker_missing_historical_version"),
    ("TIME07", "undated_evidence", "publish_time;available_time", "blocked", "blocker_undated_evidence"),
    ("TIME08", "timezone_ambiguity", "timezone", "blocked", "blocker_timezone_ambiguity"),
    ("TIME09", "post_decision_evidence", "available_time;decision_time", "blocked", "blocker_post_decision_evidence"),
    ("TIME10", "revised_or_backfilled", "original_available_time;revised_available_time", "blocked_until_lineage", "blocker_superseded_evidence_unresolved"),
]

REVISION_RULES = [
    ("REV01", "original_release", "revision_id;publish_time;available_time;effective_time", "preserve", "blocker_missing_revision_id"),
    ("REV02", "revised_release", "revision_id;supersedes;available_time", "preserve_both", "blocker_superseded_evidence_unresolved"),
    ("REV03", "correction", "revision_id;corrected_fields;available_time", "preserve_both", "blocker_superseded_evidence_unresolved"),
    ("REV04", "restatement", "revision_id;supersedes;available_time", "preserve_both", "blocker_superseded_evidence_unresolved"),
    ("REV05", "constituent_list_version", "provider;version;effective_date", "exact_history_required", "blocker_missing_constituent_version_evidence"),
    ("REV06", "current_page_vs_historical", "historical_version;archive_reference", "current_page_context_only", "blocker_current_webpage_used_as_historical_proof"),
    ("REV07", "revision_id", "revision_id;revision_id_type", "required", "blocker_missing_revision_id"),
    ("REV08", "superseded_evidence", "revision_id;superseded_by", "retain_unresolved", "blocker_superseded_evidence_unresolved"),
]

STOCK_ETF_MATRIX = [
    ("APP_STOCK_ST", "STOCK", "EF04", "applies", False),
    ("APP_ETF_ST", "ETF", "EF04", "not_applicable_context_only", True),
    ("APP_STOCK_ETF_NA", "STOCK", "EF05", "not_applicable_context_only", True),
    ("APP_ETF_ETF_NA", "ETF", "EF05", "applies", False),
]


@dataclass(frozen=True)
class HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureResult:
    run_id: str
    status: str
    health_status: str
    workflow_stage: str
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]


def run_historical_replay_source_evidence_sufficiency_policy_contract_fixture(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
) -> HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureResult:
    """Write deterministic synthetic contract artifacts only."""

    root_path = Path(root)
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    output_root_resolved = _validate_output_root(output_root)
    if run_id is None:
        run_id = _generate_run_id(root_path)
    _validate_run_id(run_id)
    artifact_dir = (output_root_resolved / run_id).resolve()
    if not _is_relative_to(artifact_dir, output_root_resolved):
        raise ValueError(
            f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: output path escapes requested root"
        )

    selected_rows = _selected_rows()
    contract_rows = _contract_rows(selected_rows)
    required_fields = _required_field_rows(selected_rows, contract_rows)
    status_rows = _status_rows()
    blocker_rows = _blocker_rows()
    timing_rows = _timing_revision_rows()
    stock_etf_rows = _stock_etf_rows()
    safety = _safety_flags()
    metadata = _metadata(
        run_id=run_id,
        selected_rows=selected_rows,
        contract_rows=contract_rows,
        required_fields=required_fields,
        status_rows=status_rows,
        blocker_rows=blocker_rows,
        timing_rows=timing_rows,
        stock_etf_rows=stock_etf_rows,
        safety=safety,
    )
    paths = _paths(artifact_dir)
    metadata["artifact_paths"] = dict(OUTPUT_FILES)
    metadata["report_path"] = OUTPUT_FILES["report"]

    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["selected_rows"], selected_rows, SELECTED_ROW_FIELDS)
    _write_csv(
        paths["evidence_family_contract"],
        contract_rows,
        EVIDENCE_FAMILY_CONTRACT_FIELDS,
    )
    _write_csv(
        paths["required_fields"],
        required_fields,
        [
            "field_scope",
            "field_name",
            "field_type",
            "required",
            "default_value",
            "blocker_if_invalid",
            "disclosure_policy",
        ],
    )
    _write_csv(
        paths["status_vocabulary"],
        status_rows,
        [
            "status",
            "scope",
            "allowed_for_selected_fixture",
            "meaning",
            "forbidden_interpretation",
        ],
    )
    _write_csv(
        paths["blocker_vocabulary"],
        blocker_rows,
        ["blocker_id", "category", "trigger", "applies_to", "meaning"],
    )
    _write_csv(
        paths["timing_revision_matrix"],
        timing_rows,
        [
            "rule_id",
            "category",
            "rule_name",
            "required_fields",
            "safe_default",
            "blocker",
            "forbidden_interpretation",
        ],
    )
    _write_csv(
        paths["stock_etf_matrix"],
        stock_etf_rows,
        [
            "applicability_rule_id",
            "instrument_type",
            "evidence_family_id",
            "selected_row_count",
            "instrument_applicability",
            "not_applicable_policy_required",
            "status_context",
            "notes",
        ],
    )
    _write_json(paths["safety_flags"], safety)
    paths["report"].write_text(_report(metadata), encoding="utf-8")

    return HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureResult(
        run_id=run_id,
        status=STATUS_CREATED,
        health_status="PASS",
        workflow_stage=WORKFLOW_STAGE,
        artifact_paths=paths,
        metadata=metadata,
    )


def _selected_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS:
        blockers = list(COMMON_ROW_BLOCKERS)
        if profile_conflict:
            blockers.insert(1, "blocker_unresolved_profile_conflict")
        rows.append(
            {
                "row_id": f"20240402_etf_core_{symbol}",
                "historical_decision_date": "2024-04-02",
                "decision_timezone": "Asia/Shanghai",
                "legacy_universe_label": "etf_core",
                "symbol": symbol,
                "instrument_type": instrument_type,
                "recommended_profile": recommended_profile,
                "profile_conflict": _bool_text(profile_conflict),
                "profile_policy_status": (
                    "unresolved_profile_conflict"
                    if profile_conflict
                    else "profile_aligned_context_only_not_universe_proof"
                ),
                "selected_row_blockers": ";".join(blockers),
                "selected_row_sufficiency_candidate": "false",
                "selected_row_evidence_accepted": "false",
                "selected_row_evidence_closed": "false",
                "selected_row_pit_admissible": "false",
                "selected_row_replay_ready": "false",
            }
        )
    return rows


def _contract_rows(selected_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for selected in selected_rows:
        for family in EVIDENCE_FAMILIES:
            applicability, not_applicable = _applicability(
                selected["instrument_type"], family["evidence_family_id"]
            )
            blockers = (
                ""
                if not_applicable
                else str(family["insufficiency_blockers"])
            )
            rows.append(
                {
                    "contract_row_id": (
                        f"{selected['row_id']}_{family['evidence_family_id'].lower()}"
                    ),
                    "row_id": selected["row_id"],
                    "evidence_family_id": str(family["evidence_family_id"]),
                    "evidence_family_name": str(family["evidence_family_name"]),
                    "instrument_applicability": applicability,
                    "not_applicable_policy_required": _bool_text(not_applicable),
                    "purpose": str(family["purpose"]),
                    "eligible_source_classes": str(family["eligible_source_classes"]),
                    "authoritative_source_class_policy": str(
                        family["authoritative_source_class_policy"]
                    ),
                    "required_structural_fields": str(
                        family["required_structural_fields"]
                    ),
                    "evidence_presence": "false",
                    "source_eligibility_context": (
                        "instrument_not_applicable_policy_context_only"
                        if not_applicable
                        else "controlled_policy_context_only"
                    ),
                    "publish_time_required": _bool_text(
                        bool(family["publish_time_required"]) and not not_applicable
                    ),
                    "available_time_required": _bool_text(
                        bool(family["available_time_required"]) and not not_applicable
                    ),
                    "effective_time_required": _bool_text(
                        bool(family["effective_time_required"]) and not not_applicable
                    ),
                    "timezone_required": _bool_text(
                        bool(family["timezone_required"]) and not not_applicable
                    ),
                    "revision_id_required": _bool_text(
                        bool(family["revision_id_required"]) and not not_applicable
                    ),
                    "historical_version_required": _bool_text(
                        bool(family["historical_version_required"])
                        and not not_applicable
                    ),
                    "source_reference_required": _bool_text(
                        bool(family["source_reference_required"]) and not not_applicable
                    ),
                    "source_hash_policy": str(family["source_hash_policy"]),
                    "permission_class_required": _bool_text(
                        bool(family["permission_class_required"]) and not not_applicable
                    ),
                    "corroboration_policy": str(family["corroboration_policy"]),
                    "reviewer_scope_required": _bool_text(
                        bool(family["reviewer_scope_required"]) and not not_applicable
                    ),
                    "no_hit_allowed_as_context_only": _bool_text(
                        bool(family["no_hit_allowed_as_context_only"])
                    ),
                    "insufficiency_blockers": blockers,
                    "sufficiency_candidate": "false",
                    "evidence_accepted": "false",
                    "evidence_closed": "false",
                    "pit_admissible": "false",
                    "replay_ready": "false",
                }
            )
    return rows


def _applicability(instrument_type: str, family_id: str) -> tuple[str, bool]:
    if family_id == "EF04" and instrument_type == "ETF":
        return "not_applicable_context_only", True
    if family_id == "EF05" and instrument_type == "STOCK":
        return "not_applicable_context_only", True
    return "applies", False


def _required_field_rows(
    selected_rows: list[dict[str, str]],
    contract_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for scope, fields, defaults in (
        ("selected_row", SELECTED_ROW_FIELDS, selected_rows[0]),
        (
            "evidence_family_contract",
            EVIDENCE_FAMILY_CONTRACT_FIELDS,
            contract_rows[0],
        ),
    ):
        for field in fields:
            rows.append(
                {
                    "field_scope": scope,
                    "field_name": field,
                    "field_type": _field_type(field),
                    "required": "true",
                    "default_value": defaults.get(field, ""),
                    "blocker_if_invalid": "blocker_missing_required_structural_fields",
                    "disclosure_policy": (
                        "preview_only_or_absent"
                        if field == "source_hash_policy"
                        else "synthetic_policy_only"
                    ),
                }
            )
    return rows


def _field_type(field: str) -> str:
    if field in {
        "profile_conflict",
        "selected_row_sufficiency_candidate",
        "selected_row_evidence_accepted",
        "selected_row_evidence_closed",
        "selected_row_pit_admissible",
        "selected_row_replay_ready",
        "not_applicable_policy_required",
        "evidence_presence",
        "publish_time_required",
        "available_time_required",
        "effective_time_required",
        "timezone_required",
        "revision_id_required",
        "historical_version_required",
        "source_reference_required",
        "permission_class_required",
        "reviewer_scope_required",
        "no_hit_allowed_as_context_only",
        "sufficiency_candidate",
        "evidence_accepted",
        "evidence_closed",
        "pit_admissible",
        "replay_ready",
    }:
        return "boolean"
    if field in {"selected_row_blockers", "insufficiency_blockers"}:
        return "delimiter_safe_list"
    return "string"


def _status_rows() -> list[dict[str, str]]:
    future_only = {
        "evidence_family_context_only",
        "evidence_family_sufficiency_candidate_not_accepted",
        "row_has_sufficiency_candidates_not_closed",
    }
    meanings = {
        status: status.replace("_", " ")
        for status in STATUS_VOCABULARY
    }
    meanings[
        "instrument_not_applicable_policy_context_only"
    ] = "Explicit opposite-instrument policy context; no family row is omitted."
    return [
        {
            "status": status,
            "scope": "row" if status.startswith("row_") else "evidence_family",
            "allowed_for_selected_fixture": _bool_text(status not in future_only),
            "meaning": meanings[status],
            "forbidden_interpretation": (
                "not evidence sufficiency, acceptance, closure, PIT approval, "
                "replay readiness, buy-review, or trading"
            ),
        }
        for status in STATUS_VOCABULARY
    ]


def _blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker_id": blocker,
            "category": _blocker_category(blocker),
            "trigger": blocker.removeprefix("blocker_").replace("_", " "),
            "applies_to": "selected_row_or_evidence_family_contract",
            "meaning": (
                "Blocks context from sufficiency, acceptance, closure, PIT, replay, "
                "buy-review, or trading interpretation."
            ),
        }
        for blocker in BLOCKER_VOCABULARY
    ]


def _blocker_category(blocker: str) -> str:
    for category in (
        "timing",
        "revision",
        "permission",
        "privacy",
        "provenance",
        "reviewer",
        "survivorship",
        "corroboration",
        "membership",
        "profile",
        "no_hit",
        "status",
        "safety",
    ):
        if category in blocker:
            return category
    if any(term in blocker for term in ("publish", "available", "effective", "timezone", "dated", "decision")):
        return "timing"
    if "source" in blocker or "reference" in blocker:
        return "source"
    return "schema"


def _timing_revision_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id, name, fields, safe_default, blocker in TIMING_RULES:
        rows.append(
            {
                "rule_id": rule_id,
                "category": "timing",
                "rule_name": name,
                "required_fields": fields,
                "safe_default": safe_default,
                "blocker": blocker,
                "forbidden_interpretation": "not real PIT comparison or approval",
            }
        )
    for rule_id, name, fields, safe_default, blocker in REVISION_RULES:
        rows.append(
            {
                "rule_id": rule_id,
                "category": "revision",
                "rule_name": name,
                "required_fields": fields,
                "safe_default": safe_default,
                "blocker": blocker,
                "forbidden_interpretation": "not revision validation or historical truth",
            }
        )
    return rows


def _stock_etf_rows() -> list[dict[str, str]]:
    counts = {"STOCK": 7, "ETF": 2}
    return [
        {
            "applicability_rule_id": rule_id,
            "instrument_type": instrument_type,
            "evidence_family_id": family_id,
            "selected_row_count": str(counts[instrument_type]),
            "instrument_applicability": applicability,
            "not_applicable_policy_required": _bool_text(not_applicable),
            "status_context": (
                "instrument_not_applicable_policy_context_only"
                if not_applicable
                else "evidence_family_missing_required_fields"
            ),
            "notes": (
                "Routing context only; not identity, official status, membership, "
                "profile validation, PIT, or replay approval."
            ),
        }
        for (
            rule_id,
            instrument_type,
            family_id,
            applicability,
            not_applicable,
        ) in STOCK_ETF_MATRIX
    ]


def _metadata(
    *,
    run_id: str,
    selected_rows: list[dict[str, str]],
    contract_rows: list[dict[str, str]],
    required_fields: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    blocker_rows: list[dict[str, str]],
    timing_rows: list[dict[str, str]],
    stock_etf_rows: list[dict[str, str]],
    safety: dict[str, bool],
) -> dict[str, Any]:
    applicable = sum(
        row["instrument_applicability"] == "applies" for row in contract_rows
    )
    not_applicable = len(contract_rows) - applicable
    return {
        **safety,
        "run_id": run_id,
        "workflow_name": WORKFLOW_NAME,
        "runtime_status": STATUS_CREATED,
        "health_status": "PASS",
        "workflow_stage": WORKFLOW_STAGE,
        "historical_decision_date": "2024-04-02",
        "decision_timezone": "Asia/Shanghai",
        "legacy_universe_label": "etf_core",
        "row_count": len(selected_rows),
        "stock_row_count": sum(row["instrument_type"] == "STOCK" for row in selected_rows),
        "etf_row_count": sum(row["instrument_type"] == "ETF" for row in selected_rows),
        "profile_conflict_count": sum(
            _truthy_text(row["profile_conflict"]) for row in selected_rows
        ),
        "profile_aligned_context_count": sum(
            not _truthy_text(row["profile_conflict"]) for row in selected_rows
        ),
        "unresolved_profile_conflict_count": sum(
            row["profile_policy_status"] == "unresolved_profile_conflict"
            for row in selected_rows
        ),
        "selected_row_with_blocker_count": sum(
            bool(row["selected_row_blockers"]) for row in selected_rows
        ),
        "evidence_family_count": len(EVIDENCE_FAMILIES),
        "row_evidence_family_contract_count": len(contract_rows),
        "applicable_contract_row_count": applicable,
        "instrument_not_applicable_context_row_count": not_applicable,
        "core_artifact_count": len(OUTPUT_FILES),
        "selected_row_required_field_count": len(SELECTED_ROW_FIELDS),
        "evidence_family_contract_field_count": len(
            EVIDENCE_FAMILY_CONTRACT_FIELDS
        ),
        "required_field_row_count": len(required_fields),
        "status_vocabulary_row_count": len(status_rows),
        "blocker_vocabulary_row_count": len(blocker_rows),
        "timing_revision_rule_count": len(timing_rows),
        "stock_etf_matrix_row_count": len(stock_etf_rows),
        "sufficiency_candidate_count": sum(
            _truthy_text(row["sufficiency_candidate"]) for row in contract_rows
        ),
        "evidence_accepted_count": sum(
            _truthy_text(row["evidence_accepted"]) for row in contract_rows
        ),
        "evidence_closed_count": sum(
            _truthy_text(row["evidence_closed"]) for row in contract_rows
        ),
        "pit_admissible_count": sum(
            _truthy_text(row["pit_admissible"]) for row in contract_rows
        ),
        "replay_ready_count": sum(
            _truthy_text(row["replay_ready"]) for row in contract_rows
        ),
        "safety_true_count": sum(
            1 for field in SAFETY_FALSE_FIELDS if safety[field]
        ),
        "symbols_preview": ";".join(row["symbol"] for row in selected_rows),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }


def _safety_flags() -> dict[str, bool]:
    return {
        **{field: False for field in SAFETY_FALSE_FIELDS},
        **POSITIVE_SCOPE_FLAGS,
    }


def _report(metadata: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture",
            "",
            "This artifact is report-only, diagnostic-only, local-only, and synthetic-only.",
            "It contains policy contracts, blockers, and negative proof only.",
            "It does not read evidence, assign sufficiency, accept or close evidence, approve PIT, or create replay readiness.",
            "",
            f"- Run id: {metadata['run_id']}",
            f"- Runtime status: {metadata['runtime_status']}",
            f"- Health status: {metadata['health_status']}",
            f"- Selected rows: {metadata['row_count']}",
            f"- STOCK rows: {metadata['stock_row_count']}",
            f"- ETF rows: {metadata['etf_row_count']}",
            f"- Evidence families: {metadata['evidence_family_count']}",
            f"- Contract rows: {metadata['row_evidence_family_contract_count']}",
            f"- Applicable contract rows: {metadata['applicable_contract_row_count']}",
            f"- Instrument N/A context rows: {metadata['instrument_not_applicable_context_row_count']}",
            f"- Selected rows with blockers: {metadata['selected_row_with_blocker_count']}",
            f"- Sufficiency candidates: {metadata['sufficiency_candidate_count']}",
            f"- Evidence accepted: {metadata['evidence_accepted_count']}",
            f"- Evidence closed: {metadata['evidence_closed_count']}",
            f"- PIT admissible: {metadata['pit_admissible_count']}",
            f"- Replay ready: {metadata['replay_ready_count']}",
            f"- Safety true count: {metadata['safety_true_count']}",
            f"- Recommended next task: {metadata['recommended_next_task']}",
            "",
            "Source eligibility is not evidence presence. Evidence presence is not sufficiency.",
            "Sufficiency is not acceptance. Acceptance is not closure. Closure is not PIT approval.",
            "PIT approval is not replay readiness, buy-review, or trading authority.",
            "",
        ]
    )


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {
        key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _validate_output_root(output_root: Path) -> Path:
    resolved = output_root.resolve()
    parts = tuple(part.lower() for part in resolved.parts)
    for protected in PROTECTED_PATH_PARTS:
        for index in range(max(len(parts) - len(protected) + 1, 0)):
            if parts[index : index + len(protected)] == protected:
                raise ValueError(
                    f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: protected output root"
                )

    diagnostics = ("outputs", "reports", "manual_diagnostics")
    diagnostics_allowed = any(
        parts[index : index + len(diagnostics)] == diagnostics
        for index in range(max(len(parts) - len(diagnostics) + 1, 0))
    )
    temp_allowed = _is_relative_to(resolved, Path(tempfile.gettempdir()).resolve())
    if not diagnostics_allowed and not temp_allowed:
        raise ValueError(
            f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: root is not report-only diagnostics or temp"
        )
    return resolved


def _validate_run_id(run_id: str) -> None:
    if any(part in run_id for part in ("..", "/", "\\")) or not run_id.strip():
        raise ValueError("invalid run_id")


def _generate_run_id(root: Path) -> str:
    digest = hashlib.sha256(
        f"{root}|2024-04-02|etf_core|{WORKFLOW_NAME}".encode("utf-8")
    ).hexdigest()
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
