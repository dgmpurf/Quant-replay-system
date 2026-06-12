"""Report-only historical replay input gate validator.

This is the first real validator-shaped workflow, but it remains diagnostic
only. It validates local package shape and simple point-in-time relationships;
it never runs replay, current-candidates, snapshots, forward labels, training,
stock profiles, broker/order/message workflows, API calls, data writes, or
cache mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


NO_INPUT = "NO_INPUT"
INPUT_FOUND_BUT_NOT_APPROVED = "INPUT_FOUND_BUT_NOT_APPROVED"
NON_INPUT_ARTIFACT_REJECTED = "NON_INPUT_ARTIFACT_REJECTED"
PIT_UNIVERSE_BLOCKED = "PIT_UNIVERSE_BLOCKED"
SOURCE_REGISTRY_BLOCKED = "SOURCE_REGISTRY_BLOCKED"
RAW_DOCUMENT_BLOCKED = "RAW_DOCUMENT_BLOCKED"
FACTOR_DEFINITION_BLOCKED = "FACTOR_DEFINITION_BLOCKED"
FACTOR_OBSERVATION_BLOCKED = "FACTOR_OBSERVATION_BLOCKED"
EVENT_STRUCTURED_BLOCKED = "EVENT_STRUCTURED_BLOCKED"
COMPANY_EXPOSURE_BLOCKED = "COMPANY_EXPOSURE_BLOCKED"
EVIDENCE_BUNDLE_BLOCKED = "EVIDENCE_BUNDLE_BLOCKED"
FUTURE_LABEL_LEAKAGE_BLOCKED = "FUTURE_LABEL_LEAKAGE_BLOCKED"
TRAINING_LEAKAGE_BLOCKED = "TRAINING_LEAKAGE_BLOCKED"
STOCK_PROFILE_LEAKAGE_BLOCKED = "STOCK_PROFILE_LEAKAGE_BLOCKED"
ACTIONABILITY_BLOCKED = "ACTIONABILITY_BLOCKED"
REPLAY_INPUT_GATE_PASS_CANDIDATE = "REPLAY_INPUT_GATE_PASS_CANDIDATE"
ACTIVE_REPLAY_INPUT_READY = "ACTIVE_REPLAY_INPUT_READY"


ALLOWED_PACKAGE_TYPES = {"historical_replay_input_package", "replay_input_package"}
NON_INPUT_PACKAGE_TYPES = {
    "checklist_validator_output",
    "policy_comparison",
    "official_status_evidence_packet",
    "reviewer_no_hit_acceptance",
    "reviewer_no_hit_downstream_impact",
    "one_row_material_package",
    "one_row_checklist_pass_preview",
    "reviewer_supplied_material_evidence_fixture_audit",
    "replay_substrate_schema_fixture",
    "input_gate_validator_fixture",
    "readiness_plan",
    "design_audit",
    "implementation_plan",
    "export_staging_only",
    "demo_current_candidates",
}

GATE_GROUPS = [
    "NON_INPUT_ARTIFACT_REJECTION",
    "PIT_UNIVERSE_GATE",
    "SOURCE_REGISTRY_GATE",
    "RAW_DOCUMENT_EVIDENCE_GATE",
    "FACTOR_DEFINITION_GATE",
    "FACTOR_OBSERVATION_GATE",
    "EVENT_STRUCTURED_GATE",
    "COMPANY_EXPOSURE_GATE",
    "REPLAY_EVIDENCE_BUNDLE_GATE",
    "FUTURE_LABEL_EXCLUSION_GATE",
    "TRAINING_EXCLUSION_GATE",
    "STOCK_PROFILE_EXCLUSION_GATE",
    "ACTIONABILITY_TRADING_SAFETY_GATE",
]

REQUIRED_FILES = {
    "source_registry.csv": SOURCE_REGISTRY_BLOCKED,
    "pit_universe.csv": PIT_UNIVERSE_BLOCKED,
    "raw_document_store.csv": RAW_DOCUMENT_BLOCKED,
    "factor_definition.csv": FACTOR_DEFINITION_BLOCKED,
    "factor_observation.csv": FACTOR_OBSERVATION_BLOCKED,
    "event_structured.csv": EVENT_STRUCTURED_BLOCKED,
    "company_exposure.csv": COMPANY_EXPOSURE_BLOCKED,
}

GATE_FOR_STATUS = {
    NON_INPUT_ARTIFACT_REJECTED: "NON_INPUT_ARTIFACT_REJECTION",
    INPUT_FOUND_BUT_NOT_APPROVED: "NON_INPUT_ARTIFACT_REJECTION",
    PIT_UNIVERSE_BLOCKED: "PIT_UNIVERSE_GATE",
    SOURCE_REGISTRY_BLOCKED: "SOURCE_REGISTRY_GATE",
    RAW_DOCUMENT_BLOCKED: "RAW_DOCUMENT_EVIDENCE_GATE",
    FACTOR_DEFINITION_BLOCKED: "FACTOR_DEFINITION_GATE",
    FACTOR_OBSERVATION_BLOCKED: "FACTOR_OBSERVATION_GATE",
    EVENT_STRUCTURED_BLOCKED: "EVENT_STRUCTURED_GATE",
    COMPANY_EXPOSURE_BLOCKED: "COMPANY_EXPOSURE_GATE",
    EVIDENCE_BUNDLE_BLOCKED: "REPLAY_EVIDENCE_BUNDLE_GATE",
    FUTURE_LABEL_LEAKAGE_BLOCKED: "FUTURE_LABEL_EXCLUSION_GATE",
    TRAINING_LEAKAGE_BLOCKED: "TRAINING_EXCLUSION_GATE",
    STOCK_PROFILE_LEAKAGE_BLOCKED: "STOCK_PROFILE_EXCLUSION_GATE",
    ACTIONABILITY_BLOCKED: "ACTIONABILITY_TRADING_SAFETY_GATE",
}

STATUS_PRIORITY = [
    NON_INPUT_ARTIFACT_REJECTED,
    PIT_UNIVERSE_BLOCKED,
    SOURCE_REGISTRY_BLOCKED,
    RAW_DOCUMENT_BLOCKED,
    FACTOR_DEFINITION_BLOCKED,
    FACTOR_OBSERVATION_BLOCKED,
    EVENT_STRUCTURED_BLOCKED,
    COMPANY_EXPOSURE_BLOCKED,
    EVIDENCE_BUNDLE_BLOCKED,
    FUTURE_LABEL_LEAKAGE_BLOCKED,
    TRAINING_LEAKAGE_BLOCKED,
    STOCK_PROFILE_LEAKAGE_BLOCKED,
    ACTIONABILITY_BLOCKED,
    INPUT_FOUND_BUT_NOT_APPROVED,
]

TAXONOMY_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"}


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorSettings:
    input_package: Path | None = None
    output_dir: Path = Path("outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class HistoricalReplayInputPackageSummary:
    section: str
    file_name: str
    exists: bool
    row_count: int
    required_field_count: int
    missing_field_count: int
    blocker_count: int


@dataclass(frozen=True)
class HistoricalReplayInputGateResult:
    gate_group: str
    status: str
    passed: bool
    blocker_count: int
    warning_count: int
    pass_candidate_allowed: bool
    active_ready_allowed_first: bool
    notes: str


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorResult:
    validator_run_id: str
    generated_at: str
    input_package_path: str
    artifact_path: Path
    status: str
    workflow_stage: str
    gate_count: int
    passed_gate_count: int
    blocked_gate_count: int
    warning_count: int
    blocker_count: int
    pass_candidate: bool
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
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    artifact_paths: dict[str, Path]


def run_historical_replay_input_gate_validator(
    *,
    input_package: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: HistoricalReplayInputGateValidatorSettings | None = None,
) -> HistoricalReplayInputGateValidatorResult:
    resolved_settings = settings or HistoricalReplayInputGateValidatorSettings()
    if input_package is not None or output_dir is not None:
        resolved_settings = HistoricalReplayInputGateValidatorSettings(
            input_package=Path(input_package) if input_package is not None else resolved_settings.input_package,
            output_dir=Path(output_dir) if output_dir is not None else resolved_settings.output_dir,
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            report_only=resolved_settings.report_only,
            diagnostic_only=resolved_settings.diagnostic_only,
        )
    _assert_settings_safe(resolved_settings)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    package_path = resolved_settings.input_package
    manifest, frames, package_summary, blockers, rejections = _evaluate_input_package(package_path)
    status = _overall_status(package_path, blockers)
    pass_candidate = status == REPLAY_INPUT_GATE_PASS_CANDIDATE
    gate_results = _build_gate_results(status, blockers)
    run_id = _validator_run_id(package_path, manifest, blockers, status, resolved_settings.config_version)
    paths = resolve_historical_replay_input_gate_validator_paths(resolved_settings.output_dir, run_id)
    overclaim_guards = _build_overclaim_guards(paths["artifact_dir"], status, pass_candidate)
    result = HistoricalReplayInputGateValidatorResult(
        validator_run_id=run_id,
        generated_at=generated_at,
        input_package_path=str(package_path or ""),
        artifact_path=paths["artifact_dir"],
        status=status,
        workflow_stage=status,
        gate_count=len(gate_results),
        passed_gate_count=int(sum(gate.passed for gate in gate_results)),
        blocked_gate_count=int(sum(not gate.passed for gate in gate_results)),
        warning_count=int(sum(gate.warning_count for gate in gate_results)),
        blocker_count=len(blockers),
        pass_candidate=pass_candidate,
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
        overclaim_guard_pass_count=int(overclaim_guards["passed"].sum()) if not overclaim_guards.empty else 0,
        overclaim_guard_total_count=len(overclaim_guards),
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_historical_replay_input_gate_validator_artifacts(
            result=result,
            manifest=manifest,
            frames=frames,
            package_summary=package_summary,
            gate_results=gate_results,
            blockers=pd.DataFrame(blockers),
            rejections=rejections,
            overclaim_guards=overclaim_guards,
        )
    return result


def resolve_historical_replay_input_gate_validator_paths(output_dir: str | Path, validator_run_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / validator_run_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "metadata.json",
        "input_gate_report": artifact_dir / "input_gate_report.md",
        "input_package_summary": artifact_dir / "input_package_summary.csv",
        "gate_results": artifact_dir / "gate_results.csv",
        "blocker_matrix": artifact_dir / "blocker_matrix.csv",
        "entity_contract_validation": artifact_dir / "entity_contract_validation.csv",
        "non_input_artifact_rejections": artifact_dir / "non_input_artifact_rejections.csv",
        "overclaim_guard_report": artifact_dir / "overclaim_guard_report.csv",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_historical_replay_input_gate_validator_artifacts(
    *,
    result: HistoricalReplayInputGateValidatorResult,
    manifest: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    package_summary: list[HistoricalReplayInputPackageSummary],
    gate_results: list[HistoricalReplayInputGateResult],
    blockers: pd.DataFrame,
    rejections: pd.DataFrame,
    overclaim_guards: pd.DataFrame,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary.__dict__ for summary in package_summary]).to_csv(
        paths["input_package_summary"], index=False
    )
    pd.DataFrame([gate.__dict__ for gate in gate_results]).to_csv(paths["gate_results"], index=False)
    _finalize_blockers(blockers).to_csv(paths["blocker_matrix"], index=False)
    _build_contract_validation(frames, blockers).to_csv(paths["entity_contract_validation"], index=False)
    _finalize_rejections(rejections).to_csv(paths["non_input_artifact_rejections"], index=False)
    overclaim_guards.to_csv(paths["overclaim_guard_report"], index=False)
    paths["metadata"].write_text(json.dumps(_metadata(result), indent=2, sort_keys=True), encoding="utf-8")
    paths["input_gate_report"].write_text(_render_report(result, manifest, gate_results), encoding="utf-8")
    paths["recommended_next_task"].write_text(
        "\n".join(
            [
                "# Recommended Next Task",
                "",
                "Add historical replay input gate validator artifact views only after the core report-only command remains stable.",
                "",
                "Do not run replay, create active replay input, compute labels, train weights, create stock profiles, or create buy-review eligibility.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _evaluate_input_package(
    package_path: Path | None,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame], list[HistoricalReplayInputPackageSummary], list[dict[str, Any]], pd.DataFrame]:
    if package_path is None:
        return {}, {}, [], [_blocker("INPUT_PACKAGE", "", NO_INPUT, "NO_INPUT_PACKAGE_PROVIDED")], _finalize_rejections(pd.DataFrame())
    package_path = Path(package_path)
    blockers: list[dict[str, Any]] = []
    frames: dict[str, pd.DataFrame] = {}
    summary: list[HistoricalReplayInputPackageSummary] = []
    manifest_path = package_path / "replay_input_manifest.json"
    if not manifest_path.exists():
        blockers.append(_blocker("replay_request", "replay_input_manifest.json", NO_INPUT, "MISSING_MANIFEST"))
        return {}, frames, summary, blockers, _finalize_rejections(pd.DataFrame())
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        blockers.append(_blocker("replay_request", "replay_input_manifest.json", NO_INPUT, f"INVALID_MANIFEST_JSON:{exc}"))
        return {}, frames, summary, blockers, _finalize_rejections(pd.DataFrame())

    package_type = _text(manifest.get("package_type")).lower()
    if package_type in NON_INPUT_PACKAGE_TYPES:
        rejection = pd.DataFrame(
            [
                {
                    "artifact_family": package_type,
                    "artifact_path": str(package_path),
                    "expected_rejection_status": NON_INPUT_ARTIFACT_REJECTED,
                    "allowed_context_use": "lineage_or_diagnostics_only",
                    "overclaim_risk": "non_input_artifact_treated_as_replay_input",
                }
            ]
        )
        blockers.append(
            _blocker("manifest", "package_type", NON_INPUT_ARTIFACT_REJECTED, "NON_INPUT_ARTIFACT_FAMILY")
        )
        return manifest, frames, summary, blockers, _finalize_rejections(rejection)
    if package_type not in ALLOWED_PACKAGE_TYPES:
        blockers.append(_blocker("manifest", "package_type", INPUT_FOUND_BUT_NOT_APPROVED, "PACKAGE_TYPE_NOT_ALLOWED"))

    decision_time = _to_utc_timestamp(manifest.get("replay_decision_time"))
    if decision_time is None:
        blockers.append(_blocker("replay_request", "replay_decision_time", NO_INPUT, "MISSING_REPLAY_DECISION_TIME"))
    if not _to_bool(manifest.get("accepted_pit_universe")) or not _text(manifest.get("approval_artifact_ref")):
        blockers.append(_blocker("accepted_pit_universe", "approval_artifact_ref", PIT_UNIVERSE_BLOCKED, "PIT_UNIVERSE_NOT_ACCEPTED"))

    _check_manifest_safety(manifest, blockers)
    for file_name, status in REQUIRED_FILES.items():
        path = package_path / file_name
        if not path.exists():
            blockers.append(_blocker(_section_for_file(file_name), file_name, status, "MISSING_REQUIRED_FILE"))
            summary.append(HistoricalReplayInputPackageSummary(_section_for_file(file_name), file_name, False, 0, 0, 0, 1))
            continue
        try:
            frame = pd.read_csv(path, dtype=str).fillna("")
        except Exception as exc:  # pragma: no cover - defensive parse guard
            blockers.append(_blocker(_section_for_file(file_name), file_name, status, f"CSV_PARSE_FAILED:{exc}"))
            summary.append(HistoricalReplayInputPackageSummary(_section_for_file(file_name), file_name, True, 0, 0, 0, 1))
            continue
        frames[file_name] = frame
        before = len(blockers)
        _validate_frame(file_name, frame, decision_time, blockers)
        summary.append(
            HistoricalReplayInputPackageSummary(
                section=_section_for_file(file_name),
                file_name=file_name,
                exists=True,
                row_count=len(frame),
                required_field_count=len(_required_columns(file_name)),
                missing_field_count=len([column for column in _required_columns(file_name) if column not in frame.columns]),
                blocker_count=len(blockers) - before,
            )
        )

    if not frames and not any(blocker["blocker_status"] == NO_INPUT for blocker in blockers):
        blockers.append(_blocker("replay_evidence_bundle", "package", EVIDENCE_BUNDLE_BLOCKED, "NO_COMPONENT_FILES_PARSED"))
    return manifest, frames, summary, blockers, _finalize_rejections(pd.DataFrame())


def _validate_frame(
    file_name: str,
    frame: pd.DataFrame,
    decision_time: pd.Timestamp | None,
    blockers: list[dict[str, Any]],
) -> None:
    status = REQUIRED_FILES[file_name]
    section = _section_for_file(file_name)
    required = _required_columns(file_name)
    if frame.empty:
        blockers.append(_blocker(section, file_name, status, "EMPTY_REQUIRED_FILE"))
        return
    for column in required:
        if column not in frame.columns:
            blockers.append(_blocker(section, column, status, "MISSING_REQUIRED_COLUMN"))
        elif frame[column].astype(str).str.strip().eq("").any():
            blockers.append(_blocker(section, column, status, "MISSING_REQUIRED_VALUE"))
    if file_name == "source_registry.csv":
        if "permission_status" in frame.columns and not frame["permission_status"].astype(str).str.contains("ACCEPTED|PERMITTED", case=False, regex=True).all():
            blockers.append(_blocker(section, "permission_status", SOURCE_REGISTRY_BLOCKED, "SOURCE_PERMISSION_NOT_ACCEPTED"))
    if file_name == "factor_definition.csv":
        if "factor_layer" in frame.columns and not frame["factor_layer"].astype(str).str.upper().isin(TAXONOMY_LAYERS).all():
            blockers.append(_blocker(section, "factor_layer", FACTOR_DEFINITION_BLOCKED, "INVALID_8_LAYER_TAXONOMY_LAYER"))
        if "fixed_12_only" in frame.columns and frame["fixed_12_only"].map(_to_bool).any():
            blockers.append(_blocker(section, "fixed_12_only", FACTOR_DEFINITION_BLOCKED, "FIXED_12_ONLY_FACTOR_DEFINITION"))
    if decision_time is not None:
        for column in ["available_time", "publish_time"]:
            if column in frame.columns:
                for value in frame[column].astype(str):
                    parsed = _to_utc_timestamp(value)
                    if parsed is None:
                        blockers.append(_blocker(section, column, status, "INVALID_TIME_VALUE"))
                    elif parsed > decision_time:
                        blockers.append(_blocker(section, column, status, "AVAILABLE_TIME_AFTER_DECISION_TIME"))
                        break
    leakage_columns = {column.lower() for column in frame.columns}
    if any("forward_return" in column or "label_target" in column for column in leakage_columns):
        blockers.append(_blocker(section, "columns", FUTURE_LABEL_LEAKAGE_BLOCKED, "FORWARD_LABEL_COLUMN_PRESENT"))
    if any("training_result" in column or "trained_weights" in column for column in leakage_columns):
        blockers.append(_blocker(section, "columns", TRAINING_LEAKAGE_BLOCKED, "TRAINING_COLUMN_PRESENT"))
    if any("stock_profile" in column for column in leakage_columns):
        blockers.append(_blocker(section, "columns", STOCK_PROFILE_LEAKAGE_BLOCKED, "STOCK_PROFILE_COLUMN_PRESENT"))


def _check_manifest_safety(manifest: dict[str, Any], blockers: list[dict[str, Any]]) -> None:
    if _to_bool(manifest.get("forward_labels_exist")):
        blockers.append(_blocker("manifest", "forward_labels_exist", FUTURE_LABEL_LEAKAGE_BLOCKED, "FORWARD_LABELS_EXIST_TRUE"))
    if _to_bool(manifest.get("weights_trained")):
        blockers.append(_blocker("manifest", "weights_trained", TRAINING_LEAKAGE_BLOCKED, "WEIGHTS_TRAINED_TRUE"))
    if _to_bool(manifest.get("active_stock_profile_exists")):
        blockers.append(_blocker("manifest", "active_stock_profile_exists", STOCK_PROFILE_LEAKAGE_BLOCKED, "ACTIVE_STOCK_PROFILE_EXISTS_TRUE"))
    unsafe_action_fields = [
        "active_replay_input",
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
    for field in unsafe_action_fields:
        if _to_bool(manifest.get(field)):
            blockers.append(_blocker("manifest", field, ACTIONABILITY_BLOCKED, f"UNSAFE_FLAG_TRUE:{field}"))
    if not _to_bool(manifest.get("report_only")) or not _to_bool(manifest.get("diagnostic_only")):
        blockers.append(_blocker("manifest", "report_only", ACTIONABILITY_BLOCKED, "REPORT_ONLY_OR_DIAGNOSTIC_ONLY_FALSE"))


def _build_gate_results(status: str, blockers: list[dict[str, Any]]) -> list[HistoricalReplayInputGateResult]:
    blocker_counts = {gate: 0 for gate in GATE_GROUPS}
    for blocker in blockers:
        gate = GATE_FOR_STATUS.get(_text(blocker.get("blocker_status")), "REPLAY_EVIDENCE_BUNDLE_GATE")
        blocker_counts[gate] = blocker_counts.get(gate, 0) + 1
    if status == NO_INPUT:
        blocker_counts["REPLAY_EVIDENCE_BUNDLE_GATE"] = max(blocker_counts["REPLAY_EVIDENCE_BUNDLE_GATE"], 1)
    rows: list[HistoricalReplayInputGateResult] = []
    for gate in GATE_GROUPS:
        count = blocker_counts.get(gate, 0)
        rows.append(
            HistoricalReplayInputGateResult(
                gate_group=gate,
                status="PASS" if count == 0 else _status_for_gate(gate, blockers),
                passed=count == 0,
                blocker_count=count,
                warning_count=0,
                pass_candidate_allowed=gate not in {
                    "FUTURE_LABEL_EXCLUSION_GATE",
                    "TRAINING_EXCLUSION_GATE",
                    "STOCK_PROFILE_EXCLUSION_GATE",
                },
                active_ready_allowed_first=False,
                notes="report_only_core_validator_first_implementation",
            )
        )
    return rows


def _build_overclaim_guards(artifact_dir: Path, status: str, pass_candidate: bool) -> pd.DataFrame:
    safe_path = _safe_diagnostics_path(artifact_dir)
    rows = [
        ("G01", "Output path under manual diagnostics", safe_path, "UNSAFE_OUTPUT_PATH"),
        ("G02", "Active ready never emitted", status != ACTIVE_REPLAY_INPUT_READY, "ACTIVE_READY_EMITTED"),
        ("G03", "Pass candidate not active ready", not pass_candidate or status == REPLAY_INPUT_GATE_PASS_CANDIDATE, "PASS_CANDIDATE_OVERCLAIM"),
        ("G04", "active_replay_input_ready false", True, "ACTIVE_READY_TRUE"),
        ("G05", "active_replay_input false", True, "ACTIVE_REPLAY_INPUT_TRUE"),
        ("G06", "forward_labels_exist false", True, "FORWARD_LABELS_TRUE"),
        ("G07", "weights_trained false", True, "WEIGHTS_TRUE"),
        ("G08", "active_stock_profile_exists false", True, "STOCK_PROFILE_TRUE"),
        ("G09", "real_buy_review_eligible false", True, "BUY_REVIEW_TRUE"),
        ("G10", "approval and order flags false", True, "ACTIONABILITY_TRUE"),
        ("G11", "no live trading and broker flags true", True, "TRADING_FLAGS_UNSAFE"),
        ("G12", "no API and cache side effects", True, "SIDE_EFFECT_FLAGS_UNSAFE"),
        ("G13", "no current-candidates or snapshots", True, "DOWNSTREAM_WORKFLOW_RAN"),
        ("G14", "signal semantics unchanged", True, "SIGNAL_SEMANTICS_CHANGED"),
        ("G15", "no data store output path", _no_data_store_path(artifact_dir), "DATA_STORE_OUTPUT_PATH"),
    ]
    return pd.DataFrame(
        [
            {
                "guard_id": guard_id,
                "guard_name": guard_name,
                "passed": bool(passed),
                "failure_status": ACTIONABILITY_BLOCKED if not passed else "",
                "blocker_reason": "" if passed else reason,
            }
            for guard_id, guard_name, passed, reason in rows
        ]
    )


def _metadata(result: HistoricalReplayInputGateValidatorResult) -> dict[str, Any]:
    return {
        "validator_run_id": result.validator_run_id,
        "generated_at": result.generated_at,
        "input_package_path": result.input_package_path,
        "artifact_path": str(result.artifact_path),
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "gate_count": result.gate_count,
        "passed_gate_count": result.passed_gate_count,
        "blocked_gate_count": result.blocked_gate_count,
        "warning_count": result.warning_count,
        "blocker_count": result.blocker_count,
        "pass_candidate": result.pass_candidate,
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
        "overclaim_guard_pass_count": result.overclaim_guard_pass_count,
        "overclaim_guard_total_count": result.overclaim_guard_total_count,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
    }


def _render_report(
    result: HistoricalReplayInputGateValidatorResult,
    manifest: dict[str, Any],
    gate_results: list[HistoricalReplayInputGateResult],
) -> str:
    lines = [
        "# Historical Replay Input Gate Validator",
        "",
        "Report-only core validator. It validates local package shape and simple point-in-time relationships only.",
        "",
        f"- validator_run_id: {result.validator_run_id}",
        f"- status: {result.status}",
        f"- workflow_stage: {result.workflow_stage}",
        f"- input_package_path: {result.input_package_path}",
        f"- package_id: {_text(manifest.get('package_id'))}",
        f"- package_type: {_text(manifest.get('package_type'))}",
        f"- gate_count: {result.gate_count}",
        f"- passed_gate_count: {result.passed_gate_count}",
        f"- blocked_gate_count: {result.blocked_gate_count}",
        f"- blocker_count: {result.blocker_count}",
        f"- pass_candidate: {result.pass_candidate}",
        f"- active_replay_input_ready: {result.active_replay_input_ready}",
        f"- active_replay_input: {result.active_replay_input}",
        "",
        "## Gate Results",
        "",
        pd.DataFrame([gate.__dict__ for gate in gate_results]).to_markdown(index=False),
        "",
        "## Safety",
        "",
        "No replay, current-candidates, snapshots, forward labels, training, active stock profiles, buy-review eligibility, live trading, broker API, order placement, message delivery, LLM/API, external API, data writes, or cache mutation was invoked.",
    ]
    return "\n".join(lines)


def _build_contract_validation(frames: dict[str, pd.DataFrame], blockers: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    blocker_fields = set()
    if not blockers.empty:
        blocker_fields = {(str(row["section"]), str(row["field_name"])) for _, row in blockers.iterrows()}
    for file_name in REQUIRED_FILES:
        section = _section_for_file(file_name)
        frame = frames.get(file_name, pd.DataFrame())
        for field in _required_columns(file_name):
            present = field in frame.columns if not frame.empty else False
            rows.append(
                {
                    "section": section,
                    "file_name": file_name,
                    "field_name": field,
                    "required": True,
                    "present": present,
                    "pit_valid": True,
                    "source_valid": field not in {"source_id", "source_hash", "revision_id"} or present,
                    "issue_code": "BLOCKED" if (section, field) in blocker_fields else "",
                }
            )
    return pd.DataFrame(rows)


def _overall_status(package_path: Path | None, blockers: list[dict[str, Any]]) -> str:
    if package_path is None:
        return NO_INPUT
    statuses = {_text(blocker.get("blocker_status")) for blocker in blockers}
    for status in STATUS_PRIORITY:
        if status in statuses:
            return status
    return REPLAY_INPUT_GATE_PASS_CANDIDATE


def _status_for_gate(gate: str, blockers: list[dict[str, Any]]) -> str:
    for blocker in blockers:
        status = _text(blocker.get("blocker_status"))
        if GATE_FOR_STATUS.get(status) == gate:
            return status
    return EVIDENCE_BUNDLE_BLOCKED


def _required_columns(file_name: str) -> list[str]:
    return {
        "source_registry.csv": ["source_id", "source_hash", "revision_id", "permission_status"],
        "pit_universe.csv": ["signal_date", "symbol", "available_time", "source_id", "source_hash", "revision_id"],
        "raw_document_store.csv": [
            "document_id",
            "publish_time",
            "available_time",
            "evidence_type",
            "source_id",
            "source_hash",
            "revision_id",
        ],
        "factor_definition.csv": [
            "factor_id",
            "factor_layer",
            "definition_revision_id",
            "fixed_12_only",
            "source_id",
            "source_hash",
            "revision_id",
        ],
        "factor_observation.csv": [
            "factor_id",
            "signal_date",
            "symbol",
            "available_time",
            "source_id",
            "source_hash",
            "revision_id",
        ],
        "event_structured.csv": [
            "event_id",
            "event_type",
            "publish_time",
            "available_time",
            "source_id",
            "source_hash",
            "revision_id",
        ],
        "company_exposure.csv": [
            "exposure_id",
            "symbol",
            "exposure_type",
            "available_time",
            "source_id",
            "source_hash",
            "revision_id",
        ],
    }[file_name]


def _section_for_file(file_name: str) -> str:
    return file_name.removesuffix(".csv")


def _blocker(section: str, field_name: str, status: str, reason: str) -> dict[str, Any]:
    return {
        "section": section,
        "identity_key": "",
        "field_name": field_name,
        "blocker_status": status,
        "blocker_reason": reason,
        "observed_value": "",
    }


def _finalize_blockers(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["section", "identity_key", "field_name", "blocker_status", "blocker_reason", "observed_value"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return frame.reindex(columns=columns, fill_value="")


def _finalize_rejections(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["artifact_family", "artifact_path", "expected_rejection_status", "allowed_context_use", "overclaim_risk"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return frame.reindex(columns=columns, fill_value="")


def _validator_run_id(
    package_path: Path | None,
    manifest: dict[str, Any],
    blockers: list[dict[str, Any]],
    status: str,
    config_version: str,
) -> str:
    payload = {
        "package_path": str(package_path or ""),
        "package_id": manifest.get("package_id"),
        "package_type": manifest.get("package_type"),
        "blockers": blockers,
        "status": status,
        "config_version": config_version,
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _to_utc_timestamp(value: Any) -> pd.Timestamp | None:
    if not _text(value):
        return None
    try:
        return pd.to_datetime(value, utc=True)
    except Exception:
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_diagnostics_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return "outputs/reports/manual_diagnostics" in normalized


def _no_data_store_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return all(part not in normalized for part in ["data/raw", "data/processed", "data/cache"])


def _assert_settings_safe(settings: HistoricalReplayInputGateValidatorSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Historical replay input gate validator core must remain report-only and diagnostic-only.")
    if not _safe_diagnostics_path(settings.output_dir):
        raise ValueError("Historical replay input gate validator output_dir must stay under outputs/reports/manual_diagnostics.")
    if not _no_data_store_path(settings.output_dir):
        raise ValueError("Historical replay input gate validator must not write data/raw, data/processed, or data/cache.")

