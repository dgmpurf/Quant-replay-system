"""Synthetic report-only Tiny PIT real reviewed package candidate contract fixture.

This module creates deterministic contract-fixture artifacts only. It does not
read real CSVs, discover real reviewed packages, validate PIT admissibility,
create active inputs, run replay, create labels, train models, create
stock_profile artifacts, authorize buy-review, validate performance, or allow
broker/API/order/message/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


NO_REAL_REVIEWED_PACKAGE_CANDIDATE = "NO_REAL_REVIEWED_PACKAGE_CANDIDATE"
REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY"
)
REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW = "REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW"
REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING"
)
REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE"
)
REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY"
)
REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY"
)
REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM = (
    "REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM"
)
REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW = (
    "REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW"
)

TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY = (
    "TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY"
)

CREATED_AT = "2026-06-30T00:00:00Z"
FIXTURE_VERSION = "v0.1"
WORKFLOW_NAME = "tiny_pit_real_reviewed_package_candidate_contract_fixture"
DEFAULT_OUTPUT_ROOT = (
    "outputs/reports/manual_diagnostics/"
    "tiny_pit_real_reviewed_package_candidate_contract_fixture_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Tiny PIT Real Reviewed Package Candidate Contract Fixture Artifact Views / "
    "Index / Health / Status Report-Only v0.1"
)

FORBIDDEN_STATUS_WORDING = [
    "PACKAGE_APPROVED",
    "PACKAGE_ADMISSIBLE",
    "PIT_ADMISSIBLE_PACKAGE",
    "READY_FOR_REPLAY",
    "REPLAY_INPUT_READY",
    "ACTIVE_REPLAY_INPUT_READY",
    "APPROVED_FOR_ACTIVE_INPUT",
    "ACTIVE_REVIEWED_INPUT",
    "TRADING_READY",
    "BUY_REVIEW_READY",
]

SAFETY_FALSE_FLAGS = [
    "real_reviewed_csv_package_created",
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
    "report": "real_reviewed_package_candidate_contract_fixture_report.md",
    "package_section_contract": "package_section_contract.csv",
    "field_family_contract": "field_family_contract.csv",
    "available_time_case_matrix": "available_time_case_matrix.csv",
    "source_hash_revision_case_matrix": "source_hash_revision_case_matrix.csv",
    "reviewer_authority_case_matrix": "reviewer_authority_case_matrix.csv",
    "quality_limitation_case_matrix": "quality_limitation_case_matrix.csv",
    "status_vocabulary": "status_vocabulary.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "limitations": "limitations.md",
}

CASE_COLUMNS = [
    "case_id",
    "purpose",
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
        "required_fields": (
            "package_id;package_version;package_type;package_created_at;package_created_by;"
            "package_scope;package_status;report_only;diagnostic_only;real_package_candidate_only"
        ),
        "blocker_warning_behavior": "Required identity gaps block schema completeness.",
        "future_test_expectation": "Missing required package manifest or identity fields block.",
    },
    {
        "field_family": "source_lineage",
        "required_fields": (
            "source_id;source_name;source_type;permission_class;source_url_or_reference;"
            "source_registered;source_permission_allowed;storage_policy_allowed"
        ),
        "blocker_warning_behavior": "Missing source lineage blocks.",
        "future_test_expectation": "Source name alone is not enough.",
    },
    {
        "field_family": "hash_revision",
        "required_fields": (
            "source_hash;source_hash_algorithm;local_file_hash;local_file_hash_algorithm;"
            "revision_id;revision_timestamp;revision_policy;revision_conflict_status"
        ),
        "blocker_warning_behavior": "Missing source_hash, local_file_hash, or revision_id blocks.",
        "future_test_expectation": "Hashes are distinct and revision conflicts block.",
    },
    {
        "field_family": "timing",
        "required_fields": (
            "replay_decision_time;available_time;available_time_basis;event_date;period_end;"
            "document_publish_time;fetched_at;reviewed_at;local_csv_created_at;"
            "future_revision_risk;future_label_excluded"
        ),
        "blocker_warning_behavior": "Missing, late, or conflicting available_time blocks.",
        "future_test_expectation": "Date fields alone do not pass available_time checks.",
    },
    {
        "field_family": "reviewer",
        "required_fields": (
            "reviewer_id;reviewer_role;reviewer_scope;reviewer_authority;"
            "reviewer_attestation;reviewer_attestation_time;reviewer_limitations;"
            "reviewer_approval_does_not_override_pit_failure"
        ),
        "blocker_warning_behavior": "Missing reviewer identity, scope, or authority blocks.",
        "future_test_expectation": "Reviewer approval cannot override blockers.",
    },
    {
        "field_family": "quality",
        "required_fields": (
            "quality_status;manual_review_status;validation_issue_count;warning_count;"
            "blocker_count;limitation_count;malformed_field_count;missing_required_section_count"
        ),
        "blocker_warning_behavior": "Failed quality or positive blockers block.",
        "future_test_expectation": "Quality accepted is review context only.",
    },
    {
        "field_family": "limitation",
        "required_fields": "limitation_id;limitation_note;affected_section;severity;required_next_review",
        "blocker_warning_behavior": "Warnings or blockers require visible limitation notes.",
        "future_test_expectation": "Limitation notes remain visible.",
    },
    {
        "field_family": "forbidden_downstream_flags",
        "required_fields": ";".join(SAFETY_FALSE_FLAGS),
        "blocker_warning_behavior": "Missing flags or true forbidden flags block.",
        "future_test_expectation": "Valid cases keep all activation/trading/data-write flags false.",
    },
]


@dataclass(frozen=True)
class RealReviewedPackageCandidateContractFixtureArtifacts:
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


def real_reviewed_package_candidate_contract_fixture_statuses() -> list[str]:
    return [
        NO_REAL_REVIEWED_PACKAGE_CANDIDATE,
        REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
        REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
        REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
        REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
        REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
        REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
        REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
        REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW,
    ]


def real_reviewed_package_candidate_contract_fixture_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def default_real_reviewed_package_candidate_contract_fixture_cases() -> list[dict[str, Any]]:
    cases = [
        _case(
            "minimal_schema_designed_report_only",
            "Baseline complete synthetic contract shape.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
            "PASS",
            why="Schema design only; no package candidate exists.",
        ),
        _case(
            "no_real_reviewed_package_candidate",
            "No real package candidate exists.",
            NO_REAL_REVIEWED_PACKAGE_CANDIDATE,
            "PASS",
            why="Absence is benign report-only context.",
        ),
        _case(
            "report_only_pass_candidate_for_human_review",
            "Complete synthetic package-candidate shape for human review semantics.",
            REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW,
            "PASS",
            pass_candidate=True,
            why="Synthetic pass-candidate for human review only; not PIT pass or active input.",
        ),
        _case(
            "missing_package_manifest",
            "Required package manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["missing_section"],
        ),
        _case(
            "missing_source_registry_snapshot",
            "Source registry snapshot missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["source_lineage", "missing_section"],
        ),
        _case(
            "missing_raw_document_reference_manifest",
            "Raw document/reference manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["source_lineage", "missing_section"],
        ),
        _case(
            "missing_reviewed_file_manifest",
            "Reviewed file manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["file_integrity", "missing_section"],
        ),
        _case(
            "missing_table_schema_manifest",
            "Table schema manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["schema", "missing_section"],
        ),
        _case(
            "missing_row_lineage_manifest",
            "Row lineage manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["row_lineage", "missing_section"],
        ),
        _case(
            "missing_available_time_manifest",
            "available_time manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing", "missing_section"],
        ),
        _case(
            "missing_source_hash_revision_manifest",
            "Hash/revision manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["hash_revision", "missing_section"],
        ),
        _case(
            "missing_reviewer_attestation_manifest",
            "Reviewer attestation manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority", "missing_section"],
        ),
        _case(
            "missing_quality_review_manifest",
            "Quality review manifest missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["quality", "missing_section"],
        ),
        _case(
            "missing_forbidden_downstream_flags",
            "Forbidden downstream flags missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["forbidden_downstream"],
        ),
        _case(
            "missing_available_time",
            "available_time missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "available_time_after_replay_decision_time",
            "available_time after replay decision time.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "conflicting_available_time",
            "Conflicting available_time evidence.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "future_revision_risk",
            "Future source revision risk.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["future_revision_risk"],
        ),
        _case(
            "missing_source_hash",
            "source_hash missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["source_hash"],
        ),
        _case(
            "missing_local_file_hash",
            "local_file_hash missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["local_file_hash"],
        ),
        _case(
            "missing_revision_id",
            "revision_id missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["revision_id"],
            warnings=["needs_pro_review"],
        ),
        _case(
            "revision_conflict",
            "Revision metadata conflict.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["revision_conflict"],
        ),
        _case(
            "missing_reviewer_id",
            "reviewer_id missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority"],
        ),
        _case(
            "missing_reviewer_scope",
            "reviewer_scope missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority"],
        ),
        _case(
            "missing_reviewer_authority",
            "reviewer_authority missing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority"],
        ),
        _case(
            "reviewer_approval_attempts_to_override_pit_failure",
            "Reviewer approval attempts to override PIT failure.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing", "reviewer_non_override"],
            why="Reviewer approval does not override PIT failure.",
        ),
        _case(
            "quality_failed",
            "quality_status failed.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["quality"],
        ),
        _case(
            "warning_without_limitation_note",
            "Warning lacks limitation note.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["limitation_missing"],
        ),
        _case(
            "blocker_count_positive",
            "blocker_count positive.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["blocker_count_positive"],
        ),
        _case(
            "forbidden_downstream_flag_true",
            "Forbidden downstream flag true.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["forbidden_downstream"],
        ),
        _case(
            "unsafe_status_wording_ready_for_replay",
            "Unsafe ready-for-replay status wording.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["unsafe_wording"],
        ),
        _case(
            "unsafe_status_wording_active_replay_input_ready",
            "Unsafe active replay input ready wording.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["unsafe_wording"],
        ),
        _case(
            "future_label_leakage",
            "Future label leakage present.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["future_label_leakage"],
        ),
        _case(
            "protected_data_write_claimed",
            "Protected data write claimed.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_FORBIDDEN_DOWNSTREAM,
            "FAIL",
            blockers=["protected_write"],
        ),
        _case(
            "malformed_metadata",
            "Malformed metadata.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["malformed_metadata"],
        ),
    ]
    cases.extend(_variant_cases())
    return cases

def validate_real_reviewed_package_candidate_contract_fixture_case(case: dict[str, Any]) -> dict[str, Any]:
    blocker_categories = list(case.get("blocker_categories", []))
    warning_categories = list(case.get("warning_categories", []))
    result = {
        "case_id": str(case["case_id"]),
        "purpose": str(case["purpose"]),
        "status": str(case["status"]),
        "health_status": str(case["health_status"]),
        "blocker_categories": blocker_categories,
        "warning_categories": warning_categories,
        "blocker_count": len(blocker_categories),
        "warning_count": len(warning_categories),
        "pass_candidate": bool(case.get("pass_candidate", False)),
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "why_report_only": str(
            case.get(
                "why_report_only",
                "Synthetic contract fixture only; not PIT pass, active input, replay input, or trading.",
            )
        ),
    }
    result.update(real_reviewed_package_candidate_contract_fixture_safety_flags())
    return result


def build_real_reviewed_package_candidate_contract_fixture_artifacts(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> RealReviewedPackageCandidateContractFixtureArtifacts:
    root = _validated_output_root(Path(output_root))
    cases = default_real_reviewed_package_candidate_contract_fixture_cases()
    case_results = [validate_real_reviewed_package_candidate_contract_fixture_case(case) for case in cases]
    fixture_id = _hash_payload({"cases": [case["case_id"] for case in cases], "version": FIXTURE_VERSION})
    artifact_dir = root / fixture_id
    paths = _artifact_paths(artifact_dir)
    pass_count = sum(1 for case in case_results if case["health_status"] == "PASS")
    warn_count = sum(1 for case in case_results if case["health_status"] == "WARN")
    fail_count = sum(1 for case in case_results if case["health_status"] == "FAIL")
    result = RealReviewedPackageCandidateContractFixtureArtifacts(
        fixture_id=fixture_id,
        fixture_version=FIXTURE_VERSION,
        workflow_name=WORKFLOW_NAME,
        workflow_stage=TINY_PIT_REAL_REVIEWED_PACKAGE_CANDIDATE_CONTRACT_FIXTURE_CREATED_REPORT_ONLY,
        status=REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
        health_status="PASS",
        created_at=CREATED_AT,
        case_count=len(case_results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        blocker_count=sum(int(case["blocker_count"]) for case in case_results),
        warning_count=sum(int(case["warning_count"]) for case in case_results),
        report_only=True,
        diagnostic_only=True,
        synthetic_only=True,
        artifact_path=artifact_dir,
        report_path=paths["report"],
        artifact_paths=paths,
        case_results=case_results,
    )
    write_real_reviewed_package_candidate_contract_fixture_artifacts(result)
    return result


def write_real_reviewed_package_candidate_contract_fixture_artifacts(
    result: RealReviewedPackageCandidateContractFixtureArtifacts,
) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_report(result)
    _write_csv(result.artifact_paths["package_section_contract"], _package_section_rows(result))
    _write_csv(result.artifact_paths["field_family_contract"], FIELD_FAMILY_CONTRACT)
    _write_csv(
        result.artifact_paths["available_time_case_matrix"],
        _case_rows(result, "pit_timing", "future_revision_risk"),
    )
    _write_csv(
        result.artifact_paths["source_hash_revision_case_matrix"],
        _case_rows(result, "source_hash", "local_file_hash", "revision_id", "revision_conflict"),
    )
    _write_csv(
        result.artifact_paths["reviewer_authority_case_matrix"],
        _case_rows(result, "reviewer_authority", "reviewer_non_override"),
    )
    _write_csv(
        result.artifact_paths["quality_limitation_case_matrix"],
        _case_rows(result, "quality", "limitation_missing", "blocker_count_positive"),
    )
    _write_csv(result.artifact_paths["status_vocabulary"], _status_rows())
    _write_json(
        result.artifact_paths["forbidden_downstream_flags"],
        real_reviewed_package_candidate_contract_fixture_safety_flags(),
    )
    _write_limitations(result)


def _variant_cases() -> list[dict[str, Any]]:
    return [
        _case(
            "event_date_only_is_blocked",
            "event_date alone is not available_time.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "period_end_only_is_blocked",
            "period_end alone is not available_time.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "document_publish_time_with_source_evidence_can_pass_timing",
            "document_publish_time with source evidence can support timing in a synthetic case.",
            REAL_REVIEWED_PACKAGE_REPORT_ONLY_PASS_CANDIDATE_FOR_HUMAN_REVIEW,
            "PASS",
            pass_candidate=True,
            why="Synthetic timing pass-candidate for human review only.",
        ),
        _case(
            "fetched_after_replay_with_historical_availability_evidence_needs_review_or_pass_candidate",
            "Fetch after replay with historical availability evidence needs review.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["historical_availability_review"],
        ),
        _case(
            "reviewed_at_only_is_blocked",
            "reviewed_at alone is not available_time.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "local_csv_created_at_only_is_blocked",
            "local_csv_created_at alone is not available_time.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "unknown_available_time_blocks",
            "unknown available_time blocks.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "future_revision_risk_warns_or_blocks",
            "future revision risk warns or blocks.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["future_revision_risk"],
        ),
        _case(
            "reviewer_approval_cannot_override_timing_failure",
            "Reviewer approval cannot override timing failure.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing", "reviewer_non_override"],
            why="Reviewer approval does not override timing failure.",
        ),
        _case(
            "source_hash_not_equal_local_file_hash",
            "source_hash and local_file_hash are distinct.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["hash_distinction_review"],
        ),
        _case(
            "changed_local_file_hash_requires_new_package_version",
            "Changed local_file_hash requires new package_version.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["package_version_review"],
        ),
        _case(
            "filename_as_revision_id_blocks",
            "File name cannot serve as revision_id.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["revision_id"],
        ),
        _case(
            "reviewer_attestation_without_authority_blocks",
            "Reviewer attestation without authority blocks.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority"],
        ),
        _case(
            "reviewer_approval_cannot_override_source_hash_failure",
            "Reviewer approval cannot override source_hash failure.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["source_hash", "reviewer_non_override"],
            why="Reviewer approval does not override source_hash failure.",
        ),
        _case(
            "reviewer_approval_cannot_override_available_time_failure",
            "Reviewer approval cannot override available_time failure.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing", "reviewer_non_override"],
            why="Reviewer approval does not override available_time failure.",
        ),
        _case(
            "reviewer_approval_cannot_override_revision_conflict",
            "Reviewer approval cannot override revision conflict.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["revision_conflict", "reviewer_non_override"],
            why="Reviewer approval does not override revision conflict.",
        ),
        _case(
            "reviewer_approval_cannot_override_quality_failed",
            "Reviewer approval cannot override quality failed.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["quality", "reviewer_non_override"],
            why="Reviewer approval does not override quality failure.",
        ),
        _case(
            "reviewer_approval_is_not_active_input_approval",
            "Reviewer approval is not active input approval.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["reviewer_scope_review"],
        ),
        _case(
            "quality_accepted_for_review_context_only",
            "Quality accepted for review context only.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_SCHEMA_DESIGNED_REPORT_ONLY,
            "PASS",
            why="Quality accepted is review context only.",
        ),
        _case(
            "quality_needs_review",
            "Quality needs review.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["quality_review"],
        ),
        _case(
            "quality_warning_requires_limitation_note",
            "Quality warning requires limitation note.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["limitation_visible"],
        ),
        _case(
            "quality_blocked_missing_required_section",
            "Quality blocked by missing required section.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["missing_section"],
        ),
        _case(
            "quality_blocked_malformed_field",
            "Quality blocked by malformed field.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_QUALITY,
            "FAIL",
            blockers=["malformed_field"],
        ),
        _case(
            "quality_blocked_source_lineage",
            "Quality blocked by source lineage.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_SOURCE_LINEAGE,
            "FAIL",
            blockers=["source_lineage"],
        ),
        _case(
            "quality_blocked_pit_timing",
            "Quality blocked by PIT timing.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_PIT_TIMING,
            "FAIL",
            blockers=["pit_timing"],
        ),
        _case(
            "quality_blocked_reviewer_authority",
            "Quality blocked by reviewer authority.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_BLOCKED_BY_REVIEWER_AUTHORITY,
            "FAIL",
            blockers=["reviewer_authority"],
        ),
        _case(
            "warning_count_positive_allows_needs_review_only",
            "Positive warning_count allows needs-review only.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["needs_review_only"],
        ),
        _case(
            "limitation_visible_required",
            "Limitation note must remain visible.",
            REAL_REVIEWED_PACKAGE_CANDIDATE_NEEDS_REVIEW,
            "WARN",
            warnings=["limitation_visible"],
        ),
    ]


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
        "status": status,
        "health_status": health_status,
        "blocker_categories": blockers or [],
        "warning_categories": warnings or [],
        "pass_candidate": pass_candidate,
        "why_report_only": why
        or "Synthetic contract fixture only; not PIT pass, active input, replay input, or trading.",
    }


REQUIRED_CASE_IDS = [case["case_id"] for case in default_real_reviewed_package_candidate_contract_fixture_cases()]


def _validated_output_root(root: Path) -> Path:
    normalized = root.as_posix().lower()
    forbidden_fragments = {
        "data/raw",
        "data/processed",
        "data/cache",
        "docs/project_sources",
    }
    if any(fragment in normalized for fragment in forbidden_fragments):
        raise ValueError(f"Unsafe real reviewed package candidate contract fixture output root: {root}")
    resolved_root = root.resolve(strict=False)
    artifact_dir = (resolved_root / "_guard").resolve(strict=False)
    if not artifact_dir.is_relative_to(resolved_root):
        raise ValueError(f"Output path escapes requested root: {root}")
    return root


def _artifact_paths(artifact_dir: Path) -> dict[str, Path]:
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _metadata(result: RealReviewedPackageCandidateContractFixtureArtifacts) -> dict[str, Any]:
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
        "real_csv_required": False,
        "real_csv_consumed": False,
        "real_package_candidate_created": False,
        "artifact_path": str(result.artifact_path),
        "report_path": str(result.report_path),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
    }
    metadata.update(real_reviewed_package_candidate_contract_fixture_safety_flags())
    return metadata


def _package_section_rows(result: RealReviewedPackageCandidateContractFixtureArtifacts) -> list[dict[str, Any]]:
    sections = [
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
    return [
        {
            "fixture_id": result.fixture_id,
            "section_name": section,
            "required": True,
            "missing_behavior": "BLOCK",
            "what_it_proves": "Synthetic contract section is represented.",
            "what_it_does_not_prove": "Does not prove PIT admissibility or active input readiness.",
            "report_only": True,
            "diagnostic_only": True,
            "synthetic_only": True,
        }
        for section in sections
    ]


def _case_rows(result: RealReviewedPackageCandidateContractFixtureArtifacts, *categories: str) -> list[dict[str, Any]]:
    selected = []
    for row in result.case_results:
        row_categories = set(row["blocker_categories"]) | set(row["warning_categories"])
        if row_categories.intersection(categories):
            selected.append(_csv_ready(row))
    return selected or [_csv_ready(row) for row in result.case_results[:1]]


def _status_rows() -> list[dict[str, Any]]:
    return [
        {
            "status": status,
            "allowed": True,
            "forbidden_interpretation": "Never implies real replay input, active replay input, ACTIVE_REPLAY_INPUT_READY, or trading.",
            "active_reviewed_input_candidate_created": False,
            "real_replay_input_created": False,
            "active_replay_input": False,
            "active_replay_input_ready_emitted": False,
            "trading_allowed": False,
        }
        for status in real_reviewed_package_candidate_contract_fixture_statuses()
    ]


def _write_report(result: RealReviewedPackageCandidateContractFixtureArtifacts) -> None:
    lines = [
        "# Tiny PIT Real Reviewed Package Candidate Contract Fixture v0.1",
        "",
        "This artifact is synthetic-only, report-only, and diagnostic-only.",
        "",
        "It is not a real reviewed CSV package, not a real PIT validator, not an active reviewed input candidate, "
        "not real replay input, not active replay input, and not ACTIVE_REPLAY_INPUT_READY.",
        "",
        "It creates no replay execution, labels, training, metrics, signal_score, model, stock_profile, paper, "
        "buy-review, performance validation, trading, or data/raw, data/processed, or data/cache writes.",
        "",
        f"- Fixture id: `{result.fixture_id}`",
        f"- Workflow stage: `{result.workflow_stage}`",
        f"- Status: `{result.status}`",
        f"- Health: `{result.health_status}`",
        f"- Case count: `{result.case_count}`",
        f"- Fail case count: `{result.fail_count}`",
        "",
        "Case-level FAIL/WARN rows are expected synthetic diagnostics and do not make the aggregate artifact unhealthy.",
        "",
        "## Case Summary",
        "",
        "| Case | Status | Health | Blockers | Warnings | Pass Candidate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result.case_results:
        lines.append(
            f"| `{row['case_id']}` | `{row['status']}` | `{row['health_status']}` | "
            f"{row['blocker_count']} | {row['warning_count']} | {row['pass_candidate']} |"
        )
    lines.extend(["", "## Recommended Next Task", "", RECOMMENDED_NEXT_TASK])
    result.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_limitations(result: RealReviewedPackageCandidateContractFixtureArtifacts) -> None:
    lines = [
        "# Tiny PIT Real Reviewed Package Candidate Contract Fixture Limitations",
        "",
        "- Synthetic contract fixture only.",
        "- No real CSV is required, read, copied, or validated.",
        "- No real reviewed package candidate is created.",
        "- No real PIT admissibility is proven.",
        "- No active reviewed input candidate, active replay input, or ACTIVE_REPLAY_INPUT_READY is created.",
        "- No replay execution, labels, training, model, stock_profile, paper, buy-review, performance validation, or trading is created.",
        "- No data/raw, data/processed, or data/cache writes are allowed.",
        "",
        f"Fixture id: `{result.fixture_id}`",
    ]
    result.artifact_paths["limitations"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not rows:
            handle.write("\n")
            return
        columns = list(rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _csv_ready(row: dict[str, Any]) -> dict[str, Any]:
    ready = {}
    for key, value in row.items():
        if isinstance(value, list):
            ready[key] = ";".join(str(item) for item in value)
        else:
            ready[key] = value
    return ready


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
