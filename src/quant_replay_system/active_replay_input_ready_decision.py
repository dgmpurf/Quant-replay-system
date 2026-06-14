"""Report-only active replay input ready-decision precondition workflow.

This workflow deliberately stops at
``READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION``. It never emits
``ACTIVE_REPLAY_INPUT_READY`` and never creates active replay input, runs
replay, computes labels, trains weights, creates stock profiles, changes
buy-review eligibility, writes data stores, calls APIs, or mutates cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT = "NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT"
ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND = "ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND"
ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED"
READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION = "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION"

EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW = "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_ready_decision_v0_1")
PASS_RESULTS = {"PASS", "ACCEPTED", "ACCEPTED_FOR_REVIEW_ONLY", "READY", "READY_FOR_REVIEW"}

LINEAGE_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
]
LEAKAGE_FALSE_FIELDS = [
    "forward_labels_exist",
    "forward_returns_exist",
    "training_outputs_exist",
    "model_weights_exist",
    "weights_trained",
    "stock_profile_artifacts_exist",
    "active_stock_profile_exists",
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
OVERCLAIM_FALSE_FIELDS = [
    "approved_for_paper",
    "replay_execution_allowed",
    "forward_labels_allowed",
    "training_allowed",
    "stock_profile_allowed",
    "buy_review_allowed",
    "trading_allowed",
]
REQUEST_FALSE_FIELDS = [
    "allow_active_replay_input_ready",
    "allow_active_replay_input_creation",
    "allow_replay_execution",
    "allow_forward_labels",
    "allow_training",
    "allow_stock_profile",
    "allow_buy_review",
    "allow_trading",
]
AUTHORITY_FIELDS = [
    "decision_authority_id",
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
    "no_active_ready_emission_attested",
    "no_trading_authority_attested",
    "no_performance_claim_attested",
    "no_replay_execution_attested",
    "report_only",
    "diagnostic_only",
]
PIT_FIELDS = [
    "accepted_pit_universe_evidence_attached",
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
    "no_broker_api_called",
    "no_order_placed",
    "no_message_sent",
    "no_llm_api_called",
    "no_external_api_called",
    "no_cache_mutated",
    "no_data_raw_written",
    "no_data_processed_written",
    "no_data_cache_written",
    "no_current_candidates_run",
    "no_snapshot_built",
]
OVERCLAIM_TRUE_FIELDS = [
    "pass_candidate_not_active_ready",
    "smoke_not_active_ready",
    "promotion_not_active_ready",
    "acceptance_not_active_ready",
    "active_ready_final_review_not_active_ready",
    "final_review_ready_not_active_input_ready",
    "emission_ready_review_not_active_input_ready",
    "ready_decision_not_active_replay_input_ready",
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


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionSettings:
    emission_artifact_path: Path | None = None
    emission_health_artifact_path: Path | None = None
    emission_status_artifact_path: Path | None = None
    emission_acceptance_audit_path: Path | None = None
    decision_request_manifest_path: Path | None = None
    decision_authority_manifest_path: Path | None = None
    decision_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    active_replay_input_ready_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionPreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionAuthorityResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionLineageResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionAttestationResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionPitSourceEvidenceResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionTaxonomyResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionLeakageSideEffectResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionOverclaimResult(ActiveReplayInputReadyDecisionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyDecisionResult:
    decision_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActiveReplayInputReadyDecisionPreconditionResult]
    authority_results: list[ActiveReplayInputReadyDecisionAuthorityResult]
    lineage_results: list[ActiveReplayInputReadyDecisionLineageResult]
    attestation_results: list[ActiveReplayInputReadyDecisionAttestationResult]
    pit_source_evidence_results: list[ActiveReplayInputReadyDecisionPitSourceEvidenceResult]
    taxonomy_results: list[ActiveReplayInputReadyDecisionTaxonomyResult]
    leakage_side_effect_results: list[ActiveReplayInputReadyDecisionLeakageSideEffectResult]
    overclaim_results: list[ActiveReplayInputReadyDecisionOverclaimResult]
    emission_artifact_path: str
    emission_health_artifact_path: str
    emission_status_artifact_path: str
    emission_acceptance_audit_path: str
    decision_request_manifest_path: str
    decision_authority_manifest_path: str
    decision_attestation_manifest_path: str
    pit_source_evidence_bundle_path: str
    taxonomy_evidence_bundle_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    active_replay_input_ready_candidate_manifest_path: str
    precondition_count: int
    passed_precondition_count: int
    blocked_precondition_count: int
    authority_gate_count: int
    passed_authority_gate_count: int
    blocked_authority_gate_count: int
    lineage_gate_count: int
    passed_lineage_gate_count: int
    blocked_lineage_gate_count: int
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
    overclaim_gate_count: int
    passed_overclaim_gate_count: int
    blocked_overclaim_gate_count: int
    issue_count: int
    blocker_count: int
    warning_count: int
    ready_for_active_replay_input_ready_decision: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    replay_execution_allowed: bool
    forward_labels_allowed: bool
    training_allowed: bool
    stock_profile_allowed: bool
    buy_review_allowed: bool
    trading_allowed: bool
    forward_labels_exist: bool
    forward_returns_exist: bool
    training_outputs_exist: bool
    model_weights_exist: bool
    weights_trained: bool
    stock_profile_artifacts_exist: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
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
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    artifact_paths: dict[str, Path]


def run_active_replay_input_ready_decision(
    settings: ActiveReplayInputReadyDecisionSettings | None = None,
) -> ActiveReplayInputReadyDecisionResult:
    settings = settings or ActiveReplayInputReadyDecisionSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    decision_run_id = _build_run_id(settings, generated_at)
    artifact_path = settings.output_dir / decision_run_id

    has_input = any(
        [
            settings.emission_artifact_path,
            settings.emission_health_artifact_path,
            settings.emission_status_artifact_path,
            settings.emission_acceptance_audit_path,
            settings.decision_request_manifest_path,
            settings.decision_authority_manifest_path,
            settings.decision_attestation_manifest_path,
            settings.pit_source_evidence_bundle_path,
            settings.taxonomy_evidence_bundle_path,
            settings.leakage_side_effect_evidence_bundle_path,
            settings.overclaim_evidence_bundle_path,
            settings.active_replay_input_ready_candidate_manifest_path,
        ]
    )
    precondition_results = [
        ActiveReplayInputReadyDecisionPreconditionResult(
            gate_group="ready_decision_input",
            gate_name="input_manifest_present",
            status=ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND
            if has_input
            else NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No active replay input ready-decision input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    emission_payload = _load_artifact_payload(settings.emission_artifact_path, "emission_metadata.json")
    emission_health_payload = _read_json(settings.emission_health_artifact_path)
    emission_status_payload = _read_json(settings.emission_status_artifact_path)
    emission_acceptance_payload = _read_json(settings.emission_acceptance_audit_path)
    request_payload = _read_json(settings.decision_request_manifest_path)
    candidate_payload = _read_json(settings.active_replay_input_ready_candidate_manifest_path)

    lineage_results = _check_emission_lineage(
        settings,
        emission_payload,
        emission_health_payload,
        emission_status_payload,
        emission_acceptance_payload,
    )
    authority_results = _check_authority(settings)
    authority_results.extend(_check_decision_request(settings, request_payload))
    authority_results.extend(_check_ready_candidate(settings, candidate_payload))
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    taxonomy_results = _check_taxonomy(settings)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)

    safety_payloads = [
        payload
        for payload in [emission_payload, emission_status_payload, request_payload, candidate_payload]
        if payload
    ]
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            LEAKAGE_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
        )
    )
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            SIDE_EFFECT_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED,
        )
    )
    overclaim_results.extend(
        _check_false_fields(safety_payloads, LINEAGE_FALSE_FIELDS, ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED)
    )
    overclaim_results.extend(
        _check_false_fields(
            safety_payloads,
            OVERCLAIM_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
        )
    )
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    status = _resolve_status(
        has_input=has_input,
        lineage_results=lineage_results,
        authority_results=authority_results,
        attestation_results=attestation_results,
        pit_source_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
    )
    ready_for_decision = status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION
    blockers = (
        _blocked(precondition_results)
        + _blocked(lineage_results)
        + _blocked(authority_results)
        + _blocked(attestation_results)
        + _blocked(pit_source_results)
        + _blocked(taxonomy_results)
        + _blocked(leakage_side_effect_results)
        + _blocked(overclaim_results)
    )

    result = ActiveReplayInputReadyDecisionResult(
        decision_run_id=decision_run_id,
        generated_at=generated_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=status,
        precondition_results=precondition_results,
        authority_results=authority_results,
        lineage_results=lineage_results,
        attestation_results=attestation_results,
        pit_source_evidence_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
        emission_artifact_path=_path_str(settings.emission_artifact_path),
        emission_health_artifact_path=_path_str(settings.emission_health_artifact_path),
        emission_status_artifact_path=_path_str(settings.emission_status_artifact_path),
        emission_acceptance_audit_path=_path_str(settings.emission_acceptance_audit_path),
        decision_request_manifest_path=_path_str(settings.decision_request_manifest_path),
        decision_authority_manifest_path=_path_str(settings.decision_authority_manifest_path),
        decision_attestation_manifest_path=_path_str(settings.decision_attestation_manifest_path),
        pit_source_evidence_bundle_path=_path_str(settings.pit_source_evidence_bundle_path),
        taxonomy_evidence_bundle_path=_path_str(settings.taxonomy_evidence_bundle_path),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle_path),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle_path),
        active_replay_input_ready_candidate_manifest_path=_path_str(
            settings.active_replay_input_ready_candidate_manifest_path
        ),
        precondition_count=len(precondition_results),
        passed_precondition_count=_passed(precondition_results),
        blocked_precondition_count=_blocked(precondition_results),
        authority_gate_count=len(authority_results),
        passed_authority_gate_count=_passed(authority_results),
        blocked_authority_gate_count=_blocked(authority_results),
        lineage_gate_count=len(lineage_results),
        passed_lineage_gate_count=_passed(lineage_results),
        blocked_lineage_gate_count=_blocked(lineage_results),
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
        overclaim_gate_count=len(overclaim_results),
        passed_overclaim_gate_count=_passed(overclaim_results),
        blocked_overclaim_gate_count=_blocked(overclaim_results),
        issue_count=blockers,
        blocker_count=blockers,
        warning_count=0,
        ready_for_active_replay_input_ready_decision=ready_for_decision,
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        replay_execution_allowed=False,
        forward_labels_allowed=False,
        training_allowed=False,
        stock_profile_allowed=False,
        buy_review_allowed=False,
        trading_allowed=False,
        forward_labels_exist=False,
        forward_returns_exist=False,
        training_outputs_exist=False,
        model_weights_exist=False,
        weights_trained=False,
        stock_profile_artifacts_exist=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        approved_for_paper=False,
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
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        overclaim_guard_pass_count=_passed(overclaim_results),
        overclaim_guard_total_count=len(overclaim_results),
        artifact_paths=resolve_active_replay_input_ready_decision_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_active_replay_input_ready_decision_artifacts(result)
    return result


def resolve_active_replay_input_ready_decision_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "decision_metadata.json",
        "decision_report": artifact_path / "decision_report.md",
        "decision_precondition_results": artifact_path / "decision_precondition_results.csv",
        "decision_authority_results": artifact_path / "decision_authority_results.csv",
        "emission_lineage_results": artifact_path / "emission_lineage_results.csv",
        "decision_attestation_results": artifact_path / "decision_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "ready_candidate": artifact_path / "active_replay_input_ready_candidate.json",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_ready_decision_artifacts(result: ActiveReplayInputReadyDecisionResult) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_results(result.artifact_paths["decision_precondition_results"], result.precondition_results)
    _write_results(result.artifact_paths["decision_authority_results"], result.authority_results)
    _write_results(result.artifact_paths["emission_lineage_results"], result.lineage_results)
    _write_results(result.artifact_paths["decision_attestation_results"], result.attestation_results)
    _write_results(result.artifact_paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_results(result.artifact_paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_results(result.artifact_paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_results(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)
    result.artifact_paths["decision_report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["ready_candidate"].write_text(
        json.dumps(_candidate_payload(result), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _check_emission_lineage(
    settings: ActiveReplayInputReadyDecisionSettings,
    emission_payload: dict[str, Any] | None,
    health_payload: dict[str, Any] | None,
    status_payload: dict[str, Any] | None,
    acceptance_payload: dict[str, Any] | None,
) -> list[ActiveReplayInputReadyDecisionLineageResult]:
    if not emission_payload:
        return [
            _row(
                ActiveReplayInputReadyDecisionLineageResult,
                "emission_lineage",
                "emission_artifact_path",
                False,
                ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
                _path_str(settings.emission_artifact_path),
                "",
                "Emission artifact is missing or unreadable.",
            )
        ]
    results = [
        _row(
            ActiveReplayInputReadyDecisionLineageResult,
            "emission_lineage",
            "emission_status",
            emission_payload.get("status") == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW,
            ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
            _path_str(settings.emission_artifact_path),
            emission_payload.get("status"),
            "Emission status is not EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW.",
        ),
        _row(
            ActiveReplayInputReadyDecisionLineageResult,
            "emission_lineage",
            "ready_for_active_replay_input_ready_review",
            _as_bool(emission_payload.get("ready_for_active_replay_input_ready_review")),
            ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
            _path_str(settings.emission_artifact_path),
            emission_payload.get("ready_for_active_replay_input_ready_review"),
            "Emission artifact is not ready for active replay input ready decision review.",
        ),
    ]
    results.append(
        _row(
            ActiveReplayInputReadyDecisionLineageResult,
            "emission_lineage",
            "emission_health",
            bool(health_payload)
            and (health_payload.get("health_status") == "PASS" or health_payload.get("status") == "PASS"),
            ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
            _path_str(settings.emission_health_artifact_path),
            (health_payload.get("health_status") or health_payload.get("status")) if health_payload else "",
            "Emission health artifact is missing or not PASS.",
        )
    )
    results.append(
        _row(
            ActiveReplayInputReadyDecisionLineageResult,
            "emission_lineage",
            "emission_status_artifact",
            bool(status_payload)
            and status_payload.get("status") == EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW
            and _as_bool(status_payload.get("ready_for_active_replay_input_ready_review")),
            ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
            _path_str(settings.emission_status_artifact_path),
            status_payload.get("status") if status_payload else "",
            "Emission status artifact is missing or not ready for decision review.",
        )
    )
    results.append(
        _row(
            ActiveReplayInputReadyDecisionLineageResult,
            "emission_lineage",
            "emission_acceptance_audit",
            bool(acceptance_payload)
            and str(acceptance_payload.get("audit_result", "")).upper() in PASS_RESULTS
            and _as_bool(acceptance_payload.get("emission_ready_for_decision_review")),
            ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED,
            _path_str(settings.emission_acceptance_audit_path),
            acceptance_payload.get("audit_result") if acceptance_payload else "",
            "Emission acceptance audit is missing or not accepted for decision review.",
        )
    )
    return results


def _check_decision_request(
    settings: ActiveReplayInputReadyDecisionSettings,
    payload: dict[str, Any] | None,
) -> list[ActiveReplayInputReadyDecisionAuthorityResult]:
    if not payload:
        return [
            _row(
                ActiveReplayInputReadyDecisionAuthorityResult,
                "decision_request",
                "decision_request_manifest_path",
                False,
                ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
                _path_str(settings.decision_request_manifest_path),
                "",
                "Decision request manifest is missing or unreadable.",
            )
        ]
    results = [
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_request",
            field,
            _present(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.decision_request_manifest_path),
            payload.get(field),
            f"Missing decision request field {field}.",
        )
        for field in ["decision_request_id", "requested_by", "requested_at", "request_reason"]
    ]
    results.append(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_request",
            "requested_status",
            payload.get("requested_status") == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.decision_request_manifest_path),
            payload.get("requested_status"),
            "First implementation only allows ready-decision review requests.",
        )
    )
    results.extend(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_request",
            field,
            not _as_bool(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.decision_request_manifest_path),
            payload.get(field),
            f"Decision request has unsafe allow flag {field}.",
        )
        for field in REQUEST_FALSE_FIELDS
    )
    results.extend(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_request",
            field,
            _as_bool(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.decision_request_manifest_path),
            payload.get(field),
            f"Decision request field {field} is not true.",
        )
        for field in ["report_only", "diagnostic_only"]
    )
    return results


def _check_ready_candidate(
    settings: ActiveReplayInputReadyDecisionSettings,
    payload: dict[str, Any] | None,
) -> list[ActiveReplayInputReadyDecisionAuthorityResult]:
    if not payload:
        return [
            _row(
                ActiveReplayInputReadyDecisionAuthorityResult,
                "ready_candidate_manifest",
                "active_replay_input_ready_candidate_manifest_path",
                False,
                ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
                _path_str(settings.active_replay_input_ready_candidate_manifest_path),
                "",
                "Ready candidate manifest is missing or unreadable.",
            )
        ]
    candidate_status = payload.get("candidate_status")
    candidate_status_failure = (
        ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED
        if candidate_status == "ACTIVE_REPLAY_INPUT_READY"
        else ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED
    )
    results = [
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "ready_candidate_manifest",
            "candidate_status",
            candidate_status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION,
            candidate_status_failure,
            _path_str(settings.active_replay_input_ready_candidate_manifest_path),
            candidate_status,
            "Ready candidate manifest is not a ready-decision candidate.",
        ),
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "ready_candidate_manifest",
            "ready_for_active_replay_input_ready_decision",
            _as_bool(payload.get("ready_for_active_replay_input_ready_decision")),
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.active_replay_input_ready_candidate_manifest_path),
            payload.get("ready_for_active_replay_input_ready_decision"),
            "Ready candidate manifest is not marked ready for ready-decision review.",
        ),
    ]
    results.extend(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "ready_candidate_manifest",
            field,
            not _as_bool(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
            _path_str(settings.active_replay_input_ready_candidate_manifest_path),
            payload.get(field),
            f"Ready candidate manifest has unsafe field {field}.",
        )
        for field in [
            "active_replay_input_ready",
            "active_replay_input",
            "active_ready_emitted",
            "replay_execution_allowed",
            "forward_labels_allowed",
            "training_allowed",
            "stock_profile_allowed",
            "buy_review_allowed",
            "trading_allowed",
        ]
    )
    results.extend(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "ready_candidate_manifest",
            field,
            _as_bool(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED,
            _path_str(settings.active_replay_input_ready_candidate_manifest_path),
            payload.get(field),
            f"Ready candidate manifest field {field} is not true.",
        )
        for field in ["report_only", "diagnostic_only"]
    )
    return results


def _check_authority(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionAuthorityResult]:
    payload = _read_json(settings.decision_authority_manifest_path)
    if not payload:
        return [
            _row(
                ActiveReplayInputReadyDecisionAuthorityResult,
                "decision_authority",
                "decision_authority_manifest_path",
                False,
                ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
                _path_str(settings.decision_authority_manifest_path),
                "",
                "Decision authority manifest is missing or unreadable.",
            )
        ]
    results = [
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_authority",
            field,
            _present(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
            _path_str(settings.decision_authority_manifest_path),
            payload.get(field),
            f"Missing authority field {field}.",
        )
        for field in AUTHORITY_FIELDS
    ]
    results.append(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_authority",
            "authority_result",
            str(payload.get("authority_result", "")).upper() in PASS_RESULTS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
            _path_str(settings.decision_authority_manifest_path),
            payload.get("authority_result"),
            "Authority result is not accepted.",
        )
    )
    results.extend(
        _row(
            ActiveReplayInputReadyDecisionAuthorityResult,
            "decision_authority",
            field,
            _as_bool(payload.get(field)),
            ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED,
            _path_str(settings.decision_authority_manifest_path),
            payload.get(field),
            f"Authority field {field} is not true.",
        )
        for field in ["report_only", "diagnostic_only"]
    )
    return results


def _check_attestation(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionAttestationResult]:
    return _check_true_manifest(
        settings.decision_attestation_manifest_path,
        "decision_attestation",
        ATTESTATION_TRUE_FIELDS,
        "attestation_result",
        ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED,
        ActiveReplayInputReadyDecisionAttestationResult,
    )


def _check_pit_source_evidence(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionPitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_bundle_path)
    if not payload:
        return [
            _missing(
                ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
                "pit_source_evidence",
                "pit_source_evidence_bundle_path",
                ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
                settings.pit_source_evidence_bundle_path,
            )
        ]
    results: list[ActiveReplayInputReadyDecisionPitSourceEvidenceResult] = []
    results.extend(
        _true_field_rows(
            ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
            "pit_source_evidence",
            PIT_FIELDS,
            payload,
            settings.pit_source_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED,
        )
    )
    results.extend(
        _true_field_rows(
            ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
            "pit_source_evidence",
            SOURCE_FIELDS,
            payload,
            settings.pit_source_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED,
        )
    )
    results.extend(
        _true_field_rows(
            ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
            "pit_source_evidence",
            EVIDENCE_FIELDS,
            payload,
            settings.pit_source_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
        )
    )
    results.append(
        _row(
            ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
            "pit_source_evidence",
            "attachment_result",
            str(payload.get("attachment_result", "")).upper() in PASS_RESULTS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
            _path_str(settings.pit_source_evidence_bundle_path),
            payload.get("attachment_result"),
            "Attachment result is not PASS.",
        )
    )
    results.extend(
        _report_only_rows(
            ActiveReplayInputReadyDecisionPitSourceEvidenceResult,
            "pit_source_evidence",
            payload,
            settings.pit_source_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
        )
    )
    return results


def _check_taxonomy(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionTaxonomyResult]:
    return _check_true_manifest(
        settings.taxonomy_evidence_bundle_path,
        "taxonomy_evidence",
        TAXONOMY_TRUE_FIELDS,
        "taxonomy_result",
        ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED,
        ActiveReplayInputReadyDecisionTaxonomyResult,
    )


def _check_leakage_side_effect(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    if not payload:
        return [
            _missing(
                ActiveReplayInputReadyDecisionLeakageSideEffectResult,
                "leakage_side_effect",
                "leakage_side_effect_evidence_bundle_path",
                ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
                settings.leakage_side_effect_evidence_bundle_path,
            )
        ]
    results: list[ActiveReplayInputReadyDecisionLeakageSideEffectResult] = []
    results.extend(
        _true_field_rows(
            ActiveReplayInputReadyDecisionLeakageSideEffectResult,
            "leakage_side_effect",
            LEAKAGE_TRUE_FIELDS,
            payload,
            settings.leakage_side_effect_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
        )
    )
    results.extend(
        _true_field_rows(
            ActiveReplayInputReadyDecisionLeakageSideEffectResult,
            "leakage_side_effect",
            SIDE_EFFECT_TRUE_FIELDS,
            payload,
            settings.leakage_side_effect_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED,
        )
    )
    results.append(
        _row(
            ActiveReplayInputReadyDecisionLeakageSideEffectResult,
            "leakage_side_effect",
            "leakage_side_effect_result",
            str(payload.get("leakage_side_effect_result", "")).upper() in PASS_RESULTS,
            ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
            _path_str(settings.leakage_side_effect_evidence_bundle_path),
            payload.get("leakage_side_effect_result"),
            "Leakage/side-effect result is not PASS.",
        )
    )
    results.extend(
        _report_only_rows(
            ActiveReplayInputReadyDecisionLeakageSideEffectResult,
            "leakage_side_effect",
            payload,
            settings.leakage_side_effect_evidence_bundle_path,
            ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
        )
    )
    return results


def _check_overclaim(
    settings: ActiveReplayInputReadyDecisionSettings,
) -> list[ActiveReplayInputReadyDecisionOverclaimResult]:
    return _check_true_manifest(
        settings.overclaim_evidence_bundle_path,
        "overclaim",
        OVERCLAIM_TRUE_FIELDS,
        "overclaim_result",
        ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
        ActiveReplayInputReadyDecisionOverclaimResult,
    )


def _check_true_manifest(
    path: Path | None,
    gate_group: str,
    true_fields: list[str],
    result_field: str,
    failure_status: str,
    row_type: type[Any],
) -> list[Any]:
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


def _true_field_rows(
    row_type: type[Any],
    gate_group: str,
    fields: list[str],
    payload: dict[str, Any],
    path: Path | None,
    failure_status: str,
) -> list[Any]:
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


def _report_only_rows(
    row_type: type[Any],
    gate_group: str,
    payload: dict[str, Any],
    path: Path | None,
    failure_status: str,
) -> list[Any]:
    return [
        _row(
            row_type,
            gate_group,
            "report_only",
            _as_bool(payload.get("report_only")),
            failure_status,
            _path_str(path),
            payload.get("report_only"),
            "Manifest is not report-only.",
        ),
        _row(
            row_type,
            gate_group,
            "diagnostic_only",
            _as_bool(payload.get("diagnostic_only")),
            failure_status,
            _path_str(path),
            payload.get("diagnostic_only"),
            "Manifest is not diagnostic-only.",
        ),
    ]


def _check_false_fields(payloads: list[dict[str, Any]], fields: list[str], failure_status: str) -> list[Any]:
    rows: list[Any] = []
    for payload in payloads:
        source = str(
            payload.get("emission_run_id")
            or payload.get("decision_request_id")
            or payload.get("candidate_id")
            or payload.get("status")
            or "payload"
        )
        for field in fields:
            if field in payload:
                row_type = (
                    ActiveReplayInputReadyDecisionLeakageSideEffectResult
                    if failure_status
                    in {
                        ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED,
                        ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED,
                    }
                    else ActiveReplayInputReadyDecisionOverclaimResult
                )
                safe = not _as_bool(payload.get(field))
                rows.append(
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
    return rows


def _built_in_overclaim_guards(output_dir: Path) -> list[ActiveReplayInputReadyDecisionOverclaimResult]:
    output_safe = _is_under(output_dir, Path("outputs/reports/manual_diagnostics"))
    guards = [
        ("replay_pass_candidate_not_active_ready", True, "REPLAY_INPUT_GATE_PASS_CANDIDATE must not be active-ready."),
        ("smoke_pass_candidate_not_active_ready", True, "SMOKE_PASS_CANDIDATE_READY must not be active-ready."),
        ("promotion_ready_not_active_ready", True, "PROMOTION_READY_FOR_HUMAN_REVIEW must not be active-ready."),
        ("acceptance_ready_not_active_ready", True, "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW must not be active-ready."),
        (
            "active_ready_final_review_not_active_ready",
            True,
            "ACTIVE_READY_READY_FOR_FINAL_REVIEW must not be active-ready.",
        ),
        (
            "final_review_ready_not_active_input_ready",
            True,
            "FINAL_REVIEW_READY_FOR_EMISSION_REVIEW must not be active input ready.",
        ),
        (
            "emission_ready_review_not_active_input_ready",
            True,
            "EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW must not be active input ready.",
        ),
        (
            "ready_decision_not_active_input_ready",
            True,
            "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION must not be ACTIVE_REPLAY_INPUT_READY.",
        ),
        ("forbidden_active_ready_not_emitted", True, "Active input ready must not be emitted."),
        ("output_path_under_manual_diagnostics", output_safe, "Output path must stay under manual_diagnostics."),
    ]
    return [
        ActiveReplayInputReadyDecisionOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status=ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND
            if passed
            else ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else reason,
            evidence_path=str(output_dir),
            observed_value=str(passed),
        )
        for name, passed, reason in guards
    ]


def _resolve_status(
    *,
    has_input: bool,
    lineage_results: list[Any],
    authority_results: list[Any],
    attestation_results: list[Any],
    pit_source_results: list[Any],
    taxonomy_results: list[Any],
    leakage_side_effect_results: list[Any],
    overclaim_results: list[Any],
) -> str:
    if not has_input:
        return NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT
    if _blocked(lineage_results):
        return ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED
    if _blocked(authority_results):
        statuses = _blocked_statuses(authority_results)
        if ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED in statuses:
            return ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED
        if ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED in statuses:
            return ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED
        return ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED
    if _blocked(attestation_results):
        return ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED
    if _blocked(pit_source_results):
        statuses = _blocked_statuses(pit_source_results)
        for status in [
            ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED,
            ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED,
            ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED,
        ]:
            if status in statuses:
                return status
        return ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED
    if _blocked(taxonomy_results):
        return ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED
    if _blocked(leakage_side_effect_results):
        statuses = _blocked_statuses(leakage_side_effect_results)
        if ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED in statuses:
            return ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED
        return ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED
    if _blocked(overclaim_results):
        return ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED
    return READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION


def _row(
    row_type: type[Any],
    gate_group: str,
    gate_name: str,
    passed: bool,
    failure_status: str,
    evidence_path: str,
    observed_value: Any,
    blocker_reason: str,
) -> Any:
    return row_type(
        gate_group=gate_group,
        gate_name=gate_name,
        status=ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND if passed else failure_status,
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
        observed_value="",
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


def _metadata(result: ActiveReplayInputReadyDecisionResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    for key in [
        "precondition_results",
        "authority_results",
        "lineage_results",
        "attestation_results",
        "pit_source_evidence_results",
        "taxonomy_results",
        "leakage_side_effect_results",
        "overclaim_results",
    ]:
        payload.pop(key, None)
    return payload


def _candidate_payload(result: ActiveReplayInputReadyDecisionResult) -> dict[str, Any]:
    return {
        "decision_run_id": result.decision_run_id,
        "status": result.status,
        "ready_for_active_replay_input_ready_decision": result.ready_for_active_replay_input_ready_decision,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "active_ready_emitted": False,
        "replay_execution_allowed": False,
        "forward_labels_allowed": False,
        "training_allowed": False,
        "stock_profile_allowed": False,
        "buy_review_allowed": False,
        "trading_allowed": False,
        "report_only": True,
        "diagnostic_only": True,
        "next_required_step": "future artifact views and independent health/status checks before any further governance",
    }


def _render_report(result: ActiveReplayInputReadyDecisionResult) -> str:
    return "\n".join(
        [
            "# Active Replay Input Ready Decision Report",
            "",
            f"- decision_run_id: {result.decision_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            (
                "- ready_for_active_replay_input_ready_decision: "
                f"{result.ready_for_active_replay_input_ready_decision}"
            ),
            f"- blocker_count: {result.blocker_count}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- active_ready_emitted: {result.active_ready_emitted}",
            "",
            "This report is diagnostics-only. READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION is not ACTIVE_REPLAY_INPUT_READY and is not active replay input. It does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create stock profiles, does not create buy-review eligibility, does not authorize trading, does not call APIs, does not write data stores, and does not mutate cache.",
        ]
    )


def _render_next_task(result: ActiveReplayInputReadyDecisionResult) -> str:
    if result.ready_for_active_replay_input_ready_decision:
        next_task = "Add Active Replay Input Ready Decision artifact views v0.1"
    else:
        next_task = "Resolve active replay input ready-decision blockers and rerun report-only core workflow"
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


def _build_run_id(settings: ActiveReplayInputReadyDecisionSettings, generated_at: str) -> str:
    paths = [
        settings.emission_artifact_path,
        settings.emission_health_artifact_path,
        settings.emission_status_artifact_path,
        settings.emission_acceptance_audit_path,
        settings.decision_request_manifest_path,
        settings.decision_authority_manifest_path,
        settings.decision_attestation_manifest_path,
        settings.pit_source_evidence_bundle_path,
        settings.taxonomy_evidence_bundle_path,
        settings.leakage_side_effect_evidence_bundle_path,
        settings.overclaim_evidence_bundle_path,
        settings.active_replay_input_ready_candidate_manifest_path,
    ]
    parts = [generated_at, *[_path_str(path) for path in paths]]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if not _is_under(path, Path("outputs/reports/manual_diagnostics")):
        raise ValueError("Ready-decision outputs must stay under outputs/reports/manual_diagnostics")


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


__all__ = [
    "NO_ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_INPUT_FOUND",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_LINEAGE_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_AUTHORITY_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_ATTESTATION_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_PIT_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_SOURCE_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_EVIDENCE_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_TAXONOMY_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_LEAKAGE_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_SIDE_EFFECT_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_OVERCLAIM_BLOCKED",
    "ACTIVE_REPLAY_INPUT_READY_DECISION_REVIEW_BLOCKED",
    "READY_FOR_ACTIVE_REPLAY_INPUT_READY_DECISION",
    "ActiveReplayInputReadyDecisionSettings",
    "ActiveReplayInputReadyDecisionResult",
    "run_active_replay_input_ready_decision",
    "resolve_active_replay_input_ready_decision_paths",
    "write_active_replay_input_ready_decision_artifacts",
]
