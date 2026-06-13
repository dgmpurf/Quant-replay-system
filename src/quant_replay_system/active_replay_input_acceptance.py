"""Report-only active replay input acceptance workflow.

This workflow reviews a promotion-ready artifact and local reviewer manifests.
It is deliberately fail-closed and stops at
``ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW``; it never emits active-ready,
runs replay, computes labels, trains weights, creates stock profiles, changes
buy-review eligibility, writes data stores, calls APIs, or mutates cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_ACCEPTANCE_INPUT = "NO_ACCEPTANCE_INPUT"
ACCEPTANCE_INPUT_FOUND = "ACCEPTANCE_INPUT_FOUND"
ACCEPTANCE_REVIEW_BLOCKED = "ACCEPTANCE_REVIEW_BLOCKED"
ACCEPTANCE_AUTHORITY_BLOCKED = "ACCEPTANCE_AUTHORITY_BLOCKED"
ACCEPTANCE_ATTESTATION_BLOCKED = "ACCEPTANCE_ATTESTATION_BLOCKED"
ACCEPTANCE_SECOND_REVIEW_BLOCKED = "ACCEPTANCE_SECOND_REVIEW_BLOCKED"
ACCEPTANCE_RED_TEAM_BLOCKED = "ACCEPTANCE_RED_TEAM_BLOCKED"
ACCEPTANCE_LINEAGE_BLOCKED = "ACCEPTANCE_LINEAGE_BLOCKED"
ACCEPTANCE_PIT_BLOCKED = "ACCEPTANCE_PIT_BLOCKED"
ACCEPTANCE_SOURCE_BLOCKED = "ACCEPTANCE_SOURCE_BLOCKED"
ACCEPTANCE_EVIDENCE_BLOCKED = "ACCEPTANCE_EVIDENCE_BLOCKED"
ACCEPTANCE_LEAKAGE_BLOCKED = "ACCEPTANCE_LEAKAGE_BLOCKED"
ACCEPTANCE_SIDE_EFFECT_BLOCKED = "ACCEPTANCE_SIDE_EFFECT_BLOCKED"
ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW = "ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW"

DEFAULT_OUTPUT_DIR = Path("outputs/reports/manual_diagnostics/active_replay_input_acceptance_v0_1")
PROMOTION_READY_FOR_HUMAN_REVIEW = "PROMOTION_READY_FOR_HUMAN_REVIEW"
REVIEW_ONLY_RESULTS = {"ACCEPTED_FOR_REVIEW_ONLY", "ACCEPTED", "PASS"}
SAFE_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
    "active_ready_emitted",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "approval_applied",
    "order_placed",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]
LEAKAGE_FIELDS = {
    "active_replay_input_ready",
    "active_ready_emitted",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
}
SIDE_EFFECT_FIELDS = {
    "active_replay_input",
    "approval_applied",
    "order_placed",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
}
AUTHORITY_FIELDS = [
    "primary_reviewer",
    "primary_reviewer_role",
    "second_reviewer",
    "red_team_reviewer",
    "data_source_reviewer",
    "strategy_owner",
    "authority_scope",
]
ATTESTATION_FIELDS = [
    "pit_validity_attested",
    "source_permission_attested",
    "source_hash_revision_attested",
    "no_future_labels_attested",
    "no_training_leakage_attested",
    "no_stock_profile_leakage_attested",
    "no_buy_review_eligibility_attested",
    "no_active_ready_attested",
    "no_side_effects_attested",
    "no_trading_authorization_attested",
    "report_only",
    "diagnostic_only",
]
SECOND_REVIEW_FIELDS = [
    "reviewer",
    "reviewed_at",
    "pit_reviewed",
    "source_reviewed",
    "evidence_reviewed",
    "leakage_reviewed",
    "side_effect_reviewed",
    "overclaim_wording_reviewed",
    "report_only",
    "diagnostic_only",
]
RED_TEAM_FIELDS = [
    "reviewer",
    "reviewed_at",
    "attempted_to_find_future_leakage",
    "attempted_to_find_permission_gap",
    "attempted_to_find_overclaim",
    "attempted_to_find_side_effect_risk",
    "report_only",
    "diagnostic_only",
]


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceSettings:
    promotion_artifact: Path | None = None
    promotion_health_artifact: Path | None = None
    promotion_status_artifact: Path | None = None
    acceptance_request_manifest: Path | None = None
    reviewer_authority_manifest: Path | None = None
    manual_attestation_manifest: Path | None = None
    second_review_manifest: Path | None = None
    red_team_review_manifest: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputAcceptancePreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceAttestationResult:
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceSecondReviewResult:
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceRedTeamResult:
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceLineageResult:
    artifact_type: str
    artifact_path: str
    status: str
    passed: bool
    blocker_reason: str


@dataclass(frozen=True)
class ActiveReplayInputAcceptanceResult:
    acceptance_run_id: str
    generated_at: str
    artifact_path: Path
    status: str
    workflow_stage: str
    precondition_results: list[ActiveReplayInputAcceptancePreconditionResult]
    reviewer_authority_results: list[ActiveReplayInputAcceptanceAttestationResult]
    manual_attestation_results: list[ActiveReplayInputAcceptanceAttestationResult]
    second_review_results: list[ActiveReplayInputAcceptanceSecondReviewResult]
    red_team_review_results: list[ActiveReplayInputAcceptanceRedTeamResult]
    lineage_results: list[ActiveReplayInputAcceptanceLineageResult]
    pit_results: list[ActiveReplayInputAcceptancePreconditionResult]
    source_results: list[ActiveReplayInputAcceptancePreconditionResult]
    leakage_results: list[ActiveReplayInputAcceptancePreconditionResult]
    side_effect_results: list[ActiveReplayInputAcceptancePreconditionResult]
    overclaim_guard_results: list[ActiveReplayInputAcceptancePreconditionResult]
    promotion_artifact_path: str
    promotion_health_artifact_path: str
    promotion_status_artifact_path: str
    acceptance_request_manifest_path: str
    reviewer_authority_manifest_path: str
    manual_attestation_manifest_path: str
    second_review_manifest_path: str
    red_team_review_manifest_path: str
    precondition_count: int
    passed_precondition_count: int
    blocked_precondition_count: int
    reviewer_authority_gate_count: int
    passed_reviewer_authority_gate_count: int
    blocked_reviewer_authority_gate_count: int
    manual_attestation_count: int
    passed_manual_attestation_count: int
    blocked_manual_attestation_count: int
    second_review_gate_count: int
    passed_second_review_gate_count: int
    blocked_second_review_gate_count: int
    red_team_gate_count: int
    passed_red_team_gate_count: int
    blocked_red_team_gate_count: int
    issue_count: int
    blocker_count: int
    warning_count: int
    ready_for_active_ready_review: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    active_ready_emitted: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    approval_applied: bool
    order_placed: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
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


def run_active_replay_input_acceptance(
    settings: ActiveReplayInputAcceptanceSettings | None = None,
) -> ActiveReplayInputAcceptanceResult:
    settings = settings or ActiveReplayInputAcceptanceSettings()
    generated_at = datetime.now(timezone.utc).isoformat()
    input_seed = "|".join(
        str(value or "")
        for value in [
            settings.promotion_artifact,
            settings.promotion_health_artifact,
            settings.promotion_status_artifact,
            settings.acceptance_request_manifest,
            settings.reviewer_authority_manifest,
            settings.manual_attestation_manifest,
            settings.second_review_manifest,
            settings.red_team_review_manifest,
            generated_at,
        ]
    )
    acceptance_run_id = hashlib.sha256(input_seed.encode("utf-8")).hexdigest()[:12]
    artifact_path = Path(settings.output_dir) / acceptance_run_id
    artifact_paths = resolve_active_replay_input_acceptance_paths(artifact_path)

    supplied_inputs = [
        settings.promotion_artifact,
        settings.promotion_health_artifact,
        settings.promotion_status_artifact,
        settings.acceptance_request_manifest,
        settings.reviewer_authority_manifest,
        settings.manual_attestation_manifest,
        settings.second_review_manifest,
        settings.red_team_review_manifest,
    ]
    no_input = not any(supplied_inputs)

    promotion = _load_promotion_metadata(settings.promotion_artifact)
    health = _load_json_any(settings.promotion_health_artifact)
    status_payload = _load_json_any(settings.promotion_status_artifact)
    request = _load_json_any(settings.acceptance_request_manifest)
    authority = _load_json_any(settings.reviewer_authority_manifest)
    attestation = _load_json_any(settings.manual_attestation_manifest)
    second_review = _load_json_any(settings.second_review_manifest)
    red_team = _load_json_any(settings.red_team_review_manifest)

    preconditions = _build_preconditions(settings, promotion, health, status_payload, request, no_input)
    lineage = _build_lineage_results(settings, promotion)
    reviewer_authority = _build_keyed_results(authority, AUTHORITY_FIELDS, "authority_result", settings.reviewer_authority_manifest)
    manual_attestation = _build_keyed_results(
        attestation, ATTESTATION_FIELDS, "attestation_result", settings.manual_attestation_manifest
    )
    second_review_results = _build_second_review_results(second_review, settings.second_review_manifest)
    red_team_results = _build_red_team_results(red_team, settings.red_team_review_manifest)
    pit_results = _build_context_results("PIT_COVERAGE_ACCEPTANCE", request, ["pit_validity_attested"], attestation)
    source_results = _build_context_results(
        "SOURCE_PERMISSION_ACCEPTANCE",
        request,
        ["source_permission_attested", "source_hash_revision_attested"],
        attestation,
    )
    leakage_results = _build_safety_results("LEAKAGE_EXCLUSION", [promotion, request], LEAKAGE_FIELDS)
    side_effect_results = _build_safety_results("SIDE_EFFECT_SAFETY", [promotion, request], SIDE_EFFECT_FIELDS)
    overclaim_guards = _build_overclaim_guards(promotion, request, artifact_path)

    status = _select_status(
        no_input=no_input,
        preconditions=preconditions,
        lineage=lineage,
        reviewer_authority=reviewer_authority,
        manual_attestation=manual_attestation,
        second_review=second_review_results,
        red_team=red_team_results,
        pit_results=pit_results,
        source_results=source_results,
        leakage_results=leakage_results,
        side_effect_results=side_effect_results,
        overclaim_guards=overclaim_guards,
    )
    ready_for_active_ready_review = status == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW
    all_gate_results = (
        preconditions
        + pit_results
        + source_results
        + leakage_results
        + side_effect_results
        + overclaim_guards
    )
    blocker_count = sum(not row.passed for row in all_gate_results)
    blocker_count += sum(not row.passed for row in reviewer_authority)
    blocker_count += sum(not row.passed for row in manual_attestation)
    blocker_count += sum(not row.passed for row in second_review_results)
    blocker_count += sum(not row.passed for row in red_team_results)
    blocker_count += sum(not row.passed for row in lineage)

    result = ActiveReplayInputAcceptanceResult(
        acceptance_run_id=acceptance_run_id,
        generated_at=generated_at,
        artifact_path=artifact_path,
        status=status,
        workflow_stage=status,
        precondition_results=preconditions,
        reviewer_authority_results=reviewer_authority,
        manual_attestation_results=manual_attestation,
        second_review_results=second_review_results,
        red_team_review_results=red_team_results,
        lineage_results=lineage,
        pit_results=pit_results,
        source_results=source_results,
        leakage_results=leakage_results,
        side_effect_results=side_effect_results,
        overclaim_guard_results=overclaim_guards,
        promotion_artifact_path=_path_text(settings.promotion_artifact),
        promotion_health_artifact_path=_path_text(settings.promotion_health_artifact),
        promotion_status_artifact_path=_path_text(settings.promotion_status_artifact),
        acceptance_request_manifest_path=_path_text(settings.acceptance_request_manifest),
        reviewer_authority_manifest_path=_path_text(settings.reviewer_authority_manifest),
        manual_attestation_manifest_path=_path_text(settings.manual_attestation_manifest),
        second_review_manifest_path=_path_text(settings.second_review_manifest),
        red_team_review_manifest_path=_path_text(settings.red_team_review_manifest),
        precondition_count=len(preconditions),
        passed_precondition_count=sum(row.passed for row in preconditions),
        blocked_precondition_count=sum(not row.passed for row in preconditions),
        reviewer_authority_gate_count=len(reviewer_authority),
        passed_reviewer_authority_gate_count=sum(row.passed for row in reviewer_authority),
        blocked_reviewer_authority_gate_count=sum(not row.passed for row in reviewer_authority),
        manual_attestation_count=len(manual_attestation),
        passed_manual_attestation_count=sum(row.passed for row in manual_attestation),
        blocked_manual_attestation_count=sum(not row.passed for row in manual_attestation),
        second_review_gate_count=len(second_review_results),
        passed_second_review_gate_count=sum(row.passed for row in second_review_results),
        blocked_second_review_gate_count=sum(not row.passed for row in second_review_results),
        red_team_gate_count=len(red_team_results),
        passed_red_team_gate_count=sum(row.passed for row in red_team_results),
        blocked_red_team_gate_count=sum(not row.passed for row in red_team_results),
        issue_count=blocker_count,
        blocker_count=blocker_count,
        warning_count=0,
        ready_for_active_ready_review=ready_for_active_ready_review,
        active_replay_input_ready=False,
        active_replay_input=False,
        active_ready_emitted=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        approval_applied=False,
        order_placed=False,
        llm_api_called=False,
        external_api_called=False,
        cache_mutated=False,
        current_candidates_run=False,
        snapshot_built=False,
        signal_semantics_changed=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        overclaim_guard_pass_count=sum(row.passed for row in overclaim_guards),
        overclaim_guard_total_count=len(overclaim_guards),
        artifact_paths=artifact_paths,
    )
    if settings.write_artifacts:
        write_active_replay_input_acceptance_artifacts(result)
    return result


def resolve_active_replay_input_acceptance_paths(artifact_path: Path) -> dict[str, Path]:
    return {
        "artifact_dir": artifact_path,
        "metadata": artifact_path / "acceptance_metadata.json",
        "acceptance_report": artifact_path / "acceptance_report.md",
        "acceptance_precondition_results": artifact_path / "acceptance_precondition_results.csv",
        "reviewer_authority_results": artifact_path / "reviewer_authority_results.csv",
        "manual_attestation_results": artifact_path / "manual_attestation_results.csv",
        "second_review_results": artifact_path / "second_review_results.csv",
        "red_team_review_results": artifact_path / "red_team_review_results.csv",
        "lineage_acceptance_results": artifact_path / "lineage_acceptance_results.csv",
        "pit_acceptance_results": artifact_path / "pit_acceptance_results.csv",
        "source_acceptance_results": artifact_path / "source_acceptance_results.csv",
        "leakage_acceptance_results": artifact_path / "leakage_acceptance_results.csv",
        "side_effect_acceptance_results": artifact_path / "side_effect_acceptance_results.csv",
        "overclaim_guard_report": artifact_path / "overclaim_guard_report.csv",
        "recommended_next_task": artifact_path / "recommended_next_task.md",
    }


def write_active_replay_input_acceptance_artifacts(result: ActiveReplayInputAcceptanceResult) -> None:
    result.artifact_path.mkdir(parents=True, exist_ok=True)
    result.artifact_paths["metadata"].write_text(
        json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8"
    )
    result.artifact_paths["acceptance_report"].write_text(_render_report(result), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    _write_frame(result.artifact_paths["acceptance_precondition_results"], result.precondition_results)
    _write_frame(result.artifact_paths["reviewer_authority_results"], result.reviewer_authority_results)
    _write_frame(result.artifact_paths["manual_attestation_results"], result.manual_attestation_results)
    _write_frame(result.artifact_paths["second_review_results"], result.second_review_results)
    _write_frame(result.artifact_paths["red_team_review_results"], result.red_team_review_results)
    _write_frame(result.artifact_paths["lineage_acceptance_results"], result.lineage_results)
    _write_frame(result.artifact_paths["pit_acceptance_results"], result.pit_results)
    _write_frame(result.artifact_paths["source_acceptance_results"], result.source_results)
    _write_frame(result.artifact_paths["leakage_acceptance_results"], result.leakage_results)
    _write_frame(result.artifact_paths["side_effect_acceptance_results"], result.side_effect_results)
    _write_frame(result.artifact_paths["overclaim_guard_report"], result.overclaim_guard_results)


def _build_preconditions(
    settings: ActiveReplayInputAcceptanceSettings,
    promotion: dict[str, Any],
    health: dict[str, Any],
    status_payload: dict[str, Any],
    request: dict[str, Any],
    no_input: bool,
) -> list[ActiveReplayInputAcceptancePreconditionResult]:
    if no_input:
        return [_precondition("ACCEPTANCE_INPUT_GATE", "acceptance_input_supplied", False, "no acceptance input supplied", "")]
    rows = [
        _precondition(
            "PROMOTION_LINEAGE_GATE",
            "promotion_artifact_exists",
            bool(settings.promotion_artifact and _resolve_metadata_path(settings.promotion_artifact).exists()),
            "promotion artifact missing",
            _path_text(settings.promotion_artifact),
        ),
        _precondition(
            "PROMOTION_LINEAGE_GATE",
            "promotion_status_ready_for_human_review",
            _text(promotion.get("status")) == PROMOTION_READY_FOR_HUMAN_REVIEW
            and _to_bool(promotion.get("ready_for_human_review")),
            "promotion is not ready for human review",
            _path_text(settings.promotion_artifact),
        ),
        _precondition(
            "PROMOTION_HEALTH_GATE",
            "promotion_health_pass",
            not health or _health_status(health) == "PASS",
            "promotion health is not PASS",
            _path_text(settings.promotion_health_artifact),
        ),
        _precondition(
            "PROMOTION_HEALTH_GATE",
            "promotion_status_artifact_consistent",
            not status_payload
            or (
                _text(status_payload.get("status")) == PROMOTION_READY_FOR_HUMAN_REVIEW
                and _to_bool(status_payload.get("ready_for_human_review"))
            ),
            "promotion status artifact is not ready for human review",
            _path_text(settings.promotion_status_artifact),
        ),
        _precondition(
            "ACCEPTANCE_INPUT_GATE",
            "acceptance_request_exists",
            bool(settings.acceptance_request_manifest and request),
            "acceptance request manifest missing",
            _path_text(settings.acceptance_request_manifest),
        ),
        _precondition(
            "ACCEPTANCE_INPUT_GATE",
            "acceptance_requested_status_review_only",
            _text(request.get("requested_status")) == ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW,
            "acceptance request did not ask for review-only readiness",
            _path_text(settings.acceptance_request_manifest),
        ),
        _precondition(
            "ACCEPTANCE_INPUT_GATE",
            "output_path_manual_diagnostics",
            "outputs/reports/manual_diagnostics" in str(Path(settings.output_dir).as_posix()),
            "output path is outside manual_diagnostics",
            _path_text(settings.output_dir),
        ),
    ]
    return rows


def _build_lineage_results(
    settings: ActiveReplayInputAcceptanceSettings,
    promotion: dict[str, Any],
) -> list[ActiveReplayInputAcceptanceLineageResult]:
    passed = _text(promotion.get("status")) == PROMOTION_READY_FOR_HUMAN_REVIEW
    return [
        ActiveReplayInputAcceptanceLineageResult(
            artifact_type="promotion",
            artifact_path=_path_text(settings.promotion_artifact),
            status="PASS" if passed else ACCEPTANCE_LINEAGE_BLOCKED,
            passed=passed,
            blocker_reason="" if passed else "promotion artifact is missing or not review-ready",
        )
    ]


def _build_keyed_results(
    payload: dict[str, Any],
    required_fields: list[str],
    result_field: str,
    path: Path | None,
) -> list[ActiveReplayInputAcceptanceAttestationResult]:
    if not path:
        return [
            ActiveReplayInputAcceptanceAttestationResult(
                gate_name="manifest_exists",
                status="BLOCKED",
                passed=False,
                blocker_reason="manifest missing",
                observed_value="",
            )
        ]
    rows = []
    for field in required_fields:
        value = payload.get(field)
        passed = bool(value) if field not in {"report_only", "diagnostic_only"} else _to_bool(value)
        rows.append(
            ActiveReplayInputAcceptanceAttestationResult(
                gate_name=field,
                status="PASS" if passed else "BLOCKED",
                passed=passed,
                blocker_reason="" if passed else f"{field} missing or false",
                observed_value=str(value),
            )
        )
    result_value = _text(payload.get(result_field))
    passed = result_value in REVIEW_ONLY_RESULTS
    rows.append(
        ActiveReplayInputAcceptanceAttestationResult(
            gate_name=result_field,
            status="PASS" if passed else "BLOCKED",
            passed=passed,
            blocker_reason="" if passed else f"{result_field} is not accepted for review only",
            observed_value=result_value,
        )
    )
    return rows


def _build_second_review_results(payload: dict[str, Any], path: Path | None) -> list[ActiveReplayInputAcceptanceSecondReviewResult]:
    base = _build_review_rows(payload, SECOND_REVIEW_FIELDS, "review_result", path)
    return [ActiveReplayInputAcceptanceSecondReviewResult(**row.__dict__) for row in base]


def _build_red_team_results(payload: dict[str, Any], path: Path | None) -> list[ActiveReplayInputAcceptanceRedTeamResult]:
    base = _build_review_rows(payload, RED_TEAM_FIELDS, "red_team_result", path)
    return [ActiveReplayInputAcceptanceRedTeamResult(**row.__dict__) for row in base]


def _build_review_rows(
    payload: dict[str, Any],
    fields: list[str],
    result_field: str,
    path: Path | None,
) -> list[ActiveReplayInputAcceptanceAttestationResult]:
    return _build_keyed_results(payload, fields, result_field, path)


def _build_context_results(
    gate_group: str,
    request: dict[str, Any],
    attestation_fields: list[str],
    attestation: dict[str, Any],
) -> list[ActiveReplayInputAcceptancePreconditionResult]:
    rows = [
        _precondition(
            gate_group,
            "acceptance_request_report_only",
            _to_bool(request.get("report_only")) and _to_bool(request.get("diagnostic_only")),
            "acceptance request is not report-only diagnostic-only",
            "",
        )
    ]
    for field in attestation_fields:
        rows.append(
            _precondition(
                gate_group,
                field,
                _to_bool(attestation.get(field)),
                f"{field} missing or false",
                "",
            )
        )
    return rows


def _build_safety_results(
    gate_group: str,
    payloads: list[dict[str, Any]],
    fields: set[str],
) -> list[ActiveReplayInputAcceptancePreconditionResult]:
    rows = []
    for field in sorted(fields):
        unsafe = any(_to_bool(payload.get(field)) for payload in payloads if payload)
        rows.append(
            _precondition(
                gate_group,
                field,
                not unsafe,
                f"{field} must remain false",
                "",
            )
        )
    return rows


def _build_overclaim_guards(
    promotion: dict[str, Any],
    request: dict[str, Any],
    artifact_path: Path,
) -> list[ActiveReplayInputAcceptancePreconditionResult]:
    return [
        _precondition(
            "OVERCLAIM_GUARD",
            "promotion_ready_not_active_ready",
            _text(promotion.get("status")) != "ACTIVE_REPLAY_INPUT_READY"
            and not _to_bool(promotion.get("active_ready_emitted")),
            "promotion artifact emitted active-ready",
            "",
        ),
        _precondition(
            "OVERCLAIM_GUARD",
            "acceptance_review_ready_not_active_ready",
            _text(request.get("requested_status")) != "ACTIVE_REPLAY_INPUT_READY"
            and not _to_bool(request.get("active_replay_input_ready"))
            and not _to_bool(request.get("active_ready_emitted")),
            "acceptance request attempted active-ready",
            "",
        ),
        _precondition(
            "OVERCLAIM_GUARD",
            "reviewer_acceptance_not_trading_authorization",
            not _to_bool(request.get("order_placed")),
            "acceptance request attempted trading authorization",
            "",
        ),
        _precondition(
            "OVERCLAIM_GUARD",
            "output_path_under_manual_diagnostics",
            "outputs/reports/manual_diagnostics" in artifact_path.as_posix(),
            "output path is outside manual_diagnostics",
            artifact_path.as_posix(),
        ),
    ]


def _select_status(
    *,
    no_input: bool,
    preconditions: list[ActiveReplayInputAcceptancePreconditionResult],
    lineage: list[ActiveReplayInputAcceptanceLineageResult],
    reviewer_authority: list[ActiveReplayInputAcceptanceAttestationResult],
    manual_attestation: list[ActiveReplayInputAcceptanceAttestationResult],
    second_review: list[ActiveReplayInputAcceptanceSecondReviewResult],
    red_team: list[ActiveReplayInputAcceptanceRedTeamResult],
    pit_results: list[ActiveReplayInputAcceptancePreconditionResult],
    source_results: list[ActiveReplayInputAcceptancePreconditionResult],
    leakage_results: list[ActiveReplayInputAcceptancePreconditionResult],
    side_effect_results: list[ActiveReplayInputAcceptancePreconditionResult],
    overclaim_guards: list[ActiveReplayInputAcceptancePreconditionResult],
) -> str:
    if no_input:
        return NO_ACCEPTANCE_INPUT
    if _has_blocker(side_effect_results):
        return ACCEPTANCE_SIDE_EFFECT_BLOCKED
    if _has_blocker(leakage_results):
        return ACCEPTANCE_LEAKAGE_BLOCKED
    if _has_blocker(preconditions, {"PROMOTION_LINEAGE_GATE", "PROMOTION_HEALTH_GATE"}) or _has_lineage_blocker(lineage):
        return ACCEPTANCE_LINEAGE_BLOCKED
    if _has_blocker(preconditions, {"ACCEPTANCE_INPUT_GATE"}):
        return ACCEPTANCE_REVIEW_BLOCKED
    if _has_blocker(reviewer_authority):
        return ACCEPTANCE_AUTHORITY_BLOCKED
    if _has_blocker(manual_attestation):
        return ACCEPTANCE_ATTESTATION_BLOCKED
    if _has_blocker(second_review):
        return ACCEPTANCE_SECOND_REVIEW_BLOCKED
    if _has_blocker(red_team):
        return ACCEPTANCE_RED_TEAM_BLOCKED
    if _has_blocker(pit_results):
        return ACCEPTANCE_PIT_BLOCKED
    if _has_blocker(source_results):
        return ACCEPTANCE_SOURCE_BLOCKED
    if _has_blocker(overclaim_guards):
        return ACCEPTANCE_REVIEW_BLOCKED
    return ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW


def _precondition(
    gate_group: str,
    gate_name: str,
    passed: bool,
    blocker_reason: str,
    evidence_path: str,
) -> ActiveReplayInputAcceptancePreconditionResult:
    return ActiveReplayInputAcceptancePreconditionResult(
        gate_group=gate_group,
        gate_name=gate_name,
        status="PASS" if passed else "BLOCKED",
        passed=passed,
        blocker_reason="" if passed else blocker_reason,
        evidence_path=evidence_path,
    )


def _metadata(result: ActiveReplayInputAcceptanceResult) -> dict[str, Any]:
    keys = [
        "acceptance_run_id",
        "generated_at",
        "artifact_path",
        "promotion_artifact_path",
        "promotion_health_artifact_path",
        "promotion_status_artifact_path",
        "acceptance_request_manifest_path",
        "reviewer_authority_manifest_path",
        "manual_attestation_manifest_path",
        "second_review_manifest_path",
        "red_team_review_manifest_path",
        "status",
        "workflow_stage",
        "precondition_count",
        "passed_precondition_count",
        "blocked_precondition_count",
        "reviewer_authority_gate_count",
        "passed_reviewer_authority_gate_count",
        "blocked_reviewer_authority_gate_count",
        "manual_attestation_count",
        "passed_manual_attestation_count",
        "blocked_manual_attestation_count",
        "second_review_gate_count",
        "passed_second_review_gate_count",
        "blocked_second_review_gate_count",
        "red_team_gate_count",
        "passed_red_team_gate_count",
        "blocked_red_team_gate_count",
        "issue_count",
        "blocker_count",
        "warning_count",
        "ready_for_active_ready_review",
        "active_replay_input_ready",
        "active_replay_input",
        "active_ready_emitted",
        "forward_labels_exist",
        "weights_trained",
        "active_stock_profile_exists",
        "real_buy_review_eligible",
        "approval_applied",
        "order_placed",
        "llm_api_called",
        "external_api_called",
        "cache_mutated",
        "current_candidates_run",
        "snapshot_built",
        "signal_semantics_changed",
        "report_only",
        "diagnostic_only",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
        "overclaim_guard_pass_count",
        "overclaim_guard_total_count",
    ]
    data: dict[str, Any] = {}
    for key in keys:
        value = getattr(result, key)
        data[key] = str(value) if isinstance(value, Path) else value
    data["artifact_paths"] = {key: str(path) for key, path in result.artifact_paths.items()}
    return data


def _render_report(result: ActiveReplayInputAcceptanceResult) -> str:
    return "\n".join(
        [
            "# Active Replay Input Acceptance Report",
            "",
            f"- acceptance_run_id: `{result.acceptance_run_id}`",
            f"- status: `{result.status}`",
            f"- workflow_stage: `{result.workflow_stage}`",
            f"- ready_for_active_ready_review: `{result.ready_for_active_ready_review}`",
            f"- active_replay_input_ready: `{result.active_replay_input_ready}`",
            f"- active_replay_input: `{result.active_replay_input}`",
            f"- active_ready_emitted: `{result.active_ready_emitted}`",
            f"- blocker_count: `{result.blocker_count}`",
            "",
            "This workflow is report-only. Acceptance-ready-for-active-ready-review is not active-ready. It does not create active replay input, run replay, compute labels, train weights, create stock profiles, create buy-review eligibility, authorize trading, call APIs, mutate cache, or write data stores.",
        ]
    )


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Task: Add Active Replay Input Acceptance artifact views report-only.",
            "",
            "Add index, health, and status only after the core workflow is stable. Do not emit active-ready or create active replay input.",
        ]
    )


def _load_promotion_metadata(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    metadata_path = _resolve_metadata_path(path)
    if not metadata_path.exists():
        return {}
    return _read_json(metadata_path)


def _resolve_metadata_path(path: Path | None) -> Path:
    if not path:
        return Path("__missing_active_replay_input_acceptance_path__")
    path = Path(path)
    if path.is_file():
        return path
    for name in ["promotion_metadata.json", "metadata.json"]:
        candidate = path / name
        if candidate.exists():
            return candidate
    return path / "promotion_metadata.json"


def _load_json_any(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    if path.is_dir():
        return _load_promotion_metadata(path)
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        return frame.iloc[0].to_dict() if not frame.empty else {}
    return _read_json(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _health_status(payload: dict[str, Any]) -> str:
    return _text(payload.get("health_status") or payload.get("status"))


def _write_frame(path: Path, rows: list[Any]) -> None:
    records = [row.__dict__ for row in rows]
    pd.DataFrame(records).to_csv(path, index=False)


def _has_blocker(rows: list[Any], gate_groups: set[str] | None = None) -> bool:
    for row in rows:
        if gate_groups is not None and getattr(row, "gate_group", "") not in gate_groups:
            continue
        if not bool(getattr(row, "passed", False)):
            return True
    return False


def _has_lineage_blocker(rows: list[ActiveReplayInputAcceptanceLineageResult]) -> bool:
    return any(not row.passed for row in rows)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y", "pass", "accepted", "accepted_for_review_only"}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _path_text(path: Path | str | None) -> str:
    return "" if path is None else str(path)
