"""Report-only active replay input promotion readiness workflow.

This core workflow reviews validator/smoke lineage and optional local
promotion request / human review manifests. It is deliberately fail-closed and
stops at ``PROMOTION_READY_FOR_HUMAN_REVIEW``; it never emits active-ready,
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


NO_PROMOTION_INPUT = "NO_PROMOTION_INPUT"
PROMOTION_INPUT_FOUND = "PROMOTION_INPUT_FOUND"
PROMOTION_REVIEW_BLOCKED = "PROMOTION_REVIEW_BLOCKED"
PROMOTION_LINEAGE_BLOCKED = "PROMOTION_LINEAGE_BLOCKED"
PROMOTION_PIT_BLOCKED = "PROMOTION_PIT_BLOCKED"
PROMOTION_SOURCE_BLOCKED = "PROMOTION_SOURCE_BLOCKED"
PROMOTION_EVIDENCE_BLOCKED = "PROMOTION_EVIDENCE_BLOCKED"
PROMOTION_LEAKAGE_BLOCKED = "PROMOTION_LEAKAGE_BLOCKED"
PROMOTION_SIDE_EFFECT_BLOCKED = "PROMOTION_SIDE_EFFECT_BLOCKED"
PROMOTION_READY_FOR_HUMAN_REVIEW = "PROMOTION_READY_FOR_HUMAN_REVIEW"
ACTIVE_REPLAY_INPUT_READY = "ACTIVE_REPLAY_INPUT_READY"

DEFAULT_OUTPUT_DIR = Path(
    "outputs/reports/manual_diagnostics/active_replay_input_promotion_v0_1"
)
REVIEW_ACCEPTED_RESULTS = {"READY_FOR_HUMAN_REVIEW", "ACCEPTED_FOR_HUMAN_REVIEW"}
SAFE_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
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
HUMAN_REVIEW_BOOL_FIELDS = [
    "pit_universe_reviewed",
    "source_permission_reviewed",
    "raw_evidence_reviewed",
    "factor_definition_reviewed",
    "factor_observation_reviewed",
    "event_structured_reviewed",
    "company_exposure_reviewed",
    "leakage_reviewed",
    "side_effect_reviewed",
    "promotion_decision_reviewed",
]


@dataclass(frozen=True)
class ActiveReplayInputPromotionSettings:
    validator_artifact: Path | None = None
    smoke_artifact: Path | None = None
    promotion_request_manifest: Path | None = None
    human_review_manifest: Path | None = None
    output_dir: Path = DEFAULT_OUTPUT_DIR
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ActiveReplayInputPromotionPreconditionResult:
    gate_group: str
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    evidence_path: str


@dataclass(frozen=True)
class ActiveReplayInputPromotionHumanReviewResult:
    gate_name: str
    status: str
    passed: bool
    blocker_reason: str
    observed_value: str


@dataclass(frozen=True)
class ActiveReplayInputPromotionLineageResult:
    artifact_type: str
    artifact_path: str
    artifact_id: str
    status: str
    linked_validator_run_id: str
    passed: bool
    blocker_reason: str


@dataclass(frozen=True)
class ActiveReplayInputPromotionResult:
    promotion_run_id: str
    generated_at: str
    artifact_path: Path
    validator_artifact_path: str
    smoke_artifact_path: str
    promotion_request_manifest_path: str
    human_review_manifest_path: str
    status: str
    workflow_stage: str
    precondition_count: int
    passed_precondition_count: int
    blocked_precondition_count: int
    human_review_gate_count: int
    passed_human_review_gate_count: int
    blocked_human_review_gate_count: int
    issue_count: int
    blocker_count: int
    warning_count: int
    ready_for_human_review: bool
    active_replay_input_ready: bool
    active_replay_input: bool
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
    active_ready_emitted: bool
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    artifact_paths: dict[str, Path]


def run_active_replay_input_promotion(
    settings: ActiveReplayInputPromotionSettings | None = None,
) -> ActiveReplayInputPromotionResult:
    resolved = settings or ActiveReplayInputPromotionSettings()
    _assert_settings_safe(resolved)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    validator_metadata, validator_path = _load_artifact_metadata(resolved.validator_artifact, "metadata.json")
    smoke_metadata, smoke_path = _load_artifact_metadata(resolved.smoke_artifact, "smoke_metadata.json")
    request_manifest, request_path = _load_json_file(resolved.promotion_request_manifest)
    review_manifest, review_path = _load_json_file(resolved.human_review_manifest)

    preconditions = _build_precondition_results(
        settings=resolved,
        validator_metadata=validator_metadata,
        validator_path=validator_path,
        smoke_metadata=smoke_metadata,
        smoke_path=smoke_path,
        request_manifest=request_manifest,
        request_path=request_path,
        review_manifest=review_manifest,
        review_path=review_path,
    )
    human_gates = _build_human_review_results(review_manifest, review_path)
    lineage = _build_lineage_results(
        validator_metadata=validator_metadata,
        validator_path=validator_path,
        smoke_metadata=smoke_metadata,
        smoke_path=smoke_path,
        request_manifest=request_manifest,
        request_path=request_path,
        review_manifest=review_manifest,
        review_path=review_path,
    )
    status = _overall_status(resolved, preconditions, human_gates)
    ready_for_human_review = status == PROMOTION_READY_FOR_HUMAN_REVIEW
    run_id = _promotion_run_id(
        settings=resolved,
        validator_metadata=validator_metadata,
        smoke_metadata=smoke_metadata,
        request_manifest=request_manifest,
        review_manifest=review_manifest,
        status=status,
    )
    paths = resolve_active_replay_input_promotion_paths(resolved.output_dir, run_id)
    overclaim_guards = _build_overclaim_guards(paths["artifact_dir"], status)
    result = ActiveReplayInputPromotionResult(
        promotion_run_id=run_id,
        generated_at=generated_at,
        artifact_path=paths["artifact_dir"],
        validator_artifact_path=str(validator_path or ""),
        smoke_artifact_path=str(smoke_path or ""),
        promotion_request_manifest_path=str(request_path or ""),
        human_review_manifest_path=str(review_path or ""),
        status=status,
        workflow_stage=status,
        precondition_count=len(preconditions),
        passed_precondition_count=sum(int(row.passed) for row in preconditions),
        blocked_precondition_count=sum(int(not row.passed) for row in preconditions),
        human_review_gate_count=len(human_gates),
        passed_human_review_gate_count=sum(int(row.passed) for row in human_gates),
        blocked_human_review_gate_count=sum(int(not row.passed) for row in human_gates),
        issue_count=sum(int(not row.passed) for row in preconditions)
        + sum(int(not row.passed) for row in human_gates),
        blocker_count=sum(int(not row.passed) for row in preconditions)
        + sum(int(not row.passed) for row in human_gates),
        warning_count=0,
        ready_for_human_review=ready_for_human_review,
        active_replay_input_ready=False,
        active_replay_input=False,
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
        active_ready_emitted=False,
        overclaim_guard_pass_count=int(overclaim_guards["passed"].sum()) if not overclaim_guards.empty else 0,
        overclaim_guard_total_count=len(overclaim_guards),
        artifact_paths=paths,
    )
    if resolved.write_artifacts:
        write_active_replay_input_promotion_artifacts(
            result=result,
            preconditions=preconditions,
            human_gates=human_gates,
            lineage=lineage,
            overclaim_guards=overclaim_guards,
        )
    return result


def resolve_active_replay_input_promotion_paths(output_dir: str | Path, promotion_run_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / promotion_run_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "promotion_metadata.json",
        "promotion_report": artifact_dir / "promotion_report.md",
        "promotion_precondition_results": artifact_dir / "promotion_precondition_results.csv",
        "human_review_gate_results": artifact_dir / "human_review_gate_results.csv",
        "artifact_lineage_results": artifact_dir / "artifact_lineage_results.csv",
        "pit_coverage_results": artifact_dir / "pit_coverage_results.csv",
        "source_permission_results": artifact_dir / "source_permission_results.csv",
        "leakage_guard_results": artifact_dir / "leakage_guard_results.csv",
        "side_effect_guard_results": artifact_dir / "side_effect_guard_results.csv",
        "overclaim_guard_report": artifact_dir / "overclaim_guard_report.csv",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_active_replay_input_promotion_artifacts(
    *,
    result: ActiveReplayInputPromotionResult,
    preconditions: list[ActiveReplayInputPromotionPreconditionResult],
    human_gates: list[ActiveReplayInputPromotionHumanReviewResult],
    lineage: list[ActiveReplayInputPromotionLineageResult],
    overclaim_guards: pd.DataFrame,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    precondition_frame = pd.DataFrame([row.__dict__ for row in preconditions])
    human_frame = pd.DataFrame([row.__dict__ for row in human_gates])
    lineage_frame = pd.DataFrame([row.__dict__ for row in lineage])
    precondition_frame.to_csv(paths["promotion_precondition_results"], index=False)
    human_frame.to_csv(paths["human_review_gate_results"], index=False)
    lineage_frame.to_csv(paths["artifact_lineage_results"], index=False)
    _filter_group(precondition_frame, "PIT_COVERAGE").to_csv(paths["pit_coverage_results"], index=False)
    _filter_group(precondition_frame, "SOURCE_PERMISSION").to_csv(paths["source_permission_results"], index=False)
    _filter_group(precondition_frame, "LEAKAGE_EXCLUSION").to_csv(paths["leakage_guard_results"], index=False)
    _filter_group(precondition_frame, "SIDE_EFFECT_SAFETY").to_csv(paths["side_effect_guard_results"], index=False)
    overclaim_guards.to_csv(paths["overclaim_guard_report"], index=False)
    paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    paths["promotion_report"].write_text(_render_report(result, preconditions, human_gates), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    return paths


def _build_precondition_results(
    *,
    settings: ActiveReplayInputPromotionSettings,
    validator_metadata: dict[str, Any],
    validator_path: Path | None,
    smoke_metadata: dict[str, Any],
    smoke_path: Path | None,
    request_manifest: dict[str, Any],
    request_path: Path | None,
    review_manifest: dict[str, Any],
    review_path: Path | None,
) -> list[ActiveReplayInputPromotionPreconditionResult]:
    rows: list[ActiveReplayInputPromotionPreconditionResult] = []
    any_input = any(
        [
            settings.validator_artifact,
            settings.smoke_artifact,
            settings.promotion_request_manifest,
            settings.human_review_manifest,
        ]
    )
    _add_gate(rows, "PROMOTION_INPUT", "any_input_provided", any_input, NO_PROMOTION_INPUT, "NO_INPUT_PROVIDED", "")
    _add_gate(
        rows,
        "VALIDATOR_LINEAGE",
        "validator_artifact_readable",
        bool(validator_metadata),
        PROMOTION_LINEAGE_BLOCKED,
        "VALIDATOR_METADATA_MISSING",
        validator_path,
    )
    _add_gate(
        rows,
        "VALIDATOR_LINEAGE",
        "validator_status_pass_candidate",
        _text(validator_metadata.get("status")) == "REPLAY_INPUT_GATE_PASS_CANDIDATE",
        PROMOTION_LINEAGE_BLOCKED,
        "VALIDATOR_NOT_PASS_CANDIDATE",
        validator_path,
    )
    _add_gate(
        rows,
        "VALIDATOR_LINEAGE",
        "validator_pass_candidate_true",
        _to_bool(validator_metadata.get("pass_candidate")),
        PROMOTION_LINEAGE_BLOCKED,
        "VALIDATOR_PASS_CANDIDATE_FALSE",
        validator_path,
    )
    _add_gate(
        rows,
        "SMOKE_LINEAGE",
        "smoke_artifact_readable",
        bool(smoke_metadata),
        PROMOTION_LINEAGE_BLOCKED,
        "SMOKE_METADATA_MISSING",
        smoke_path,
    )
    smoke_stage = _text(smoke_metadata.get("workflow_stage")) or _text(smoke_metadata.get("smoke_stage"))
    _add_gate(
        rows,
        "SMOKE_LINEAGE",
        "smoke_stage_ready",
        smoke_stage == "SMOKE_PASS_CANDIDATE_READY",
        PROMOTION_LINEAGE_BLOCKED,
        "SMOKE_NOT_PASS_CANDIDATE_READY",
        smoke_path,
    )
    _add_gate(
        rows,
        "SMOKE_LINEAGE",
        "smoke_validator_linkage_matches",
        bool(validator_metadata)
        and bool(smoke_metadata)
        and _text(smoke_metadata.get("validator_run_id")) == _text(validator_metadata.get("validator_run_id")),
        PROMOTION_LINEAGE_BLOCKED,
        "SMOKE_VALIDATOR_LINKAGE_MISMATCH",
        smoke_path,
    )
    _add_gate(
        rows,
        "PACKAGE_IDENTITY",
        "validator_input_package_ref_present",
        bool(_text(validator_metadata.get("input_package_path"))),
        PROMOTION_LINEAGE_BLOCKED,
        "INPUT_PACKAGE_REF_MISSING",
        validator_path,
    )
    _add_gate(
        rows,
        "PROMOTION_REVIEW",
        "promotion_request_manifest_readable",
        bool(request_manifest),
        PROMOTION_REVIEW_BLOCKED,
        "PROMOTION_REQUEST_MISSING",
        request_path,
    )
    _add_gate(
        rows,
        "PROMOTION_REVIEW",
        "human_review_manifest_readable",
        bool(review_manifest),
        PROMOTION_REVIEW_BLOCKED,
        "HUMAN_REVIEW_MISSING",
        review_path,
    )
    _add_required_text_gates(rows, request_manifest, request_path)
    if request_manifest:
        _add_request_reference_gates(rows, request_manifest, validator_path, smoke_path)
    _add_safety_gates(rows, validator_metadata, "validator", validator_path)
    _add_safety_gates(rows, smoke_metadata, "smoke", smoke_path)
    _add_safety_gates(rows, request_manifest, "promotion_request", request_path)
    if request_manifest:
        _add_manifest_truth_gate(rows, request_manifest, request_path, "report_only", True, PROMOTION_SIDE_EFFECT_BLOCKED)
        _add_manifest_truth_gate(rows, request_manifest, request_path, "diagnostic_only", True, PROMOTION_SIDE_EFFECT_BLOCKED)
    if review_manifest:
        _add_manifest_truth_gate(rows, review_manifest, review_path, "report_only", True, PROMOTION_SIDE_EFFECT_BLOCKED)
        _add_manifest_truth_gate(rows, review_manifest, review_path, "diagnostic_only", True, PROMOTION_SIDE_EFFECT_BLOCKED)
    _add_gate(rows, "PIT_COVERAGE", "pit_review_manifest_present", bool(review_manifest), PROMOTION_PIT_BLOCKED, "PIT_REVIEW_CONTEXT_MISSING", review_path)
    _add_gate(rows, "SOURCE_PERMISSION", "source_permission_review_manifest_present", bool(review_manifest), PROMOTION_SOURCE_BLOCKED, "SOURCE_REVIEW_CONTEXT_MISSING", review_path)
    _add_gate(rows, "EVIDENCE_COVERAGE", "raw_evidence_review_manifest_present", bool(review_manifest), PROMOTION_EVIDENCE_BLOCKED, "EVIDENCE_REVIEW_CONTEXT_MISSING", review_path)
    _add_gate(rows, "OVERCLAIM_GUARD", "active_ready_not_emitted", True, PROMOTION_LINEAGE_BLOCKED, "ACTIVE_READY_EMITTED", "")
    _add_gate(rows, "OVERCLAIM_GUARD", "output_path_manual_diagnostics", _safe_manual_diagnostics_path(settings.output_dir), PROMOTION_SIDE_EFFECT_BLOCKED, "UNSAFE_OUTPUT_PATH", settings.output_dir)
    _add_gate(rows, "OVERCLAIM_GUARD", "output_path_not_data_store", _no_data_store_path(settings.output_dir), PROMOTION_SIDE_EFFECT_BLOCKED, "DATA_STORE_OUTPUT_PATH", settings.output_dir)
    return rows


def _add_required_text_gates(
    rows: list[ActiveReplayInputPromotionPreconditionResult],
    request_manifest: dict[str, Any],
    request_path: Path | None,
) -> None:
    for field in [
        "promotion_request_id",
        "requested_by",
        "requested_at",
        "request_reason",
        "validator_artifact_ref",
        "smoke_artifact_ref",
        "input_package_ref",
        "requested_status",
    ]:
        _add_gate(
            rows,
            "PROMOTION_REVIEW",
            f"promotion_request_{field}_present",
            bool(_text(request_manifest.get(field))),
            PROMOTION_REVIEW_BLOCKED,
            f"PROMOTION_REQUEST_{field.upper()}_MISSING",
            request_path,
        )
    _add_gate(
        rows,
        "PROMOTION_REVIEW",
        "requested_status_review_only",
        _text(request_manifest.get("requested_status")) == PROMOTION_READY_FOR_HUMAN_REVIEW,
        PROMOTION_REVIEW_BLOCKED,
        "REQUESTED_STATUS_NOT_REVIEW_ONLY",
        request_path,
    )


def _add_request_reference_gates(
    rows: list[ActiveReplayInputPromotionPreconditionResult],
    request_manifest: dict[str, Any],
    validator_path: Path | None,
    smoke_path: Path | None,
) -> None:
    validator_ref = _text(request_manifest.get("validator_artifact_ref"))
    smoke_ref = _text(request_manifest.get("smoke_artifact_ref"))
    _add_gate(
        rows,
        "PACKAGE_IDENTITY",
        "promotion_request_validator_ref_matches",
        bool(validator_path) and _same_path_text(validator_ref, validator_path),
        PROMOTION_LINEAGE_BLOCKED,
        "PROMOTION_REQUEST_VALIDATOR_REF_MISMATCH",
        validator_path,
    )
    _add_gate(
        rows,
        "PACKAGE_IDENTITY",
        "promotion_request_smoke_ref_matches",
        bool(smoke_path) and _same_path_text(smoke_ref, smoke_path),
        PROMOTION_LINEAGE_BLOCKED,
        "PROMOTION_REQUEST_SMOKE_REF_MISMATCH",
        smoke_path,
    )


def _build_human_review_results(
    review_manifest: dict[str, Any],
    review_path: Path | None,
) -> list[ActiveReplayInputPromotionHumanReviewResult]:
    rows: list[ActiveReplayInputPromotionHumanReviewResult] = []
    required_text = ["human_review_id", "reviewer", "reviewed_at", "review_scope", "notes"]
    for field in required_text:
        _add_human_gate(rows, field, bool(_text(review_manifest.get(field))), "MISSING_REVIEW_FIELD", review_manifest.get(field))
    for field in HUMAN_REVIEW_BOOL_FIELDS:
        _add_human_gate(rows, field, _to_bool(review_manifest.get(field)), "REVIEW_BOOLEAN_NOT_TRUE", review_manifest.get(field))
    _add_human_gate(
        rows,
        "review_result",
        _text(review_manifest.get("review_result")) in REVIEW_ACCEPTED_RESULTS,
        "REVIEW_RESULT_NOT_READY_FOR_HUMAN_REVIEW",
        review_manifest.get("review_result"),
    )
    _add_human_gate(rows, "review_manifest_path", bool(review_path), "HUMAN_REVIEW_MANIFEST_MISSING", review_path)
    return rows


def _build_lineage_results(
    *,
    validator_metadata: dict[str, Any],
    validator_path: Path | None,
    smoke_metadata: dict[str, Any],
    smoke_path: Path | None,
    request_manifest: dict[str, Any],
    request_path: Path | None,
    review_manifest: dict[str, Any],
    review_path: Path | None,
) -> list[ActiveReplayInputPromotionLineageResult]:
    validator_id = _text(validator_metadata.get("validator_run_id"))
    return [
        ActiveReplayInputPromotionLineageResult(
            "validator",
            str(validator_path or ""),
            validator_id,
            _text(validator_metadata.get("status")),
            validator_id,
            bool(validator_metadata),
            "" if validator_metadata else "VALIDATOR_METADATA_MISSING",
        ),
        ActiveReplayInputPromotionLineageResult(
            "smoke",
            str(smoke_path or ""),
            _text(smoke_metadata.get("smoke_run_id")),
            _text(smoke_metadata.get("workflow_stage")) or _text(smoke_metadata.get("smoke_stage")),
            _text(smoke_metadata.get("validator_run_id")),
            bool(smoke_metadata) and _text(smoke_metadata.get("validator_run_id")) == validator_id,
            "" if bool(smoke_metadata) and _text(smoke_metadata.get("validator_run_id")) == validator_id else "SMOKE_VALIDATOR_LINKAGE_MISMATCH",
        ),
        ActiveReplayInputPromotionLineageResult(
            "promotion_request",
            str(request_path or ""),
            _text(request_manifest.get("promotion_request_id")),
            _text(request_manifest.get("requested_status")),
            validator_id,
            bool(request_manifest),
            "" if request_manifest else "PROMOTION_REQUEST_MISSING",
        ),
        ActiveReplayInputPromotionLineageResult(
            "human_review",
            str(review_path or ""),
            _text(review_manifest.get("human_review_id")),
            _text(review_manifest.get("review_result")),
            validator_id,
            bool(review_manifest),
            "" if review_manifest else "HUMAN_REVIEW_MISSING",
        ),
    ]


def _add_safety_gates(
    rows: list[ActiveReplayInputPromotionPreconditionResult],
    manifest: dict[str, Any],
    prefix: str,
    evidence_path: Path | None,
) -> None:
    for field in SAFE_FALSE_FIELDS:
        value = _to_bool(manifest.get(field))
        if field in LEAKAGE_FIELDS:
            group = "LEAKAGE_EXCLUSION"
            status = PROMOTION_LEAKAGE_BLOCKED
        else:
            group = "SIDE_EFFECT_SAFETY"
            status = PROMOTION_SIDE_EFFECT_BLOCKED
        _add_gate(
            rows,
            group,
            f"{prefix}_{field}_false",
            value is False,
            status,
            f"{prefix.upper()}_{field.upper()}_TRUE",
            evidence_path,
        )


def _add_manifest_truth_gate(
    rows: list[ActiveReplayInputPromotionPreconditionResult],
    manifest: dict[str, Any],
    evidence_path: Path | None,
    field: str,
    expected: bool,
    status: str,
) -> None:
    _add_gate(
        rows,
        "SIDE_EFFECT_SAFETY",
        f"{field}_{expected}",
        _to_bool(manifest.get(field)) is expected,
        status,
        f"{field.upper()}_NOT_{str(expected).upper()}",
        evidence_path,
    )


def _add_gate(
    rows: list[ActiveReplayInputPromotionPreconditionResult],
    gate_group: str,
    gate_name: str,
    passed: bool,
    status: str,
    blocker_reason: str,
    evidence_path: str | Path | None,
) -> None:
    rows.append(
        ActiveReplayInputPromotionPreconditionResult(
            gate_group=gate_group,
            gate_name=gate_name,
            status="PASS" if passed else status,
            passed=bool(passed),
            blocker_reason="" if passed else blocker_reason,
            evidence_path=str(evidence_path or ""),
        )
    )


def _add_human_gate(
    rows: list[ActiveReplayInputPromotionHumanReviewResult],
    gate_name: str,
    passed: bool,
    blocker_reason: str,
    observed_value: Any,
) -> None:
    rows.append(
        ActiveReplayInputPromotionHumanReviewResult(
            gate_name=gate_name,
            status="PASS" if passed else PROMOTION_REVIEW_BLOCKED,
            passed=bool(passed),
            blocker_reason="" if passed else blocker_reason,
            observed_value=_text(observed_value),
        )
    )


def _overall_status(
    settings: ActiveReplayInputPromotionSettings,
    preconditions: list[ActiveReplayInputPromotionPreconditionResult],
    human_gates: list[ActiveReplayInputPromotionHumanReviewResult],
) -> str:
    if not any(
        [
            settings.validator_artifact,
            settings.smoke_artifact,
            settings.promotion_request_manifest,
            settings.human_review_manifest,
        ]
    ):
        return NO_PROMOTION_INPUT
    statuses = [row.status for row in preconditions if not row.passed]
    statuses.extend(row.status for row in human_gates if not row.passed)
    for status in [
        PROMOTION_LEAKAGE_BLOCKED,
        PROMOTION_SIDE_EFFECT_BLOCKED,
        PROMOTION_LINEAGE_BLOCKED,
        PROMOTION_REVIEW_BLOCKED,
        PROMOTION_PIT_BLOCKED,
        PROMOTION_SOURCE_BLOCKED,
        PROMOTION_EVIDENCE_BLOCKED,
        PROMOTION_INPUT_FOUND,
    ]:
        if status in statuses:
            return status
    return PROMOTION_READY_FOR_HUMAN_REVIEW


def _build_overclaim_guards(artifact_dir: Path, status: str) -> pd.DataFrame:
    rows = [
        ("OG001", "No active-ready status emitted", status != ACTIVE_REPLAY_INPUT_READY, "ACTIVE_READY_EMITTED"),
        ("OG002", "Ready for human review is not active-ready", True, "HUMAN_REVIEW_READY_OVERCLAIM"),
        ("OG003", "Active replay input remains false", True, "ACTIVE_REPLAY_INPUT_TRUE"),
        ("OG004", "Forward labels remain absent", True, "FORWARD_LABELS_TRUE"),
        ("OG005", "Weights remain untrained", True, "WEIGHTS_TRAINED_TRUE"),
        ("OG006", "Stock profile remains absent", True, "STOCK_PROFILE_TRUE"),
        ("OG007", "Buy-review eligibility remains false", True, "BUY_REVIEW_TRUE"),
        ("OG008", "No trading permission", True, "TRADING_PERMISSION_OVERCLAIM"),
        ("OG009", "No performance validation claim", True, "PERFORMANCE_CLAIM_OVERCLAIM"),
        ("OG010", "Output under manual diagnostics", _safe_manual_diagnostics_path(artifact_dir), "UNSAFE_OUTPUT_PATH"),
        ("OG011", "No data store output", _no_data_store_path(artifact_dir), "DATA_STORE_OUTPUT_PATH"),
        ("OG012", "No source/API/cache side effect flags", True, "SIDE_EFFECT_TRUE"),
        ("OG013", "No current-candidates or snapshots", True, "DOWNSTREAM_WORKFLOW_TRUE"),
    ]
    return pd.DataFrame(
        [
            {
                "guard_id": guard_id,
                "guard_name": name,
                "passed": bool(passed),
                "failure_status": "" if passed else PROMOTION_SIDE_EFFECT_BLOCKED,
                "blocker_reason": "" if passed else reason,
            }
            for guard_id, name, passed, reason in rows
        ]
    )


def _metadata(result: ActiveReplayInputPromotionResult) -> dict[str, Any]:
    return {
        "promotion_run_id": result.promotion_run_id,
        "generated_at": result.generated_at,
        "artifact_path": str(result.artifact_path),
        "validator_artifact_path": result.validator_artifact_path,
        "smoke_artifact_path": result.smoke_artifact_path,
        "promotion_request_manifest_path": result.promotion_request_manifest_path,
        "human_review_manifest_path": result.human_review_manifest_path,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "precondition_count": result.precondition_count,
        "passed_precondition_count": result.passed_precondition_count,
        "blocked_precondition_count": result.blocked_precondition_count,
        "human_review_gate_count": result.human_review_gate_count,
        "passed_human_review_gate_count": result.passed_human_review_gate_count,
        "blocked_human_review_gate_count": result.blocked_human_review_gate_count,
        "issue_count": result.issue_count,
        "blocker_count": result.blocker_count,
        "warning_count": result.warning_count,
        "ready_for_human_review": result.ready_for_human_review,
        "active_replay_input_ready": False,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
        "approval_applied": False,
        "order_placed": False,
        "llm_api_called": False,
        "external_api_called": False,
        "cache_mutated": False,
        "current_candidates_run": False,
        "snapshot_built": False,
        "signal_semantics_changed": False,
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "active_ready_emitted": False,
        "overclaim_guard_pass_count": result.overclaim_guard_pass_count,
        "overclaim_guard_total_count": result.overclaim_guard_total_count,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
    }


def _render_report(
    result: ActiveReplayInputPromotionResult,
    preconditions: list[ActiveReplayInputPromotionPreconditionResult],
    human_gates: list[ActiveReplayInputPromotionHumanReviewResult],
) -> str:
    return "\n".join(
        [
            "# Active Replay Input Promotion",
            "",
            "Report-only core workflow. It reviews promotion readiness and stops before active replay input.",
            "",
            f"- promotion_run_id: {result.promotion_run_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- ready_for_human_review: {result.ready_for_human_review}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- precondition_count: {result.precondition_count}",
            f"- blocked_precondition_count: {result.blocked_precondition_count}",
            f"- human_review_gate_count: {result.human_review_gate_count}",
            f"- blocked_human_review_gate_count: {result.blocked_human_review_gate_count}",
            "",
            "## Preconditions",
            "",
            pd.DataFrame([row.__dict__ for row in preconditions]).to_markdown(index=False),
            "",
            "## Human Review Gates",
            "",
            pd.DataFrame([row.__dict__ for row in human_gates]).to_markdown(index=False),
            "",
            "## Safety",
            "",
            "No active replay input, replay, current-candidates, snapshots, forward labels, training, active stock profiles, buy-review eligibility, live trading, broker API, orders, messages, API calls, data-store writes, or cache mutation was invoked.",
        ]
    )


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Add artifact views for active-replay-input-promotion only after this core report-only command remains stable.",
            "",
            "Do not emit active-ready, run replay, compute labels, train weights, create stock profiles, create buy-review eligibility, or integrate research-status until explicitly scoped.",
        ]
    )


def _filter_group(frame: pd.DataFrame, group: str) -> pd.DataFrame:
    columns = ["gate_group", "gate_name", "status", "passed", "blocker_reason", "evidence_path"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return frame[frame["gate_group"] == group].reindex(columns=columns, fill_value="")


def _load_artifact_metadata(path: Path | None, file_name: str) -> tuple[dict[str, Any], Path | None]:
    if path is None:
        return {}, None
    resolved = Path(path)
    metadata_path = resolved if resolved.is_file() else resolved / file_name
    if not metadata_path.exists():
        return {}, resolved
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8")), resolved
    except json.JSONDecodeError:
        return {}, resolved


def _load_json_file(path: Path | None) -> tuple[dict[str, Any], Path | None]:
    if path is None:
        return {}, None
    resolved = Path(path)
    if not resolved.exists():
        return {}, resolved
    try:
        return json.loads(resolved.read_text(encoding="utf-8")), resolved
    except json.JSONDecodeError:
        return {}, resolved


def _promotion_run_id(
    *,
    settings: ActiveReplayInputPromotionSettings,
    validator_metadata: dict[str, Any],
    smoke_metadata: dict[str, Any],
    request_manifest: dict[str, Any],
    review_manifest: dict[str, Any],
    status: str,
) -> str:
    payload = {
        "version": settings.config_version,
        "validator_run_id": validator_metadata.get("validator_run_id"),
        "smoke_run_id": smoke_metadata.get("smoke_run_id"),
        "promotion_request_id": request_manifest.get("promotion_request_id"),
        "human_review_id": review_manifest.get("human_review_id"),
        "status": status,
        "validator_artifact": str(settings.validator_artifact or ""),
        "smoke_artifact": str(settings.smoke_artifact or ""),
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _same_path_text(text: str, path: Path | None) -> bool:
    if not text or path is None:
        return False
    try:
        return Path(text).resolve() == Path(path).resolve()
    except OSError:
        return str(Path(text)) == str(path)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_manual_diagnostics_path(path: str | Path) -> bool:
    return "outputs/reports/manual_diagnostics" in str(Path(path)).replace("\\", "/").lower()


def _no_data_store_path(path: str | Path) -> bool:
    normalized = str(Path(path)).replace("\\", "/").lower()
    return all(part not in normalized for part in ["data/raw", "data/processed", "data/cache"])


def _assert_settings_safe(settings: ActiveReplayInputPromotionSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Active replay input promotion must remain report-only and diagnostic-only.")
    if not _safe_manual_diagnostics_path(settings.output_dir):
        raise ValueError("Active replay input promotion output_dir must stay under outputs/reports/manual_diagnostics.")
    if not _no_data_store_path(settings.output_dir):
        raise ValueError("Active replay input promotion must not write data/raw, data/processed, or data/cache.")


__all__ = [
    "ActiveReplayInputPromotionHumanReviewResult",
    "ActiveReplayInputPromotionLineageResult",
    "ActiveReplayInputPromotionPreconditionResult",
    "ActiveReplayInputPromotionResult",
    "ActiveReplayInputPromotionSettings",
    "PROMOTION_READY_FOR_HUMAN_REVIEW",
    "resolve_active_replay_input_promotion_paths",
    "run_active_replay_input_promotion",
    "write_active_replay_input_promotion_artifacts",
]
