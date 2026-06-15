"""Report-only active replay input creation workflow.

This workflow may create only a governed, report-only active replay input
artifact when every gate passes and the explicit allow flag is supplied. It
never runs replay, creates replay decisions, computes labels, trains weights,
creates stock profiles, changes buy-review eligibility, writes data stores,
calls APIs, mutates cache, or authorizes trading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT = "NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT"
ACTIVE_REPLAY_INPUT_CREATION_INPUT_FOUND = "ACTIVE_REPLAY_INPUT_CREATION_INPUT_FOUND"
ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED"
ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED = "ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED"
READY_FOR_ACTIVE_REPLAY_INPUT_CREATION = "READY_FOR_ACTIVE_REPLAY_INPUT_CREATION"
ACTIVE_REPLAY_INPUT_CREATED = "ACTIVE_REPLAY_INPUT_CREATED"
ACTIVE_REPLAY_INPUT_READY = "ACTIVE_REPLAY_INPUT_READY"

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_create_v0_1")
PASS_RESULTS = {"PASS", "ACCEPTED", "ACCEPTED_FOR_REVIEW_ONLY", "READY", "READY_FOR_REVIEW"}

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
    "active_input_creation_attested",
    "report_only_attested",
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
    "source_registry_evidence_attached",
    "source_id_coverage_attached",
    "source_hash_coverage_attached",
    "revision_id_coverage_attached",
    "available_time_policy_attached",
    "permission_class_coverage_attached",
]
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
    "active_input_not_replay_permission",
    "active_input_not_replay_decision_permission",
    "active_input_not_label_permission",
    "active_input_not_training_permission",
    "active_input_not_stock_profile_permission",
    "active_input_not_buy_review_eligibility",
    "active_input_not_paper_approval",
    "active_input_not_performance_validation",
    "active_input_not_trading_authorization",
    "marker_file_exists_not_sufficient",
    "marker_only_ready_not_active_input",
    "report_only",
    "diagnostic_only",
]

LEAKAGE_FALSE_FIELDS = [
    "replay_decisions_exist",
    "forward_labels_allowed",
    "forward_labels_exist",
    "forward_returns_exist",
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
    "replay_execution_allowed",
    "replay_execution_happened",
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
OVERCLAIM_FALSE_FIELDS = [
    "active_replay_input",
    "buy_review_allowed",
    "trading_allowed",
    "approved_for_paper",
]


@dataclass(frozen=True)
class ActiveReplayInputCreateSettings:
    marker_artifact_path: Path | None = None
    marker_health_artifact_path: Path | None = None
    marker_status_artifact_path: Path | None = None
    active_input_creation_plan_path: Path | None = None
    active_input_creation_request_manifest_path: Path | None = None
    active_input_authority_manifest_path: Path | None = None
    second_reviewer_attestation_manifest_path: Path | None = None
    pit_source_evidence_bundle_path: Path | None = None
    taxonomy_evidence_bundle_path: Path | None = None
    source_hash_revision_available_time_evidence_path: Path | None = None
    leakage_side_effect_evidence_bundle_path: Path | None = None
    overclaim_evidence_bundle_path: Path | None = None
    active_replay_input_candidate_manifest_path: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    allow_active_replay_input_creation: bool = False
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputCreatePreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputCreateAuthorityResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateLineageResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateAttestationResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreatePitSourceEvidenceResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateTaxonomyResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateLeakageSideEffectResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateOverclaimResult(ActiveReplayInputCreatePreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputCreateResult:
    active_input_creation_run_id: str
    active_replay_input_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActiveReplayInputCreatePreconditionResult]
    authority_results: list[ActiveReplayInputCreateAuthorityResult]
    lineage_results: list[ActiveReplayInputCreateLineageResult]
    attestation_results: list[ActiveReplayInputCreateAttestationResult]
    pit_source_evidence_results: list[ActiveReplayInputCreatePitSourceEvidenceResult]
    taxonomy_results: list[ActiveReplayInputCreateTaxonomyResult]
    leakage_side_effect_results: list[ActiveReplayInputCreateLeakageSideEffectResult]
    overclaim_results: list[ActiveReplayInputCreateOverclaimResult]
    marker_artifact_path: str
    marker_health_artifact_path: str
    marker_status_artifact_path: str
    active_input_creation_plan_path: str
    active_input_creation_request_manifest_path: str
    active_input_authority_manifest_path: str
    second_reviewer_attestation_manifest_path: str
    pit_source_evidence_bundle_path: str
    taxonomy_evidence_bundle_path: str
    source_hash_revision_available_time_evidence_path: str
    leakage_side_effect_evidence_bundle_path: str
    overclaim_evidence_bundle_path: str
    active_replay_input_candidate_manifest_path: str
    allow_active_replay_input_creation: bool
    blocker_count: int
    issue_count: int
    warning_count: int
    active_replay_input_created: bool
    active_replay_input: bool
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


def run_active_replay_input_create(
    settings: ActiveReplayInputCreateSettings | None = None,
) -> ActiveReplayInputCreateResult:
    settings = settings or ActiveReplayInputCreateSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    active_input_creation_run_id = _build_run_id(settings, generated_at)
    active_replay_input_id = f"ari_{active_input_creation_run_id}"
    artifact_path = settings.output_dir / active_input_creation_run_id

    has_input = any(
        [
            settings.marker_artifact_path,
            settings.marker_health_artifact_path,
            settings.marker_status_artifact_path,
            settings.active_input_creation_plan_path,
            settings.active_input_creation_request_manifest_path,
            settings.active_input_authority_manifest_path,
            settings.second_reviewer_attestation_manifest_path,
            settings.pit_source_evidence_bundle_path,
            settings.taxonomy_evidence_bundle_path,
            settings.source_hash_revision_available_time_evidence_path,
            settings.leakage_side_effect_evidence_bundle_path,
            settings.overclaim_evidence_bundle_path,
            settings.active_replay_input_candidate_manifest_path,
        ]
    )
    precondition_results = [
        ActiveReplayInputCreatePreconditionResult(
            gate_group="active_replay_input_creation_input",
            gate_name="active_input_creation_input_present",
            status=ACTIVE_REPLAY_INPUT_CREATION_INPUT_FOUND
            if has_input
            else NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No active replay input creation input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    marker_payload = _load_artifact_payload(settings.marker_artifact_path, "active_replay_input_ready_marker.json")
    marker_health_payload = _read_json(settings.marker_health_artifact_path)
    marker_status_payload = _read_json(settings.marker_status_artifact_path)
    request_payload = _read_json(settings.active_input_creation_request_manifest_path)
    candidate_payload = _read_json(settings.active_replay_input_candidate_manifest_path)

    lineage_results = _check_marker_lineage(settings, marker_payload, marker_health_payload, marker_status_payload)
    precondition_results.extend(_check_creation_plan(settings))
    authority_results = _check_creation_request(settings, request_payload)
    authority_results.extend(_check_authority(settings))
    attestation_results = _check_attestation(settings)
    pit_source_results = _check_pit_source_evidence(settings)
    taxonomy_results = _check_taxonomy(settings)
    source_hash_results = _check_source_hash_revision_available_time(settings)
    pit_source_results.extend(source_hash_results)
    leakage_side_effect_results = _check_leakage_side_effect(settings)
    overclaim_results = _check_overclaim(settings)
    candidate_results = _check_candidate_manifest(settings, candidate_payload)
    pit_source_results.extend(candidate_results)

    safety_payloads = [
        payload
        for payload in [
            marker_payload,
            marker_status_payload,
            request_payload,
            candidate_payload,
            _read_json(settings.leakage_side_effect_evidence_bundle_path),
        ]
        if payload
    ]
    leakage_side_effect_results.extend(
        _check_false_fields(safety_payloads, LEAKAGE_FALSE_FIELDS, ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED)
    )
    leakage_side_effect_results.extend(
        _check_false_fields(safety_payloads, SIDE_EFFECT_FALSE_FIELDS, ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED)
    )
    overclaim_results.extend(
        _check_false_fields(safety_payloads, OVERCLAIM_FALSE_FIELDS, ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED)
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
        ACTIVE_REPLAY_INPUT_CREATED
        if base_status == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION
        and settings.allow_active_replay_input_creation
        else base_status
    )
    created = status == ACTIVE_REPLAY_INPUT_CREATED
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
    result = ActiveReplayInputCreateResult(
        active_input_creation_run_id=active_input_creation_run_id,
        active_replay_input_id=active_replay_input_id,
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
        marker_artifact_path=_path_str(settings.marker_artifact_path),
        marker_health_artifact_path=_path_str(settings.marker_health_artifact_path),
        marker_status_artifact_path=_path_str(settings.marker_status_artifact_path),
        active_input_creation_plan_path=_path_str(settings.active_input_creation_plan_path),
        active_input_creation_request_manifest_path=_path_str(
            settings.active_input_creation_request_manifest_path
        ),
        active_input_authority_manifest_path=_path_str(settings.active_input_authority_manifest_path),
        second_reviewer_attestation_manifest_path=_path_str(
            settings.second_reviewer_attestation_manifest_path
        ),
        pit_source_evidence_bundle_path=_path_str(settings.pit_source_evidence_bundle_path),
        taxonomy_evidence_bundle_path=_path_str(settings.taxonomy_evidence_bundle_path),
        source_hash_revision_available_time_evidence_path=_path_str(
            settings.source_hash_revision_available_time_evidence_path
        ),
        leakage_side_effect_evidence_bundle_path=_path_str(settings.leakage_side_effect_evidence_bundle_path),
        overclaim_evidence_bundle_path=_path_str(settings.overclaim_evidence_bundle_path),
        active_replay_input_candidate_manifest_path=_path_str(
            settings.active_replay_input_candidate_manifest_path
        ),
        allow_active_replay_input_creation=settings.allow_active_replay_input_creation,
        blocker_count=blockers,
        issue_count=blockers,
        warning_count=0,
        active_replay_input_created=created,
        active_replay_input=created,
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
        artifact_paths=resolve_active_replay_input_create_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_active_replay_input_create_artifacts(result, marker_payload, candidate_payload)
    return result


def resolve_active_replay_input_create_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "active_input_creation_metadata.json",
        "report": artifact_path / "active_input_creation_report.md",
        "precondition_results": artifact_path / "active_input_precondition_results.csv",
        "authority_results": artifact_path / "active_input_authority_results.csv",
        "lineage_results": artifact_path / "active_input_lineage_results.csv",
        "attestation_results": artifact_path / "active_input_attestation_results.csv",
        "pit_source_evidence_results": artifact_path / "pit_source_evidence_results.csv",
        "taxonomy_evidence_results": artifact_path / "taxonomy_evidence_results.csv",
        "leakage_side_effect_guard_results": artifact_path / "leakage_side_effect_guard_results.csv",
        "overclaim_guard_results": artifact_path / "overclaim_guard_results.csv",
        "active_replay_input": artifact_path / "active_replay_input.json",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_create_artifacts(
    result: ActiveReplayInputCreateResult,
    marker_payload: dict[str, Any] | None = None,
    candidate_payload: dict[str, Any] | None = None,
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
    _write_json(
        result.artifact_paths["active_replay_input"],
        _active_replay_input_payload(result, marker_payload or {}, candidate_payload or {}),
    )
    result.artifact_paths["report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _check_marker_lineage(
    settings: ActiveReplayInputCreateSettings,
    marker_payload: dict[str, Any],
    marker_health_payload: dict[str, Any],
    marker_status_payload: dict[str, Any],
) -> list[ActiveReplayInputCreateLineageResult]:
    results: list[ActiveReplayInputCreateLineageResult] = []
    marker_status = _text(marker_payload.get("marker_status") or marker_payload.get("status"))
    marker_emitted = _to_bool(marker_payload.get("active_replay_input_ready_marker_emitted"))
    marker_file_exists = _path_exists(settings.marker_artifact_path)
    passed_marker = marker_file_exists and marker_status == ACTIVE_REPLAY_INPUT_READY and marker_emitted
    results.append(
        _lineage(
            "marker_status_and_emitted",
            "PASS" if passed_marker else ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
            passed_marker,
            ""
            if passed_marker
            else "Marker lineage must have status ACTIVE_REPLAY_INPUT_READY and marker emitted true.",
            settings.marker_artifact_path,
            f"{marker_status}|emitted={marker_emitted}|exists={marker_file_exists}",
        )
    )
    health_status = _text(marker_health_payload.get("health_status") or marker_health_payload.get("status"))
    passed_health = _path_exists(settings.marker_health_artifact_path) and health_status == "PASS"
    results.append(
        _lineage(
            "marker_health",
            "PASS" if passed_health else ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
            passed_health,
            "" if passed_health else "Marker health must be PASS.",
            settings.marker_health_artifact_path,
            health_status,
        )
    )
    summary_status = _text(marker_status_payload.get("status") or marker_status_payload.get("marker_status"))
    summary_emitted = _to_bool(marker_status_payload.get("active_replay_input_ready_marker_emitted"))
    summary_ok = (
        _path_exists(settings.marker_status_artifact_path)
        and summary_status == ACTIVE_REPLAY_INPUT_READY
        and summary_emitted
    )
    results.append(
        _lineage(
            "marker_status_artifact",
            "PASS" if summary_ok else ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
            summary_ok,
            "" if summary_ok else "Marker status artifact is not ACTIVE_REPLAY_INPUT_READY with emitted true.",
            settings.marker_status_artifact_path,
            f"{summary_status}|emitted={summary_emitted}",
        )
    )
    semantics_ok = _to_bool(marker_payload.get("marker_only_semantics_confirmed")) or _to_bool(
        marker_status_payload.get("marker_only_semantics_confirmed")
    )
    results.append(
        _lineage(
            "marker_only_semantics",
            "PASS" if semantics_ok else ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED,
            semantics_ok,
            "" if semantics_ok else "Marker-only semantics must be confirmed.",
            settings.marker_artifact_path,
            str(semantics_ok),
        )
    )
    return results


def _check_creation_plan(
    settings: ActiveReplayInputCreateSettings,
) -> list[ActiveReplayInputCreatePreconditionResult]:
    passed = _path_exists(settings.active_input_creation_plan_path)
    return [
        ActiveReplayInputCreatePreconditionResult(
            gate_group="active_input_creation_review",
            gate_name="active_input_creation_plan_present",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Active input creation plan path is missing.",
            evidence_path=_path_str(settings.active_input_creation_plan_path),
            observed_value=str(passed),
        )
    ]


def _check_creation_request(
    settings: ActiveReplayInputCreateSettings,
    payload: dict[str, Any],
) -> list[ActiveReplayInputCreateAuthorityResult]:
    passed = (
        _path_exists(settings.active_input_creation_request_manifest_path)
        and _passish(payload.get("request_result"))
        and _to_bool(payload.get("explicit_active_replay_input_creation_request"))
        and _text(payload.get("requested_input_status")) == ACTIVE_REPLAY_INPUT_CREATED
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
    )
    return [
        _authority(
            "active_input_creation_request",
            "PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED,
            passed,
            "" if passed else "Active input creation request must be explicit, report_only, and diagnostic_only.",
            settings.active_input_creation_request_manifest_path,
            "PASS" if passed else _text(payload.get("request_result")),
        )
    ]


def _check_authority(
    settings: ActiveReplayInputCreateSettings,
) -> list[ActiveReplayInputCreateAuthorityResult]:
    payload = _read_json(settings.active_input_authority_manifest_path)
    missing = [field for field in AUTHORITY_FIELDS if not _text(payload.get(field))]
    scope = _text(payload.get("authority_scope"))
    passed = (
        _path_exists(settings.active_input_authority_manifest_path)
        and _passish(payload.get("authority_result"))
        and not missing
        and "REPORT_ONLY_ACTIVE_REPLAY_INPUT_CREATION" in scope
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
    )
    return [
        _authority(
            "active_input_creation_authority",
            "PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED,
            passed,
            "" if passed else "Active input creation authority is incomplete or overbroad.",
            settings.active_input_authority_manifest_path,
            "missing=" + ",".join(missing) if missing else scope,
        )
    ]


def _check_attestation(settings: ActiveReplayInputCreateSettings) -> list[ActiveReplayInputCreateAttestationResult]:
    payload = _read_json(settings.second_reviewer_attestation_manifest_path)
    missing = _missing_true_fields(payload, ATTESTATION_TRUE_FIELDS)
    passed = _path_exists(settings.second_reviewer_attestation_manifest_path) and not missing
    return [
        ActiveReplayInputCreateAttestationResult(
            gate_group="second_reviewer_attestation",
            gate_name="required_attestations",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Second reviewer active-input creation attestations are incomplete.",
            evidence_path=_path_str(settings.second_reviewer_attestation_manifest_path),
            observed_value=missing,
        )
    ]


def _check_pit_source_evidence(
    settings: ActiveReplayInputCreateSettings,
) -> list[ActiveReplayInputCreatePitSourceEvidenceResult]:
    payload = _read_json(settings.pit_source_evidence_bundle_path)
    if not _path_exists(settings.pit_source_evidence_bundle_path):
        return [
            _pit_source(
                "pit_source_evidence_bundle_present",
                ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
                False,
                "PIT/source evidence bundle is missing.",
                settings.pit_source_evidence_bundle_path,
            )
        ]
    pit_missing = _missing_true_fields(payload, PIT_TRUE_FIELDS)
    source_missing = _missing_true_fields(payload, SOURCE_TRUE_FIELDS)
    evidence_missing = _missing_true_fields(payload, EVIDENCE_TRUE_FIELDS)
    return [
        _pit_source(
            "pit_universe_evidence",
            "PASS" if not pit_missing else ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
            not pit_missing,
            "" if not pit_missing else "PIT universe evidence is incomplete.",
            settings.pit_source_evidence_bundle_path,
            pit_missing,
        ),
        _pit_source(
            "source_registry_evidence",
            "PASS" if not source_missing else ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
            not source_missing,
            "" if not source_missing else "Source registry or source coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            source_missing,
        ),
        _pit_source(
            "raw_document_evidence_bundle",
            "PASS" if not evidence_missing else ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
            not evidence_missing,
            "" if not evidence_missing else "Raw document or evidence bundle coverage is incomplete.",
            settings.pit_source_evidence_bundle_path,
            evidence_missing,
        ),
    ]


def _check_taxonomy(settings: ActiveReplayInputCreateSettings) -> list[ActiveReplayInputCreateTaxonomyResult]:
    payload = _read_json(settings.taxonomy_evidence_bundle_path)
    missing = _missing_true_fields(payload, TAXONOMY_TRUE_FIELDS)
    passed = _path_exists(settings.taxonomy_evidence_bundle_path) and not missing
    return [
        ActiveReplayInputCreateTaxonomyResult(
            gate_group="taxonomy_evidence",
            gate_name="eight_layer_taxonomy_coverage",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "8-layer taxonomy evidence is missing or incomplete.",
            evidence_path=_path_str(settings.taxonomy_evidence_bundle_path),
            observed_value=missing,
        )
    ]


def _check_source_hash_revision_available_time(
    settings: ActiveReplayInputCreateSettings,
) -> list[ActiveReplayInputCreatePitSourceEvidenceResult]:
    payload = _read_json(settings.source_hash_revision_available_time_evidence_path)
    missing = _missing_true_fields(payload, SOURCE_HASH_TRUE_FIELDS)
    passed = _path_exists(settings.source_hash_revision_available_time_evidence_path) and not missing
    return [
        _pit_source(
            "source_hash_revision_available_time",
            "PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
            passed,
            "" if passed else "Source hash, revision_id, or available_time evidence is incomplete.",
            settings.source_hash_revision_available_time_evidence_path,
            missing,
        )
    ]


def _check_leakage_side_effect(
    settings: ActiveReplayInputCreateSettings,
) -> list[ActiveReplayInputCreateLeakageSideEffectResult]:
    payload = _read_json(settings.leakage_side_effect_evidence_bundle_path)
    if not _path_exists(settings.leakage_side_effect_evidence_bundle_path):
        return [
            _leakage(
                "leakage_side_effect_bundle_present",
                ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
                False,
                "Leakage/side-effect evidence bundle is missing.",
                settings.leakage_side_effect_evidence_bundle_path,
            )
        ]
    leakage_missing = _missing_true_fields(payload, LEAKAGE_TRUE_FIELDS)
    side_missing = _missing_true_fields(payload, SIDE_EFFECT_TRUE_FIELDS)
    return [
        _leakage(
            "leakage_checks",
            "PASS" if not leakage_missing else ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED,
            not leakage_missing,
            "" if not leakage_missing else "Leakage exclusion evidence is incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            leakage_missing,
        ),
        _leakage(
            "side_effect_checks",
            "PASS" if not side_missing else ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED,
            not side_missing,
            "" if not side_missing else "Side-effect exclusion evidence is incomplete.",
            settings.leakage_side_effect_evidence_bundle_path,
            side_missing,
        ),
    ]


def _check_overclaim(settings: ActiveReplayInputCreateSettings) -> list[ActiveReplayInputCreateOverclaimResult]:
    payload = _read_json(settings.overclaim_evidence_bundle_path)
    missing = _missing_true_fields(payload, OVERCLAIM_TRUE_FIELDS)
    passed = _path_exists(settings.overclaim_evidence_bundle_path) and not missing
    return [
        ActiveReplayInputCreateOverclaimResult(
            gate_group="overclaim_guard",
            gate_name="active_input_boundary_guards",
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "Overclaim guard evidence is incomplete.",
            evidence_path=_path_str(settings.overclaim_evidence_bundle_path),
            observed_value=missing,
        )
    ]


def _check_candidate_manifest(
    settings: ActiveReplayInputCreateSettings,
    payload: dict[str, Any],
) -> list[ActiveReplayInputCreatePitSourceEvidenceResult]:
    required_fields = [
        "source_marker_run_id",
        "source_marker_artifact_path",
        "marker_status",
        "marker_file_exists",
        "active_replay_input_ready_marker_emitted",
        "marker_only_semantics_confirmed",
        "replay_as_of_date",
        "replay_calendar",
        "symbol_universe_ref",
        "pit_universe_ref",
        "source_registry_ref",
        "raw_document_store_ref",
        "factor_definition_ref",
        "factor_observation_ref",
        "event_structured_ref",
        "company_exposure_ref",
        "evidence_bundle_ref",
        "source_hash_coverage",
        "revision_id_coverage",
        "available_time_policy",
        "taxonomy_coverage",
        "leakage_check_status",
        "side_effect_check_status",
    ]
    missing = [field for field in required_fields if not _text(payload.get(field))]
    bool_failures = [
        field
        for field in ["marker_file_exists", "active_replay_input_ready_marker_emitted", "marker_only_semantics_confirmed"]
        if not _to_bool(payload.get(field))
    ]
    status_failures = []
    if _text(payload.get("marker_status")) != ACTIVE_REPLAY_INPUT_READY:
        status_failures.append("marker_status")
    if _text(payload.get("leakage_check_status")) != "PASS":
        status_failures.append("leakage_check_status")
    if _text(payload.get("side_effect_check_status")) != "PASS":
        status_failures.append("side_effect_check_status")
    passed = (
        _path_exists(settings.active_replay_input_candidate_manifest_path)
        and not missing
        and not bool_failures
        and not status_failures
        and _to_bool(payload.get("report_only"))
        and _to_bool(payload.get("diagnostic_only"))
    )
    observed = ",".join(missing + bool_failures + status_failures)
    return [
        _pit_source(
            "active_replay_input_candidate_manifest",
            "PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
            passed,
            "" if passed else "Active replay input candidate manifest is incomplete.",
            settings.active_replay_input_candidate_manifest_path,
            observed,
        )
    ]


def _check_false_fields(
    payloads: list[dict[str, Any]], fields: list[str], failure_status: str
) -> list[ActiveReplayInputCreateLeakageSideEffectResult]:
    results: list[ActiveReplayInputCreateLeakageSideEffectResult] = []
    for field in fields:
        offenders = [payload for payload in payloads if _to_bool(payload.get(field))]
        passed = not offenders
        results.append(
            ActiveReplayInputCreateLeakageSideEffectResult(
                gate_group="false_field_guard",
                gate_name=field,
                status="PASS" if passed else failure_status,
                passed=passed,
                blocker_reason="" if passed else f"{field} must remain false for active input creation.",
                evidence_path="input_payloads",
                observed_value=str(bool(offenders)),
            )
        )
    return results


def _built_in_overclaim_guards(output_dir: Path) -> list[ActiveReplayInputCreateOverclaimResult]:
    manual_path_ok = "manual_diagnostics" in output_dir.parts
    guards = [
        (
            "output_path_under_manual_diagnostics",
            manual_path_ok,
            "Output path must remain under outputs/reports/manual_diagnostics.",
        ),
        (
            "active_input_not_replay",
            True,
            "Active input is not replay execution.",
        ),
        (
            "active_input_not_trading",
            True,
            "Active input is not trading authorization.",
        ),
    ]
    return [
        ActiveReplayInputCreateOverclaimResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status="PASS" if passed else ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED,
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
    precondition_results: list[ActiveReplayInputCreatePreconditionResult],
    lineage_results: list[ActiveReplayInputCreateLineageResult],
    authority_results: list[ActiveReplayInputCreateAuthorityResult],
    attestation_results: list[ActiveReplayInputCreateAttestationResult],
    pit_source_results: list[ActiveReplayInputCreatePitSourceEvidenceResult],
    taxonomy_results: list[ActiveReplayInputCreateTaxonomyResult],
    leakage_side_effect_results: list[ActiveReplayInputCreateLeakageSideEffectResult],
    overclaim_results: list[ActiveReplayInputCreateOverclaimResult],
) -> str:
    if not has_input:
        return NO_ACTIVE_REPLAY_INPUT_CREATION_INPUT
    ordered_groups: list[tuple[list[Any], list[str]]] = [
        (lineage_results, [ACTIVE_REPLAY_INPUT_CREATION_LINEAGE_BLOCKED]),
        (precondition_results, [ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED]),
        (
            authority_results,
            [ACTIVE_REPLAY_INPUT_CREATION_REVIEW_BLOCKED, ACTIVE_REPLAY_INPUT_CREATION_AUTHORITY_BLOCKED],
        ),
        (attestation_results, [ACTIVE_REPLAY_INPUT_CREATION_ATTESTATION_BLOCKED]),
        (
            pit_source_results,
            [
                ACTIVE_REPLAY_INPUT_CREATION_PIT_BLOCKED,
                ACTIVE_REPLAY_INPUT_CREATION_SOURCE_BLOCKED,
                ACTIVE_REPLAY_INPUT_CREATION_EVIDENCE_BLOCKED,
            ],
        ),
        (taxonomy_results, [ACTIVE_REPLAY_INPUT_CREATION_TAXONOMY_BLOCKED]),
        (
            leakage_side_effect_results,
            [ACTIVE_REPLAY_INPUT_CREATION_LEAKAGE_BLOCKED, ACTIVE_REPLAY_INPUT_CREATION_SIDE_EFFECT_BLOCKED],
        ),
        (overclaim_results, [ACTIVE_REPLAY_INPUT_CREATION_OVERCLAIM_BLOCKED]),
    ]
    for rows, statuses in ordered_groups:
        for status in statuses:
            if any(not row.passed and row.status == status for row in rows):
                return status
    return READY_FOR_ACTIVE_REPLAY_INPUT_CREATION


def _metadata(result: ActiveReplayInputCreateResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    return payload


def _active_replay_input_payload(
    result: ActiveReplayInputCreateResult,
    marker_payload: dict[str, Any],
    candidate_payload: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "active_replay_input_id": result.active_replay_input_id,
        "active_input_creation_run_id": result.active_input_creation_run_id,
        "created_at": result.generated_at,
        "input_status": result.status,
        "source_marker_run_id": _text(
            candidate_payload.get("source_marker_run_id") or marker_payload.get("actual_emission_run_id")
        ),
        "source_marker_artifact_path": _text(
            candidate_payload.get("source_marker_artifact_path") or result.marker_artifact_path
        ),
        "marker_status": _text(candidate_payload.get("marker_status") or marker_payload.get("marker_status")),
        "marker_file_exists": _to_bool(candidate_payload.get("marker_file_exists"))
        or bool(result.marker_artifact_path),
        "active_replay_input_ready_marker_emitted": _to_bool(
            candidate_payload.get("active_replay_input_ready_marker_emitted")
            or marker_payload.get("active_replay_input_ready_marker_emitted")
        ),
        "marker_only_semantics_confirmed": _to_bool(
            candidate_payload.get("marker_only_semantics_confirmed")
            or marker_payload.get("marker_only_semantics_confirmed")
        ),
        "replay_as_of_date": _text(candidate_payload.get("replay_as_of_date")),
        "replay_calendar": _text(candidate_payload.get("replay_calendar")),
        "symbol_universe_ref": _text(candidate_payload.get("symbol_universe_ref")),
        "pit_universe_ref": _text(candidate_payload.get("pit_universe_ref")),
        "source_registry_ref": _text(candidate_payload.get("source_registry_ref")),
        "raw_document_store_ref": _text(candidate_payload.get("raw_document_store_ref")),
        "factor_definition_ref": _text(candidate_payload.get("factor_definition_ref")),
        "factor_observation_ref": _text(candidate_payload.get("factor_observation_ref")),
        "event_structured_ref": _text(candidate_payload.get("event_structured_ref")),
        "company_exposure_ref": _text(candidate_payload.get("company_exposure_ref")),
        "evidence_bundle_ref": _text(candidate_payload.get("evidence_bundle_ref")),
        "source_hash_coverage": _text(candidate_payload.get("source_hash_coverage")),
        "revision_id_coverage": _text(candidate_payload.get("revision_id_coverage")),
        "available_time_policy": _text(candidate_payload.get("available_time_policy")),
        "taxonomy_coverage": _text(candidate_payload.get("taxonomy_coverage")),
        "leakage_check_status": _text(candidate_payload.get("leakage_check_status")),
        "side_effect_check_status": _text(candidate_payload.get("side_effect_check_status")),
        "active_replay_input_created": result.active_replay_input_created,
        "active_replay_input": result.active_replay_input,
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
            "Report-only active replay input is not replay execution, not replay decisions, "
            "not forward labels, not training, not stock_profile, not buy-review, and not trading."
        ),
    }
    if not candidate_payload:
        payload["input_status"] = result.status
        payload["marker_file_exists"] = bool(result.marker_artifact_path)
    return payload


def _render_report(result: ActiveReplayInputCreateResult) -> str:
    return "\n".join(
        [
            "# Active Replay Input Creation Report",
            "",
            f"- active_input_creation_run_id: `{result.active_input_creation_run_id}`",
            f"- status: `{result.status}`",
            f"- workflow_stage: `{result.workflow_stage}`",
            f"- active_replay_input_created: `{result.active_replay_input_created}`",
            f"- active_replay_input: `{result.active_replay_input}`",
            f"- blocker_count: `{result.blocker_count}`",
            "",
            "This artifact is report-only. A created active replay input means only that a governed input "
            "package exists for a future separate replay execution workflow.",
            "",
            "It is not replay execution, not replay decisions, not forward labels, not training, "
            "not stock_profile, not buy-review, not paper approval, not performance validation, "
            "not broker integration, not orders, not messages, and not trading.",
            "",
            "Replay execution, replay decisions, forward labels, training, stock profiles, buy-review "
            "eligibility, and trading remain separate future stages.",
        ]
    )


def _render_next_task(result: ActiveReplayInputCreateResult) -> str:
    if result.status == ACTIVE_REPLAY_INPUT_CREATED:
        return (
            "# Recommended Next Task\n\n"
            "Add Active Replay Input Creation artifact views report-only v0.1. Implement index, health, "
            "and status only after preserving the no replay, no replay decisions, no labels, no training, "
            "no stock_profile, no buy-review, and no trading boundary.\n"
        )
    if result.status == READY_FOR_ACTIVE_REPLAY_INPUT_CREATION:
        return (
            "# Recommended Next Task\n\n"
            "Run `active-replay-input-create` with `--allow-active-replay-input-creation` only if explicit "
            "report-only active input artifact creation is intended. Do not run replay.\n"
        )
    return (
        "# Recommended Next Task\n\n"
        "Complete the blocked active replay input creation evidence gates. Do not run replay, create "
        "replay decisions, compute labels, train weights, create stock profiles, or authorize trading.\n"
    )


def _write_frame(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([asdict(row) for row in rows]).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_run_id(settings: ActiveReplayInputCreateSettings, generated_at: str) -> str:
    payload = {
        "generated_at": generated_at,
        "marker_artifact_path": _path_str(settings.marker_artifact_path),
        "candidate_path": _path_str(settings.active_replay_input_candidate_manifest_path),
        "allow": settings.allow_active_replay_input_creation,
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
) -> ActiveReplayInputCreateLineageResult:
    return ActiveReplayInputCreateLineageResult(
        gate_group="marker_only_active_replay_input_ready_lineage",
        gate_name=gate_name,
        status=status,
        passed=passed,
        blocker_reason=blocker_reason,
        evidence_path=_path_str(evidence_path),
        observed_value=observed_value,
    )


def _authority(
    gate_name: str,
    status: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: Path | None,
    observed_value: str = "",
) -> ActiveReplayInputCreateAuthorityResult:
    return ActiveReplayInputCreateAuthorityResult(
        gate_group="active_input_creation_authority",
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
) -> ActiveReplayInputCreatePitSourceEvidenceResult:
    return ActiveReplayInputCreatePitSourceEvidenceResult(
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
) -> ActiveReplayInputCreateLeakageSideEffectResult:
    return ActiveReplayInputCreateLeakageSideEffectResult(
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


def _passish(value: Any) -> bool:
    return _text(value).upper() in PASS_RESULTS


def _missing_true_fields(payload: dict[str, Any], fields: list[str]) -> str:
    return ",".join(field for field in fields if not _to_bool(payload.get(field)))


def _passed(rows: list[Any]) -> int:
    return sum(1 for row in rows if row.passed)


def _blocked(rows: list[Any]) -> int:
    return sum(1 for row in rows if not row.passed)


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if "manual_diagnostics" not in path.parts:
        raise ValueError("Active replay input creation artifacts must be written under manual_diagnostics.")
