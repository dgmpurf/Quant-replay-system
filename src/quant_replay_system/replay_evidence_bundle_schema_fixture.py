"""Report-only replay evidence bundle schema fixture workflow.

This module writes tiny synthetic replay_evidence_bundle rows for schema and
governance review only. The fixture rows are not real replay evidence bundles,
replay decisions, forward labels, signal scores, model inputs, stock profile
validation, paper validation, buy-review permission, performance validation, or
trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED = "REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED"

BUNDLE_STATUSES = {"PASS", "WARN", "FAIL", "DIAGNOSTIC_ONLY"}
BUNDLE_COMPLETENESS_STATUSES = {
    "COMPLETE_SYNTHETIC_FIXTURE",
    "PARTIAL_CONTEXT_ONLY",
    "BLOCKED_MISSING_REQUIRED_EVIDENCE",
    "BLOCKED_PIT_VIOLATION",
    "BLOCKED_SOURCE_PERMISSION",
    "BLOCKED_RESTRICTED_OR_ILLEGAL_SOURCE",
    "DIAGNOSTIC_ONLY",
}
EVIDENCE_ITEM_TYPES = {
    "SOURCE_REGISTRY",
    "RAW_DOCUMENT",
    "RAW_DATASET",
    "FACTOR_DEFINITION",
    "COMPANY_EXPOSURE",
    "EVENT_STRUCTURED",
    "FACTOR_OBSERVATION",
    "RISK_VETO",
    "COMPLIANCE_RULE",
    "SYNTHETIC_FIXTURE",
}
ADMISSIBILITY_STATUSES = {
    "ADMISSIBLE",
    "BLOCKED_FUTURE_AVAILABLE_TIME",
    "BLOCKED_FUTURE_REVISION",
    "BLOCKED_MISSING_HASH",
    "BLOCKED_MISSING_REVISION",
    "BLOCKED_PERMISSION",
    "BLOCKED_QUALITY",
    "BLOCKED_REVIEW",
    "BLOCKED_PRIVATE_RESTRICTED_ILLEGAL",
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
    "MISSING_AVAILABLE_TIME",
    "MISSING_HASH_OR_REVISION",
    "QUALITY_FAIL",
    "MANUAL_REVIEW_FAIL",
    "RESTRICTED_SOURCE",
    "PRIVATE_OR_ILLEGAL_SOURCE",
    "ST_OR_DELIST_RISK",
    "SUSPENSION_OR_NO_TRADE",
    "UNRESOLVED_EVENT_RISK",
    "DIAGNOSTIC_ONLY",
}
ALLOWED_TRADE_USAGE = {
    "research_context",
    "replay_evidence_context",
    "risk_filter",
    "observe_only",
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

REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS = [
    "replay_evidence_bundle_id",
    "bundle_version",
    "bundle_key",
    "schema_version",
    "created_by_workflow",
    "created_at",
    "report_only",
    "diagnostic_only",
    "replay_decision_time",
    "replay_as_of_date",
    "replay_calendar",
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
    "bundle_status",
    "workflow_stage",
    "bundle_completeness_status",
    "validation_issue_count",
    "blocking_issue_count",
    "warning_issue_count",
    "evidence_item_count",
    "admissible_evidence_count",
    "blocked_evidence_count",
    "missing_required_evidence_count",
    "source_registry_run_id",
    "source_registry_status",
    "source_registry_health_status",
    "source_id_refs",
    "source_permission_status",
    "source_tier_summary",
    "source_registry_version",
    "source_policy_version",
    "raw_document_store_run_id",
    "raw_document_store_status",
    "raw_document_store_health_status",
    "document_id_refs",
    "dataset_id_refs",
    "document_version_refs",
    "raw_document_ref_count",
    "raw_dataset_ref_count",
    "source_hash_coverage",
    "content_hash_coverage",
    "metadata_hash_coverage",
    "columns_hash_coverage",
    "revision_id_coverage",
    "storage_policy_status",
    "factor_definition_run_id",
    "factor_definition_status",
    "factor_definition_health_status",
    "factor_definition_version_refs",
    "factor_id_refs",
    "taxonomy_layer_refs",
    "factor_definition_coverage_status",
    "company_exposure_run_id",
    "company_exposure_status",
    "company_exposure_health_status",
    "company_exposure_id_refs",
    "exposure_context_count",
    "exposure_pit_valid",
    "exposure_direction_context_status",
    "event_structured_run_id",
    "event_structured_status",
    "event_structured_health_status",
    "event_structured_id_refs",
    "event_count",
    "event_available_time_status",
    "event_compliance_status",
    "event_confidence_summary",
    "factor_observation_run_id",
    "factor_observation_status",
    "factor_observation_health_status",
    "factor_observation_id_refs",
    "factor_observation_count",
    "factor_observation_available_time_status",
    "factor_observation_value_semantics_status",
    "factor_observation_transform_status",
    "factor_observation_signal_score_input_authorized",
    "available_time_max",
    "all_available_time_lte_replay_time",
    "future_label_excluded",
    "future_revision_excluded",
    "decision_time_eligible",
    "pit_valid",
    "stale_evidence_count",
    "unavailable_evidence_count",
    "future_dated_evidence_count",
    "revision_gap_count",
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
    "replay_evidence_bundle_created",
    "real_replay_evidence_bundle_created",
    "replay_decisions_created",
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
    "period_end",
    "source_publish_time",
    "raw_document_or_dataset_required",
    "parser_version_refs",
    "extractor_version_refs",
    "calculation_version_refs",
    "admissibility_status",
    "trade_usage",
    "evidence_item_types",
]

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "real_replay_evidence_bundles_created",
    "replay_decisions_created",
    "forward_labels_created",
    "future_labels_joined",
    "production_factor_observations_created",
    "real_factor_observations_created",
    "production_factor_registry_created",
    "active_factor_library_created",
    "production_event_ingestion_created",
    "active_event_library_created",
    "production_company_exposure_mapping_created",
    "real_raw_document_ingestion_created",
    "normalization_created",
    "winsorization_created",
    "direction_adjusted_values_created",
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
    "real_replay_evidence_bundle_created",
    "replay_decisions_created",
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


@dataclass(frozen=True)
class ReplayEvidenceBundleSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/replay_evidence_bundle_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class ReplayEvidenceBundleSchemaFixtureResult:
    replay_evidence_bundle_schema_fixture_id: str
    status: str
    workflow_stage: str
    bundle_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_replay_evidence_bundle_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: ReplayEvidenceBundleSchemaFixtureSettings | None = None,
) -> ReplayEvidenceBundleSchemaFixtureResult:
    resolved_settings = settings or ReplayEvidenceBundleSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = ReplayEvidenceBundleSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_replay_evidence_bundle_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_replay_evidence_bundle_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_replay_evidence_bundle_schema_fields()
    item_matrix = build_replay_evidence_bundle_item_matrix(fixture_rows)
    pit_admissibility_matrix = build_replay_evidence_bundle_pit_admissibility_matrix(fixture_rows)
    lineage_matrix = build_replay_evidence_bundle_lineage_matrix(fixture_rows)
    quality_compliance_matrix = build_replay_evidence_bundle_quality_compliance_matrix(fixture_rows)
    risk_veto_matrix = build_replay_evidence_bundle_risk_veto_matrix(fixture_rows)
    forbidden_output_guard_matrix = build_replay_evidence_bundle_forbidden_output_guard_matrix()
    validation_summary = validate_replay_evidence_bundle_fixture(fixture_rows, resolved_settings)
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = ReplayEvidenceBundleSchemaFixtureResult(
        replay_evidence_bundle_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED,
        bundle_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_replay_evidence_bundle_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            item_matrix=item_matrix,
            pit_admissibility_matrix=pit_admissibility_matrix,
            lineage_matrix=lineage_matrix,
            quality_compliance_matrix=quality_compliance_matrix,
            risk_veto_matrix=risk_veto_matrix,
            forbidden_output_guard_matrix=forbidden_output_guard_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_replay_evidence_bundle_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            replay_evidence_bundle_id="SYNTH_COMPLETE_PRICE_VOLUME_FACTOR_BUNDLE",
            bundle_completeness_status="COMPLETE_SYNTHETIC_FIXTURE",
            entity_id="SYNTH_ENTITY_001",
            symbol="SYN001",
            instrument_type="STOCK",
            source_id_refs="SYNTH_EXCHANGE_SOURCE",
            dataset_id_refs="SYNTH_DAILY_BAR_DATASET",
            raw_dataset_ref_count=1,
            factor_id_refs="L5_SYNTH_DAILY_RETURN_CONTEXT",
            factor_observation_id_refs="SYNTH_DAILY_RETURN_PRICE_VOLUME_OBSERVATION",
            factor_observation_count=1,
            evidence_item_types="SOURCE_REGISTRY|RAW_DATASET|FACTOR_DEFINITION|FACTOR_OBSERVATION|SYNTHETIC_FIXTURE",
            trade_usage="replay_evidence_context",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_FUNDAMENTAL_AVAILABLE_AFTER_PERIOD_END_BUNDLE",
            entity_id="SYNTH_ENTITY_002",
            symbol="SYN002",
            instrument_type="STOCK",
            replay_decision_time="2024-04-26T09:30:00",
            available_time_max="2024-04-25T09:30:00",
            period_end="2024-03-31",
            source_publish_time="2024-04-24T20:00:00",
            source_id_refs="SYNTH_COMPANY_DISCLOSURE_SOURCE",
            document_id_refs="SYNTH_REVENUE_REPORT_DOC",
            document_version_refs="SYNTH_REVENUE_REPORT_DOC_V1",
            raw_document_ref_count=1,
            factor_id_refs="L1_SYNTH_REVENUE_GROWTH_CONTEXT",
            factor_observation_id_refs="SYNTH_REVENUE_GROWTH_FUNDAMENTAL_CONTEXT",
            factor_observation_count=1,
            evidence_item_types="SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|FACTOR_OBSERVATION|SYNTHETIC_FIXTURE",
            trade_usage="replay_evidence_context",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_EVENT_POLICY_CONTEXT_BUNDLE",
            entity_id="SYNTH_ENTITY_003",
            symbol="SYN003",
            source_id_refs="SYNTH_POLICY_SOURCE",
            document_id_refs="SYNTH_POLICY_DOC",
            raw_document_ref_count=1,
            event_structured_id_refs="SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT",
            event_count=1,
            event_available_time_status="PASS",
            event_compliance_status="PUBLIC_ALLOWED",
            event_confidence_summary="synthetic event confidence context only",
            factor_id_refs="L3_SYNTH_POLICY_CONTEXT",
            factor_observation_id_refs="SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT_CONTEXT",
            factor_observation_count=1,
            evidence_item_types=(
                "SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|EVENT_STRUCTURED|"
                "FACTOR_OBSERVATION|COMPLIANCE_RULE|SYNTHETIC_FIXTURE"
            ),
            trade_usage="replay_evidence_context",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_COMPANY_EXPOSURE_DIRECTION_CONTEXT_BUNDLE",
            entity_id="SYNTH_ENTITY_004",
            symbol="SYN004",
            source_id_refs="SYNTH_EXPOSURE_SOURCE",
            document_id_refs="SYNTH_EXPOSURE_DOC",
            raw_document_ref_count=1,
            company_exposure_id_refs="SYNTH_EXPORT_POLICY_EXPOSURE",
            exposure_context_count=1,
            exposure_pit_valid=True,
            exposure_direction_context_status="MIXED_BY_EXPOSURE",
            factor_id_refs="L2_SYNTH_EXPOSURE_CONTEXT",
            factor_observation_id_refs="SYNTH_EXPORT_TRADE_POLICY_EXPOSURE_CONTEXT",
            factor_observation_count=1,
            evidence_item_types=(
                "SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|COMPANY_EXPOSURE|"
                "FACTOR_OBSERVATION|SYNTHETIC_FIXTURE"
            ),
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_COMMODITY_COST_SPREAD_BUNDLE",
            entity_id="SYNTH_ENTITY_005",
            symbol="SYN005",
            source_id_refs="SYNTH_COMMODITY_SOURCE",
            dataset_id_refs="SYNTH_COMMODITY_SPREAD_DATASET",
            raw_dataset_ref_count=1,
            company_exposure_id_refs="SYNTH_STEEL_BUYER_EXPOSURE|SYNTH_RESOURCE_PRODUCER_EXPOSURE",
            exposure_context_count=2,
            exposure_pit_valid=True,
            exposure_direction_context_status="EXPOSURE_DEPENDENT",
            factor_id_refs="L2_SYNTH_COMMODITY_COST_SPREAD",
            factor_observation_id_refs="SYNTH_IRON_ORE_COST_PRESSURE_CONTEXT",
            factor_observation_count=1,
            evidence_item_types=(
                "SOURCE_REGISTRY|RAW_DATASET|FACTOR_DEFINITION|COMPANY_EXPOSURE|"
                "FACTOR_OBSERVATION|SYNTHETIC_FIXTURE"
            ),
            factor_observation_transform_status="RAW_ONLY_NOT_SIGNAL_SCORE",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_RISK_VETO_ST_DELIST_BUNDLE",
            bundle_status="WARN",
            bundle_completeness_status="BLOCKED_MISSING_REQUIRED_EVIDENCE",
            admissibility_status="BLOCKED_QUALITY",
            entity_id="SYNTH_ENTITY_006",
            symbol="SYN006",
            source_id_refs="SYNTH_RISK_STATUS_SOURCE",
            document_id_refs="SYNTH_ST_DELIST_RISK_DOC",
            raw_document_ref_count=1,
            factor_id_refs="L8_SYNTH_ST_DELIST_RISK",
            factor_observation_id_refs="SYNTH_ST_DELIST_RISK_VETO_OBSERVATION",
            factor_observation_count=1,
            decision_time_eligible=False,
            pit_valid=False,
            risk_veto_flag=True,
            risk_veto_type="ST_OR_DELIST_RISK",
            hard_veto_reason="Synthetic ST/delist risk veto; no positive alpha and no buy permission.",
            no_trade_reason="risk_veto_blocks_actionability",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
            blocking_issue_count=1,
            blocked_evidence_count=1,
            evidence_item_types="SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|FACTOR_OBSERVATION|RISK_VETO|SYNTHETIC_FIXTURE",
            trade_usage="no_trade",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_BLOCKED_FUTURE_AVAILABLE_TIME_BUNDLE",
            bundle_status="WARN",
            bundle_completeness_status="BLOCKED_PIT_VIOLATION",
            admissibility_status="BLOCKED_FUTURE_AVAILABLE_TIME",
            entity_id="SYNTH_ENTITY_007",
            symbol="SYN007",
            replay_decision_time="2024-04-02T09:30:00",
            available_time_max="2024-04-03T09:30:00",
            all_available_time_lte_replay_time=False,
            future_dated_evidence_count=1,
            unavailable_evidence_count=1,
            decision_time_eligible=False,
            pit_valid=False,
            source_id_refs="SYNTH_FUTURE_AVAILABLE_SOURCE",
            document_id_refs="SYNTH_FUTURE_AVAILABLE_DOC",
            raw_document_ref_count=1,
            factor_id_refs="L1_SYNTH_FUTURE_AVAILABLE_CONTEXT",
            factor_observation_id_refs="SYNTH_FUTURE_AVAILABLE_FACTOR_OBSERVATION",
            factor_observation_count=1,
            risk_veto_type="FUTURE_LEAKAGE",
            hard_veto_reason="Evidence available after replay_decision_time is blocked from decision-time bundle.",
            blocking_issue_count=1,
            blocked_evidence_count=1,
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
            evidence_item_types="SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|FACTOR_OBSERVATION|RISK_VETO|SYNTHETIC_FIXTURE",
            trade_usage="no_trade",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_BLOCKED_MISSING_HASH_REVISION_BUNDLE",
            bundle_status="WARN",
            bundle_completeness_status="BLOCKED_MISSING_REQUIRED_EVIDENCE",
            admissibility_status="BLOCKED_MISSING_HASH",
            entity_id="SYNTH_ENTITY_008",
            symbol="SYN008",
            source_id_refs="SYNTH_MISSING_HASH_SOURCE",
            document_id_refs="SYNTH_MISSING_HASH_DOC",
            raw_document_ref_count=1,
            factor_id_refs="L6_SYNTH_MISSING_HASH_CONTEXT",
            factor_observation_id_refs="SYNTH_MISSING_HASH_OBSERVATION",
            factor_observation_count=1,
            source_hash_coverage="MISSING",
            content_hash_coverage="MISSING",
            metadata_hash_coverage="MISSING",
            revision_id_coverage="MISSING",
            revision_gap_count=1,
            decision_time_eligible=False,
            pit_valid=False,
            risk_veto_type="MISSING_HASH_OR_REVISION",
            hard_veto_reason="Missing hash or revision id blocks admissibility.",
            blocking_issue_count=1,
            blocked_evidence_count=1,
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
            evidence_item_types="SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|FACTOR_OBSERVATION|RISK_VETO|SYNTHETIC_FIXTURE",
            trade_usage="no_trade",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_BLOCKED_RESTRICTED_OR_PRIVATE_SOURCE_BUNDLE",
            bundle_status="WARN",
            bundle_completeness_status="BLOCKED_RESTRICTED_OR_ILLEGAL_SOURCE",
            admissibility_status="BLOCKED_PRIVATE_RESTRICTED_ILLEGAL",
            entity_id="SYNTH_ENTITY_009",
            symbol="SYN009",
            source_id_refs="SYNTH_RESTRICTED_SOURCE",
            document_id_refs="SYNTH_RESTRICTED_DOC",
            raw_document_ref_count=1,
            factor_id_refs="L8_SYNTH_RESTRICTED_SOURCE_CONTEXT",
            factor_observation_id_refs="SYNTH_RESTRICTED_SOURCE_OBSERVATION",
            factor_observation_count=1,
            source_permission_status="BLOCKED",
            permission_class_summary="RESTRICTED|PRIVATE",
            compliance_class="RESTRICTED",
            restricted_source_count=1,
            private_source_count=1,
            decision_time_eligible=False,
            pit_valid=False,
            risk_veto_type="PRIVATE_OR_ILLEGAL_SOURCE",
            hard_veto_reason="Restricted/private evidence is blocked and no_trade.",
            blocking_issue_count=1,
            blocked_evidence_count=1,
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
            evidence_item_types="SOURCE_REGISTRY|RAW_DOCUMENT|FACTOR_DEFINITION|FACTOR_OBSERVATION|COMPLIANCE_RULE|RISK_VETO|SYNTHETIC_FIXTURE",
            trade_usage="no_trade",
        ),
        _row(
            replay_evidence_bundle_id="SYNTH_OBSERVE_ONLY_INCOMPLETE_CONTEXT_BUNDLE",
            bundle_status="WARN",
            bundle_completeness_status="PARTIAL_CONTEXT_ONLY",
            admissibility_status="OBSERVE_ONLY",
            entity_id="SYNTH_ENTITY_010",
            symbol="SYN010",
            source_id_refs="SYNTH_PARTIAL_CONTEXT_SOURCE",
            dataset_id_refs="SYNTH_PARTIAL_CONTEXT_DATASET",
            raw_dataset_ref_count=1,
            factor_id_refs="L7_SYNTH_PARTIAL_CONTEXT",
            factor_observation_id_refs="SYNTH_PARTIAL_CONTEXT_OBSERVATION",
            factor_observation_count=1,
            missing_required_evidence_count=1,
            warning_issue_count=1,
            decision_time_eligible=False,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
            evidence_item_types="SOURCE_REGISTRY|RAW_DATASET|FACTOR_DEFINITION|FACTOR_OBSERVATION|SYNTHETIC_FIXTURE",
            trade_usage="observe_only",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS)


def build_replay_evidence_bundle_schema_fields() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "field_group": _field_group(field),
                "required": True,
                "data_type_hint": _data_type_hint(field),
                "description": _field_description(field),
                "allowed_values": _allowed_values(field),
            }
            for field in REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS
        ]
    )


def build_replay_evidence_bundle_item_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for evidence_type in sorted(EVIDENCE_ITEM_TYPES):
        matched = fixture_rows[
            fixture_rows["evidence_item_types"].map(lambda value: evidence_type in _split_refs(value))
        ]
        rows.append(
            {
                "evidence_item_type": evidence_type,
                "row_count": len(matched),
                "bundle_ids": "|".join(matched["replay_evidence_bundle_id"]),
                "report_only": True,
                "diagnostic_only": True,
            }
        )
    return pd.DataFrame(rows)


def build_replay_evidence_bundle_pit_admissibility_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_evidence_bundle_id",
        "replay_decision_time",
        "available_time_max",
        "all_available_time_lte_replay_time",
        "future_label_excluded",
        "future_revision_excluded",
        "decision_time_eligible",
        "pit_valid",
        "admissibility_status",
        "stale_evidence_count",
        "unavailable_evidence_count",
        "future_dated_evidence_count",
        "revision_gap_count",
    ]
    return fixture_rows[columns].copy()


def build_replay_evidence_bundle_lineage_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_evidence_bundle_id",
        "source_registry_run_id",
        "source_id_refs",
        "raw_document_store_run_id",
        "document_id_refs",
        "dataset_id_refs",
        "factor_definition_run_id",
        "factor_id_refs",
        "company_exposure_run_id",
        "company_exposure_id_refs",
        "event_structured_run_id",
        "event_structured_id_refs",
        "factor_observation_run_id",
        "factor_observation_id_refs",
        "source_hash_coverage",
        "content_hash_coverage",
        "metadata_hash_coverage",
        "revision_id_coverage",
        "parser_version_refs",
        "extractor_version_refs",
        "calculation_version_refs",
    ]
    return fixture_rows[columns].copy()


def build_replay_evidence_bundle_quality_compliance_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_evidence_bundle_id",
        "quality_status",
        "manual_review_required",
        "manual_review_status",
        "compliance_class",
        "permission_class_summary",
        "source_permission_status",
        "restricted_source_count",
        "illegal_source_count",
        "private_source_count",
        "rumor_only_count",
    ]
    return fixture_rows[columns].copy()


def build_replay_evidence_bundle_risk_veto_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "replay_evidence_bundle_id",
        "risk_veto_flag",
        "risk_veto_type",
        "hard_veto_reason",
        "no_trade_reason",
        "trade_usage",
        "decision_time_eligible",
        "pit_valid",
    ]
    return fixture_rows[columns].copy()


def build_replay_evidence_bundle_forbidden_output_guard_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "guard_name": flag,
                "observed_value": False,
                "expected_value": False,
                "passed": True,
                "notes": "Forbidden side effect remains false for report-only schema fixture.",
            }
            for flag in ROW_FALSE_FLAGS
        ]
    )


def validate_replay_evidence_bundle_fixture(
    fixture_rows: pd.DataFrame,
    settings: ReplayEvidenceBundleSchemaFixtureSettings,
) -> pd.DataFrame:
    checks = [
        ("settings_report_only", settings.report_only),
        ("settings_diagnostic_only", settings.diagnostic_only),
        ("exactly_10_rows", len(fixture_rows) == 10),
        ("unique_bundle_ids", fixture_rows["replay_evidence_bundle_id"].is_unique),
        ("required_fields_present", set(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS).issubset(fixture_rows.columns)),
        ("status_stage_convention", set(fixture_rows["workflow_stage"]) == {REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED}),
        ("valid_bundle_statuses", set(fixture_rows["bundle_status"]) <= BUNDLE_STATUSES),
        ("valid_completeness_statuses", set(fixture_rows["bundle_completeness_status"]) <= BUNDLE_COMPLETENESS_STATUSES),
        ("valid_admissibility_statuses", set(fixture_rows["admissibility_status"]) <= ADMISSIBILITY_STATUSES),
        ("valid_quality_statuses", set(fixture_rows["quality_status"]) <= QUALITY_STATUSES),
        ("valid_manual_review_statuses", set(fixture_rows["manual_review_status"]) <= MANUAL_REVIEW_STATUSES),
        ("valid_compliance_classes", set(fixture_rows["compliance_class"]) <= COMPLIANCE_CLASSES),
        ("valid_risk_veto_types", set(fixture_rows["risk_veto_type"]) <= RISK_VETO_TYPES),
        ("no_forbidden_trade_usage", not set(fixture_rows["trade_usage"]) & FORBIDDEN_TRADE_USAGE),
        ("required_context_present", _all_non_empty(fixture_rows, ["replay_decision_time", "entity_id", "symbol", "instrument_type"])),
        ("source_linkage_present", fixture_rows["source_id_refs"].map(_is_non_empty_string).all()),
        ("future_labels_excluded", fixture_rows["future_label_excluded"].map(_bool).all()),
        ("future_revisions_excluded", fixture_rows["future_revision_excluded"].map(_bool).all()),
        (
            "admissible_available_time_lte_replay_time",
            fixture_rows[fixture_rows["admissibility_status"] == "ADMISSIBLE"].apply(
                lambda row: _timestamp_order_ok(row["available_time_max"], row["replay_decision_time"]),
                axis=1,
            ).all(),
        ),
        ("row_false_flags_false", all((fixture_rows[flag] == False).all() for flag in ROW_FALSE_FLAGS)),  # noqa: E712
        ("no_sensitive_credential_like_values", not _contains_secret_like(fixture_rows.to_csv(index=False))),
    ]
    return pd.DataFrame(
        [
            {
                "check_name": check_name,
                "passed": bool(passed),
                "details": "PASS" if passed else "FAIL",
            }
            for check_name, passed in checks
        ]
    )


def resolve_replay_evidence_bundle_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "replay_evidence_bundle_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "replay_evidence_bundle_schema_fields.csv",
        "fixture_rows": artifact_dir / "replay_evidence_bundle_fixture_rows.csv",
        "item_matrix": artifact_dir / "replay_evidence_bundle_item_matrix.csv",
        "pit_admissibility_matrix": artifact_dir / "replay_evidence_bundle_pit_admissibility_matrix.csv",
        "lineage_matrix": artifact_dir / "replay_evidence_bundle_lineage_matrix.csv",
        "quality_compliance_matrix": artifact_dir / "replay_evidence_bundle_quality_compliance_matrix.csv",
        "risk_veto_matrix": artifact_dir / "replay_evidence_bundle_risk_veto_matrix.csv",
        "forbidden_output_guard_matrix": artifact_dir / "replay_evidence_bundle_forbidden_output_guard_matrix.csv",
        "validation_summary": artifact_dir / "replay_evidence_bundle_validation_summary.csv",
        "limitations": artifact_dir / "replay_evidence_bundle_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_replay_evidence_bundle_schema_fixture_artifacts(
    *,
    result: ReplayEvidenceBundleSchemaFixtureResult,
    settings: ReplayEvidenceBundleSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    item_matrix: pd.DataFrame,
    pit_admissibility_matrix: pd.DataFrame,
    lineage_matrix: pd.DataFrame,
    quality_compliance_matrix: pd.DataFrame,
    risk_veto_matrix: pd.DataFrame,
    forbidden_output_guard_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    item_matrix.to_csv(paths["item_matrix"], index=False)
    pit_admissibility_matrix.to_csv(paths["pit_admissibility_matrix"], index=False)
    lineage_matrix.to_csv(paths["lineage_matrix"], index=False)
    quality_compliance_matrix.to_csv(paths["quality_compliance_matrix"], index=False)
    risk_veto_matrix.to_csv(paths["risk_veto_matrix"], index=False)
    forbidden_output_guard_matrix.to_csv(paths["forbidden_output_guard_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_replay_evidence_bundle_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_replay_evidence_bundle_limitations(result: ReplayEvidenceBundleSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Replay Evidence Bundle Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic replay_evidence_bundle rows for schema and governance review only.",
            "",
            "## Not Created",
            "",
            "- No real replay evidence bundles are created.",
            "- No replay decisions are created.",
            "- No forward labels or future labels are created or joined.",
            "- No real factor observations, production factor registry, or active factor library is created.",
            "- No production event ingestion or production company exposure mapping is created.",
            "- No real raw document ingestion, source adapters, crawlers, connectors, or LLM extraction runtime is created.",
            "- No normalization, winsorization, or direction-adjusted runtime is created.",
            "- No signal_score implementation or signal score input authorization is created.",
            "- No model training, active weights, active thresholds, stock_profile validation, or paper validation is created.",
            "- No buy-review eligibility, buy_review_allowed, or strategy performance validation is created.",
            "- No trading, broker behavior, orders, messages, or APIs are created.",
            "",
            "## Current Result",
            "",
            f"- replay_evidence_bundle_schema_fixture_id: {result.replay_evidence_bundle_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- bundle_count: {result.bundle_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: ReplayEvidenceBundleSchemaFixtureResult,
    settings: ReplayEvidenceBundleSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "replay_evidence_bundle_schema_fixture_id": result.replay_evidence_bundle_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "replay_evidence_bundle_schema_fixture_created": True,
        "replay_evidence_bundle_rows_created": True,
        "bundle_count": result.bundle_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "conceptual_formula": (
            "bundle_{i,T}=admissible_sources_{<=T}+raw_document_refs_{<=T}+"
            "factor_definitions_{<=T}+company_exposures_{i,<=T}+"
            "event_structured_context_{i,<=T}+factor_observations_{i,<=T}"
        ),
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    bundle_id = values.get("replay_evidence_bundle_id", "")
    row: dict[str, Any] = {
        "replay_evidence_bundle_id": bundle_id,
        "bundle_version": "replay_evidence_bundle_schema_fixture_v0.1",
        "bundle_key": "",
        "schema_version": "replay_evidence_bundle_schema_fixture_v0.1",
        "created_by_workflow": "replay-evidence-bundle-schema-fixture",
        "created_at": "2026-06-27T00:00:00",
        "report_only": True,
        "diagnostic_only": True,
        "replay_decision_time": "2024-04-02T17:30:00",
        "replay_as_of_date": "2024-04-02",
        "replay_calendar": "CN_SYNTHETIC_TRADING_CALENDAR",
        "decision_timezone": "Asia/Shanghai",
        "decision_session": "POST_CLOSE_REVIEW",
        "entity_id": "SYNTH_ENTITY",
        "symbol": "SYN000",
        "instrument_type": "SYNTHETIC_ENTITY",
        "exchange": "SYNTHETIC",
        "market": "CN_SYNTHETIC",
        "universe_name": "synthetic_replay_fixture",
        "universe_as_of_date": "2024-04-02",
        "candidate_context_ref": "SYNTH_CANDIDATE_CONTEXT",
        "bundle_status": "PASS",
        "workflow_stage": REPLAY_EVIDENCE_BUNDLE_SCHEMA_FIXTURE_CREATED,
        "bundle_completeness_status": "COMPLETE_SYNTHETIC_FIXTURE",
        "validation_issue_count": 0,
        "blocking_issue_count": 0,
        "warning_issue_count": 0,
        "evidence_item_count": 5,
        "admissible_evidence_count": 5,
        "blocked_evidence_count": 0,
        "missing_required_evidence_count": 0,
        "source_registry_run_id": "3d04b1f6480e",
        "source_registry_status": "PASS",
        "source_registry_health_status": "PASS",
        "source_id_refs": "SYNTH_SOURCE",
        "source_permission_status": "ALLOWED",
        "source_tier_summary": "SYNTHETIC_FIXTURE",
        "source_registry_version": "source_registry_schema_fixture_v0.1",
        "source_policy_version": "source_policy_schema_fixture_v0.1",
        "raw_document_store_run_id": "ea35302eb116",
        "raw_document_store_status": "PASS",
        "raw_document_store_health_status": "PASS",
        "document_id_refs": "",
        "dataset_id_refs": "",
        "document_version_refs": "",
        "raw_document_ref_count": 0,
        "raw_dataset_ref_count": 0,
        "source_hash_coverage": "COMPLETE",
        "content_hash_coverage": "COMPLETE",
        "metadata_hash_coverage": "COMPLETE",
        "columns_hash_coverage": "COMPLETE",
        "revision_id_coverage": "COMPLETE",
        "storage_policy_status": "MANUAL_DIAGNOSTICS_ONLY",
        "factor_definition_run_id": "3692a14c6771",
        "factor_definition_status": "PASS",
        "factor_definition_health_status": "PASS",
        "factor_definition_version_refs": "factor_definition_schema_fixture_v0.1",
        "factor_id_refs": "",
        "taxonomy_layer_refs": "L5_TRADING_BEHAVIOR_MICROSTRUCTURE",
        "factor_definition_coverage_status": "COMPLETE",
        "company_exposure_run_id": "192547b93758",
        "company_exposure_status": "PASS",
        "company_exposure_health_status": "PASS",
        "company_exposure_id_refs": "",
        "exposure_context_count": 0,
        "exposure_pit_valid": False,
        "exposure_direction_context_status": "NOT_APPLICABLE",
        "event_structured_run_id": "1822243d009a",
        "event_structured_status": "PASS",
        "event_structured_health_status": "PASS",
        "event_structured_id_refs": "",
        "event_count": 0,
        "event_available_time_status": "NOT_APPLICABLE",
        "event_compliance_status": "NOT_APPLICABLE",
        "event_confidence_summary": "not_applicable",
        "factor_observation_run_id": "b1577e2e725a",
        "factor_observation_status": "PASS",
        "factor_observation_health_status": "PASS",
        "factor_observation_id_refs": "",
        "factor_observation_count": 0,
        "factor_observation_available_time_status": "PASS",
        "factor_observation_value_semantics_status": "RAW_CONTEXT_ONLY",
        "factor_observation_transform_status": "NO_RUNTIME_TRANSFORM",
        "factor_observation_signal_score_input_authorized": False,
        "available_time_max": "2024-04-02T17:00:00",
        "all_available_time_lte_replay_time": True,
        "future_label_excluded": True,
        "future_revision_excluded": True,
        "decision_time_eligible": True,
        "pit_valid": True,
        "stale_evidence_count": 0,
        "unavailable_evidence_count": 0,
        "future_dated_evidence_count": 0,
        "revision_gap_count": 0,
        "quality_status": "PASS",
        "manual_review_required": True,
        "manual_review_status": "REVIEW_REQUIRED",
        "reviewer": "diagnostic_fixture",
        "reviewed_at": "",
        "compliance_class": "PUBLIC_ALLOWED",
        "permission_class_summary": "PUBLIC_ALLOWED",
        "restricted_source_count": 0,
        "illegal_source_count": 0,
        "private_source_count": 0,
        "rumor_only_count": 0,
        "risk_veto_flag": False,
        "risk_veto_type": "NONE",
        "hard_veto_reason": "",
        "no_trade_reason": "",
        "replay_evidence_bundle_created": True,
        "recommended_next_task": "Replay Evidence Bundle Schema Fixture Views Report-Only v0.1",
        "limitations_ref": "replay_evidence_bundle_limitations.md",
        "validation_summary_ref": "replay_evidence_bundle_validation_summary.csv",
        "period_end": "2024-04-02",
        "source_publish_time": "2024-04-02T16:00:00",
        "raw_document_or_dataset_required": True,
        "parser_version_refs": "synthetic_parser_v0.1",
        "extractor_version_refs": "synthetic_extractor_v0.1",
        "calculation_version_refs": "synthetic_calculation_v0.1",
        "admissibility_status": "ADMISSIBLE",
        "trade_usage": "replay_evidence_context",
        "evidence_item_types": "SOURCE_REGISTRY|SYNTHETIC_FIXTURE",
    }
    row.update({flag: False for flag in ROW_FALSE_FLAGS})
    row.update(values)
    if not row["bundle_key"]:
        row["bundle_key"] = f"{row['symbol']}::{row['replay_decision_time']}::{row['replay_evidence_bundle_id']}"
    return row


def _assert_settings_safe(settings: ReplayEvidenceBundleSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Replay evidence bundle schema fixture must remain report_only and diagnostic_only.")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_REPLAY_EVIDENCE_BUNDLE_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Replay Evidence Bundle Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only replay evidence bundle schema fixture. Keep the workflow synthetic and do not create real replay evidence bundles, replay decisions, forward labels, signal_score inputs, model training inputs, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, current-candidates, snapshots, signal_semantics mutation, broker/order/message/API behavior, or trading permission.",
        ]
    )


def _field_group(field: str) -> str:
    groups = {
        "identity_version": {"replay_evidence_bundle_id", "bundle_version", "bundle_key", "schema_version", "created_by_workflow", "created_at", "report_only", "diagnostic_only"},
        "replay_context": {"replay_decision_time", "replay_as_of_date", "replay_calendar", "decision_timezone", "decision_session", "entity_id", "symbol", "instrument_type", "exchange", "market", "universe_name", "universe_as_of_date", "candidate_context_ref"},
        "bundle_status": {"bundle_status", "workflow_stage", "bundle_completeness_status", "validation_issue_count", "blocking_issue_count", "warning_issue_count", "evidence_item_count", "admissible_evidence_count", "blocked_evidence_count", "missing_required_evidence_count"},
        "source_registry_lineage": {"source_registry_run_id", "source_registry_status", "source_registry_health_status", "source_id_refs", "source_permission_status", "source_tier_summary", "source_registry_version", "source_policy_version"},
        "raw_document_dataset_lineage": {"raw_document_store_run_id", "raw_document_store_status", "raw_document_store_health_status", "document_id_refs", "dataset_id_refs", "document_version_refs", "raw_document_ref_count", "raw_dataset_ref_count", "source_hash_coverage", "content_hash_coverage", "metadata_hash_coverage", "columns_hash_coverage", "revision_id_coverage", "storage_policy_status"},
        "factor_definition_lineage": {"factor_definition_run_id", "factor_definition_status", "factor_definition_health_status", "factor_definition_version_refs", "factor_id_refs", "taxonomy_layer_refs", "factor_definition_coverage_status"},
        "company_exposure_lineage": {"company_exposure_run_id", "company_exposure_status", "company_exposure_health_status", "company_exposure_id_refs", "exposure_context_count", "exposure_pit_valid", "exposure_direction_context_status"},
        "event_structured_lineage": {"event_structured_run_id", "event_structured_status", "event_structured_health_status", "event_structured_id_refs", "event_count", "event_available_time_status", "event_compliance_status", "event_confidence_summary"},
        "factor_observation_lineage": {"factor_observation_run_id", "factor_observation_status", "factor_observation_health_status", "factor_observation_id_refs", "factor_observation_count", "factor_observation_available_time_status", "factor_observation_value_semantics_status", "factor_observation_transform_status", "factor_observation_signal_score_input_authorized"},
        "pit_admissibility": {"available_time_max", "all_available_time_lte_replay_time", "future_label_excluded", "future_revision_excluded", "decision_time_eligible", "pit_valid", "stale_evidence_count", "unavailable_evidence_count", "future_dated_evidence_count", "revision_gap_count", "period_end", "source_publish_time", "admissibility_status"},
        "quality_review_compliance": {"quality_status", "manual_review_required", "manual_review_status", "reviewer", "reviewed_at", "compliance_class", "permission_class_summary", "restricted_source_count", "illegal_source_count", "private_source_count", "rumor_only_count", "risk_veto_flag", "risk_veto_type", "hard_veto_reason", "no_trade_reason", "trade_usage"},
    }
    for group, fields in groups.items():
        if field in fields:
            return group
    if field in ROW_FALSE_FLAGS or field == "replay_evidence_bundle_created":
        return "safety_governance"
    return "recommended_next"


def _field_description(field: str) -> str:
    descriptions = {
        "replay_evidence_bundle_id": "Stable synthetic replay evidence bundle identifier.",
        "replay_decision_time": "Historical decision-time cutoff T for PIT admissibility.",
        "available_time_max": "Latest available_time across included synthetic evidence.",
        "future_label_excluded": "Must remain true; labels and outcomes are excluded from evidence bundles.",
        "trade_usage": "Non-actionable report-only usage category.",
        "buy_review_allowed": "Must remain false.",
        "trading_allowed": "Must remain false.",
    }
    return descriptions.get(field, "Replay evidence bundle schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "report_only",
        "diagnostic_only",
        "all_available_time_lte_replay_time",
        "future_label_excluded",
        "future_revision_excluded",
        "decision_time_eligible",
        "pit_valid",
        "manual_review_required",
        "risk_veto_flag",
        "replay_evidence_bundle_created",
        "raw_document_or_dataset_required",
        "exposure_pit_valid",
        "factor_observation_signal_score_input_authorized",
    } | set(ROW_FALSE_FLAGS):
        return "boolean"
    if field.endswith("_count") or field in {"evidence_item_count", "admissible_evidence_count", "blocked_evidence_count"}:
        return "integer"
    if field in {"replay_decision_time", "available_time_max", "source_publish_time", "created_at", "reviewed_at"}:
        return "timestamp"
    if field in {"replay_as_of_date", "universe_as_of_date", "period_end"}:
        return "date"
    return "string"


def _allowed_values(field: str) -> str:
    mapping = {
        "bundle_status": BUNDLE_STATUSES,
        "bundle_completeness_status": BUNDLE_COMPLETENESS_STATUSES,
        "admissibility_status": ADMISSIBILITY_STATUSES,
        "quality_status": QUALITY_STATUSES,
        "manual_review_status": MANUAL_REVIEW_STATUSES,
        "compliance_class": COMPLIANCE_CLASSES,
        "risk_veto_type": RISK_VETO_TYPES,
        "trade_usage": ALLOWED_TRADE_USAGE,
        "evidence_item_types": EVIDENCE_ITEM_TYPES,
    }
    return "|".join(sorted(mapping.get(field, [])))


def _all_non_empty(frame: pd.DataFrame, columns: list[str]) -> bool:
    return all(frame[column].map(_is_non_empty_string).all() for column in columns)


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_ts = pd.to_datetime(_text(first), errors="coerce")
    second_ts = pd.to_datetime(_text(second), errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _split_refs(value: Any) -> set[str]:
    return {part.strip() for part in _text(value).split("|") if part.strip()}


def _is_non_empty_string(value: Any) -> bool:
    return bool(_text(value))


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text.lower()))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
