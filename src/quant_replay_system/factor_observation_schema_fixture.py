"""Report-only factor observation schema fixture workflow.

This module writes tiny synthetic factor_observation rows for schema and
governance review only. Factor observations in this fixture are not real factor
observations, active model inputs, signal scores, buy/sell rules, stock profile
validation, paper validation, performance validation, or trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED = "FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED"

REQUIRED_FACTOR_OBSERVATION_FIELDS = [
    "factor_observation_id",
    "observation_version",
    "observation_key",
    "schema_version",
    "created_by_workflow",
    "created_at",
    "factor_id",
    "factor_definition_version",
    "factor_name",
    "taxonomy_layer_id",
    "taxonomy_layer_name",
    "second_level",
    "observation_rule_ref",
    "factor_family",
    "factor_observation_type",
    "entity_id",
    "symbol",
    "instrument_type",
    "exchange",
    "market",
    "industry_id",
    "sector_id",
    "region_tags",
    "product_tags",
    "commodity_tags",
    "policy_tags",
    "company_exposure_id_refs",
    "event_structured_id_refs",
    "observation_date",
    "observation_time",
    "period_start",
    "period_end",
    "source_publish_time",
    "available_time",
    "as_of_date",
    "decision_time_eligible",
    "pit_valid",
    "stale_after",
    "timezone",
    "lag_days",
    "revision_id",
    "supersedes_observation_version_id",
    "source_id",
    "source_name",
    "source_tier",
    "dataset_id",
    "document_id",
    "document_version_id",
    "source_hash",
    "content_hash",
    "metadata_hash",
    "raw_document_ref",
    "raw_dataset_ref",
    "url_or_file_ref",
    "permission_class",
    "storage_policy",
    "parser_version",
    "extractor_version",
    "calculation_version",
    "extraction_method",
    "calculation_method",
    "value_dtype",
    "raw_value",
    "value_unit",
    "value_scale",
    "categorical_value",
    "boolean_value",
    "ordinal_value",
    "missing_value_policy",
    "imputation_status",
    "denominator_policy",
    "frequency",
    "transform_status",
    "normalization_status",
    "winsorization_status",
    "direction_adjustment_status",
    "normalized_value",
    "winsorized_value",
    "direction_adjusted_value",
    "direction_rule_type",
    "direction_for_entity",
    "direction_rule_detail",
    "exposure_direction_context",
    "event_direction_context",
    "market_regime_context",
    "expected_horizon",
    "risk_veto_flag",
    "hard_veto_reason",
    "trade_usage",
    "observation_confidence",
    "evidence_confidence",
    "calculation_confidence",
    "evidence_specificity",
    "manual_review_required",
    "manual_review_status",
    "reviewer",
    "reviewed_at",
    "quality_status",
    "validation_notes",
    "validation_issue_count",
    "compliance_class",
    "report_only",
    "diagnostic_only",
    "is_live_signal",
    "is_alpha_claim",
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
    "observation_status",
    "production_event_ingestion_created",
    "production_company_exposure_mapping_created",
]

FACTOR_OBSERVATION_TYPES = {
    "MARKET_PRICE_VOLUME",
    "TECHNICAL_INDICATOR",
    "FUNDAMENTAL_REPORT",
    "FINANCIAL_RATIO",
    "ANNOUNCEMENT_EVENT_CONTEXT",
    "POLICY_EVENT_CONTEXT",
    "INDUSTRY_CHAIN_PRICE",
    "COMMODITY_SPREAD",
    "COMPANY_EXPOSURE_CONTEXT",
    "RISK_STATUS",
    "MACRO_CONTEXT",
    "SYNTHETIC_FIXTURE",
}

INSTRUMENT_TYPES = {"STOCK", "ETF", "INDEX", "INDUSTRY", "COMMODITY_PROXY", "MACRO_SERIES", "SYNTHETIC_ENTITY"}
VALUE_DTYPES = {"NUMERIC", "BOOLEAN", "CATEGORICAL", "ORDINAL", "TEXT_LABEL", "MISSING", "BLOCKED"}
FREQUENCIES = {"INTRADAY", "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "ANNUAL", "EVENT_DRIVEN", "AD_HOC", "SYNTHETIC_FIXTURE"}
SOURCE_TIERS = {
    "OFFICIAL",
    "EXCHANGE",
    "COMPANY_DISCLOSURE",
    "REGULATOR",
    "MAJOR_MEDIA",
    "INDUSTRY_MEDIA",
    "REVIEWED_LOCAL_CSV",
    "SYNTHETIC_FIXTURE",
}
DIRECTION_RULE_TYPES = {"DIRECT", "INVERSE", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME", "CONDITIONAL", "RISK_VETO_ONLY", "UNKNOWN"}
DIRECTION_FOR_ENTITY = {"POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "CONDITIONAL", "RISK_VETO_ONLY", "UNKNOWN", "NOT_APPLICABLE"}
TRANSFORM_STATUSES = {"RAW_ONLY", "NOT_APPLIED_REPORT_ONLY", "PLANNED_ONLY", "BLOCKED", "DIAGNOSTIC_ONLY"}
NORMALIZATION_STATUSES = {"NOT_APPLIED", "NOT_ALLOWED_IN_FIXTURE", "PLANNED_ONLY", "BLOCKED", "DIAGNOSTIC_ONLY"}
WINSORIZATION_STATUSES = {"NOT_APPLIED", "NOT_ALLOWED_IN_FIXTURE", "PLANNED_ONLY", "BLOCKED", "DIAGNOSTIC_ONLY"}
DIRECTION_ADJUSTMENT_STATUSES = {"NOT_APPLIED", "NOT_ALLOWED_IN_FIXTURE", "PLANNED_ONLY", "BLOCKED", "DIAGNOSTIC_ONLY"}
QUALITY_STATUSES = {"PASS", "WARN", "REVIEW_REQUIRED", "FAIL", "BLOCKED", "DIAGNOSTIC_ONLY"}
MANUAL_REVIEW_STATUSES = {"NOT_REVIEWED", "REVIEW_REQUIRED", "REVIEWED_PASS", "REVIEWED_WARN", "REVIEWED_FAIL", "BLOCKED", "DIAGNOSTIC_ONLY"}
OBSERVATION_STATUSES = {"OBSERVED", "MISSING", "STALE", "SUPERSEDED", "BLOCKED", "DIAGNOSTIC_ONLY"}
ALLOWED_TRADE_USAGE = {"research_context", "factor_context", "event_context", "exposure_context", "risk_filter", "observe_only", "no_trade", "diagnostic_only"}
FORBIDDEN_TRADE_USAGE = {
    "buy_signal",
    "sell_signal",
    "real_buy_review",
    "trading_signal",
    "active_portfolio_weight",
    "active_model_input",
    "active_threshold_input",
}

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "production_factor_observations_created",
    "real_factor_observations_created",
    "production_factor_registry_created",
    "active_factor_library_created",
    "production_event_ingestion_created",
    "active_event_library_created",
    "production_company_exposure_mapping_created",
    "real_raw_document_ingestion_created",
    "replay_evidence_bundle_created",
    "replay_decisions_created",
    "forward_labels_created",
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


@dataclass(frozen=True)
class FactorObservationSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/factor_observation_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    production_factor_observations_created: bool = False
    real_factor_observations_created: bool = False
    production_factor_registry_created: bool = False
    active_factor_library_created: bool = False
    production_event_ingestion_created: bool = False
    active_event_library_created: bool = False
    production_company_exposure_mapping_created: bool = False
    real_raw_document_ingestion_created: bool = False
    replay_evidence_bundle_created: bool = False
    replay_decisions_created: bool = False
    forward_labels_created: bool = False
    normalization_created: bool = False
    winsorization_created: bool = False
    direction_adjusted_values_created: bool = False
    signal_score_implemented: bool = False
    signal_score_input_authorized: bool = False
    model_training_performed: bool = False
    active_weights_created: bool = False
    active_thresholds_created: bool = False
    stock_profile_validation_created: bool = False
    paper_validation_created: bool = False
    real_buy_review_eligible: bool = False
    buy_review_allowed: bool = False
    strategy_performance_validated: bool = False
    trading_allowed: bool = False
    live_trading_enabled: bool = False
    broker_api_called: bool = False
    external_api_called: bool = False
    llm_api_called: bool = False
    data_raw_written: bool = False
    data_processed_written: bool = False
    data_cache_written: bool = False
    current_candidates_run: bool = False
    snapshot_built: bool = False
    signal_semantics_changed: bool = False
    active_stock_profile_created: bool = False
    operational_global_approved_for_paper_granted: bool = False


@dataclass(frozen=True)
class FactorObservationSchemaFixtureResult:
    factor_observation_schema_fixture_id: str
    status: str
    workflow_stage: str
    observation_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_factor_observation_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: FactorObservationSchemaFixtureSettings | None = None,
) -> FactorObservationSchemaFixtureResult:
    resolved_settings = settings or FactorObservationSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = FactorObservationSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_factor_observation_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_factor_observation_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_factor_observation_schema_fields()
    type_matrix = build_factor_observation_type_matrix(fixture_rows)
    value_semantics_matrix = build_factor_observation_value_semantics_matrix(fixture_rows)
    pit_lineage_matrix = build_factor_observation_pit_lineage_matrix(fixture_rows)
    source_quality_matrix = build_factor_observation_source_quality_matrix(fixture_rows)
    factor_event_exposure_lineage_matrix = build_factor_event_exposure_lineage_matrix(fixture_rows)
    validation_summary = validate_factor_observation_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = FactorObservationSchemaFixtureResult(
        factor_observation_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=FACTOR_OBSERVATION_SCHEMA_FIXTURE_CREATED,
        observation_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_factor_observation_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            type_matrix=type_matrix,
            value_semantics_matrix=value_semantics_matrix,
            pit_lineage_matrix=pit_lineage_matrix,
            source_quality_matrix=source_quality_matrix,
            factor_event_exposure_lineage_matrix=factor_event_exposure_lineage_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_factor_observation_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            factor_observation_id="SYNTH_DAILY_RETURN_PRICE_VOLUME_OBSERVATION",
            factor_id="L5_SYNTH_DAILY_RETURN_CONTEXT",
            factor_name="Synthetic daily price-volume context",
            taxonomy_layer_id="L5_TRADING_BEHAVIOR_MICROSTRUCTURE",
            taxonomy_layer_name="Trading behavior and microstructure",
            second_level="price_volume_context",
            observation_rule_ref="synthetic_daily_price_volume_observation_rule",
            factor_family="market_price_volume",
            factor_observation_type="MARKET_PRICE_VOLUME",
            entity_id="SYNTH_STOCK_ENTITY_001",
            symbol="000001",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_BANKING",
            sector_id="SYNTH_FINANCIALS",
            observation_date="2024-04-01",
            observation_time="2024-04-02T15:00:00",
            period_start="2024-04-02",
            period_end="2024-04-02",
            source_publish_time="2024-04-02T15:30:00",
            available_time="2024-04-02T17:00:00",
            as_of_date="2024-04-03",
            source_tier="EXCHANGE",
            dataset_id="SYNTH_EXCHANGE_DAILY_BAR_DATASET",
            document_id="",
            document_version_id="",
            value_dtype="NUMERIC",
            raw_value="0.0123",
            value_unit="decimal_return_like_context",
            value_scale="1.0",
            frequency="DAILY",
            direction_rule_type="DIRECT",
            direction_for_entity="NEUTRAL",
            direction_rule_detail="Synthetic daily return-like context is descriptive only and not a signal or prediction.",
            trade_usage="factor_context",
            observation_confidence=0.82,
            evidence_confidence=0.84,
            calculation_confidence=0.8,
            quality_status="PASS",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_MOVING_AVERAGE_TECHNICAL_CONTEXT",
            factor_id="L5_SYNTH_MOVING_AVERAGE_CONTEXT",
            factor_name="Synthetic moving average context",
            taxonomy_layer_id="L5_TRADING_BEHAVIOR_MICROSTRUCTURE",
            taxonomy_layer_name="Trading behavior and microstructure",
            second_level="technical_indicator_context",
            observation_rule_ref="synthetic_moving_average_observation_rule",
            factor_family="technical_indicator",
            factor_observation_type="TECHNICAL_INDICATOR",
            entity_id="SYNTH_STOCK_ENTITY_002",
            symbol="000002",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_INDUSTRIALS",
            sector_id="SYNTH_INDUSTRIALS",
            observation_date="2024-04-01",
            observation_time="2024-04-02T15:00:00",
            period_start="2024-03-20",
            period_end="2024-04-02",
            source_publish_time="2024-04-02T15:30:00",
            available_time="2024-04-02T17:00:00",
            as_of_date="2024-04-03",
            source_tier="REVIEWED_LOCAL_CSV",
            dataset_id="SYNTH_TECHNICAL_CONTEXT_DATASET",
            value_dtype="NUMERIC",
            raw_value="1.045",
            value_unit="ratio_to_synthetic_moving_average",
            value_scale="1.0",
            frequency="DAILY",
            direction_rule_type="UNKNOWN",
            direction_for_entity="UNKNOWN",
            direction_rule_detail="Synthetic raw technical context only; no active threshold and no buy/sell rule.",
            trade_usage="observe_only",
            observation_confidence=0.7,
            evidence_confidence=0.74,
            calculation_confidence=0.72,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_REVENUE_GROWTH_FUNDAMENTAL_CONTEXT",
            factor_id="L1_SYNTH_REVENUE_GROWTH_CONTEXT",
            factor_name="Synthetic revenue growth context",
            taxonomy_layer_id="L1_OPERATIONS_COMPANY_EVENTS",
            taxonomy_layer_name="Operations and company events",
            second_level="fundamental_report_context",
            observation_rule_ref="synthetic_revenue_growth_observation_rule",
            factor_family="fundamental_report",
            factor_observation_type="FUNDAMENTAL_REPORT",
            entity_id="SYNTH_STOCK_ENTITY_003",
            symbol="000003",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_ADVANCED_MANUFACTURING",
            sector_id="SYNTH_INDUSTRIALS",
            observation_date="2024-03-31",
            period_start="2024-01-01",
            period_end="2024-03-31",
            source_publish_time="2024-04-24T20:00:00",
            available_time="2024-04-25T09:30:00",
            as_of_date="2024-04-26",
            source_tier="COMPANY_DISCLOSURE",
            document_id="SYNTH_REVENUE_REPORT_DOC",
            document_version_id="SYNTH_REVENUE_REPORT_DOC_V1",
            value_dtype="NUMERIC",
            raw_value="0.084",
            value_unit="yoy_growth_decimal",
            value_scale="1.0",
            denominator_policy="reported_period_revenue_prior_year_same_period",
            frequency="QUARTERLY",
            direction_rule_type="DIRECT",
            direction_for_entity="POSITIVE",
            direction_rule_detail="Positive revenue growth is context only and not immediately usable before available_time.",
            trade_usage="factor_context",
            observation_confidence=0.86,
            evidence_confidence=0.88,
            calculation_confidence=0.83,
            quality_status="PASS",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_ROE_FINANCIAL_RATIO_CONTEXT",
            factor_id="L1_SYNTH_ROE_CONTEXT",
            factor_name="Synthetic ROE financial ratio context",
            taxonomy_layer_id="L1_OPERATIONS_COMPANY_EVENTS",
            taxonomy_layer_name="Operations and company events",
            second_level="financial_ratio_context",
            observation_rule_ref="synthetic_roe_observation_rule",
            factor_family="financial_ratio",
            factor_observation_type="FINANCIAL_RATIO",
            entity_id="SYNTH_STOCK_ENTITY_004",
            symbol="000004",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_CONSUMER",
            sector_id="SYNTH_CONSUMER",
            observation_date="2024-03-31",
            period_start="2024-01-01",
            period_end="2024-03-31",
            source_publish_time="2024-04-26T20:00:00",
            available_time="2024-04-27T09:30:00",
            as_of_date="2024-04-28",
            source_tier="COMPANY_DISCLOSURE",
            document_id="SYNTH_ROE_REPORT_DOC",
            document_version_id="SYNTH_ROE_REPORT_DOC_V1",
            value_dtype="NUMERIC",
            raw_value="0.117",
            value_unit="roe_decimal",
            value_scale="1.0",
            denominator_policy="reported_average_equity",
            frequency="QUARTERLY",
            direction_rule_type="DIRECT",
            direction_for_entity="POSITIVE",
            direction_rule_detail="ROE context requires calculation_version and is not model training input.",
            trade_usage="factor_context",
            observation_confidence=0.84,
            evidence_confidence=0.86,
            calculation_confidence=0.8,
            quality_status="PASS",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_IRON_ORE_COST_PRESSURE_CONTEXT",
            factor_id="L2_SYNTH_IRON_ORE_COST_PRESSURE",
            factor_name="Synthetic iron ore cost pressure context",
            taxonomy_layer_id="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            taxonomy_layer_name="Industry supply demand and value-chain prices",
            second_level="industry_chain_price_context",
            observation_rule_ref="synthetic_iron_ore_cost_pressure_rule",
            factor_family="industry_chain_price",
            factor_observation_type="INDUSTRY_CHAIN_PRICE",
            entity_id="SYNTH_STEEL_BUYER_ENTITY",
            symbol="000005",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_STEEL",
            sector_id="SYNTH_MATERIALS",
            commodity_tags="iron_ore",
            company_exposure_id_refs="SYNTH_STEEL_IRON_ORE_COST_BUYER,SYNTH_IRON_ORE_RESOURCE_PRODUCER",
            observation_date="2024-04-01",
            period_start="2024-04-02",
            period_end="2024-04-02",
            source_publish_time="2024-04-02T16:00:00",
            available_time="2024-04-02T17:30:00",
            as_of_date="2024-04-03",
            source_tier="INDUSTRY_MEDIA",
            dataset_id="SYNTH_COMMODITY_CONTEXT_DATASET",
            value_dtype="NUMERIC",
            raw_value="3.2",
            value_unit="synthetic_pct_change",
            value_scale="percent",
            frequency="DAILY",
            direction_rule_type="MIXED_BY_EXPOSURE",
            direction_for_entity="MIXED",
            direction_rule_detail="Iron ore cost pressure may be negative for a steel buyer and positive for a resource producer; no direct factor direction without exposure context.",
            exposure_direction_context="steel buyer cost pressure versus resource producer revenue context",
            trade_usage="exposure_context",
            observation_confidence=0.76,
            evidence_confidence=0.78,
            calculation_confidence=0.72,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_STEEL_SPREAD_MARGIN_CONTEXT",
            factor_id="L2_SYNTH_STEEL_SPREAD_MARGIN",
            factor_name="Synthetic steel spread margin context",
            taxonomy_layer_id="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            taxonomy_layer_name="Industry supply demand and value-chain prices",
            second_level="commodity_spread_context",
            observation_rule_ref="synthetic_steel_spread_margin_rule",
            factor_family="commodity_spread",
            factor_observation_type="COMMODITY_SPREAD",
            entity_id="SYNTH_STEEL_INDUSTRY_CONTEXT",
            symbol="SYNTH_STEEL_INDEX",
            instrument_type="INDUSTRY",
            exchange="SYNTHETIC",
            industry_id="SYNTH_STEEL",
            sector_id="SYNTH_MATERIALS",
            commodity_tags="steel,iron_ore,coke",
            observation_date="2024-04-01",
            period_start="2024-04-02",
            period_end="2024-04-02",
            source_publish_time="2024-04-02T16:00:00",
            available_time="2024-04-02T18:00:00",
            as_of_date="2024-04-03",
            source_tier="REVIEWED_LOCAL_CSV",
            dataset_id="SYNTH_STEEL_SPREAD_DATASET",
            value_dtype="NUMERIC",
            raw_value="125.0",
            value_unit="synthetic_margin_proxy",
            value_scale="index_points",
            frequency="DAILY",
            direction_rule_type="CONDITIONAL",
            direction_for_entity="CONDITIONAL",
            direction_rule_detail="Steel spread is descriptive industry-chain context only and does not validate performance.",
            trade_usage="factor_context",
            observation_confidence=0.72,
            evidence_confidence=0.72,
            calculation_confidence=0.7,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT_CONTEXT",
            factor_id="L3_SYNTH_POLICY_CAPACITY_CONTEXT",
            factor_name="Synthetic policy capacity restriction event context",
            taxonomy_layer_id="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            taxonomy_layer_name="Macro liquidity policy and global context",
            second_level="policy_event_context",
            observation_rule_ref="synthetic_policy_capacity_context_rule",
            factor_family="policy_event_context",
            factor_observation_type="POLICY_EVENT_CONTEXT",
            entity_id="SYNTH_POLICY_AFFECTED_ENTITY",
            symbol="000006",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_STEEL",
            sector_id="SYNTH_MATERIALS",
            policy_tags="capacity_restriction",
            company_exposure_id_refs="SYNTH_REGIONAL_CAPACITY_RESTRICTION",
            event_structured_id_refs="SYNTH_OFFICIAL_STEEL_CAPACITY_RESTRICTION",
            observation_date="2024-04-01",
            source_publish_time="2024-04-01T15:00:00",
            available_time="2024-04-01T17:00:00",
            as_of_date="2024-04-02",
            source_tier="OFFICIAL",
            document_id="SYNTH_POLICY_CAPACITY_DOC",
            document_version_id="SYNTH_POLICY_CAPACITY_DOC_V1",
            value_dtype="CATEGORICAL",
            raw_value="",
            categorical_value="capacity_restriction_context",
            frequency="EVENT_DRIVEN",
            direction_rule_type="CONDITIONAL",
            direction_for_entity="CONDITIONAL",
            direction_rule_detail="Event-derived policy context references event_structured context but does not create production event ingestion.",
            event_direction_context="depends on restricted capacity exposure",
            trade_usage="event_context",
            observation_confidence=0.8,
            evidence_confidence=0.83,
            calculation_confidence=0.66,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_EXPORT_TRADE_POLICY_EXPOSURE_CONTEXT",
            factor_id="L3_SYNTH_EXPORT_TRADE_POLICY_CONTEXT",
            factor_name="Synthetic export trade policy exposure context",
            taxonomy_layer_id="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            taxonomy_layer_name="Macro liquidity policy and global context",
            second_level="trade_policy_exposure_context",
            observation_rule_ref="synthetic_export_trade_policy_context_rule",
            factor_family="company_exposure_context",
            factor_observation_type="COMPANY_EXPOSURE_CONTEXT",
            entity_id="SYNTH_EXPORTER_ENTITY",
            symbol="000007",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_EXPORT_MANUFACTURING",
            sector_id="SYNTH_INDUSTRIALS",
            region_tags="synthetic_export_region",
            policy_tags="export_trade_policy",
            company_exposure_id_refs="SYNTH_EXPORTER_POLICY_EXPOSURE,SYNTH_IMPORTER_POLICY_EXPOSURE",
            event_structured_id_refs="SYNTH_EXPORT_TRADE_POLICY_CHANGE",
            observation_date="2024-04-03",
            source_publish_time="2024-04-03T14:00:00",
            available_time="2024-04-03T17:00:00",
            as_of_date="2024-04-04",
            source_tier="REGULATOR",
            document_id="SYNTH_EXPORT_POLICY_DOC",
            document_version_id="SYNTH_EXPORT_POLICY_DOC_V1",
            value_dtype="TEXT_LABEL",
            raw_value="",
            categorical_value="conditional_export_policy_context",
            frequency="EVENT_DRIVEN",
            direction_rule_type="CONDITIONAL",
            direction_for_entity="CONDITIONAL",
            direction_rule_detail="Trade policy direction depends on exporter/importer exposure and does not create production exposure mapping.",
            exposure_direction_context="exporter and importer exposure context only",
            event_direction_context="policy event reference only",
            trade_usage="exposure_context",
            observation_confidence=0.77,
            evidence_confidence=0.8,
            calculation_confidence=0.65,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_ST_DELIST_RISK_VETO_OBSERVATION",
            factor_id="L8_SYNTH_ST_DELIST_RISK_VETO",
            factor_name="Synthetic ST/delist risk veto context",
            taxonomy_layer_id="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            taxonomy_layer_name="Risk events and compliance boundary",
            second_level="risk_status_context",
            observation_rule_ref="synthetic_st_delist_risk_veto_rule",
            factor_family="risk_status",
            factor_observation_type="RISK_STATUS",
            entity_id="SYNTH_RISK_ENTITY",
            symbol="000008",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_RISK_INDUSTRY",
            sector_id="SYNTH_RISK_SECTOR",
            observation_date="2024-04-01",
            source_publish_time="2024-04-02T12:00:00",
            available_time="2024-04-02T15:30:00",
            as_of_date="2024-04-03",
            source_tier="EXCHANGE",
            dataset_id="SYNTH_RISK_STATUS_DATASET",
            value_dtype="BOOLEAN",
            raw_value="",
            boolean_value="True",
            frequency="DAILY",
            direction_rule_type="RISK_VETO_ONLY",
            direction_for_entity="RISK_VETO_ONLY",
            direction_rule_detail="Risk veto observation may block actionability but creates no positive alpha.",
            risk_veto_flag=True,
            hard_veto_reason="synthetic ST/delist risk requires review",
            trade_usage="risk_filter",
            observation_confidence=0.86,
            evidence_confidence=0.86,
            calculation_confidence=0.7,
            quality_status="REVIEW_REQUIRED",
            manual_review_status="REVIEW_REQUIRED",
        ),
        _row(
            factor_observation_id="SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION",
            factor_id="L8_SYNTH_BLOCKED_UNVERIFIED_CONTEXT",
            factor_name="Synthetic blocked unverified event observation",
            taxonomy_layer_id="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            taxonomy_layer_name="Risk events and compliance boundary",
            second_level="blocked_unverified_context",
            observation_rule_ref="synthetic_blocked_unverified_observation_rule",
            factor_family="risk_status",
            factor_observation_type="SYNTHETIC_FIXTURE",
            entity_id="SYNTH_BLOCKED_ENTITY",
            symbol="000009",
            instrument_type="STOCK",
            exchange="SZSE",
            industry_id="SYNTH_UNKNOWN",
            sector_id="SYNTH_UNKNOWN",
            event_structured_id_refs="SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT",
            observation_date="2024-04-02",
            source_publish_time="2024-04-02T10:00:00",
            available_time="2024-04-02T10:00:00",
            as_of_date="2024-04-03",
            decision_time_eligible=False,
            pit_valid=False,
            source_tier="SYNTHETIC_FIXTURE",
            value_dtype="BLOCKED",
            raw_value="",
            frequency="AD_HOC",
            direction_rule_type="UNKNOWN",
            direction_for_entity="UNKNOWN",
            direction_rule_detail="Blocked unverified observation is no_trade and cannot be used as an active usable value.",
            observation_status="BLOCKED",
            manual_review_status="BLOCKED",
            quality_status="BLOCKED",
            trade_usage="no_trade",
            observation_confidence=0.0,
            evidence_confidence=0.0,
            calculation_confidence=0.0,
            validation_issue_count=1,
            compliance_class="BLOCKED_NO_TRADE",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_FACTOR_OBSERVATION_FIELDS)


def build_factor_observation_schema_fields() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "field_group": _field_group(field),
                "required": True,
                "data_type_hint": _data_type_hint(field),
                "allowed_values": _allowed_values(field),
                "description": _field_description(field),
            }
            for field in REQUIRED_FACTOR_OBSERVATION_FIELDS
        ]
    )


def build_factor_observation_type_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    return (
        rows.groupby(["factor_observation_type", "instrument_type", "source_tier", "frequency"], dropna=False)
        .size()
        .reset_index(name="row_count")
    )


def build_factor_observation_value_semantics_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[
        [
            "factor_observation_id",
            "value_dtype",
            "raw_value",
            "categorical_value",
            "boolean_value",
            "value_unit",
            "transform_status",
            "normalization_status",
            "winsorization_status",
            "direction_adjustment_status",
            "normalized_value",
            "winsorized_value",
            "direction_adjusted_value",
            "observation_status",
            "trade_usage",
        ]
    ].copy()


def build_factor_observation_pit_lineage_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[
        [
            "factor_observation_id",
            "observation_date",
            "period_start",
            "period_end",
            "source_publish_time",
            "available_time",
            "as_of_date",
            "stale_after",
            "pit_valid",
            "decision_time_eligible",
            "revision_id",
            "supersedes_observation_version_id",
        ]
    ].copy()


def build_factor_observation_source_quality_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[
        [
            "factor_observation_id",
            "source_id",
            "source_name",
            "source_tier",
            "dataset_id",
            "document_id",
            "document_version_id",
            "source_hash",
            "content_hash",
            "metadata_hash",
            "parser_version",
            "extractor_version",
            "calculation_version",
            "quality_status",
            "manual_review_status",
            "observation_confidence",
            "evidence_confidence",
            "calculation_confidence",
        ]
    ].copy()


def build_factor_event_exposure_lineage_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[
        [
            "factor_observation_id",
            "factor_id",
            "factor_definition_version",
            "taxonomy_layer_id",
            "company_exposure_id_refs",
            "event_structured_id_refs",
            "direction_rule_type",
            "direction_for_entity",
            "direction_rule_detail",
            "exposure_direction_context",
            "event_direction_context",
            "trade_usage",
        ]
    ].copy()


def validate_factor_observation_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: FactorObservationSchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    lower_text = fixture_rows.to_csv(index=False).lower()
    blocked = fixture_rows.set_index("factor_observation_id").loc["SYNTH_BLOCKED_UNVERIFIED_EVENT_OBSERVATION"]
    risk = fixture_rows.set_index("factor_observation_id").loc["SYNTH_ST_DELIST_RISK_VETO_OBSERVATION"]
    commodity = fixture_rows.set_index("factor_observation_id").loc["SYNTH_IRON_ORE_COST_PRESSURE_CONTEXT"]
    event_row = fixture_rows.set_index("factor_observation_id").loc["SYNTH_POLICY_CAPACITY_RESTRICTION_EVENT_CONTEXT"]
    exposure_row = fixture_rows.set_index("factor_observation_id").loc["SYNTH_EXPORT_TRADE_POLICY_EXPOSURE_CONTEXT"]
    period_rows = fixture_rows[fixture_rows["period_end"].map(_is_non_empty_string)]
    observed = fixture_rows[fixture_rows["observation_status"] == "OBSERVED"]
    evidence_backed = fixture_rows[fixture_rows["source_tier"] != "SYNTHETIC_FIXTURE"]
    checks: list[tuple[str, bool]] = [
        ("exactly_10_rows", len(fixture_rows) == 10),
        ("unique_factor_observation_id", fixture_rows["factor_observation_id"].is_unique),
        ("required_fields_present", set(REQUIRED_FACTOR_OBSERVATION_FIELDS).issubset(fixture_rows.columns)),
        ("factor_id_present", fixture_rows["factor_id"].map(_is_non_empty_string).all()),
        ("factor_definition_version_present", fixture_rows["factor_definition_version"].map(_is_non_empty_string).all()),
        ("taxonomy_layer_id_present", fixture_rows["taxonomy_layer_id"].map(_is_non_empty_string).all()),
        ("observation_date_present", fixture_rows["observation_date"].map(_is_non_empty_string).all()),
        ("available_time_present", fixture_rows["available_time"].map(_is_non_empty_string).all()),
        ("available_time_lte_as_of_date", fixture_rows.apply(lambda row: _timestamp_to_date_order_ok(row["available_time"], row["as_of_date"]), axis=1).all()),
        ("period_end_lte_available_time", period_rows.apply(lambda row: _date_lte_timestamp(row["period_end"], row["available_time"]), axis=1).all()),
        ("stale_after_not_before_available_time", fixture_rows.apply(lambda row: _timestamp_order_ok(row["available_time"], row["stale_after"]), axis=1).all()),
        ("source_id_present", fixture_rows["source_id"].map(_is_non_empty_string).all()),
        ("document_or_dataset_present_for_evidence_backed", evidence_backed.apply(lambda row: bool(row["document_id"]) or bool(row["dataset_id"]), axis=1).all()),
        ("hashes_present", fixture_rows[["source_hash", "content_hash", "metadata_hash"]].map(_is_non_empty_string).all().all()),
        ("revision_id_present", fixture_rows["revision_id"].map(_is_non_empty_string).all()),
        ("versions_present", fixture_rows[["parser_version", "extractor_version", "calculation_version"]].map(_is_non_empty_string).all().all()),
        ("valid_factor_observation_type", fixture_rows["factor_observation_type"].isin(FACTOR_OBSERVATION_TYPES).all()),
        ("valid_instrument_type", fixture_rows["instrument_type"].isin(INSTRUMENT_TYPES).all()),
        ("valid_value_dtype", fixture_rows["value_dtype"].isin(VALUE_DTYPES).all()),
        ("valid_direction_rule_type", fixture_rows["direction_rule_type"].isin(DIRECTION_RULE_TYPES).all()),
        ("valid_direction_for_entity", fixture_rows["direction_for_entity"].isin(DIRECTION_FOR_ENTITY).all()),
        ("valid_quality_status", fixture_rows["quality_status"].isin(QUALITY_STATUSES).all()),
        ("valid_manual_review_status", fixture_rows["manual_review_status"].isin(MANUAL_REVIEW_STATUSES).all()),
        ("valid_observation_status", fixture_rows["observation_status"].isin(OBSERVATION_STATUSES).all()),
        ("valid_trade_usage", fixture_rows["trade_usage"].isin(ALLOWED_TRADE_USAGE).all()),
        ("observed_rows_have_value", observed.apply(lambda row: bool(row["raw_value"]) or bool(row["categorical_value"]) or bool(row["boolean_value"]), axis=1).all()),
        ("blocked_row_no_active_value", not bool(blocked["raw_value"]) and blocked["value_dtype"] == "BLOCKED"),
        ("confidence_bounded", fixture_rows[["observation_confidence", "evidence_confidence", "calculation_confidence"]].astype(float).map(lambda value: 0 <= value <= 1).all().all()),
        ("confidence_not_return_probability", "not return probability" in lower_text),
        ("conditional_mixed_direction_detail", fixture_rows[fixture_rows["direction_rule_type"].isin({"CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"})]["direction_rule_detail"].map(_is_non_empty_string).all()),
        ("commodity_exposure_dependent", "steel buyer" in commodity["direction_rule_detail"] and "resource producer" in commodity["direction_rule_detail"]),
        ("event_row_references_event_no_ingestion", bool(event_row["event_structured_id_refs"]) and not _bool(event_row["production_event_ingestion_created"])),
        ("exposure_row_references_exposure_no_production_mapping", bool(exposure_row["company_exposure_id_refs"]) and not _bool(exposure_row["production_company_exposure_mapping_created"])),
        ("risk_veto_no_positive_alpha", risk["direction_rule_type"] == "RISK_VETO_ONLY" and not _bool(risk["is_alpha_claim"]) and "no positive alpha" in risk["direction_rule_detail"]),
        ("blocked_row_no_trade", blocked["trade_usage"] == "no_trade"),
        ("blocked_row_not_pit_valid", not _bool(blocked["pit_valid"])),
        ("blocked_row_not_decision_time_eligible", not _bool(blocked["decision_time_eligible"])),
        ("normalization_inactive", not fixture_rows["normalization_status"].isin({"ACTIVE", "APPLIED"}).any()),
        ("winsorization_inactive", not fixture_rows["winsorization_status"].isin({"ACTIVE", "APPLIED"}).any()),
        ("direction_adjustment_inactive", not fixture_rows["direction_adjustment_status"].isin({"ACTIVE", "APPLIED"}).any()),
        ("normalized_values_inactive", fixture_rows["normalized_value"].isin({"", "not_applied"}).all()),
        ("winsorized_values_inactive", fixture_rows["winsorized_value"].isin({"", "not_applied"}).all()),
        ("direction_adjusted_values_inactive", fixture_rows["direction_adjusted_value"].isin({"", "not_applied"}).all()),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("is_live_signal_false", fixture_rows["is_live_signal"].map(lambda value: not _bool(value)).all()),
        ("is_alpha_claim_false", fixture_rows["is_alpha_claim"].map(lambda value: not _bool(value)).all()),
        ("signal_score_implemented_false", fixture_rows["signal_score_implemented"].map(lambda value: not _bool(value)).all()),
        ("signal_score_input_authorized_false", fixture_rows["signal_score_input_authorized"].map(lambda value: not _bool(value)).all()),
        ("model_training_allowed_false", fixture_rows["model_training_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_weight_allowed_false", fixture_rows["active_weight_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_threshold_allowed_false", fixture_rows["active_threshold_allowed"].map(lambda value: not _bool(value)).all()),
        ("stock_profile_validation_allowed_false", fixture_rows["stock_profile_validation_allowed"].map(lambda value: not _bool(value)).all()),
        ("paper_validation_allowed_false", fixture_rows["paper_validation_allowed"].map(lambda value: not _bool(value)).all()),
        ("real_buy_review_allowed_false", fixture_rows["real_buy_review_allowed"].map(lambda value: not _bool(value)).all()),
        ("buy_review_allowed_false", fixture_rows["buy_review_allowed"].map(lambda value: not _bool(value)).all()),
        ("strategy_performance_validated_false", fixture_rows["strategy_performance_validated"].map(lambda value: not _bool(value)).all()),
        ("trading_allowed_false", fixture_rows["trading_allowed"].map(lambda value: not _bool(value)).all()),
        ("no_forbidden_trade_usage", not fixture_rows["trade_usage"].isin(FORBIDDEN_TRADE_USAGE).any()),
        ("no_token_or_private_values", not _contains_secret_like(lower_text)),
        ("settings_forbidden_flags_false", all(getattr(settings, flag) is False for flag in FORBIDDEN_METADATA_FALSE_FLAGS)),
        ("no_protected_data_writes", not any((output_dir / part).exists() for part in ["data/raw", "data/processed", "data/cache"])),
        ("no_docs_project_sources", not (output_dir / "docs" / "project_sources").exists()),
    ]
    checks.extend((f"settings_{flag}_false", getattr(settings, flag) is False) for flag in FORBIDDEN_METADATA_FALSE_FLAGS)
    return pd.DataFrame(
        [
            {
                "check_name": name,
                "passed": bool(passed),
                "issue_detail": "" if passed else f"{name} failed",
            }
            for name, passed in checks
        ]
    )


def resolve_factor_observation_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "factor_observation_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "factor_observation_schema_fields.csv",
        "fixture_rows": artifact_dir / "factor_observation_fixture_rows.csv",
        "type_matrix": artifact_dir / "factor_observation_type_matrix.csv",
        "value_semantics_matrix": artifact_dir / "factor_observation_value_semantics_matrix.csv",
        "pit_lineage_matrix": artifact_dir / "factor_observation_pit_lineage_matrix.csv",
        "source_quality_matrix": artifact_dir / "factor_observation_source_quality_matrix.csv",
        "factor_event_exposure_lineage_matrix": artifact_dir / "factor_observation_factor_event_exposure_lineage_matrix.csv",
        "validation_summary": artifact_dir / "factor_observation_validation_summary.csv",
        "limitations": artifact_dir / "factor_observation_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_factor_observation_schema_fixture_artifacts(
    *,
    result: FactorObservationSchemaFixtureResult,
    settings: FactorObservationSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    type_matrix: pd.DataFrame,
    value_semantics_matrix: pd.DataFrame,
    pit_lineage_matrix: pd.DataFrame,
    source_quality_matrix: pd.DataFrame,
    factor_event_exposure_lineage_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    type_matrix.to_csv(paths["type_matrix"], index=False)
    value_semantics_matrix.to_csv(paths["value_semantics_matrix"], index=False)
    pit_lineage_matrix.to_csv(paths["pit_lineage_matrix"], index=False)
    source_quality_matrix.to_csv(paths["source_quality_matrix"], index=False)
    factor_event_exposure_lineage_matrix.to_csv(paths["factor_event_exposure_lineage_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_factor_observation_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_factor_observation_limitations(result: FactorObservationSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Factor Observation Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic factor_observation rows for schema and governance review only.",
            "",
            "## Not Created",
            "",
            "- No real factor observations are created.",
            "- No production factor observation ingestion or production factor registry is created.",
            "- No production factor registry is created.",
            "- No active factor library is created.",
            "- No production event ingestion or active event library is created.",
            "- No production company exposure mapping is created.",
            "- No real raw document ingestion, source adapters, crawlers, connectors, or LLM extraction runtime is created.",
            "- No normalization, winsorization, or direction-adjustment runtime is created.",
            "- No replay evidence bundles, replay decisions, or forward labels are created.",
            "- No signal_score implementation or signal score input authorization is created.",
            "- No model training, active weights, active thresholds, stock_profile validation, or paper validation is created.",
            "- No buy-review eligibility, buy_review_allowed, or strategy performance validation is created.",
            "- No trading, broker behavior, orders, messages, or APIs are created.",
            "- Confidence fields are evidence/calculation confidence only, not return probability.",
            "- Raw values are not normalized model inputs, not a signal score, and not a model weight.",
            "",
            "## Current Result",
            "",
            f"- factor_observation_schema_fixture_id: {result.factor_observation_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- observation_count: {result.observation_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: FactorObservationSchemaFixtureResult,
    settings: FactorObservationSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "factor_observation_schema_fixture_id": result.factor_observation_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "factor_observation_schema_fixture_created": True,
        "factor_observation_rows_created": True,
        "observation_count": result.observation_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "conceptual_formula": "x_{i,j,t} = O_j(E_{<=t}, exposure_{i,<=t}, event_{<=t})",
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "factor_observation_id": "",
        "observation_version": "factor_observation_schema_fixture_v0.1",
        "observation_key": "",
        "schema_version": "factor_observation_schema_fixture_v0.1",
        "created_by_workflow": "factor-observation-schema-fixture",
        "created_at": "2026-06-27T00:00:00",
        "factor_id": "",
        "factor_definition_version": "factor_definition_schema_fixture_v0.1",
        "factor_name": "",
        "taxonomy_layer_id": "",
        "taxonomy_layer_name": "",
        "second_level": "",
        "observation_rule_ref": "",
        "factor_family": "",
        "factor_observation_type": "SYNTHETIC_FIXTURE",
        "entity_id": "",
        "symbol": "",
        "instrument_type": "SYNTHETIC_ENTITY",
        "exchange": "SYNTHETIC",
        "market": "CN_SYNTHETIC",
        "industry_id": "",
        "sector_id": "",
        "region_tags": "",
        "product_tags": "",
        "commodity_tags": "",
        "policy_tags": "",
        "company_exposure_id_refs": "",
        "event_structured_id_refs": "",
        "observation_date": "2024-04-02",
        "observation_time": "",
        "period_start": "",
        "period_end": "",
        "source_publish_time": "2024-04-02T16:00:00",
        "available_time": "2024-04-02T17:00:00",
        "as_of_date": "2024-04-03",
        "decision_time_eligible": True,
        "pit_valid": True,
        "stale_after": "2024-12-31T23:59:59",
        "timezone": "Asia/Shanghai",
        "lag_days": "0",
        "revision_id": "",
        "supersedes_observation_version_id": "",
        "source_id": "",
        "source_name": "Synthetic reviewed source",
        "source_tier": "SYNTHETIC_FIXTURE",
        "dataset_id": "",
        "document_id": "",
        "document_version_id": "",
        "source_hash": "",
        "content_hash": "",
        "metadata_hash": "",
        "raw_document_ref": "",
        "raw_dataset_ref": "",
        "url_or_file_ref": "synthetic://factor-observation-schema-fixture",
        "permission_class": "SYNTHETIC_FIXTURE_ONLY",
        "storage_policy": "manual_diagnostics_only",
        "parser_version": "synthetic_parser_v0.1",
        "extractor_version": "synthetic_extractor_v0.1",
        "calculation_version": "synthetic_calculation_v0.1",
        "extraction_method": "manual_synthetic_fixture",
        "calculation_method": "schema_fixture_manual_synthetic_calculation",
        "value_dtype": "MISSING",
        "raw_value": "",
        "value_unit": "",
        "value_scale": "",
        "categorical_value": "",
        "boolean_value": "",
        "ordinal_value": "",
        "missing_value_policy": "not_missing_unless_blocked",
        "imputation_status": "NOT_IMPUTED",
        "denominator_policy": "",
        "frequency": "SYNTHETIC_FIXTURE",
        "transform_status": "RAW_ONLY",
        "normalization_status": "NOT_ALLOWED_IN_FIXTURE",
        "winsorization_status": "NOT_ALLOWED_IN_FIXTURE",
        "direction_adjustment_status": "NOT_ALLOWED_IN_FIXTURE",
        "normalized_value": "not_applied",
        "winsorized_value": "not_applied",
        "direction_adjusted_value": "not_applied",
        "direction_rule_type": "UNKNOWN",
        "direction_for_entity": "UNKNOWN",
        "direction_rule_detail": "",
        "exposure_direction_context": "",
        "event_direction_context": "",
        "market_regime_context": "",
        "expected_horizon": "not_applicable",
        "risk_veto_flag": False,
        "hard_veto_reason": "",
        "trade_usage": "research_context",
        "observation_confidence": 0.5,
        "evidence_confidence": 0.5,
        "calculation_confidence": 0.5,
        "evidence_specificity": "SYNTHETIC_FIXTURE",
        "manual_review_required": True,
        "manual_review_status": "REVIEW_REQUIRED",
        "reviewer": "diagnostic_fixture",
        "reviewed_at": "",
        "quality_status": "REVIEW_REQUIRED",
        "validation_notes": "Synthetic/report-only factor observation context; confidence is not return probability, not a signal score, and not a model weight.",
        "validation_issue_count": 0,
        "compliance_class": "REPORT_ONLY_REVIEW_REQUIRED",
        "report_only": True,
        "diagnostic_only": True,
        "is_live_signal": False,
        "is_alpha_claim": False,
        "signal_score_implemented": False,
        "signal_score_input_authorized": False,
        "model_training_allowed": False,
        "active_weight_allowed": False,
        "active_threshold_allowed": False,
        "stock_profile_validation_allowed": False,
        "paper_validation_allowed": False,
        "real_buy_review_allowed": False,
        "buy_review_allowed": False,
        "strategy_performance_validated": False,
        "trading_allowed": False,
        "observation_status": "OBSERVED",
        "production_event_ingestion_created": False,
        "production_company_exposure_mapping_created": False,
    }
    row.update(values)
    observation_id = row["factor_observation_id"]
    if not row["observation_key"]:
        row["observation_key"] = f"{row['factor_id']}::{row['entity_id']}::{row['observation_date']}"
    row["source_id"] = row["source_id"] or f"SYNTH_FACTOR_SOURCE_{_short_hash(observation_id)}"
    if row["dataset_id"]:
        row["raw_dataset_ref"] = row["raw_dataset_ref"] or row["dataset_id"]
    if row["document_id"]:
        row["raw_document_ref"] = row["raw_document_ref"] or row["document_version_id"] or row["document_id"]
    row["source_hash"] = row["source_hash"] or f"sha256:{_hash_text('source:' + row['source_id'])}"
    row["content_hash"] = row["content_hash"] or f"sha256:{_hash_text('content:' + observation_id)}"
    row["metadata_hash"] = row["metadata_hash"] or f"sha256:{_hash_text('metadata:' + observation_id)}"
    row["revision_id"] = row["revision_id"] or f"REV-{_short_hash(observation_id)}"
    return row


def _assert_settings_safe(settings: FactorObservationSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Factor observation schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_METADATA_FALSE_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe factor observation fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_FACTOR_OBSERVATION_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Factor Observation Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only factor observation schema fixture. Keep the workflow synthetic and do not create real factor observations, production factor registry state, active factor libraries, production event ingestion, production company exposure mapping, replay evidence bundles, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, or trading permission.",
        ]
    )


def _field_group(field: str) -> str:
    groups = {
        "identity_version": {"factor_observation_id", "observation_version", "observation_key", "schema_version", "created_by_workflow", "created_at"},
        "factor_definition_lineage": {"factor_id", "factor_definition_version", "factor_name", "taxonomy_layer_id", "taxonomy_layer_name", "second_level", "observation_rule_ref", "factor_family", "factor_observation_type"},
        "entity_instrument_context": {"entity_id", "symbol", "instrument_type", "exchange", "market", "industry_id", "sector_id", "region_tags", "product_tags", "commodity_tags", "policy_tags", "company_exposure_id_refs", "event_structured_id_refs"},
        "timing_pit": {"observation_date", "observation_time", "period_start", "period_end", "source_publish_time", "available_time", "as_of_date", "decision_time_eligible", "pit_valid", "stale_after", "timezone", "lag_days", "revision_id", "supersedes_observation_version_id"},
        "source_evidence_lineage": {"source_id", "source_name", "source_tier", "dataset_id", "document_id", "document_version_id", "source_hash", "content_hash", "metadata_hash", "raw_document_ref", "raw_dataset_ref", "url_or_file_ref", "permission_class", "storage_policy", "parser_version", "extractor_version", "calculation_version", "extraction_method", "calculation_method"},
        "value_semantics": {"value_dtype", "raw_value", "value_unit", "value_scale", "categorical_value", "boolean_value", "ordinal_value", "missing_value_policy", "imputation_status", "denominator_policy", "frequency", "transform_status", "normalization_status", "winsorization_status", "direction_adjustment_status", "normalized_value", "winsorized_value", "direction_adjusted_value"},
        "direction_context": {"direction_rule_type", "direction_for_entity", "direction_rule_detail", "exposure_direction_context", "event_direction_context", "market_regime_context", "expected_horizon", "risk_veto_flag", "hard_veto_reason", "trade_usage"},
        "quality_review_confidence": {"observation_confidence", "evidence_confidence", "calculation_confidence", "evidence_specificity", "manual_review_required", "manual_review_status", "reviewer", "reviewed_at", "quality_status", "validation_notes", "validation_issue_count"},
    }
    for group, fields in groups.items():
        if field in fields:
            return group
    return "compliance_governance"


def _field_description(field: str) -> str:
    descriptions = {
        "factor_observation_id": "Stable synthetic factor observation identifier.",
        "factor_id": "Factor definition reference; fixture only.",
        "factor_definition_version": "Versioned factor definition lineage.",
        "available_time": "Earliest reviewed availability time; controls future replay eligibility.",
        "raw_value": "Raw observed value; not normalized, not a signal score, not a model input.",
        "observation_confidence": "Observation confidence only, not return probability.",
        "trade_usage": "Non-actionable research/governance usage category.",
        "report_only": "Must be true for this workflow.",
        "diagnostic_only": "Must be true for this workflow.",
    }
    return descriptions.get(field, "Factor observation schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "decision_time_eligible",
        "pit_valid",
        "risk_veto_flag",
        "manual_review_required",
        "report_only",
        "diagnostic_only",
        "is_live_signal",
        "is_alpha_claim",
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
        "production_event_ingestion_created",
        "production_company_exposure_mapping_created",
    }:
        return "boolean"
    if field in {"observation_confidence", "evidence_confidence", "calculation_confidence"}:
        return "float_0_to_1"
    if field in {"observation_time", "source_publish_time", "available_time", "stale_after", "created_at", "reviewed_at"}:
        return "timestamp"
    if field in {"observation_date", "period_start", "period_end", "as_of_date"}:
        return "date"
    return "string"


def _allowed_values(field: str) -> str:
    mapping = {
        "factor_observation_type": FACTOR_OBSERVATION_TYPES,
        "instrument_type": INSTRUMENT_TYPES,
        "value_dtype": VALUE_DTYPES,
        "frequency": FREQUENCIES,
        "source_tier": SOURCE_TIERS,
        "direction_rule_type": DIRECTION_RULE_TYPES,
        "direction_for_entity": DIRECTION_FOR_ENTITY,
        "transform_status": TRANSFORM_STATUSES,
        "normalization_status": NORMALIZATION_STATUSES,
        "winsorization_status": WINSORIZATION_STATUSES,
        "direction_adjustment_status": DIRECTION_ADJUSTMENT_STATUSES,
        "quality_status": QUALITY_STATUSES,
        "manual_review_status": MANUAL_REVIEW_STATUSES,
        "observation_status": OBSERVATION_STATUSES,
        "trade_usage": ALLOWED_TRADE_USAGE,
    }
    return "|".join(sorted(mapping.get(field, [])))


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_ts = pd.to_datetime(_text(first), errors="coerce")
    second_ts = pd.to_datetime(_text(second), errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _timestamp_to_date_order_ok(timestamp_value: Any, date_value: Any) -> bool:
    timestamp = pd.to_datetime(_text(timestamp_value), errors="coerce")
    date = pd.to_datetime(_text(date_value), errors="coerce")
    if pd.isna(timestamp) or pd.isna(date):
        return False
    return bool(timestamp.normalize() <= date.normalize())


def _date_lte_timestamp(date_value: Any, timestamp_value: Any) -> bool:
    date = pd.to_datetime(_text(date_value), errors="coerce")
    timestamp = pd.to_datetime(_text(timestamp_value), errors="coerce")
    if pd.isna(date) or pd.isna(timestamp):
        return False
    return bool(date.normalize() <= timestamp.normalize())


def _is_non_empty_string(value: Any) -> bool:
    return bool(_text(value))


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _short_hash(text: str) -> str:
    return _hash_text(text)[:10].upper()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()
