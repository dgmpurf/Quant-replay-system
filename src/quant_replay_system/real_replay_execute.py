"""Report-only real replay execution precheck workflow.

This workflow validates whether a governed active replay input package appears
ready for a future human-reviewed replay execution implementation. It never
runs replay, creates replay decisions, computes labels, trains weights, creates
stock profiles, changes buy-review eligibility, writes data stores, calls APIs,
mutates cache, or authorizes trading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_REAL_REPLAY_EXECUTION_INPUT = "NO_REAL_REPLAY_EXECUTION_INPUT"
REAL_REPLAY_EXECUTION_INPUT_FOUND = "REAL_REPLAY_EXECUTION_INPUT_FOUND"
REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED = "REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED"
REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED = "REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED"
REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED = "REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED"
REAL_REPLAY_EXECUTION_PIT_BLOCKED = "REAL_REPLAY_EXECUTION_PIT_BLOCKED"
REAL_REPLAY_EXECUTION_SOURCE_BLOCKED = "REAL_REPLAY_EXECUTION_SOURCE_BLOCKED"
REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED = "REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED"
REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED = "REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED"
REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED = "REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED"
REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED = "REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED"
REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED = "REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED"
REAL_REPLAY_EXECUTION_REVIEW_BLOCKED = "REAL_REPLAY_EXECUTION_REVIEW_BLOCKED"
READY_FOR_REAL_REPLAY_EXECUTION_REVIEW = "READY_FOR_REAL_REPLAY_EXECUTION_REVIEW"

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/real_replay_execute_v0_1")
ACTIVE_REPLAY_INPUT_CREATED = "ACTIVE_REPLAY_INPUT_CREATED"

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
    "real_replay_pre_execution_review_attested",
    "report_only_attested",
    "no_actual_replay_execution_attested",
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
SOURCE_TRUE_FIELDS = ["source_registry_evidence_attached"]
EVIDENCE_TRUE_FIELDS = ["raw_document_store_attached", "evidence_bundle_attached"]
TAXONOMY_TRUE_FIELDS = [
    "uses_8_layer_taxonomy",
    "not_fixed_12_only",
    "factor_definition_attached",
    "factor_observation_attached",
    "event_structured_attached",
    "company_exposure_attached",
    "factor_layer_metadata_attached",
    "report_only",
    "diagnostic_only",
]
FACTOR_EVENT_COMPANY_TRUE_FIELDS = [
    "factor_definition_attached",
    "factor_observation_attached",
    "event_structured_attached",
    "company_exposure_attached",
    "all_available_time_lte_replay_decision_time",
    "report_only",
    "diagnostic_only",
]
SOURCE_HASH_TRUE_FIELDS = [
    "source_hash_coverage_attached",
    "revision_id_coverage_attached",
    "available_time_policy_attached",
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
    "replay_precheck_not_replay_execution",
    "replay_precheck_not_replay_decision_permission",
    "replay_precheck_not_label_permission",
    "replay_precheck_not_training_permission",
    "replay_precheck_not_stock_profile_permission",
    "replay_precheck_not_buy_review_eligibility",
    "replay_precheck_not_paper_approval",
    "replay_precheck_not_performance_validation",
    "replay_precheck_not_trading_authorization",
    "active_input_not_replay_execution",
    "report_only",
    "diagnostic_only",
]
LEAKAGE_FALSE_FIELDS = [
    "future_labels_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_returns_exist",
    "replay_decisions_created",
    "replay_decisions_exist",
    "training_allowed",
    "training_outputs_exist",
    "model_weights_exist",
    "weights_trained",
    "stock_profile_allowed",
    "stock_profile_artifacts_exist",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
]
SIDE_EFFECT_FALSE_FIELDS = [
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
]
OVERCLAIM_FALSE_FIELDS = ["buy_review_allowed", "trading_allowed", "approved_for_paper"]
DOWNSTREAM_FALSE_FIELDS = [
    "replay_execution_started",
    "replay_execution_completed",
    "real_replay_executed",
    "replay_execution_allowed",
    "replay_decisions_created",
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "training_allowed",
    "weights_trained",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "trading_allowed",
    "order_placed",
    "broker_api_called",
    "message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
]


@dataclass(frozen=True)
class RealReplayExecuteSettings:
    active_replay_input_artifact_path: Path | None = None
    active_input_health_artifact_path: Path | None = None
    active_input_status_artifact_path: Path | None = None
    real_replay_execution_plan_path: Path | None = None
    replay_execution_request_manifest_path: Path | None = None
    replay_execution_authority_manifest_path: Path | None = None
    second_reviewer_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    factor_event_company_evidence_bundle_path: Path | None = None
    source_hash_revision_available_time_evidence_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    replay_execution_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class RealReplayExecutePreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class RealReplayExecuteAuthorityResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteLineageResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteAttestationResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecutePitSourceEvidenceResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteTaxonomyResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteLeakageSideEffectResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteOverclaimResult(RealReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class RealReplayExecuteResult:
    real_replay_execution_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    ready_for_real_replay_execution_review: bool
    precondition_results: list[RealReplayExecutePreconditionResult]
    authority_results: list[RealReplayExecuteAuthorityResult]
    lineage_results: list[RealReplayExecuteLineageResult]
    attestation_results: list[RealReplayExecuteAttestationResult]
    pit_source_evidence_results: list[RealReplayExecutePitSourceEvidenceResult]
    taxonomy_results: list[RealReplayExecuteTaxonomyResult]
    leakage_side_effect_results: list[RealReplayExecuteLeakageSideEffectResult]
    overclaim_results: list[RealReplayExecuteOverclaimResult]
    active_replay_input_artifact_path: str
    active_input_health_artifact_path: str
    active_input_status_artifact_path: str
    real_replay_execution_plan_path: str
    replay_execution_request_manifest_path: str
    replay_execution_authority_manifest_path: str
    second_reviewer_attestation_manifest_path: str
    pit_source_evidence_bundle_path: str
    taxonomy_evidence_bundle_path: str
    factor_event_company_evidence_bundle_path: str
    source_hash_revision_available_time_evidence_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    replay_execution_candidate_manifest_path: str
    source_active_input_creation_run_id: str
    source_active_replay_input_artifact_path: str
    replay_as_of_date: str
    replay_calendar: str
    blocker_count: int
    issue_count: int
    warning_count: int
    replay_execution_started: bool
    replay_execution_completed: bool
    real_replay_executed: bool
    replay_execution_allowed: bool
    replay_decisions_created: bool
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
    artifact_paths: dict[str, Path]


def run_real_replay_execute(settings: RealReplayExecuteSettings | None = None) -> RealReplayExecuteResult:
    settings = settings or RealReplayExecuteSettings()
    _ensure_manual_diagnostics_path(settings.output_dir)

    generated_at = datetime.now(timezone.utc).isoformat()
    real_replay_execution_run_id = _build_run_id(settings, generated_at)
    artifact_path = settings.output_dir / real_replay_execution_run_id

    has_input = any(
        [
            settings.active_replay_input_artifact_path,
            settings.active_input_health_artifact_path,
            settings.active_input_status_artifact_path,
            settings.real_replay_execution_plan_path,
            settings.replay_execution_request_manifest_path,
            settings.replay_execution_authority_manifest_path,
            settings.second_reviewer_attestation_manifest_path,
            settings.pit_source_evidence_bundle_path,
            settings.taxonomy_evidence_bundle_path,
            settings.factor_event_company_evidence_bundle_path,
            settings.source_hash_revision_available_time_evidence_path,
            settings.leakage_side_effect_evidence_bundle_path,
            settings.overclaim_evidence_bundle_path,
            settings.replay_execution_candidate_manifest_path,
        ]
    )
    precondition_results = [
        RealReplayExecutePreconditionResult(
            gate_group="real_replay_execution_input",
            gate_name="real_replay_execution_input_present",
            status=REAL_REPLAY_EXECUTION_INPUT_FOUND if has_input else NO_REAL_REPLAY_EXECUTION_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No real replay execution input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    active_payload = _load_artifact_payload(settings.active_replay_input_artifact_path, "active_replay_input.json")
    health_payload = _read_json(settings.active_input_health_artifact_path)
    status_payload = _read_json(settings.active_input_status_artifact_path)
    request_payload = _read_json(settings.replay_execution_request_manifest_path)
    candidate_payload = _read_json(settings.replay_execution_candidate_manifest_path)

    lineage_results = _check_active_input_lineage(settings, active_payload, health_payload, status_payload)
    precondition_results.extend(_check_execution_plan(settings))
    precondition_results.extend(_check_execution_request(settings, request_payload))
    precondition_results.extend(_check_candidate_manifest(settings, candidate_payload))
    authority_results = _check_authority(settings)
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    pit_source_results.extend(_check_factor_event_company(settings))
    pit_source_results.extend(_check_source_hash_revision_available_time(settings))
    taxonomy_results = _check_taxonomy(settings)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)

    safety_payloads = [
        payload
        for payload in [
            active_payload,
            status_payload,
            request_payload,
            candidate_payload,
            _read_json(settings.leakage_side_effect_evidence_bundle_path),
        ]
        if payload
    ]
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            LEAKAGE_FALSE_FIELDS,
            REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
            "leakage_false_field_guard",
        )
    )
    leakage_side_effect_results.extend(
        _check_false_fields(
            safety_payloads,
            SIDE_EFFECT_FALSE_FIELDS,
            REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
            "side_effect_false_field_guard",
        )
    )
    overclaim_results.extend(_check_overclaim_false_fields(safety_payloads))
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
    ready = status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
    workflow_stage = "REAL_REPLAY_EXECUTION_NO_INPUT" if status == NO_REAL_REPLAY_EXECUTION_INPUT else status
    source_active_input_creation_run_id = _text(
        active_payload.get("active_input_creation_run_id")
        or candidate_payload.get("source_active_input_creation_run_id")
    )
    source_active_replay_input_artifact_path = _text(
        candidate_payload.get("source_active_replay_input_artifact_path")
        or settings.active_replay_input_artifact_path
    )
    result = RealReplayExecuteResult(
        real_replay_execution_run_id=real_replay_execution_run_id,
        generated_at=generated_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=workflow_stage,
        ready_for_real_replay_execution_review=ready,
        precondition_results=precondition_results,
        authority_results=authority_results,
        lineage_results=lineage_results,
        attestation_results=attestation_results,
        pit_source_evidence_results=pit_source_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_side_effect_results,
        overclaim_results=overclaim_results,
        active_replay_input_artifact_path=_path_str(settings.active_replay_input_artifact_path),
        active_input_health_artifact_path=_path_str(settings.active_input_health_artifact_path),
        active_input_status_artifact_path=_path_str(settings.active_input_status_artifact_path),
        real_replay_execution_plan_path=_path_str(settings.real_replay_execution_plan_path),
        replay_execution_request_manifest_path=_path_str(settings.replay_execution_request_manifest_path),
        replay_execution_authority_manifest_path=_path_str(settings.replay_execution_authority_manifest_path),
        second_reviewer_attestation_manifest_path=_path_str(settings.second_reviewer_attestation_manifest_path),
        pit_source_evidence_bundle_path=_path_str(settings.pit_source_evidence_bundle_path),
        taxonomy_evidence_bundle_path=_path_str(settings.taxonomy_evidence_bundle_path),
        factor_event_company_evidence_bundle_path=_path_str(settings.factor_event_company_evidence_bundle_path),
        source_hash_revision_available_time_evidence_path=_path_str(
            settings.source_hash_revision_available_time_evidence_path
        ),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle_path),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle_path),
        replay_execution_candidate_manifest_path=_path_str(settings.replay_execution_candidate_manifest_path),
        source_active_input_creation_run_id=source_active_input_creation_run_id,
        source_active_replay_input_artifact_path=source_active_replay_input_artifact_path,
        replay_as_of_date=_text(active_payload.get("replay_as_of_date")),
        replay_calendar=_text(active_payload.get("replay_calendar")),
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        replay_execution_started=False,
        replay_execution_completed=False,
        real_replay_executed=False,
        replay_execution_allowed=False,
        replay_decisions_created=False,
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
        artifact_paths=resolve_real_replay_execute_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_real_replay_execute_artifacts(result, active_payload, candidate_payload)
    return result


def resolve_real_replay_execute_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "real_replay_execution_metadata.json",
        "report": artifact_path / "real_replay_execution_report.md",
        "precondition_results": artifact_path / "real_replay_precondition_results.csv",
        "authority_results": artifact_path / "real_replay_authority_results.csv",
        "lineage_results": artifact_path / "real_replay_lineage_results.csv",
        "attestation_results": artifact_path / "real_replay_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "precheck": artifact_path / "real_replay_execution_precheck.json",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_real_replay_execute_artifacts(
    result: RealReplayExecuteResult,
    active_payload: dict[str, Any] | None = None,
    candidate_payload: dict[str, Any] | None = None,
) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    active_payload = active_payload or {}
    candidate_payload = candidate_payload or {}
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_json(result.artifact_paths["precheck"], _precheck(result, active_payload, candidate_payload))
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")
    _write_frame(result.artifact_paths["precondition_results"], result.precondition_results)
    _write_frame(result.artifact_paths["authority_results"], result.authority_results)
    _write_frame(result.artifact_paths["lineage_results"], result.lineage_results)
    _write_frame(result.artifact_paths["attestation_results"], result.attestation_results)
    _write_frame(result.artifact_paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_frame(result.artifact_paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_frame(result.artifact_paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_frame(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)


def _check_active_input_lineage(
    settings: RealReplayExecuteSettings,
    active_payload: dict[str, Any],
    health_payload: dict[str, Any],
    status_payload: dict[str, Any],
) -> list[RealReplayExecuteLineageResult]:
    active_path = settings.active_replay_input_artifact_path
    health_path = settings.active_input_health_artifact_path
    status_path = settings.active_input_status_artifact_path
    input_status = _text(active_payload.get("input_status") or active_payload.get("status"))
    health_status = _text(health_payload.get("health_status") or health_payload.get("status"))
    status_status = _text(status_payload.get("status") or status_payload.get("input_status"))
    return [
        _lineage(
            "active_replay_input_artifact_exists",
            "PASS" if _path_exists(active_path) else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            _path_exists(active_path),
            "" if _path_exists(active_path) else "active_replay_input.json is missing.",
            active_path,
        ),
        _lineage(
            "active_input_status_is_created",
            "PASS" if input_status == ACTIVE_REPLAY_INPUT_CREATED else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            input_status == ACTIVE_REPLAY_INPUT_CREATED,
            "" if input_status == ACTIVE_REPLAY_INPUT_CREATED else "Active input status is not ACTIVE_REPLAY_INPUT_CREATED.",
            active_path,
            input_status,
        ),
        _lineage(
            "active_replay_input_created_true",
            "PASS" if _to_bool(active_payload.get("active_replay_input_created")) else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            _to_bool(active_payload.get("active_replay_input_created")),
            "" if _to_bool(active_payload.get("active_replay_input_created")) else "active_replay_input_created is not true.",
            active_path,
            str(active_payload.get("active_replay_input_created", "")),
        ),
        _lineage(
            "active_replay_input_true",
            "PASS" if _to_bool(active_payload.get("active_replay_input")) else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            _to_bool(active_payload.get("active_replay_input")),
            "" if _to_bool(active_payload.get("active_replay_input")) else "active_replay_input is not true.",
            active_path,
            str(active_payload.get("active_replay_input", "")),
        ),
        _lineage(
            "active_input_health_pass",
            "PASS" if health_status == "PASS" else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            health_status == "PASS",
            "" if health_status == "PASS" else "Active input health is not PASS.",
            health_path,
            health_status,
        ),
        _lineage(
            "active_input_status_artifact_created",
            "PASS" if status_status == ACTIVE_REPLAY_INPUT_CREATED else REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED,
            status_status == ACTIVE_REPLAY_INPUT_CREATED,
            "" if status_status == ACTIVE_REPLAY_INPUT_CREATED else "Active input status artifact is not ACTIVE_REPLAY_INPUT_CREATED.",
            status_path,
            status_status,
        ),
    ]


def _check_execution_plan(settings: RealReplayExecuteSettings) -> list[RealReplayExecutePreconditionResult]:
    exists = _path_exists(settings.real_replay_execution_plan_path)
    return [
        RealReplayExecutePreconditionResult(
            gate_group="real_replay_execution_review",
            gate_name="real_replay_execution_plan_present",
            status="PASS" if exists else REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
            passed=exists,
            blocker_reason="" if exists else "Real replay execution precheck plan is missing.",
            evidence_path=_path_str(settings.real_replay_execution_plan_path),
            observed_value=str(exists),
        )
    ]


def _check_execution_request(
    settings: RealReplayExecuteSettings,
    payload: dict[str, Any],
) -> list[RealReplayExecutePreconditionResult]:
    exists = _path_exists(settings.replay_execution_request_manifest_path)
    explicit_request = _to_bool(payload.get("explicit_real_replay_execution_review_request"))
    safe_scope = (
        not _to_bool(payload.get("actual_replay_execution_authorized"))
        and not _to_bool(payload.get("replay_decision_creation_authorized"))
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
    )
    passed = exists and explicit_request and safe_scope
    observed = []
    if not exists:
        observed.append("missing_manifest")
    if not explicit_request:
        observed.append("explicit_real_replay_execution_review_request")
    if not safe_scope:
        observed.append("safe_report_only_scope")
    return [
        RealReplayExecutePreconditionResult(
            gate_group="real_replay_execution_review",
            gate_name="replay_execution_request_manifest",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Replay execution review request is missing or not report-only.",
            evidence_path=_path_str(settings.replay_execution_request_manifest_path),
            observed_value=",".join(observed),
        )
    ]


def _check_candidate_manifest(
    settings: RealReplayExecuteSettings,
    payload: dict[str, Any],
) -> list[RealReplayExecutePreconditionResult]:
    exists = _path_exists(settings.replay_execution_candidate_manifest_path)
    required_text = ["source_active_replay_input_artifact_path", "source_active_input_creation_run_id"]
    missing = [field for field in required_text if not _text(payload.get(field))]
    true_failures = [field for field in ["deterministic_only", "future_labels_excluded", "report_only", "diagnostic_only"] if not _to_bool(payload.get(field))]
    false_failures = [field for field in DOWNSTREAM_FALSE_FIELDS if _to_bool(payload.get(field))]
    replay_decision_path = _text(payload.get("replay_decision_artifact_path"))
    if replay_decision_path:
        false_failures.append("replay_decision_artifact_path")
    passed = exists and not missing and not true_failures and not false_failures
    return [
        RealReplayExecutePreconditionResult(
            gate_group="real_replay_execution_review",
            gate_name="replay_execution_candidate_manifest",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_REVIEW_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Replay execution candidate manifest is incomplete or unsafe.",
            evidence_path=_path_str(settings.replay_execution_candidate_manifest_path),
            observed_value=",".join(missing + true_failures + false_failures),
        )
    ]


def _check_authority(settings: RealReplayExecuteSettings) -> list[RealReplayExecuteAuthorityResult]:
    payload = _read_json(settings.replay_execution_authority_manifest_path)
    exists = _path_exists(settings.replay_execution_authority_manifest_path)
    missing = [field for field in AUTHORITY_FIELDS if not _text(payload.get(field))]
    result = _text(payload.get("authority_result"))
    passed = (
        exists
        and not missing
        and result == "ACCEPTED_FOR_PRE_EXECUTION_REVIEW_ONLY"
        and not _to_bool(payload.get("can_authorize_actual_replay_execution"))
    )
    observed = missing[:]
    if result != "ACCEPTED_FOR_PRE_EXECUTION_REVIEW_ONLY":
        observed.append("authority_result")
    if _to_bool(payload.get("can_authorize_actual_replay_execution")):
        observed.append("can_authorize_actual_replay_execution")
    return [
        RealReplayExecuteAuthorityResult(
            gate_group="real_replay_execution_authority",
            gate_name="pre_execution_review_authority",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Replay execution authority is missing or exceeds pre-execution review scope.",
            evidence_path=_path_str(settings.replay_execution_authority_manifest_path),
            observed_value=",".join(observed),
        )
    ]


def _check_attestation(settings: RealReplayExecuteSettings) -> list[RealReplayExecuteAttestationResult]:
    payload = _read_json(settings.second_reviewer_attestation_manifest_path)
    exists = _path_exists(settings.second_reviewer_attestation_manifest_path)
    missing = _missing_true_fields(payload, ATTESTATION_TRUE_FIELDS)
    passed = exists and not missing
    return [
        RealReplayExecuteAttestationResult(
            gate_group="second_reviewer_attestation",
            gate_name="second_reviewer_report_only_attestation",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Second reviewer report-only attestation is incomplete.",
            evidence_path=_path_str(settings.second_reviewer_attestation_manifest_path),
            observed_value=missing,
        )
    ]


def _check_pit_source_evidence(settings: RealReplayExecuteSettings) -> list[RealReplayExecutePitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_bundle_path)
    exists = _path_exists(settings.pit_source_evidence_bundle_path)
    if not exists:
        return [
            _pit_source(
                "pit_source_evidence_bundle_present",
                REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
                False,
                "PIT/source/evidence bundle is missing.",
                settings.pit_source_evidence_bundle_path,
                "missing_bundle",
            )
        ]
    pit_missing = _missing_true_fields(payload, PIT_TRUE_FIELDS)
    source_missing = _missing_true_fields(payload, SOURCE_TRUE_FIELDS)
    evidence_missing = _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS)
    return [
        _pit_source(
            "accepted_pit_universe_evidence",
            "PASS" if not pit_missing else REAL_REPLAY_EXECUTION_PIT_BLOCKED,
            not pit_missing,
            "" if not pit_missing else "Accepted PIT universe evidence is missing.",
            settings.pit_source_evidence_bundle_path,
            pit_missing,
        ),
        _pit_source(
            "source_registry_evidence",
            "PASS" if not source_missing else REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
            not source_missing,
            "" if not source_missing else "Source registry evidence is missing.",
            settings.pit_source_evidence_bundle_path,
            source_missing,
        ),
        _pit_source(
            "raw_document_and_evidence_bundle",
            "PASS" if not evidence_missing else REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
            not evidence_missing,
            "" if not evidence_missing else "Raw document or evidence bundle evidence is missing.",
            settings.pit_source_evidence_bundle_path,
            evidence_missing,
        ),
    ]


def _check_factor_event_company(settings: RealReplayExecuteSettings) -> list[RealReplayExecutePitSourceEvidenceResult]:
    payload = _read_json(settings.factor_event_company_evidence_bundle_path)
    exists = _path_exists(settings.factor_event_company_evidence_bundle_path)
    missing = _missing_true_fields(payload, FACTOR_EVENT_COMPANY_TRUE_FIELDS)
    passed = exists and not missing
    return [
        _pit_source(
            "factor_event_company_pit_evidence",
            "PASS" if passed else REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
            passed,
            "" if passed else "Factor, event, or company exposure PIT evidence is incomplete.",
            settings.factor_event_company_evidence_bundle_path,
            missing if exists else "missing_bundle",
        )
    ]


def _check_source_hash_revision_available_time(
    settings: RealReplayExecuteSettings,
) -> list[RealReplayExecutePitSourceEvidenceResult]:
    payload = _read_json(settings.source_hash_revision_available_time_evidence_path)
    exists = _path_exists(settings.source_hash_revision_available_time_evidence_path)
    missing = _missing_true_fields(payload, SOURCE_HASH_TRUE_FIELDS)
    policy_ok = _text(payload.get("available_time_policy")) == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    passed = exists and not missing and policy_ok
    observed = missing
    if not policy_ok:
        observed = ",".join(filter(None, [observed, "available_time_policy"]))
    if not exists:
        observed = "missing_bundle"
    return [
        _pit_source(
            "source_hash_revision_available_time",
            "PASS" if passed else REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
            passed,
            "" if passed else "Source hash, revision_id, or available_time evidence is incomplete.",
            settings.source_hash_revision_available_time_evidence_path,
            observed,
        )
    ]


def _check_taxonomy(settings: RealReplayExecuteSettings) -> list[RealReplayExecuteTaxonomyResult]:
    payload = _read_json(settings.taxonomy_evidence_bundle_path)
    exists = _path_exists(settings.taxonomy_evidence_bundle_path)
    missing = _missing_true_fields(payload, TAXONOMY_TRUE_FIELDS)
    passed = exists and not missing
    return [
        RealReplayExecuteTaxonomyResult(
            gate_group="taxonomy_evidence",
            gate_name="eight_layer_taxonomy_evidence",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "8-layer taxonomy evidence is incomplete.",
            evidence_path=_path_str(settings.taxonomy_evidence_bundle_path),
            observed_value=missing if exists else "missing_bundle",
        )
    ]


def _check_leakage_side_effect(
    settings: RealReplayExecuteSettings,
) -> list[RealReplayExecuteLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    exists = _path_exists(settings.leakage_side_effect_evidence_bundle_path)
    leakage_missing = _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS)
    side_missing = _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS)
    return [
        _leakage(
            "leakage_exclusion_checks",
            "PASS" if exists and not leakage_missing else REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED,
            exists and not leakage_missing,
            "" if exists and not leakage_missing else "Leakage exclusion evidence is incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            leakage_missing if exists else "missing_bundle",
        ),
        _leakage(
            "side_effect_exclusion_checks",
            "PASS" if exists and not side_missing else REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED,
            exists and not side_missing,
            "" if exists and not side_missing else "Side-effect exclusion evidence is incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            side_missing if exists else "missing_bundle",
        ),
    ]


def _check_overclaim(settings: RealReplayExecuteSettings) -> list[RealReplayExecuteOverclaimResult]:
    payload = _read_json(settings.overclaim_evidence_bundle_path)
    exists = _path_exists(settings.overclaim_evidence_bundle_path)
    missing = _missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS)
    passed = exists and not missing
    return [
        RealReplayExecuteOverclaimResult(
            gate_group="overclaim_guard",
            gate_name="real_replay_precheck_boundary_guards",
            status="PASS" if passed else REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Overclaim guard evidence is incomplete.",
            evidence_path=_path_str(settings.overclaim_evidence_bundle_path),
            observed_value=missing if exists else "missing_bundle",
        )
    ]


def _check_false_fields(
    payloads: list[dict[str, Any]],
    fields: list[str],
    failure_status: str,
    gate_group: str,
) -> list[RealReplayExecuteLeakageSideEffectResult]:
    results: list[RealReplayExecuteLeakageSideEffectResult] = []
    for field in fields:
        offenders = [payload for payload in payloads if _to_bool(payload.get(field))]
        passed = not offenders
        results.append(
            RealReplayExecuteLeakageSideEffectResult(
                gate_group=gate_group,
                gate_name=field,
                status="PASS" if passed else failure_status,
                passed=passed,
                blocker_reason="" if passed else f"{field} must remain false for real replay execution precheck.",
                evidence_path="input_payloads",
                observed_value=str(bool(offenders)),
            )
        )
    return results


def _check_overclaim_false_fields(payloads: list[dict[str, Any]]) -> list[RealReplayExecuteOverclaimResult]:
    results: list[RealReplayExecuteOverclaimResult] = []
    for field in OVERCLAIM_FALSE_FIELDS:
        offenders = [payload for payload in payloads if _to_bool(payload.get(field))]
        passed = not offenders
        results.append(
            RealReplayExecuteOverclaimResult(
                gate_group="overclaim_false_field_guard",
                gate_name=field,
                status="PASS" if passed else REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
                passed=passed,
                blocker_reason="" if passed else f"{field} must remain false for real replay execution precheck.",
                evidence_path="input_payloads",
                observed_value=str(bool(offenders)),
            )
        )
    return results


def _built_in_overclaim_guards(output_dir: Path) -> list[RealReplayExecuteOverclaimResult]:
    manual_path_ok = "manual_diagnostics" in output_dir.parts
    guards = [
        (
            "output_path_under_manual_diagnostics",
            manual_path_ok,
            "Output path must remain under outputs/reports/manual_diagnostics.",
        ),
        (
            "precheck_not_replay_execution",
            True,
            "Real replay execute core is a pre-execution review, not replay execution.",
        ),
        (
            "precheck_not_trading",
            True,
            "Real replay execute core is not trading authorization.",
        ),
    ]
    return [
        RealReplayExecuteOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status="PASS" if passed else REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else blocker,
            evidence_path=str(output_dir),
            observed_value=str(passed),
        )
        for name, passed, blocker in guards
    ]


def _resolve_status(
    *,
    has_input: bool,
    precondition_results: list[RealReplayExecutePreconditionResult],
    lineage_results: list[RealReplayExecuteLineageResult],
    authority_results: list[RealReplayExecuteAuthorityResult],
    attestation_results: list[RealReplayExecuteAttestationResult],
    pit_source_results: list[RealReplayExecutePitSourceEvidenceResult],
    taxonomy_results: list[RealReplayExecuteTaxonomyResult],
    leakage_side_effect_results: list[RealReplayExecuteLeakageSideEffectResult],
    overclaim_results: list[RealReplayExecuteOverclaimResult],
) -> str:
    if not has_input:
        return NO_REAL_REPLAY_EXECUTION_INPUT
    ordered_groups: list[tuple[list[Any], list[str]]] = [
        (lineage_results, [REAL_REPLAY_EXECUTION_LINEAGE_BLOCKED]),
        (precondition_results, [REAL_REPLAY_EXECUTION_REVIEW_BLOCKED]),
        (authority_results, [REAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED]),
        (attestation_results, [REAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED]),
        (
            pit_source_results,
            [
                REAL_REPLAY_EXECUTION_PIT_BLOCKED,
                REAL_REPLAY_EXECUTION_SOURCE_BLOCKED,
                REAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
            ],
        ),
        (taxonomy_results, [REAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED]),
        (
            leakage_side_effect_results,
            [REAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED, REAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED],
        ),
        (overclaim_results, [REAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED]),
    ]
    for rows, statuses in ordered_groups:
        for status in statuses:
            if any(not row.passed and row.status == status for row in rows):
                return status
    return READY_FOR_REAL_REPLAY_EXECUTION_REVIEW


def _metadata(result: RealReplayExecuteResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    return payload


def _precheck(
    result: RealReplayExecuteResult,
    active_payload: dict[str, Any],
    candidate_payload: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "real_replay_execution_run_id": result.real_replay_execution_run_id,
        "created_at": result.generated_at,
        "execution_status": result.status,
        "ready_for_real_replay_execution_review": result.ready_for_real_replay_execution_review,
        "source_active_input_creation_run_id": result.source_active_input_creation_run_id,
        "source_active_replay_input_artifact_path": result.source_active_replay_input_artifact_path,
        "active_replay_input_created": _to_bool(active_payload.get("active_replay_input_created")),
        "active_replay_input": _to_bool(active_payload.get("active_replay_input")),
        "replay_as_of_date": _text(active_payload.get("replay_as_of_date")),
        "replay_calendar": _text(active_payload.get("replay_calendar")),
        "symbol_universe_ref": _text(active_payload.get("symbol_universe_ref")),
        "pit_universe_ref": _text(active_payload.get("pit_universe_ref")),
        "source_registry_ref": _text(active_payload.get("source_registry_ref")),
        "raw_document_store_ref": _text(active_payload.get("raw_document_store_ref")),
        "factor_definition_ref": _text(active_payload.get("factor_definition_ref")),
        "factor_observation_ref": _text(active_payload.get("factor_observation_ref")),
        "event_structured_ref": _text(active_payload.get("event_structured_ref")),
        "company_exposure_ref": _text(active_payload.get("company_exposure_ref")),
        "evidence_bundle_ref": _text(active_payload.get("evidence_bundle_ref")),
        "source_hash_coverage": _text(active_payload.get("source_hash_coverage")),
        "revision_id_coverage": _text(active_payload.get("revision_id_coverage")),
        "available_time_policy": _text(active_payload.get("available_time_policy")),
        "taxonomy_coverage": _text(active_payload.get("taxonomy_coverage")),
        "future_labels_excluded": _to_bool(candidate_payload.get("future_labels_excluded")) if candidate_payload else True,
        "deterministic_only": _to_bool(candidate_payload.get("deterministic_only")) if candidate_payload else True,
        "replay_decision_artifact_path": "",
        "report_only": True,
        "diagnostic_only": True,
    }
    for field in DOWNSTREAM_FALSE_FIELDS:
        payload[field] = False
    return payload


def _render_report(result: RealReplayExecuteResult) -> str:
    return "\n".join(
        [
            "# Real Replay Execution Precheck Report",
            "",
            f"- real_replay_execution_run_id: `{result.real_replay_execution_run_id}`",
            f"- status: `{result.status}`",
            f"- workflow_stage: `{result.workflow_stage}`",
            f"- ready_for_real_replay_execution_review: `{result.ready_for_real_replay_execution_review}`",
            f"- blocker_count: `{result.blocker_count}`",
            "",
            "This artifact is a report-only pre-execution review package.",
            "",
            "It is not replay execution, not replay decisions, not forward labels, not training, "
            "not stock_profile, not buy-review, not paper approval, not performance validation, "
            "not broker integration, not orders, not messages, and not trading.",
            "",
            "A READY_FOR_REAL_REPLAY_EXECUTION_REVIEW status means only that the supplied package passed "
            "fail-closed precheck gates for future human review. It does not allow actual replay execution.",
        ]
    )


def _render_next_task(result: RealReplayExecuteResult) -> str:
    if result.status == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW:
        return (
            "# Recommended Next Task\n\n"
            "Add Real Replay Execute artifact views report-only v0.1. Implement index, health, and status "
            "without running replay, creating replay decisions, computing labels, training weights, creating "
            "stock_profile artifacts, creating buy-review eligibility, or authorizing trading.\n"
        )
    if result.status == NO_REAL_REPLAY_EXECUTION_INPUT:
        return (
            "# Recommended Next Task\n\n"
            "Provide a governed active replay input artifact and report-only review manifests before rerunning "
            "`real-replay-execute`. Do not run actual replay.\n"
        )
    return (
        "# Recommended Next Task\n\n"
        "Complete the blocked real replay execution precheck evidence gates. Do not run replay, create replay "
        "decisions, compute labels, train weights, create stock profiles, or authorize trading.\n"
    )


def _write_frame(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_run_id(settings: RealReplayExecuteSettings, generated_at: str) -> str:
    payload = {
        "generated_at": generated_at,
        "active_replay_input_artifact_path": _path_str(settings.active_replay_input_artifact_path),
        "candidate_path": _path_str(settings.replay_execution_candidate_manifest_path),
        "output_dir": str(settings.output_dir),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _load_artifact_payload(path: Path | None, metadata_name: str) -> dict[str, Any]:
    if path is None:
        return {}
    if path.is_dir():
        return _read_json(path / metadata_name)
    return _read_json(path)


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
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
    evidence_path: Path | None,
    observed_value: str = "",
) -> RealReplayExecuteLineageResult:
    return RealReplayExecuteLineageResult(
        gate_group="active_replay_input_lineage",
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=_path_str(evidence_path),
        observed_value=observed_value,
    )


def _pit_source(
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: Path | None,
    observed_value: str = "",
) -> RealReplayExecutePitSourceEvidenceResult:
    return RealReplayExecutePitSourceEvidenceResult(
        gate_group="pit_source_evidence",
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=_path_str(evidence_path),
        observed_value=observed_value,
    )


def _leakage(
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: Path | None,
    observed_value: str = "",
) -> RealReplayExecuteLeakageSideEffectResult:
    return RealReplayExecuteLeakageSideEffectResult(
        gate_group="leakage_side_effect",
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=_path_str(evidence_path),
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
        return value.strip().lower() in {"1", "true", "yes", "y", "pass"}
    return False


def _missing_true_fields(payload: dict[str, Any], fields: list[str]) -> str:
    return ",".join(field for field in fields if not _to_bool(payload.get(field)))


def _blocked(rows: list[Any]) -> int:
    return sum(1 for row in rows if not row.passed)


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if "manual_diagnostics" not in path.parts:
        raise ValueError("Real replay execution precheck artifacts must be written under manual_diagnostics.")
