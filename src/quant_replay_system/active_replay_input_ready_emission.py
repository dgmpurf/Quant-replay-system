"""Report-only ACTIVE_REPLAY_INPUT_READY emission-decision workflow.

This workflow deliberately stops at
``READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION``. It never emits
``ACTIVE_REPLAY_INPUT_READY`` and never creates active replay input, runs
replay, creates replay decisions, computes labels, trains weights, creates
stock profiles, changes buy-review eligibility, writes data stores, calls APIs,
or mutates cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT = "NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT"
ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND = "ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND"
ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED"
ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED = "ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED"
READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION = (
    "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION"
)

READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY = "READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY"
ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT = "ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_ready_emission_v0_1")
PASS_RESULTS = {"PASS", "ACCEPTED", "ACCEPTED_FOR_REVIEW_ONLY", "READY", "READY_FOR_REVIEW"}

OVERCLAIM_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "replay_execution_allowed",
    "forward_labels_allowed",
    "training_allowed",
    "stock_profile_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "approved_for_paper",
    "allow_active_replay_input_ready_emission",
    "explicit_actual_emission_allowed",
    "emit_active_replay_input_ready",
]
LEAKAGE_FALSE_FIELDS = [
    "replay_decisions_exist",
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
    "replay_execution_happened",
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
    "broker_api_called",
    "signal_semantics_changed",
]
AUTHORITY_FIELDS = ["primary_reviewer", "second_reviewer", "authority_scope"]
ATTESTATION_TRUE_FIELDS = [
    "primary_reviewer_attested",
    "second_reviewer_attested",
    "no_active_ready_emission_attested",
    "no_active_input_creation_attested",
    "no_replay_execution_attested",
    "no_replay_decision_creation_attested",
    "no_forward_label_attested",
    "no_training_attested",
    "no_stock_profile_attested",
    "no_buy_review_attested",
    "no_trading_authority_attested",
    "no_performance_claim_attested",
    "report_only",
    "diagnostic_only",
]
PIT_TRUE_FIELDS = ["accepted_pit_universe_evidence_attached"]
SOURCE_TRUE_FIELDS = [
    "source_id_coverage_attached",
    "source_hash_coverage_attached",
    "revision_id_coverage_attached",
    "permission_class_coverage_attached",
]
EVIDENCE_TRUE_FIELDS = ["factor_observation_coverage_attached", "raw_evidence_refs_attached"]
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
    "no_replay_decisions",
    "no_replay_execution",
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
    "ready_to_emit_not_active_replay_input_ready",
    "emission_decision_ready_not_active_replay_input_ready",
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
class ActiveReplayInputReadyEmissionSettings:
    ready_to_emit_artifact_path: Path | None = None
    active_ready_health_artifact_path: Path | None = None
    active_ready_status_artifact_path: Path | None = None
    final_emission_governance_plan_path: Path | None = None
    final_emission_request_manifest_path: Path | None = None
    final_authority_manifest_path: Path | None = None
    final_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    active_replay_input_ready_emission_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionPreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionAuthorityResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionLineageResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionAttestationResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionPitSourceEvidenceResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionTaxonomyResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionLeakageSideEffectResult(
    ActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionOverclaimResult(ActiveReplayInputReadyEmissionPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputReadyEmissionResult:
    active_ready_emission_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActiveReplayInputReadyEmissionPreconditionResult]
    authority_results: list[ActiveReplayInputReadyEmissionAuthorityResult]
    lineage_results: list[ActiveReplayInputReadyEmissionLineageResult]
    attestation_results: list[ActiveReplayInputReadyEmissionAttestationResult]
    pit_source_evidence_results: list[ActiveReplayInputReadyEmissionPitSourceEvidenceResult]
    taxonomy_results: list[ActiveReplayInputReadyEmissionTaxonomyResult]
    leakage_side_effect_results: list[ActiveReplayInputReadyEmissionLeakageSideEffectResult]
    overclaim_results: list[ActiveReplayInputReadyEmissionOverclaimResult]
    ready_to_emit_artifact_path: str
    active_ready_health_artifact_path: str
    active_ready_status_artifact_path: str
    final_emission_governance_plan_path: str
    final_emission_request_manifest_path: str
    final_authority_manifest_path: str
    final_attestation_manifest_path: str
    pit_source_evidence_bundle_path: str
    taxonomy_evidence_bundle_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    active_replay_input_ready_emission_candidate_manifest_path: str
    blocker_count: int
    issue_count: int
    warning_count: int
    ready_for_active_replay_input_ready_emission_decision: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    replay_execution_allowed: bool
    replay_decisions_exist: bool
    forward_labels_allowed: bool
    forward_labels_exist: bool
    training_allowed: bool
    weights_trained: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    trading_allowed: bool
    order_placed: bool
    broker_api_called: bool
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


def run_active_replay_input_ready_emission(
    settings: ActiveReplayInputReadyEmissionSettings | None = None,
) -> ActiveReplayInputReadyEmissionResult:
    settings = settings or ActiveReplayInputReadyEmissionSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    emission_run_id = _build_run_id(settings, generated_at)
    artifact_path = settings.output_dir / emission_run_id

    has_input = any(
        [
            settings.ready_to_emit_artifact_path,
            settings.active_ready_health_artifact_path,
            settings.active_ready_status_artifact_path,
            settings.final_emission_governance_plan_path,
            settings.final_emission_request_manifest_path,
            settings.final_authority_manifest_path,
            settings.final_attestation_manifest_path,
            settings.pit_source_evidence_bundle_path,
            settings.taxonomy_evidence_bundle_path,
            settings.leakage_side_effect_evidence_bundle_path,
            settings.overclaim_evidence_bundle_path,
            settings.active_replay_input_ready_emission_candidate_manifest_path,
        ]
    )
    precondition_results = [
        ActiveReplayInputReadyEmissionPreconditionResult(
            gate_group="active_replay_input_ready_emission_input",
            gate_name="final_emission_input_present",
            status=ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND
            if has_input
            else NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No ACTIVE_REPLAY_INPUT_READY emission input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    ready_payload = _load_artifact_payload(settings.ready_to_emit_artifact_path, "active_ready_metadata.json")
    health_payload = _read_json(settings.active_ready_health_artifact_path)
    status_payload = _read_json(settings.active_ready_status_artifact_path)
    request_payload = _read_json(settings.final_emission_request_manifest_path)
    candidate_payload = _read_json(settings.active_replay_input_ready_emission_candidate_manifest_path)

    lineage_results = _check_ready_to_emit_lineage(settings, ready_payload, health_payload, status_payload)
    precondition_results.extend(_check_final_emission_governance_plan(settings))
    authority_results = _check_final_emission_request(settings, request_payload)
    authority_results.extend(_check_authority(settings))
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    taxonomy_results = _check_taxonomy(settings)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)

    safety_payloads = [
        payload for payload in [ready_payload, status_payload, request_payload, candidate_payload] if payload
    ]
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            LEAKAGE_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
        )
    )
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            SIDE_EFFECT_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
        )
    )
    overclaim_results.extend(
        _check_false_fields(
            safety_payloads,
            OVERCLAIM_FALSE_FIELDS,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
        )
    )
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    status = _resolve_status(
        has_input=has_input,
        precondition_results=precondition_results,
        lineage_results=lineage_results,
        authority_results=authority_results,
        attestation_results=attestation_results,
        pit_source_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
    )
    ready_for_decision = status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
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
    result = ActiveReplayInputReadyEmissionResult(
        active_ready_emission_run_id=emission_run_id,
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
        ready_to_emit_artifact_path=_path_str(settings.ready_to_emit_artifact_path),
        active_ready_health_artifact_path=_path_str(settings.active_ready_health_artifact_path),
        active_ready_status_artifact_path=_path_str(settings.active_ready_status_artifact_path),
        final_emission_governance_plan_path=_path_str(settings.final_emission_governance_plan_path),
        final_emission_request_manifest_path=_path_str(settings.final_emission_request_manifest_path),
        final_authority_manifest_path=_path_str(settings.final_authority_manifest_path),
        final_attestation_manifest_path=_path_str(settings.final_attestation_manifest_path),
        pit_source_evidence_bundle_path=_path_str(settings.pit_source_evidence_bundle_path),
        taxonomy_evidence_bundle_path=_path_str(settings.taxonomy_evidence_bundle_path),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle_path),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle_path),
        active_replay_input_ready_emission_candidate_manifest_path=_path_str(
            settings.active_replay_input_ready_emission_candidate_manifest_path
        ),
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        ready_for_active_replay_input_ready_emission_decision=ready_for_decision,
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        replay_execution_allowed=False,
        replay_decisions_exist=False,
        forward_labels_allowed=False,
        forward_labels_exist=False,
        training_allowed=False,
        weights_trained=False,
        stock_profile_allowed=False,
        active_stock_profile_exists=False,
        buy_review_allowed=False,
        real_buy_review_eligible=False,
        trading_allowed=False,
        order_placed=False,
        broker_api_called=False,
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
        artifact_paths=resolve_active_replay_input_ready_emission_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_active_replay_input_ready_emission_artifacts(result)
    return result


def resolve_active_replay_input_ready_emission_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "active_ready_emission_metadata.json",
        "emission_report": artifact_path / "active_ready_emission_report.md",
        "final_emission_precondition_results": artifact_path / "final_emission_precondition_results.csv",
        "final_emission_authority_results": artifact_path / "final_emission_authority_results.csv",
        "ready_to_emit_lineage_results": artifact_path / "ready_to_emit_lineage_results.csv",
        "final_emission_attestation_results": artifact_path / "final_emission_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "emission_candidate": artifact_path / "active_replay_input_ready_emission_candidate.json",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_ready_emission_artifacts(result: ActiveReplayInputReadyEmissionResult) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_frame(result.artifact_paths["final_emission_precondition_results"], result.precondition_results)
    _write_frame(result.artifact_paths["final_emission_authority_results"], result.authority_results)
    _write_frame(result.artifact_paths["ready_to_emit_lineage_results"], result.lineage_results)
    _write_frame(result.artifact_paths["final_emission_attestation_results"], result.attestation_results)
    _write_frame(result.artifact_paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_frame(result.artifact_paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_frame(result.artifact_paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_frame(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)
    _write_json(
        result.artifact_paths["emission_candidate"],
        {
            "active_ready_emission_run_id": result.active_ready_emission_run_id,
            "status": result.status,
            "workflow_stage": result.workflow_stage,
            "ready_for_active_replay_input_ready_emission_decision": (
                result.ready_for_active_replay_input_ready_emission_decision
            ),
            "active_replay_input_ready": False,
            "active_replay_input": False,
            "active_ready_emitted": False,
            "replay_execution_allowed": False,
            "replay_decisions_exist": False,
            "forward_labels_allowed": False,
            "forward_labels_exist": False,
            "training_allowed": False,
            "weights_trained": False,
            "stock_profile_allowed": False,
            "active_stock_profile_exists": False,
            "buy_review_allowed": False,
            "real_buy_review_eligible": False,
            "trading_allowed": False,
            "report_only": True,
            "diagnostic_only": True,
            "safety_statement": (
                "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION is not ACTIVE_REPLAY_INPUT_READY."
            ),
        },
    )
    result.artifact_paths["emission_report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(
        "\n".join(
            [
                "# Recommended Next Task",
                "",
                "Add ACTIVE_REPLAY_INPUT_READY emission-decision artifact views only after the core workflow is accepted.",
                "",
                "Do not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, create replay "
                "decisions, compute labels, train weights, create stock profiles, create buy-review eligibility, "
                "or authorize trading without a later explicit scope.",
            ]
        ),
        encoding="utf-8",
    )


def _check_ready_to_emit_lineage(
    settings: ActiveReplayInputReadyEmissionSettings,
    ready_payload: dict[str, Any],
    health_payload: dict[str, Any],
    status_payload: dict[str, Any],
) -> list[ActiveReplayInputReadyEmissionLineageResult]:
    results: list[ActiveReplayInputReadyEmissionLineageResult] = []
    if not _path_exists(settings.ready_to_emit_artifact_path):
        results.append(
            _lineage(
                "ready_to_emit_artifact",
                ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
                False,
                "Ready-to-emit active-ready artifact is missing.",
                settings.ready_to_emit_artifact_path,
            )
        )
    else:
        ready_status = _text(ready_payload.get("status"))
        ready_to_emit = _to_bool(ready_payload.get("ready_to_emit_active_replay_input_ready"))
        passed = ready_status == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY and ready_to_emit
        results.append(
            _lineage(
                "ready_to_emit_status",
                "PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
                passed,
                "" if passed else "Active-ready artifact is not READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY.",
                settings.ready_to_emit_artifact_path,
                ready_status,
            )
        )
    health_status = _text(health_payload.get("health_status") or health_payload.get("status"))
    passed_health = _path_exists(settings.active_ready_health_artifact_path) and health_status == "PASS"
    results.append(
        _lineage(
            "active_ready_health",
            "PASS" if passed_health else ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
            passed_health,
            "" if passed_health else "Active-ready workflow health must be PASS.",
            settings.active_ready_health_artifact_path,
            health_status,
        )
    )
    summary_status = _text(status_payload.get("status"))
    summary_stage = _text(status_payload.get("workflow_stage"))
    passed_summary = (
        _path_exists(settings.active_ready_status_artifact_path)
        and summary_status == READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY
        and summary_stage in {READY_TO_EMIT_ACTIVE_REPLAY_INPUT_READY, ACTIVE_REPLAY_INPUT_READY_READY_TO_EMIT}
        and _to_bool(status_payload.get("ready_to_emit_active_replay_input_ready"))
    )
    results.append(
        _lineage(
            "active_ready_status_artifact",
            "PASS" if passed_summary else ACTIVE_REPLAY_INPUT_READY_EMISSION_LINEAGE_BLOCKED,
            passed_summary,
            "" if passed_summary else "Active-ready status summary is not ready for final emission decision.",
            settings.active_ready_status_artifact_path,
            summary_status or summary_stage,
        )
    )
    return results


def _check_final_emission_governance_plan(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionPreconditionResult]:
    passed = _path_exists(settings.final_emission_governance_plan_path)
    return [
        ActiveReplayInputReadyEmissionPreconditionResult(
            gate_group="final_emission_review",
            gate_name="governance_plan_present",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Final emission governance plan path is missing.",
            evidence_path=_path_str(settings.final_emission_governance_plan_path),
            observed_value=str(passed),
        )
    ]


def _check_final_emission_request(
    settings: ActiveReplayInputReadyEmissionSettings, payload: dict[str, Any]
) -> list[ActiveReplayInputReadyEmissionAuthorityResult]:
    passed = (
        _path_exists(settings.final_emission_request_manifest_path)
        and _passish(payload.get("request_result"))
        and _to_bool(payload.get("explicit_final_emission_request"))
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
        and not _to_bool(payload.get("explicit_actual_emission_allowed"))
    )
    return [
        _authority(
            "final_emission_request",
            passed,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_REVIEW_BLOCKED,
            "Final emission request must pass, be explicit, remain report_only diagnostic_only, and stop before emission.",
            settings.final_emission_request_manifest_path,
            _text(payload.get("request_result")),
        )
    ]


def _check_authority(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionAuthorityResult]:
    payload = _read_json(settings.final_authority_manifest_path)
    passed = (
        _path_exists(settings.final_authority_manifest_path)
        and _passish(payload.get("authority_result"))
        and all(_text(payload.get(field)) for field in AUTHORITY_FIELDS)
    )
    return [
        _authority(
            "final_authority",
            passed,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_AUTHORITY_BLOCKED,
            "Final authority manifest must include primary reviewer, second reviewer, and scope.",
            settings.final_authority_manifest_path,
            _text(payload.get("authority_result")),
        )
    ]


def _check_attestation(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionAttestationResult]:
    payload = _read_json(settings.final_attestation_manifest_path)
    passed = _path_exists(settings.final_attestation_manifest_path) and all(
        _to_bool(payload.get(field)) for field in ATTESTATION_TRUE_FIELDS
    )
    return [
        ActiveReplayInputReadyEmissionAttestationResult(
            gate_group="final_attestation",
            gate_name="required_attestations",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_ATTESTATION_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Final emission attestations are incomplete.",
            evidence_path=_path_str(settings.final_attestation_manifest_path),
            observed_value=_missing_true_fields(payload, ATTESTATION_TRUE_FIELDS),
        )
    ]


def _check_pit_source_evidence(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionPitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_bundle_path)
    if not _path_exists(settings.pit_source_evidence_bundle_path):
        return [
            _pit_source(
                "evidence_bundle_present",
                False,
                ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
                "PIT/source/evidence bundle is missing.",
                settings.pit_source_evidence_bundle_path,
            )
        ]
    return [
        _pit_source(
            "pit_coverage",
            all(_to_bool(payload.get(field)) for field in PIT_TRUE_FIELDS),
            ACTIVE_REPLAY_INPUT_READY_EMISSION_PIT_BLOCKED,
            "PIT coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, PIT_TRUE_FIELDS),
        ),
        _pit_source(
            "source_coverage",
            all(_to_bool(payload.get(field)) for field in SOURCE_TRUE_FIELDS),
            ACTIVE_REPLAY_INPUT_READY_EMISSION_SOURCE_BLOCKED,
            "Source coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, SOURCE_TRUE_FIELDS),
        ),
        _pit_source(
            "evidence_coverage",
            all(_to_bool(payload.get(field)) for field in EVIDENCE_TRUE_FIELDS),
            ACTIVE_REPLAY_INPUT_READY_EMISSION_EVIDENCE_BLOCKED,
            "Evidence coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS),
        ),
    ]


def _check_taxonomy(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionTaxonomyResult]:
    payload = _read_json(settings.taxonomy_evidence_bundle_path)
    passed = _path_exists(settings.taxonomy_evidence_bundle_path) and all(
        _to_bool(payload.get(field)) for field in TAXONOMY_TRUE_FIELDS
    )
    return [
        ActiveReplayInputReadyEmissionTaxonomyResult(
            gate_group="taxonomy",
            gate_name="eight_layer_taxonomy",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_TAXONOMY_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "8-layer taxonomy evidence is incomplete.",
            evidence_path=_path_str(settings.taxonomy_evidence_bundle_path),
            observed_value=_missing_true_fields(payload, TAXONOMY_TRUE_FIELDS),
        )
    ]


def _check_leakage_side_effect(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    if not _path_exists(settings.leakage_side_effect_evidence_bundle_path):
        return [
            _leakage(
                "leakage_side_effect_bundle_present",
                False,
                ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
                "Leakage/side-effect evidence bundle is missing.",
                settings.leakage_side_effect_evidence_bundle_path,
            )
        ]
    return [
        _leakage(
            "leakage_checks",
            all(_to_bool(payload.get(field)) for field in LEAKAGE_TRUE_FIELDS),
            ACTIVE_REPLAY_INPUT_READY_EMISSION_LEAKAGE_BLOCKED,
            "Leakage checks are incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS),
        ),
        _leakage(
            "side_effect_checks",
            all(_to_bool(payload.get(field)) for field in SIDE_EFFECT_TRUE_FIELDS),
            ACTIVE_REPLAY_INPUT_READY_EMISSION_SIDE_EFFECT_BLOCKED,
            "Side-effect checks are incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS),
        ),
    ]


def _check_overclaim(
    settings: ActiveReplayInputReadyEmissionSettings,
) -> list[ActiveReplayInputReadyEmissionOverclaimResult]:
    payload = _read_json(settings.overclaim_evidence_bundle_path)
    passed = _path_exists(settings.overclaim_evidence_bundle_path) and all(
        _to_bool(payload.get(field)) for field in OVERCLAIM_TRUE_FIELDS
    )
    return [
        ActiveReplayInputReadyEmissionOverclaimResult(
            gate_group="overclaim",
            gate_name="overclaim_bundle",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Overclaim evidence is incomplete.",
            evidence_path=_path_str(settings.overclaim_evidence_bundle_path),
            observed_value=_missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS),
        )
    ]


def _check_false_fields(
    payloads: list[dict[str, Any]], fields: list[str], failure_status: str
) -> list[ActiveReplayInputReadyEmissionLeakageSideEffectResult | ActiveReplayInputReadyEmissionOverclaimResult]:
    results: list[
        ActiveReplayInputReadyEmissionLeakageSideEffectResult | ActiveReplayInputReadyEmissionOverclaimResult
    ] = []
    cls: type[ActiveReplayInputReadyEmissionLeakageSideEffectResult | ActiveReplayInputReadyEmissionOverclaimResult]
    cls = (
        ActiveReplayInputReadyEmissionOverclaimResult
        if failure_status == ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED
        else ActiveReplayInputReadyEmissionLeakageSideEffectResult
    )
    for field in fields:
        offenders = [payload for payload in payloads if _to_bool(payload.get(field))]
        results.append(
            cls(
                gate_group="false_field_guard",
                gate_name=field,
                status=failure_status if offenders else "PASS",
                passed=not offenders,
                blocker_reason=f"{field} must remain false." if offenders else "",
                evidence_path="input_payloads",
                observed_value=str(bool(offenders)),
            )
        )
    return results


def _built_in_overclaim_guards(output_dir: Path) -> list[ActiveReplayInputReadyEmissionOverclaimResult]:
    conditions = [
        ("ready_to_emit_not_active_replay_input_ready", True),
        ("emission_decision_ready_not_active_replay_input_ready", True),
        ("active_replay_input_ready_not_active_input", True),
        ("active_replay_input_ready_not_replay", True),
        ("active_replay_input_ready_not_replay_decisions", True),
        ("active_replay_input_ready_not_labels", True),
        ("active_replay_input_ready_not_training", True),
        ("active_replay_input_ready_not_stock_profile", True),
        ("active_replay_input_ready_not_buy_review", True),
        ("active_replay_input_ready_not_trading", True),
    ]
    return [
        ActiveReplayInputReadyEmissionOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_READY_EMISSION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else f"{name} failed.",
            evidence_path=str(output_dir),
            observed_value=str(passed),
        )
        for name, passed in conditions
    ]


def _resolve_status(
    *,
    has_input: bool,
    precondition_results: list[ActiveReplayInputReadyEmissionPreconditionResult],
    lineage_results: list[ActiveReplayInputReadyEmissionLineageResult],
    authority_results: list[ActiveReplayInputReadyEmissionAuthorityResult],
    attestation_results: list[ActiveReplayInputReadyEmissionAttestationResult],
    pit_source_results: list[ActiveReplayInputReadyEmissionPitSourceEvidenceResult],
    taxonomy_results: list[ActiveReplayInputReadyEmissionTaxonomyResult],
    leakage_side_effect_results: list[ActiveReplayInputReadyEmissionLeakageSideEffectResult],
    overclaim_results: list[ActiveReplayInputReadyEmissionOverclaimResult],
) -> str:
    if not has_input:
        return NO_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
    for collection in [
        precondition_results,
        lineage_results,
        authority_results,
        attestation_results,
        pit_source_results,
        taxonomy_results,
        leakage_side_effect_results,
        overclaim_results,
    ]:
        for result in collection:
            if not result.passed and result.status != "PASS":
                return result.status
    return READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION


def _metadata(result: ActiveReplayInputReadyEmissionResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    return payload


def _render_report(result: ActiveReplayInputReadyEmissionResult) -> str:
    return "\n".join(
        [
            "# ACTIVE_REPLAY_INPUT_READY Emission Decision Core Report",
            "",
            f"- active_ready_emission_run_id: {result.active_ready_emission_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            "- ready_for_active_replay_input_ready_emission_decision: "
            f"{result.ready_for_active_replay_input_ready_emission_decision}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- active_ready_emitted: {result.active_ready_emitted}",
            f"- blocker_count: {result.blocker_count}",
            "",
            "`READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION is not ACTIVE_REPLAY_INPUT_READY`.",
            "",
            "This workflow does not emit ACTIVE_REPLAY_INPUT_READY, does not create active replay input, "
            "does not run replay, does not create replay decisions, does not compute labels, does not train "
            "weights, does not create stock profiles, does not create buy-review eligibility, does not approve "
            "paper workflow, does not validate strategy performance, and does not authorize trading.",
            "",
            "It also does not call broker APIs, place orders, send messages, call LLM or external APIs, mutate "
            "cache, write data/raw, write data/processed, write data/cache, run current-candidates, or build "
            "snapshots.",
        ]
    )


def _write_frame(path: Path, rows: list[Any]) -> None:
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_run_id(settings: ActiveReplayInputReadyEmissionSettings, generated_at: str) -> str:
    seed = json.dumps(
        {
            "generated_at": generated_at,
            "ready_to_emit_artifact_path": _path_str(settings.ready_to_emit_artifact_path),
            "active_ready_health_artifact_path": _path_str(settings.active_ready_health_artifact_path),
            "active_ready_status_artifact_path": _path_str(settings.active_ready_status_artifact_path),
            "final_emission_request_manifest_path": _path_str(settings.final_emission_request_manifest_path),
            "final_authority_manifest_path": _path_str(settings.final_authority_manifest_path),
            "final_attestation_manifest_path": _path_str(settings.final_attestation_manifest_path),
            "output_dir": str(settings.output_dir),
            "config_version": settings.config_version,
        },
        sort_keys=True,
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def _load_artifact_payload(path: Path | None, metadata_name: str) -> dict[str, Any]:
    if path is None:
        return {}
    if path.is_dir():
        return _read_json(path / metadata_name)
    return _read_json(path)


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists() or path.is_dir():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _lineage(
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    path: Path | None,
    observed_value: str = "",
) -> ActiveReplayInputReadyEmissionLineageResult:
    return ActiveReplayInputReadyEmissionLineageResult(
        gate_group="ready_to_emit_lineage",
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=_path_str(path),
        observed_value=observed_value,
    )


def _authority(
    gate_name: str,
    passed: bool,
    failure_status: str,
    blocker_reason: str,
    path: Path | None,
    observed_value: str,
) -> ActiveReplayInputReadyEmissionAuthorityResult:
    return ActiveReplayInputReadyEmissionAuthorityResult(
        gate_group="final_authority",
        gate_name=gate_name,
        status="PASS" if passed else failure_status,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        evidence_path=_path_str(path),
        observed_value=observed_value,
    )


def _pit_source(
    gate_name: str,
    passed: bool,
    failure_status: str,
    blocker_reason: str,
    path: Path | None,
    observed_value: str = "",
) -> ActiveReplayInputReadyEmissionPitSourceEvidenceResult:
    return ActiveReplayInputReadyEmissionPitSourceEvidenceResult(
        gate_group="pit_source_evidence",
        gate_name=gate_name,
        status="PASS" if passed else failure_status,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        evidence_path=_path_str(path),
        observed_value=observed_value,
    )


def _leakage(
    gate_name: str,
    passed: bool,
    failure_status: str,
    blocker_reason: str,
    path: Path | None,
    observed_value: str = "",
) -> ActiveReplayInputReadyEmissionLeakageSideEffectResult:
    return ActiveReplayInputReadyEmissionLeakageSideEffectResult(
        gate_group="leakage_side_effect",
        gate_name=gate_name,
        status="PASS" if passed else failure_status,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        evidence_path=_path_str(path),
        observed_value=observed_value,
    )


def _path_exists(path: Path | None) -> bool:
    return path is not None and path.exists()


def _path_str(path: Path | None) -> str:
    return "" if path is None else str(path)


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "accepted"}
    return False


def _passish(value: Any) -> bool:
    return _text(value).upper() in PASS_RESULTS


def _missing_true_fields(payload: dict[str, Any], fields: list[str]) -> str:
    missing = [field for field in fields if not _to_bool(payload.get(field))]
    return ",".join(missing)


def _passed(rows: list[Any]) -> int:
    return sum(1 for row in rows if row.passed)


def _blocked(rows: list[Any]) -> int:
    return sum(1 for row in rows if not row.passed)


def _ensure_manual_diagnostics_path(path: Path) -> None:
    parts = [part.lower() for part in path.parts]
    try:
        outputs_index = parts.index("outputs")
        reports_index = parts.index("reports")
        diagnostics_index = parts.index("manual_diagnostics")
    except ValueError as exc:
        raise ValueError(
            "ACTIVE_REPLAY_INPUT_READY emission artifacts must stay under manual_diagnostics"
        ) from exc
    if not (outputs_index < reports_index < diagnostics_index):
        raise ValueError(
            "ACTIVE_REPLAY_INPUT_READY emission artifacts must stay under outputs/reports/manual_diagnostics"
        )
