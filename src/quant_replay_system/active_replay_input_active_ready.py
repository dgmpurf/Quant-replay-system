"""Report-only active replay input active-ready governance workflow.

This workflow deliberately stops at ``ACTIVE_READY_READY_FOR_FINAL_REVIEW``.
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


NO_ACTIVE_READY_INPUT = "NO_ACTIVE_READY_INPUT"
ACTIVE_READY_INPUT_FOUND = "ACTIVE_READY_INPUT_FOUND"
ACTIVE_READY_AUTHORITY_BLOCKED = "ACTIVE_READY_AUTHORITY_BLOCKED"
ACTIVE_READY_LINEAGE_BLOCKED = "ACTIVE_READY_LINEAGE_BLOCKED"
ACTIVE_READY_PIT_BLOCKED = "ACTIVE_READY_PIT_BLOCKED"
ACTIVE_READY_SOURCE_BLOCKED = "ACTIVE_READY_SOURCE_BLOCKED"
ACTIVE_READY_EVIDENCE_BLOCKED = "ACTIVE_READY_EVIDENCE_BLOCKED"
ACTIVE_READY_TAXONOMY_BLOCKED = "ACTIVE_READY_TAXONOMY_BLOCKED"
ACTIVE_READY_LEAKAGE_BLOCKED = "ACTIVE_READY_LEAKAGE_BLOCKED"
ACTIVE_READY_SIDE_EFFECT_BLOCKED = "ACTIVE_READY_SIDE_EFFECT_BLOCKED"
ACTIVE_READY_REVIEW_BLOCKED = "ACTIVE_READY_REVIEW_BLOCKED"
ACTIVE_READY_READY_FOR_FINAL_REVIEW = "ACTIVE_READY_READY_FOR_FINAL_REVIEW"
FORBIDDEN_ACTIVE_READY_STATUS = "ACTIVE_REPLAY_INPUT_READY"

ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW = "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"
DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_active_ready_v0_1")
PASS_RESULTS = {"PASS", "ACCEPTED", "ACCEPTED_FOR_REVIEW_ONLY", "READY_FOR_FINAL_REVIEW"}

LEAKAGE_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_ready_emitted",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
]
SIDE_EFFECT_FALSE_FIELDS = [
    "active_replay_input",
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
REQUEST_SAFE_FALSE_FIELDS = LEAKAGE_FALSE_FIELDS + SIDE_EFFECT_FALSE_FIELDS

AUTHORITY_FIELDS = [
    "primary_approver",
    "second_approver",
    "pit_reviewer",
    "source_reviewer",
    "evidence_reviewer",
    "risk_compliance_reviewer",
    "strategy_owner",
    "authority_scope",
]
PIT_TRUE_FIELDS = [
    "available_time_coverage_complete",
    "universe_coverage_complete",
    "suspension_st_delist_coverage_complete",
    "corporate_action_policy_reviewed",
    "report_only",
    "diagnostic_only",
]
SOURCE_TRUE_FIELDS = [
    "source_id_coverage_complete",
    "source_hash_coverage_complete",
    "revision_id_coverage_complete",
    "permission_class_coverage_complete",
    "quality_status_coverage_complete",
    "report_only",
    "diagnostic_only",
]
EVIDENCE_TRUE_FIELDS = [
    "raw_evidence_refs_complete",
    "replay_evidence_bundle_complete",
    "factor_definition_coverage_complete",
    "factor_observation_coverage_complete",
    "event_structured_coverage_complete",
    "company_exposure_coverage_complete",
    "report_only",
    "diagnostic_only",
]
TAXONOMY_TRUE_FIELDS = [
    "uses_8_layer_taxonomy",
    "not_fixed_12_only",
    "factor_layer_metadata_complete",
    "trade_usage_metadata_complete",
    "compliance_metadata_complete",
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
    "report_only",
    "diagnostic_only",
]
SIDE_EFFECT_TRUE_FIELDS = [
    "no_approval_applied",
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
    "no_signal_semantics_changed",
    "report_only",
    "diagnostic_only",
]
OVERCLAIM_TRUE_FIELDS = [
    "pass_candidate_not_active_ready",
    "smoke_not_active_ready",
    "promotion_not_active_ready",
    "acceptance_not_active_ready",
    "final_review_not_active_ready",
    "active_ready_not_replay",
    "active_ready_not_labels",
    "active_ready_not_training",
    "active_ready_not_stock_profile",
    "active_ready_not_buy_review",
    "active_ready_not_trading",
    "active_ready_not_performance_validation",
    "report_only",
    "diagnostic_only",
]


@dataclass(frozen=True)
class ActiveReplayInputActiveReadySettings:
    acceptance_artifact: Path | None = None
    acceptance_health_artifact: Path | None = None
    acceptance_status_artifact: Path | None = None
    active_ready_request_manifest: Path | None = None
    active_ready_authority_manifest: Path | None = None
    pit_coverage_manifest: Path | None = None
    source_coverage_manifest: Path | None = None
    evidence_coverage_manifest: Path | None = None
    taxonomy_compliance_manifest: Path | None = None
    leakage_review_manifest: Path | None = None
    side_effect_review_manifest: Path | None = None
    overclaim_review_manifest: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyPreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyAuthorityResult:
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyLineageResult:
    artifact_type: str
    artifact_path: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str = ""


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyPitCoverageResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadySourceCoverageResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyEvidenceCoverageResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyTaxonomyResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyLeakageResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadySideEffectResult(ActiveReplayInputActiveReadyPreconditionResult):
    pass


@dataclass(frozen=True)
class ActiveReplayInputActiveReadyResult:
    active_ready_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActiveReplayInputActiveReadyPreconditionResult]
    authority_results: list[ActiveReplayInputActiveReadyAuthorityResult]
    lineage_results: list[ActiveReplayInputActiveReadyLineageResult]
    pit_coverage_results: list[ActiveReplayInputActiveReadyPitCoverageResult]
    source_coverage_results: list[ActiveReplayInputActiveReadySourceCoverageResult]
    evidence_coverage_results: list[ActiveReplayInputActiveReadyEvidenceCoverageResult]
    taxonomy_results: list[ActiveReplayInputActiveReadyTaxonomyResult]
    leakage_results: list[ActiveReplayInputActiveReadyLeakageResult]
    side_effect_results: list[ActiveReplayInputActiveReadySideEffectResult]
    overclaim_guard_results: list[ActiveReplayInputActiveReadyPreconditionResult]
    acceptance_artifact_path: str
    acceptance_health_artifact_path: str
    acceptance_status_artifact_path: str
    active_ready_request_manifest_path: str
    active_ready_authority_manifest_path: str
    pit_coverage_manifest_path: str
    source_coverage_manifest_path: str
    evidence_coverage_manifest_path: str
    taxonomy_compliance_manifest_path: str
    leakage_review_manifest_path: str
    side_effect_review_manifest_path: str
    overclaim_review_manifest_path: str
    precondition_count: int
    passed_precondition_count: int
    blocked_precondition_count: int
    authority_gate_count: int
    passed_authority_gate_count: int
    blocked_authority_gate_count: int
    lineage_gate_count: int
    passed_lineage_gate_count: int
    blocked_lineage_gate_count: int
    pit_coverage_gate_count: int
    passed_pit_coverage_gate_count: int
    blocked_pit_coverage_gate_count: int
    source_coverage_gate_count: int
    passed_source_coverage_gate_count: int
    blocked_source_coverage_gate_count: int
    evidence_coverage_gate_count: int
    passed_evidence_coverage_gate_count: int
    blocked_evidence_coverage_gate_count: int
    taxonomy_gate_count: int
    passed_taxonomy_gate_count: int
    blocked_taxonomy_gate_count: int
    issue_count: int
    blocker_count: int
    warning_count: int
    ready_for_final_review: bool
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


def run_active_replay_input_active_ready(
    settings: ActiveReplayInputActiveReadySettings | None = None,
) -> ActiveReplayInputActiveReadyResult:
    settings = settings or ActiveReplayInputActiveReadySettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    run_id = _build_run_id(settings=settings, generated_at=generated_at)
    artifact_path = settings.output_dir / run_id

    has_input = any(
        [
            settings.acceptance_artifact,
            settings.acceptance_health_artifact,
            settings.acceptance_status_artifact,
            settings.active_ready_request_manifest,
            settings.active_ready_authority_manifest,
            settings.pit_coverage_manifest,
            settings.source_coverage_manifest,
            settings.evidence_coverage_manifest,
            settings.taxonomy_compliance_manifest,
            settings.leakage_review_manifest,
            settings.side_effect_review_manifest,
            settings.overclaim_review_manifest,
        ]
    )

    precondition_results = [
        ActiveReplayInputActiveReadyPreconditionResult(
            gate_group="active_ready_input",
            gate_name="input_manifest_present",
            status=ACTIVE_READY_INPUT_FOUND if has_input else NO_ACTIVE_READY_INPUT,
            passed=has_input,
            blocker_reason="" if has_input else "No active-ready governance input was supplied.",
            evidence_path="",
            observed_value=str(has_input),
        )
    ]

    lineage_results, acceptance_payload = _check_acceptance_lineage(settings)
    request_results, request_payload = _check_active_ready_request(settings)
    authority_results = _check_authority(settings)
    pit_results = _check_boolean_manifest(
        settings.pit_coverage_manifest,
        "pit_coverage",
        PIT_TRUE_FIELDS,
        "pit_result",
        ACTIVE_READY_PIT_BLOCKED,
        ActiveReplayInputActiveReadyPitCoverageResult,
    )
    source_results = _check_boolean_manifest(
        settings.source_coverage_manifest,
        "source_coverage",
        SOURCE_TRUE_FIELDS,
        "source_result",
        ACTIVE_READY_SOURCE_BLOCKED,
        ActiveReplayInputActiveReadySourceCoverageResult,
    )
    evidence_results = _check_boolean_manifest(
        settings.evidence_coverage_manifest,
        "evidence_coverage",
        EVIDENCE_TRUE_FIELDS,
        "evidence_result",
        ACTIVE_READY_EVIDENCE_BLOCKED,
        ActiveReplayInputActiveReadyEvidenceCoverageResult,
    )
    taxonomy_results = _check_boolean_manifest(
        settings.taxonomy_compliance_manifest,
        "taxonomy_compliance",
        TAXONOMY_TRUE_FIELDS,
        "taxonomy_result",
        ACTIVE_READY_TAXONOMY_BLOCKED,
        ActiveReplayInputActiveReadyTaxonomyResult,
    )
    leakage_results = _check_boolean_manifest(
        settings.leakage_review_manifest,
        "leakage_review",
        LEAKAGE_TRUE_FIELDS,
        "leakage_result",
        ACTIVE_READY_LEAKAGE_BLOCKED,
        ActiveReplayInputActiveReadyLeakageResult,
    )
    side_effect_results = _check_boolean_manifest(
        settings.side_effect_review_manifest,
        "side_effect_review",
        SIDE_EFFECT_TRUE_FIELDS,
        "side_effect_result",
        ACTIVE_READY_SIDE_EFFECT_BLOCKED,
        ActiveReplayInputActiveReadySideEffectResult,
    )
    overclaim_results = _check_boolean_manifest(
        settings.overclaim_review_manifest,
        "overclaim_review",
        OVERCLAIM_TRUE_FIELDS,
        "overclaim_result",
        ACTIVE_READY_REVIEW_BLOCKED,
        ActiveReplayInputActiveReadyPreconditionResult,
    )
    overclaim_results.extend(_built_in_overclaim_guards(settings.output_dir))

    safety_payloads = [acceptance_payload, request_payload]
    leakage_results.extend(_check_false_fields(safety_payloads, LEAKAGE_FALSE_FIELDS, ACTIVE_READY_LEAKAGE_BLOCKED))
    side_effect_results.extend(
        _check_false_fields(safety_payloads, SIDE_EFFECT_FALSE_FIELDS, ACTIVE_READY_SIDE_EFFECT_BLOCKED)
    )

    status = _resolve_status(
        has_input=has_input,
        lineage_results=lineage_results,
        authority_results=[*request_results, *authority_results],
        pit_results=pit_results,
        source_results=source_results,
        evidence_results=evidence_results,
        taxonomy_results=taxonomy_results,
        leakage_results=leakage_results,
        side_effect_results=side_effect_results,
        overclaim_results=overclaim_results,
    )
    ready_for_final_review = status == ACTIVE_READY_READY_FOR_FINAL_REVIEW

    authority_all = [*request_results, *authority_results]
    blockers = _blocked(precondition_results) + _blocked(lineage_results) + _blocked(authority_all)
    blockers += _blocked(pit_results) + _blocked(source_results) + _blocked(evidence_results)
    blockers += _blocked(taxonomy_results) + _blocked(leakage_results) + _blocked(side_effect_results)
    blockers += _blocked(overclaim_results)

    result = ActiveReplayInputActiveReadyResult(
        active_ready_run_id=run_id,
        generated_at=generated_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=status,
        precondition_results=precondition_results,
        authority_results=authority_all,
        lineage_results=lineage_results,
        pit_coverage_results=pit_results,
        source_coverage_results=source_results,
        evidence_coverage_results=evidence_results,
        taxonomy_results=taxonomy_results,
        leakage_results=leakage_results,
        side_effect_results=side_effect_results,
        overclaim_guard_results=overclaim_results,
        acceptance_artifact_path=_path_str(settings.acceptance_artifact),
        acceptance_health_artifact_path=_path_str(settings.acceptance_health_artifact),
        acceptance_status_artifact_path=_path_str(settings.acceptance_status_artifact),
        active_ready_request_manifest_path=_path_str(settings.active_ready_request_manifest),
        active_ready_authority_manifest_path=_path_str(settings.active_ready_authority_manifest),
        pit_coverage_manifest_path=_path_str(settings.pit_coverage_manifest),
        source_coverage_manifest_path=_path_str(settings.source_coverage_manifest),
        evidence_coverage_manifest_path=_path_str(settings.evidence_coverage_manifest),
        taxonomy_compliance_manifest_path=_path_str(settings.taxonomy_compliance_manifest),
        leakage_review_manifest_path=_path_str(settings.leakage_review_manifest),
        side_effect_review_manifest_path=_path_str(settings.side_effect_review_manifest),
        overclaim_review_manifest_path=_path_str(settings.overclaim_review_manifest),
        precondition_count=len(precondition_results),
        passed_precondition_count=_passed(precondition_results),
        blocked_precondition_count=_blocked(precondition_results),
        authority_gate_count=len(authority_all),
        passed_authority_gate_count=_passed(authority_all),
        blocked_authority_gate_count=_blocked(authority_all),
        lineage_gate_count=len(lineage_results),
        passed_lineage_gate_count=_passed(lineage_results),
        blocked_lineage_gate_count=_blocked(lineage_results),
        pit_coverage_gate_count=len(pit_results),
        passed_pit_coverage_gate_count=_passed(pit_results),
        blocked_pit_coverage_gate_count=_blocked(pit_results),
        source_coverage_gate_count=len(source_results),
        passed_source_coverage_gate_count=_passed(source_results),
        blocked_source_coverage_gate_count=_blocked(source_results),
        evidence_coverage_gate_count=len(evidence_results),
        passed_evidence_coverage_gate_count=_passed(evidence_results),
        blocked_evidence_coverage_gate_count=_blocked(evidence_results),
        taxonomy_gate_count=len(taxonomy_results),
        passed_taxonomy_gate_count=_passed(taxonomy_results),
        blocked_taxonomy_gate_count=_blocked(taxonomy_results),
        issue_count=blockers,
        blocker_count=blockers,
        warning_count=0,
        ready_for_final_review=ready_for_final_review,
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
        artifact_paths=resolve_active_replay_input_active_ready_paths(artifact_path),
    )
    if settings.write_artifacts:
        write_active_replay_input_active_ready_artifacts(result)
    return result


def resolve_active_replay_input_active_ready_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "metadata": artifact_path / "active_ready_metadata.json",
        "active_ready_report": artifact_path / "active_ready_report.md",
        "active_ready_precondition_results": artifact_path / "active_ready_precondition_results.csv",
        "authority_review_results": artifact_path / "authority_review_results.csv",
        "acceptance_lineage_results": artifact_path / "acceptance_lineage_results.csv",
        "pit_coverage_results": artifact_path / "pit_coverage_results.csv",
        "source_coverage_results": artifact_path / "source_coverage_results.csv",
        "evidence_coverage_results": artifact_path / "evidence_coverage_results.csv",
        "taxonomy_compliance_results": artifact_path / "taxonomy_compliance_results.csv",
        "leakage_guard_results": artifact_path / "leakage_guard_results.csv",
        "side_effect_guard_results": artifact_path / "side_effect_guard_results.csv",
        "overclaim_guard_report": artifact_path / "overclaim_guard_report.csv",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_active_ready_artifacts(result: ActiveReplayInputActiveReadyResult) -> None:
    _ensure_manual_diagnostics_path(result.artifact_path)
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_results(result.artifact_paths["active_ready_precondition_results"], result.precondition_results)
    _write_results(result.artifact_paths["authority_review_results"], result.authority_results)
    _write_results(result.artifact_paths["acceptance_lineage_results"], result.lineage_results)
    _write_results(result.artifact_paths["pit_coverage_results"], result.pit_coverage_results)
    _write_results(result.artifact_paths["source_coverage_results"], result.source_coverage_results)
    _write_results(result.artifact_paths["evidence_coverage_results"], result.evidence_coverage_results)
    _write_results(result.artifact_paths["taxonomy_compliance_results"], result.taxonomy_results)
    _write_results(result.artifact_paths["leakage_guard_results"], result.leakage_results)
    _write_results(result.artifact_paths["side_effect_guard_results"], result.side_effect_results)
    _write_results(result.artifact_paths["overclaim_guard_report"], result.overclaim_guard_results)
    result.artifact_paths["active_ready_report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_render_next_task(result), encoding="utf-8")


def _check_acceptance_lineage(
    settings: ActiveReplayInputActiveReadySettings,
) -> tuple[list[ActiveReplayInputActiveReadyLineageResult], dict[str, Any]]:
    results: list[ActiveReplayInputActiveReadyLineageResult] = []
    payload = _load_artifact_payload(settings.acceptance_artifact, "acceptance_metadata.json")
    if payload is None:
        results.append(
            ActiveReplayInputActiveReadyLineageResult(
                artifact_type="acceptance_artifact",
                artifact_path=_path_str(settings.acceptance_artifact),
                status=ACTIVE_READY_LINEAGE_BLOCKED,
                passed=False,
                blocker_reason="Acceptance artifact is missing or unreadable.",
            )
        )
        return results, {}

    results.append(
        _lineage_check(
            "acceptance_status",
            settings.acceptance_artifact,
            payload.get("status") == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW,
            f"status={payload.get('status')}",
            "Acceptance status is not ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW.",
        )
    )
    results.append(
        _lineage_check(
            "ready_for_active_ready_review",
            settings.acceptance_artifact,
            _as_bool(payload.get("ready_for_active_ready_review")),
            f"ready_for_active_ready_review={payload.get('ready_for_active_ready_review')}",
            "Acceptance artifact is not ready for active-ready review.",
        )
    )

    if settings.acceptance_health_artifact:
        health_payload = _read_json(settings.acceptance_health_artifact)
        results.append(
            _lineage_check(
                "acceptance_health",
                settings.acceptance_health_artifact,
                bool(health_payload) and health_payload.get("health_status") == "PASS",
                f"health_status={health_payload.get('health_status') if health_payload else ''}",
                "Acceptance health artifact is not PASS.",
            )
        )
    if settings.acceptance_status_artifact:
        status_payload = _read_json(settings.acceptance_status_artifact)
        results.append(
            _lineage_check(
                "acceptance_status_artifact",
                settings.acceptance_status_artifact,
                bool(status_payload)
                and status_payload.get("status") == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW
                and _as_bool(status_payload.get("ready_for_active_ready_review")),
                f"status={status_payload.get('status') if status_payload else ''}",
                "Acceptance status artifact is not ready for active-ready review.",
            )
        )
    return results, payload


def _check_active_ready_request(
    settings: ActiveReplayInputActiveReadySettings,
) -> tuple[list[ActiveReplayInputActiveReadyAuthorityResult], dict[str, Any]]:
    payload = _read_json(settings.active_ready_request_manifest)
    if not payload:
        return [
            ActiveReplayInputActiveReadyAuthorityResult(
                gate_name="active_ready_request_manifest",
                status=ACTIVE_READY_AUTHORITY_BLOCKED,
                passed=False,
                blocker_reason="Active-ready request manifest is missing or unreadable.",
                observed_value="",
            )
        ], {}

    results = [
        _authority_check(
            field,
            _present(payload.get(field)) if field not in {"report_only", "diagnostic_only"} else _as_bool(payload.get(field)),
            payload.get(field),
            "Active-ready request manifest is missing required request metadata.",
        )
        for field in ["active_ready_request_id", "requested_by", "requested_at", "request_reason", "report_only", "diagnostic_only"]
    ]
    results.extend(
        _authority_check(
            field,
            not _as_bool(payload.get(field)),
            payload.get(field),
            f"Active-ready request has unsafe flag {field}.",
            status=ACTIVE_READY_LEAKAGE_BLOCKED if field in LEAKAGE_FALSE_FIELDS else ACTIVE_READY_SIDE_EFFECT_BLOCKED,
        )
        for field in REQUEST_SAFE_FALSE_FIELDS
    )
    requested_status = payload.get("requested_status")
    results.append(
        _authority_check(
            "requested_status",
            requested_status == ACTIVE_READY_READY_FOR_FINAL_REVIEW,
            requested_status,
            "First implementation only allows ACTIVE_READY_READY_FOR_FINAL_REVIEW requests.",
            status=ACTIVE_READY_REVIEW_BLOCKED,
        )
    )
    return results, payload


def _check_authority(settings: ActiveReplayInputActiveReadySettings) -> list[ActiveReplayInputActiveReadyAuthorityResult]:
    payload = _read_json(settings.active_ready_authority_manifest)
    if not payload:
        return [
            ActiveReplayInputActiveReadyAuthorityResult(
                gate_name="active_ready_authority_manifest",
                status=ACTIVE_READY_AUTHORITY_BLOCKED,
                passed=False,
                blocker_reason="Active-ready authority manifest is missing or unreadable.",
                observed_value="",
            )
        ]
    results = [
        _authority_check(field, _present(payload.get(field)), payload.get(field), f"Missing authority field {field}.")
        for field in AUTHORITY_FIELDS
    ]
    results.append(
        _authority_check(
            "authority_result",
            str(payload.get("authority_result", "")).upper() in PASS_RESULTS,
            payload.get("authority_result"),
            "Authority result is not accepted for review-only governance.",
        )
    )
    results.append(
        _authority_check("report_only", _as_bool(payload.get("report_only")), payload.get("report_only"), "Authority is not report-only.")
    )
    results.append(
        _authority_check(
            "diagnostic_only",
            _as_bool(payload.get("diagnostic_only")),
            payload.get("diagnostic_only"),
            "Authority is not diagnostic-only.",
        )
    )
    return results


def _check_boolean_manifest(
    path: Path | None,
    gate_group: str,
    true_fields: list[str],
    result_field: str,
    failure_status: str,
    row_type: type[ActiveReplayInputActiveReadyPreconditionResult],
) -> list[Any]:
    payload = _read_json(path)
    if not payload:
        return [
            row_type(
                gate_group=gate_group,
                gate_name=f"{gate_group}_manifest",
                status=failure_status,
                passed=False,
                blocker_reason=f"{gate_group} manifest is missing or unreadable.",
                evidence_path=_path_str(path),
            )
        ]
    results = [
        row_type(
            gate_group=gate_group,
            gate_name=field,
            status=ACTIVE_READY_INPUT_FOUND if _as_bool(payload.get(field)) else failure_status,
            passed=_as_bool(payload.get(field)),
            blocker_reason="" if _as_bool(payload.get(field)) else f"{field} is not true.",
            evidence_path=_path_str(path),
            observed_value=str(payload.get(field)),
        )
        for field in true_fields
    ]
    result_value = str(payload.get(result_field, "")).upper()
    results.append(
        row_type(
            gate_group=gate_group,
            gate_name=result_field,
            status=ACTIVE_READY_INPUT_FOUND if result_value in PASS_RESULTS else failure_status,
            passed=result_value in PASS_RESULTS,
            blocker_reason="" if result_value in PASS_RESULTS else f"{result_field} is not PASS.",
            evidence_path=_path_str(path),
            observed_value=str(payload.get(result_field)),
        )
    )
    return results


def _check_false_fields(
    payloads: list[dict[str, Any]],
    fields: list[str],
    failure_status: str,
) -> list[ActiveReplayInputActiveReadyPreconditionResult]:
    results: list[ActiveReplayInputActiveReadyPreconditionResult] = []
    for payload in payloads:
        if not payload:
            continue
        source = str(payload.get("acceptance_run_id") or payload.get("active_ready_request_id") or "payload")
        for field in fields:
            if field in payload:
                safe = not _as_bool(payload.get(field))
                results.append(
                    ActiveReplayInputActiveReadyPreconditionResult(
                        gate_group="safety_flag",
                        gate_name=f"{source}:{field}",
                        status=ACTIVE_READY_INPUT_FOUND if safe else failure_status,
                        passed=safe,
                        blocker_reason="" if safe else f"Unsafe flag {field} is true.",
                        evidence_path=source,
                        observed_value=str(payload.get(field)),
                    )
                )
    return results


def _built_in_overclaim_guards(output_dir: Path) -> list[ActiveReplayInputActiveReadyPreconditionResult]:
    manual_diagnostics = Path("outputs/reports/manual_diagnostics")
    output_safe = _is_under(output_dir, manual_diagnostics)
    guards = [
        ("replay_pass_candidate_not_active_ready", True, "REPLAY_INPUT_GATE_PASS_CANDIDATE must not be active-ready."),
        ("smoke_pass_candidate_not_active_ready", True, "SMOKE_PASS_CANDIDATE_READY must not be active-ready."),
        ("promotion_ready_not_active_ready", True, "PROMOTION_READY_FOR_HUMAN_REVIEW must not be active-ready."),
        (
            "acceptance_ready_not_active_ready",
            True,
            "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW must not be active-ready.",
        ),
        ("final_review_not_active_ready", True, "ACTIVE_READY_READY_FOR_FINAL_REVIEW must not be active-ready."),
        ("forbidden_active_ready_not_emitted", True, "ACTIVE_REPLAY_INPUT_READY must not be emitted."),
        ("output_path_under_manual_diagnostics", output_safe, "Output path must stay under manual_diagnostics."),
    ]
    return [
        ActiveReplayInputActiveReadyPreconditionResult(
            gate_group="built_in_overclaim_guard",
            gate_name=name,
            status=ACTIVE_READY_INPUT_FOUND if passed else ACTIVE_READY_REVIEW_BLOCKED,
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
    lineage_results: list[ActiveReplayInputActiveReadyLineageResult],
    authority_results: list[ActiveReplayInputActiveReadyAuthorityResult],
    pit_results: list[Any],
    source_results: list[Any],
    evidence_results: list[Any],
    taxonomy_results: list[Any],
    leakage_results: list[Any],
    side_effect_results: list[Any],
    overclaim_results: list[Any],
) -> str:
    if not has_input:
        return NO_ACTIVE_READY_INPUT
    for status, rows in [
        (ACTIVE_READY_LINEAGE_BLOCKED, lineage_results),
        (ACTIVE_READY_AUTHORITY_BLOCKED, authority_results),
        (ACTIVE_READY_PIT_BLOCKED, pit_results),
        (ACTIVE_READY_SOURCE_BLOCKED, source_results),
        (ACTIVE_READY_EVIDENCE_BLOCKED, evidence_results),
        (ACTIVE_READY_TAXONOMY_BLOCKED, taxonomy_results),
        (ACTIVE_READY_LEAKAGE_BLOCKED, leakage_results),
        (ACTIVE_READY_SIDE_EFFECT_BLOCKED, side_effect_results),
        (ACTIVE_READY_REVIEW_BLOCKED, overclaim_results),
    ]:
        if _blocked(rows):
            if status == ACTIVE_READY_AUTHORITY_BLOCKED:
                row_statuses = {getattr(row, "status", "") for row in rows if not getattr(row, "passed", False)}
                if ACTIVE_READY_LEAKAGE_BLOCKED in row_statuses:
                    return ACTIVE_READY_LEAKAGE_BLOCKED
                if ACTIVE_READY_SIDE_EFFECT_BLOCKED in row_statuses:
                    return ACTIVE_READY_SIDE_EFFECT_BLOCKED
                if ACTIVE_READY_REVIEW_BLOCKED in row_statuses:
                    return ACTIVE_READY_REVIEW_BLOCKED
            return status
    return ACTIVE_READY_READY_FOR_FINAL_REVIEW


def _lineage_check(
    name: str,
    path: Path | None,
    passed: bool,
    observed_value: str,
    blocker_reason: str,
) -> ActiveReplayInputActiveReadyLineageResult:
    return ActiveReplayInputActiveReadyLineageResult(
        artifact_type=name,
        artifact_path=_path_str(path),
        status=ACTIVE_READY_INPUT_FOUND if passed else ACTIVE_READY_LINEAGE_BLOCKED,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        observed_value=observed_value,
    )


def _authority_check(
    name: str,
    passed: bool,
    observed_value: Any,
    blocker_reason: str,
    status: str = ACTIVE_READY_AUTHORITY_BLOCKED,
) -> ActiveReplayInputActiveReadyAuthorityResult:
    return ActiveReplayInputActiveReadyAuthorityResult(
        gate_name=name,
        status=ACTIVE_READY_INPUT_FOUND if passed else status,
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        observed_value=str(observed_value),
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


def _metadata(result: ActiveReplayInputActiveReadyResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["artifact_path"] = str(result.artifact_path)
    payload["artifact_paths"] = {key: str(value) for key, value in result.artifact_paths.items()}
    for key in [
        "precondition_results",
        "authority_results",
        "lineage_results",
        "pit_coverage_results",
        "source_coverage_results",
        "evidence_coverage_results",
        "taxonomy_results",
        "leakage_results",
        "side_effect_results",
        "overclaim_guard_results",
    ]:
        payload.pop(key, None)
    return payload


def _render_report(result: ActiveReplayInputActiveReadyResult) -> str:
    return "\n".join(
        [
            "# Active Replay Input Active-Ready Report",
            "",
            f"- active_ready_run_id: {result.active_ready_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- ready_for_final_review: {result.ready_for_final_review}",
            f"- blocker_count: {result.blocker_count}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- active_ready_emitted: {result.active_ready_emitted}",
            "",
            "This report is diagnostics-only. It does not emit ACTIVE_REPLAY_INPUT_READY, create active replay input, run replay, compute labels, train weights, create stock profiles, create buy-review eligibility, authorize trading, call APIs, write data stores, or mutate cache.",
        ]
    )


def _render_next_task(result: ActiveReplayInputActiveReadyResult) -> str:
    if result.ready_for_final_review:
        next_task = "Add Active Replay Input Active-Ready artifact views v0.1"
    else:
        next_task = "Resolve active-ready governance blockers and rerun report-only core workflow"
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
    records = [asdict(row) for row in rows]
    pd.DataFrame(records).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _build_run_id(settings: ActiveReplayInputActiveReadySettings, generated_at: str) -> str:
    parts = [
        generated_at,
        *[
            _path_str(path)
            for path in [
                settings.acceptance_artifact,
                settings.acceptance_health_artifact,
                settings.acceptance_status_artifact,
                settings.active_ready_request_manifest,
                settings.active_ready_authority_manifest,
                settings.pit_coverage_manifest,
                settings.source_coverage_manifest,
                settings.evidence_coverage_manifest,
                settings.taxonomy_compliance_manifest,
                settings.leakage_review_manifest,
                settings.side_effect_review_manifest,
                settings.overclaim_review_manifest,
            ]
        ],
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _ensure_manual_diagnostics_path(path: Path) -> None:
    if not _is_under(path, Path("outputs/reports/manual_diagnostics")):
        raise ValueError("Active-ready outputs must stay under outputs/reports/manual_diagnostics")


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        parts = [part.lower() for part in path.parts]
        expected = [part.lower() for part in parent.parts]
        if not expected:
            return False
        return any(parts[index : index + len(expected)] == expected for index in range(len(parts) - len(expected) + 1))


def _passed(rows: list[Any]) -> int:
    return sum(1 for row in rows if bool(getattr(row, "passed", False)))


def _blocked(rows: list[Any]) -> int:
    return sum(1 for row in rows if not bool(getattr(row, "passed", False)))


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
