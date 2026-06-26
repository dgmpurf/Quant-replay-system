"""Report-only event structured schema fixture workflow.

This module writes tiny synthetic event_structured rows for schema and
governance review only. Event structured rows describe event context with PIT
lineage. They are not raw document ingestion, factor observations, replay
evidence, signals, alpha claims, model inputs, stock profile validation,
buy-review permission, performance validation, or trading permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED = "EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED"

REQUIRED_EVENT_STRUCTURED_FIELDS = [
    "event_structured_id",
    "event_version",
    "event_key",
    "event_name",
    "schema_version",
    "created_by_workflow",
    "event_time",
    "publish_time",
    "available_time",
    "as_of_date",
    "effective_from",
    "effective_to",
    "stale_after",
    "timezone",
    "pit_valid",
    "decision_time_eligible",
    "revision_id",
    "supersedes_event_version_id",
    "source_id",
    "source_name",
    "source_tier",
    "document_id",
    "document_version_id",
    "source_hash",
    "content_hash",
    "raw_document_ref",
    "url_or_file_ref",
    "permission_class",
    "storage_policy",
    "parser_version",
    "extractor_version",
    "extraction_method",
    "event_type",
    "event_category",
    "event_scope",
    "event_status",
    "event_severity",
    "event_materiality_bucket",
    "event_subject",
    "announcement_type",
    "policy_type",
    "risk_type",
    "affected_entity_ids",
    "symbols",
    "instrument_types",
    "company_exposure_id_refs",
    "factor_id_refs",
    "taxonomy_layer_ids",
    "industry_id",
    "sector_id",
    "region_tags",
    "product_tags",
    "commodity_tags",
    "policy_tags",
    "impact_path",
    "transmission_path",
    "direction_rule_type",
    "direction_for_affected_entity",
    "direction_rule_detail",
    "time_horizon",
    "lag_policy",
    "magnitude_hint",
    "risk_veto_flag",
    "hard_veto_reason",
    "extraction_confidence",
    "event_confidence",
    "evidence_specificity",
    "manual_review_required",
    "manual_review_status",
    "reviewer",
    "reviewed_at",
    "quality_status",
    "validation_notes",
    "compliance_class",
    "trade_usage",
    "report_only",
    "diagnostic_only",
    "is_live_signal",
    "is_alpha_claim",
    "signal_score_implemented",
    "model_training_allowed",
    "active_weight_allowed",
    "active_threshold_allowed",
    "stock_profile_validation_allowed",
    "real_buy_review_allowed",
    "trading_allowed",
]

EVENT_TYPES = {
    "COMPANY_ANNOUNCEMENT",
    "EARNINGS_GUIDANCE",
    "FINANCIAL_REPORT",
    "MAJOR_CONTRACT",
    "DIVIDEND_BUYBACK",
    "POLICY_RELEASE",
    "REGULATORY_ACTION",
    "MACRO_RELEASE",
    "COMMODITY_PRICE_SHOCK",
    "INDUSTRY_SUPPLY_DEMAND",
    "TRADE_POLICY",
    "INDEX_REBALANCE",
    "ETF_FLOW_CONTEXT",
    "RISK_EVENT",
    "ST_DELIST_SUSPENSION",
    "RUMOR_UNVERIFIED",
    "REFUTATION_CLARIFICATION",
    "OTHER",
}

EVENT_SCOPES = {
    "COMPANY",
    "INDUSTRY",
    "SECTOR",
    "MARKET",
    "MACRO",
    "POLICY",
    "REGION",
    "GLOBAL",
    "ETF_INDEX",
    "SYNTHETIC_FIXTURE",
}

SOURCE_TIERS = {
    "OFFICIAL",
    "EXCHANGE",
    "COMPANY_DISCLOSURE",
    "REGULATOR",
    "MAJOR_MEDIA",
    "INDUSTRY_MEDIA",
    "SOCIAL_PLATFORM",
    "REVIEWED_LOCAL_CSV",
    "SYNTHETIC_FIXTURE",
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

DIRECTION_FOR_AFFECTED_ENTITY = {
    "POSITIVE",
    "NEGATIVE",
    "NEUTRAL",
    "MIXED",
    "CONDITIONAL",
    "RISK_VETO_ONLY",
    "UNKNOWN",
}

EVENT_STATUSES = {
    "OBSERVED",
    "UPDATED",
    "SUPERSEDED",
    "REFUTED",
    "BLOCKED",
    "DIAGNOSTIC_ONLY",
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

ALLOWED_TRADE_USAGE = {
    "research_context",
    "event_mapping",
    "factor_context",
    "exposure_context",
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

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "production_event_ingestion_created",
    "active_event_library_created",
    "real_raw_document_ingestion_created",
    "factor_observations_created",
    "company_exposure_production_mapping_created",
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
class EventStructuredSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/event_structured_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    production_event_ingestion_created: bool = False
    active_event_library_created: bool = False
    real_raw_document_ingestion_created: bool = False
    factor_observations_created: bool = False
    company_exposure_production_mapping_created: bool = False
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
class EventStructuredSchemaFixtureResult:
    event_structured_schema_fixture_id: str
    status: str
    workflow_stage: str
    event_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_event_structured_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: EventStructuredSchemaFixtureSettings | None = None,
) -> EventStructuredSchemaFixtureResult:
    resolved_settings = settings or EventStructuredSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = EventStructuredSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_event_structured_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_event_structured_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_event_structured_schema_fields()
    type_matrix = build_event_structured_type_matrix(fixture_rows)
    direction_matrix = build_event_structured_direction_matrix(fixture_rows)
    pit_lineage_matrix = build_event_structured_pit_lineage_matrix(fixture_rows)
    source_quality_matrix = build_event_structured_source_quality_matrix(fixture_rows)
    validation_summary = validate_event_structured_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = EventStructuredSchemaFixtureResult(
        event_structured_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=EVENT_STRUCTURED_SCHEMA_FIXTURE_CREATED,
        event_count=len(fixture_rows),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_event_structured_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            type_matrix=type_matrix,
            direction_matrix=direction_matrix,
            pit_lineage_matrix=pit_lineage_matrix,
            source_quality_matrix=source_quality_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_event_structured_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            event_structured_id="SYNTH_OFFICIAL_STEEL_CAPACITY_RESTRICTION",
            event_key="POLICY:STEEL_CAPACITY_RESTRICTION:SYNTH",
            event_name="Synthetic official steel capacity restriction",
            event_type="POLICY_RELEASE",
            event_category="policy_capacity",
            event_scope="POLICY",
            event_status="OBSERVED",
            event_severity="MEDIUM",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic regional steel capacity policy",
            policy_type="capacity_restriction",
            affected_entity_ids="SYNTH_STEEL_BUYER_ENTITY,SYNTH_REGIONAL_CAPACITY_ENTITY",
            symbols="000001,000005",
            instrument_types="STOCK",
            company_exposure_id_refs="SYNTH_STEEL_IRON_ORE_COST_BUYER,SYNTH_REGIONAL_CAPACITY_RESTRICTION",
            factor_id_refs="L3_POLICY_CAPACITY_RESTRICTION_SAMPLE",
            taxonomy_layer_ids="L3_MACRO_LIQUIDITY_POLICY_GLOBAL,L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            industry_id="SYNTH_STEEL",
            sector_id="SYNTH_MATERIALS",
            region_tags="synthetic_region_a",
            commodity_tags="steel",
            policy_tags="capacity_restriction",
            impact_path="policy release -> capacity restriction context",
            transmission_path="official policy -> affected plant exposure -> supply context",
            direction_rule_type="CONDITIONAL",
            direction_for_affected_entity="CONDITIONAL",
            direction_rule_detail="Capacity restriction direction depends on whether the entity is directly restricted or benefits from competitor supply limits.",
            time_horizon="event_window",
            lag_policy="available after official publish and review time only",
            magnitude_hint="synthetic_medium",
            trade_usage="event_mapping",
            extraction_confidence=0.82,
            event_confidence=0.8,
            source_tier="OFFICIAL",
        ),
        _row(
            event_structured_id="SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC",
            event_key="COMMODITY:IRON_ORE:PRICE_SHOCK:SYNTH",
            event_name="Synthetic public iron ore price shock",
            event_type="COMMODITY_PRICE_SHOCK",
            event_category="commodity_price",
            event_scope="INDUSTRY",
            event_status="OBSERVED",
            event_severity="MEDIUM",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic iron ore price movement",
            affected_entity_ids="SYNTH_STEEL_BUYER_ENTITY,SYNTH_IRON_ORE_PRODUCER_ENTITY",
            symbols="000001,000002",
            instrument_types="STOCK",
            company_exposure_id_refs="SYNTH_STEEL_IRON_ORE_COST_BUYER,SYNTH_IRON_ORE_RESOURCE_PRODUCER",
            factor_id_refs="L2_IRON_ORE_PRICE_CHANGE_SAMPLE",
            taxonomy_layer_ids="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            industry_id="SYNTH_STEEL,SYNTH_MINING",
            sector_id="SYNTH_MATERIALS",
            commodity_tags="iron_ore",
            impact_path="commodity price shock -> exposure-specific margin/revenue context",
            transmission_path="public commodity context -> steel buyer cost pressure or resource producer revenue context",
            direction_rule_type="MIXED_BY_EXPOSURE",
            direction_for_affected_entity="MIXED",
            direction_rule_detail="The same iron ore event may be negative for a steel buyer and positive for a resource producer; it does not compute a factor observation.",
            time_horizon="daily_to_quarterly",
            magnitude_hint="synthetic_price_shock",
            trade_usage="factor_context",
            extraction_confidence=0.78,
            event_confidence=0.78,
            source_tier="INDUSTRY_MEDIA",
        ),
        _row(
            event_structured_id="SYNTH_COMPANY_MAJOR_CONTRACT_DISCLOSURE",
            event_key="COMPANY:MAJOR_CONTRACT:SYNTH",
            event_name="Synthetic major contract disclosure",
            event_type="MAJOR_CONTRACT",
            event_category="company_disclosure",
            event_scope="COMPANY",
            event_status="OBSERVED",
            event_severity="MEDIUM",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic company contract disclosure",
            announcement_type="major_contract",
            affected_entity_ids="SYNTH_CONTRACT_ENTITY",
            symbols="000006",
            instrument_types="STOCK",
            company_exposure_id_refs="SYNTH_PRODUCT_REVENUE_EXPOSURE",
            factor_id_refs="L1_PRODUCT_REVENUE_EXPOSURE_SAMPLE",
            taxonomy_layer_ids="L1_OPERATIONS_COMPANY_EVENTS",
            industry_id="SYNTH_ADVANCED_MANUFACTURING",
            product_tags="battery_component",
            impact_path="contract disclosure -> revenue certainty context",
            transmission_path="company disclosure -> order backlog context",
            direction_rule_type="DIRECT",
            direction_for_affected_entity="POSITIVE",
            direction_rule_detail="Contract disclosure may be positive revenue-certainty context but is not a profit guarantee or buy signal.",
            time_horizon="quarterly",
            magnitude_hint="synthetic_contract_context",
            trade_usage="research_context",
            extraction_confidence=0.86,
            event_confidence=0.82,
            source_tier="COMPANY_DISCLOSURE",
        ),
        _row(
            event_structured_id="SYNTH_EARNINGS_GUIDANCE_UPWARD_REVISION",
            event_key="COMPANY:EARNINGS_GUIDANCE_UP:SYNTH",
            event_name="Synthetic upward earnings guidance revision",
            event_type="EARNINGS_GUIDANCE",
            event_category="earnings_guidance",
            event_scope="COMPANY",
            event_status="OBSERVED",
            event_severity="MEDIUM",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic earnings guidance revision",
            announcement_type="earnings_guidance",
            affected_entity_ids="SYNTH_GUIDANCE_ENTITY",
            symbols="000007",
            instrument_types="STOCK",
            factor_id_refs="L1_REVENUE_GROWTH_YOY_SAMPLE",
            taxonomy_layer_ids="L1_OPERATIONS_COMPANY_EVENTS",
            impact_path="guidance revision -> earnings expectation context",
            transmission_path="company disclosure -> reviewed earnings context",
            direction_rule_type="DIRECT",
            direction_for_affected_entity="POSITIVE",
            direction_rule_detail="Upward guidance is positive context only and cannot become a buy signal without separate review.",
            time_horizon="quarterly",
            magnitude_hint="synthetic_guidance_up",
            trade_usage="research_context",
            extraction_confidence=0.84,
            event_confidence=0.81,
            source_tier="COMPANY_DISCLOSURE",
        ),
        _row(
            event_structured_id="SYNTH_REGULATORY_INQUIRY_LETTER_RISK",
            event_key="REGULATOR:INQUIRY_LETTER:SYNTH",
            event_name="Synthetic regulatory inquiry letter risk",
            event_type="REGULATORY_ACTION",
            event_category="regulatory_risk",
            event_scope="COMPANY",
            event_status="OBSERVED",
            event_severity="HIGH",
            event_materiality_bucket="HIGH",
            event_subject="Synthetic regulatory inquiry",
            risk_type="regulatory_inquiry",
            affected_entity_ids="SYNTH_REGULATORY_RISK_ENTITY",
            symbols="000008",
            instrument_types="STOCK",
            factor_id_refs="L8_ST_STATUS_RISK_VETO_SAMPLE",
            taxonomy_layer_ids="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            impact_path="regulatory inquiry -> risk review context",
            transmission_path="regulator notice -> compliance review context",
            direction_rule_type="RISK_VETO_ONLY",
            direction_for_affected_entity="RISK_VETO_ONLY",
            direction_rule_detail="Regulatory inquiry is a risk filter / observe-only event and cannot create positive alpha.",
            time_horizon="event_window",
            magnitude_hint="risk_review",
            risk_veto_flag=True,
            hard_veto_reason="requires manual regulatory review",
            trade_usage="risk_filter",
            extraction_confidence=0.88,
            event_confidence=0.84,
            source_tier="REGULATOR",
        ),
        _row(
            event_structured_id="SYNTH_DIVIDEND_BUYBACK_ANNOUNCEMENT",
            event_key="COMPANY:DIVIDEND_BUYBACK:SYNTH",
            event_name="Synthetic dividend and buyback announcement",
            event_type="DIVIDEND_BUYBACK",
            event_category="capital_return",
            event_scope="COMPANY",
            event_status="OBSERVED",
            event_severity="LOW",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic capital return announcement",
            announcement_type="dividend_buyback",
            affected_entity_ids="SYNTH_CAPITAL_RETURN_ENTITY",
            symbols="000009",
            instrument_types="STOCK",
            factor_id_refs="L7_VALUATION_PERCENTILE_SAMPLE",
            taxonomy_layer_ids="L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION",
            impact_path="capital return announcement -> shareholder return context",
            transmission_path="company disclosure -> capital allocation context",
            direction_rule_type="CONDITIONAL",
            direction_for_affected_entity="CONDITIONAL",
            direction_rule_detail="Capital return announcements are descriptive context only and depend on valuation, cash flow, and review state.",
            time_horizon="event_window",
            magnitude_hint="synthetic_capital_return",
            trade_usage="research_context",
            extraction_confidence=0.8,
            event_confidence=0.76,
            source_tier="COMPANY_DISCLOSURE",
        ),
        _row(
            event_structured_id="SYNTH_EXPORT_TRADE_POLICY_CHANGE",
            event_key="POLICY:EXPORT_TRADE_CHANGE:SYNTH",
            event_name="Synthetic export trade policy change",
            event_type="TRADE_POLICY",
            event_category="trade_policy",
            event_scope="POLICY",
            event_status="OBSERVED",
            event_severity="MEDIUM",
            event_materiality_bucket="MEDIUM",
            event_subject="Synthetic export trade policy change",
            policy_type="trade_policy",
            affected_entity_ids="SYNTH_EXPORTER_ENTITY,SYNTH_IMPORTER_ENTITY",
            symbols="000003,000004",
            instrument_types="STOCK",
            company_exposure_id_refs="SYNTH_EXPORTER_CNY_DEPRECIATION,SYNTH_IMPORTER_CNY_DEPRECIATION",
            factor_id_refs="L3_FX_CNY_DEPRECIATION_SAMPLE",
            taxonomy_layer_ids="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            region_tags="overseas_revenue,import_cost",
            policy_tags="trade_policy",
            impact_path="trade policy change -> exporter/importer exposure context",
            transmission_path="policy release -> exposure-specific revenue/cost context",
            direction_rule_type="MIXED_BY_EXPOSURE",
            direction_for_affected_entity="MIXED",
            direction_rule_detail="Direction differs by exporter/importer exposure and cannot be interpreted without company exposure context.",
            time_horizon="monthly_or_quarterly",
            magnitude_hint="synthetic_policy_context",
            trade_usage="exposure_context",
            extraction_confidence=0.76,
            event_confidence=0.74,
            source_tier="OFFICIAL",
        ),
        _row(
            event_structured_id="SYNTH_INDEX_REBALANCE_CONTEXT",
            event_key="INDEX:REBALANCE:SYNTH",
            event_name="Synthetic index rebalance context",
            event_type="INDEX_REBALANCE",
            event_category="index_context",
            event_scope="ETF_INDEX",
            event_status="OBSERVED",
            event_severity="LOW",
            event_materiality_bucket="LOW",
            event_subject="Synthetic index rebalance",
            affected_entity_ids="SYNTH_ETF_ENTITY",
            symbols="159915",
            instrument_types="ETF",
            company_exposure_id_refs="SYNTH_ETF_INDEX_HOLDING_EXPOSURE",
            factor_id_refs="L4_INDEX_INCLUSION_EVENT_SAMPLE",
            taxonomy_layer_ids="L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND",
            impact_path="index rebalance -> ETF/index context",
            transmission_path="index notice -> synthetic ETF/index context",
            direction_rule_type="CONDITIONAL",
            direction_for_affected_entity="CONDITIONAL",
            direction_rule_detail="ETF/index context is synthetic only and requires real holdings review before production use.",
            time_horizon="event_window",
            magnitude_hint="synthetic_index_context",
            trade_usage="observe_only",
            validation_notes="Synthetic ETF/index context only; does not claim real or current holdings ingestion.",
            extraction_confidence=0.7,
            event_confidence=0.68,
            source_tier="EXCHANGE",
        ),
        _row(
            event_structured_id="SYNTH_ST_DELIST_RISK_VETO_EVENT",
            event_key="RISK:ST_DELIST:SYNTH",
            event_name="Synthetic ST/delist risk veto event",
            event_type="ST_DELIST_SUSPENSION",
            event_category="status_risk",
            event_scope="COMPANY",
            event_status="OBSERVED",
            event_severity="HIGH",
            event_materiality_bucket="HIGH",
            event_subject="Synthetic ST/delist status risk",
            risk_type="st_delist_suspension",
            affected_entity_ids="SYNTH_ST_STATUS_ENTITY",
            symbols="000010",
            instrument_types="STOCK",
            factor_id_refs="L8_ST_STATUS_RISK_VETO_SAMPLE",
            taxonomy_layer_ids="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            impact_path="status risk -> risk veto context",
            transmission_path="status event -> compliance/risk review",
            direction_rule_type="RISK_VETO_ONLY",
            direction_for_affected_entity="RISK_VETO_ONLY",
            direction_rule_detail="ST/delist risk veto can block review but creates no positive alpha and no trading permission.",
            time_horizon="daily",
            magnitude_hint="risk_veto",
            risk_veto_flag=True,
            hard_veto_reason="status risk requires manual blocker review",
            trade_usage="no_trade",
            extraction_confidence=0.82,
            event_confidence=0.8,
            source_tier="EXCHANGE",
        ),
        _row(
            event_structured_id="SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT",
            event_key="RUMOR:UNVERIFIED:SYNTH",
            event_name="Synthetic blocked unverified rumor event",
            event_type="RUMOR_UNVERIFIED",
            event_category="unverified_rumor",
            event_scope="SYNTHETIC_FIXTURE",
            event_status="BLOCKED",
            event_severity="UNKNOWN",
            event_materiality_bucket="UNKNOWN",
            event_subject="Synthetic unverified rumor",
            risk_type="unverified_private_or_restricted",
            affected_entity_ids="SYNTH_RUMOR_ENTITY",
            symbols="000011",
            instrument_types="STOCK",
            taxonomy_layer_ids="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            impact_path="blocked rumor -> no downstream use",
            transmission_path="unverified/private source style -> blocked",
            direction_rule_type="UNKNOWN",
            direction_for_affected_entity="UNKNOWN",
            direction_rule_detail="Unverified or private/restricted rumor is blocked and cannot be PIT-valid, decision-time eligible, or tradeable.",
            time_horizon="none",
            magnitude_hint="unknown",
            trade_usage="no_trade",
            pit_valid=False,
            decision_time_eligible=False,
            event_status_override="BLOCKED",
            quality_status="BLOCKED",
            manual_review_status="BLOCKED",
            evidence_specificity="BLOCKED",
            compliance_class="BLOCKED_UNVERIFIED",
            extraction_confidence=0.0,
            event_confidence=0.0,
            source_tier="SOCIAL_PLATFORM",
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_EVENT_STRUCTURED_FIELDS)


def build_event_structured_schema_fields() -> pd.DataFrame:
    enum_values = {
        "event_type": ",".join(sorted(EVENT_TYPES)),
        "event_scope": ",".join(sorted(EVENT_SCOPES)),
        "source_tier": ",".join(sorted(SOURCE_TIERS)),
        "direction_rule_type": ",".join(sorted(DIRECTION_RULE_TYPES)),
        "direction_for_affected_entity": ",".join(sorted(DIRECTION_FOR_AFFECTED_ENTITY)),
        "event_status": ",".join(sorted(EVENT_STATUSES)),
        "quality_status": ",".join(sorted(QUALITY_STATUSES)),
        "manual_review_status": ",".join(sorted(MANUAL_REVIEW_STATUSES)),
        "trade_usage": ",".join(sorted(ALLOWED_TRADE_USAGE)),
    }
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "field_group": _field_group(field),
                "required": True,
                "data_type_hint": _data_type_hint(field),
                "allowed_values": enum_values.get(field, ""),
                "description": _field_description(field),
            }
            for field in REQUIRED_EVENT_STRUCTURED_FIELDS
        ]
    )


def build_event_structured_type_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return fixture_rows[
        [
            "event_structured_id",
            "event_type",
            "event_scope",
            "source_tier",
            "event_category",
            "event_status",
            "quality_status",
            "trade_usage",
        ]
    ].copy()


def build_event_structured_direction_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return fixture_rows[
        [
            "event_structured_id",
            "affected_entity_ids",
            "company_exposure_id_refs",
            "factor_id_refs",
            "impact_path",
            "transmission_path",
            "direction_rule_type",
            "direction_for_affected_entity",
            "direction_rule_detail",
            "risk_veto_flag",
            "hard_veto_reason",
        ]
    ].copy()


def build_event_structured_pit_lineage_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return fixture_rows[
        [
            "event_structured_id",
            "event_time",
            "publish_time",
            "available_time",
            "as_of_date",
            "stale_after",
            "pit_valid",
            "decision_time_eligible",
            "revision_id",
            "supersedes_event_version_id",
        ]
    ].copy()


def build_event_structured_source_quality_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    return fixture_rows[
        [
            "event_structured_id",
            "source_id",
            "source_name",
            "source_tier",
            "document_id",
            "document_version_id",
            "source_hash",
            "content_hash",
            "parser_version",
            "extractor_version",
            "extraction_method",
            "extraction_confidence",
            "event_confidence",
            "manual_review_status",
            "quality_status",
        ]
    ].copy()


def validate_event_structured_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: EventStructuredSchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    row_text = " ".join(fixture_rows.fillna("").astype(str).agg(" ".join, axis=1))
    lower_text = row_text.lower()
    rows_by_id = fixture_rows.set_index("event_structured_id", drop=False)
    iron = rows_by_id.loc["SYNTH_IRON_ORE_PRICE_SHOCK_PUBLIC"]
    risk = rows_by_id.loc["SYNTH_ST_DELIST_RISK_VETO_EVENT"]
    blocked = rows_by_id.loc["SYNTH_BLOCKED_UNVERIFIED_RUMOR_EVENT"]
    etf = rows_by_id.loc["SYNTH_INDEX_REBALANCE_CONTEXT"]
    conditional = fixture_rows[
        fixture_rows["direction_rule_type"].isin({"CONDITIONAL", "MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"})
        | fixture_rows["direction_for_affected_entity"].isin({"CONDITIONAL", "MIXED"})
    ]
    evidence_backed = fixture_rows[fixture_rows["evidence_specificity"] != "BLOCKED"]

    checks = [
        ("required_fields_present", set(REQUIRED_EVENT_STRUCTURED_FIELDS).issubset(set(fixture_rows.columns))),
        ("exactly_10_fixture_rows", len(fixture_rows) == 10),
        ("event_structured_id_unique", fixture_rows["event_structured_id"].is_unique),
        ("event_version_present", fixture_rows["event_version"].map(_is_non_empty_string).all()),
        ("event_times_present", fixture_rows["event_time"].map(_is_non_empty_string).all()),
        ("publish_times_present", fixture_rows["publish_time"].map(_is_non_empty_string).all()),
        ("available_times_present", fixture_rows["available_time"].map(_is_non_empty_string).all()),
        (
            "timing_examples_separated",
            len(
                fixture_rows[
                    (fixture_rows["event_time"] != fixture_rows["publish_time"])
                    & (fixture_rows["publish_time"] != fixture_rows["available_time"])
                ]
            )
            >= 6,
        ),
        (
            "available_time_before_as_of_date",
            fixture_rows.apply(lambda row: _timestamp_to_date_order_ok(row["available_time"], row["as_of_date"]), axis=1).all(),
        ),
        (
            "stale_after_not_before_available_time",
            fixture_rows.apply(lambda row: _timestamp_order_ok(row["available_time"], row["stale_after"]), axis=1).all(),
        ),
        ("source_id_present", fixture_rows["source_id"].map(_is_non_empty_string).all()),
        ("document_id_present_for_evidence_backed", evidence_backed["document_id"].map(_is_non_empty_string).all()),
        ("document_version_id_present_for_evidence_backed", evidence_backed["document_version_id"].map(_is_non_empty_string).all()),
        (
            "source_hash_or_content_hash_present",
            fixture_rows.apply(lambda row: bool(_text(row["source_hash"])) or bool(_text(row["content_hash"])), axis=1).all(),
        ),
        ("revision_id_present", fixture_rows["revision_id"].map(_is_non_empty_string).all()),
        ("parser_version_present", fixture_rows["parser_version"].map(_is_non_empty_string).all()),
        ("extractor_version_present", fixture_rows["extractor_version"].map(_is_non_empty_string).all()),
        ("event_type_valid", fixture_rows["event_type"].isin(EVENT_TYPES).all()),
        ("event_scope_valid", fixture_rows["event_scope"].isin(EVENT_SCOPES).all()),
        ("source_tier_valid", fixture_rows["source_tier"].isin(SOURCE_TIERS).all()),
        ("direction_rule_type_valid", fixture_rows["direction_rule_type"].isin(DIRECTION_RULE_TYPES).all()),
        ("direction_for_affected_entity_valid", fixture_rows["direction_for_affected_entity"].isin(DIRECTION_FOR_AFFECTED_ENTITY).all()),
        ("event_status_valid", fixture_rows["event_status"].isin(EVENT_STATUSES).all()),
        ("quality_status_valid", fixture_rows["quality_status"].isin(QUALITY_STATUSES).all()),
        ("manual_review_status_valid", fixture_rows["manual_review_status"].isin(MANUAL_REVIEW_STATUSES).all()),
        ("mixed_conditional_direction_detail_present", conditional["direction_rule_detail"].map(_is_non_empty_string).all()),
        (
            "commodity_event_exposure_dependent",
            iron["direction_rule_type"] == "MIXED_BY_EXPOSURE"
            and iron["direction_for_affected_entity"] == "MIXED"
            and "steel buyer" in iron["direction_rule_detail"]
            and "resource producer" in iron["direction_rule_detail"],
        ),
        (
            "risk_veto_not_positive_alpha",
            risk["direction_for_affected_entity"] == "RISK_VETO_ONLY"
            and not _bool(risk["is_alpha_claim"])
            and "no positive alpha" in risk["direction_rule_detail"],
        ),
        (
            "blocked_rumor_no_trade_not_pit_valid",
            blocked["trade_usage"] == "no_trade"
            and not _bool(blocked["pit_valid"])
            and not _bool(blocked["decision_time_eligible"]),
        ),
        (
            "etf_row_no_real_holdings_claim",
            etf["event_scope"] == "ETF_INDEX"
            and "does not claim real or current holdings ingestion" in etf["validation_notes"],
        ),
        ("extraction_confidence_bounded", fixture_rows["extraction_confidence"].astype(float).between(0, 1).all()),
        ("event_confidence_bounded", fixture_rows["event_confidence"].astype(float).between(0, 1).all()),
        ("confidence_not_return_probability", "not return probability" in lower_text),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("is_live_signal_false", fixture_rows["is_live_signal"].map(lambda value: not _bool(value)).all()),
        ("is_alpha_claim_false", fixture_rows["is_alpha_claim"].map(lambda value: not _bool(value)).all()),
        ("signal_score_implemented_false", fixture_rows["signal_score_implemented"].map(lambda value: not _bool(value)).all()),
        ("model_training_allowed_false", fixture_rows["model_training_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_weight_allowed_false", fixture_rows["active_weight_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_threshold_allowed_false", fixture_rows["active_threshold_allowed"].map(lambda value: not _bool(value)).all()),
        ("stock_profile_validation_allowed_false", fixture_rows["stock_profile_validation_allowed"].map(lambda value: not _bool(value)).all()),
        ("real_buy_review_allowed_false", fixture_rows["real_buy_review_allowed"].map(lambda value: not _bool(value)).all()),
        ("trading_allowed_false", fixture_rows["trading_allowed"].map(lambda value: not _bool(value)).all()),
        (
            "no_forbidden_trade_usage",
            fixture_rows["trade_usage"].isin(ALLOWED_TRADE_USAGE).all()
            and not fixture_rows["trade_usage"].isin(FORBIDDEN_TRADE_USAGE).any(),
        ),
        ("no_token_or_secret_values", not _contains_secret_like(lower_text)),
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


def resolve_event_structured_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "event_structured_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "event_structured_schema_fields.csv",
        "fixture_rows": artifact_dir / "event_structured_fixture_rows.csv",
        "type_matrix": artifact_dir / "event_structured_type_matrix.csv",
        "direction_matrix": artifact_dir / "event_structured_direction_matrix.csv",
        "pit_lineage_matrix": artifact_dir / "event_structured_pit_lineage_matrix.csv",
        "source_quality_matrix": artifact_dir / "event_structured_source_quality_matrix.csv",
        "validation_summary": artifact_dir / "event_structured_validation_summary.csv",
        "limitations": artifact_dir / "event_structured_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_event_structured_schema_fixture_artifacts(
    *,
    result: EventStructuredSchemaFixtureResult,
    settings: EventStructuredSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    type_matrix: pd.DataFrame,
    direction_matrix: pd.DataFrame,
    pit_lineage_matrix: pd.DataFrame,
    source_quality_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    type_matrix.to_csv(paths["type_matrix"], index=False)
    direction_matrix.to_csv(paths["direction_matrix"], index=False)
    pit_lineage_matrix.to_csv(paths["pit_lineage_matrix"], index=False)
    source_quality_matrix.to_csv(paths["source_quality_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_event_structured_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_event_structured_limitations(result: EventStructuredSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Event Structured Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic event_structured rows for schema and governance review only.",
            "",
            "## Not Created",
            "",
            "- No production event ingestion is created.",
            "- No active event library or real raw document ingestion is created.",
            "- No factor observations are created.",
            "- No production company exposure mapping is created.",
            "- No replay evidence bundles are created.",
            "- No signal_score implementation is created.",
            "- No model training, active weights, active thresholds, stock_profile validation, or paper validation is created.",
            "- No buy-review eligibility or performance validation is created.",
            "- No trading, broker behavior, orders, messages, or APIs are created.",
            "- Extraction confidence and event confidence are evidence confidence only, not a model weight and not return probability.",
            "",
            "## Current Result",
            "",
            f"- event_structured_schema_fixture_id: {result.event_structured_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- event_count: {result.event_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: EventStructuredSchemaFixtureResult,
    settings: EventStructuredSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "event_structured_schema_fixture_id": result.event_structured_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "event_structured_schema_fixture_created": True,
        "event_structured_rows_created": True,
        "event_count": result.event_count,
        "validation_issue_count": result.validation_issue_count,
        "report_only": True,
        "diagnostic_only": True,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    row = {
        "event_structured_id": "",
        "event_version": "event_structured_schema_fixture_v0.1",
        "event_key": "",
        "event_name": "",
        "schema_version": "event_structured_schema_fixture_v0.1",
        "created_by_workflow": "event-structured-schema-fixture",
        "event_time": "2024-04-01T10:00:00",
        "publish_time": "2024-04-01T15:00:00",
        "available_time": "2024-04-01T17:00:00",
        "as_of_date": "2024-04-02",
        "effective_from": "2024-04-01",
        "effective_to": "",
        "stale_after": "2024-12-31T23:59:59",
        "timezone": "Asia/Shanghai",
        "pit_valid": True,
        "decision_time_eligible": True,
        "revision_id": "",
        "supersedes_event_version_id": "",
        "source_id": "",
        "source_name": "Synthetic reviewed source",
        "source_tier": "SYNTHETIC_FIXTURE",
        "document_id": "",
        "document_version_id": "",
        "source_hash": "",
        "content_hash": "",
        "raw_document_ref": "",
        "url_or_file_ref": "synthetic://event-structured-schema-fixture",
        "permission_class": "SYNTHETIC_FIXTURE_ONLY",
        "storage_policy": "manual_diagnostics_only",
        "parser_version": "synthetic_parser_v0.1",
        "extractor_version": "synthetic_extractor_v0.1",
        "extraction_method": "manual_synthetic_fixture",
        "event_type": "OTHER",
        "event_category": "",
        "event_scope": "SYNTHETIC_FIXTURE",
        "event_status": "OBSERVED",
        "event_severity": "LOW",
        "event_materiality_bucket": "LOW",
        "event_subject": "",
        "announcement_type": "",
        "policy_type": "",
        "risk_type": "",
        "affected_entity_ids": "",
        "symbols": "",
        "instrument_types": "",
        "company_exposure_id_refs": "",
        "factor_id_refs": "",
        "taxonomy_layer_ids": "",
        "industry_id": "",
        "sector_id": "",
        "region_tags": "",
        "product_tags": "",
        "commodity_tags": "",
        "policy_tags": "",
        "impact_path": "",
        "transmission_path": "",
        "direction_rule_type": "UNKNOWN",
        "direction_for_affected_entity": "UNKNOWN",
        "direction_rule_detail": "",
        "time_horizon": "",
        "lag_policy": "available_time controls replay eligibility; no downstream use in fixture",
        "magnitude_hint": "",
        "risk_veto_flag": False,
        "hard_veto_reason": "",
        "extraction_confidence": 0.5,
        "event_confidence": 0.5,
        "evidence_specificity": "SYNTHETIC_FIXTURE",
        "manual_review_required": True,
        "manual_review_status": "REVIEW_REQUIRED",
        "reviewer": "diagnostic_fixture",
        "reviewed_at": "",
        "quality_status": "REVIEW_REQUIRED",
        "validation_notes": "Synthetic/report-only event context; confidence is not return probability and not a model weight.",
        "compliance_class": "REPORT_ONLY_REVIEW_REQUIRED",
        "trade_usage": "research_context",
        "report_only": True,
        "diagnostic_only": True,
        "is_live_signal": False,
        "is_alpha_claim": False,
        "signal_score_implemented": False,
        "model_training_allowed": False,
        "active_weight_allowed": False,
        "active_threshold_allowed": False,
        "stock_profile_validation_allowed": False,
        "real_buy_review_allowed": False,
        "trading_allowed": False,
    }
    event_status_override = values.pop("event_status_override", None)
    row.update(values)
    if event_status_override is not None:
        row["event_status"] = event_status_override
    event_id = row["event_structured_id"]
    row["source_id"] = row["source_id"] or f"SYNTH_EVENT_SOURCE_{_short_hash(event_id)}"
    row["document_id"] = row["document_id"] or f"{event_id}::doc"
    row["document_version_id"] = row["document_version_id"] or f"{event_id}::doc_v0"
    row["raw_document_ref"] = row["raw_document_ref"] or row["document_version_id"]
    row["source_hash"] = row["source_hash"] or f"sha256:{_hash_text('source:' + row['source_id'])}"
    row["content_hash"] = row["content_hash"] or f"sha256:{_hash_text('content:' + event_id)}"
    row["revision_id"] = row["revision_id"] or f"REV-{_short_hash(event_id)}"
    return row


def _assert_settings_safe(settings: EventStructuredSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Event structured schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_METADATA_FALSE_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe event structured fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_EVENT_STRUCTURED_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Event Structured Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only event structured schema fixture. Keep the workflow synthetic and do not create production event ingestion, active event libraries, real raw document ingestion, factor observations, replay evidence bundles, signal_score, model training, active weights, active thresholds, stock_profile validation, paper validation, buy-review eligibility, performance validation, or trading permission.",
        ]
    )


def _field_group(field: str) -> str:
    if field in {"event_structured_id", "event_version", "event_key", "event_name", "schema_version", "created_by_workflow"}:
        return "identity_version"
    if field in {
        "event_time",
        "publish_time",
        "available_time",
        "as_of_date",
        "effective_from",
        "effective_to",
        "stale_after",
        "timezone",
        "pit_valid",
        "decision_time_eligible",
        "revision_id",
        "supersedes_event_version_id",
    }:
        return "timing_pit"
    if field in {
        "source_id",
        "source_name",
        "source_tier",
        "document_id",
        "document_version_id",
        "source_hash",
        "content_hash",
        "raw_document_ref",
        "url_or_file_ref",
        "permission_class",
        "storage_policy",
        "parser_version",
        "extractor_version",
        "extraction_method",
    }:
        return "source_evidence_lineage"
    if field in {
        "event_type",
        "event_category",
        "event_scope",
        "event_status",
        "event_severity",
        "event_materiality_bucket",
        "event_subject",
        "announcement_type",
        "policy_type",
        "risk_type",
    }:
        return "event_classification"
    if field in {
        "affected_entity_ids",
        "symbols",
        "instrument_types",
        "company_exposure_id_refs",
        "factor_id_refs",
        "taxonomy_layer_ids",
        "industry_id",
        "sector_id",
        "region_tags",
        "product_tags",
        "commodity_tags",
        "policy_tags",
    }:
        return "entity_exposure_factor_mapping"
    if field in {
        "impact_path",
        "transmission_path",
        "direction_rule_type",
        "direction_for_affected_entity",
        "direction_rule_detail",
        "time_horizon",
        "lag_policy",
        "magnitude_hint",
        "risk_veto_flag",
        "hard_veto_reason",
    }:
        return "impact_direction_transmission"
    if field in {
        "extraction_confidence",
        "event_confidence",
        "evidence_specificity",
        "manual_review_required",
        "manual_review_status",
        "reviewer",
        "reviewed_at",
        "quality_status",
        "validation_notes",
    }:
        return "quality_review_confidence"
    return "compliance_governance"


def _field_description(field: str) -> str:
    descriptions = {
        "event_structured_id": "Stable synthetic structured event identifier.",
        "event_version": "Version of the structured event row.",
        "event_time": "When the synthetic event happened.",
        "publish_time": "When the synthetic event was published.",
        "available_time": "Earliest reviewed availability time for replay eligibility.",
        "source_id": "Source registry reference; does not grant production permission by itself.",
        "document_id": "Raw document reference for evidence lineage.",
        "parser_version": "Parser version used for the synthetic event row.",
        "extractor_version": "Extractor version used for the synthetic event row.",
        "event_type": "Governed event type.",
        "direction_rule_detail": "Human-readable contextual direction rule.",
        "extraction_confidence": "Extraction evidence confidence only; not return probability.",
        "event_confidence": "Event evidence confidence only; not return probability.",
        "trade_usage": "Non-actionable research/governance usage category.",
        "report_only": "Must be true for this workflow.",
        "diagnostic_only": "Must be true for this workflow.",
    }
    return descriptions.get(field, "Event structured schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "pit_valid",
        "decision_time_eligible",
        "risk_veto_flag",
        "manual_review_required",
        "report_only",
        "diagnostic_only",
        "is_live_signal",
        "is_alpha_claim",
        "signal_score_implemented",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "stock_profile_validation_allowed",
        "real_buy_review_allowed",
        "trading_allowed",
    }:
        return "boolean"
    if field in {"extraction_confidence", "event_confidence"}:
        return "float_0_to_1"
    if field in {"event_time", "publish_time", "available_time", "stale_after", "reviewed_at"}:
        return "timestamp"
    if field in {"as_of_date", "effective_from", "effective_to"}:
        return "date"
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
