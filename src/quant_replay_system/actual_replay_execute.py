"""Report-only actual replay execution core.

This workflow may freeze report-only input/observation/evidence artifacts after
explicit approval. It never creates replay decisions, computes labels, trains
weights, creates stock profiles, changes buy-review eligibility, calls APIs,
mutates cache, writes data stores, or authorizes trading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACTUAL_REPLAY_EXECUTION_INPUT = "NO_ACTUAL_REPLAY_EXECUTION_INPUT"
ACTUAL_REPLAY_EXECUTION_INPUT_FOUND = "ACTUAL_REPLAY_EXECUTION_INPUT_FOUND"
ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED = "ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED"
ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED = "ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED"
ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED = "ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED"
ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED = "ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED"
ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED = "ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED"
ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED = "ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED"
ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED = "ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED"
ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED = "ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED"
ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED = "ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED"
ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED = "ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED"
ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED = "ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED"
READY_FOR_ACTUAL_REPLAY_EXECUTION = "READY_FOR_ACTUAL_REPLAY_EXECUTION"
ACTUAL_REPLAY_EXECUTED = "ACTUAL_REPLAY_EXECUTED"

ACTIVE_REPLAY_INPUT_CREATED = "ACTIVE_REPLAY_INPUT_CREATED"
READY_FOR_REAL_REPLAY_EXECUTION_REVIEW = "READY_FOR_REAL_REPLAY_EXECUTION_REVIEW"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/actual_replay_execute_v0_1")
EXACT_APPROVAL_TEXT = (
    "I explicitly authorize implementation of actual replay execution core only, "
    "report-only, no replay_decision creation, no forward labels, no training, "
    "no stock_profile, no buy-review, no trading."
)

AUTHORITY_FIELDS = [
    "approval_text",
]
ATTESTATION_TRUE_FIELDS = [
    "second_reviewer_attested",
    "actual_replay_execution_core_attested",
    "report_only_attested",
    "no_replay_decision_creation_attested",
    "no_forward_label_attested",
    "no_training_attested",
    "no_stock_profile_attested",
    "no_buy_review_attested",
    "no_trading_authority_attested",
    "no_performance_claim_attested",
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
]
FACTOR_EVENT_COMPANY_TRUE_FIELDS = [
    "factor_definition_attached",
    "factor_observation_attached",
    "event_structured_attached",
    "company_exposure_attached",
    "all_available_time_lte_replay_decision_time",
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
    "actual_replay_execution_not_replay_decision",
    "actual_replay_execution_not_label_permission",
    "actual_replay_execution_not_training_permission",
    "actual_replay_execution_not_stock_profile_permission",
    "actual_replay_execution_not_buy_review_eligibility",
    "actual_replay_execution_not_paper_approval",
    "actual_replay_execution_not_performance_validation",
    "actual_replay_execution_not_trading_authorization",
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
class ActualReplayExecuteSettings:
    active_replay_input_artifact_path: Path | None = None
    active_input_health_artifact_path: Path | None = None
    active_input_status_artifact_path: Path | None = None
    real_replay_precheck_artifact_path: Path | None = None
    real_replay_precheck_health_artifact_path: Path | None = None
    real_replay_precheck_status_artifact_path: Path | None = None
    actual_replay_execution_plan_path: Path | None = None
    approval_manifest_path: Path | None = None
    actual_replay_execution_request_manifest_path: Path | None = None
    actual_replay_execution_authority_manifest_path: Path | None = None
    second_reviewer_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    factor_event_company_evidence_bundle_path: Path | None = None
    source_hash_revision_available_time_evidence_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    actual_replay_execution_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_actual_replay_execution: bool = False
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActualReplayExecutePreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActualReplayExecuteAuthorityResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteLineageResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteAttestationResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecutePitSourceEvidenceResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteTaxonomyResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteLeakageSideEffectResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteOverclaimResult(ActualReplayExecutePreconditionResult):
    pass


@dataclass(frozen=True)
class ActualReplayExecuteResult:
    actual_replay_execution_run_id: str
    created_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    ready_for_actual_replay_execution: bool
    actual_replay_executed: bool
    precondition_results: list[ActualReplayExecutePreconditionResult]
    authority_results: list[ActualReplayExecuteAuthorityResult]
    lineage_results: list[ActualReplayExecuteLineageResult]
    attestation_results: list[ActualReplayExecuteAttestationResult]
    pit_source_evidence_results: list[ActualReplayExecutePitSourceEvidenceResult]
    taxonomy_results: list[ActualReplayExecuteTaxonomyResult]
    leakage_side_effect_results: list[ActualReplayExecuteLeakageSideEffectResult]
    overclaim_results: list[ActualReplayExecuteOverclaimResult]
    source_active_input_creation_run_id: str
    source_active_replay_input_artifact_path: str
    source_real_replay_precheck_run_id: str
    source_real_replay_precheck_artifact_path: str
    active_replay_input_created: bool
    active_replay_input: bool
    precheck_status: str
    ready_for_real_replay_execution_review: bool
    replay_as_of_date: str
    replay_calendar: str
    symbol_universe_ref: str
    pit_universe_ref: str
    source_registry_ref: str
    raw_document_store_ref: str
    factor_definition_ref: str
    factor_observation_ref: str
    event_structured_ref: str
    company_exposure_ref: str
    evidence_bundle_ref: str
    source_hash_coverage: str
    revision_id_coverage: str
    available_time_policy: str
    taxonomy_coverage: str
    future_labels_excluded: bool
    deterministic_only: bool
    replay_execution_started: bool
    replay_execution_completed: bool
    replay_decisions_created: bool
    replay_decisions_exist: bool
    replay_decision_artifact_path: str
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
    blocker_count: int
    issue_count: int
    warning_count: int
    artifact_paths: dict[str, Path]


def run_actual_replay_execute(settings: ActualReplayExecuteSettings | None = None) -> ActualReplayExecuteResult:
    settings = settings or ActualReplayExecuteSettings()
    _ensure_manual_diagnostics_path(settings.output_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    run_id = _build_run_id(settings, created_at)
    artifact_path = settings.output_dir / run_id
    has_input = any(
        getattr(settings, field) is not None
        for field in [
            "active_replay_input_artifact_path",
            "active_input_health_artifact_path",
            "active_input_status_artifact_path",
            "real_replay_precheck_artifact_path",
            "approval_manifest_path",
            "actual_replay_execution_candidate_manifest_path",
        ]
    )

    active_payload = _read_json(settings.active_replay_input_artifact_path)
    active_health = _read_json(settings.active_input_health_artifact_path)
    active_status = _read_json(settings.active_input_status_artifact_path)
    precheck_payload = _read_json(settings.real_replay_precheck_artifact_path)
    precheck_health = _read_json(settings.real_replay_precheck_health_artifact_path)
    precheck_status = _read_json(settings.real_replay_precheck_status_artifact_path)
    approval_payload = _read_json(settings.approval_manifest_path)
    request_payload = _read_json(settings.actual_replay_execution_request_manifest_path)
    authority_payload = _read_json(settings.actual_replay_execution_authority_manifest_path)
    attestation_payload = _read_json(settings.second_reviewer_attestation_manifest_path)
    pit_payload = _read_json(settings.pit_source_evidence_bundle_path)
    taxonomy_payload = _read_json(settings.taxonomy_evidence_bundle_path)
    factor_payload = _read_json(settings.factor_event_company_evidence_bundle_path)
    source_hash_payload = _read_json(settings.source_hash_revision_available_time_evidence_path)
    leakage_payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    overclaim_payload = _read_json(settings.overclaim_evidence_bundle_path)
    candidate_payload = _read_json(settings.actual_replay_execution_candidate_manifest_path)

    precondition_results = [
        ActualReplayExecutePreconditionResult(
            "actual_replay_execution_input",
            "input_present",
            ACTUAL_REPLAY_EXECUTION_INPUT_FOUND if has_input else NO_ACTUAL_REPLAY_EXECUTION_INPUT,
            has_input,
            "" if has_input else "No actual replay execution input was supplied.",
            "",
            str(has_input),
        )
    ]
    precondition_results.extend(_check_file(settings.actual_replay_execution_plan_path, "actual_replay_execution_plan"))
    precondition_results.extend(_check_request(settings, request_payload))
    precondition_results.extend(_check_candidate(settings, candidate_payload))

    lineage_results = _check_lineage(settings, active_payload, active_health, active_status, precheck_payload, precheck_health, precheck_status)
    authority_results = _check_authority(settings, approval_payload, authority_payload)
    attestation_results = _check_attestation(settings, attestation_payload)
    pit_results = _check_pit_source(settings, pit_payload)
    pit_results.extend(_check_factor_event_company(settings, factor_payload))
    pit_results.extend(_check_source_hash(settings, source_hash_payload))
    taxonomy_results = _check_taxonomy(settings, taxonomy_payload)
    leakage_results = _check_leakage_side_effect(settings, leakage_payload)
    payloads = [p for p in [active_payload, precheck_payload, request_payload, candidate_payload, leakage_payload] if p]
    leakage_results.extend(_check_false_fields(payloads, LEAKAGE_FALSE_FIELDS, ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED, "leakage_false_field_guard"))
    leakage_results.extend(_check_false_fields(payloads, SIDE_EFFECT_FALSE_FIELDS, ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED, "side_effect_false_field_guard"))
    overclaim_results = _check_overclaim(settings, overclaim_payload)
    overclaim_results.extend(_check_overclaim_false_fields(payloads))
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    status = _resolve_status(
        has_input,
        precondition_results,
        lineage_results,
        authority_results,
        attestation_results,
        pit_results,
        taxonomy_results,
        leakage_results,
        overclaim_results,
    )
    ready = status == READY_FOR_ACTUAL_REPLAY_EXECUTION
    executed = ready and settings.allow_actual_replay_execution
    if executed:
        status = ACTUAL_REPLAY_EXECUTED
    workflow_stage = "ACTUAL_REPLAY_EXECUTION_NO_INPUT" if status == NO_ACTUAL_REPLAY_EXECUTION_INPUT else status
    blockers = sum(
        _blocked(rows)
        for rows in [
            precondition_results,
            lineage_results,
            authority_results,
            attestation_results,
            pit_results,
            taxonomy_results,
            leakage_results,
            overclaim_results,
        ]
    )
    source_active_input_creation_run_id = _text(
        active_payload.get("active_input_creation_run_id") or candidate_payload.get("source_active_input_creation_run_id")
    )
    source_precheck_run_id = _text(
        precheck_payload.get("real_replay_execution_run_id") or candidate_payload.get("source_real_replay_precheck_run_id")
    )
    result = ActualReplayExecuteResult(
        actual_replay_execution_run_id=run_id,
        created_at=created_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=workflow_stage,
        ready_for_actual_replay_execution=ready or executed,
        actual_replay_executed=executed,
        precondition_results=precondition_results,
        authority_results=authority_results,
        lineage_results=lineage_results,
        attestation_results=attestation_results,
        pit_source_evidence_results=pit_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_results,
        overclaim_results=overclaim_results,
        source_active_input_creation_run_id=source_active_input_creation_run_id,
        source_active_replay_input_artifact_path=_text(
            candidate_payload.get("source_active_replay_input_artifact_path") or settings.active_replay_input_artifact_path
        ),
        source_real_replay_precheck_run_id=source_precheck_run_id,
        source_real_replay_precheck_artifact_path=_text(
            candidate_payload.get("source_real_replay_precheck_artifact_path") or settings.real_replay_precheck_artifact_path
        ),
        active_replay_input_created=_to_bool(active_payload.get("active_replay_input_created")),
        active_replay_input=_to_bool(active_payload.get("active_replay_input")),
        precheck_status=_text(precheck_payload.get("execution_status") or precheck_status.get("status")),
        ready_for_real_replay_execution_review=_to_bool(precheck_payload.get("ready_for_real_replay_execution_review")),
        replay_as_of_date=_text(active_payload.get("replay_as_of_date")),
        replay_calendar=_text(active_payload.get("replay_calendar")),
        symbol_universe_ref=_text(active_payload.get("symbol_universe_ref")),
        pit_universe_ref=_text(active_payload.get("pit_universe_ref")),
        source_registry_ref=_text(active_payload.get("source_registry_ref")),
        raw_document_store_ref=_text(active_payload.get("raw_document_store_ref")),
        factor_definition_ref=_text(active_payload.get("factor_definition_ref")),
        factor_observation_ref=_text(active_payload.get("factor_observation_ref")),
        event_structured_ref=_text(active_payload.get("event_structured_ref")),
        company_exposure_ref=_text(active_payload.get("company_exposure_ref")),
        evidence_bundle_ref=_text(active_payload.get("evidence_bundle_ref")),
        source_hash_coverage=_text(active_payload.get("source_hash_coverage")),
        revision_id_coverage=_text(active_payload.get("revision_id_coverage")),
        available_time_policy=_text(active_payload.get("available_time_policy")),
        taxonomy_coverage=_text(active_payload.get("taxonomy_coverage")),
        future_labels_excluded=_to_bool(candidate_payload.get("future_labels_excluded")) if candidate_payload else True,
        deterministic_only=_to_bool(candidate_payload.get("deterministic_only")),
        replay_execution_started=executed,
        replay_execution_completed=executed,
        replay_decisions_created=False,
        replay_decisions_exist=False,
        replay_decision_artifact_path="",
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
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        artifact_paths=_artifact_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_actual_replay_execute_artifacts(result, active_payload, precheck_payload, approval_payload)
    return result


def write_actual_replay_execute_artifacts(
    result: ActualReplayExecuteResult,
    active_payload: dict[str, Any],
    precheck_payload: dict[str, Any],
    approval_payload: dict[str, Any],
) -> None:
    for key, path in result.artifact_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_json(result.artifact_paths["input_snapshot"], _input_snapshot(result, active_payload, precheck_payload, approval_payload))
    _write_json(result.artifact_paths["safety_flags"], _safety_flags(result))
    pd.DataFrame([_observation_row(result)]).to_csv(result.artifact_paths["observation_snapshot"], index=False)
    pd.DataFrame(_evidence_rows(result)).to_csv(result.artifact_paths["evidence_bundle_index"], index=False)
    _write_frame(result.artifact_paths["precondition_results"], result.precondition_results)
    _write_frame(result.artifact_paths["authority_results"], result.authority_results)
    _write_frame(result.artifact_paths["lineage_results"], result.lineage_results)
    _write_frame(result.artifact_paths["attestation_results"], result.attestation_results)
    _write_frame(result.artifact_paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_frame(result.artifact_paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_frame(result.artifact_paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_frame(result.artifact_paths["overclaim_guard_results"], result.overclaim_results)
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _artifact_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "actual_replay_execution_metadata.json",
        "report": artifact_path / "actual_replay_execution_report.md",
        "input_snapshot": artifact_path / "actual_replay_execution_input_snapshot.json",
        "observation_snapshot": artifact_path / "actual_replay_observation_snapshot.csv",
        "evidence_bundle_index": artifact_path / "actual_replay_evidence_bundle_index.csv",
        "safety_flags": artifact_path / "actual_replay_safety_flags.json",
        "precondition_results": artifact_path / "actual_replay_precondition_results.csv",
        "authority_results": artifact_path / "actual_replay_authority_results.csv",
        "lineage_results": artifact_path / "actual_replay_lineage_results.csv",
        "attestation_results": artifact_path / "actual_replay_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def _check_lineage(
    settings: ActualReplayExecuteSettings,
    active: dict[str, Any],
    active_health: dict[str, Any],
    active_status: dict[str, Any],
    precheck: dict[str, Any],
    precheck_health: dict[str, Any],
    precheck_status: dict[str, Any],
) -> list[ActualReplayExecuteLineageResult]:
    rows = [
        _lineage("active_replay_input_json_exists", _path_exists(settings.active_replay_input_artifact_path), settings.active_replay_input_artifact_path, "Active replay input artifact is missing."),
        _lineage(
            "active_input_status_created",
            _path_exists(settings.active_input_status_artifact_path)
            and _text(active.get("input_status")) == ACTIVE_REPLAY_INPUT_CREATED
            and _text(active_status.get("status")) == ACTIVE_REPLAY_INPUT_CREATED,
            settings.active_input_status_artifact_path,
            "Active input status is not ACTIVE_REPLAY_INPUT_CREATED.",
        ),
        _lineage("active_replay_input_created", _to_bool(active.get("active_replay_input_created")), settings.active_replay_input_artifact_path, "active_replay_input_created must be true."),
        _lineage("active_replay_input", _to_bool(active.get("active_replay_input")), settings.active_replay_input_artifact_path, "active_replay_input must be true."),
        _lineage("active_input_health_pass", _text(active_health.get("health_status")) == "PASS", settings.active_input_health_artifact_path, "Active input health is not PASS."),
        _lineage("real_replay_precheck_exists", _path_exists(settings.real_replay_precheck_artifact_path), settings.real_replay_precheck_artifact_path, "v1.41 precheck artifact is missing."),
        _lineage(
            "real_replay_precheck_review_ready",
            _path_exists(settings.real_replay_precheck_status_artifact_path)
            and _text(precheck.get("execution_status")) == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW
            and _text(precheck_status.get("status")) == READY_FOR_REAL_REPLAY_EXECUTION_REVIEW,
            settings.real_replay_precheck_artifact_path,
            "v1.41 precheck is not review-ready.",
        ),
        _lineage("ready_for_real_replay_execution_review", _to_bool(precheck.get("ready_for_real_replay_execution_review")), settings.real_replay_precheck_artifact_path, "ready_for_real_replay_execution_review must be true."),
        _lineage("real_replay_precheck_health_pass", _text(precheck_health.get("health_status")) == "PASS", settings.real_replay_precheck_health_artifact_path, "v1.41 precheck health is not PASS."),
    ]
    return rows


def _check_file(path: Path | None, gate_name: str) -> list[ActualReplayExecutePreconditionResult]:
    passed = _path_exists(path)
    return [ActualReplayExecutePreconditionResult("actual_replay_execution_review", gate_name, "PASS" if passed else ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED, passed, "" if passed else f"{gate_name} is missing.", _path_str(path))]


def _check_request(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecutePreconditionResult]:
    exists = _path_exists(settings.actual_replay_execution_request_manifest_path)
    passed = exists and _to_bool(payload.get("actual_replay_execution_core_requested")) and _to_bool(payload.get("report_only"))
    return [ActualReplayExecutePreconditionResult("actual_replay_execution_review", "actual_replay_execution_request", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED, passed, "" if passed else "Actual replay execution request is incomplete.", _path_str(settings.actual_replay_execution_request_manifest_path))]


def _check_candidate(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecutePreconditionResult]:
    exists = _path_exists(settings.actual_replay_execution_candidate_manifest_path)
    passed = exists and _to_bool(payload.get("deterministic_only")) and _to_bool(payload.get("future_labels_excluded")) and not _text(payload.get("replay_decision_artifact_path"))
    return [ActualReplayExecutePreconditionResult("actual_replay_execution_review", "actual_replay_execution_candidate_manifest", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED, passed, "" if passed else "Actual replay execution candidate manifest is incomplete.", _path_str(settings.actual_replay_execution_candidate_manifest_path))]


def _check_authority(settings: ActualReplayExecuteSettings, approval: dict[str, Any], authority: dict[str, Any]) -> list[ActualReplayExecuteAuthorityResult]:
    text = _text(approval.get("approval_text"))
    exact = _normalize(text) == _normalize(EXACT_APPROVAL_TEXT)
    forbidden = any(token in text.lower() for token in ["replay_decision creation.", "labels and training", "trading."]) and not exact
    authority_ok = _text(authority.get("authority_result")) == "ACCEPTED_FOR_ACTUAL_REPLAY_EXECUTION_CORE_ONLY"
    rows = [
        ActualReplayExecuteAuthorityResult("authority", "exact_approval_wording", "PASS" if exact and not forbidden else ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED, exact and not forbidden, "" if exact and not forbidden else "Exact narrow approval wording is missing or invalid.", _path_str(settings.approval_manifest_path), text),
        ActualReplayExecuteAuthorityResult("authority", "actual_replay_execution_authority", "PASS" if _path_exists(settings.actual_replay_execution_authority_manifest_path) and authority_ok else ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED, _path_exists(settings.actual_replay_execution_authority_manifest_path) and authority_ok, "" if authority_ok else "Actual replay execution authority is missing or invalid.", _path_str(settings.actual_replay_execution_authority_manifest_path), _text(authority.get("authority_result"))),
    ]
    return rows


def _check_attestation(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecuteAttestationResult]:
    exists = _path_exists(settings.second_reviewer_attestation_manifest_path)
    missing = _missing_true_fields(payload, ATTESTATION_TRUE_FIELDS)
    passed = exists and not missing
    return [ActualReplayExecuteAttestationResult("attestation", "second_reviewer_attestation", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED, passed, "" if passed else "Second reviewer attestation is incomplete.", _path_str(settings.second_reviewer_attestation_manifest_path), missing if exists else "missing_bundle")]


def _check_pit_source(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecutePitSourceEvidenceResult]:
    exists = _path_exists(settings.pit_source_evidence_bundle_path)
    if not exists:
        return [
            ActualReplayExecutePitSourceEvidenceResult(
                "pit_source_evidence",
                "pit_source_evidence_bundle",
                ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED,
                False,
                "PIT/source/evidence bundle is missing.",
                _path_str(settings.pit_source_evidence_bundle_path),
                "missing_bundle",
            )
        ]
    return [
        _pit_source("accepted_pit_universe_evidence", exists and not _missing_true_fields(payload, PIT_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED, "Accepted PIT universe evidence is missing."),
        _pit_source("source_registry_evidence", exists and not _missing_true_fields(payload, SOURCE_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED, "Source registry evidence is missing."),
        _pit_source("raw_document_and_evidence_bundle", exists and not _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED, "Raw document or evidence bundle evidence is missing."),
    ]


def _check_taxonomy(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecuteTaxonomyResult]:
    exists = _path_exists(settings.taxonomy_evidence_bundle_path)
    missing = _missing_true_fields(payload, TAXONOMY_TRUE_FIELDS)
    passed = exists and not missing
    return [ActualReplayExecuteTaxonomyResult("taxonomy_evidence", "eight_layer_taxonomy_evidence", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED, passed, "" if passed else "8-layer taxonomy evidence is incomplete.", _path_str(settings.taxonomy_evidence_bundle_path), missing if exists else "missing_bundle")]


def _check_factor_event_company(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecutePitSourceEvidenceResult]:
    exists = _path_exists(settings.factor_event_company_evidence_bundle_path)
    missing = _missing_true_fields(payload, FACTOR_EVENT_COMPANY_TRUE_FIELDS)
    passed = exists and not missing
    return [ActualReplayExecutePitSourceEvidenceResult("pit_source_evidence", "factor_event_company_pit_evidence", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED, passed, "" if passed else "Factor, event, or company exposure PIT evidence is incomplete.", _path_str(settings.factor_event_company_evidence_bundle_path), missing if exists else "missing_bundle")]


def _check_source_hash(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecutePitSourceEvidenceResult]:
    exists = _path_exists(settings.source_hash_revision_available_time_evidence_path)
    missing = _missing_true_fields(payload, SOURCE_HASH_TRUE_FIELDS)
    policy_ok = _text(payload.get("available_time_policy")) == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    passed = exists and not missing and policy_ok
    return [ActualReplayExecutePitSourceEvidenceResult("pit_source_evidence", "source_hash_revision_available_time", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED, passed, "" if passed else "Source hash, revision_id, or available_time evidence is incomplete.", _path_str(settings.source_hash_revision_available_time_evidence_path), missing if exists else "missing_bundle")]


def _check_leakage_side_effect(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecuteLeakageSideEffectResult]:
    exists = _path_exists(settings.leakage_side_effect_evidence_bundle_path)
    leakage_missing = _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS)
    side_missing = _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS)
    return [
        ActualReplayExecuteLeakageSideEffectResult("leakage_side_effect", "leakage_exclusion_checks", "PASS" if exists and not leakage_missing else ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED, exists and not leakage_missing, "" if exists and not leakage_missing else "Leakage exclusion evidence is incomplete.", _path_str(settings.leakage_side_effect_evidence_bundle_path), leakage_missing if exists else "missing_bundle"),
        ActualReplayExecuteLeakageSideEffectResult("leakage_side_effect", "side_effect_exclusion_checks", "PASS" if exists and not side_missing else ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED, exists and not side_missing, "" if exists and not side_missing else "Side-effect exclusion evidence is incomplete.", _path_str(settings.leakage_side_effect_evidence_bundle_path), side_missing if exists else "missing_bundle"),
    ]


def _check_overclaim(settings: ActualReplayExecuteSettings, payload: dict[str, Any]) -> list[ActualReplayExecuteOverclaimResult]:
    exists = _path_exists(settings.overclaim_evidence_bundle_path)
    missing = _missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS)
    passed = exists and not missing
    return [ActualReplayExecuteOverclaimResult("overclaim_guard", "actual_replay_execution_boundary_guards", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED, passed, "" if passed else "Overclaim guard evidence is incomplete.", _path_str(settings.overclaim_evidence_bundle_path), missing if exists else "missing_bundle")]


def _pit_source(gate_name: str, passed: bool, path: Path | None, fail_status: str, blocker: str) -> ActualReplayExecutePitSourceEvidenceResult:
    return ActualReplayExecutePitSourceEvidenceResult("pit_source_evidence", gate_name, "PASS" if passed else fail_status, passed, "" if passed else blocker, _path_str(path))


def _lineage(gate_name: str, passed: bool, path: Path | None, blocker: str) -> ActualReplayExecuteLineageResult:
    return ActualReplayExecuteLineageResult("lineage", gate_name, "PASS" if passed else ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED, passed, "" if passed else blocker, _path_str(path), str(passed))


def _check_false_fields(payloads: list[dict[str, Any]], fields: list[str], failure_status: str, gate_group: str) -> list[ActualReplayExecuteLeakageSideEffectResult]:
    rows: list[ActualReplayExecuteLeakageSideEffectResult] = []
    for field in fields:
        passed = not any(_to_bool(payload.get(field)) for payload in payloads)
        rows.append(ActualReplayExecuteLeakageSideEffectResult(gate_group, field, "PASS" if passed else failure_status, passed, "" if passed else f"{field} must remain false.", "input_payloads", str(not passed)))
    return rows


def _check_overclaim_false_fields(payloads: list[dict[str, Any]]) -> list[ActualReplayExecuteOverclaimResult]:
    rows: list[ActualReplayExecuteOverclaimResult] = []
    for field in OVERCLAIM_FALSE_FIELDS:
        passed = not any(_to_bool(payload.get(field)) for payload in payloads)
        rows.append(ActualReplayExecuteOverclaimResult("overclaim_false_field_guard", field, "PASS" if passed else ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED, passed, "" if passed else f"{field} must remain false.", "input_payloads", str(not passed)))
    return rows


def _built_in_overclaim_guards(output_dir: Path) -> list[ActualReplayExecuteOverclaimResult]:
    passed = "manual_diagnostics" in output_dir.parts
    return [ActualReplayExecuteOverclaimResult("built_in_overclaim_guard", "output_path_under_manual_diagnostics", "PASS" if passed else ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED, passed, "" if passed else "Output path must remain under manual_diagnostics.", str(output_dir), str(passed))]


def _resolve_status(
    has_input: bool,
    precondition_results: list[ActualReplayExecutePreconditionResult],
    lineage_results: list[ActualReplayExecuteLineageResult],
    authority_results: list[ActualReplayExecuteAuthorityResult],
    attestation_results: list[ActualReplayExecuteAttestationResult],
    pit_results: list[ActualReplayExecutePitSourceEvidenceResult],
    taxonomy_results: list[ActualReplayExecuteTaxonomyResult],
    leakage_results: list[ActualReplayExecuteLeakageSideEffectResult],
    overclaim_results: list[ActualReplayExecuteOverclaimResult],
) -> str:
    if not has_input:
        return NO_ACTUAL_REPLAY_EXECUTION_INPUT
    ordered = [
        (lineage_results, [ACTUAL_REPLAY_EXECUTION_LINEAGE_BLOCKED]),
        (precondition_results, [ACTUAL_REPLAY_EXECUTION_REVIEW_BLOCKED]),
        (authority_results, [ACTUAL_REPLAY_EXECUTION_AUTHORITY_BLOCKED]),
        (attestation_results, [ACTUAL_REPLAY_EXECUTION_ATTESTATION_BLOCKED]),
        (pit_results, [ACTUAL_REPLAY_EXECUTION_PIT_BLOCKED, ACTUAL_REPLAY_EXECUTION_SOURCE_BLOCKED, ACTUAL_REPLAY_EXECUTION_EVIDENCE_BLOCKED]),
        (taxonomy_results, [ACTUAL_REPLAY_EXECUTION_TAXONOMY_BLOCKED]),
        (leakage_results, [ACTUAL_REPLAY_EXECUTION_LEAKAGE_BLOCKED, ACTUAL_REPLAY_EXECUTION_SIDE_EFFECT_BLOCKED]),
        (overclaim_results, [ACTUAL_REPLAY_EXECUTION_OVERCLAIM_BLOCKED]),
    ]
    for rows, statuses in ordered:
        for status in statuses:
            if any(not row.passed and row.status == status for row in rows):
                return status
    return READY_FOR_ACTUAL_REPLAY_EXECUTION


def _metadata(result: ActualReplayExecuteResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    payload["execution_status"] = result.status
    return payload


def _input_snapshot(result: ActualReplayExecuteResult, active: dict[str, Any], precheck: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_active_input_creation_run_id": result.source_active_input_creation_run_id,
        "source_active_replay_input_artifact_path": result.source_active_replay_input_artifact_path,
        "source_real_replay_precheck_run_id": result.source_real_replay_precheck_run_id,
        "source_real_replay_precheck_artifact_path": result.source_real_replay_precheck_artifact_path,
        "replay_as_of_date": result.replay_as_of_date,
        "replay_calendar": result.replay_calendar,
        "symbol_universe_ref": result.symbol_universe_ref,
        "pit_universe_ref": result.pit_universe_ref,
        "source_registry_ref": result.source_registry_ref,
        "raw_document_store_ref": result.raw_document_store_ref,
        "factor_definition_ref": result.factor_definition_ref,
        "factor_observation_ref": result.factor_observation_ref,
        "event_structured_ref": result.event_structured_ref,
        "company_exposure_ref": result.company_exposure_ref,
        "evidence_bundle_ref": result.evidence_bundle_ref,
        "source_hash_coverage": result.source_hash_coverage,
        "revision_id_coverage": result.revision_id_coverage,
        "available_time_policy": result.available_time_policy,
        "taxonomy_coverage": result.taxonomy_coverage,
        "approval_text": _text(approval.get("approval_text")),
        "explicit_approval_validation_result": "PASS" if _normalize(_text(approval.get("approval_text"))) == _normalize(EXACT_APPROVAL_TEXT) else "FAIL",
        "active_input_lineage_fields": sorted(active.keys()),
        "precheck_lineage_fields": sorted(precheck.keys()),
    }


def _safety_flags(result: ActualReplayExecuteResult) -> dict[str, Any]:
    return {field: getattr(result, field) for field in ["actual_replay_executed", "replay_execution_started", "replay_execution_completed"] + DOWNSTREAM_FALSE_FIELDS}


def _observation_row(result: ActualReplayExecuteResult) -> dict[str, Any]:
    return {
        "actual_replay_execution_run_id": result.actual_replay_execution_run_id,
        "signal_date": result.replay_as_of_date,
        "observation_type": "PIT_INPUT_CONTEXT",
        "source_hash": result.source_hash_coverage,
        "revision_id": result.revision_id_coverage,
        "available_time": result.available_time_policy,
        "taxonomy_coverage": result.taxonomy_coverage,
        "pit_status": "PIT_CONTEXT_REVIEWED",
    }


def _evidence_rows(result: ActualReplayExecuteResult) -> list[dict[str, Any]]:
    refs = [
        ("symbol_universe_ref", result.symbol_universe_ref),
        ("pit_universe_ref", result.pit_universe_ref),
        ("source_registry_ref", result.source_registry_ref),
        ("raw_document_store_ref", result.raw_document_store_ref),
        ("factor_definition_ref", result.factor_definition_ref),
        ("factor_observation_ref", result.factor_observation_ref),
        ("event_structured_ref", result.event_structured_ref),
        ("company_exposure_ref", result.company_exposure_ref),
        ("evidence_bundle_ref", result.evidence_bundle_ref),
    ]
    return [
        {
            "evidence_ref_type": name,
            "artifact_ref": value,
            "source_hash": result.source_hash_coverage,
            "revision_id": result.revision_id_coverage,
            "available_time": result.available_time_policy,
            "quality_status": "PASS" if value else "MISSING",
            "taxonomy_coverage": result.taxonomy_coverage,
            "pit_status": "PIT_VALIDATED_CONTEXT" if value else "MISSING",
        }
        for name, value in refs
    ]


def _render_report(result: ActualReplayExecuteResult) -> str:
    return "\n".join(
        [
            "# Actual Replay Execution Core Report",
            "",
            f"- actual_replay_execution_run_id: `{result.actual_replay_execution_run_id}`",
            f"- status: `{result.status}`",
            f"- workflow_stage: `{result.workflow_stage}`",
            f"- ready_for_actual_replay_execution: `{result.ready_for_actual_replay_execution}`",
            f"- actual_replay_executed: `{result.actual_replay_executed}`",
            "",
            "This is report-only actual replay execution core.",
            "",
            "It is not replay_decision creation, not forward labels, not training, not stock_profile, "
            "not buy-review, not paper approval, not performance validation, not broker integration, "
            "not orders, not messages, and not trading.",
        ]
    )


def _render_next_task(result: ActualReplayExecuteResult) -> str:
    if result.status == ACTUAL_REPLAY_EXECUTED:
        return "# Recommended Next Task\n\nAdd Actual Replay Execution Artifact Views Report-Only v0.1.\n"
    if result.status == READY_FOR_ACTUAL_REPLAY_EXECUTION:
        return "# Recommended Next Task\n\nRerun with --allow-actual-replay-execution only if execution is explicitly desired.\n"
    return "# Recommended Next Task\n\nResolve actual replay execution blockers before execution.\n"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_frame(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


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


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _build_run_id(settings: ActualReplayExecuteSettings, created_at: str) -> str:
    payload = {
        "created_at": created_at,
        "active_replay_input_artifact_path": _path_str(settings.active_replay_input_artifact_path),
        "precheck_path": _path_str(settings.real_replay_precheck_artifact_path),
        "candidate_path": _path_str(settings.actual_replay_execution_candidate_manifest_path),
        "allow": settings.allow_actual_replay_execution,
        "output_dir": str(settings.output_dir),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if "manual_diagnostics" not in path.parts:
        raise ValueError("Actual replay execution artifacts must be written under manual_diagnostics.")
