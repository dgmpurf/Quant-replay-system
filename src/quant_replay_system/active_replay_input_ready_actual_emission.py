"""Report-only actual ACTIVE_REPLAY_INPUT_READY marker emission workflow.

This workflow may emit only a marker artifact when every governance gate passes
and the explicit allow flag is supplied. It never creates active replay input,
runs replay, creates replay decisions, computes labels, trains weights, creates
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


NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT = "NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND = (
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND"
)
ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED"
ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED = "ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED"
READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION = "READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION"
ACTIVE_REPLAY_INPUT_READY = "ACTIVE_REPLAY_INPUT_READY"

READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION = (
    "READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION"
)
ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY = "ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_ready_actual_emission_v0_1")
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
AUTHORITY_FIELDS = [
    "primary_reviewer",
    "second_reviewer",
    "authorized_by",
    "authorized_at",
    "authority_scope",
    "authority_reason",
]
ATTESTATION_TRUE_FIELDS = [
    "second_reviewer_attested",
    "marker_only_attested",
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
    "marker_only_not_active_input",
    "marker_only_not_replay_permission",
    "marker_only_not_replay_decision",
    "marker_only_not_labels",
    "marker_only_not_training",
    "marker_only_not_stock_profile",
    "marker_only_not_buy_review",
    "marker_only_not_trading",
    "marker_only_not_performance_validation",
    "marker_only_not_paper_approval",
    "report_only",
    "diagnostic_only",
]


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionSettings:
    emission_decision_artifact_path: Path | None = None
    emission_decision_health_artifact_path: Path | None = None
    emission_decision_status_artifact_path: Path | None = None
    actual_emission_plan_path: Path | None = None
    actual_emission_request_manifest_path: Path | None = None
    final_authority_manifest_path: Path | None = None
    second_reviewer_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    active_replay_input_ready_marker_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_active_replay_input_ready_marker_emission: bool = False
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionPreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionAuthorityResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionLineageResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionAttestationResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionTaxonomyResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionLeakageSideEffectResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionOverclaimResult(
    ActualActiveReplayInputReadyEmissionPreconditionResult
):
    pass


@dataclass(frozen=True)
class ActualActiveReplayInputReadyEmissionResult:
    actual_emission_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActualActiveReplayInputReadyEmissionPreconditionResult]
    authority_results: list[ActualActiveReplayInputReadyEmissionAuthorityResult]
    lineage_results: list[ActualActiveReplayInputReadyEmissionLineageResult]
    attestation_results: list[ActualActiveReplayInputReadyEmissionAttestationResult]
    pit_source_evidence_results: list[ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult]
    taxonomy_results: list[ActualActiveReplayInputReadyEmissionTaxonomyResult]
    leakage_side_effect_results: list[ActualActiveReplayInputReadyEmissionLeakageSideEffectResult]
    overclaim_results: list[ActualActiveReplayInputReadyEmissionOverclaimResult]
    emission_decision_artifact_path: str
    emission_decision_health_artifact_path: str
    emission_decision_status_artifact_path: str
    actual_emission_plan_path: str
    actual_emission_request_manifest_path: str
    final_authority_manifest_path: str
    second_reviewer_attestation_manifest_path: str
    pit_source_evidence_bundle_path: str
    taxonomy_evidence_bundle_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    active_replay_input_ready_marker_candidate_manifest_path: str
    allow_active_replay_input_ready_marker_emission: bool
    blocker_count: int
    issue_count: int
    warning_count: int
    active_replay_input_ready_marker_emitted: bool
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


def run_actual_active_replay_input_ready_emission(
    settings: ActualActiveReplayInputReadyEmissionSettings | None = None,
) -> ActualActiveReplayInputReadyEmissionResult:
    settings = settings or ActualActiveReplayInputReadyEmissionSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    actual_emission_run_id = _build_run_id(settings, generated_at)
    artifact_path = settings.output_dir / actual_emission_run_id

    has_input = any(
        [
            settings.emission_decision_artifact_path,
            settings.emission_decision_health_artifact_path,
            settings.emission_decision_status_artifact_path,
            settings.actual_emission_plan_path,
            settings.actual_emission_request_manifest_path,
            settings.final_authority_manifest_path,
            settings.second_reviewer_attestation_manifest_path,
            settings.pit_source_evidence_bundle_path,
            settings.taxonomy_evidence_bundle_path,
            settings.leakage_side_effect_evidence_bundle_path,
            settings.overclaim_evidence_bundle_path,
            settings.active_replay_input_ready_marker_candidate_manifest_path,
        ]
    )
    precondition_results = [
        ActualActiveReplayInputReadyEmissionPreconditionResult(
            gate_group="actual_active_replay_input_ready_emission_input",
            gate_name="actual_emission_input_present",
            status=ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT_FOUND
            if has_input
            else NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No actual ACTIVE_REPLAY_INPUT_READY emission input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    emission_payload = _load_artifact_payload(
        settings.emission_decision_artifact_path, "active_ready_emission_metadata.json"
    )
    health_payload = _read_json(settings.emission_decision_health_artifact_path)
    status_payload = _read_json(settings.emission_decision_status_artifact_path)
    request_payload = _read_json(settings.actual_emission_request_manifest_path)
    marker_candidate_payload = _read_json(settings.active_replay_input_ready_marker_candidate_manifest_path)

    lineage_results = _check_emission_decision_lineage(settings, emission_payload, health_payload, status_payload)
    precondition_results.extend(_check_actual_emission_plan(settings))
    authority_results = _check_actual_emission_request(settings, request_payload)
    authority_results.extend(_check_authority(settings))
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    taxonomy_results = _check_taxonomy(settings)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)

    safety_payloads = [
        payload for payload in [emission_payload, status_payload, request_payload, marker_candidate_payload] if payload
    ]
    leakage_side_effect_results.extend(
        _check_false_fields(safety_payloads, LEAKAGE_FALSE_FIELDS, ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED)
    )
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads, SIDE_EFFECT_FALSE_FIELDS, ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED
        )
    )
    overclaim_results.extend(
        _check_false_fields(safety_payloads, OVERCLAIM_FALSE_FIELDS, ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED)
    )
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    base_status = _resolve_status(
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
    status = (
        ACTIVE_REPLAY_INPUT_READY
        if base_status == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION
        and settings.allow_active_replay_input_ready_marker_emission
        else base_status
    )
    marker_emitted = status == ACTIVE_REPLAY_INPUT_READY
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
    result = ActualActiveReplayInputReadyEmissionResult(
        actual_emission_run_id=actual_emission_run_id,
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
        emission_decision_artifact_path=_path_str(settings.emission_decision_artifact_path),
        emission_decision_health_artifact_path=_path_str(settings.emission_decision_health_artifact_path),
        emission_decision_status_artifact_path=_path_str(settings.emission_decision_status_artifact_path),
        actual_emission_plan_path=_path_str(settings.actual_emission_plan_path),
        actual_emission_request_manifest_path=_path_str(settings.actual_emission_request_manifest_path),
        final_authority_manifest_path=_path_str(settings.final_authority_manifest_path),
        second_reviewer_attestation_manifest_path=_path_str(
            settings.second_reviewer_attestation_manifest_path
        ),
        pit_source_evidence_bundle_path=_path_str(settings.pit_source_evidence_bundle_path),
        taxonomy_evidence_bundle_path=_path_str(settings.taxonomy_evidence_bundle_path),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle_path),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle_path),
        active_replay_input_ready_marker_candidate_manifest_path=_path_str(
            settings.active_replay_input_ready_marker_candidate_manifest_path
        ),
        allow_active_replay_input_ready_marker_emission=settings.allow_active_replay_input_ready_marker_emission,
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        active_replay_input_ready_marker_emitted=marker_emitted,
        active_replay_input_ready=marker_emitted,
        active_replay_input=False,
        active_ready_emitted=marker_emitted,
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
        artifact_paths=resolve_actual_active_replay_input_ready_emission_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_actual_active_replay_input_ready_emission_artifacts(result)
    return result


def resolve_actual_active_replay_input_ready_emission_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "actual_emission_metadata.json",
        "report": artifact_path / "actual_emission_report.md",
        "precondition_results": artifact_path / "actual_emission_precondition_results.csv",
        "authority_results": artifact_path / "actual_emission_authority_results.csv",
        "lineage_results": artifact_path / "actual_emission_lineage_results.csv",
        "attestation_results": artifact_path / "actual_emission_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "marker": artifact_path / "active_replay_input_ready_marker.json",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_actual_active_replay_input_ready_emission_artifacts(
    result: ActualActiveReplayInputReadyEmissionResult,
) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_frame(result.artifact_paths["precondition_results"], result.precondition_results)
    _write_frame(result.artifact_paths["authority_results"], result.authority_results)
    _write_frame(result.artifact_paths["lineage_results"], result.lineage_results)
    _write_frame(result.artifact_paths["attestation_results"], result.attestation_results)
    _write_frame(result.artifact_paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_frame(result.artifact_paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_frame(result.artifact_paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_frame(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)
    _write_json(result.artifact_paths["marker"], _marker_payload(result))
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _check_emission_decision_lineage(
    settings: ActualActiveReplayInputReadyEmissionSettings,
    emission_payload: dict[str, Any],
    health_payload: dict[str, Any],
    status_payload: dict[str, Any],
) -> list[ActualActiveReplayInputReadyEmissionLineageResult]:
    results: list[ActualActiveReplayInputReadyEmissionLineageResult] = []
    if not _path_exists(settings.emission_decision_artifact_path):
        results.append(
            _lineage(
                "emission_decision_artifact",
                ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
                False,
                "Emission-decision artifact is missing.",
                settings.emission_decision_artifact_path,
            )
        )
    else:
        status = _text(emission_payload.get("status"))
        ready = _to_bool(emission_payload.get("ready_for_active_replay_input_ready_emission_decision"))
        passed = status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION and ready
        results.append(
            _lineage(
                "emission_decision_status",
                "PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
                passed,
                "" if passed else "Emission-decision artifact is not ready for actual marker emission.",
                settings.emission_decision_artifact_path,
                status,
            )
        )
    health_status = _text(health_payload.get("health_status") or health_payload.get("status"))
    passed_health = _path_exists(settings.emission_decision_health_artifact_path) and health_status == "PASS"
    results.append(
        _lineage(
            "emission_decision_health",
            "PASS" if passed_health else ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
            passed_health,
            "" if passed_health else "Emission-decision health must be PASS.",
            settings.emission_decision_health_artifact_path,
            health_status,
        )
    )
    summary_status = _text(status_payload.get("status"))
    summary_stage = _text(status_payload.get("workflow_stage"))
    passed_summary = (
        _path_exists(settings.emission_decision_status_artifact_path)
        and summary_status == READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION
        and summary_stage
        in {
            READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION,
            ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION_READY,
        }
        and _to_bool(status_payload.get("ready_for_active_replay_input_ready_emission_decision"))
    )
    results.append(
        _lineage(
            "emission_decision_status_artifact",
            "PASS" if passed_summary else ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED,
            passed_summary,
            "" if passed_summary else "Emission-decision status summary is not ready.",
            settings.emission_decision_status_artifact_path,
            summary_status or summary_stage,
        )
    )
    return results


def _check_actual_emission_plan(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionPreconditionResult]:
    passed = _path_exists(settings.actual_emission_plan_path)
    return [
        ActualActiveReplayInputReadyEmissionPreconditionResult(
            gate_group="actual_emission_review",
            gate_name="actual_emission_plan_present",
            status="PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Actual marker emission plan path is missing.",
            evidence_path=_path_str(settings.actual_emission_plan_path),
            observed_value=str(passed),
        )
    ]


def _check_actual_emission_request(
    settings: ActualActiveReplayInputReadyEmissionSettings,
    payload: dict[str, Any],
) -> list[ActualActiveReplayInputReadyEmissionAuthorityResult]:
    passed = (
        _path_exists(settings.actual_emission_request_manifest_path)
        and _passish(payload.get("request_result"))
        and _to_bool(payload.get("explicit_actual_active_replay_input_ready_emission_request"))
        and _text(payload.get("requested_marker_status")) == ACTIVE_REPLAY_INPUT_READY
        and _to_bool(payload.get("marker_only"))
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
    )
    return [
        _authority(
            "actual_emission_request",
            passed,
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED,
            "Actual emission request must be explicit, marker-only, report_only, and diagnostic_only.",
            settings.actual_emission_request_manifest_path,
            _text(payload.get("request_result")),
        )
    ]


def _check_authority(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionAuthorityResult]:
    payload = _read_json(settings.final_authority_manifest_path)
    passed = (
        _path_exists(settings.final_authority_manifest_path)
        and _passish(payload.get("authority_result"))
        and all(_text(payload.get(field)) for field in AUTHORITY_FIELDS)
        and "marker" in _text(payload.get("authority_scope")).lower()
    )
    return [
        _authority(
            "final_authority",
            passed,
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED,
            "Final authority manifest must include reviewer fields and marker-only scope.",
            settings.final_authority_manifest_path,
            _text(payload.get("authority_result")),
        )
    ]


def _check_attestation(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionAttestationResult]:
    payload = _read_json(settings.second_reviewer_attestation_manifest_path)
    passed = _path_exists(settings.second_reviewer_attestation_manifest_path) and all(
        _to_bool(payload.get(field)) for field in ATTESTATION_TRUE_FIELDS
    )
    return [
        ActualActiveReplayInputReadyEmissionAttestationResult(
            gate_group="second_reviewer_attestation",
            gate_name="required_attestations",
            status="PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Second reviewer marker-only attestations are incomplete.",
            evidence_path=_path_str(settings.second_reviewer_attestation_manifest_path),
            observed_value=_missing_true_fields(payload, ATTESTATION_TRUE_FIELDS),
        )
    ]


def _check_pit_source_evidence(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_bundle_path)
    if not _path_exists(settings.pit_source_evidence_bundle_path):
        return [
            _pit_source(
                "evidence_bundle_present",
                False,
                ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
                "PIT/source/evidence bundle is missing.",
                settings.pit_source_evidence_bundle_path,
            )
        ]
    return [
        _pit_source(
            "pit_coverage",
            all(_to_bool(payload.get(field)) for field in PIT_TRUE_FIELDS),
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED,
            "PIT coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, PIT_TRUE_FIELDS),
        ),
        _pit_source(
            "source_coverage",
            all(_to_bool(payload.get(field)) for field in SOURCE_TRUE_FIELDS),
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED,
            "Source coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, SOURCE_TRUE_FIELDS),
        ),
        _pit_source(
            "evidence_coverage",
            all(_to_bool(payload.get(field)) for field in EVIDENCE_TRUE_FIELDS),
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED,
            "Evidence coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS),
        ),
    ]


def _check_taxonomy(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionTaxonomyResult]:
    payload = _read_json(settings.taxonomy_evidence_bundle_path)
    passed = _path_exists(settings.taxonomy_evidence_bundle_path) and all(
        _to_bool(payload.get(field)) for field in TAXONOMY_TRUE_FIELDS
    )
    return [
        ActualActiveReplayInputReadyEmissionTaxonomyResult(
            gate_group="taxonomy",
            gate_name="eight_layer_taxonomy",
            status="PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "8-layer taxonomy evidence is incomplete.",
            evidence_path=_path_str(settings.taxonomy_evidence_bundle_path),
            observed_value=_missing_true_fields(payload, TAXONOMY_TRUE_FIELDS),
        )
    ]


def _check_leakage_side_effect(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    if not _path_exists(settings.leakage_side_effect_evidence_bundle_path):
        return [
            _leakage(
                "leakage_side_effect_bundle_present",
                False,
                ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
                "Leakage/side-effect evidence bundle is missing.",
                settings.leakage_side_effect_evidence_bundle_path,
            )
        ]
    return [
        _leakage(
            "leakage_checks",
            all(_to_bool(payload.get(field)) for field in LEAKAGE_TRUE_FIELDS),
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED,
            "Leakage checks are incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS),
        ),
        _leakage(
            "side_effect_checks",
            all(_to_bool(payload.get(field)) for field in SIDE_EFFECT_TRUE_FIELDS),
            ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED,
            "Side-effect checks are incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS),
        ),
    ]


def _check_overclaim(
    settings: ActualActiveReplayInputReadyEmissionSettings,
) -> list[ActualActiveReplayInputReadyEmissionOverclaimResult]:
    payload = _read_json(settings.overclaim_evidence_bundle_path)
    passed = _path_exists(settings.overclaim_evidence_bundle_path) and all(
        _to_bool(payload.get(field)) for field in OVERCLAIM_TRUE_FIELDS
    )
    return [
        ActualActiveReplayInputReadyEmissionOverclaimResult(
            gate_group="overclaim",
            gate_name="overclaim_bundle",
            status="PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Overclaim evidence is incomplete.",
            evidence_path=_path_str(settings.overclaim_evidence_bundle_path),
            observed_value=_missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS),
        )
    ]


def _check_false_fields(
    payloads: list[dict[str, Any]],
    fields: list[str],
    failure_status: str,
) -> list[ActualActiveReplayInputReadyEmissionLeakageSideEffectResult | ActualActiveReplayInputReadyEmissionOverclaimResult]:
    results: list[
        ActualActiveReplayInputReadyEmissionLeakageSideEffectResult
        | ActualActiveReplayInputReadyEmissionOverclaimResult
    ] = []
    cls: type[
        ActualActiveReplayInputReadyEmissionLeakageSideEffectResult
        | ActualActiveReplayInputReadyEmissionOverclaimResult
    ] = (
        ActualActiveReplayInputReadyEmissionOverclaimResult
        if failure_status == ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED
        else ActualActiveReplayInputReadyEmissionLeakageSideEffectResult
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


def _built_in_overclaim_guards(output_dir: Path) -> list[ActualActiveReplayInputReadyEmissionOverclaimResult]:
    conditions = [
        ("actual_marker_not_active_input", True),
        ("actual_marker_not_replay_permission", True),
        ("actual_marker_not_replay_decision", True),
        ("actual_marker_not_labels", True),
        ("actual_marker_not_training", True),
        ("actual_marker_not_stock_profile", True),
        ("actual_marker_not_buy_review", True),
        ("actual_marker_not_trading", True),
        ("actual_marker_not_performance_validation", True),
        ("actual_marker_not_paper_approval", True),
    ]
    return [
        ActualActiveReplayInputReadyEmissionOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status="PASS" if passed else ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED,
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
    precondition_results: list[ActualActiveReplayInputReadyEmissionPreconditionResult],
    lineage_results: list[ActualActiveReplayInputReadyEmissionLineageResult],
    authority_results: list[ActualActiveReplayInputReadyEmissionAuthorityResult],
    attestation_results: list[ActualActiveReplayInputReadyEmissionAttestationResult],
    pit_source_results: list[ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult],
    taxonomy_results: list[ActualActiveReplayInputReadyEmissionTaxonomyResult],
    leakage_side_effect_results: list[ActualActiveReplayInputReadyEmissionLeakageSideEffectResult],
    overclaim_results: list[ActualActiveReplayInputReadyEmissionOverclaimResult],
) -> str:
    if not has_input:
        return NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT
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
    return READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION


def _metadata(result: ActualActiveReplayInputReadyEmissionResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    return payload


def _marker_payload(result: ActualActiveReplayInputReadyEmissionResult) -> dict[str, Any]:
    return {
        "actual_emission_run_id": result.actual_emission_run_id,
        "marker_status": result.status,
        "workflow_stage": result.workflow_stage,
        "active_replay_input_ready_marker_emitted": result.active_replay_input_ready_marker_emitted,
        "active_replay_input_ready": result.active_replay_input_ready,
        "active_ready_emitted": result.active_ready_emitted,
        "active_replay_input": False,
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
        "order_placed": False,
        "broker_api_called": False,
        "message_sent": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "report_only": True,
        "diagnostic_only": True,
        "safety_statement": (
            "ACTIVE_REPLAY_INPUT_READY is marker-only and not active replay input, replay permission, "
            "replay decision permission, label permission, training permission, stock_profile permission, "
            "buy-review eligibility, paper approval, performance validation, broker permission, order "
            "permission, message permission, or trading authorization."
        ),
    }


def _render_report(result: ActualActiveReplayInputReadyEmissionResult) -> str:
    return "\n".join(
        [
            "# Actual ACTIVE_REPLAY_INPUT_READY Emission Core Report",
            "",
            f"- actual_emission_run_id: {result.actual_emission_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- active_replay_input_ready_marker_emitted: {result.active_replay_input_ready_marker_emitted}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- active_ready_emitted: {result.active_ready_emitted}",
            f"- blocker_count: {result.blocker_count}",
            "",
            "`ACTIVE_REPLAY_INPUT_READY` is marker-only in this workflow.",
            "",
            "It is not active replay input, does not run replay, does not create replay decisions, "
            "does not compute labels, does not train weights, does not create stock_profile artifacts, "
            "does not create buy-review eligibility, does not approve paper workflow, does not validate "
            "strategy performance, and does not authorize trading.",
            "",
            "It also does not call broker APIs, place orders, send messages, call LLM or external APIs, mutate "
            "cache, write data/raw, write data/processed, write data/cache, run current-candidates, or build "
            "snapshots.",
        ]
    )


def _render_next_task(result: ActualActiveReplayInputReadyEmissionResult) -> str:
    if result.status == ACTIVE_REPLAY_INPUT_READY:
        next_task = "Add actual ACTIVE_REPLAY_INPUT_READY marker artifact views and health/status checks."
    elif result.status == READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION:
        next_task = "Review whether to rerun with the explicit allow flag for marker-only emission."
    else:
        next_task = "Resolve actual ACTIVE_REPLAY_INPUT_READY emission blockers before marker-only emission."
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            next_task,
            "",
            "Do not create active replay input, run replay, create replay decisions, compute labels, train "
            "weights, create stock profiles, create buy-review eligibility, approve paper workflow, or "
            "authorize trading in this line.",
        ]
    )


def _write_frame(path: Path, rows: list[Any]) -> None:
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_run_id(settings: ActualActiveReplayInputReadyEmissionSettings, generated_at: str) -> str:
    seed = json.dumps(
        {
            "generated_at": generated_at,
            "emission_decision_artifact_path": _path_str(settings.emission_decision_artifact_path),
            "actual_emission_request_manifest_path": _path_str(settings.actual_emission_request_manifest_path),
            "final_authority_manifest_path": _path_str(settings.final_authority_manifest_path),
            "output_dir": str(settings.output_dir),
            "allow_active_replay_input_ready_marker_emission": (
                settings.allow_active_replay_input_ready_marker_emission
            ),
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
) -> ActualActiveReplayInputReadyEmissionLineageResult:
    return ActualActiveReplayInputReadyEmissionLineageResult(
        gate_group="emission_decision_lineage",
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
) -> ActualActiveReplayInputReadyEmissionAuthorityResult:
    return ActualActiveReplayInputReadyEmissionAuthorityResult(
        gate_group="actual_emission_authority",
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
) -> ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult:
    return ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult(
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
) -> ActualActiveReplayInputReadyEmissionLeakageSideEffectResult:
    return ActualActiveReplayInputReadyEmissionLeakageSideEffectResult(
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
    return ",".join(field for field in fields if not _to_bool(payload.get(field)))


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
            "Actual ACTIVE_REPLAY_INPUT_READY emission artifacts must stay under manual_diagnostics"
        ) from exc
    if not (outputs_index < reports_index < diagnostics_index):
        raise ValueError(
            "Actual ACTIVE_REPLAY_INPUT_READY emission artifacts must stay under outputs/reports/manual_diagnostics"
        )


__all__ = [
    "ACTIVE_REPLAY_INPUT_READY",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_ATTESTATION_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_AUTHORITY_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_EVIDENCE_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_LEAKAGE_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_LINEAGE_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_OVERCLAIM_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_PIT_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_REVIEW_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_SIDE_EFFECT_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_SOURCE_BLOCKED",
    "ACTUAL_ACTIVE_REPLAY_INPUT_READY_TAXONOMY_BLOCKED",
    "NO_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION_INPUT",
    "READY_FOR_ACTUAL_ACTIVE_REPLAY_INPUT_READY_EMISSION",
    "ActualActiveReplayInputReadyEmissionSettings",
    "ActualActiveReplayInputReadyEmissionResult",
    "ActualActiveReplayInputReadyEmissionPreconditionResult",
    "ActualActiveReplayInputReadyEmissionAuthorityResult",
    "ActualActiveReplayInputReadyEmissionLineageResult",
    "ActualActiveReplayInputReadyEmissionAttestationResult",
    "ActualActiveReplayInputReadyEmissionPitSourceEvidenceResult",
    "ActualActiveReplayInputReadyEmissionTaxonomyResult",
    "ActualActiveReplayInputReadyEmissionLeakageSideEffectResult",
    "ActualActiveReplayInputReadyEmissionOverclaimResult",
    "run_actual_active_replay_input_ready_emission",
    "write_actual_active_replay_input_ready_emission_artifacts",
]
