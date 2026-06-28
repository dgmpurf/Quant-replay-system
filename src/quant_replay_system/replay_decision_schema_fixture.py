"""Report-only replay decision schema fixture workflow.

This module writes tiny synthetic replay_decision rows for schema and governance
review only. The fixture rows are not real replay decisions, real replay
evidence bundle consumption, forward labels, future labels, signal scores,
model inputs, stock profile validation, paper validation, buy-review
permission, performance validation, or trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REPLAY_DECISION_SCHEMA_FIXTURE_CREATED = "REPLAY_DECISION_SCHEMA_FIXTURE_CREATED"

ALLOWED_DECISION_STATUSES = {"PASS", "WARN", "FAIL", "DIAGNOSTIC_ONLY"}
ALLOWED_DECISION_LABELS = {
    "WATCH",
    "REVIEW_BUY_CANDIDATE",
    "REVIEW_SELL_CANDIDATE",
    "HOLD_REVIEW",
    "NO_ACTION",
    "BLOCKED",
    "DIAGNOSTIC_ONLY",
}
ALLOWED_DECISION_ACTIONABILITY = {"review_only", "observe_only", "no_action", "blocked", "diagnostic_only"}
ALLOWED_FREEZE_STATUS = {
    "FROZEN_SYNTHETIC_FIXTURE",
    "NOT_FROZEN_DIAGNOSTIC_ONLY",
    "BLOCKED_NOT_ELIGIBLE",
    "DIAGNOSTIC_ONLY",
}
ALLOWED_DECISION_TIME_ELIGIBILITY = {
    "ELIGIBLE_SYNTHETIC_FIXTURE",
    "BLOCKED_MISSING_EVIDENCE_BUNDLE",
    "BLOCKED_EVIDENCE_BUNDLE_NOT_PIT_VALID",
    "BLOCKED_FUTURE_AVAILABLE_TIME",
    "BLOCKED_FUTURE_REVISION",
    "BLOCKED_SOURCE_PERMISSION",
    "BLOCKED_QUALITY",
    "BLOCKED_REVIEW",
    "BLOCKED_RISK_VETO",
    "OBSERVE_ONLY",
    "DIAGNOSTIC_ONLY",
}
QUALITY_STATUSES = {"PASS", "WARN", "REVIEW_REQUIRED", "FAIL", "BLOCKED", "DIAGNOSTIC_ONLY"}
MANUAL_REVIEW_STATUSES = {
    "NOT_REVIEWED",
    "REVIEW_REQUIRED",
    "REVIEWED_PASS",
    "REVIEWED_WARN",
    "REVIEWED_FAIL",
    "BLOCKED",
    "DIAGNOSTIC_ONLY",
}
COMPLIANCE_CLASSES = {
    "PUBLIC_ALLOWED",
    "PUBLIC_REVIEW_REQUIRED",
    "RUMOR_ONLY",
    "RESTRICTED",
    "PRIVATE",
    "ILLEGAL",
    "DIAGNOSTIC_ONLY",
}
RISK_VETO_TYPES = {
    "NONE",
    "SOURCE_PERMISSION",
    "FUTURE_LEAKAGE",
    "MISSING_EVIDENCE_BUNDLE",
    "BUNDLE_NOT_PIT_VALID",
    "QUALITY_FAIL",
    "MANUAL_REVIEW_FAIL",
    "RESTRICTED_SOURCE",
    "PRIVATE_OR_ILLEGAL_SOURCE",
    "ST_OR_DELIST_RISK",
    "SUSPENSION_OR_NO_TRADE",
    "UNRESOLVED_EVENT_RISK",
    "LIQUIDITY_UNTRADABLE",
    "DIAGNOSTIC_ONLY",
}
ALLOWED_TRADE_USAGE = {
    "research_context",
    "replay_decision_context",
    "review_only",
    "observe_only",
    "risk_filter",
    "no_trade",
    "diagnostic_only",
}
FORBIDDEN_TRADE_USAGE = {
    "buy_signal",
    "sell_signal",
    "real_buy_review",
    "trading_signal",
    "active_portfolio_weight",
    "active_model_input",
    "active_threshold_input",
    "signal_score_input",
}

REQUIRED_REPLAY_DECISION_FIELDS = [
    "replay_decision_id",
    "replay_decision_version",
    "decision_key",
    "schema_version",
    "created_by_workflow",
    "created_at",
    "report_only",
    "diagnostic_only",
    "replay_decision_time",
    "replay_as_of_date",
    "decision_timezone",
    "decision_session",
    "entity_id",
    "symbol",
    "instrument_type",
    "exchange",
    "market",
    "universe_name",
    "universe_as_of_date",
    "candidate_context_ref",
    "replay_evidence_bundle_run_id",
    "replay_evidence_bundle_id",
    "replay_evidence_bundle_status",
    "replay_evidence_bundle_health_status",
    "replay_evidence_bundle_workflow_stage",
    "replay_evidence_bundle_artifact_path",
    "replay_evidence_bundle_available_time_max",
    "replay_evidence_bundle_pit_valid",
    "replay_evidence_bundle_decision_time_eligible",
    "replay_evidence_bundle_completeness_status",
    "replay_evidence_bundle_validation_issue_count",
    "replay_evidence_bundle_blocking_issue_count",
    "decision_label",
    "decision_actionability",
    "decision_confidence_context",
    "decision_rationale_code",
    "decision_rationale_summary",
    "decision_reason_refs",
    "supporting_factor_observation_refs",
    "supporting_event_refs",
    "supporting_exposure_refs",
    "supporting_source_refs",
    "supporting_document_refs",
    "market_confirmation_context",
    "risk_veto_context",
    "signal_semantics_version",
    "review_policy_version",
    "decision_policy_version",
    "freeze_status",
    "frozen_at",
    "frozen_by_workflow",
    "mutation_allowed",
    "supersedes_decision_id",
    "superseded_by_decision_id",
    "revision_id",
    "decision_hash",
    "evidence_snapshot_hash",
    "source_revision_snapshot_hash",
    "available_time_max",
    "all_inputs_available_lte_decision_time",
    "future_label_excluded",
    "future_outcome_excluded",
    "future_return_excluded",
    "future_revision_excluded",
    "metrics_excluded",
    "training_output_excluded",
    "model_output_excluded",
    "stock_profile_output_excluded",
    "paper_approval_excluded",
    "buy_review_output_excluded",
    "pit_valid",
    "decision_time_eligible",
    "quality_status",
    "manual_review_required",
    "manual_review_status",
    "reviewer",
    "reviewed_at",
    "compliance_class",
    "permission_class_summary",
    "restricted_source_count",
    "illegal_source_count",
    "private_source_count",
    "rumor_only_count",
    "risk_veto_flag",
    "risk_veto_type",
    "hard_veto_reason",
    "no_trade_reason",
    "replay_decision_schema_fixture_created",
    "replay_decision_rows_created",
    "real_replay_decisions_created",
    "replay_evidence_bundle_schema_fixture_used",
    "real_replay_evidence_bundle_used",
    "forward_labels_created",
    "future_labels_joined",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_allowed",
    "active_weight_allowed",
    "active_threshold_allowed",
    "stock_profile_validation_allowed",
    "paper_validation_allowed",
    "real_buy_review_allowed",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "operational_global_approved_for_paper_granted",
    "recommended_next_task",
    "limitations_ref",
    "validation_summary_ref",
    "decision_status",
    "workflow_stage",
    "decision_time_eligibility",
    "trade_usage",
]

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "real_replay_decisions_created",
    "real_replay_evidence_bundle_used",
    "forward_labels_created",
    "future_labels_joined",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "operational_global_approved_for_paper_granted",
]

ROW_FALSE_FLAGS = [
    "real_replay_decisions_created",
    "real_replay_evidence_bundle_used",
    "forward_labels_created",
    "future_labels_joined",
    "signal_score_implemented",
    "signal_score_input_authorized",
    "model_training_allowed",
    "active_weight_allowed",
    "active_threshold_allowed",
    "stock_profile_validation_allowed",
    "paper_validation_allowed",
    "real_buy_review_allowed",
    "buy_review_allowed",
    "strategy_performance_validated",
    "trading_allowed",
    "live_trading_enabled",
    "broker_api_called",
    "external_api_called",
    "llm_api_called",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "active_stock_profile_created",
    "operational_global_approved_for_paper_granted",
]

ARTIFACT_FILENAMES = {
    "metadata": "replay_decision_schema_fixture_metadata.json",
    "schema_fields": "replay_decision_schema_fields.csv",
    "fixture_rows": "replay_decision_fixture_rows.csv",
    "evidence_bundle_matrix": "replay_decision_evidence_bundle_matrix.csv",
    "pit_admissibility_matrix": "replay_decision_pit_admissibility_matrix.csv",
    "freeze_matrix": "replay_decision_freeze_matrix.csv",
    "label_exclusion_matrix": "replay_decision_label_exclusion_matrix.csv",
    "quality_compliance_matrix": "replay_decision_quality_compliance_matrix.csv",
    "risk_veto_matrix": "replay_decision_risk_veto_matrix.csv",
    "forbidden_output_guard_matrix": "replay_decision_forbidden_output_guard_matrix.csv",
    "validation_summary": "replay_decision_validation_summary.csv",
    "limitations": "replay_decision_limitations.md",
    "recommended_next_task": "recommended_next_task.md",
}


@dataclass(frozen=True)
class ReplayDecisionSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/replay_decision_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ReplayDecisionSchemaFixtureResult:
    replay_decision_schema_fixture_id: str
    status: str
    workflow_stage: str
    decision_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_replay_decision_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: ReplayDecisionSchemaFixtureSettings | None = None,
) -> ReplayDecisionSchemaFixtureResult:
    resolved_settings = settings or ReplayDecisionSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = ReplayDecisionSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_replay_decision_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_replay_decision_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_replay_decision_schema_fields()
    evidence_bundle_matrix = build_replay_decision_evidence_bundle_matrix(fixture_rows)
    pit_admissibility_matrix = build_replay_decision_pit_admissibility_matrix(fixture_rows)
    freeze_matrix = build_replay_decision_freeze_matrix(fixture_rows)
    label_exclusion_matrix = build_replay_decision_label_exclusion_matrix(fixture_rows)
    quality_compliance_matrix = build_replay_decision_quality_compliance_matrix(fixture_rows)
    risk_veto_matrix = build_replay_decision_risk_veto_matrix(fixture_rows)
    forbidden_output_guard_matrix = build_replay_decision_forbidden_output_guard_matrix()
    validation_summary = validate_replay_decision_fixture(fixture_rows, resolved_settings)
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = ReplayDecisionSchemaFixtureResult(
        replay_decision_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
        decision_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_replay_decision_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            evidence_bundle_matrix=evidence_bundle_matrix,
            pit_admissibility_matrix=pit_admissibility_matrix,
            freeze_matrix=freeze_matrix,
            label_exclusion_matrix=label_exclusion_matrix,
            quality_compliance_matrix=quality_compliance_matrix,
            risk_veto_matrix=risk_veto_matrix,
            forbidden_output_guard_matrix=forbidden_output_guard_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_replay_decision_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            replay_decision_id="SYNTH_WATCH_COMPLETE_EVIDENCE_DECISION",
            decision_label="WATCH",
            decision_rationale_code="COMPLETE_EVIDENCE_WATCH",
            decision_rationale_summary="Complete admissible synthetic evidence supports watch review context only.",
            replay_evidence_bundle_id="SYNTH_COMPLETE_PRICE_VOLUME_FACTOR_BUNDLE",
            supporting_factor_observation_refs="SYNTH_DAILY_RETURN_PRICE_VOLUME_OBSERVATION",
            supporting_source_refs="SYNTH_EXCHANGE_SOURCE",
        ),
        _row(
            replay_decision_id="SYNTH_REVIEW_BUY_CANDIDATE_REPORT_ONLY_DECISION",
            decision_label="REVIEW_BUY_CANDIDATE",
            decision_rationale_code="REVIEW_BUY_CANDIDATE_REPORT_ONLY",
            decision_rationale_summary=(
                "Synthetic REVIEW_BUY_CANDIDATE is human-review context only and not a buy instruction."
            ),
            replay_evidence_bundle_id="SYNTH_FUNDAMENTAL_AVAILABLE_AFTER_PERIOD_END_BUNDLE",
            supporting_factor_observation_refs="SYNTH_REVENUE_GROWTH_FUNDAMENTAL_CONTEXT",
            supporting_document_refs="SYNTH_REVENUE_REPORT_DOC",
            decision_confidence_context="synthetic_context_complete_not_probability",
        ),
        _row(
            replay_decision_id="SYNTH_REVIEW_SELL_CANDIDATE_REPORT_ONLY_DECISION",
            decision_label="REVIEW_SELL_CANDIDATE",
            decision_rationale_code="REVIEW_SELL_CANDIDATE_REPORT_ONLY",
            decision_rationale_summary=(
                "Synthetic REVIEW_SELL_CANDIDATE is human-review context only and not a sell instruction."
            ),
            replay_evidence_bundle_id="SYNTH_EVENT_POLICY_CONTEXT_BUNDLE",
            supporting_event_refs="SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT",
            supporting_document_refs="SYNTH_POLICY_DOC",
        ),
        _row(
            replay_decision_id="SYNTH_HOLD_REVIEW_DECISION",
            decision_label="HOLD_REVIEW",
            decision_rationale_code="HOLD_REVIEW_SYNTHETIC_CONTEXT",
            decision_rationale_summary="Synthetic existing-position placeholder only; no broker or account integration.",
            replay_evidence_bundle_id="SYNTH_COMPANY_EXPOSURE_DIRECTION_CONTEXT_BUNDLE",
            supporting_exposure_refs="SYNTH_EXPORT_POLICY_EXPOSURE",
            candidate_context_ref="SYNTH_EXISTING_POSITION_CONTEXT",
        ),
        _row(
            replay_decision_id="SYNTH_NO_ACTION_WEAK_EVIDENCE_DECISION",
            decision_label="NO_ACTION",
            decision_actionability="no_action",
            decision_rationale_code="WEAK_EVIDENCE_NO_ACTION",
            decision_rationale_summary="Admissible but weak synthetic evidence leads to no-action review context.",
            replay_evidence_bundle_id="SYNTH_COMMODITY_COST_SPREAD_BUNDLE",
            replay_evidence_bundle_completeness_status="PARTIAL_CONTEXT_ONLY",
            decision_confidence_context="weak_synthetic_context",
            quality_status="WARN",
        ),
        _row(
            replay_decision_id="SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION",
            decision_label="BLOCKED",
            decision_actionability="blocked",
            decision_time_eligibility="BLOCKED_RISK_VETO",
            decision_rationale_code="RISK_VETO_ST_DELIST",
            decision_rationale_summary="Synthetic ST/delist risk veto blocks actionability with no positive alpha claim.",
            replay_evidence_bundle_id="SYNTH_RISK_VETO_ST_DELIST_BUNDLE",
            replay_evidence_bundle_status="WARN",
            replay_evidence_bundle_pit_valid=False,
            replay_evidence_bundle_decision_time_eligible=False,
            replay_evidence_bundle_completeness_status="BLOCKED_MISSING_REQUIRED_EVIDENCE",
            replay_evidence_bundle_blocking_issue_count=1,
            pit_valid=False,
            decision_time_eligible=False,
            freeze_status="BLOCKED_NOT_ELIGIBLE",
            risk_veto_flag=True,
            risk_veto_type="ST_OR_DELIST_RISK",
            hard_veto_reason="Synthetic ST/delist risk veto blocks actionability and no positive alpha claim is made.",
            no_trade_reason="risk_veto_blocks_actionability",
            trade_usage="no_trade",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
        ),
        _row(
            replay_decision_id="SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION",
            decision_label="BLOCKED",
            decision_actionability="blocked",
            decision_time_eligibility="BLOCKED_FUTURE_AVAILABLE_TIME",
            decision_rationale_code="FUTURE_AVAILABLE_EVIDENCE_BLOCKED",
            decision_rationale_summary="Synthetic evidence available after replay_decision_time is blocked.",
            replay_evidence_bundle_id="SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE",
            replay_decision_time="2024-04-02T09:30:00",
            available_time_max="2024-04-03T09:30:00",
            replay_evidence_bundle_available_time_max="2024-04-03T09:30:00",
            all_inputs_available_lte_decision_time=False,
            replay_evidence_bundle_status="WARN",
            replay_evidence_bundle_pit_valid=False,
            replay_evidence_bundle_decision_time_eligible=False,
            replay_evidence_bundle_completeness_status="BLOCKED_PIT_VIOLATION",
            replay_evidence_bundle_blocking_issue_count=1,
            pit_valid=False,
            decision_time_eligible=False,
            freeze_status="BLOCKED_NOT_ELIGIBLE",
            risk_veto_flag=True,
            risk_veto_type="FUTURE_LEAKAGE",
            hard_veto_reason="Future-available evidence is not admissible at replay_decision_time.",
            no_trade_reason="future_available_evidence_blocked",
            trade_usage="no_trade",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
        ),
        _row(
            replay_decision_id="SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION",
            decision_label="BLOCKED",
            decision_actionability="blocked",
            decision_time_eligibility="BLOCKED_MISSING_EVIDENCE_BUNDLE",
            decision_rationale_code="MISSING_REPLAY_EVIDENCE_BUNDLE",
            decision_rationale_summary="Missing replay_evidence_bundle reference blocks decision-time eligibility.",
            replay_evidence_bundle_id="",
            replay_evidence_bundle_status="FAIL",
            replay_evidence_bundle_health_status="FAIL",
            replay_evidence_bundle_workflow_stage="",
            replay_evidence_bundle_pit_valid=False,
            replay_evidence_bundle_decision_time_eligible=False,
            replay_evidence_bundle_completeness_status="BLOCKED_MISSING_REQUIRED_EVIDENCE",
            replay_evidence_bundle_blocking_issue_count=1,
            pit_valid=False,
            decision_time_eligible=False,
            freeze_status="BLOCKED_NOT_ELIGIBLE",
            risk_veto_flag=True,
            risk_veto_type="MISSING_EVIDENCE_BUNDLE",
            hard_veto_reason="Missing replay evidence bundle prevents review decision eligibility.",
            no_trade_reason="missing_replay_evidence_bundle",
            trade_usage="no_trade",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
        ),
        _row(
            replay_decision_id="SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION",
            decision_label="BLOCKED",
            decision_actionability="blocked",
            decision_time_eligibility="BLOCKED_SOURCE_PERMISSION",
            decision_rationale_code="RESTRICTED_PRIVATE_SOURCE_BLOCKED",
            decision_rationale_summary="Restricted/private synthetic evidence context is blocked and no-trade.",
            replay_evidence_bundle_id="SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_BUNDLE",
            replay_evidence_bundle_status="WARN",
            replay_evidence_bundle_pit_valid=False,
            replay_evidence_bundle_decision_time_eligible=False,
            replay_evidence_bundle_completeness_status="BLOCKED_RESTRICTED_OR_ILLEGAL_SOURCE",
            replay_evidence_bundle_blocking_issue_count=1,
            pit_valid=False,
            decision_time_eligible=False,
            freeze_status="BLOCKED_NOT_ELIGIBLE",
            compliance_class="RESTRICTED",
            permission_class_summary="restricted_or_private_source_blocked",
            restricted_source_count=1,
            private_source_count=1,
            risk_veto_flag=True,
            risk_veto_type="PRIVATE_OR_ILLEGAL_SOURCE",
            hard_veto_reason="Restricted/private source context blocks decision actionability.",
            no_trade_reason="restricted_or_private_source",
            trade_usage="no_trade",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
        ),
        _row(
            replay_decision_id="SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION",
            decision_label="WATCH",
            decision_actionability="observe_only",
            decision_time_eligibility="OBSERVE_ONLY",
            decision_rationale_code="INCOMPLETE_REVIEW_OBSERVE_ONLY",
            decision_rationale_summary="Incomplete manual review is observe-only and not frozen as a real decision.",
            replay_evidence_bundle_id="SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE",
            replay_evidence_bundle_status="WARN",
            replay_evidence_bundle_decision_time_eligible=False,
            replay_evidence_bundle_completeness_status="PARTIAL_CONTEXT_ONLY",
            replay_evidence_bundle_blocking_issue_count=1,
            decision_time_eligible=False,
            freeze_status="NOT_FROZEN_DIAGNOSTIC_ONLY",
            manual_review_required=True,
            manual_review_status="REVIEW_REQUIRED",
            no_trade_reason="manual_review_incomplete_observe_only",
            trade_usage="observe_only",
            quality_status="REVIEW_REQUIRED",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_REPLAY_DECISION_FIELDS)


def build_replay_decision_schema_fields() -> pd.DataFrame:
    allowed_values: dict[str, str] = {
        "decision_status": "|".join(sorted(ALLOWED_DECISION_STATUSES)),
        "workflow_stage": REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
        "decision_label": "|".join(sorted(ALLOWED_DECISION_LABELS)),
        "decision_actionability": "|".join(sorted(ALLOWED_DECISION_ACTIONABILITY)),
        "freeze_status": "|".join(sorted(ALLOWED_FREEZE_STATUS)),
        "decision_time_eligibility": "|".join(sorted(ALLOWED_DECISION_TIME_ELIGIBILITY)),
        "quality_status": "|".join(sorted(QUALITY_STATUSES)),
        "manual_review_status": "|".join(sorted(MANUAL_REVIEW_STATUSES)),
        "compliance_class": "|".join(sorted(COMPLIANCE_CLASSES)),
        "risk_veto_type": "|".join(sorted(RISK_VETO_TYPES)),
        "trade_usage": "|".join(sorted(ALLOWED_TRADE_USAGE)),
    }
    groups = {
        "replay_decision_id": "identity_version",
        "replay_decision_time": "replay_context",
        "replay_evidence_bundle_id": "evidence_bundle_lineage",
        "decision_label": "decision_semantics",
        "freeze_status": "decision_freeze",
        "future_label_excluded": "pit_and_leakage",
        "quality_status": "quality_review_compliance",
        "real_replay_decisions_created": "safety_governance",
        "recommended_next_task": "recommended_next",
    }
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "field_group": groups.get(field, _field_group(field)),
                "required_for_fixture": True,
                "description": _field_description(field),
                "allowed_values": allowed_values.get(field, ""),
            }
            for field in REQUIRED_REPLAY_DECISION_FIELDS
        ]
    )


def build_replay_decision_evidence_bundle_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "replay_evidence_bundle_run_id",
        "replay_evidence_bundle_id",
        "replay_evidence_bundle_status",
        "replay_evidence_bundle_health_status",
        "replay_evidence_bundle_workflow_stage",
        "replay_evidence_bundle_pit_valid",
        "replay_evidence_bundle_decision_time_eligible",
        "replay_evidence_bundle_completeness_status",
        "replay_evidence_bundle_validation_issue_count",
        "replay_evidence_bundle_blocking_issue_count",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_pit_admissibility_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "replay_decision_time",
        "available_time_max",
        "all_inputs_available_lte_decision_time",
        "future_label_excluded",
        "future_outcome_excluded",
        "future_return_excluded",
        "future_revision_excluded",
        "decision_time_eligible",
        "pit_valid",
        "decision_time_eligibility",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_freeze_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "freeze_status",
        "frozen_at",
        "frozen_by_workflow",
        "mutation_allowed",
        "revision_id",
        "decision_hash",
        "evidence_snapshot_hash",
        "source_revision_snapshot_hash",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_label_exclusion_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "future_label_excluded",
        "future_outcome_excluded",
        "future_return_excluded",
        "metrics_excluded",
        "training_output_excluded",
        "model_output_excluded",
        "stock_profile_output_excluded",
        "paper_approval_excluded",
        "buy_review_output_excluded",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_quality_compliance_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "quality_status",
        "manual_review_status",
        "compliance_class",
        "permission_class_summary",
        "restricted_source_count",
        "private_source_count",
        "illegal_source_count",
        "rumor_only_count",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_risk_veto_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_decision_id",
        "risk_veto_flag",
        "risk_veto_type",
        "hard_veto_reason",
        "no_trade_reason",
        "trade_usage",
    ]
    return fixture_rows[columns].copy()


def build_replay_decision_forbidden_output_guard_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "guard_name": flag,
                "observed_value": False,
                "expected_value": False,
                "passed": True,
                "notes": "Report-only replay decision schema fixture must not create this output or side effect.",
            }
            for flag in ROW_FALSE_FLAGS
        ]
    )


def validate_replay_decision_fixture(
    fixture_rows: pd.DataFrame,
    settings: ReplayDecisionSchemaFixtureSettings,
) -> pd.DataFrame:
    checks: list[dict[str, Any]] = []

    def add(check_name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": check_name, "passed": bool(passed), "detail": detail})

    eligible = fixture_rows[fixture_rows["decision_time_eligible"] == True]  # noqa: E712
    frozen = fixture_rows[fixture_rows["freeze_status"] == "FROZEN_SYNTHETIC_FIXTURE"]
    all_text = "\n".join(fixture_rows.astype(str).to_numpy().ravel().tolist())

    add("exactly_10_decision_rows", len(fixture_rows) == 10, f"row_count={len(fixture_rows)}")
    add("unique_replay_decision_id", fixture_rows["replay_decision_id"].is_unique, "replay_decision_id is unique")
    add("required_fields_present", set(REQUIRED_REPLAY_DECISION_FIELDS) <= set(fixture_rows.columns), "required fields present")
    add(
        "decision_context_present",
        fixture_rows[["replay_decision_time", "entity_id", "symbol", "instrument_type"]].astype(str).ne("").all().all(),
        "decision context fields populated",
    )
    add(
        "eligible_rows_have_bundle_id",
        eligible["replay_evidence_bundle_id"].astype(str).str.len().gt(0).all(),
        "eligible rows reference a replay evidence bundle",
    )
    add(
        "eligible_bundle_status_health_stage",
        (
            (eligible["replay_evidence_bundle_status"] == "PASS")
            & (eligible["replay_evidence_bundle_health_status"] == "PASS")
            & (eligible["replay_evidence_bundle_workflow_stage"] == "REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED")
        ).all(),
        "eligible rows use PASS replay evidence bundle fixture context",
    )
    add(
        "eligible_inputs_available_by_decision_time",
        eligible.apply(
            lambda row: pd.Timestamp(row["available_time_max"]) <= pd.Timestamp(row["replay_decision_time"]),
            axis=1,
        ).all(),
        "available_time_max <= replay_decision_time for eligible rows",
    )
    add(
        "future_available_evidence_blocked",
        (
            fixture_rows.loc[
                fixture_rows["replay_decision_id"] == "SYNTH_BLOCKED_FUTURE_AVAILABLE_EVIDENCE_DECISION",
                "decision_time_eligible",
            ]
            == False
        ).all(),
        "future-available evidence row blocked",
    )
    for column in [
        "future_label_excluded",
        "future_outcome_excluded",
        "future_return_excluded",
        "future_revision_excluded",
        "metrics_excluded",
        "training_output_excluded",
        "model_output_excluded",
        "stock_profile_output_excluded",
        "paper_approval_excluded",
        "buy_review_output_excluded",
    ]:
        add(f"{column}_true", (fixture_rows[column] == True).all(), f"{column} true for all rows")  # noqa: E712
    add("allowed_decision_labels", set(fixture_rows["decision_label"]) <= ALLOWED_DECISION_LABELS, "decision labels valid")
    add(
        "review_candidates_are_review_only",
        (
            fixture_rows.loc[
                fixture_rows["decision_label"].isin(["REVIEW_BUY_CANDIDATE", "REVIEW_SELL_CANDIDATE"]),
                "decision_actionability",
            ]
            == "review_only"
        ).all(),
        "review candidate labels are not order signals",
    )
    add(
        "risk_veto_blocks_actionability",
        (
            fixture_rows.loc[
                fixture_rows["replay_decision_id"] == "SYNTH_BLOCKED_RISK_VETO_ST_DELIST_DECISION",
                "decision_actionability",
            ]
            == "blocked"
        ).all(),
        "risk veto row blocked",
    )
    add(
        "missing_bundle_blocked",
        (
            fixture_rows.loc[
                fixture_rows["replay_decision_id"] == "SYNTH_BLOCKED_MISSING_REPLAY_EVIDENCE_BUNDLE_DECISION",
                "decision_time_eligible",
            ]
            == False
        ).all(),
        "missing bundle row blocked",
    )
    add(
        "restricted_private_source_blocked",
        (
            fixture_rows.loc[
                fixture_rows["replay_decision_id"] == "SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_DECISION",
                "trade_usage",
            ]
            == "no_trade"
        ).all(),
        "restricted/private source row no_trade",
    )
    add(
        "observe_only_incomplete_not_eligible",
        (
            fixture_rows.loc[
                fixture_rows["replay_decision_id"] == "SYNTH_OBSERVE_ONLY_INCOMPLETE_REVIEW_DECISION",
                "decision_actionability",
            ]
            == "observe_only"
        ).all(),
        "observe-only row remains non-active",
    )
    add("freeze_status_valid", set(fixture_rows["freeze_status"]) <= ALLOWED_FREEZE_STATUS, "freeze status valid")
    add(
        "frozen_rows_immutable",
        (frozen["mutation_allowed"] == False).all(),  # noqa: E712
        "frozen synthetic rows have mutation_allowed=false",
    )
    add(
        "frozen_rows_have_hashes",
        frozen[["decision_hash", "evidence_snapshot_hash", "source_revision_snapshot_hash"]].astype(str).ne("").all().all(),
        "frozen synthetic rows have hashes",
    )
    for flag in ROW_FALSE_FLAGS:
        add(f"{flag}_false", (fixture_rows[flag] == False).all(), f"{flag} false for all rows")  # noqa: E712
    add("no_forbidden_trade_usage", not (set(fixture_rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE), "forbidden trade_usage absent")
    add(
        "no_private_credential_like_values",
        re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", all_text.lower()) is None,
        "no private credential-like values",
    )
    return pd.DataFrame(checks)


def write_replay_decision_schema_fixture_artifacts(
    *,
    result: ReplayDecisionSchemaFixtureResult,
    settings: ReplayDecisionSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    evidence_bundle_matrix: pd.DataFrame,
    pit_admissibility_matrix: pd.DataFrame,
    freeze_matrix: pd.DataFrame,
    label_exclusion_matrix: pd.DataFrame,
    quality_compliance_matrix: pd.DataFrame,
    risk_veto_matrix: pd.DataFrame,
    forbidden_output_guard_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    artifact_dir = result.artifact_paths["artifact_dir"]
    artifact_dir.mkdir(parents=True, exist_ok=True)

    schema_fields.to_csv(result.artifact_paths["schema_fields"], index=False)
    fixture_rows.to_csv(result.artifact_paths["fixture_rows"], index=False)
    evidence_bundle_matrix.to_csv(result.artifact_paths["evidence_bundle_matrix"], index=False)
    pit_admissibility_matrix.to_csv(result.artifact_paths["pit_admissibility_matrix"], index=False)
    freeze_matrix.to_csv(result.artifact_paths["freeze_matrix"], index=False)
    label_exclusion_matrix.to_csv(result.artifact_paths["label_exclusion_matrix"], index=False)
    quality_compliance_matrix.to_csv(result.artifact_paths["quality_compliance_matrix"], index=False)
    risk_veto_matrix.to_csv(result.artifact_paths["risk_veto_matrix"], index=False)
    forbidden_output_guard_matrix.to_csv(result.artifact_paths["forbidden_output_guard_matrix"], index=False)
    validation_summary.to_csv(result.artifact_paths["validation_summary"], index=False)
    result.artifact_paths["limitations"].write_text(_limitations_text(), encoding="utf-8")
    result.artifact_paths["recommended_next_task"].write_text(
        "# Recommended Next Task\n\nReplay Decision Schema Fixture Views Report-Only v0.1\n",
        encoding="utf-8",
    )

    metadata = _metadata(result, settings)
    result.artifact_paths["metadata"].write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def resolve_replay_decision_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _row(**overrides: Any) -> dict[str, Any]:
    replay_decision_id = overrides.get("replay_decision_id", "SYNTH_REPLAY_DECISION")
    replay_evidence_bundle_id = overrides.get("replay_evidence_bundle_id", "SYNTH_COMPLETE_PRICE_VOLUME_FACTOR_BUNDLE")
    replay_decision_time = overrides.get("replay_decision_time", "2024-04-02T09:30:00")
    available_time_max = overrides.get("available_time_max", "2024-04-01T16:00:00")
    frozen_at = overrides.get("frozen_at", "2024-04-02T09:31:00")
    decision_hash = _stable_hash(f"decision|{replay_decision_id}|{replay_decision_time}")
    evidence_snapshot_hash = _stable_hash(f"evidence|{replay_decision_id}|{replay_evidence_bundle_id}")
    source_revision_snapshot_hash = _stable_hash(f"source|{replay_decision_id}|SYNTH_SOURCE_REVISION")
    base = {
        "replay_decision_id": replay_decision_id,
        "replay_decision_version": "v0.1",
        "decision_key": f"{replay_decision_id}|{replay_decision_time}",
        "schema_version": "replay_decision_schema_fixture_v0.1",
        "created_by_workflow": "replay-decision-schema-fixture",
        "created_at": "2026-06-28T00:00:00Z",
        "report_only": True,
        "diagnostic_only": True,
        "replay_decision_time": replay_decision_time,
        "replay_as_of_date": replay_decision_time[:10],
        "decision_timezone": "Asia/Shanghai",
        "decision_session": "OPEN_REVIEW_SYNTHETIC",
        "entity_id": "SYNTH_ENTITY_DECISION",
        "symbol": "SYNTH001",
        "instrument_type": "STOCK",
        "exchange": "SYNTH_EXCHANGE",
        "market": "SYNTH_MARKET",
        "universe_name": "synthetic_replay_decision_fixture",
        "universe_as_of_date": replay_decision_time[:10],
        "candidate_context_ref": "SYNTH_REVIEW_CONTEXT",
        "replay_evidence_bundle_run_id": "d400661214a4",
        "replay_evidence_bundle_id": replay_evidence_bundle_id,
        "replay_evidence_bundle_status": "PASS",
        "replay_evidence_bundle_health_status": "PASS",
        "replay_evidence_bundle_workflow_stage": "REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED",
        "replay_evidence_bundle_artifact_path": "outputs/reports/manual_diagnostics/replay_evidence_bundle_schema_fixture_v0_1/d400661214a4",
        "replay_evidence_bundle_available_time_max": available_time_max,
        "replay_evidence_bundle_pit_valid": True,
        "replay_evidence_bundle_decision_time_eligible": True,
        "replay_evidence_bundle_completeness_status": "COMPLETE_SYNTHETIC_FIXTURE",
        "replay_evidence_bundle_validation_issue_count": 0,
        "replay_evidence_bundle_blocking_issue_count": 0,
        "decision_label": "WATCH",
        "decision_actionability": "review_only",
        "decision_confidence_context": "synthetic_review_context_not_probability",
        "decision_rationale_code": "SYNTHETIC_REVIEW_ONLY",
        "decision_rationale_summary": "Synthetic replay decision schema context only.",
        "decision_reason_refs": "SYNTH_DECISION_REASON",
        "supporting_factor_observation_refs": "SYNTH_FACTOR_OBSERVATION_REF",
        "supporting_event_refs": "",
        "supporting_exposure_refs": "",
        "supporting_source_refs": "SYNTH_PUBLIC_SOURCE",
        "supporting_document_refs": "SYNTH_DOCUMENT_REF",
        "market_confirmation_context": "synthetic_market_context_only",
        "risk_veto_context": "no_risk_veto",
        "signal_semantics_version": "signal_semantics_design_reference_only",
        "review_policy_version": "review_policy_fixture_v0.1",
        "decision_policy_version": "decision_policy_fixture_v0.1",
        "freeze_status": "FROZEN_SYNTHETIC_FIXTURE",
        "frozen_at": frozen_at,
        "frozen_by_workflow": "replay-decision-schema-fixture",
        "mutation_allowed": False,
        "supersedes_decision_id": "",
        "superseded_by_decision_id": "",
        "revision_id": f"SYNTH_REVISION_{_stable_hash(replay_decision_id)[:8]}",
        "decision_hash": decision_hash,
        "evidence_snapshot_hash": evidence_snapshot_hash,
        "source_revision_snapshot_hash": source_revision_snapshot_hash,
        "available_time_max": available_time_max,
        "all_inputs_available_lte_decision_time": True,
        "future_label_excluded": True,
        "future_outcome_excluded": True,
        "future_return_excluded": True,
        "future_revision_excluded": True,
        "metrics_excluded": True,
        "training_output_excluded": True,
        "model_output_excluded": True,
        "stock_profile_output_excluded": True,
        "paper_approval_excluded": True,
        "buy_review_output_excluded": True,
        "pit_valid": True,
        "decision_time_eligible": True,
        "quality_status": "PASS",
        "manual_review_required": False,
        "manual_review_status": "REVIEWED_PASS",
        "reviewer": "SYNTHETIC_FIXTURE_REVIEWER",
        "reviewed_at": "2026-06-28T00:00:00Z",
        "compliance_class": "PUBLIC_ALLOWED",
        "permission_class_summary": "synthetic_public_allowed_context",
        "restricted_source_count": 0,
        "illegal_source_count": 0,
        "private_source_count": 0,
        "rumor_only_count": 0,
        "risk_veto_flag": False,
        "risk_veto_type": "NONE",
        "hard_veto_reason": "",
        "no_trade_reason": "report_only_fixture_not_tradeable",
        "replay_decision_schema_fixture_created": True,
        "replay_decision_rows_created": True,
        "replay_evidence_bundle_schema_fixture_used": True,
        "recommended_next_task": "Replay Decision Schema Fixture Views Report-Only v0.1",
        "limitations_ref": "replay_decision_limitations.md",
        "validation_summary_ref": "replay_decision_validation_summary.csv",
        "decision_status": "PASS",
        "workflow_stage": REPLAY_DECISION_SCHEMA_FIXTURE_CREATED,
        "decision_time_eligibility": "ELIGIBLE_SYNTHETIC_FIXTURE",
        "trade_usage": "review_only",
    }
    for flag in ROW_FALSE_FLAGS:
        base[flag] = False
    base.update(overrides)
    return base


def _metadata(
    result: ReplayDecisionSchemaFixtureResult,
    settings: ReplayDecisionSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "replay_decision_schema_fixture_id": result.replay_decision_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "decision_count": result.decision_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "config_version": settings.config_version,
        "replay_decision_schema_fixture_created": True,
        "replay_decision_rows_created": True,
        "artifact_list": sorted(path.name for key, path in result.artifact_paths.items() if key != "artifact_dir"),
        "recommended_next_task": "Replay Decision Schema Fixture Views Report-Only v0.1",
    }
    for flag in FORBIDDEN_METADATA_FALSE_FLAGS:
        metadata[flag] = False
    return metadata


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    payload = fixture_rows.to_json(orient="records", date_format="iso") + config_version
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _assert_settings_safe(settings: ReplayDecisionSchemaFixtureSettings) -> None:
    output_dir = Path(settings.output_dir)
    if any(part in {"data", "raw", "processed", "cache"} for part in output_dir.parts):
        raise ValueError("Replay decision schema fixture output must not target data/raw, data/processed, or data/cache")
    if "docs" in output_dir.parts and "project_sources" in output_dir.parts:
        raise ValueError("Replay decision schema fixture must not write docs/project_sources")
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Replay decision schema fixture must remain report_only and diagnostic_only")


def _field_group(field: str) -> str:
    if field.startswith("replay_evidence_bundle_"):
        return "evidence_bundle_lineage"
    if field.startswith("decision_"):
        return "decision_semantics"
    if field.startswith("future_") or field.endswith("_excluded") or field in {"pit_valid", "available_time_max"}:
        return "pit_and_leakage"
    if field in ROW_FALSE_FLAGS or field.startswith("replay_decision_"):
        return "safety_governance"
    return "supporting_context"


def _field_description(field: str) -> str:
    return field.replace("_", " ") + " for report-only replay decision schema fixture governance."


def _limitations_text() -> str:
    return """# Replay Decision Schema Fixture Limitations

No real replay decisions are created.
No real replay evidence bundles are consumed.
No forward labels are created.
No future labels joined.
No signal_score is implemented or authorized as input.
No model training is performed.
No active weights are created.
No active thresholds are created.
No stock_profile validation is created.
No paper validation is created.
No buy-review is created.
No real buy-review is created.
No buy_review_allowed flag is set.
No strategy performance validation is claimed.
No trading is allowed.

The fixture is synthetic-only and report-only. REVIEW_BUY_CANDIDATE and
REVIEW_SELL_CANDIDATE are human-review candidate semantics only, not order
signals, trading signals, current-candidates, recommendations, or advisory
predictions.
"""
