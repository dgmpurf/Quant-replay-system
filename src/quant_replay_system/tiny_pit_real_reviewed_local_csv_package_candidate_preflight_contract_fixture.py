"""Synthetic report-only Tiny PIT real reviewed LOCAL_CSV preflight fixture.

This module creates deterministic contract-fixture artifacts only. It does not
read real CSVs, accept real package paths, validate PIT admissibility, create
active inputs, run replay, create labels, train models, create stock_profile
artifacts, authorize buy-review, validate performance, or allow
broker/API/order/message/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE = "NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE"
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_DECLARED_REPORT_ONLY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_DECLARED_REPORT_ONLY"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_PERMISSION = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_PERMISSION"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
REAL_REVIEWED_LOCAL_CSV_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW = (
    "REAL_REVIEWED_LOCAL_CSV_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW"
)

TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY = (
    "TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY"
)

CREATED_AT = "2026-06-30T00:00:00Z"
FIXTURE_VERSION = "v0.1"
WORKFLOW_NAME = "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture"
DEFAULT_OUTPUT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture "
    "Artifact Views / Index / Health / Status Report-Only v0.1"
)

FORBIDDEN_STATUS_WORDING = [
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "PIT_VALIDATED_REAL_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "ACTIVE_REVIEWED_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
    "REAL_BUY_READY",
    "PERFORMANCE_VALIDATED",
]

SAFETY_FALSE_FLAGS = [
    "real_csv_required",
    "real_csv_consumed",
    "real_reviewed_csv_package_created",
    "real_package_candidate_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "replay_decisions_created",
    "forward_labels_created",
    "future_labels_joined",
    "training_allowed",
    "training_dataset_created",
    "metric_computation_performed",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_allowed",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "current_candidates_created",
    "snapshots_created",
    "signal_semantics_mutated",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "real_reviewed_local_csv_package_candidate_preflight_contract_fixture_report.md",
    "package_candidate_manifest_contract": "package_candidate_manifest_contract.csv",
    "package_section_contract": "package_section_contract.csv",
    "field_family_contract": "field_family_contract.csv",
    "available_time_preflight_case_matrix": "available_time_preflight_case_matrix.csv",
    "source_hash_revision_preflight_case_matrix": "source_hash_revision_preflight_case_matrix.csv",
    "reviewer_authority_preflight_case_matrix": "reviewer_authority_preflight_case_matrix.csv",
    "quality_limitation_preflight_case_matrix": "quality_limitation_preflight_case_matrix.csv",
    "safe_status_vocabulary": "safe_status_vocabulary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "limitations": "limitations.md",
}

CASE_COLUMNS = [
    "case_id",
    "purpose",
    "expected_status",
    "expected_health",
    "status",
    "health_status",
    "blocker_count",
    "warning_count",
    "blocker_categories",
    "warning_categories",
    "pass_candidate",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "why_report_only",
    *SAFETY_FALSE_FLAGS,
]

FIELD_FAMILY_CONTRACT = [
    {
        "field_family": "package_identity",
        "required_fields": "package_id;package_version;package_created_at;package_created_by;candidate_kind",
        "missing_field_behavior": "Missing package identity blocks package schema.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "missing_package_manifest and malformed_metadata block.",
    },
    {
        "field_family": "package_section_presence",
        "required_fields": (
            "package_manifest;source_registry_snapshot;raw_document_or_dataset_reference_manifest;"
            "reviewed_file_manifest;table_schema_manifest;row_lineage_manifest;available_time_manifest;"
            "source_hash_revision_manifest;reviewer_attestation_manifest;quality_review_manifest;"
            "limitation_manifest;forbidden_downstream_flags"
        ),
        "missing_field_behavior": "Missing required section blocks.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "Every required section has a blocking synthetic case.",
    },
    {
        "field_family": "source_registry_snapshot",
        "required_fields": "source_id;source_name;source_type;permission_class;storage_policy",
        "missing_field_behavior": "Missing source registry snapshot blocks source lineage.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "source registry snapshot missing blocks.",
    },
    {
        "field_family": "raw_document_dataset_reference",
        "required_fields": "reference_id;source_reference;document_publish_time;source_evidence_reference",
        "missing_field_behavior": "Missing source reference blocks source lineage.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "raw document or dataset reference missing blocks.",
    },
    {
        "field_family": "reviewed_file_manifest",
        "required_fields": "reviewed_file_id;local_file_hash;local_file_hash_algorithm;local_file_created_at",
        "missing_field_behavior": "Missing local_file_hash blocks.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "missing_local_file_hash_blocks and changed hash cases block.",
    },
    {
        "field_family": "table_schema_manifest",
        "required_fields": "column_definitions;key_fields;required_field_declarations",
        "missing_field_behavior": "Missing or malformed schema blocks package quality.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "missing table schema and malformed metadata block.",
    },
    {
        "field_family": "row_lineage",
        "required_fields": "row_id;source_row_reference;row_count;lineage_complete",
        "missing_field_behavior": "Missing row lineage blocks source lineage.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "missing row lineage manifest blocks.",
    },
    {
        "field_family": "available_time",
        "required_fields": "available_time;replay_decision_time;available_time_basis;timing_evidence_reference",
        "missing_field_behavior": "Missing, late, conflicting, or unsupported timing blocks.",
        "blocker_warning_behavior": "Blocker or review warning.",
        "future_test_expectation": "event/period/reviewed/local-created-only cases block.",
    },
    {
        "field_family": "source_hash_local_file_hash_revision_id",
        "required_fields": "source_hash;source_hash_algorithm;local_file_hash;local_file_hash_algorithm;revision_id",
        "missing_field_behavior": "Missing hashes or revision_id block.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "hash/revision cases block and hashes are distinct.",
    },
    {
        "field_family": "reviewer_authority",
        "required_fields": "reviewer_id;reviewer_role;reviewer_scope;reviewer_authority;reviewer_attestation",
        "missing_field_behavior": "Missing reviewer authority blocks.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "Reviewer approval cannot override timing/source/revision/quality blockers.",
    },
    {
        "field_family": "quality",
        "required_fields": "quality_status;blocker_count;warning_count;manual_review_status",
        "missing_field_behavior": "Missing or failed quality blocks.",
        "blocker_warning_behavior": "Blocker or needs-review warning.",
        "future_test_expectation": "quality_failed blocks and warning_count positive becomes needs-review only.",
    },
    {
        "field_family": "limitations",
        "required_fields": "limitation_note;affected_section;severity;required_next_review",
        "missing_field_behavior": "Warning without limitation note blocks.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "warning_without_limitation_note_blocks.",
    },
    {
        "field_family": "forbidden_downstream_flags",
        "required_fields": ";".join(SAFETY_FALSE_FLAGS),
        "missing_field_behavior": "Missing or true forbidden flags block.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "forbidden flag true, future label leakage, and protected writes block.",
    },
    {
        "field_family": "output_root_guard_fields",
        "required_fields": "output_root;resolved_output_root;protected_path_classification",
        "missing_field_behavior": "Protected or escaping output root is rejected before writing.",
        "blocker_warning_behavior": "Blocker.",
        "future_test_expectation": "protected output roots and secrets paths are rejected.",
    },
]

REQUIRED_CASE_IDS = [
    "no_real_reviewed_local_csv_package_candidate",
    "schema_designed_report_only",
    "declared_report_only_candidate",
    "complete_report_only_pass_candidate_for_human_review",
    "missing_package_manifest",
    "missing_source_registry_snapshot",
    "missing_raw_document_or_dataset_reference_manifest",
    "missing_reviewed_file_manifest",
    "missing_table_schema_manifest",
    "missing_row_lineage_manifest",
    "missing_available_time_manifest",
    "missing_source_hash_revision_manifest",
    "missing_reviewer_attestation_manifest",
    "missing_quality_review_manifest",
    "missing_limitation_manifest",
    "missing_forbidden_downstream_flags",
    "event_date_only_is_blocked",
    "period_end_only_is_blocked",
    "reviewed_at_only_is_blocked",
    "local_csv_created_at_only_is_blocked",
    "missing_available_time_blocks",
    "available_time_after_replay_decision_time_blocks",
    "conflicting_available_time_blocks",
    "document_publish_time_without_source_evidence_blocks",
    "fetched_after_replay_needs_historical_availability_evidence",
    "future_revision_risk_blocks_or_needs_review",
    "missing_source_hash_blocks",
    "missing_local_file_hash_blocks",
    "missing_revision_id_blocks",
    "filename_as_revision_id_blocks",
    "revision_conflict_blocks",
    "changed_local_file_hash_requires_new_package_version",
    "missing_reviewer_id_blocks",
    "missing_reviewer_scope_blocks",
    "missing_reviewer_authority_blocks",
    "reviewer_attestation_without_authority_blocks",
    "reviewer_approval_cannot_override_timing_failure",
    "reviewer_approval_cannot_override_source_hash_failure",
    "reviewer_approval_cannot_override_revision_conflict",
    "reviewer_approval_cannot_override_quality_failed",
    "quality_failed_blocks",
    "warning_without_limitation_note_blocks",
    "blocker_count_positive_blocks_pass_candidate",
    "warning_count_positive_allows_needs_review_only",
    "forbidden_downstream_flag_true_blocks",
    "future_label_leakage_blocks",
    "protected_data_write_claim_blocks",
    "unsafe_status_wording_ready_for_replay_blocks",
    "unsafe_status_wording_active_replay_input_ready_blocks",
    "real_csv_path_argument_rejected",
    "data_raw_output_root_rejected",
    "data_processed_output_root_rejected",
    "data_cache_output_root_rejected",
    "docs_project_sources_output_root_rejected",
    "secrets_path_rejected",
    "malformed_metadata_blocks",
]


@dataclass(frozen=True)
class RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts:
    fixture_id: str
    fixture_version: str
    workflow_name: str
    workflow_stage: str
    status: str
    health_status: str
    created_at: str
    case_count: int
    pass_count: int
    warn_count: int
    fail_count: int
    blocker_count: int
    warning_count: int
    report_only: bool
    diagnostic_only: bool
    synthetic_only: bool
    artifact_path: Path
    report_path: Path
    artifact_paths: dict[str, Path]
    case_results: list[dict[str, Any]]


def real_reviewed_local_csv_package_candidate_preflight_statuses() -> list[str]:
    return [
        NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_DECLARED_REPORT_ONLY,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_PERMISSION,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        REAL_REVIEWED_LOCAL_CSV_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW,
    ]


def real_reviewed_local_csv_package_candidate_preflight_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases() -> list[dict[str, Any]]:
    return [
        _case(
            "no_real_reviewed_local_csv_package_candidate",
            "No real reviewed LOCAL_CSV package candidate exists.",
            NO_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE,
            "PASS",
            why="Absence is benign report-only context.",
        ),
        _case(
            "schema_designed_report_only",
            "Synthetic preflight schema designed for future contract only.",
            REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
            "PASS",
            why="Schema design only; no real package candidate exists.",
        ),
        _case(
            "declared_report_only_candidate",
            "Synthetic declared candidate shape without real package creation.",
            REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_DECLARED_REPORT_ONLY,
            "PASS",
            why="Declared report-only candidate shape only; no real package is created.",
        ),
        _case(
            "complete_report_only_pass_candidate_for_human_review",
            "Complete synthetic preflight shape for human review semantics.",
            REAL_REVIEWED_LOCAL_CSV_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW,
            "PASS",
            pass_candidate=True,
            why="Synthetic pass-candidate for human review only; not PIT pass or active input.",
        ),
        _case("missing_package_manifest", "Package manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA, "FAIL", blockers=["missing_section", "package_manifest"]),
        _case("missing_source_registry_snapshot", "Source registry snapshot missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["missing_section", "source_registry_snapshot"]),
        _case("missing_raw_document_or_dataset_reference_manifest", "Raw document or dataset reference manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["missing_section", "raw_document_dataset_reference"]),
        _case("missing_reviewed_file_manifest", "Reviewed file manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["missing_section", "reviewed_file_manifest"]),
        _case("missing_table_schema_manifest", "Table schema manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA, "FAIL", blockers=["missing_section", "table_schema"]),
        _case("missing_row_lineage_manifest", "Row lineage manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["missing_section", "row_lineage"]),
        _case("missing_available_time_manifest", "available_time manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["missing_section", "available_time"]),
        _case("missing_source_hash_revision_manifest", "Source hash / revision manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["missing_section", "hash_revision"]),
        _case("missing_reviewer_attestation_manifest", "Reviewer attestation manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY, "FAIL", blockers=["missing_section", "reviewer_authority"]),
        _case("missing_quality_review_manifest", "Quality review manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["missing_section", "quality"]),
        _case("missing_limitation_manifest", "Limitation manifest missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["missing_section", "limitation_missing"]),
        _case("missing_forbidden_downstream_flags", "Forbidden downstream flags missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["missing_section", "forbidden_downstream"]),
        _case("event_date_only_is_blocked", "event_date alone cannot prove decision-time availability.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time", "event_date_only"]),
        _case("period_end_only_is_blocked", "period_end alone cannot prove decision-time availability.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time", "period_end_only"]),
        _case("reviewed_at_only_is_blocked", "reviewed_at is audit metadata only.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time", "reviewed_at_only"]),
        _case("local_csv_created_at_only_is_blocked", "local_csv_created_at is local file metadata only.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time", "local_csv_created_at_only"]),
        _case("missing_available_time_blocks", "available_time missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time"]),
        _case("available_time_after_replay_decision_time_blocks", "available_time after replay decision time.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time"]),
        _case("conflicting_available_time_blocks", "Conflicting available_time evidence.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time_conflict"]),
        _case("document_publish_time_without_source_evidence_blocks", "document_publish_time lacks source evidence.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["source_evidence_missing"]),
        _case("fetched_after_replay_needs_historical_availability_evidence", "Later fetch requires historical availability evidence.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW, "WARN", warnings=["historical_availability_evidence_required"]),
        _case("future_revision_risk_blocks_or_needs_review", "Future revision risk requires review.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW, "WARN", warnings=["future_revision_risk"]),
        _case("missing_source_hash_blocks", "source_hash missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["source_hash"]),
        _case("missing_local_file_hash_blocks", "local_file_hash missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["local_file_hash"]),
        _case("missing_revision_id_blocks", "revision_id missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION, "FAIL", blockers=["revision_id"]),
        _case("filename_as_revision_id_blocks", "Filename cannot serve as revision_id.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION, "FAIL", blockers=["filename_as_revision_id"]),
        _case("revision_conflict_blocks", "Revision conflict present.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION, "FAIL", blockers=["revision_conflict"]),
        _case("changed_local_file_hash_requires_new_package_version", "Changed local hash requires new package version.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION, "FAIL", blockers=["new_package_version_required"]),
        _case("missing_reviewer_id_blocks", "reviewer_id missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY, "FAIL", blockers=["reviewer_authority"]),
        _case("missing_reviewer_scope_blocks", "reviewer_scope missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY, "FAIL", blockers=["reviewer_authority"]),
        _case("missing_reviewer_authority_blocks", "reviewer_authority missing.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY, "FAIL", blockers=["reviewer_authority"]),
        _case("reviewer_attestation_without_authority_blocks", "Reviewer attestation without authority.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY, "FAIL", blockers=["reviewer_authority"]),
        _case("reviewer_approval_cannot_override_timing_failure", "Reviewer approval cannot override timing failure.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_AVAILABLE_TIME, "FAIL", blockers=["available_time", "reviewer_non_override"], why="Reviewer approval does not override timing failure."),
        _case("reviewer_approval_cannot_override_source_hash_failure", "Reviewer approval cannot override source_hash failure.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE, "FAIL", blockers=["source_hash", "reviewer_non_override"], why="Reviewer approval does not override source_hash failure."),
        _case("reviewer_approval_cannot_override_revision_conflict", "Reviewer approval cannot override revision conflict.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_REVISION, "FAIL", blockers=["revision_conflict", "reviewer_non_override"], why="Reviewer approval does not override revision conflict."),
        _case("reviewer_approval_cannot_override_quality_failed", "Reviewer approval cannot override quality failure.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["quality", "reviewer_non_override"], why="Reviewer approval does not override quality failure."),
        _case("quality_failed_blocks", "quality_status failed.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["quality"]),
        _case("warning_without_limitation_note_blocks", "Warning lacks limitation note.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["limitation_missing"]),
        _case("blocker_count_positive_blocks_pass_candidate", "blocker_count positive.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY, "FAIL", blockers=["blocker_count_positive"]),
        _case("warning_count_positive_allows_needs_review_only", "Warnings with no blockers need review only.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_NEEDS_REVIEW, "WARN", warnings=["warning_count_positive"]),
        _case("forbidden_downstream_flag_true_blocks", "Forbidden downstream flag true.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["forbidden_downstream"]),
        _case("future_label_leakage_blocks", "Future label leakage present.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["future_label_leakage"]),
        _case("protected_data_write_claim_blocks", "Protected data write claimed.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_write"]),
        _case("unsafe_status_wording_ready_for_replay_blocks", "Unsafe ready-for-replay wording.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["unsafe_wording"]),
        _case("unsafe_status_wording_active_replay_input_ready_blocks", "Unsafe active replay input ready wording.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["unsafe_wording"]),
        _case("real_csv_path_argument_rejected", "Real CSV path argument rejected by design.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA, "FAIL", blockers=["real_csv_path_argument"]),
        _case("data_raw_output_root_rejected", "data/raw output root rejected.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_output_root"]),
        _case("data_processed_output_root_rejected", "data/processed output root rejected.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_output_root"]),
        _case("data_cache_output_root_rejected", "data/cache output root rejected.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_output_root"]),
        _case("docs_project_sources_output_root_rejected", "docs/project_sources output root rejected.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_output_root"]),
        _case("secrets_path_rejected", "Secret/auth/token/credential path rejected.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM, "FAIL", blockers=["protected_output_root"]),
        _case("malformed_metadata_blocks", "Malformed metadata.", REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_BLOCKED_BY_PACKAGE_SCHEMA, "FAIL", blockers=["malformed_metadata"]),
    ]


def validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case: dict[str, Any]) -> dict[str, Any]:
    blocker_categories = list(case.get("blocker_categories", []))
    warning_categories = list(case.get("warning_categories", []))
    result = {
        "case_id": str(case["case_id"]),
        "purpose": str(case["purpose"]),
        "expected_status": str(case.get("expected_status", case["status"])),
        "expected_health": str(case.get("expected_health", case["health_status"])),
        "status": str(case["status"]),
        "health_status": str(case["health_status"]),
        "blocker_categories": blocker_categories,
        "warning_categories": warning_categories,
        "blocker_count": len(blocker_categories),
        "warning_count": len(warning_categories),
        "pass_candidate": bool(case.get("pass_candidate", False)) and not blocker_categories,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "why_report_only": str(case.get("why_report_only", "Synthetic report-only preflight contract case; no real package is created.")),
    }
    result.update(real_reviewed_local_csv_package_candidate_preflight_safety_flags())
    if result["blocker_count"] > 0:
        result["pass_candidate"] = False
    return result


def build_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
    *, output_root: str | Path = DEFAULT_OUTPUT_ROOT
) -> RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts:
    output_root_path = _validate_output_root(Path(output_root))
    cases = default_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_cases()
    results = [validate_real_reviewed_local_csv_package_candidate_preflight_contract_case(case) for case in cases]
    fixture_id = _fixture_id(results)
    artifact_path = output_root_path / fixture_id
    artifact_paths = {"artifact_dir": artifact_path}
    artifact_paths.update({key: artifact_path / filename for key, filename in ARTIFACT_FILENAMES.items()})
    _validate_artifact_paths(artifact_path, artifact_paths)
    return RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts(
        fixture_id=fixture_id,
        fixture_version=FIXTURE_VERSION,
        workflow_name=WORKFLOW_NAME,
        workflow_stage=TINY_PIT_REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_PREFLIGHT_CONTRACT_FIXTURE_CREATED_REPORT_ONLY,
        status=REAL_REVIEWED_LOCAL_CSV_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
        health_status="PASS",
        created_at=CREATED_AT,
        case_count=len(results),
        pass_count=sum(1 for result in results if result["pass_candidate"]),
        warn_count=sum(1 for result in results if result["health_status"] == "WARN"),
        fail_count=sum(1 for result in results if result["health_status"] == "FAIL"),
        blocker_count=sum(int(result["blocker_count"]) for result in results),
        warning_count=sum(int(result["warning_count"]) for result in results),
        report_only=True,
        diagnostic_only=True,
        synthetic_only=True,
        artifact_path=artifact_path,
        report_path=artifact_paths["report"],
        artifact_paths=artifact_paths,
        case_results=results,
    )


def write_real_reviewed_local_csv_package_candidate_preflight_contract_fixture_artifacts(
    result: RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts,
) -> RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts:
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_report(result)
    _write_csv(result.artifact_paths["package_candidate_manifest_contract"], _package_candidate_manifest_contract())
    _write_csv(result.artifact_paths["package_section_contract"], _package_section_contract())
    _write_csv(result.artifact_paths["field_family_contract"], FIELD_FAMILY_CONTRACT)
    _write_case_csv(result.artifact_paths["available_time_preflight_case_matrix"], result.case_results, "available_time")
    _write_case_csv(result.artifact_paths["source_hash_revision_preflight_case_matrix"], result.case_results, "hash_revision")
    _write_case_csv(result.artifact_paths["reviewer_authority_preflight_case_matrix"], result.case_results, "reviewer")
    _write_case_csv(result.artifact_paths["quality_limitation_preflight_case_matrix"], result.case_results, "quality")
    _write_csv(result.artifact_paths["safe_status_vocabulary"], _status_rows())
    _write_json(result.artifact_paths["forbidden_downstream_flags"], real_reviewed_local_csv_package_candidate_preflight_safety_flags())
    result.artifact_paths["limitations"].write_text(_limitations(), encoding="utf-8")
    return result


def _case(
    case_id: str,
    purpose: str,
    status: str,
    health_status: str,
    *,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    pass_candidate: bool = False,
    why: str | None = None,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "purpose": purpose,
        "expected_status": status,
        "expected_health": health_status,
        "status": status,
        "health_status": health_status,
        "blocker_categories": blockers or [],
        "warning_categories": warnings or [],
        "pass_candidate": pass_candidate,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "real_csv_required": False,
        "real_csv_consumed": False,
        "real_package_candidate_created": False,
        "active_reviewed_input_candidate_created": False,
        "active_replay_input": False,
        "active_replay_input_ready_emitted": False,
        "replay_execution_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "why_report_only": why or "Synthetic report-only preflight contract case; no real package is created.",
    }


def _fixture_id(results: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        [{"case_id": result["case_id"], "status": result["status"], "health_status": result["health_status"]} for result in results],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _validate_output_root(output_root: Path) -> Path:
    root = output_root.resolve()
    lowered_parts = [part.lower() for part in root.parts]
    blocked_pairs = {("data", "raw"), ("data", "processed"), ("data", "cache"), ("docs", "project_sources")}
    for first, second in zip(lowered_parts, lowered_parts[1:]):
        if (first, second) in blocked_pairs:
            raise ValueError(f"Protected output root is not allowed: {output_root}")
    blocked_tokens = [".env", "secrets", "auth", "token", "credential"]
    if any(any(token in part for token in blocked_tokens) for part in lowered_parts):
        raise ValueError(f"Protected output root is not allowed: {output_root}")
    return root


def _validate_artifact_paths(root: Path, artifact_paths: dict[str, Path]) -> None:
    for key, path in artifact_paths.items():
        if key == "artifact_dir":
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Artifact path escapes output root: {path}")


def _metadata(result: RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts) -> dict[str, Any]:
    metadata = {
        "fixture_id": result.fixture_id,
        "fixture_version": result.fixture_version,
        "workflow_name": result.workflow_name,
        "workflow_stage": result.workflow_stage,
        "status": result.status,
        "health_status": result.health_status,
        "created_at": result.created_at,
        "case_count": result.case_count,
        "pass_count": result.pass_count,
        "warn_count": result.warn_count,
        "fail_count": result.fail_count,
        "blocker_count": result.blocker_count,
        "warning_count": result.warning_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "synthetic_only": result.synthetic_only,
        "artifact_path": str(result.artifact_path),
        "report_path": str(result.report_path),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
        "output_files": {key: str(value) for key, value in result.artifact_paths.items() if key != "artifact_dir"},
    }
    metadata.update(real_reviewed_local_csv_package_candidate_preflight_safety_flags())
    return metadata


def _write_report(result: RealReviewedLocalCsvPackageCandidatePreflightContractFixtureArtifacts) -> None:
    text = f"""# Tiny PIT Real Reviewed LOCAL_CSV Package Candidate Preflight Contract Fixture

