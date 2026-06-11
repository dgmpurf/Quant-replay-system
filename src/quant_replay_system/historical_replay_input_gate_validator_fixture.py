"""Report-only fixtures for a future historical replay input gate validator.

This module writes synthetic/manual fixture cases for future validator tests.
It is not the validator, does not validate real replay inputs, and never runs
replay, current-candidates, snapshots, labels, training, stock profiles,
broker/order/message workflows, API calls, data writes, or cache mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DESIGN_ONLY = "DESIGN_ONLY"
NO_INPUT = "NO_INPUT"
INPUT_FOUND_BUT_NOT_APPROVED = "INPUT_FOUND_BUT_NOT_APPROVED"
PIT_UNIVERSE_BLOCKED = "PIT_UNIVERSE_BLOCKED"
SOURCE_REGISTRY_BLOCKED = "SOURCE_REGISTRY_BLOCKED"
FACTOR_OBSERVATION_BLOCKED = "FACTOR_OBSERVATION_BLOCKED"
EVENT_STRUCTURED_BLOCKED = "EVENT_STRUCTURED_BLOCKED"
EVIDENCE_BUNDLE_BLOCKED = "EVIDENCE_BUNDLE_BLOCKED"
REPLAY_INPUT_GATE_PASS_CANDIDATE = "REPLAY_INPUT_GATE_PASS_CANDIDATE"
ACTIVE_REPLAY_INPUT_READY = "ACTIVE_REPLAY_INPUT_READY"


EXPECTED_FIXTURE_CASE_GROUP_COUNTS = {
    "NON_REPLAY_ARTIFACT_REJECTION": 13,
    "PIT_UNIVERSE_BLOCKED": 8,
    "SOURCE_REGISTRY_BLOCKED": 6,
    "RAW_DOCUMENT_EVIDENCE_BLOCKED": 7,
    "FACTOR_DEFINITION_BLOCKED": 8,
    "FACTOR_OBSERVATION_BLOCKED": 9,
    "EVENT_STRUCTURED_BLOCKED": 8,
    "COMPANY_EXPOSURE_BLOCKED": 7,
    "REPLAY_INPUT_PASS_CANDIDATE": 1,
    "ACTIVE_READY_BOUNDARY": 1,
}

SAFETY_FALSE_FIELDS = [
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "validator_implemented",
    "active_ready_status_allowed",
]

SAFETY_TRUE_FIELDS = [
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    enable_replay: bool = False
    enable_current_candidates: bool = False
    enable_snapshot_build: bool = False
    enable_forward_labels: bool = False
    enable_weight_training: bool = False
    enable_active_stock_profile: bool = False
    enable_real_buy_review: bool = False
    enable_data_raw_write: bool = False
    enable_data_processed_write: bool = False
    enable_data_cache_write: bool = False
    enable_cache_mutation: bool = False
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False
    enable_llm_api: bool = False
    enable_external_api: bool = False
    enable_approved_for_paper: bool = False


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorFixtureResult:
    fixture_run_id: str
    status: str
    generated_at: str
    artifact_path: Path
    case_count: int
    blocked_case_count: int
    pass_candidate_case_count: int
    active_ready_case_count: int
    expected_status_counts: dict[str, int]
    validation_issue_count: int
    overclaim_guard_pass_count: int
    overclaim_guard_total_count: int
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    validator_implemented: bool
    active_ready_status_allowed: bool
    artifact_paths: dict[str, Path]


def build_historical_replay_input_gate_validator_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: HistoricalReplayInputGateValidatorFixtureSettings | None = None,
) -> HistoricalReplayInputGateValidatorFixtureResult:
    resolved_settings = settings or HistoricalReplayInputGateValidatorFixtureSettings()
    if output_dir is not None:
        resolved_settings = HistoricalReplayInputGateValidatorFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    cases = build_fixture_cases()
    blocked_requirements = build_blocked_requirements(cases)
    expected_status = build_expected_status_matrix(cases)
    fixture_input_schema = build_fixture_input_schema()
    fixture_run_id = _fixture_run_id(cases, resolved_settings.config_version)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    paths = resolve_historical_replay_input_gate_validator_fixture_paths(
        resolved_settings.output_dir, fixture_run_id
    )
    safety = _safety_metadata()
    overclaim_guards = build_overclaim_guard_report(cases, paths, safety)
    validation_issues = _validation_issues(cases, overclaim_guards)
    status_counts = {str(key): int(value) for key, value in cases["expected_status"].value_counts().sort_index().items()}

    result = HistoricalReplayInputGateValidatorFixtureResult(
        fixture_run_id=fixture_run_id,
        status="PASS" if validation_issues.empty and bool(overclaim_guards["passed"].all()) else "FAIL",
        generated_at=generated_at,
        artifact_path=paths["artifact_dir"],
        case_count=len(cases),
        blocked_case_count=int((cases["expected_status"] != REPLAY_INPUT_GATE_PASS_CANDIDATE).sum()),
        pass_candidate_case_count=int((cases["expected_status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE).sum()),
        active_ready_case_count=int((cases["expected_status"] == ACTIVE_REPLAY_INPUT_READY).sum()),
        expected_status_counts=status_counts,
        validation_issue_count=len(validation_issues),
        overclaim_guard_pass_count=int(overclaim_guards["passed"].sum()),
        overclaim_guard_total_count=len(overclaim_guards),
        active_replay_input=False,
        forward_labels_exist=False,
        weights_trained=False,
        active_stock_profile_exists=False,
        real_buy_review_eligible=False,
        report_only=True,
        diagnostic_only=True,
        no_live_trading=True,
        no_broker_api=True,
        no_order_placement=True,
        no_message_sent=True,
        llm_api_called=False,
        external_api_called=False,
        cache_mutated=False,
        current_candidates_run=False,
        snapshot_built=False,
        signal_semantics_changed=False,
        validator_implemented=False,
        active_ready_status_allowed=False,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_historical_replay_input_gate_validator_fixture_artifacts(
            result=result,
            cases=cases,
            blocked_requirements=blocked_requirements,
            expected_status=expected_status,
            fixture_input_schema=fixture_input_schema,
            overclaim_guards=overclaim_guards,
            validation_issues=validation_issues,
            settings=resolved_settings,
        )
    return result


def build_fixture_cases() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add(
        case_id: str,
        case_group: str,
        fixture_name: str,
        fixture_intent: str,
        expected_status: str,
        expected_blocker_count: int,
        reason: str,
    ) -> None:
        rows.append(
            {
                "case_id": case_id,
                "case_group": case_group,
                "fixture_name": fixture_name,
                "fixture_intent": fixture_intent,
                "expected_status": expected_status,
                "expected_blocker_count": expected_blocker_count,
                "active_allowed": False,
                "should_block_replay": True,
                "should_block_forward_labels": True,
                "should_block_training": True,
                "should_block_stock_profile": True,
                "should_block_buy_review": True,
                "symbol": "000001" if case_id.endswith("01") or case_id == "PASS01" else "",
                "reason": reason,
            }
        )

    for case_id, name, status, reason in [
        ("NRA01", "checklist_validator_output_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Checklist output is diagnostic and not approval"),
        ("NRA02", "policy_comparison_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Policy comparison is context only"),
        ("NRA03", "official_status_packet_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Evidence packet is not reviewed replay input"),
        ("NRA04", "reviewer_no_hit_acceptance_rejected", PIT_UNIVERSE_BLOCKED, "No-hit context is supporting context only"),
        ("NRA05", "reviewer_no_hit_downstream_impact_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Impact report does not create approval"),
        ("NRA06", "one_row_material_package_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Context fields are not material closure"),
        ("NRA07", "one_row_checklist_pass_preview_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Preview is not active readiness"),
        ("NRA08", "reviewer_supplied_fixture_audit_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Audit proposal is not evidence"),
        ("NRA09", "replay_substrate_schema_fixture_rejected", DESIGN_ONLY, "Schema fixture is synthetic and inactive"),
        ("NRA10", "historical_replay_readiness_plan_rejected", DESIGN_ONLY, "Plan is not an input artifact"),
        ("NRA11", "input_gate_validator_design_audit_rejected", DESIGN_ONLY, "Design audit is not implementation"),
        ("NRA12", "demo_current_candidates_rejected", INPUT_FOUND_BUT_NOT_APPROVED, "Demo candidates are not replay input"),
        ("NRA13", "export_staging_only_rejected", PIT_UNIVERSE_BLOCKED, "Staging preview is not data/raw export"),
    ]:
        add(case_id, "NON_REPLAY_ARTIFACT_REJECTION", name, "Reject non-replay artifact as active replay input", status, 1, reason)

    for index, (name, status, reason) in enumerate(
        [
            ("no_approved_pit_universe", PIT_UNIVERSE_BLOCKED, "PIT approval missing"),
            ("export_ready_missing", PIT_UNIVERSE_BLOCKED, "Export-ready gate missing"),
            ("staged_only_not_approved", INPUT_FOUND_BUT_NOT_APPROVED, "Staged-only artifact cannot be active input"),
            ("available_time_after_decision", PIT_UNIVERSE_BLOCKED, "Timing policy violated"),
            ("missing_revision_id", PIT_UNIVERSE_BLOCKED, "Lineage incomplete"),
            ("missing_source_lineage", PIT_UNIVERSE_BLOCKED, "Source lineage incomplete"),
            ("future_status_leakage", PIT_UNIVERSE_BLOCKED, "Future status leakage"),
            ("checklist_preview_as_approval", INPUT_FOUND_BUT_NOT_APPROVED, "Preview cannot become approval"),
        ],
        start=1,
    ):
        add(f"PIT{index:02d}", "PIT_UNIVERSE_BLOCKED", name, "Block invalid PIT universe fixture", status, 1, reason)

    for index, name in enumerate(
        [
            "missing_source_id",
            "missing_permission_class",
            "paid_unverified_required",
            "missing_source_hash",
            "no_historical_replay_support",
            "context_only_source",
        ],
        start=1,
    ):
        add(f"SRC{index:02d}", "SOURCE_REGISTRY_BLOCKED", name, "Block invalid source registry fixture", SOURCE_REGISTRY_BLOCKED, 1, "Source registry gate failed")

    for index, name in enumerate(
        [
            "missing_document_id",
            "missing_publish_time",
            "missing_available_time",
            "missing_revision_id",
            "missing_compliance_flag",
            "missing_parser_version_for_extraction",
            "manual_review_required_no_status",
        ],
        start=1,
    ):
        add(f"DOC{index:02d}", "RAW_DOCUMENT_EVIDENCE_BLOCKED", name, "Block invalid raw document/evidence fixture", EVIDENCE_BUNDLE_BLOCKED, 1, "Raw document/evidence gate failed")

    for index, name in enumerate(
        [
            "missing_factor_id",
            "missing_taxonomy_layer",
            "fixed_12_only_classification",
            "missing_direction_rule",
            "missing_time_horizon",
            "missing_data_sources",
            "missing_compliance_flag",
            "status_not_replay_context_approved",
        ],
        start=1,
    ):
        add(f"FDEF{index:02d}", "FACTOR_DEFINITION_BLOCKED", name, "Block invalid factor definition fixture", FACTOR_OBSERVATION_BLOCKED, 1, "Factor definition gate failed")

    for index, name in enumerate(
        [
            "missing_as_of_date",
            "missing_symbol_or_entity",
            "missing_factor_id",
            "missing_available_time",
            "available_time_after_decision",
            "missing_source_lineage",
            "quality_status_failed",
            "pit_valid_false",
            "future_label_leakage",
        ],
        start=1,
    ):
        add(f"FOBS{index:02d}", "FACTOR_OBSERVATION_BLOCKED", name, "Block invalid factor observation fixture", FACTOR_OBSERVATION_BLOCKED, 1, "Factor observation gate failed")

    for index, name in enumerate(
        [
            "missing_event_id",
            "missing_document_id",
            "missing_event_time_public",
            "missing_available_time",
            "available_time_after_decision",
            "missing_legality_flag",
            "missing_parser_version",
            "rumor_only_tradeable",
        ],
        start=1,
    ):
        add(f"EVT{index:02d}", "EVENT_STRUCTURED_BLOCKED", name, "Block invalid structured event fixture", EVENT_STRUCTURED_BLOCKED, 1, "Event structured gate failed")

    for index, name in enumerate(
        [
            "missing_symbol",
            "missing_industry_sector",
            "missing_source_id",
            "missing_available_time",
            "missing_revision_id",
            "future_index_membership_leakage",
            "low_confidence_without_review",
        ],
        start=1,
    ):
        add(f"CEXP{index:02d}", "COMPANY_EXPOSURE_BLOCKED", name, "Block invalid company exposure fixture", EVIDENCE_BUNDLE_BLOCKED, 1, "Company exposure gate failed")

    add(
        "PASS01",
        "REPLAY_INPUT_PASS_CANDIDATE",
        "one_stock_one_etf_local_csv_candidate",
        "Design a complete synthetic candidate package",
        REPLAY_INPUT_GATE_PASS_CANDIDATE,
        0,
        "Pass-candidate is not active replay readiness",
    )
    add(
        "BOUND01",
        "ACTIVE_READY_BOUNDARY",
        "no_active_ready_fixture_yet",
        "Define why no active-ready fixture exists yet",
        NO_INPUT,
        1,
        "ACTIVE_REPLAY_INPUT_READY requires later explicit promotion workflow",
    )
    return pd.DataFrame(rows)


def build_blocked_requirements(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in cases.to_dict("records"):
        if row["expected_status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE:
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "blocked_gate_group": row["case_group"],
                "missing_or_invalid_condition": row["fixture_name"],
                "required_field": _required_field_for_case(row["case_id"]),
                "expected_failure_status": row["expected_status"],
                "blocker_reason": row["reason"],
                "overclaim_risk": _overclaim_risk_for_group(row["case_group"]),
            }
        )
    return pd.DataFrame(rows)


def build_expected_status_matrix(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in cases.to_dict("records"):
        rows.append(
            {
                "case_id": row["case_id"],
                "expected_status": row["expected_status"],
                "expected_health": "PASS" if row["expected_status"] in {DESIGN_ONLY, NO_INPUT, REPLAY_INPUT_GATE_PASS_CANDIDATE} else "WARN",
                "expected_research_status_summary": row["reason"],
                "should_block_replay": True,
                "should_block_forward_labels": True,
                "should_block_training": True,
                "should_block_stock_profile": True,
                "should_block_buy_review": True,
            }
        )
    return pd.DataFrame(rows)


def build_fixture_input_schema() -> pd.DataFrame:
    rows = [
        ("fixture_metadata", "case_id", True, True, "string", False, False, "Stable fixture case id"),
        ("fixture_metadata", "case_group", True, True, "string", False, False, "Fixture category"),
        ("fixture_metadata", "expected_status", True, True, "string", False, False, "Expected validator status"),
        ("pit_universe", "signal_date", True, True, "date", True, False, "Preserve date identity"),
        ("pit_universe", "symbol", True, True, "string", True, False, "Preserve leading zeros"),
        ("pit_universe", "universe_name", True, True, "string", True, False, "Example stock_core or etf_core"),
        ("pit_universe", "review_status", True, True, "string", True, False, "Approved only for pass-candidate context"),
        ("pit_universe", "available_time", True, True, "datetime", True, False, "Must be <= replay_decision_time"),
        ("pit_universe", "revision_id", True, True, "string", True, True, "Lineage field"),
        ("source_registry", "source_id", True, True, "string", False, True, "Required source identity"),
        ("source_registry", "permission_class", True, True, "string", False, True, "Permission class required"),
        ("source_registry", "source_hash", True, True, "string", False, True, "Required for file-backed source"),
        ("raw_document", "document_id", True, True, "string", True, True, "Stable id or file ref"),
        ("raw_document", "publish_time", True, True, "datetime", True, True, "Evidence publication time"),
        ("raw_document", "available_time", True, True, "datetime", True, True, "Evidence available time"),
        ("raw_document", "parser_version", True, True, "string", False, True, "Required when extraction claimed"),
        ("factor_definition", "factor_id", True, True, "string", False, True, "Required factor id"),
        ("factor_definition", "layer", True, True, "string", False, False, "8-layer taxonomy layer"),
        ("factor_definition", "fixed_12_only", True, True, "boolean", False, False, "Must be false"),
        ("factor_observation", "as_of_date", True, True, "date", True, False, "Observation as-of date"),
        ("factor_observation", "symbol_or_entity", True, True, "string", True, False, "Preserve leading zeros"),
        ("factor_observation", "available_time", True, True, "datetime", True, False, "Must be <= decision time"),
        ("factor_observation", "pit_valid", True, True, "boolean", True, False, "true required"),
        ("event_structured", "event_id", True, False, "string", True, False, "Required if event supplied"),
        ("event_structured", "event_time_public", True, False, "datetime", True, True, "Required if event supplied"),
        ("event_structured", "legality_flag", True, False, "string", False, True, "Required if event supplied"),
        ("company_exposure", "symbol", True, True, "string", True, False, "Preserve leading zeros"),
        ("company_exposure", "industry_or_sector", True, True, "string", True, False, "Required exposure context"),
        ("evidence_bundle", "bundle_id", False, True, "string", False, False, "Pass-candidate required"),
        ("model_version", "model_version_id", False, True, "string", False, False, "Baseline or research-only model id"),
        ("safety_flags", "order_placed", True, True, "boolean", False, False, "Must be false"),
        ("safety_flags", "llm_api_called", True, True, "boolean", False, False, "Must be false"),
        ("safety_flags", "real_buy_review_eligible", True, True, "boolean", False, False, "Must be false"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "field_group",
            "field_name",
            "required_for_blocked_fixture",
            "required_for_pass_candidate_fixture",
            "data_type_hint",
            "pit_requirement",
            "source_requirement",
            "notes",
        ],
    )


def build_overclaim_guard_report(
    cases: pd.DataFrame,
    paths: dict[str, Path],
    safety: dict[str, bool],
) -> pd.DataFrame:
    status_values = set(cases["expected_status"])
    groups = cases.groupby("case_group").size().to_dict()
    guards = [
        ("G01", "case_count == 68", len(cases) == 68),
        ("G02", "pass_candidate_case_count == 1", int((cases["expected_status"] == REPLAY_INPUT_GATE_PASS_CANDIDATE).sum()) == 1),
        ("G03", "active_ready_case_count == 0", ACTIVE_REPLAY_INPUT_READY not in status_values),
        ("G04", "no fixture case uses ACTIVE_REPLAY_INPUT_READY", ACTIVE_REPLAY_INPUT_READY not in status_values),
        ("G05", "every case blocks replay", bool(cases["should_block_replay"].all())),
        ("G06", "every case blocks forward labels", bool(cases["should_block_forward_labels"].all())),
        ("G07", "every case blocks training", bool(cases["should_block_training"].all())),
        ("G08", "every case blocks active stock_profile", bool(cases["should_block_stock_profile"].all())),
        ("G09", "every case blocks real buy-review eligibility", bool(cases["should_block_buy_review"].all())),
        (
            "G10",
            "all safety flags are safe",
            all(value for key, value in safety.items() if key != "validator_implemented_is_true"),
        ),
        ("G11", "artifact path is safe diagnostics output", _safe_output_path(paths["artifact_dir"])),
        ("G12", "no data/raw, data/processed, or data/cache output path is used", not _unsafe_path(paths["artifact_dir"])),
        ("G13", "expected group counts match design", groups == EXPECTED_FIXTURE_CASE_GROUP_COUNTS),
        ("G14", "real validator not implemented", not safety["validator_implemented_is_true"]),
    ]
    return pd.DataFrame(
        [
            {
                "guard_id": guard_id,
                "guard_name": guard_name,
                "passed": passed,
                "failure_status": "FAIL",
                "blocker_reason": "" if passed else f"Guard failed: {guard_name}",
                "overclaim_risk": _guard_risk(guard_name),
            }
            for guard_id, guard_name, passed in guards
        ]
    )


def resolve_historical_replay_input_gate_validator_fixture_paths(output_dir: Path, fixture_run_id: str) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / fixture_run_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "metadata.json",
        "fixture_cases": artifact_dir / "fixture_cases.csv",
        "blocked_requirements": artifact_dir / "blocked_requirements.csv",
        "expected_status_matrix": artifact_dir / "expected_status_matrix.csv",
        "fixture_input_schema": artifact_dir / "fixture_input_schema.csv",
        "overclaim_guard_report": artifact_dir / "overclaim_guard_report.csv",
        "validation_issues": artifact_dir / "validation_issues.csv",
        "report": artifact_dir / "historical_replay_input_gate_validator_fixture_report.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_historical_replay_input_gate_validator_fixture_artifacts(
    *,
    result: HistoricalReplayInputGateValidatorFixtureResult,
    cases: pd.DataFrame,
    blocked_requirements: pd.DataFrame,
    expected_status: pd.DataFrame,
    fixture_input_schema: pd.DataFrame,
    overclaim_guards: pd.DataFrame,
    validation_issues: pd.DataFrame,
    settings: HistoricalReplayInputGateValidatorFixtureSettings,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    cases.to_csv(paths["fixture_cases"], index=False)
    blocked_requirements.to_csv(paths["blocked_requirements"], index=False)
    expected_status.to_csv(paths["expected_status_matrix"], index=False)
    fixture_input_schema.to_csv(paths["fixture_input_schema"], index=False)
    overclaim_guards.to_csv(paths["overclaim_guard_report"], index=False)
    validation_issues.to_csv(paths["validation_issues"], index=False)
    paths["report"].write_text(render_historical_replay_input_gate_validator_fixture_report(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(
        json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def render_historical_replay_input_gate_validator_fixture_report(
    result: HistoricalReplayInputGateValidatorFixtureResult,
) -> str:
    return "\n".join(
        [
            "# Historical Replay Input Gate Validator Fixture Report v0.1",
            "",
            "## Executive Summary",
            "",
            "This report-only workflow generated synthetic/manual fixture cases for a future historical replay input gate validator. It is not the validator and does not run replay.",
            "",
            "## Counts",
            "",
            f"- fixture_run_id: {result.fixture_run_id}",
            f"- status: {result.status}",
            f"- case_count: {result.case_count}",
            f"- blocked_case_count: {result.blocked_case_count}",
            f"- pass_candidate_case_count: {result.pass_candidate_case_count}",
            f"- active_ready_case_count: {result.active_ready_case_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
            f"- overclaim_guard_pass_count: {result.overclaim_guard_pass_count}",
            f"- overclaim_guard_total_count: {result.overclaim_guard_total_count}",
            "",
            "## Safety",
            "",
            "- active_replay_input=false",
            "- forward_labels_exist=false",
            "- weights_trained=false",
            "- active_stock_profile_exists=false",
            "- real_buy_review_eligible=false",
            "- validator_implemented=false",
            "- active_ready_status_allowed=false",
            "",
            "## Next Recommended Task",
            "",
            "Add index/health/status for this fixture workflow after the core command and tests are stable. Do not run real replay.",
        ]
    )


def _metadata(
    result: HistoricalReplayInputGateValidatorFixtureResult,
    settings: HistoricalReplayInputGateValidatorFixtureSettings,
) -> dict[str, Any]:
    return {
        "fixture_run_id": result.fixture_run_id,
        "generated_at": result.generated_at,
        "artifact_path": str(result.artifact_path),
        "case_count": result.case_count,
        "blocked_case_count": result.blocked_case_count,
        "pass_candidate_case_count": result.pass_candidate_case_count,
        "active_ready_case_count": result.active_ready_case_count,
        "expected_status_counts": result.expected_status_counts,
        "validation_issue_count": result.validation_issue_count,
        "overclaim_guard_pass_count": result.overclaim_guard_pass_count,
        "overclaim_guard_total_count": result.overclaim_guard_total_count,
        "active_replay_input": result.active_replay_input,
        "forward_labels_exist": result.forward_labels_exist,
        "weights_trained": result.weights_trained,
        "active_stock_profile_exists": result.active_stock_profile_exists,
        "real_buy_review_eligible": result.real_buy_review_eligible,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "no_live_trading": result.no_live_trading,
        "no_broker_api": result.no_broker_api,
        "no_order_placement": result.no_order_placement,
        "no_message_sent": result.no_message_sent,
        "llm_api_called": result.llm_api_called,
        "external_api_called": result.external_api_called,
        "cache_mutated": result.cache_mutated,
        "current_candidates_run": result.current_candidates_run,
        "snapshot_built": result.snapshot_built,
        "signal_semantics_changed": result.signal_semantics_changed,
        "validator_implemented": result.validator_implemented,
        "active_ready_status_allowed": result.active_ready_status_allowed,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
        "settings": {
            "config_version": settings.config_version,
            "report_only": settings.report_only,
            "diagnostic_only": settings.diagnostic_only,
        },
    }


def _safety_metadata() -> dict[str, bool]:
    return {
        "active_replay_input_is_false": True,
        "forward_labels_exist_is_false": True,
        "weights_trained_is_false": True,
        "active_stock_profile_exists_is_false": True,
        "real_buy_review_eligible_is_false": True,
        "report_only_is_true": True,
        "diagnostic_only_is_true": True,
        "no_live_trading_is_true": True,
        "no_broker_api_is_true": True,
        "no_order_placement_is_true": True,
        "no_message_sent_is_true": True,
        "llm_api_called_is_false": True,
        "external_api_called_is_false": True,
        "cache_mutated_is_false": True,
        "current_candidates_run_is_false": True,
        "snapshot_built_is_false": True,
        "signal_semantics_changed_is_false": True,
        "validator_implemented_is_true": False,
        "active_ready_status_allowed_is_false": True,
    }


def _validation_issues(cases: pd.DataFrame, overclaim_guards: pd.DataFrame) -> pd.DataFrame:
    issues = []
    if len(cases) != 68:
        issues.append({"severity": "ERROR", "issue_code": "CASE_COUNT_MISMATCH", "message": "case_count must be 68"})
    if ACTIVE_REPLAY_INPUT_READY in set(cases["expected_status"]):
        issues.append(
            {"severity": "ERROR", "issue_code": "ACTIVE_READY_STATUS_UNEXPECTED", "message": "ACTIVE_REPLAY_INPUT_READY is not allowed"}
        )
    for group, expected in EXPECTED_FIXTURE_CASE_GROUP_COUNTS.items():
        actual = int((cases["case_group"] == group).sum())
        if actual != expected:
            issues.append(
                {
                    "severity": "ERROR",
                    "issue_code": "CASE_GROUP_COUNT_MISMATCH",
                    "message": f"{group} expected {expected}, found {actual}",
                }
            )
    if not bool(overclaim_guards["passed"].all()):
        issues.append(
            {"severity": "ERROR", "issue_code": "OVERCLAIM_GUARD_FAILED", "message": "One or more overclaim guards failed"}
        )
    return pd.DataFrame(issues, columns=["severity", "issue_code", "message"])


def _fixture_run_id(cases: pd.DataFrame, config_version: str) -> str:
    payload = {"config_version": config_version, "cases": cases.to_dict("records")}
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def _required_field_for_case(case_id: str) -> str:
    if case_id.startswith("PIT"):
        return "pit_universe_lineage"
    if case_id.startswith("SRC"):
        return "source_registry_fields"
    if case_id.startswith("DOC"):
        return "raw_document_evidence_fields"
    if case_id.startswith("FDEF"):
        return "factor_definition_fields"
    if case_id.startswith("FOBS"):
        return "factor_observation_fields"
    if case_id.startswith("EVT"):
        return "event_structured_fields"
    if case_id.startswith("CEXP"):
        return "company_exposure_fields"
    if case_id.startswith("NRA"):
        return "active_replay_input_promotion"
    return "active_ready_promotion_workflow"


def _overclaim_risk_for_group(group: str) -> str:
    return {
        "NON_REPLAY_ARTIFACT_REJECTION": "Diagnostics treated as active replay input",
        "PIT_UNIVERSE_BLOCKED": "Invalid PIT universe treated as approved",
        "SOURCE_REGISTRY_BLOCKED": "Source name treated as source permission",
        "RAW_DOCUMENT_EVIDENCE_BLOCKED": "Unreviewed evidence treated as replay-ready",
        "FACTOR_DEFINITION_BLOCKED": "Fixed or incomplete factor treated as replay factor",
        "FACTOR_OBSERVATION_BLOCKED": "Factor observation treated as alpha",
        "EVENT_STRUCTURED_BLOCKED": "Event extraction treated as deterministic signal",
        "COMPANY_EXPOSURE_BLOCKED": "Future exposure leakage",
        "ACTIVE_READY_BOUNDARY": "Pass-candidate treated as active-ready",
    }.get(group, "Pass-candidate overclaimed as active replay readiness")


def _guard_risk(guard_name: str) -> str:
    if "active_ready" in guard_name or "ACTIVE_REPLAY" in guard_name:
        return "Pass-candidate treated as active-ready"
    if "forward" in guard_name:
        return "Forward labels computed early"
    if "training" in guard_name:
        return "Training triggered early"
    if "stock" in guard_name:
        return "Stock profile set active"
    if "buy" in guard_name:
        return "Buy-review eligibility set true"
    if "data/" in guard_name:
        return "Fixture writes usable data or cache"
    return "Fixture treated as real replay input"


def _safe_output_path(path: Path) -> bool:
    text = str(path).replace("\\", "/").lower()
    if "manual_diagnostics" in text:
        return True
    # Unit tests may pass an isolated temporary directory directly.
    return not _unsafe_path(path)


def _unsafe_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    joined = "/".join(parts)
    return "data/raw" in joined or "data/processed" in joined or "data/cache" in joined


def _assert_settings_safe(settings: HistoricalReplayInputGateValidatorFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Fixture workflow must remain report-only and diagnostic-only.")
    unsafe = {
        "enable_replay": settings.enable_replay,
        "enable_current_candidates": settings.enable_current_candidates,
        "enable_snapshot_build": settings.enable_snapshot_build,
        "enable_forward_labels": settings.enable_forward_labels,
        "enable_weight_training": settings.enable_weight_training,
        "enable_active_stock_profile": settings.enable_active_stock_profile,
        "enable_real_buy_review": settings.enable_real_buy_review,
        "enable_data_raw_write": settings.enable_data_raw_write,
        "enable_data_processed_write": settings.enable_data_processed_write,
        "enable_data_cache_write": settings.enable_data_cache_write,
        "enable_cache_mutation": settings.enable_cache_mutation,
        "enable_live_trading": settings.enable_live_trading,
        "enable_broker_api": settings.enable_broker_api,
        "enable_order_placement": settings.enable_order_placement,
        "enable_message_delivery": settings.enable_message_delivery,
        "enable_llm_api": settings.enable_llm_api,
        "enable_external_api": settings.enable_external_api,
        "enable_approved_for_paper": settings.enable_approved_for_paper,
    }
    enabled = [name for name, value in unsafe.items() if value]
    if enabled:
        raise ValueError(f"Unsafe fixture workflow settings enabled: {', '.join(enabled)}")
    if _unsafe_path(settings.output_dir):
        raise ValueError(f"Unsafe fixture output path: {settings.output_dir}")


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Task: Historical Replay Input Gate Validator Fixture Artifact Views v0.1",
            "",
            "Add index, health, and status views for the report-only fixture workflow. Do not implement the real validator, research-status integration, checkpoint docs, replay, labels, training, stock profiles, or buy-review eligibility yet.",
        ]
    )


__all__ = [
    "ACTIVE_REPLAY_INPUT_READY",
    "EXPECTED_FIXTURE_CASE_GROUP_COUNTS",
    "HistoricalReplayInputGateValidatorFixtureResult",
    "HistoricalReplayInputGateValidatorFixtureSettings",
    "REPLAY_INPUT_GATE_PASS_CANDIDATE",
    "build_historical_replay_input_gate_validator_fixture",
    "build_fixture_cases",
]
