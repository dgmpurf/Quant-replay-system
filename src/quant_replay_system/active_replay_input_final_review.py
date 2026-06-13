"""Report-only active replay input final-review workflow.

This workflow deliberately stops at ``FINAL_REVIEW_READY_FOR_EMISSION_REVIEW``.
It never emits ``ACTIVE_REPLAY_INPUT_READY`` and never creates active replay
input, runs replay, computes labels, trains weights, creates stock profiles,
changes buy-review eligibility, writes data stores, calls APIs, or mutates
cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_FINAL_REVIEW_PACKAGE = "NO_FINAL_REVIEW_PACKAGE"
FINAL_REVIEW_PACKAGE_FOUND = "FINAL_REVIEW_PACKAGE_FOUND"
FINAL_REVIEW_LINEAGE_BLOCKED = "FINAL_REVIEW_LINEAGE_BLOCKED"
FINAL_REVIEW_AUTHORITY_BLOCKED = "FINAL_REVIEW_AUTHORITY_BLOCKED"
FINAL_REVIEW_ATTESTATION_BLOCKED = "FINAL_REVIEW_ATTESTATION_BLOCKED"
FINAL_REVIEW_PIT_BLOCKED = "FINAL_REVIEW_PIT_BLOCKED"
FINAL_REVIEW_SOURCE_BLOCKED = "FINAL_REVIEW_SOURCE_BLOCKED"
FINAL_REVIEW_EVIDENCE_BLOCKED = "FINAL_REVIEW_EVIDENCE_BLOCKED"
FINAL_REVIEW_TAXONOMY_BLOCKED = "FINAL_REVIEW_TAXONOMY_BLOCKED"
FINAL_REVIEW_LEAKAGE_BLOCKED = "FINAL_REVIEW_LEAKAGE_BLOCKED"
FINAL_REVIEW_SIDE_EFFECT_BLOCKED = "FINAL_REVIEW_SIDE_EFFECT_BLOCKED"
FINAL_REVIEW_OVERCLAIM_BLOCKED = "FINAL_REVIEW_OVERCLAIM_BLOCKED"
FINAL_REVIEW_REVIEW_BLOCKED = "FINAL_REVIEW_REVIEW_BLOCKED"
FINAL_REVIEW_READY_FOR_EMISSION_REVIEW = "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW"

ACTIVE_READY_READY_FOR_FINAL_REVIEW = "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
FORBIDDEN_ACTIVE_READY_STATUS = "ACTIVE_REPLAY_INPUT_READY"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_final_review_v0_1")
PASS_RESULTS = {"PASS", "ACCEPTED", "ACCEPTED_FOR_REVIEW_ONLY", "READY", "READY_FOR_REVIEW"}

LEAKAGE_FALSE_FIELDS = [
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
]
OVERCLAIM_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "real_buy_review_eligible",
]
SIDE_EFFECT_FALSE_FIELDS = [
    "approval_applied",
    "order_placed",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]
SAFE_FALSE_FIELDS = LEAKAGE_FALSE_FIELDS + OVERCLAIM_FALSE_FIELDS + SIDE_EFFECT_FALSE_FIELDS

PACKAGE_REQUIRED_FIELDS = [
    "final_review_package_id",
    "requested_by",
    "requested_at",
    "package_reason",
    "active_ready_artifact_ref",
    "requested_status",
]
AUTHORITY_FIELDS = [
    "final_review_authority_id",
    "primary_reviewer",
    "second_reviewer",
    "pit_source_reviewer",
    "evidence_taxonomy_reviewer",
    "risk_compliance_reviewer",
    "system_operator",
    "strategy_owner",
    "authority_scope",
]
ATTESTATION_TRUE_FIELDS = [
    "primary_reviewer_attested",
    "second_reviewer_attested",
    "pit_source_reviewer_attested",
    "evidence_taxonomy_reviewer_attested",
    "risk_compliance_reviewer_attested",
    "no_trading_authority_attested",
    "no_performance_claim_attested",
    "no_replay_execution_attested",
    "report_only",
    "diagnostic_only",
]
PIT_FIELDS = [
    "pit_universe_evidence_attached",
    "available_time_coverage_attached",
]
SOURCE_FIELDS = [
    "source_id_coverage_attached",
    "source_hash_coverage_attached",
    "revision_id_coverage_attached",
    "permission_class_coverage_attached",
    "quality_status_coverage_attached",
]
EVIDENCE_FIELDS = [
    "raw_evidence_refs_attached",
    "replay_evidence_bundle_ref_attached",
    "factor_definition_coverage_attached",
    "factor_observation_coverage_attached",
    "event_structured_coverage_attached",
    "company_exposure_coverage_attached",
]
TAXONOMY_TRUE_FIELDS = [
    "uses_8_layer_taxonomy",
    "not_fixed_12_only",
    "factor_layer_metadata_attached",
    "trade_usage_metadata_attached",
    "compliance_metadata_attached",
    "report_only",
    "diagnostic_only",
]
LEAKAGE_TRUE_FIELDS = [
    "no_future_labels",
    "no_forward_returns",
    "no_training_outputs",
    "no_model_weights",
    "no_stock_profile_artifacts",
    "no_buy_review_eligibility",
    "no_approved_for_paper",
]
SIDE_EFFECT_TRUE_FIELDS = [
    "no_order_placed",
    "no_message_sent",
    "no_broker_api_called",
    "no_llm_api_called",
    "no_external_api_called",
    "no_cache_mutated",
    "no_data_raw_written",
    "no_data_processed_written",
    "no_data_cache_written",
    "no_current_candidates_run",
    "no_snapshot_built",
    "no_signal_semantics_changed",
]
OVERCLAIM_TRUE_FIELDS = [
    "pass_candidate_not_active_ready",
    "smoke_not_active_ready",
    "promotion_not_active_ready",
    "acceptance_not_active_ready",
    "active_ready_final_review_not_active_ready",
    "final_review_ready_not_active_input_ready",
    "active_input_ready_not_replay",
    "active_input_ready_not_labels",
    "active_input_ready_not_training",
    "active_input_ready_not_stock_profile",
    "active_input_ready_not_buy_review",
    "active_input_ready_not_trading",
    "active_input_ready_not_performance_validation",
    "report_only",
    "diagnostic_only",
]
EMISSION_FALSE_FIELDS = [
    "allow_active_replay_input_ready_emission",
    "allow_active_replay_input_creation",
    "allow_replay_execution",
    "allow_forward_labels",
    "allow_training",
    "allow_stock_profile",
    "allow_buy_review",
    "allow_trading",
]


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewSettings:
    active_ready_artifact: Path | None = None
    active_ready_health_artifact: Path | None = None
    active_ready_status_artifact: Path | None = None
    final_review_package_manifest: Path | None = None
    final_review_authority_manifest: Path | None = None
    final_review_attestation_manifest: Path | None = None
    pit_source_evidence_attachment_bundle: Path | None = None
    taxonomy_attachment_bundle: Path | None = None
    leakage_side_effect_evidence_bundle: Path | None = None
    overclaim_evidence_bundle: Path | None = None
    emission_request_manifest: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewPackageResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewLineageResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewAuthorityResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewAttestationResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewPitSourceEvidenceResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewTaxonomyResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewLeakageSideEffectResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewOverclaimResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewEmissionReadinessResult(ActiveReplayInputFinalReviewPackageResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputFinalReviewResult:
    final_review_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    package_results: list[ActiveReplayInputFinalReviewPackageResult]
    lineage_results: list[ActiveReplayInputFinalReviewLineageResult]
    authority_results: list[ActiveReplayInputFinalReviewAuthorityResult]
    attestation_results: list[ActiveReplayInputFinalReviewAttestationResult]
    pit_source_evidence_results: list[ActiveReplayInputFinalReviewPitSourceEvidenceResult]
    taxonomy_results: list[ActiveReplayInputFinalReviewTaxonomyResult]
    leakage_side_effect_results: list[ActiveReplayInputFinalReviewLeakageSideEffectResult]
    overclaim_results: list[ActiveReplayInputFinalReviewOverclaimResult]
    emission_readiness_results: list[ActiveReplayInputFinalReviewEmissionReadinessResult]
    active_ready_artifact_path: str
    active_ready_health_artifact_path: str
    active_ready_status_artifact_path: str
    final_review_package_manifest_path: str
    final_review_authority_manifest_path: str
    final_review_attestation_manifest_path: str
    pit_source_evidence_attachment_bundle_path: str
    taxonomy_attachment_bundle_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    emission_request_manifest_path: str
    package_gate_count: int
    passed_package_gate_count: int
    blocked_package_gate_count: int
    lineage_gate_count: int
    passed_lineage_gate_count: int
    blocked_lineage_gate_count: int
    authority_gate_count: int
    passed_authority_gate_count: int
    blocked_authority_gate_count: int
    attestation_gate_count: int
    passed_attestation_gate_count: int
    blocked_attestation_gate_count: int
    pit_source_evidence_gate_count: int
    passed_pit_source_evidence_gate_count: int
    blocked_pit_source_evidence_gate_count: int
    taxonomy_gate_count: int
    passed_taxonomy_gate_count: int
    blocked_taxonomy_gate_count: int
    leakage_side_effect_gate_count: int
    passed_leakage_side_effect_gate_count: int
    blocked_leakage_side_effect_gate_count: int
    issue_count: int
    blocker_count: int
    warning_count: int
    ready_for_emission_review: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    approval_applied: bool
    order_placed: bool
    message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    data_raw_written: bool
    data_processed_written: bool
    data_cache_written: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    artifact_paths: dict[str, Path]


def run_active_replay_input_final_review(
    settings: ActiveReplayInputFinalReviewSettings | None = None,
) -> ActiveReplayInputFinalReviewResult:
    settings = settings or ActiveReplayInputFinalReviewSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    final_review_run_id = _build_run_id(settings, generated_at)
    artifact_path = Path(settings.output_dir) / final_review_run_id

    package_payload = _read_json(settings.final_review_package_manifest)
    active_ready_payload = _load_artifact_payload(settings.active_ready_artifact, "active_ready_metadata.json")
    health_payload = _read_json(settings.active_ready_health_artifact)
    status_payload = _read_json(settings.active_ready_status_artifact)

    package_results = _check_package(settings, package_payload)
    lineage_results = _check_active_ready_lineage(settings, active_ready_payload, health_payload, status_payload)
    authority_results = _check_authority(settings)
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    taxonomy_results = _check_taxonomy(settings)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)
    emission_results = _check_emission_request(settings)

    safety_payloads = [
        payload
        for payload in [
            package_payload,
            active_ready_payload,
            status_payload,
        ]
        if payload
    ]
    leakage_side_effect_results.extend(_check_unsafe_false_fields(safety_payloads, LEAKAGE_FALSE_FIELDS, FINAL_REVIEW_LEAKAGE_BLOCKED))
    leakage_side_effect_results.extend(
        _check_unsafe_false_fields(safety_payloads, SIDE_EFFECT_FALSE_FIELDS, FINAL_REVIEW_SIDE_EFFECT_BLOCKED)
    )
    overclaim_results.extend(_check_unsafe_false_fields(safety_payloads, OVERCLAIM_FALSE_FIELDS, FINAL_REVIEW_OVERCLAIM_BLOCKED))
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    status = _resolve_status(
        package_results=package_results,
        lineage_results=lineage_results,
        authority_results=authority_results,
        attestation_results=attestation_results,
        pit_source_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
        emission_results=emission_results,
    )
    ready_for_emission_review = status == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW
    blockers = (
        _blocked(package_results)
        + _blocked(lineage_results)
        + _blocked(authority_results)
        + _blocked(attestation_results)
        + _blocked(pit_source_results)
        + _blocked(taxonomy_results)
        + _blocked(leakage_side_effect_results)
        + _blocked(overclaim_results)
        + _blocked(emission_results)
    )
    result = ActiveReplayInputFinalReviewResult(
        final_review_run_id=final_review_run_id,
        generated_at=generated_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=status,
        package_results=package_results,
        lineage_results=lineage_results,
        authority_results=authority_results,
        attestation_results=attestation_results,
        pit_source_evidence_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
        emission_readiness_results=emission_results,
        active_ready_artifact_path=_path_str(settings.active_ready_artifact),
        active_ready_health_artifact_path=_path_str(settings.active_ready_health_artifact),
        active_ready_status_artifact_path=_path_str(settings.active_ready_status_artifact),
        final_review_package_manifest_path=_path_str(settings.final_review_package_manifest),
        final_review_authority_manifest_path=_path_str(settings.final_review_authority_manifest),
        final_review_attestation_manifest_path=_path_str(settings.final_review_attestation_manifest),
        pit_source_evidence_attachment_bundle_path=_path_str(settings.pit_source_evidence_attachment_bundle),
        taxonomy_attachment_bundle_path=_path_str(settings.taxonomy_attachment_bundle),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle),
        emission_request_manifest_path=_path_str(settings.emission_request_manifest),
        package_gate_count=len(package_results),
        passed_package_gate_count=_passed(package_results),
        blocked_package_gate_count=_blocked(package_results),
        lineage_gate_count=len(lineage_results),
        passed_lineage_gate_count=_passed(lineage_results),
        blocked_lineage_gate_count=_blocked(lineage_results),
        authority_gate_count=len(authority_results),
        passed_authority_gate_count=_passed(authority_results),
        blocked_authority_gate_count=_blocked(authority_results),
        attestation_gate_count=len(attestation_results),
        passed_attestation_gate_count=_passed(attestation_results),
        blocked_attestation_gate_count=_blocked(attestation_results),
        pit_source_evidence_gate_count=len(pit_source_results),
        passed_pit_source_evidence_gate_count=_passed(pit_source_results),
        blocked_pit_source_evidence_gate_count=_blocked(pit_source_results),
        taxonomy_gate_count=len(taxonomy_results),
        passed_taxonomy_gate_count=_passed(taxonomy_results),
        blocked_taxonomy_gate_count=_blocked(taxonomy_results),
        leakage_side_effect_gate_count=len(leakage_side_effect_results),
        passed_leakage_side_effect_gate_count=_passed(leakage_side_effect_results),
        blocked_leakage_side_effect_gate_count=_blocked(leakage_side_effect_results),
        issue_count=blockers,
        blocker_count=blockers,
        warning_count=0,
        ready_for_emission_review=ready_for_emission_review,
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        approval_applied=False,
        order_placed=False,
        message_sent=False,
        llm_api_called=False,
        external_api_called=False,
        cache_mutated=False,
        data_raw_written=False,
        data_processed_written=False,
        data_cache_written=False,
        current_candidates_run=False,
        snapshot_built=False,
        signal_semantics_changed=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        overclaim_guard_pass_count=_passed(overclaim_results),
        overclaim_guard_total_count=len(overclaim_results),
        artifact_paths=resolve_active_replay_input_final_review_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_active_replay_input_final_review_artifacts(result)
    return result


def resolve_active_replay_input_final_review_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "final_review_metadata.json",
        "final_review_report": artifact_path / "final_review_report.md",
        "final_review_package_manifest_results": artifact_path / "final_review_package_manifest_results.csv",
        "active_ready_lineage_results": artifact_path / "active_ready_lineage_results.csv",
        "final_reviewer_authority_results": artifact_path / "final_reviewer_authority_results.csv",
        "final_reviewer_attestation_results": artifact_path / "final_reviewer_attestation_results.csv",
        "pit_source_evidence_attachment_results": artifact_path / "pit_source_evidence_attachment_results.csv",
        "taxonomy_attachment_results": artifact_path / "taxonomy_attachment_results.csv",
        "leakage_side_effect_evidence_results": artifact_path / "leakage_side_effect_evidence_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "emission_readiness_results": artifact_path / "emission_readiness_results.csv",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_final_review_artifacts(result: ActiveReplayInputFinalReviewResult) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_results(result.artifact_paths["final_review_package_manifest_results"], result.package_results)
    _write_results(result.artifact_paths["active_ready_lineage_results"], result.lineage_results)
    _write_results(result.artifact_paths["final_reviewer_authority_results"], result.authority_results)
    _write_results(result.artifact_paths["final_reviewer_attestation_results"], result.attestation_results)
    _write_results(result.artifact_paths["pit_source_evidence_attachment_results"], result.pit_source_evidence_results)
    _write_results(result.artifact_paths["taxonomy_attachment_results"], result.taxonomy_results)
    _write_results(result.artifact_paths["leakage_side_effect_evidence_results"], result.leakage_side_effect_results)
    _write_results(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)
    _write_results(result.artifact_paths["emission_readiness_results"], result.emission_readiness_results)
    result.artifact_paths["final_review_report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _check_package(
    settings: ActiveReplayInputFinalReviewSettings,
    payload: dict[str, Any] | None,
) -> list[ActiveReplayInputFinalReviewPackageResult]:
    if not payload:
        return [
            ActiveReplayInputFinalReviewPackageResult(
                gate_group="final_review_package",
                gate_name="final_review_package_manifest",
                status=NO_FINAL_REVIEW_PACKAGE,
                passed=False,
                blocker_reason="Final-review package manifest is missing or unreadable.",
                evidence_path=_path_str(settings.final_review_package_manifest),
            )
        ]
    results = [
        _row(
            ActiveReplayInputFinalReviewPackageResult,
            "final_review_package",
            field,
            _present(payload.get(field)),
            FINAL_REVIEW_REVIEW_BLOCKED,
            _path_str(settings.final_review_package_manifest),
            payload.get(field),
            f"Missing final-review package field {field}.",
        )
        for field in PACKAGE_REQUIRED_FIELDS
    ]
    results.append(
        _row(
            ActiveReplayInputFinalReviewPackageResult,
            "final_review_package",
            "requested_status",
            payload.get("requested_status") == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW,
            FINAL_REVIEW_REVIEW_BLOCKED,
            _path_str(settings.final_review_package_manifest),
            payload.get("requested_status"),
            "First implementation only accepts FINAL_REVIEW_READY_FOR_EMISSION_REVIEW requests.",
        )
    )
    results.extend(_report_only_rows(ActiveReplayInputFinalReviewPackageResult, "final_review_package", payload, settings.final_review_package_manifest, FINAL_REVIEW_REVIEW_BLOCKED))
    return results


def _check_active_ready_lineage(
    settings: ActiveReplayInputFinalReviewSettings,
    payload: dict[str, Any] | None,
    health_payload: dict[str, Any] | None,
    status_payload: dict[str, Any] | None,
) -> list[ActiveReplayInputFinalReviewLineageResult]:
    if not payload:
        return [
            ActiveReplayInputFinalReviewLineageResult(
                gate_group="active_ready_lineage",
                gate_name="active_ready_artifact",
                status=FINAL_REVIEW_LINEAGE_BLOCKED,
                passed=False,
                blocker_reason="Active-ready artifact is missing or unreadable.",
                evidence_path=_path_str(settings.active_ready_artifact),
            )
        ]
    path = _path_str(settings.active_ready_artifact)
    results = [
        _row(
            ActiveReplayInputFinalReviewLineageResult,
            "active_ready_lineage",
            "active_ready_status",
            payload.get("status") == ACTIVE_READY_READY_FOR_FINAL_REVIEW,
            FINAL_REVIEW_LINEAGE_BLOCKED,
            path,
            payload.get("status"),
            "Active-ready status is not ACTIVE_READY_READY_FOR_FINAL_REVIEW.",
        ),
        _row(
            ActiveReplayInputFinalReviewLineageResult,
            "active_ready_lineage",
            "ready_for_final_review",
            _as_bool(payload.get("ready_for_final_review")),
            FINAL_REVIEW_LINEAGE_BLOCKED,
            path,
            payload.get("ready_for_final_review"),
            "Active-ready artifact is not ready for final review.",
        ),
    ]
    if "health_status" in payload:
        results.append(
            _row(
                ActiveReplayInputFinalReviewLineageResult,
                "active_ready_lineage",
                "active_ready_metadata_health",
                payload.get("health_status") == "PASS",
                FINAL_REVIEW_LINEAGE_BLOCKED,
                path,
                payload.get("health_status"),
                "Active-ready metadata health is not PASS.",
            )
        )
    if settings.active_ready_health_artifact:
        results.append(
            _row(
                ActiveReplayInputFinalReviewLineageResult,
                "active_ready_lineage",
                "active_ready_health_artifact",
                bool(health_payload) and health_payload.get("health_status", health_payload.get("status")) == "PASS",
                FINAL_REVIEW_LINEAGE_BLOCKED,
                _path_str(settings.active_ready_health_artifact),
                health_payload.get("health_status", health_payload.get("status")) if health_payload else "",
                "Active-ready health artifact is not PASS.",
            )
        )
    if settings.active_ready_status_artifact:
        results.append(
            _row(
                ActiveReplayInputFinalReviewLineageResult,
                "active_ready_lineage",
                "active_ready_status_artifact",
                bool(status_payload)
                and status_payload.get("workflow_stage", status_payload.get("status")) == ACTIVE_READY_READY_FOR_FINAL_REVIEW
                and status_payload.get("health_status") == "PASS",
                FINAL_REVIEW_LINEAGE_BLOCKED,
                _path_str(settings.active_ready_status_artifact),
                status_payload.get("workflow_stage", status_payload.get("status")) if status_payload else "",
                "Active-ready status artifact is not ACTIVE_READY_READY_FOR_FINAL_REVIEW with PASS health.",
            )
        )
    return results


def _check_authority(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewAuthorityResult]:
    payload = _read_json(settings.final_review_authority_manifest)
    if not payload:
        return [_missing(ActiveReplayInputFinalReviewAuthorityResult, "final_review_authority", "final_review_authority_manifest", FINAL_REVIEW_AUTHORITY_BLOCKED, settings.final_review_authority_manifest)]
    results = [
        _row(
            ActiveReplayInputFinalReviewAuthorityResult,
            "final_review_authority",
            field,
            _present(payload.get(field)),
            FINAL_REVIEW_AUTHORITY_BLOCKED,
            _path_str(settings.final_review_authority_manifest),
            payload.get(field),
            f"Missing authority field {field}.",
        )
        for field in AUTHORITY_FIELDS
    ]
    results.append(
        _row(
            ActiveReplayInputFinalReviewAuthorityResult,
            "final_review_authority",
            "authority_result",
            str(payload.get("authority_result", "")).upper() in PASS_RESULTS,
            FINAL_REVIEW_AUTHORITY_BLOCKED,
            _path_str(settings.final_review_authority_manifest),
            payload.get("authority_result"),
            "Authority result is not PASS.",
        )
    )
    results.extend(_report_only_rows(ActiveReplayInputFinalReviewAuthorityResult, "final_review_authority", payload, settings.final_review_authority_manifest, FINAL_REVIEW_AUTHORITY_BLOCKED))
    return results


def _check_attestation(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewAttestationResult]:
    return _check_true_manifest(
        settings.final_review_attestation_manifest,
        "final_review_attestation",
        ATTESTATION_TRUE_FIELDS,
        "attestation_result",
        FINAL_REVIEW_ATTESTATION_BLOCKED,
        ActiveReplayInputFinalReviewAttestationResult,
    )


def _check_pit_source_evidence(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewPitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_attachment_bundle)
    if not payload:
        return [_missing(ActiveReplayInputFinalReviewPitSourceEvidenceResult, "pit_source_evidence", "pit_source_evidence_attachment_bundle", FINAL_REVIEW_EVIDENCE_BLOCKED, settings.pit_source_evidence_attachment_bundle)]
    results: list[ActiveReplayInputFinalReviewPitSourceEvidenceResult] = []
    results.extend(_true_field_rows(ActiveReplayInputFinalReviewPitSourceEvidenceResult, "pit_source_evidence", PIT_FIELDS, payload, settings.pit_source_evidence_attachment_bundle, FINAL_REVIEW_PIT_BLOCKED))
    results.extend(_true_field_rows(ActiveReplayInputFinalReviewPitSourceEvidenceResult, "pit_source_evidence", SOURCE_FIELDS, payload, settings.pit_source_evidence_attachment_bundle, FINAL_REVIEW_SOURCE_BLOCKED))
    results.extend(_true_field_rows(ActiveReplayInputFinalReviewPitSourceEvidenceResult, "pit_source_evidence", EVIDENCE_FIELDS, payload, settings.pit_source_evidence_attachment_bundle, FINAL_REVIEW_EVIDENCE_BLOCKED))
    results.append(
        _row(
            ActiveReplayInputFinalReviewPitSourceEvidenceResult,
            "pit_source_evidence",
            "attachment_result",
            str(payload.get("attachment_result", "")).upper() in PASS_RESULTS,
            FINAL_REVIEW_EVIDENCE_BLOCKED,
            _path_str(settings.pit_source_evidence_attachment_bundle),
            payload.get("attachment_result"),
            "Attachment result is not PASS.",
        )
    )
    results.extend(_report_only_rows(ActiveReplayInputFinalReviewPitSourceEvidenceResult, "pit_source_evidence", payload, settings.pit_source_evidence_attachment_bundle, FINAL_REVIEW_EVIDENCE_BLOCKED))
    return results


def _check_taxonomy(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewTaxonomyResult]:
    return _check_true_manifest(
        settings.taxonomy_attachment_bundle,
        "taxonomy_attachment",
        TAXONOMY_TRUE_FIELDS,
        "taxonomy_result",
        FINAL_REVIEW_TAXONOMY_BLOCKED,
        ActiveReplayInputFinalReviewTaxonomyResult,
    )


def _check_leakage_side_effect(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle)
    if not payload:
        return [_missing(ActiveReplayInputFinalReviewLeakageSideEffectResult, "leakage_side_effect", "leakage_side_effect_evidence_bundle", FINAL_REVIEW_LEAKAGE_BLOCKED, settings.leakage_side_effect_evidence_bundle)]
    results: list[ActiveReplayInputFinalReviewLeakageSideEffectResult] = []
    results.extend(_true_field_rows(ActiveReplayInputFinalReviewLeakageSideEffectResult, "leakage_side_effect", LEAKAGE_TRUE_FIELDS, payload, settings.leakage_side_effect_evidence_bundle, FINAL_REVIEW_LEAKAGE_BLOCKED))
    results.extend(_true_field_rows(ActiveReplayInputFinalReviewLeakageSideEffectResult, "leakage_side_effect", SIDE_EFFECT_TRUE_FIELDS, payload, settings.leakage_side_effect_evidence_bundle, FINAL_REVIEW_SIDE_EFFECT_BLOCKED))
    results.append(
        _row(
            ActiveReplayInputFinalReviewLeakageSideEffectResult,
            "leakage_side_effect",
            "leakage_side_effect_result",
            str(payload.get("leakage_side_effect_result", "")).upper() in PASS_RESULTS,
            FINAL_REVIEW_LEAKAGE_BLOCKED,
            _path_str(settings.leakage_side_effect_evidence_bundle),
            payload.get("leakage_side_effect_result"),
            "Leakage/side-effect result is not PASS.",
        )
    )
    results.extend(_report_only_rows(ActiveReplayInputFinalReviewLeakageSideEffectResult, "leakage_side_effect", payload, settings.leakage_side_effect_evidence_bundle, FINAL_REVIEW_LEAKAGE_BLOCKED))
    return results


def _check_overclaim(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewOverclaimResult]:
    return _check_true_manifest(
        settings.overclaim_evidence_bundle,
        "overclaim",
        OVERCLAIM_TRUE_FIELDS,
        "overclaim_result",
        FINAL_REVIEW_OVERCLAIM_BLOCKED,
        ActiveReplayInputFinalReviewOverclaimResult,
    )


def _check_emission_request(settings: ActiveReplayInputFinalReviewSettings) -> list[ActiveReplayInputFinalReviewEmissionReadinessResult]:
    payload = _read_json(settings.emission_request_manifest)
    if not payload:
        return [_missing(ActiveReplayInputFinalReviewEmissionReadinessResult, "emission_readiness", "emission_request_manifest", FINAL_REVIEW_REVIEW_BLOCKED, settings.emission_request_manifest)]
    results = [
        _row(
            ActiveReplayInputFinalReviewEmissionReadinessResult,
            "emission_readiness",
            "requested_status",
            payload.get("requested_status") == FINAL_REVIEW_READY_FOR_EMISSION_REVIEW,
            FINAL_REVIEW_REVIEW_BLOCKED,
            _path_str(settings.emission_request_manifest),
            payload.get("requested_status"),
            "First implementation only allows FINAL_REVIEW_READY_FOR_EMISSION_REVIEW requests.",
        )
    ]
    results.extend(_report_only_rows(ActiveReplayInputFinalReviewEmissionReadinessResult, "emission_readiness", payload, settings.emission_request_manifest, FINAL_REVIEW_REVIEW_BLOCKED))
    for field in EMISSION_FALSE_FIELDS:
        safe = not _as_bool(payload.get(field))
        results.append(
            _row(
                ActiveReplayInputFinalReviewEmissionReadinessResult,
                "emission_readiness",
                field,
                safe,
                FINAL_REVIEW_REVIEW_BLOCKED,
                _path_str(settings.emission_request_manifest),
                payload.get(field),
                f"Emission request has unsafe allow flag {field}.",
            )
        )
    return results


def _check_true_manifest(path: Path | None, gate_group: str, true_fields: list[str], result_field: str, failure_status: str, row_type: type[Any]) -> list[Any]:
    payload = _read_json(path)
    if not payload:
        return [_missing(row_type, gate_group, f"{gate_group}_manifest", failure_status, path)]
    results = _true_field_rows(row_type, gate_group, true_fields, payload, path, failure_status)
    results.append(
        _row(
            row_type,
            gate_group,
            result_field,
            str(payload.get(result_field, "")).upper() in PASS_RESULTS,
            failure_status,
            _path_str(path),
            payload.get(result_field),
            f"{result_field} is not PASS.",
        )
    )
    return results


def _true_field_rows(row_type: type[Any], gate_group: str, fields: list[str], payload: dict[str, Any], path: Path | None, failure_status: str) -> list[Any]:
    return [
        _row(
            row_type,
            gate_group,
            field,
            _as_bool(payload.get(field)),
            failure_status,
            _path_str(path),
            payload.get(field),
            f"{field} is not true.",
        )
        for field in fields
    ]


def _report_only_rows(row_type: type[Any], gate_group: str, payload: dict[str, Any], path: Path | None, failure_status: str) -> list[Any]:
    return [
        _row(row_type, gate_group, "report_only", _as_bool(payload.get("report_only")), failure_status, _path_str(path), payload.get("report_only"), "Manifest is not report-only."),
        _row(row_type, gate_group, "diagnostic_only", _as_bool(payload.get("diagnostic_only")), failure_status, _path_str(path), payload.get("diagnostic_only"), "Manifest is not diagnostic-only."),
    ]


def _check_unsafe_false_fields(payloads: list[dict[str, Any]], fields: list[str], failure_status: str) -> list[Any]:
    results: list[Any] = []
    for payload in payloads:
        source = str(
            payload.get("final_review_package_id")
            or payload.get("active_ready_run_id")
            or payload.get("emission_request_id")
            or "payload"
        )
        for field in fields:
            if field in payload:
                safe = not _as_bool(payload.get(field))
                row_type = (
                    ActiveReplayInputFinalReviewLeakageSideEffectResult
                    if failure_status in {FINAL_REVIEW_LEAKAGE_BLOCKED, FINAL_REVIEW_SIDE_EFFECT_BLOCKED}
                    else ActiveReplayInputFinalReviewOverclaimResult
                )
                results.append(
                    _row(
                        row_type,
                        "safety_flag",
                        f"{source}:{field}",
                        safe,
                        failure_status,
                        source,
                        payload.get(field),
                        f"Unsafe flag {field} is true.",
                    )
                )
    return results


def _built_in_overclaim_guards(output_dir: Path) -> list[ActiveReplayInputFinalReviewOverclaimResult]:
    output_safe = _is_under(output_dir, Path("outputs/reports/manual_diagnostics"))
    guards = [
        ("replay_pass_candidate_not_active_ready", True, "REPLAY_INPUT_GATE_PASS_CANDIDATE must not be active-ready."),
        ("smoke_pass_candidate_not_active_ready", True, "SMOKE_PASS_CANDIDATE_READY must not be active-ready."),
        ("promotion_ready_not_active_ready", True, "PROMOTION_READY_FOR_HUMAN_REVIEW must not be active-ready."),
        ("acceptance_ready_not_active_ready", True, "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW must not be active-ready."),
        ("active_ready_final_review_not_active_ready", True, "ACTIVE_READY_READY_FOR_FINAL_REVIEW must not be active-ready."),
        ("final_review_ready_not_active_input_ready", True, "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW must not be ACTIVE_REPLAY_INPUT_READY."),
        ("forbidden_active_replay_input_ready_not_emitted", True, "ACTIVE_REPLAY_INPUT_READY must not be emitted."),
        ("output_path_under_manual_diagnostics", output_safe, "Output path must stay under manual_diagnostics."),
    ]
    return [
        ActiveReplayInputFinalReviewOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status=FINAL_REVIEW_PACKAGE_FOUND if passed else FINAL_REVIEW_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else reason,
            evidence_path=str(output_dir),
            observed_value=str(passed),
        )
        for name, passed, reason in guards
    ]


def _resolve_status(
    *,
    package_results: list[Any],
    lineage_results: list[Any],
    authority_results: list[Any],
    attestation_results: list[Any],
    pit_source_results: list[Any],
    taxonomy_results: list[Any],
    leakage_side_effect_results: list[Any],
    overclaim_results: list[Any],
    emission_results: list[Any],
) -> str:
    if _blocked(package_results):
        statuses = _blocked_statuses(package_results)
        if NO_FINAL_REVIEW_PACKAGE in statuses:
            return NO_FINAL_REVIEW_PACKAGE
        if FINAL_REVIEW_OVERCLAIM_BLOCKED in statuses:
            return FINAL_REVIEW_OVERCLAIM_BLOCKED
        return FINAL_REVIEW_REVIEW_BLOCKED
    for rows in [lineage_results, authority_results, attestation_results]:
        if _blocked(rows):
            return _blocked_statuses(rows)[0]
    if _blocked(pit_source_results):
        statuses = _blocked_statuses(pit_source_results)
        for status in [FINAL_REVIEW_PIT_BLOCKED, FINAL_REVIEW_SOURCE_BLOCKED, FINAL_REVIEW_EVIDENCE_BLOCKED]:
            if status in statuses:
                return status
    if _blocked(taxonomy_results):
        return FINAL_REVIEW_TAXONOMY_BLOCKED
    if _blocked(leakage_side_effect_results):
        statuses = _blocked_statuses(leakage_side_effect_results)
        if FINAL_REVIEW_LEAKAGE_BLOCKED in statuses:
            return FINAL_REVIEW_LEAKAGE_BLOCKED
        return FINAL_REVIEW_SIDE_EFFECT_BLOCKED
    if _blocked(overclaim_results):
        return FINAL_REVIEW_OVERCLAIM_BLOCKED
    if _blocked(emission_results):
        return FINAL_REVIEW_REVIEW_BLOCKED
    return FINAL_REVIEW_READY_FOR_EMISSION_REVIEW


def _row(row_type: type[Any], gate_group: str, gate_name: str, passed: bool, failure_status: str, evidence_path: str, observed_value: Any, blocker_reason: str) -> Any:
    return row_type(
        gate_group=gate_group,
        gate_name=gate_name,
        status=FINAL_REVIEW_PACKAGE_FOUND if passed else failure_status,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        evidence_path=evidence_path,
        observed_value=str(observed_value),
    )


def _missing(row_type: type[Any], gate_group: str, gate_name: str, failure_status: str, path: Path | None) -> Any:
    return row_type(
        gate_group=gate_group,
        gate_name=gate_name,
        status=failure_status,
        passed=False,
        blocker_reason=f"{gate_name} is missing or unreadable.",
        evidence_path=_path_str(path),
    )


def _load_artifact_payload(path: Path | None, metadata_name: str) -> dict[str, Any] | None:
    if path is None:
        return None
    if path.is_dir():
        return _read_json(path / metadata_name)
    return _read_json(path)


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _metadata(result: ActiveReplayInputFinalReviewResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    for key in [
        "package_results",
        "lineage_results",
        "authority_results",
        "attestation_results",
        "pit_source_evidence_results",
        "taxonomy_results",
        "leakage_side_effect_results",
        "overclaim_results",
        "emission_readiness_results",
    ]:
        payload.pop(key, None)
    return payload


def _render_report(result: ActiveReplayInputFinalReviewResult) -> str:
    return "\n".join(
        [
            "# Active Replay Input Final-Review Report",
            "",
            f"- final_review_run_id: {result.final_review_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- ready_for_emission_review: {result.ready_for_emission_review}",
            f"- blocker_count: {result.blocker_count}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- active_ready_emitted: {result.active_ready_emitted}",
            "",
            "This report is diagnostics-only. FINAL_REVIEW_READY_FOR_EMISSION_REVIEW is not ACTIVE_REPLAY_INPUT_READY. It does not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, compute labels, train weights, create stock profiles, create buy-review eligibility, authorize trading, call APIs, write data stores, or mutate cache.",
        ]
    )


def _render_next_task(result: ActiveReplayInputFinalReviewResult) -> str:
    if result.ready_for_emission_review:
        next_task = "Add Active Replay Input Final-Review artifact views v0.1"
    else:
        next_task = "Resolve final-review blockers and rerun report-only core workflow"
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            next_task,
            "",
            "Do not emit ACTIVE_REPLAY_INPUT_READY in this first implementation line.",
        ]
    )


def _write_results(path: Path, rows: list[Any]) -> None:
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _build_run_id(settings: ActiveReplayInputFinalReviewSettings, generated_at: str) -> str:
    paths = [
        settings.active_ready_artifact,
        settings.active_ready_health_artifact,
        settings.active_ready_status_artifact,
        settings.final_review_package_manifest,
        settings.final_review_authority_manifest,
        settings.final_review_attestation_manifest,
        settings.pit_source_evidence_attachment_bundle,
        settings.taxonomy_attachment_bundle,
        settings.leakage_side_effect_evidence_bundle,
        settings.overclaim_evidence_bundle,
        settings.emission_request_manifest,
    ]
    parts = [generated_at, *[_path_str(path) for path in paths]]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if not _is_under(path, Path("outputs/reports/manual_diagnostics")):
        raise ValueError("Final-review outputs must stay under outputs/reports/manual_diagnostics")


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        parts = [part.lower() for part in path.parts]
        expected = [part.lower() for part in parent.parts]
        return any(parts[index : index + len(expected)] == expected for index in range(len(parts) - len(expected) + 1))


def _passed(rows: list[Any]) -> int:
    return sum(1 for row in rows if bool(getattr(row, "passed", False)))


def _blocked(rows: list[Any]) -> int:
    return sum(1 for row in rows if not bool(getattr(row, "passed", False)))


def _blocked_statuses(rows: list[Any]) -> list[str]:
    return [str(getattr(row, "status", "")) for row in rows if not bool(getattr(row, "passed", False))]


def _path_str(path: Path | None) -> str:
    return "" if path is None else str(path)


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "accepted"}

