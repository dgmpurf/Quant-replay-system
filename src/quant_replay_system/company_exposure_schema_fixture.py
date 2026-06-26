"""Report-only company exposure schema fixture workflow.

This module writes tiny synthetic company-exposure rows for schema and
governance review only. Company exposure maps an entity to industry, product,
commodity, region, policy, style, risk, ETF holding, or index membership
context. It is not a production company exposure mapping, knowledge graph,
factor observation, event ingestion, signal, alpha claim, model input
authorization, stock profile validation, buy-review permission, performance
validation, or trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED = "COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED"

REQUIRED_COMPANY_EXPOSURE_FIELDS = [
    "company_exposure_id",
    "company_exposure_version",
    "entity_id",
    "symbol",
    "instrument_type",
    "entity_name",
    "exposure_type",
    "exposure_name",
    "exposure_key",
    "exposure_scope",
    "exposure_measure_type",
    "exposure_measure_value",
    "exposure_measure_unit",
    "exposure_strength_bucket",
    "direction_rule_type",
    "direction_for_factor_increase",
    "direction_rule_detail",
    "transmission_path",
    "time_horizon",
    "lag_policy",
    "factor_id_refs",
    "event_type_refs",
    "taxonomy_layer_ids",
    "industry_id",
    "sector_id",
    "product_tags",
    "commodity_tags",
    "region_tags",
    "policy_tags",
    "source_id",
    "document_version_id",
    "source_hash",
    "content_hash",
    "revision_id",
    "mapping_method",
    "mapping_version",
    "evidence_specificity",
    "manual_review_required",
    "manual_review_status",
    "reviewer",
    "reviewed_at",
    "quality_status",
    "mapping_confidence",
    "effective_from",
    "effective_to",
    "as_of_date",
    "available_time",
    "stale_after",
    "pit_valid",
    "decision_time_eligible",
    "supersedes_exposure_version_id",
    "is_proxy",
    "proxy_reason",
    "compliance_class",
    "trade_usage",
    "report_only",
    "diagnostic_only",
    "is_live_signal",
    "is_alpha_claim",
    "model_training_allowed",
    "active_weight_allowed",
    "active_threshold_allowed",
    "stock_profile_validation_allowed",
    "real_buy_review_allowed",
    "trading_allowed",
    "schema_version",
    "created_by_workflow",
]

INSTRUMENT_TYPES = {
    "STOCK",
    "ETF",
    "INDEX",
    "INDUSTRY_ENTITY",
    "SYNTHETIC_ENTITY",
}

EXPOSURE_TYPES = {
    "INDUSTRY",
    "SECTOR",
    "PRODUCT",
    "RAW_MATERIAL",
    "COMMODITY",
    "VALUE_CHAIN_ROLE",
    "REGION",
    "CUSTOMER",
    "SUPPLIER",
    "POLICY",
    "EXPORT",
    "IMPORT",
    "FX",
    "INTEREST_RATE",
    "STYLE",
    "MARKET_CAP",
    "OWNERSHIP",
    "RISK",
    "ETF_HOLDING",
    "INDEX_MEMBERSHIP",
    "TECHNOLOGY",
    "CAPACITY",
}

EXPOSURE_MEASURE_TYPES = {
    "CATEGORICAL",
    "NUMERIC_RATIO",
    "PERCENTAGE",
    "BOOLEAN",
    "TEXT_TAG",
    "UNKNOWN",
}

EXPOSURE_STRENGTH_BUCKETS = {
    "HIGH",
    "MEDIUM",
    "LOW",
    "UNKNOWN",
    "NOT_APPLICABLE",
}

MAPPING_METHODS = {
    "MANUAL_REVIEWED",
    "OFFICIAL_DISCLOSURE_DERIVED",
    "OFFICIAL_DATASET_DERIVED",
    "RAW_DOCUMENT_DERIVED",
    "ETF_HOLDING_DERIVED",
    "INDEX_MEMBERSHIP_DERIVED",
    "RULE_BASED",
    "PROXY_ESTIMATE",
    "BLOCKED_UNVERIFIED",
}

EVIDENCE_SPECIFICITY = {
    "DIRECT_COMPANY_DISCLOSURE",
    "OFFICIAL_PUBLIC_DATA",
    "REVIEWED_LOCAL_DATA",
    "DERIVED_FROM_PUBLIC_HOLDINGS",
    "INDUSTRY_PROXY",
    "INFERRED_PROXY",
    "UNVERIFIED",
    "BLOCKED",
}

DIRECTION_RULE_TYPES = {
    "DIRECT",
    "INVERSE",
    "MIXED_BY_EXPOSURE",
    "MIXED_BY_REGIME",
    "CONDITIONAL",
    "RISK_VETO_ONLY",
    "UNKNOWN",
}

DIRECTION_FOR_FACTOR_INCREASE = {
    "POSITIVE",
    "NEGATIVE",
    "NEUTRAL",
    "MIXED",
    "CONDITIONAL",
    "RISK_VETO_ONLY",
    "UNKNOWN",
}

ALLOWED_TRADE_USAGE = {
    "research_context",
    "event_mapping",
    "factor_direction_support",
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
}

QUALITY_STATUSES = {
    "PASS",
    "WARN",
    "REVIEW_REQUIRED",
    "FAIL",
    "BLOCKED",
    "DIAGNOSTIC_ONLY",
}

MANUAL_REVIEW_STATUSES = {
    "NOT_REVIEWED",
    "REVIEW_REQUIRED",
    "REVIEWED_PASS",
    "REVIEWED_WARN",
    "REVIEWED_FAIL",
    "BLOCKED",
    "DIAGNOSTIC_ONLY",
}

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "production_company_exposure_created",
    "active_company_exposure_mapping_created",
    "company_knowledge_graph_created",
    "real_holdings_ingested",
    "supplier_customer_graph_created",
    "factor_observations_created",
    "event_ingestion_created",
    "replay_evidence_bundle_created",
    "signal_score_implemented",
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
class CompanyExposureSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/company_exposure_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    production_company_exposure_created: bool = False
    active_company_exposure_mapping_created: bool = False
    company_knowledge_graph_created: bool = False
    real_holdings_ingested: bool = False
    supplier_customer_graph_created: bool = False
    factor_observations_created: bool = False
    event_ingestion_created: bool = False
    replay_evidence_bundle_created: bool = False
    signal_score_implemented: bool = False
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
class CompanyExposureSchemaFixtureResult:
    company_exposure_schema_fixture_id: str
    status: str
    workflow_stage: str
    exposure_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_company_exposure_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: CompanyExposureSchemaFixtureSettings | None = None,
) -> CompanyExposureSchemaFixtureResult:
    resolved_settings = settings or CompanyExposureSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = CompanyExposureSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_company_exposure_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_company_exposure_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_company_exposure_schema_fields()
    type_matrix = build_company_exposure_type_matrix(fixture_rows)
    direction_matrix = build_company_exposure_direction_matrix(fixture_rows)
    pit_lineage_matrix = build_company_exposure_pit_lineage_matrix(fixture_rows)
    validation_summary = validate_company_exposure_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = CompanyExposureSchemaFixtureResult(
        company_exposure_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=COMPANY_EXPOSURE_SCHEMA_FIXTURE_CREATED,
        exposure_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_company_exposure_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            type_matrix=type_matrix,
            direction_matrix=direction_matrix,
            pit_lineage_matrix=pit_lineage_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_company_exposure_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            company_exposure_id="SYNTH_STEEL_IRON_ORE_COST_BUYER",
            entity_id="SYNTH_STEEL_BUYER_ENTITY",
            symbol="000001",
            instrument_type="STOCK",
            entity_name="Synthetic steel input-cost buyer",
            exposure_type="RAW_MATERIAL",
            exposure_name="Iron ore input cost exposure",
            exposure_key="RAW_MATERIAL:IRON_ORE:COST_BUYER",
            exposure_scope="company_input_cost",
            exposure_measure_type="TEXT_TAG",
            exposure_measure_value="iron_ore_cost_buyer",
            exposure_strength_bucket="HIGH",
            direction_rule_type="INVERSE",
            direction_for_factor_increase="NEGATIVE",
            direction_rule_detail=(
                "Iron ore price increases can be negative for input-cost steelmakers when raw-material "
                "cost pass-through is limited."
            ),
            transmission_path="raw material price increase -> cost pressure -> margin context",
            time_horizon="quarterly",
            factor_id_refs="L2_IRON_ORE_PRICE_CHANGE_SAMPLE",
            taxonomy_layer_ids="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            industry_id="SYNTH_STEEL",
            sector_id="SYNTH_MATERIALS",
            commodity_tags="iron_ore",
            mapping_method="OFFICIAL_DISCLOSURE_DERIVED",
            evidence_specificity="DIRECT_COMPANY_DISCLOSURE",
            mapping_confidence=0.8,
            trade_usage="factor_direction_support",
        ),
        _row(
            company_exposure_id="SYNTH_IRON_ORE_RESOURCE_PRODUCER",
            entity_id="SYNTH_IRON_ORE_PRODUCER_ENTITY",
            symbol="000002",
            instrument_type="STOCK",
            entity_name="Synthetic iron ore resource producer",
            exposure_type="COMMODITY",
            exposure_name="Iron ore resource revenue exposure",
            exposure_key="COMMODITY:IRON_ORE:RESOURCE_PRODUCER",
            exposure_scope="company_revenue_driver",
            exposure_measure_type="TEXT_TAG",
            exposure_measure_value="iron_ore_resource_producer",
            exposure_strength_bucket="HIGH",
            direction_rule_type="DIRECT",
            direction_for_factor_increase="POSITIVE",
            direction_rule_detail=(
                "The same iron-ore factor can be positive for resource producer exposure when revenue "
                "is linked to iron ore prices."
            ),
            transmission_path="commodity price increase -> resource revenue context",
            time_horizon="quarterly",
            factor_id_refs="L2_IRON_ORE_PRICE_CHANGE_SAMPLE",
            taxonomy_layer_ids="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            industry_id="SYNTH_MINING",
            sector_id="SYNTH_MATERIALS",
            commodity_tags="iron_ore",
            mapping_method="OFFICIAL_DISCLOSURE_DERIVED",
            evidence_specificity="DIRECT_COMPANY_DISCLOSURE",
            mapping_confidence=0.8,
            trade_usage="factor_direction_support",
        ),
        _row(
            company_exposure_id="SYNTH_EXPORTER_CNY_DEPRECIATION",
            entity_id="SYNTH_EXPORTER_ENTITY",
            symbol="000003",
            instrument_type="STOCK",
            entity_name="Synthetic export-oriented company",
            exposure_type="EXPORT",
            exposure_name="Export revenue and CNY depreciation context",
            exposure_key="FX:CNY_DEPRECIATION:EXPORTER",
            exposure_scope="company_revenue_context",
            exposure_measure_type="CATEGORICAL",
            exposure_measure_value="export_oriented",
            exposure_strength_bucket="MEDIUM",
            direction_rule_type="CONDITIONAL",
            direction_for_factor_increase="CONDITIONAL",
            direction_rule_detail=(
                "CNY depreciation can help export revenue only under assumptions about foreign-currency "
                "sales, costs, hedging, and demand; it does not imply universal benefit."
            ),
            transmission_path="FX move -> export revenue translation context",
            time_horizon="monthly_or_quarterly",
            factor_id_refs="L3_FX_CNY_DEPRECIATION_SAMPLE",
            taxonomy_layer_ids="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            industry_id="SYNTH_EXPORT_MANUFACTURING",
            sector_id="SYNTH_INDUSTRIALS",
            region_tags="overseas_revenue",
            policy_tags="fx_context",
            mapping_method="MANUAL_REVIEWED",
            evidence_specificity="REVIEWED_LOCAL_DATA",
            mapping_confidence=0.65,
            trade_usage="research_context",
        ),
        _row(
            company_exposure_id="SYNTH_IMPORTER_CNY_DEPRECIATION",
            entity_id="SYNTH_IMPORTER_ENTITY",
            symbol="000004",
            instrument_type="STOCK",
            entity_name="Synthetic import-input-cost company",
            exposure_type="IMPORT",
            exposure_name="Import cost and CNY depreciation context",
            exposure_key="FX:CNY_DEPRECIATION:IMPORTER",
            exposure_scope="company_input_cost",
            exposure_measure_type="CATEGORICAL",
            exposure_measure_value="import_input_cost",
            exposure_strength_bucket="MEDIUM",
            direction_rule_type="CONDITIONAL",
            direction_for_factor_increase="NEGATIVE",
            direction_rule_detail=(
                "CNY depreciation can be negative for import-input-cost companies when imported inputs "
                "are material and not hedged; it does not imply universal harm."
            ),
            transmission_path="FX move -> imported input cost context",
            time_horizon="monthly_or_quarterly",
            factor_id_refs="L3_FX_CNY_DEPRECIATION_SAMPLE",
            taxonomy_layer_ids="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            industry_id="SYNTH_IMPORT_DEPENDENT",
            sector_id="SYNTH_CONSUMER",
            region_tags="import_cost",
            policy_tags="fx_context",
            mapping_method="MANUAL_REVIEWED",
            evidence_specificity="REVIEWED_LOCAL_DATA",
            mapping_confidence=0.65,
            trade_usage="research_context",
        ),
        _row(
            company_exposure_id="SYNTH_REGIONAL_CAPACITY_RESTRICTION",
            entity_id="SYNTH_REGIONAL_CAPACITY_ENTITY",
            symbol="000005",
            instrument_type="STOCK",
            entity_name="Synthetic regional capacity-sensitive company",
            exposure_type="CAPACITY",
            exposure_name="Regional capacity restriction context",
            exposure_key="POLICY:REGIONAL_CAPACITY_RESTRICTION",
            exposure_scope="plant_region_context",
            exposure_measure_type="BOOLEAN",
            exposure_measure_value="true",
            exposure_strength_bucket="MEDIUM",
            direction_rule_type="CONDITIONAL",
            direction_for_factor_increase="CONDITIONAL",
            direction_rule_detail=(
                "Regional capacity restriction affects directly restricted plants differently from "
                "unaffected peers; direction depends on plant location and competitor exposure."
            ),
            transmission_path="regional policy -> supply restriction context",
            time_horizon="event_window",
            factor_id_refs="L3_POLICY_CAPACITY_RESTRICTION_SAMPLE",
            event_type_refs="POLICY_CAPACITY_RESTRICTION",
            taxonomy_layer_ids="L3_MACRO_LIQUIDITY_POLICY_GLOBAL,L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            industry_id="SYNTH_HEAVY_INDUSTRY",
            sector_id="SYNTH_INDUSTRIALS",
            region_tags="synthetic_region_a",
            policy_tags="capacity_restriction",
            mapping_method="RAW_DOCUMENT_DERIVED",
            evidence_specificity="OFFICIAL_PUBLIC_DATA",
            mapping_confidence=0.7,
            trade_usage="event_mapping",
        ),
        _row(
            company_exposure_id="SYNTH_PRODUCT_REVENUE_EXPOSURE",
            entity_id="SYNTH_PRODUCT_REVENUE_ENTITY",
            symbol="000006",
            instrument_type="STOCK",
            entity_name="Synthetic product revenue segment company",
            exposure_type="PRODUCT",
            exposure_name="Product revenue segment exposure",
            exposure_key="PRODUCT:BATTERY_COMPONENT:REVENUE_SEGMENT",
            exposure_scope="company_revenue_segment",
            exposure_measure_type="PERCENTAGE",
            exposure_measure_value="35",
            exposure_measure_unit="percent_of_revenue_bucketed",
            exposure_strength_bucket="MEDIUM",
            direction_rule_type="MIXED_BY_EXPOSURE",
            direction_for_factor_increase="MIXED",
            direction_rule_detail=(
                "Product revenue exposure is descriptive context only; direction depends on product "
                "demand, margin, capacity, and customer concentration."
            ),
            transmission_path="product demand factor -> revenue segment context",
            time_horizon="quarterly_or_annual",
            factor_id_refs="L1_PRODUCT_REVENUE_EXPOSURE_SAMPLE",
            taxonomy_layer_ids="L1_OPERATIONS_COMPANY_EVENTS",
            industry_id="SYNTH_ADVANCED_MANUFACTURING",
            sector_id="SYNTH_INDUSTRIALS",
            product_tags="battery_component",
            mapping_method="OFFICIAL_DISCLOSURE_DERIVED",
            evidence_specificity="DIRECT_COMPANY_DISCLOSURE",
            mapping_confidence=0.75,
            trade_usage="research_context",
        ),
        _row(
            company_exposure_id="SYNTH_ETF_INDEX_HOLDING_EXPOSURE",
            entity_id="SYNTH_ETF_ENTITY",
            symbol="159915",
            instrument_type="ETF",
            entity_name="Synthetic ETF/index holding exposure",
            exposure_type="ETF_HOLDING",
            exposure_name="ETF/index holding-derived context",
            exposure_key="ETF_HOLDING:SYNTH_INDEX:TECH_WEIGHT",
            exposure_scope="fund_holding_context",
            exposure_measure_type="PERCENTAGE",
            exposure_measure_value="20",
            exposure_measure_unit="synthetic_percent_bucket",
            exposure_strength_bucket="LOW",
            direction_rule_type="MIXED_BY_EXPOSURE",
            direction_for_factor_increase="MIXED",
            direction_rule_detail=(
                "ETF/index holding exposure is synthetic holding-derived context only and does not "
                "claim real or current holdings ingestion."
            ),
            transmission_path="constituent exposure -> ETF/index context",
            time_horizon="as_of_holding_snapshot",
            factor_id_refs="L4_INDEX_MEMBERSHIP_CONTEXT_SAMPLE",
            taxonomy_layer_ids="L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND",
            industry_id="SYNTH_INDEX",
            sector_id="SYNTH_MULTI_SECTOR",
            product_tags="etf_index_holding_context",
            mapping_method="ETF_HOLDING_DERIVED",
            evidence_specificity="DERIVED_FROM_PUBLIC_HOLDINGS",
            mapping_confidence=0.55,
            trade_usage="research_context",
        ),
        _row(
            company_exposure_id="SYNTH_SOE_DIVIDEND_STYLE_EXPOSURE",
            entity_id="SYNTH_SOE_STYLE_ENTITY",
            symbol="000007",
            instrument_type="STOCK",
            entity_name="Synthetic SOE dividend style entity",
            exposure_type="STYLE",
            exposure_name="SOE dividend style context",
            exposure_key="STYLE:SOE_DIVIDEND",
            exposure_scope="style_context",
            exposure_measure_type="TEXT_TAG",
            exposure_measure_value="soe_dividend_style",
            exposure_strength_bucket="MEDIUM",
            direction_rule_type="CONDITIONAL",
            direction_for_factor_increase="CONDITIONAL",
            direction_rule_detail=(
                "SOE dividend style exposure remains descriptive and does not imply factor "
                "profitability, paper approval, buy-review, or trading permission; mapping "
                "confidence is not a model weight and not return probability."
            ),
            transmission_path="ownership/style context -> valuation and income preference context",
            time_horizon="annual_or_policy_cycle",
            factor_id_refs="L7_STYLE_DIVIDEND_CONTEXT_SAMPLE",
            taxonomy_layer_ids="L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION",
            industry_id="SYNTH_UTILITIES",
            sector_id="SYNTH_DEFENSIVE",
            policy_tags="soe_governance",
            mapping_method="RULE_BASED",
            evidence_specificity="INDUSTRY_PROXY",
            mapping_confidence=0.5,
            is_proxy=True,
            proxy_reason="Synthetic style proxy requires future direct reviewed evidence before downstream use.",
            trade_usage="observe_only",
        ),
        _row(
            company_exposure_id="SYNTH_ST_STATUS_RISK_VETO_EXPOSURE",
            entity_id="SYNTH_ST_RISK_ENTITY",
            symbol="000008",
            instrument_type="STOCK",
            entity_name="Synthetic ST status risk entity",
            exposure_type="RISK",
            exposure_name="ST status risk veto exposure",
            exposure_key="RISK:ST_STATUS:VETO",
            exposure_scope="risk_veto_context",
            exposure_measure_type="BOOLEAN",
            exposure_measure_value="true",
            exposure_strength_bucket="NOT_APPLICABLE",
            direction_rule_type="RISK_VETO_ONLY",
            direction_for_factor_increase="RISK_VETO_ONLY",
            direction_rule_detail=(
                "Risk veto exposure can block or require review but cannot create positive alpha, "
                "buy-review permission, or trading permission."
            ),
            transmission_path="risk status -> review blocker context",
            time_horizon="daily",
            factor_id_refs="L8_ST_STATUS_RISK_VETO_SAMPLE",
            event_type_refs="ST_RISK_WARNING",
            taxonomy_layer_ids="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            industry_id="SYNTH_RISK",
            sector_id="SYNTH_RISK",
            mapping_method="OFFICIAL_DATASET_DERIVED",
            evidence_specificity="OFFICIAL_PUBLIC_DATA",
            mapping_confidence=0.7,
            trade_usage="risk_filter",
        ),
        _row(
            company_exposure_id="SYNTH_BLOCKED_PRIVATE_SUPPLIER_RELATIONSHIP",
            entity_id="SYNTH_BLOCKED_SUPPLIER_ENTITY",
            symbol="000009",
            instrument_type="STOCK",
            entity_name="Synthetic blocked private supplier relationship",
            exposure_type="SUPPLIER",
            exposure_name="Blocked private supplier relationship",
            exposure_key="SUPPLIER:PRIVATE_UNVERIFIED:BLOCKED",
            exposure_scope="blocked_relationship_context",
            exposure_measure_type="UNKNOWN",
            exposure_measure_value="UNKNOWN",
            exposure_strength_bucket="UNKNOWN",
            direction_rule_type="UNKNOWN",
            direction_for_factor_increase="UNKNOWN",
            direction_rule_detail=(
                "Unverified private supplier relationship is blocked and cannot be PIT-valid, "
                "decision-time eligible, model input, buy-review evidence, or trading input."
            ),
            transmission_path="blocked private relationship -> no downstream use",
            time_horizon="not_applicable",
            factor_id_refs="",
            event_type_refs="PRIVATE_SUPPLIER_RUMOR",
            taxonomy_layer_ids="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            industry_id="SYNTH_BLOCKED",
            sector_id="SYNTH_BLOCKED",
            mapping_method="BLOCKED_UNVERIFIED",
            evidence_specificity="BLOCKED",
            manual_review_status="BLOCKED",
            quality_status="BLOCKED",
            mapping_confidence=0.0,
            pit_valid=False,
            decision_time_eligible=False,
            compliance_class="BLOCKED_PRIVATE_UNVERIFIED",
            trade_usage="no_trade",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_COMPANY_EXPOSURE_FIELDS)


def build_company_exposure_schema_fields() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "required": True,
                "hard_gate": field
                in {
                    "company_exposure_id",
                    "company_exposure_version",
                    "entity_id",
                    "symbol",
                    "instrument_type",
                    "exposure_type",
                    "direction_rule_type",
                    "direction_for_factor_increase",
                    "source_id",
                    "document_version_id",
                    "revision_id",
                    "mapping_method",
                    "mapping_version",
                    "available_time",
                    "quality_status",
                    "manual_review_status",
                    "report_only",
                    "diagnostic_only",
                },
                "data_type_hint": _data_type_hint(field),
                "description": _field_description(field),
            }
            for field in REQUIRED_COMPANY_EXPOSURE_FIELDS
        ]
    )


def build_company_exposure_type_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "company_exposure_id": row["company_exposure_id"],
                "instrument_type": row["instrument_type"],
                "exposure_type": row["exposure_type"],
                "exposure_measure_type": row["exposure_measure_type"],
                "exposure_strength_bucket": row["exposure_strength_bucket"],
                "mapping_method": row["mapping_method"],
                "evidence_specificity": row["evidence_specificity"],
                "production_mapping_created": False,
                "real_holdings_ingested": False,
                "notes": "Synthetic/report-only schema fixture row; not production company exposure.",
            }
            for row in fixture_rows.to_dict(orient="records")
        ]
    )


def build_company_exposure_direction_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "company_exposure_id": row["company_exposure_id"],
                "factor_id_refs": row["factor_id_refs"],
                "direction_rule_type": row["direction_rule_type"],
                "direction_for_factor_increase": row["direction_for_factor_increase"],
                "direction_rule_detail": row["direction_rule_detail"],
                "trade_usage": row["trade_usage"],
                "direction_is_model_weight": False,
                "direction_is_buy_sell_rule": False,
                "notes": "Direction is exposure-specific context only, not active signal or trading rule.",
            }
            for row in fixture_rows.to_dict(orient="records")
        ]
    )


def build_company_exposure_pit_lineage_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "company_exposure_id": row["company_exposure_id"],
                "source_id": row["source_id"],
                "document_version_id": row["document_version_id"],
                "source_hash": row["source_hash"],
                "content_hash": row["content_hash"],
                "revision_id": row["revision_id"],
                "mapping_version": row["mapping_version"],
                "available_time": row["available_time"],
                "as_of_date": row["as_of_date"],
                "pit_valid": _bool(row["pit_valid"]),
                "decision_time_eligible": _bool(row["decision_time_eligible"]),
                "lineage_required_before_downstream_use": True,
                "available_time_gate": "future replay gate must require available_time <= replay_decision_time",
            }
            for row in fixture_rows.to_dict(orient="records")
        ]
    )


def validate_company_exposure_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: CompanyExposureSchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    row_text = " ".join(fixture_rows.fillna("").astype(str).agg(" ".join, axis=1))
    lower_text = row_text.lower()
    rows_by_id = fixture_rows.set_index("company_exposure_id", drop=False)
    buyer = rows_by_id.loc["SYNTH_STEEL_IRON_ORE_COST_BUYER"]
    producer = rows_by_id.loc["SYNTH_IRON_ORE_RESOURCE_PRODUCER"]
    blocked = rows_by_id.loc["SYNTH_BLOCKED_PRIVATE_SUPPLIER_RELATIONSHIP"]
    etf = rows_by_id.loc["SYNTH_ETF_INDEX_HOLDING_EXPOSURE"]
    risk = rows_by_id.loc["SYNTH_ST_STATUS_RISK_VETO_EXPOSURE"]
    evidence_backed = fixture_rows[fixture_rows["evidence_specificity"] != "BLOCKED"]
    conditional = fixture_rows[
        fixture_rows["direction_for_factor_increase"].isin(["CONDITIONAL", "MIXED"])
        | fixture_rows["direction_rule_type"].isin(["CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"])
    ]
    checks = [
        ("required_fields_present", set(REQUIRED_COMPANY_EXPOSURE_FIELDS).issubset(set(fixture_rows.columns))),
        ("exactly_10_synthetic_rows", len(fixture_rows) == 10),
        ("company_exposure_id_unique", fixture_rows["company_exposure_id"].is_unique),
        ("company_exposure_version_present", fixture_rows["company_exposure_version"].map(_is_non_empty_string).all()),
        ("entity_id_and_symbol_string_like", fixture_rows["entity_id"].map(_is_non_empty_string).all()),
        ("instrument_type_valid", fixture_rows["instrument_type"].isin(INSTRUMENT_TYPES).all()),
        ("exposure_type_valid", fixture_rows["exposure_type"].isin(EXPOSURE_TYPES).all()),
        ("exposure_measure_type_valid", fixture_rows["exposure_measure_type"].isin(EXPOSURE_MEASURE_TYPES).all()),
        ("mapping_method_valid", fixture_rows["mapping_method"].isin(MAPPING_METHODS).all()),
        ("direction_rule_type_valid", fixture_rows["direction_rule_type"].isin(DIRECTION_RULE_TYPES).all()),
        ("direction_for_factor_increase_valid", fixture_rows["direction_for_factor_increase"].isin(DIRECTION_FOR_FACTOR_INCREASE).all()),
        ("mixed_conditional_direction_detail_present", conditional["direction_rule_detail"].map(_is_non_empty_string).all()),
        (
            "iron_ore_factor_opposite_directions",
            buyer["factor_id_refs"] == producer["factor_id_refs"]
            and buyer["direction_for_factor_increase"] == "NEGATIVE"
            and producer["direction_for_factor_increase"] == "POSITIVE",
        ),
        (
            "risk_veto_not_positive_alpha",
            risk["direction_for_factor_increase"] == "RISK_VETO_ONLY"
            and "positive alpha" in risk["direction_rule_detail"].lower()
            and risk["trade_usage"] in {"risk_filter", "no_trade"},
        ),
        (
            "blocked_row_no_trade_not_pit_valid",
            blocked["mapping_method"] == "BLOCKED_UNVERIFIED"
            and blocked["trade_usage"] == "no_trade"
            and not _bool(blocked["pit_valid"])
            and not _bool(blocked["decision_time_eligible"]),
        ),
        (
            "etf_row_no_real_holdings_claim",
            etf["instrument_type"] == "ETF"
            and "does not claim real or current holdings ingestion" in etf["direction_rule_detail"],
        ),
        ("source_id_present", fixture_rows["source_id"].map(_is_non_empty_string).all()),
        ("document_version_id_present_for_evidence_backed", evidence_backed["document_version_id"].map(_is_non_empty_string).all()),
        (
            "source_hash_or_content_hash_present",
            fixture_rows.apply(lambda row: bool(_text(row["source_hash"])) or bool(_text(row["content_hash"])), axis=1).all(),
        ),
        ("revision_id_present", fixture_rows["revision_id"].map(_is_non_empty_string).all()),
        ("mapping_version_present", fixture_rows["mapping_version"].map(_is_non_empty_string).all()),
        ("available_time_present", fixture_rows["available_time"].map(_is_non_empty_string).all()),
        (
            "effective_from_before_effective_to",
            fixture_rows.apply(lambda row: _date_order_ok(row["effective_from"], row["effective_to"]), axis=1).all(),
        ),
        (
            "available_time_before_as_of_date",
            fixture_rows.apply(lambda row: _timestamp_to_date_order_ok(row["available_time"], row["as_of_date"]), axis=1).all(),
        ),
        (
            "stale_after_not_before_available_time",
            fixture_rows.apply(lambda row: _timestamp_order_ok(row["available_time"], row["stale_after"]), axis=1).all(),
        ),
        ("quality_status_present_valid", fixture_rows["quality_status"].isin(QUALITY_STATUSES).all()),
        ("manual_review_status_present_valid", fixture_rows["manual_review_status"].isin(MANUAL_REVIEW_STATUSES).all()),
        ("mapping_confidence_bounded", fixture_rows["mapping_confidence"].astype(float).between(0, 1).all()),
        ("mapping_confidence_not_return_probability", "not return probability" in lower_text),
        (
            "proxy_reason_required",
            fixture_rows[fixture_rows["is_proxy"].map(_bool)]["proxy_reason"].map(_is_non_empty_string).all(),
        ),
        ("supersedes_exposure_version_id_explicit", "supersedes_exposure_version_id" in fixture_rows.columns),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("is_live_signal_false", fixture_rows["is_live_signal"].map(lambda value: not _bool(value)).all()),
        ("is_alpha_claim_false", fixture_rows["is_alpha_claim"].map(lambda value: not _bool(value)).all()),
        ("model_training_allowed_false", fixture_rows["model_training_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_weight_allowed_false", fixture_rows["active_weight_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_threshold_allowed_false", fixture_rows["active_threshold_allowed"].map(lambda value: not _bool(value)).all()),
        (
            "stock_profile_validation_allowed_false",
            fixture_rows["stock_profile_validation_allowed"].map(lambda value: not _bool(value)).all(),
        ),
        ("real_buy_review_allowed_false", fixture_rows["real_buy_review_allowed"].map(lambda value: not _bool(value)).all()),
        ("trading_allowed_false", fixture_rows["trading_allowed"].map(lambda value: not _bool(value)).all()),
        (
            "no_forbidden_trade_usage",
            fixture_rows["trade_usage"].isin(ALLOWED_TRADE_USAGE).all()
            and not fixture_rows["trade_usage"].isin(FORBIDDEN_TRADE_USAGE).any(),
        ),
        ("no_token_or_secret_values", not _contains_secret_like(lower_text)),
        ("no_production_company_exposure_mapping", not settings.production_company_exposure_created),
        ("no_company_knowledge_graph", not settings.company_knowledge_graph_created),
        ("no_real_holdings_ingestion", not settings.real_holdings_ingested),
        ("no_supplier_customer_production_graph", not settings.supplier_customer_graph_created),
        ("no_factor_observations", not settings.factor_observations_created),
        ("no_event_ingestion", not settings.event_ingestion_created),
        ("no_replay_evidence_bundle", not settings.replay_evidence_bundle_created),
        ("no_signal_score", not settings.signal_score_implemented),
        ("no_model_training_weights_thresholds", not settings.model_training_performed and not settings.active_weights_created and not settings.active_thresholds_created),
        ("no_stock_profile_paper_validation", not settings.stock_profile_validation_created and not settings.paper_validation_created),
        ("no_buy_review_performance_trading", not settings.buy_review_allowed and not settings.strategy_performance_validated and not settings.trading_allowed),
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


def resolve_company_exposure_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "company_exposure_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "company_exposure_schema_fields.csv",
        "fixture_rows": artifact_dir / "company_exposure_fixture_rows.csv",
        "type_matrix": artifact_dir / "company_exposure_type_matrix.csv",
        "direction_matrix": artifact_dir / "company_exposure_direction_matrix.csv",
        "pit_lineage_matrix": artifact_dir / "company_exposure_pit_lineage_matrix.csv",
        "validation_summary": artifact_dir / "company_exposure_validation_summary.csv",
        "limitations": artifact_dir / "company_exposure_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_company_exposure_schema_fixture_artifacts(
    *,
    result: CompanyExposureSchemaFixtureResult,
    settings: CompanyExposureSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    type_matrix: pd.DataFrame,
    direction_matrix: pd.DataFrame,
    pit_lineage_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    type_matrix.to_csv(paths["type_matrix"], index=False)
    direction_matrix.to_csv(paths["direction_matrix"], index=False)
    pit_lineage_matrix.to_csv(paths["pit_lineage_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_company_exposure_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_company_exposure_limitations(result: CompanyExposureSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Company Exposure Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic company_exposure rows for schema and governance review only.",
            "",
            "## Not Created",
            "",
            "- No production company exposure mapping is created.",
            "- No company knowledge graph or supplier/customer production graph is created.",
            "- No real ETF holdings are ingested.",
            "- No factor observations, event ingestion, replay evidence bundles, signal_score implementation, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, broker behavior, orders, messages, APIs, or trading are created.",
            "- Exposure strength and mapping confidence are evidence confidence only, not a model weight and not return probability.",
            "",
            "## Current Result",
            "",
            f"- company_exposure_schema_fixture_id: {result.company_exposure_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- exposure_count: {result.exposure_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: CompanyExposureSchemaFixtureResult,
    settings: CompanyExposureSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "company_exposure_schema_fixture_id": result.company_exposure_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "company_exposure_schema_fixture_created": True,
        "company_exposure_rows_created": True,
        "exposure_count": result.exposure_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    row = {
        "company_exposure_id": "",
        "company_exposure_version": "company_exposure_schema_fixture_v0.1",
        "entity_id": "",
        "symbol": "",
        "instrument_type": "STOCK",
        "entity_name": "",
        "exposure_type": "INDUSTRY",
        "exposure_name": "",
        "exposure_key": "",
        "exposure_scope": "",
        "exposure_measure_type": "TEXT_TAG",
        "exposure_measure_value": "",
        "exposure_measure_unit": "",
        "exposure_strength_bucket": "UNKNOWN",
        "direction_rule_type": "UNKNOWN",
        "direction_for_factor_increase": "UNKNOWN",
        "direction_rule_detail": "",
        "transmission_path": "",
        "time_horizon": "",
        "lag_policy": "explicit lag review required before downstream use",
        "factor_id_refs": "",
        "event_type_refs": "",
        "taxonomy_layer_ids": "",
        "industry_id": "",
        "sector_id": "",
        "product_tags": "",
        "commodity_tags": "",
        "region_tags": "",
        "policy_tags": "",
        "source_id": "",
        "document_version_id": "",
        "source_hash": "",
        "content_hash": "",
        "revision_id": "",
        "mapping_method": "MANUAL_REVIEWED",
        "mapping_version": "mapping_v0.1",
        "evidence_specificity": "REVIEWED_LOCAL_DATA",
        "manual_review_required": True,
        "manual_review_status": "REVIEW_REQUIRED",
        "reviewer": "diagnostic_fixture",
        "reviewed_at": "",
        "quality_status": "REVIEW_REQUIRED",
        "mapping_confidence": 0.5,
        "effective_from": "2024-01-01",
        "effective_to": "2024-12-31",
        "as_of_date": "2024-04-02",
        "available_time": "2024-04-01T17:00:00",
        "stale_after": "2025-01-31T23:59:59",
        "pit_valid": True,
        "decision_time_eligible": True,
        "supersedes_exposure_version_id": "",
        "is_proxy": False,
        "proxy_reason": "",
        "compliance_class": "REPORT_ONLY_REVIEW_REQUIRED",
        "trade_usage": "research_context",
        "report_only": True,
        "diagnostic_only": True,
        "is_live_signal": False,
        "is_alpha_claim": False,
        "model_training_allowed": False,
        "active_weight_allowed": False,
        "active_threshold_allowed": False,
        "stock_profile_validation_allowed": False,
        "real_buy_review_allowed": False,
        "trading_allowed": False,
        "schema_version": "company_exposure_schema_fixture_v0.1",
        "created_by_workflow": "company-exposure-schema-fixture",
    }
    row.update(values)
    exposure_id = row["company_exposure_id"]
    row["source_id"] = row["source_id"] or f"SYNTH_SOURCE_{_short_hash(exposure_id)}"
    row["document_version_id"] = row["document_version_id"] or f"{exposure_id}::doc_v0"
    row["source_hash"] = row["source_hash"] or f"sha256:{_hash_text('source:' + row['source_id'])}"
    row["content_hash"] = row["content_hash"] or f"sha256:{_hash_text('content:' + exposure_id)}"
    row["revision_id"] = row["revision_id"] or f"REV-{_short_hash(exposure_id)}"
    return row


def _assert_settings_safe(settings: CompanyExposureSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Company exposure schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_METADATA_FALSE_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe company exposure fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_COMPANY_EXPOSURE_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Company Exposure Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only company exposure schema fixture. Keep the workflow synthetic and do not create production company exposure mappings, company knowledge graph state, real holdings ingestion, supplier/customer production graphs, factor observations, event ingestion, replay evidence bundles, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, or trading permission.",
        ]
    )


def _field_description(field: str) -> str:
    descriptions = {
        "company_exposure_id": "Stable synthetic company exposure mapping identifier.",
        "company_exposure_version": "Version of the exposure mapping row.",
        "entity_id": "Stable entity identifier; string-preserved.",
        "symbol": "Instrument symbol; string-preserved.",
        "exposure_type": "Governed exposure category.",
        "direction_rule_detail": "Human-readable exposure-specific direction rule.",
        "source_id": "Source registry reference; does not grant production permission by itself.",
        "document_version_id": "Raw document store reference for evidence lineage.",
        "mapping_confidence": "Evidence confidence only; not return probability.",
        "available_time": "Earliest time this exposure mapping can be known.",
        "report_only": "Must be true for this workflow.",
        "diagnostic_only": "Must be true for this workflow.",
    }
    return descriptions.get(field, "Company exposure schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "manual_review_required",
        "pit_valid",
        "decision_time_eligible",
        "is_proxy",
        "report_only",
        "diagnostic_only",
        "is_live_signal",
        "is_alpha_claim",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "stock_profile_validation_allowed",
        "real_buy_review_allowed",
        "trading_allowed",
    }:
        return "boolean"
    if field == "mapping_confidence":
        return "float_0_to_1"
    if field in {"effective_from", "effective_to", "as_of_date"}:
        return "date"
    if field in {"available_time", "stale_after", "reviewed_at"}:
        return "timestamp"
    return "string"


def _timestamp_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return True
    first_ts = pd.to_datetime(first_text, errors="coerce")
    second_ts = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_ts) or pd.isna(second_ts):
        return False
    return bool(first_ts <= second_ts)


def _timestamp_to_date_order_ok(timestamp_value: Any, date_value: Any) -> bool:
    timestamp_text = _text(timestamp_value)
    date_text = _text(date_value)
    if not timestamp_text or not date_text:
        return False
    timestamp = pd.to_datetime(timestamp_text, errors="coerce")
    date = pd.to_datetime(date_text, errors="coerce")
    if pd.isna(timestamp) or pd.isna(date):
        return False
    return bool(timestamp.normalize() <= date.normalize())


def _date_order_ok(first: Any, second: Any) -> bool:
    first_text = _text(first)
    second_text = _text(second)
    if not first_text or not second_text:
        return True
    first_date = pd.to_datetime(first_text, errors="coerce")
    second_date = pd.to_datetime(second_text, errors="coerce")
    if pd.isna(first_date) or pd.isna(second_date):
        return False
    return bool(first_date <= second_date)


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