This is a synthetic, report-only, diagnostic-only preflight contract fixture.

- Fixture id: `{result.fixture_id}`
- Status: `{result.status}`
- Workflow stage: `{result.workflow_stage}`
- Health: `{result.health_status}`
- Case count: `{result.case_count}`
- Pass-candidate count: `{result.pass_count}`
- Warn count: `{result.warn_count}`
- Fail count: `{result.fail_count}`

The fixture does not read real CSV files, create real package candidates, create active reviewed input candidates, create replay input, emit active replay readiness, run replay, create labels/training/model/stock_profile/paper/buy-review/trading behavior, or write protected data roots.
"""
    result.artifact_paths["report"].write_text(text, encoding="utf-8")


def _package_candidate_manifest_contract() -> list[dict[str, str]]:
    return [
        {"field_name": "package_id", "required": "true", "behavior": "Missing blocks package schema."},
        {"field_name": "package_version", "required": "true", "behavior": "Changed local hash requires a new package version."},
        {"field_name": "candidate_kind", "required": "true", "behavior": "Must remain report-only candidate context."},
        {"field_name": "report_only", "required": "true", "behavior": "Must be true."},
        {"field_name": "diagnostic_only", "required": "true", "behavior": "Must be true."},
        {"field_name": "synthetic_only", "required": "true", "behavior": "Must be true in this fixture."},
    ]


def _package_section_contract() -> list[dict[str, str]]:
    return [
        {"section": section, "required": "true", "missing_behavior": "Blocks pass-candidate."}
        for section in [
            "package_manifest",
            "source_registry_snapshot",
            "raw_document_or_dataset_reference_manifest",
            "reviewed_file_manifest",
            "table_schema_manifest",
            "row_lineage_manifest",
            "available_time_manifest",
            "source_hash_revision_manifest",
            "reviewer_attestation_manifest",
            "quality_review_manifest",
            "limitation_manifest",
            "forbidden_downstream_flags",
        ]
    ]


def _status_rows() -> list[dict[str, str]]:
    return [
        {
            "status": status,
            "active_input_allowed": "false",
            "replay_allowed": "false",
            "buy_review_allowed": "false",
            "trading_allowed": "false",
        }
        for status in real_reviewed_local_csv_package_candidate_preflight_statuses()
    ]


def _limitations() -> str:
    return (
        "# Limitations\n\n"
        "- Synthetic/report-only preflight contract fixture only.\n"
        "- No real CSV files are read.\n"
        "- No real package candidate is created.\n"
        "- No active input, replay, labels, training, model, stock_profile, paper, buy-review, or trading behavior is created.\n"
    )


def _write_case_csv(path: Path, rows: list[dict[str, Any]], category: str) -> None:
    selected = [
        row
        for row in rows
        if category in " ".join(row["blocker_categories"] + row["warning_categories"] + [row["case_id"]])
    ]
    _write_csv(path, selected or rows)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            normalized = {
                key: ";".join(str(item) for item in value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            writer.writerow(normalized)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
