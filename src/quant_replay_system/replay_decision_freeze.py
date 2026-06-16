"""Report-only replay decision freeze core.

This workflow may freeze decision-time replay decision rows after explicit
approval and healthy ACTUAL_REPLAY_EXECUTED lineage. It never computes forward
labels, trains weights, creates stock profiles, creates buy-review eligibility,
calls broker/order/message/API systems, mutates cache, writes data stores, or
authorizes trading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_REPLAY_DECISION_FREEZE_INPUT = "NO_REPLAY_DECISION_FREEZE_INPUT"
REPLAY_DECISION_FREEZE_INPUT_FOUND = "REPLAY_DECISION_FREEZE_INPUT_FOUND"
REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED = "REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED"
REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED = "REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED"
REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED = "REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED"
REPLAY_DECISION_FREEZE_PIT_BLOCKED = "REPLAY_DECISION_FREEZE_PIT_BLOCKED"
REPLAY_DECISION_FREEZE_SOURCE_BLOCKED = "REPLAY_DECISION_FREEZE_SOURCE_BLOCKED"
REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED = "REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED"
REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED = "REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED"
REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED = "REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED"
REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED = "REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED"
REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED = "REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED"
REPLAY_DECISION_FREEZE_REVIEW_BLOCKED = "REPLAY_DECISION_FREEZE_REVIEW_BLOCKED"
READY_FOR_REPLAY_DECISION_FREEZE = "READY_FOR_REPLAY_DECISION_FREEZE"
REPLAY_DECISION_FROZEN = "REPLAY_DECISION_FROZEN"

ACTUAL_REPLAY_EXECUTED = "ACTUAL_REPLAY_EXECUTED"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/replay_decision_freeze_v0_1")
EXACT_APPROVAL_TEXT = (
    "I explicitly authorize implementation of replay decision freeze core only, "
    "report-only, no forward labels, no training, no stock_profile, no buy-review, no trading."
)
ALLOWED_DECISION_LABELS = {
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
}

ATTESTATION_TRUE_FIELDS = [
    "second_reviewer_attested",
    "replay_decision_freeze_core_attested",
    "report_only_attested",
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
    "replay_decision_not_forward_label_permission",
    "replay_decision_not_training_permission",
    "replay_decision_not_stock_profile_permission",
    "replay_decision_not_buy_review_eligibility",
    "replay_decision_not_paper_approval",
    "replay_decision_not_performance_validation",
    "replay_decision_not_trading_authorization",
]
LEAKAGE_FALSE_FIELDS = [
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "forward_returns_exist",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
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
SAFETY_FALSE_FIELDS = [
    "replay_decision_freeze_executed",
    "replay_decision_frozen",
    "replay_decision_artifacts_created",
    "replay_decisions_created",
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_return_labels_created",
    "training_allowed",
    "weights_trained",
    "training_result_created",
    "stock_profile_allowed",
    "active_stock_profile_exists",
    "stock_profile_created",
    "buy_review_allowed",
    "real_buy_review_eligible",
    "approved_for_paper",
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
    "signal_semantics_changed",
]


@dataclass(frozen=True)
class ReplayDecisionFreezeSettings:
    actual_replay_execution_artifact_path: Path | None = None
    actual_replay_execution_health_artifact_path: Path | None = None
    actual_replay_execution_status_artifact_path: Path | None = None
    replay_decision_freeze_plan_path: Path | None = None
    approval_manifest_path: Path | None = None
    replay_decision_freeze_request_manifest_path: Path | None = None
    replay_decision_freeze_authority_manifest_path: Path | None = None
    second_reviewer_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    factor_event_company_evidence_bundle_path: Path | None = None
    source_hash_revision_available_time_evidence_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    replay_decision_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_replay_decision_freeze: bool = False
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ReplayDecisionFreezePreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ReplayDecisionFreezeAuthorityResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeLineageResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeAttestationResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezePitSourceEvidenceResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeTaxonomyResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeLeakageSideEffectResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeOverclaimResult(ReplayDecisionFreezePreconditionResult):
    pass


@dataclass(frozen=True)
class ReplayDecisionFreezeResult:
    replay_decision_freeze_run_id: str
    created_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    ready_for_replay_decision_freeze: bool
    replay_decision_freeze_executed: bool
    replay_decision_frozen: bool
    replay_decision_artifacts_created: bool
    precondition_results: list[ReplayDecisionFreezePreconditionResult]
    authority_results: list[ReplayDecisionFreezeAuthorityResult]
    lineage_results: list[ReplayDecisionFreezeLineageResult]
    attestation_results: list[ReplayDecisionFreezeAttestationResult]
    pit_source_evidence_results: list[ReplayDecisionFreezePitSourceEvidenceResult]
    taxonomy_results: list[ReplayDecisionFreezeTaxonomyResult]
    leakage_side_effect_results: list[ReplayDecisionFreezeLeakageSideEffectResult]
    overclaim_results: list[ReplayDecisionFreezeOverclaimResult]
    source_actual_replay_execution_run_id: str
    source_actual_replay_execution_artifact_path: str
    source_active_input_creation_run_id: str
    source_real_replay_precheck_run_id: str
    actual_replay_execution_status: str
    actual_replay_execution_health_status: str
    actual_replay_executed: bool
    replay_execution_started: bool
    replay_execution_completed: bool
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
    replay_decisions_created: bool
    replay_decisions_exist: bool
    replay_decision_artifact_path: str
    forward_labels_allowed: bool
    forward_labels_exist: bool
    forward_return_labels_created: bool
    training_allowed: bool
    weights_trained: bool
    training_result_created: bool
    stock_profile_allowed: bool
    active_stock_profile_exists: bool
    stock_profile_created: bool
    buy_review_allowed: bool
    real_buy_review_eligible: bool
    approved_for_paper: bool
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
    signal_semantics_changed: bool
    report_only: bool
    diagnostic_only: bool
    blocker_count: int
    issue_count: int
    warning_count: int
    artifact_paths: dict[str, Path]


def run_replay_decision_freeze(
    settings: ReplayDecisionFreezeSettings | None = None,
) -> ReplayDecisionFreezeResult:
    settings = settings or ReplayDecisionFreezeSettings()
    _ensure_manual_diagnostics_path(settings.output_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    run_id = _build_run_id(settings, created_at)
    artifact_path = settings.output_dir / run_id
    has_input = any(
        getattr(settings, field) is not None
        for field in [
            "actual_replay_execution_artifact_path",
            "actual_replay_execution_health_artifact_path",
            "actual_replay_execution_status_artifact_path",
            "approval_manifest_path",
            "replay_decision_candidate_manifest_path",
        ]
    )

    actual_payload = _read_json(settings.actual_replay_execution_artifact_path)
    actual_health = _read_json(settings.actual_replay_execution_health_artifact_path)
    actual_status = _read_json(settings.actual_replay_execution_status_artifact_path)
    approval_payload = _read_json(settings.approval_manifest_path)
    request_payload = _read_json(settings.replay_decision_freeze_request_manifest_path)
    authority_payload = _read_json(settings.replay_decision_freeze_authority_manifest_path)
    attestation_payload = _read_json(settings.second_reviewer_attestation_manifest_path)
    pit_payload = _read_json(settings.pit_source_evidence_bundle_path)
    taxonomy_payload = _read_json(settings.taxonomy_evidence_bundle_path)
    factor_payload = _read_json(settings.factor_event_company_evidence_bundle_path)
    source_hash_payload = _read_json(settings.source_hash_revision_available_time_evidence_path)
    leakage_payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    overclaim_payload = _read_json(settings.overclaim_evidence_bundle_path)
    candidate_payload = _read_json(settings.replay_decision_candidate_manifest_path)

    precondition_results = [
        ReplayDecisionFreezePreconditionResult(
            "replay_decision_freeze_input",
            "input_present",
            REPLAY_DECISION_FREEZE_INPUT_FOUND if has_input else NO_REPLAY_DECISION_FREEZE_INPUT,
            has_input,
            "" if has_input else "No replay decision freeze input was supplied.",
            "",
            str(has_input),
        )
    ]
    precondition_results.extend(_check_file(settings.replay_decision_freeze_plan_path, "replay_decision_freeze_plan"))
    precondition_results.extend(_check_request(settings, request_payload))
    precondition_results.extend(_check_candidate(settings, candidate_payload))

    lineage_results = _check_lineage(settings, actual_payload, actual_health, actual_status)
    authority_results = _check_authority(settings, approval_payload, authority_payload)
    attestation_results = _check_attestation(settings, attestation_payload)
    pit_results = _check_pit_source(settings, pit_payload)
    pit_results.extend(_check_factor_event_company(settings, factor_payload))
    pit_results.extend(_check_source_hash(settings, source_hash_payload))
    taxonomy_results = _check_taxonomy(settings, taxonomy_payload)
    leakage_results = _check_leakage_side_effect(settings, leakage_payload)
    payloads = [p for p in [actual_payload, request_payload, candidate_payload, leakage_payload] if p]
    leakage_results.extend(
        _check_false_fields(payloads, LEAKAGE_FALSE_FIELDS, REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED, "leakage_false_field_guard")
    )
    leakage_results.extend(
        _check_false_fields(payloads, SIDE_EFFECT_FALSE_FIELDS, REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED, "side_effect_false_field_guard")
    )
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
    ready = status == READY_FOR_REPLAY_DECISION_FREEZE
    frozen = ready and settings.allow_replay_decision_freeze
    if frozen:
        status = REPLAY_DECISION_FROZEN
    workflow_stage = "REPLAY_DECISION_FREEZE_NO_INPUT" if status == NO_REPLAY_DECISION_FREEZE_INPUT else status
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
    replay_decision_rows_path = artifact_path / "replay_decision_rows.csv"
    result = ReplayDecisionFreezeResult(
        replay_decision_freeze_run_id=run_id,
        created_at=created_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=workflow_stage,
        ready_for_replay_decision_freeze=ready or frozen,
        replay_decision_freeze_executed=frozen,
        replay_decision_frozen=frozen,
        replay_decision_artifacts_created=frozen,
        precondition_results=precondition_results,
        authority_results=authority_results,
        lineage_results=lineage_results,
        attestation_results=attestation_results,
        pit_source_evidence_results=pit_results,
        taxonomy_results=taxonomy_results,
        leakage_side_effect_results=leakage_results,
        overclaim_results=overclaim_results,
        source_actual_replay_execution_run_id=_text(actual_payload.get("actual_replay_execution_run_id")),
        source_actual_replay_execution_artifact_path=_path_str(settings.actual_replay_execution_artifact_path),
        source_active_input_creation_run_id=_text(actual_payload.get("source_active_input_creation_run_id")),
        source_real_replay_precheck_run_id=_text(actual_payload.get("source_real_replay_precheck_run_id")),
        actual_replay_execution_status=_text(actual_payload.get("execution_status") or actual_payload.get("status") or actual_status.get("status")),
        actual_replay_execution_health_status=_text(actual_health.get("health_status") or actual_health.get("status")),
        actual_replay_executed=_to_bool(actual_payload.get("actual_replay_executed")),
        replay_execution_started=_to_bool(actual_payload.get("replay_execution_started")),
        replay_execution_completed=_to_bool(actual_payload.get("replay_execution_completed")),
        replay_as_of_date=_text(actual_payload.get("replay_as_of_date")),
        replay_calendar=_text(actual_payload.get("replay_calendar")),
        symbol_universe_ref=_text(actual_payload.get("symbol_universe_ref")),
        pit_universe_ref=_text(actual_payload.get("pit_universe_ref")),
        source_registry_ref=_text(actual_payload.get("source_registry_ref")),
        raw_document_store_ref=_text(actual_payload.get("raw_document_store_ref")),
        factor_definition_ref=_text(actual_payload.get("factor_definition_ref")),
        factor_observation_ref=_text(actual_payload.get("factor_observation_ref")),
        event_structured_ref=_text(actual_payload.get("event_structured_ref")),
        company_exposure_ref=_text(actual_payload.get("company_exposure_ref")),
        evidence_bundle_ref=_text(actual_payload.get("evidence_bundle_ref")),
        source_hash_coverage=_text(actual_payload.get("source_hash_coverage")),
        revision_id_coverage=_text(actual_payload.get("revision_id_coverage")),
        available_time_policy=_text(actual_payload.get("available_time_policy")),
        taxonomy_coverage=_text(actual_payload.get("taxonomy_coverage")),
        future_labels_excluded=_to_bool(actual_payload.get("future_labels_excluded") or candidate_payload.get("future_labels_excluded")),
        deterministic_only=_to_bool(actual_payload.get("deterministic_only") or candidate_payload.get("deterministic_only")),
        replay_decisions_created=frozen,
        replay_decisions_exist=frozen,
        replay_decision_artifact_path=str(replay_decision_rows_path) if frozen else "",
        forward_labels_allowed=False,
        forward_labels_exist=False,
        forward_return_labels_created=False,
        training_allowed=False,
        weights_trained=False,
        training_result_created=False,
        stock_profile_allowed=False,
        active_stock_profile_exists=False,
        stock_profile_created=False,
        buy_review_allowed=False,
        real_buy_review_eligible=False,
        approved_for_paper=False,
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
        signal_semantics_changed=False,
        report_only=settings.report_only,
        diagnostic_only=settings.diagnostic_only,
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        artifact_paths=_artifact_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_replay_decision_freeze_artifacts(result, candidate_payload)
    return result


def write_replay_decision_freeze_artifacts(
    result: ReplayDecisionFreezeResult,
    candidate_payload: dict[str, Any] | None = None,
) -> None:
    candidate_payload = candidate_payload or {}
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], _metadata(result))
    _write_json(paths["safety_flags"], _safety_flags(result))
    paths["report"].write_text(_render_report(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")
    _write_frame(paths["precondition_results"], result.precondition_results)
    _write_frame(paths["authority_results"], result.authority_results)
    _write_frame(paths["lineage_results"], result.lineage_results)
    _write_frame(paths["attestation_results"], result.attestation_results)
    _write_frame(paths["pit_source_evidence_results"], result.pit_source_evidence_results)
    _write_frame(paths["taxonomy_evidence_results"], result.taxonomy_results)
    _write_frame(paths["leakage_side_effect_guard_results"], result.leakage_side_effect_results)
    _write_frame(paths["overclaim_guard_results"], result.overclaim_results)
    pd.DataFrame(_decision_rows(result, candidate_payload), columns=_decision_columns()).to_csv(
        paths["replay_decision_rows"], index=False
    )
    pd.DataFrame(_evidence_rows(result), columns=_evidence_columns()).to_csv(
        paths["replay_decision_evidence_index"], index=False
    )


def _artifact_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "artifact_dir": artifact_path,
        "metadata": artifact_path / "replay_decision_metadata.json",
        "report": artifact_path / "replay_decision_freeze_report.md",
        "replay_decision_rows": artifact_path / "replay_decision_rows.csv",
        "replay_decision_evidence_index": artifact_path / "replay_decision_evidence_index.csv",
        "safety_flags": artifact_path / "replay_decision_safety_flags.json",
        "precondition_results": artifact_path / "replay_decision_precondition_results.csv",
        "authority_results": artifact_path / "replay_decision_authority_results.csv",
        "lineage_results": artifact_path / "replay_decision_lineage_results.csv",
        "attestation_results": artifact_path / "replay_decision_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def _check_file(path: Path | None, gate_name: str) -> list[ReplayDecisionFreezePreconditionResult]:
    passed = _path_exists(path)
    return [
        ReplayDecisionFreezePreconditionResult(
            "replay_decision_freeze_review",
            gate_name,
            "PASS" if passed else REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
            passed,
            "" if passed else f"{gate_name} is missing.",
            _path_str(path),
        )
    ]


def _check_request(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezePreconditionResult]:
    passed = _path_exists(settings.replay_decision_freeze_request_manifest_path) and _to_bool(
        payload.get("replay_decision_freeze_core_requested")
    ) and _to_bool(payload.get("report_only"))
    return [
        ReplayDecisionFreezePreconditionResult(
            "replay_decision_freeze_review",
            "replay_decision_freeze_request",
            "PASS" if passed else REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
            passed,
            "" if passed else "Replay decision freeze request is incomplete.",
            _path_str(settings.replay_decision_freeze_request_manifest_path),
        )
    ]


def _check_candidate(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezePreconditionResult]:
    exists = _path_exists(settings.replay_decision_candidate_manifest_path)
    label = _text(payload.get("decision_label") or "WATCH")
    forbidden_fields = [
        field
        for field in [
            "future_close",
            "future_price",
            "forward_return",
            "forward_return_label",
            "training_score",
            "model_weight",
            "stock_profile_status",
            "order_id",
            "trade_id",
        ]
        if field in payload
    ]
    passed = exists and _to_bool(payload.get("deterministic_only")) and _to_bool(
        payload.get("future_labels_excluded")
    ) and label in ALLOWED_DECISION_LABELS and not forbidden_fields
    return [
        ReplayDecisionFreezePreconditionResult(
            "replay_decision_freeze_review",
            "replay_decision_candidate_manifest",
            "PASS" if passed else REPLAY_DECISION_FREEZE_REVIEW_BLOCKED,
            passed,
            "" if passed else "Replay decision candidate manifest is incomplete or unsafe.",
            _path_str(settings.replay_decision_candidate_manifest_path),
            ",".join(forbidden_fields),
        )
    ]


def _check_lineage(
    settings: ReplayDecisionFreezeSettings,
    actual: dict[str, Any],
    health: dict[str, Any],
    status: dict[str, Any],
) -> list[ReplayDecisionFreezeLineageResult]:
    actual_status = _text(actual.get("execution_status") or actual.get("status") or status.get("status"))
    health_status = _text(health.get("health_status") or health.get("status"))
    checks = [
        ("actual_replay_execution_artifact_exists", _path_exists(settings.actual_replay_execution_artifact_path), settings.actual_replay_execution_artifact_path, "Actual replay execution artifact is missing."),
        ("actual_replay_execution_status_artifact_exists", _path_exists(settings.actual_replay_execution_status_artifact_path), settings.actual_replay_execution_status_artifact_path, "Actual replay execution status artifact is missing."),
        ("actual_replay_execution_status", actual_status == ACTUAL_REPLAY_EXECUTED, settings.actual_replay_execution_artifact_path, "Actual replay execution status is not ACTUAL_REPLAY_EXECUTED."),
        ("actual_replay_execution_health_pass", health_status == "PASS", settings.actual_replay_execution_health_artifact_path, "Actual replay execution health is not PASS."),
        ("actual_replay_executed_true", _to_bool(actual.get("actual_replay_executed")), settings.actual_replay_execution_artifact_path, "actual_replay_executed is not true."),
        ("replay_execution_started_true", _to_bool(actual.get("replay_execution_started")), settings.actual_replay_execution_artifact_path, "replay_execution_started is not true."),
        ("replay_execution_completed_true", _to_bool(actual.get("replay_execution_completed")), settings.actual_replay_execution_artifact_path, "replay_execution_completed is not true."),
        ("source_active_input_creation_lineage", bool(_text(actual.get("source_active_input_creation_run_id"))), settings.actual_replay_execution_artifact_path, "Active input creation lineage is missing."),
        ("source_real_replay_precheck_lineage", bool(_text(actual.get("source_real_replay_precheck_run_id"))), settings.actual_replay_execution_artifact_path, "Real replay precheck lineage is missing."),
    ]
    return [_lineage(*check) for check in checks]


def _check_authority(
    settings: ReplayDecisionFreezeSettings,
    approval: dict[str, Any],
    authority: dict[str, Any],
) -> list[ReplayDecisionFreezeAuthorityResult]:
    text = _text(approval.get("approval_text"))
    exact = _normalize(text) == _normalize(EXACT_APPROVAL_TEXT)
    lower = text.lower()
    forbidden = any(
        token in lower
        for token in ["forward label", "training", "stock_profile", "buy-review", "trading"]
    ) and not exact
    authority_ok = _text(authority.get("authority_result")) == "ACCEPTED_FOR_REPLAY_DECISION_FREEZE_CORE_ONLY"
    return [
        ReplayDecisionFreezeAuthorityResult(
            "authority",
            "exact_approval_wording",
            "PASS" if exact and not forbidden else REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED,
            exact and not forbidden,
            "" if exact and not forbidden else "Exact narrow approval wording is missing or invalid.",
            _path_str(settings.approval_manifest_path),
            text,
        ),
        ReplayDecisionFreezeAuthorityResult(
            "authority",
            "replay_decision_freeze_authority",
            "PASS" if _path_exists(settings.replay_decision_freeze_authority_manifest_path) and authority_ok else REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED,
            _path_exists(settings.replay_decision_freeze_authority_manifest_path) and authority_ok,
            "" if authority_ok else "Replay decision freeze authority is missing or invalid.",
            _path_str(settings.replay_decision_freeze_authority_manifest_path),
            _text(authority.get("authority_result")),
        ),
    ]


def _check_attestation(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezeAttestationResult]:
    exists = _path_exists(settings.second_reviewer_attestation_manifest_path)
    missing = _missing_true_fields(payload, ATTESTATION_TRUE_FIELDS)
    passed = exists and not missing
    return [
        ReplayDecisionFreezeAttestationResult(
            "attestation",
            "second_reviewer_attestation",
            "PASS" if passed else REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED,
            passed,
            "" if passed else "Second reviewer attestation is incomplete.",
            _path_str(settings.second_reviewer_attestation_manifest_path),
            missing if exists else "missing_bundle",
        )
    ]


def _check_pit_source(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezePitSourceEvidenceResult]:
    exists = _path_exists(settings.pit_source_evidence_bundle_path)
    if not exists:
        return [
            ReplayDecisionFreezePitSourceEvidenceResult(
                "pit_source_evidence",
                "pit_source_evidence_bundle",
                REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED,
                False,
                "PIT/source/evidence bundle is missing.",
                _path_str(settings.pit_source_evidence_bundle_path),
                "missing_bundle",
            )
        ]
    return [
        _pit_source("accepted_pit_universe_evidence", not _missing_true_fields(payload, PIT_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, REPLAY_DECISION_FREEZE_PIT_BLOCKED, "Accepted PIT universe evidence is missing."),
        _pit_source("source_registry_evidence", not _missing_true_fields(payload, SOURCE_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, REPLAY_DECISION_FREEZE_SOURCE_BLOCKED, "Source registry evidence is missing."),
        _pit_source("raw_document_and_evidence_bundle", not _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS), settings.pit_source_evidence_bundle_path, REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED, "Raw document or evidence bundle evidence is missing."),
    ]


def _check_taxonomy(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezeTaxonomyResult]:
    exists = _path_exists(settings.taxonomy_evidence_bundle_path)
    missing = _missing_true_fields(payload, TAXONOMY_TRUE_FIELDS)
    passed = exists and not missing
    return [
        ReplayDecisionFreezeTaxonomyResult(
            "taxonomy_evidence",
            "eight_layer_taxonomy_evidence",
            "PASS" if passed else REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED,
            passed,
            "" if passed else "8-layer taxonomy evidence is incomplete.",
            _path_str(settings.taxonomy_evidence_bundle_path),
            missing if exists else "missing_bundle",
        )
    ]


def _check_factor_event_company(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezePitSourceEvidenceResult]:
    exists = _path_exists(settings.factor_event_company_evidence_bundle_path)
    missing = _missing_true_fields(payload, FACTOR_EVENT_COMPANY_TRUE_FIELDS)
    passed = exists and not missing
    return [
        ReplayDecisionFreezePitSourceEvidenceResult(
            "pit_source_evidence",
            "factor_event_company_pit_evidence",
            "PASS" if passed else REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED,
            passed,
            "" if passed else "Factor, event, or company exposure PIT evidence is incomplete.",
            _path_str(settings.factor_event_company_evidence_bundle_path),
            missing if exists else "missing_bundle",
        )
    ]


def _check_source_hash(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezePitSourceEvidenceResult]:
    exists = _path_exists(settings.source_hash_revision_available_time_evidence_path)
    missing = _missing_true_fields(payload, SOURCE_HASH_TRUE_FIELDS)
    policy_ok = _text(payload.get("available_time_policy")) == "ALL_AVAILABLE_TIME_LTE_REPLAY_DECISION_TIME"
    passed = exists and not missing and policy_ok
    return [
        ReplayDecisionFreezePitSourceEvidenceResult(
            "pit_source_evidence",
            "source_hash_revision_available_time",
            "PASS" if passed else REPLAY_DECISION_FREEZE_SOURCE_BLOCKED,
            passed,
            "" if passed else "Source hash, revision_id, or available_time evidence is incomplete.",
            _path_str(settings.source_hash_revision_available_time_evidence_path),
            missing if exists else "missing_bundle",
        )
    ]


def _check_leakage_side_effect(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezeLeakageSideEffectResult]:
    exists = _path_exists(settings.leakage_side_effect_evidence_bundle_path)
    leakage_missing = _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS)
    side_missing = _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS)
    return [
        ReplayDecisionFreezeLeakageSideEffectResult(
            "leakage_side_effect",
            "leakage_exclusion_checks",
            "PASS" if exists and not leakage_missing else REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED,
            exists and not leakage_missing,
            "" if exists and not leakage_missing else "Leakage exclusion evidence is incomplete.",
            _path_str(settings.leakage_side_effect_evidence_bundle_path),
            leakage_missing if exists else "missing_bundle",
        ),
        ReplayDecisionFreezeLeakageSideEffectResult(
            "leakage_side_effect",
            "side_effect_exclusion_checks",
            "PASS" if exists and not side_missing else REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED,
            exists and not side_missing,
            "" if exists and not side_missing else "Side-effect exclusion evidence is incomplete.",
            _path_str(settings.leakage_side_effect_evidence_bundle_path),
            side_missing if exists else "missing_bundle",
        ),
    ]


def _check_overclaim(settings: ReplayDecisionFreezeSettings, payload: dict[str, Any]) -> list[ReplayDecisionFreezeOverclaimResult]:
    exists = _path_exists(settings.overclaim_evidence_bundle_path)
    missing = _missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS)
    passed = exists and not missing
    return [
        ReplayDecisionFreezeOverclaimResult(
            "overclaim_guard",
            "replay_decision_boundary_guards",
            "PASS" if passed else REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
            passed,
            "" if passed else "Overclaim guard evidence is incomplete.",
            _path_str(settings.overclaim_evidence_bundle_path),
            missing if exists else "missing_bundle",
        )
    ]


def _pit_source(
    gate_name: str,
    passed: bool,
    path: Path | None,
    fail_status: str,
    blocker: str,
) -> ReplayDecisionFreezePitSourceEvidenceResult:
    return ReplayDecisionFreezePitSourceEvidenceResult(
        "pit_source_evidence",
        gate_name,
        "PASS" if passed else fail_status,
        passed,
        "" if passed else blocker,
        _path_str(path),
    )


def _lineage(gate_name: str, passed: bool, path: Path | None, blocker: str) -> ReplayDecisionFreezeLineageResult:
    return ReplayDecisionFreezeLineageResult(
        "lineage",
        gate_name,
        "PASS" if passed else REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED,
        passed,
        "" if passed else blocker,
        _path_str(path),
        str(passed),
    )


def _check_false_fields(
    payloads: list[dict[str, Any]],
    fields: list[str],
    failure_status: str,
    gate_group: str,
) -> list[ReplayDecisionFreezeLeakageSideEffectResult]:
    rows: list[ReplayDecisionFreezeLeakageSideEffectResult] = []
    for field in fields:
        passed = not any(_to_bool(payload.get(field)) for payload in payloads)
        rows.append(
            ReplayDecisionFreezeLeakageSideEffectResult(
                gate_group,
                field,
                "PASS" if passed else failure_status,
                passed,
                "" if passed else f"{field} must remain false.",
                "input_payloads",
                str(not passed),
            )
        )
    return rows


def _check_overclaim_false_fields(payloads: list[dict[str, Any]]) -> list[ReplayDecisionFreezeOverclaimResult]:
    rows: list[ReplayDecisionFreezeOverclaimResult] = []
    for field in OVERCLAIM_FALSE_FIELDS:
        passed = not any(_to_bool(payload.get(field)) for payload in payloads)
        rows.append(
            ReplayDecisionFreezeOverclaimResult(
                "overclaim_false_field_guard",
                field,
                "PASS" if passed else REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
                passed,
                "" if passed else f"{field} must remain false.",
                "input_payloads",
                str(not passed),
            )
        )
    return rows


def _built_in_overclaim_guards(output_dir: Path) -> list[ReplayDecisionFreezeOverclaimResult]:
    passed = "manual_diagnostics" in output_dir.parts
    return [
        ReplayDecisionFreezeOverclaimResult(
            "built_in_overclaim_guard",
            "output_path_under_manual_diagnostics",
            "PASS" if passed else REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED,
            passed,
            "" if passed else "Output path must remain under manual_diagnostics.",
            str(output_dir),
            str(passed),
        )
    ]


def _resolve_status(
    has_input: bool,
    precondition_results: list[ReplayDecisionFreezePreconditionResult],
    lineage_results: list[ReplayDecisionFreezeLineageResult],
    authority_results: list[ReplayDecisionFreezeAuthorityResult],
    attestation_results: list[ReplayDecisionFreezeAttestationResult],
    pit_results: list[ReplayDecisionFreezePitSourceEvidenceResult],
    taxonomy_results: list[ReplayDecisionFreezeTaxonomyResult],
    leakage_results: list[ReplayDecisionFreezeLeakageSideEffectResult],
    overclaim_results: list[ReplayDecisionFreezeOverclaimResult],
) -> str:
    if not has_input:
        return NO_REPLAY_DECISION_FREEZE_INPUT
    ordered = [
        (lineage_results, [REPLAY_DECISION_FREEZE_LINEAGE_BLOCKED]),
        (precondition_results, [REPLAY_DECISION_FREEZE_REVIEW_BLOCKED]),
        (authority_results, [REPLAY_DECISION_FREEZE_AUTHORITY_BLOCKED]),
        (attestation_results, [REPLAY_DECISION_FREEZE_ATTESTATION_BLOCKED]),
        (pit_results, [REPLAY_DECISION_FREEZE_PIT_BLOCKED, REPLAY_DECISION_FREEZE_SOURCE_BLOCKED, REPLAY_DECISION_FREEZE_EVIDENCE_BLOCKED]),
        (taxonomy_results, [REPLAY_DECISION_FREEZE_TAXONOMY_BLOCKED]),
        (leakage_results, [REPLAY_DECISION_FREEZE_LEAKAGE_BLOCKED, REPLAY_DECISION_FREEZE_SIDE_EFFECT_BLOCKED]),
        (overclaim_results, [REPLAY_DECISION_FREEZE_OVERCLAIM_BLOCKED]),
    ]
    for rows, statuses in ordered:
        for status in statuses:
            if any(not row.passed and row.status == status for row in rows):
                return status
    return READY_FOR_REPLAY_DECISION_FREEZE


def _metadata(result: ReplayDecisionFreezeResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    payload["execution_status"] = result.status
    return payload


def _safety_flags(result: ReplayDecisionFreezeResult) -> dict[str, Any]:
    return {field: getattr(result, field) for field in SAFETY_FALSE_FIELDS}


def _decision_columns() -> list[str]:
    return [
        "replay_decision_id",
        "replay_decision_freeze_run_id",
        "actual_replay_execution_run_id",
        "source_active_input_creation_run_id",
        "source_real_replay_precheck_run_id",
        "replay_as_of_date",
        "symbol",
        "instrument_type",
        "decision_label",
        "decision_reason_code",
        "evidence_bundle_id",
        "factor_layer_support",
        "factor_ids",
        "event_ids",
        "source_ids",
        "available_time_max",
        "source_hash_coverage",
        "revision_id_coverage",
        "taxonomy_coverage",
        "risk_vetoes",
        "confidence",
        "generated_at",
        "frozen_at",
        "report_only",
        "diagnostic_only",
    ]


def _decision_rows(result: ReplayDecisionFreezeResult, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    if not result.replay_decision_frozen:
        return []
    label = _text(candidate.get("decision_label") or "WATCH")
    if label not in ALLOWED_DECISION_LABELS:
        label = "BLOCKED"
    decision_id = hashlib.sha256(
        f"{result.replay_decision_freeze_run_id}|{candidate.get('symbol', '000001')}|{label}".encode("utf-8")
    ).hexdigest()[:12]
    return [
        {
            "replay_decision_id": decision_id,
            "replay_decision_freeze_run_id": result.replay_decision_freeze_run_id,
            "actual_replay_execution_run_id": result.source_actual_replay_execution_run_id,
            "source_active_input_creation_run_id": result.source_active_input_creation_run_id,
            "source_real_replay_precheck_run_id": result.source_real_replay_precheck_run_id,
            "replay_as_of_date": result.replay_as_of_date,
            "symbol": _text(candidate.get("symbol") or "000001"),
            "instrument_type": _text(candidate.get("instrument_type") or "STOCK"),
            "decision_label": label,
            "decision_reason_code": _text(candidate.get("decision_reason_code") or "REPORT_ONLY_REPLAY_DECISION_FREEZE"),
            "evidence_bundle_id": _text(candidate.get("evidence_bundle_id") or result.evidence_bundle_ref or "evidence_bundle"),
            "factor_layer_support": _text(candidate.get("factor_layer_support") or result.taxonomy_coverage),
            "factor_ids": _text(candidate.get("factor_ids")),
            "event_ids": _text(candidate.get("event_ids")),
            "source_ids": _text(candidate.get("source_ids")),
            "available_time_max": _text(candidate.get("available_time_max") or result.available_time_policy),
            "source_hash_coverage": result.source_hash_coverage,
            "revision_id_coverage": result.revision_id_coverage,
            "taxonomy_coverage": result.taxonomy_coverage,
            "risk_vetoes": _text(candidate.get("risk_vetoes")),
            "confidence": candidate.get("confidence", ""),
            "generated_at": result.created_at,
            "frozen_at": result.created_at,
            "report_only": result.report_only,
            "diagnostic_only": result.diagnostic_only,
        }
    ]


def _evidence_columns() -> list[str]:
    return [
        "replay_decision_id",
        "evidence_bundle_id",
        "source_id",
        "source_hash",
        "revision_id",
        "available_time",
        "taxonomy_layer",
        "factor_ids",
        "event_ids",
        "pit_valid",
        "quality_status",
        "permission_class",
    ]


def _evidence_rows(result: ReplayDecisionFreezeResult) -> list[dict[str, Any]]:
    if not result.replay_decision_frozen:
        return []
    return [
        {
            "replay_decision_id": result.replay_decision_freeze_run_id,
            "evidence_bundle_id": result.evidence_bundle_ref or "evidence_bundle",
            "source_id": "source_registry",
            "source_hash": result.source_hash_coverage,
            "revision_id": result.revision_id_coverage,
            "available_time": result.available_time_policy,
            "taxonomy_layer": result.taxonomy_coverage,
            "factor_ids": "factor_ids",
            "event_ids": "event_ids",
            "pit_valid": True,
            "quality_status": "PASS",
            "permission_class": "REPORT_ONLY_LOCAL_EVIDENCE",
        }
    ]


def _render_report(result: ReplayDecisionFreezeResult) -> str:
    return "\n".join(
        [
            "# Replay Decision Freeze Core Report",
            "",
            f"- replay_decision_freeze_run_id: `{result.replay_decision_freeze_run_id}`",
            f"- status: `{result.status}`",
            f"- workflow_stage: `{result.workflow_stage}`",
            f"- ready_for_replay_decision_freeze: `{result.ready_for_replay_decision_freeze}`",
            f"- replay_decision_frozen: `{result.replay_decision_frozen}`",
            "",
            "This is report-only replay decision freeze core.",
            "",
            "A frozen replay_decision is not forward-label permission, not training, not stock_profile, "
            "not buy-review, not paper approval, not performance validation, not broker integration, "
            "not orders, not messages, and not trading.",
        ]
    )


def _render_next_task(result: ReplayDecisionFreezeResult) -> str:
    if result.status == REPLAY_DECISION_FROZEN:
        return "# Recommended Next Task\n\nReplay Decision Freeze Artifact Views Report-Only v0.1.\n"
    if result.status == READY_FOR_REPLAY_DECISION_FREEZE:
        return "# Recommended Next Task\n\nRerun with --allow-replay-decision-freeze only with explicit approval.\n"
    return "# Recommended Next Task\n\nResolve replay decision freeze blockers before freezing decisions.\n"


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


def _build_run_id(settings: ReplayDecisionFreezeSettings, created_at: str) -> str:
    payload = {
        "created_at": created_at,
        "actual_replay_execution_artifact_path": _path_str(settings.actual_replay_execution_artifact_path),
        "candidate_path": _path_str(settings.replay_decision_candidate_manifest_path),
        "allow": settings.allow_replay_decision_freeze,
        "output_dir": str(settings.output_dir),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if "manual_diagnostics" not in path.parts:
        raise ValueError("Replay decision freeze artifacts must be written under manual_diagnostics.")
