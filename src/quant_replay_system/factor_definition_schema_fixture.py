"""Report-only factor definition schema fixture workflow.

This module writes tiny synthetic factor-definition rows for schema and
governance review only. It defines factor definitions as stable observation
rules, not observations, signals, training inputs, active weights, active
thresholds, stock profiles, buy-review eligibility, performance validation, or
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


FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED = "FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED"

CANONICAL_TAXONOMY_LAYERS: dict[str, str] = {
    "L1_OPERATIONS_COMPANY_EVENTS": "缁忚惀涓庡叕鍙镐簨浠跺眰",
    "L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES": "琛屼笟渚涢渶涓庝骇涓氶摼浠锋牸灞?",
    "L3_MACRO_LIQUIDITY_POLICY_GLOBAL": "瀹忚娴佸姩鎬т笌鏀跨瓥鍥介檯灞?",
    "L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND": "璧勬湰甯傚満鍒跺害涓庝緵闇€灞?",
    "L5_TRADING_BEHAVIOR_MICROSTRUCTURE": "浜ゆ槗琛屼负涓庡井瑙傜粨鏋勫眰",
    "L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION": "淇℃伅鎶湶涓庤垎鎯呬紶鎾眰",
    "L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION": "棰勬湡銆佷及鍊间笌瀹氫环鍋忕灞?",
    "L8_RISK_EVENTS_COMPLIANCE_BOUNDARY": "椋庨櫓浜嬩欢涓庡悎瑙勮竟鐣屽眰",
}

MOJIBAKE_LAYER_NAME_FRAGMENTS = [
    "缂佸繗鎯€",
    "鐞涘奔绗?",
    "鐎瑰繗",
    "鐠у嫭",
    "娴溿倖",
    "娣団剝",
    "妫板嫭",
    "妞嬪酣",
]

REQUIRED_FACTOR_DEFINITION_FIELDS = [
    "factor_id",
    "factor_name",
    "factor_version",
    "taxonomy_layer_id",
    "taxonomy_layer_name",
    "second_level",
    "legacy_12_factor_tags",
    "factor_kind",
    "entity_scope",
    "observation_unit",
    "value_type",
    "time_horizon",
    "impact_path",
    "affected_entities_rule",
    "expected_direction",
    "direction_rule_type",
    "direction_rule_detail",
    "required_source_types",
    "required_document_types",
    "required_raw_document_fields",
    "source_registry_required",
    "raw_document_store_required",
    "calculation_method",
    "transformation_method",
    "normalization_scope",
    "available_time_policy",
    "lag_policy",
    "revision_policy",
    "missing_value_policy",
    "quality_rule",
    "confidence_rule",
    "compliance_class",
    "trade_usage",
    "backtestable",
    "stock_profile_usage",
    "is_live_signal",
    "is_alpha_claim",
    "signal_score_component_allowed",
    "model_training_allowed",
    "active_weight_allowed",
    "active_threshold_allowed",
    "real_buy_review_allowed",
    "trading_allowed",
    "validation_status",
    "report_only",
    "diagnostic_only",
    "schema_version",
    "created_by_workflow",
]

FACTOR_KINDS = {
    "NUMERIC_CONTINUOUS",
    "NUMERIC_DISCRETE",
    "BINARY_EVENT",
    "CATEGORICAL_EVENT",
    "TEXT_DERIVED_EVENT",
    "REGIME_CONTEXT",
    "RISK_VETO",
    "META_GOVERNANCE",
}

ENTITY_SCOPES = {
    "SYMBOL",
    "ETF",
    "INDUSTRY",
    "SECTOR",
    "MARKET",
    "MACRO",
    "COMMODITY",
    "POLICY",
    "REGION",
    "PORTFOLIO",
}

TRADE_USAGE_ALLOWED = {
    "research_feature",
    "event_context",
    "market_confirmation",
    "risk_filter",
    "observe_only",
    "no_trade",
    "diagnostic_only",
}

TRADE_USAGE_FORBIDDEN = {
    "buy_signal",
    "sell_signal",
    "real_buy_review",
    "trading_signal",
}

EXPECTED_DIRECTIONS = {
    "POSITIVE",
    "NEGATIVE",
    "NEUTRAL",
    "MIXED_BY_EXPOSURE",
    "MIXED_BY_REGIME",
    "RISK_VETO_ONLY",
    "UNKNOWN",
}

FORBIDDEN_METADATA_FALSE_FLAGS = [
    "signal_score_formula_active",
    "signal_score_implemented",
    "live_signals_created",
    "signal_semantics_changed",
    "factor_observations_created",
    "event_ingestion_created",
    "company_exposure_created",
    "replay_evidence_bundle_created",
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
    "active_stock_profile_created",
    "operational_global_approved_for_paper_granted",
]


@dataclass(frozen=True)
class FactorDefinitionSchemaFixtureSettings:
    output_dir: Path = Path("outputs/reports/manual_diagnostics/factor_definition_schema_fixture_v0_1")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True
    signal_score_formula_active: bool = False
    signal_score_implemented: bool = False
    live_signals_created: bool = False
    signal_semantics_changed: bool = False
    factor_observations_created: bool = False
    event_ingestion_created: bool = False
    company_exposure_created: bool = False
    replay_evidence_bundle_created: bool = False
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
    active_stock_profile_created: bool = False
    operational_global_approved_for_paper_granted: bool = False


@dataclass(frozen=True)
class FactorDefinitionSchemaFixtureResult:
    factor_definition_schema_fixture_id: str
    status: str
    workflow_stage: str
    factor_count: int
    taxonomy_layer_count: int
    validation_issue_count: int
    report_only: bool
    diagnostic_only: bool
    artifact_paths: dict[str, Path]


def build_factor_definition_schema_fixture(
    *,
    output_dir: str | Path | None = None,
    settings: FactorDefinitionSchemaFixtureSettings | None = None,
) -> FactorDefinitionSchemaFixtureResult:
    resolved_settings = settings or FactorDefinitionSchemaFixtureSettings()
    if output_dir is not None:
        resolved_settings = FactorDefinitionSchemaFixtureSettings(
            **{**resolved_settings.__dict__, "output_dir": Path(output_dir)}
        )
    _assert_settings_safe(resolved_settings)

    fixture_rows = build_factor_definition_fixture_rows()
    fixture_id = _fixture_id(fixture_rows, resolved_settings.config_version)
    paths = resolve_factor_definition_schema_fixture_paths(resolved_settings.output_dir, fixture_id)
    schema_fields = build_factor_definition_schema_fields()
    taxonomy_layer_matrix = build_factor_definition_taxonomy_layer_matrix(fixture_rows)
    usage_boundary_matrix = build_factor_definition_usage_boundary_matrix(fixture_rows)
    validation_summary = validate_factor_definition_fixture(
        fixture_rows=fixture_rows,
        settings=resolved_settings,
        output_dir=resolved_settings.output_dir,
    )
    validation_issue_count = int((~validation_summary["passed"]).sum())
    result = FactorDefinitionSchemaFixtureResult(
        factor_definition_schema_fixture_id=fixture_id,
        status="PASS" if validation_issue_count == 0 else "FAIL",
        workflow_stage=FACTOR_DEFINITION_SCHEMA_FIXTURE_CREATED,
        factor_count=len(fixture_rows),
        taxonomy_layer_count=int(fixture_rows["taxonomy_layer_id"].nunique()),
        validation_issue_count=validation_issue_count,
        report_only=True,
        diagnostic_only=True,
        artifact_paths=paths,
    )
    if resolved_settings.write_artifacts:
        write_factor_definition_schema_fixture_artifacts(
            result=result,
            settings=resolved_settings,
            schema_fields=schema_fields,
            fixture_rows=fixture_rows,
            taxonomy_layer_matrix=taxonomy_layer_matrix,
            usage_boundary_matrix=usage_boundary_matrix,
            validation_summary=validation_summary,
        )
    return result


def build_factor_definition_fixture_rows() -> pd.DataFrame:
    rows = [
        _row(
            factor_id="L1_REVENUE_GROWTH_YOY_SAMPLE",
            factor_name="Synthetic revenue growth year-over-year rule",
            taxonomy_layer_id="L1_OPERATIONS_COMPANY_EVENTS",
            second_level="company_financial_growth",
            legacy_12_factor_tags="fundamental_quality,growth",
            factor_kind="NUMERIC_CONTINUOUS",
            entity_scope="SYMBOL",
            observation_unit="symbol_period",
            value_type="ratio",
            time_horizon="quarterly_or_annual",
            impact_path="company operations context",
            affected_entities_rule="Applies to listed company symbols with reviewed financial reports.",
            expected_direction="POSITIVE",
            direction_rule_type="default_positive_research_context",
            direction_rule_detail="Revenue growth may be positive research context only after PIT source and revision checks.",
            required_source_types="PUBLIC_OFFICIAL,LOCAL_CSV_REVIEWED",
            required_document_types="annual_report,quarterly_report,reviewed_dataset",
            calculation_method="year_over_year_percent_change",
            transformation_method="winsorize_then_standardize_for_research_only",
            normalization_scope="industry_and_period",
            confidence_rule="Requires source lineage, revision id, and reviewer confidence before downstream use.",
            trade_usage="research_feature",
            backtestable=True,
        ),
        _row(
            factor_id="L2_IRON_ORE_PRICE_CHANGE_SAMPLE",
            factor_name="Synthetic iron ore price change rule",
            taxonomy_layer_id="L2_INDUSTRY_SUPPLY_DEMAND_VALUE_CHAIN_PRICES",
            second_level="commodity_value_chain_price",
            legacy_12_factor_tags="industry_supply_demand,commodity_price",
            factor_kind="NUMERIC_CONTINUOUS",
            entity_scope="COMMODITY",
            observation_unit="commodity_date",
            value_type="percent_change",
            time_horizon="daily_or_weekly",
            impact_path="industry input cost and resource exposure context",
            affected_entities_rule="Maps to companies only through reviewed exposure direction rules.",
            expected_direction="MIXED_BY_EXPOSURE",
            direction_rule_type="exposure_dependent",
            direction_rule_detail="Iron ore price increases may be negative for input-cost steelmakers but positive for iron ore resource exposure.",
            required_source_types="PUBLIC_COMMODITY_REFERENCE,LOCAL_CSV_REVIEWED",
            required_document_types="commodity_price_dataset,reviewed_exposure_note",
            calculation_method="period_over_period_percent_change",
            transformation_method="standardize_by_commodity_history_for_research_only",
            normalization_scope="commodity",
            confidence_rule="Requires reviewed commodity source and company exposure mapping before interpretation.",
            trade_usage="event_context",
            backtestable=True,
        ),
        _row(
            factor_id="L3_PMI_CHANGE_SAMPLE",
            factor_name="Synthetic PMI change macro regime rule",
            taxonomy_layer_id="L3_MACRO_LIQUIDITY_POLICY_GLOBAL",
            second_level="macro_activity_regime",
            legacy_12_factor_tags="macro,policy_liquidity",
            factor_kind="REGIME_CONTEXT",
            entity_scope="MACRO",
            observation_unit="macro_release_period",
            value_type="index_change",
            time_horizon="monthly",
            impact_path="macro regime context",
            affected_entities_rule="Applies as market or industry context only after PIT release timing review.",
            expected_direction="MIXED_BY_REGIME",
            direction_rule_type="regime_dependent",
            direction_rule_detail="PMI changes require regime and industry context and remain observe-only in this fixture.",
            required_source_types="PUBLIC_MACRO_RELEASE,LOCAL_CSV_REVIEWED",
            required_document_types="macro_release_dataset,official_release_note",
            calculation_method="released_value_minus_prior_value",
            transformation_method="z_score_against_historical_release_series",
            normalization_scope="macro_series",
            confidence_rule="Requires release timestamp, revision policy, and as-of availability review.",
            trade_usage="observe_only",
            backtestable=False,
        ),
        _row(
            factor_id="L4_INDEX_INCLUSION_EVENT_SAMPLE",
            factor_name="Synthetic index inclusion event rule",
            taxonomy_layer_id="L4_CAPITAL_MARKET_INSTITUTIONS_SUPPLY_DEMAND",
            second_level="index_institutional_flow_event",
            legacy_12_factor_tags="capital_flow,index_event",
            factor_kind="BINARY_EVENT",
            entity_scope="SYMBOL",
            observation_unit="symbol_event",
            value_type="boolean",
            time_horizon="event_window",
            impact_path="institutional demand context",
            affected_entities_rule="Applies only when official index methodology and effective-date evidence are reviewed.",
            expected_direction="POSITIVE",
            direction_rule_type="event_context_positive_bias",
            direction_rule_detail="Index inclusion can be positive context but does not become an active signal or approval.",
            required_source_types="PUBLIC_INDEX_PROVIDER,LOCAL_CSV_REVIEWED",
            required_document_types="index_change_notice,reviewed_event_record",
            calculation_method="official_event_presence",
            transformation_method="binary_indicator_for_research_only",
            normalization_scope="event_family",
            confidence_rule="Requires official notice, effective date, and source hash lineage.",
            trade_usage="event_context",
            backtestable=True,
        ),
        _row(
            factor_id="L5_VOLUME_CONFIRMATION_SAMPLE",
            factor_name="Synthetic volume confirmation rule",
            taxonomy_layer_id="L5_TRADING_BEHAVIOR_MICROSTRUCTURE",
            second_level="trading_activity_confirmation",
            legacy_12_factor_tags="technical_liquidity,market_microstructure",
            factor_kind="NUMERIC_CONTINUOUS",
            entity_scope="SYMBOL",
            observation_unit="symbol_date",
            value_type="ratio",
            time_horizon="daily",
            impact_path="market participation context",
            affected_entities_rule="Applies to symbols with PIT-valid market data and trading calendar context.",
            expected_direction="NEUTRAL",
            direction_rule_type="context_dependent",
            direction_rule_detail="Volume confirmation is context-dependent and cannot be interpreted as buy/sell.",
            required_source_types="LOCAL_CSV_REVIEWED,PUBLIC_EXCHANGE_REFERENCE",
            required_document_types="market_data_dataset,trading_calendar",
            calculation_method="volume_divided_by_recent_average_volume",
            transformation_method="cap_extremes_for_research_only",
            normalization_scope="symbol_history",
            confidence_rule="Requires PIT market data lineage and trading calendar validation.",
            trade_usage="market_confirmation",
            backtestable=True,
        ),
        _row(
            factor_id="L6_ANNOUNCEMENT_EVENT_SAMPLE",
            factor_name="Synthetic announcement event rule",
            taxonomy_layer_id="L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION",
            second_level="disclosure_event_context",
            legacy_12_factor_tags="disclosure,sentiment",
            factor_kind="TEXT_DERIVED_EVENT",
            entity_scope="SYMBOL",
            observation_unit="symbol_disclosure",
            value_type="categorical_event",
            time_horizon="event_window",
            impact_path="information disclosure context",
            affected_entities_rule="Applies only to official/public disclosure references with reviewed timestamps.",
            expected_direction="MIXED_BY_EXPOSURE",
            direction_rule_type="reviewed_event_dependent",
            direction_rule_detail="Disclosure/sentiment rows do not directly create buy/sell signals.",
            required_source_types="PUBLIC_OFFICIAL,LOCAL_REVIEWED_TEXT_REFERENCE",
            required_document_types="announcement_reference,reviewed_text_extract",
            calculation_method="reviewed_event_classification",
            transformation_method="controlled_vocabulary_mapping_for_research_only",
            normalization_scope="event_taxonomy",
            confidence_rule="Requires reviewed event extraction and source permission boundary.",
            trade_usage="event_context",
            backtestable=False,
        ),
        _row(
            factor_id="L7_VALUATION_PERCENTILE_SAMPLE",
            factor_name="Synthetic valuation percentile rule",
            taxonomy_layer_id="L7_EXPECTATIONS_VALUATION_PRICING_DEVIATION",
            second_level="valuation_pricing_deviation",
            legacy_12_factor_tags="valuation,expectations",
            factor_kind="NUMERIC_CONTINUOUS",
            entity_scope="SYMBOL",
            observation_unit="symbol_date",
            value_type="percentile",
            time_horizon="daily_or_monthly",
            impact_path="pricing deviation research context",
            affected_entities_rule="Applies to symbols with PIT-valid fundamentals, prices, and industry classification.",
            expected_direction="MIXED_BY_REGIME",
            direction_rule_type="regime_and_industry_dependent",
            direction_rule_detail="Valuation percentiles require industry, regime, and accounting context before interpretation.",
            required_source_types="LOCAL_CSV_REVIEWED,PUBLIC_FINANCIAL_DISCLOSURE",
            required_document_types="valuation_dataset,financial_statement_reference",
            calculation_method="cross_sectional_or_history_percentile",
            transformation_method="industry_neutral_percentile_for_research_only",
            normalization_scope="industry_and_date",
            confidence_rule="Requires PIT fundamentals, price lineage, and benchmark/industry context.",
            trade_usage="research_feature",
            backtestable=True,
        ),
        _row(
            factor_id="L8_ST_STATUS_RISK_VETO_SAMPLE",
            factor_name="Synthetic ST status risk veto rule",
            taxonomy_layer_id="L8_RISK_EVENTS_COMPLIANCE_BOUNDARY",
            second_level="compliance_risk_veto",
            legacy_12_factor_tags="risk,compliance",
            factor_kind="RISK_VETO",
            entity_scope="SYMBOL",
            observation_unit="symbol_date",
            value_type="boolean",
            time_horizon="daily",
            impact_path="risk and compliance review context",
            affected_entities_rule="Applies to stock symbols with official/public status evidence and reviewer no-hit policy where needed.",
            expected_direction="RISK_VETO_ONLY",
            direction_rule_type="veto_only",
            direction_rule_detail="Risk veto rows can block or require review but cannot create positive alpha or buy permission.",
            required_source_types="PUBLIC_EXCHANGE_REFERENCE,PUBLIC_OFFICIAL_DISCLOSURE",
            required_document_types="risk_warning_status,delisting_or_status_reference",
            calculation_method="official_status_presence_or_reviewed_no_hit_context",
            transformation_method="veto_flag_for_review_only",
            normalization_scope="symbol_date",
            confidence_rule="Requires official status evidence, no-hit acceptance if used, and survivorship rationale.",
            trade_usage="risk_filter",
            backtestable=False,
        ),
    ]
    return pd.DataFrame(rows, columns=REQUIRED_FACTOR_DEFINITION_FIELDS)


def build_factor_definition_schema_fields() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_name": field,
                "required": True,
                "hard_gate": field
                in {
                    "factor_id",
                    "factor_version",
                    "taxonomy_layer_id",
                    "taxonomy_layer_name",
                    "factor_kind",
                    "entity_scope",
                    "expected_direction",
                    "trade_usage",
                    "source_registry_required",
                    "raw_document_store_required",
                    "available_time_policy",
                    "revision_policy",
                    "report_only",
                    "diagnostic_only",
                },
                "data_type_hint": _data_type_hint(field),
                "description": _field_description(field),
            }
            for field in REQUIRED_FACTOR_DEFINITION_FIELDS
        ]
    )


def build_factor_definition_taxonomy_layer_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        rows.append(
            {
                "factor_id": row["factor_id"],
                "taxonomy_layer_id": row["taxonomy_layer_id"],
                "taxonomy_layer_name": row["taxonomy_layer_name"],
                "taxonomy_primary": True,
                "legacy_12_factor_tags": row["legacy_12_factor_tags"],
                "legacy_12_factor_tags_primary": False,
                "canonical_layer_name_match": CANONICAL_TAXONOMY_LAYERS.get(row["taxonomy_layer_id"]) == row["taxonomy_layer_name"],
                "notes": "8-layer taxonomy is the primary classification; legacy tags are checklist context only.",
            }
        )
    return pd.DataFrame(rows)


def build_factor_definition_usage_boundary_matrix(fixture_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in fixture_rows.to_dict(orient="records"):
        rows.append(
            {
                "factor_id": row["factor_id"],
                "trade_usage": row["trade_usage"],
                "backtestable": _bool(row["backtestable"]),
                "stock_profile_usage": row["stock_profile_usage"],
                "is_live_signal": _bool(row["is_live_signal"]),
                "is_alpha_claim": _bool(row["is_alpha_claim"]),
                "signal_score_component_allowed": _bool(row["signal_score_component_allowed"]),
                "model_training_allowed": _bool(row["model_training_allowed"]),
                "active_weight_allowed": _bool(row["active_weight_allowed"]),
                "active_threshold_allowed": _bool(row["active_threshold_allowed"]),
                "real_buy_review_allowed": _bool(row["real_buy_review_allowed"]),
                "trading_allowed": _bool(row["trading_allowed"]),
                "allowed_downstream_use": _allowed_downstream_use(row),
                "forbidden_interpretation": "Not a live signal, active score, trained weight, active threshold, buy-review input, performance validation, or trading permission.",
            }
        )
    return pd.DataFrame(rows)


def validate_factor_definition_fixture(
    *,
    fixture_rows: pd.DataFrame,
    settings: FactorDefinitionSchemaFixtureSettings,
    output_dir: Path,
) -> pd.DataFrame:
    row_text = " ".join(fixture_rows.fillna("").astype(str).agg(" ".join, axis=1))
    lower_text = row_text.lower()
    checks = [
        ("required_fields_present", set(REQUIRED_FACTOR_DEFINITION_FIELDS).issubset(set(fixture_rows.columns))),
        ("exactly_8_fixture_rows", len(fixture_rows) == 8),
        ("factor_id_non_empty_string", fixture_rows["factor_id"].map(_is_non_empty_string).all()),
        ("factor_version_present", fixture_rows["factor_version"].map(_is_non_empty_string).all()),
        (
            "taxonomy_layer_ids_canonical",
            set(fixture_rows["taxonomy_layer_id"]) == set(CANONICAL_TAXONOMY_LAYERS),
        ),
        (
            "taxonomy_layer_names_match_canonical",
            fixture_rows.apply(
                lambda row: CANONICAL_TAXONOMY_LAYERS.get(row["taxonomy_layer_id"]) == row["taxonomy_layer_name"],
                axis=1,
            ).all(),
        ),
        (
            "taxonomy_layer_names_exclude_known_bad_fragments",
            not any(fragment in row_text for fragment in MOJIBAKE_LAYER_NAME_FRAGMENTS),
        ),
        ("all_8_layers_once", fixture_rows["taxonomy_layer_id"].nunique() == 8 and fixture_rows["taxonomy_layer_id"].is_unique),
        ("taxonomy_primary_classification", True),
        ("legacy_12_tags_checklist_only", fixture_rows["legacy_12_factor_tags"].map(_is_non_empty_string).all()),
        ("factor_kind_valid", fixture_rows["factor_kind"].isin(FACTOR_KINDS).all()),
        ("entity_scope_valid", fixture_rows["entity_scope"].isin(ENTITY_SCOPES).all()),
        (
            "trade_usage_valid_and_non_actionable",
            fixture_rows["trade_usage"].isin(TRADE_USAGE_ALLOWED).all()
            and not fixture_rows["trade_usage"].isin(TRADE_USAGE_FORBIDDEN).any(),
        ),
        ("expected_direction_valid", fixture_rows["expected_direction"].isin(EXPECTED_DIRECTIONS).all()),
        (
            "mixed_direction_rows_have_detail",
            fixture_rows[fixture_rows["expected_direction"].isin({"MIXED_BY_EXPOSURE", "MIXED_BY_REGIME"})][
                "direction_rule_detail"
            ]
            .map(_is_non_empty_string)
            .all(),
        ),
        (
            "risk_veto_not_positive",
            not (
                (fixture_rows["factor_kind"] == "RISK_VETO")
                & (fixture_rows["expected_direction"] == "POSITIVE")
            ).any(),
        ),
        (
            "disclosure_rows_not_direct_action",
            fixture_rows[fixture_rows["taxonomy_layer_id"] == "L6_INFORMATION_DISCLOSURE_SENTIMENT_TRANSMISSION"][
                "trade_usage"
            ]
            .isin({"event_context", "observe_only", "no_trade", "diagnostic_only"})
            .all(),
        ),
        ("source_registry_required_true", fixture_rows["source_registry_required"].map(_bool).all()),
        ("raw_document_store_required_true", fixture_rows["raw_document_store_required"].map(_bool).all()),
        ("available_time_policy_present", fixture_rows["available_time_policy"].map(_is_non_empty_string).all()),
        ("revision_policy_present", fixture_rows["revision_policy"].map(_is_non_empty_string).all()),
        ("compliance_class_present", fixture_rows["compliance_class"].map(_is_non_empty_string).all()),
        ("report_only_true", fixture_rows["report_only"].map(_bool).all()),
        ("diagnostic_only_true", fixture_rows["diagnostic_only"].map(_bool).all()),
        ("is_live_signal_false", fixture_rows["is_live_signal"].map(lambda value: not _bool(value)).all()),
        ("is_alpha_claim_false", fixture_rows["is_alpha_claim"].map(lambda value: not _bool(value)).all()),
        (
            "signal_score_component_allowed_false",
            fixture_rows["signal_score_component_allowed"].map(lambda value: not _bool(value)).all(),
        ),
        ("model_training_allowed_false", fixture_rows["model_training_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_weight_allowed_false", fixture_rows["active_weight_allowed"].map(lambda value: not _bool(value)).all()),
        ("active_threshold_allowed_false", fixture_rows["active_threshold_allowed"].map(lambda value: not _bool(value)).all()),
        ("real_buy_review_allowed_false", fixture_rows["real_buy_review_allowed"].map(lambda value: not _bool(value)).all()),
        ("trading_allowed_false", fixture_rows["trading_allowed"].map(lambda value: not _bool(value)).all()),
        ("no_active_signal_score_formula", not settings.signal_score_formula_active and not settings.signal_score_implemented),
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


def resolve_factor_definition_schema_fixture_paths(output_dir: Path, fixture_id: str) -> dict[str, Path]:
    artifact_dir = output_dir / fixture_id
    return {
        "artifact_dir": artifact_dir,
        "metadata": artifact_dir / "factor_definition_schema_fixture_metadata.json",
        "schema_fields": artifact_dir / "factor_definition_schema_fields.csv",
        "fixture_rows": artifact_dir / "factor_definition_fixture_rows.csv",
        "taxonomy_layer_matrix": artifact_dir / "factor_definition_taxonomy_layer_matrix.csv",
        "usage_boundary_matrix": artifact_dir / "factor_definition_usage_boundary_matrix.csv",
        "validation_summary": artifact_dir / "factor_definition_validation_summary.csv",
        "limitations": artifact_dir / "factor_definition_limitations.md",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def write_factor_definition_schema_fixture_artifacts(
    *,
    result: FactorDefinitionSchemaFixtureResult,
    settings: FactorDefinitionSchemaFixtureSettings,
    schema_fields: pd.DataFrame,
    fixture_rows: pd.DataFrame,
    taxonomy_layer_matrix: pd.DataFrame,
    usage_boundary_matrix: pd.DataFrame,
    validation_summary: pd.DataFrame,
) -> None:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    schema_fields.to_csv(paths["schema_fields"], index=False)
    fixture_rows.to_csv(paths["fixture_rows"], index=False)
    taxonomy_layer_matrix.to_csv(paths["taxonomy_layer_matrix"], index=False)
    usage_boundary_matrix.to_csv(paths["usage_boundary_matrix"], index=False)
    validation_summary.to_csv(paths["validation_summary"], index=False)
    paths["limitations"].write_text(render_factor_definition_limitations(result), encoding="utf-8")
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    paths["metadata"].write_text(json.dumps(_metadata(result, settings), indent=2, ensure_ascii=False), encoding="utf-8")


def render_factor_definition_limitations(result: FactorDefinitionSchemaFixtureResult) -> str:
    return "\n".join(
        [
            "# Factor Definition Schema Fixture Limitations v0.1",
            "",
            "This workflow creates tiny synthetic factor-definition rows for schema and governance review only.",
            "",
            "## Not Created",
            "",
            "- No factor observations are created.",
            "- No event ingestion, company exposure mapping, or replay evidence bundle is created.",
            "- No signal score formula is active.",
            "- No live signals, active weights, active thresholds, stock profile validation, paper validation, buy-review eligibility, performance validation, broker behavior, orders, messages, APIs, or trading are created.",
            "- Legacy factor tags are checklist context only; the 8-layer taxonomy is the primary classification.",
            "",
            "## Current Result",
            "",
            f"- factor_definition_schema_fixture_id: {result.factor_definition_schema_fixture_id}",
            f"- status: {result.status}",
            f"- workflow_stage: {result.workflow_stage}",
            f"- factor_count: {result.factor_count}",
            f"- taxonomy_layer_count: {result.taxonomy_layer_count}",
            f"- validation_issue_count: {result.validation_issue_count}",
        ]
    )


def _metadata(
    result: FactorDefinitionSchemaFixtureResult,
    settings: FactorDefinitionSchemaFixtureSettings,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "factor_definition_schema_fixture_id": result.factor_definition_schema_fixture_id,
        "status": result.status,
        "workflow_stage": result.workflow_stage,
        "config_version": settings.config_version,
        "factor_definition_schema_fixture_created": True,
        "report_only": True,
        "diagnostic_only": True,
        "factor_definition_rows_created": True,
        "factor_count": result.factor_count,
        "taxonomy_layer_count": result.taxonomy_layer_count,
        "taxonomy_primary_classification": True,
        "legacy_12_factor_tags_checklist_only": True,
        "validation_issue_count": result.validation_issue_count,
        "artifact_paths": {key: str(path) for key, path in result.artifact_paths.items()},
    }
    metadata.update({flag: False for flag in FORBIDDEN_METADATA_FALSE_FLAGS})
    return metadata


def _row(**values: Any) -> dict[str, Any]:
    layer_id = values["taxonomy_layer_id"]
    row = {
        "factor_id": "",
        "factor_name": "",
        "factor_version": "factor_definition_schema_fixture_v0.1",
        "taxonomy_layer_id": layer_id,
        "taxonomy_layer_name": CANONICAL_TAXONOMY_LAYERS[layer_id],
        "second_level": "",
        "legacy_12_factor_tags": "",
        "factor_kind": "",
        "entity_scope": "",
        "observation_unit": "",
        "value_type": "",
        "time_horizon": "",
        "impact_path": "",
        "affected_entities_rule": "",
        "expected_direction": "",
        "direction_rule_type": "",
        "direction_rule_detail": "",
        "required_source_types": "",
        "required_document_types": "",
        "required_raw_document_fields": "source_id,available_time,revision_id,source_hash,quality_status",
        "source_registry_required": True,
        "raw_document_store_required": True,
        "calculation_method": "",
        "transformation_method": "",
        "normalization_scope": "",
        "available_time_policy": "available_time must be present and <= replay decision time before downstream use",
        "lag_policy": "explicit lag review required before use",
        "revision_policy": "revision_id and supersession policy required before use",
        "missing_value_policy": "missing values require explicit reviewed handling",
        "quality_rule": "quality_status must be reviewed before downstream use",
        "confidence_rule": "",
        "compliance_class": "REPORT_ONLY_REVIEW_REQUIRED",
        "trade_usage": "diagnostic_only",
        "backtestable": False,
        "stock_profile_usage": "not_allowed_in_v0_1_fixture",
        "is_live_signal": False,
        "is_alpha_claim": False,
        "signal_score_component_allowed": False,
        "model_training_allowed": False,
        "active_weight_allowed": False,
        "active_threshold_allowed": False,
        "real_buy_review_allowed": False,
        "trading_allowed": False,
        "validation_status": "DIAGNOSTIC_ONLY",
        "report_only": True,
        "diagnostic_only": True,
        "schema_version": "factor_definition_schema_fixture_v0.1",
        "created_by_workflow": "factor-definition-schema-fixture",
    }
    row.update(values)
    return row


def _assert_settings_safe(settings: FactorDefinitionSchemaFixtureSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Factor definition schema fixture must remain report_only and diagnostic_only.")
    enabled = [flag for flag in FORBIDDEN_METADATA_FALSE_FLAGS if getattr(settings, flag)]
    if enabled:
        raise ValueError(f"Unsafe factor definition fixture settings enabled: {', '.join(enabled)}")


def _fixture_id(fixture_rows: pd.DataFrame, config_version: str) -> str:
    digest = hashlib.sha256(config_version.encode("utf-8"))
    digest.update("|".join(REQUIRED_FACTOR_DEFINITION_FIELDS).encode("utf-8"))
    digest.update(fixture_rows.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()[:12]


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Factor Definition Schema Fixture Views Report-Only v0.1",
            "",
            "Add index, health, and status artifact views for this report-only factor definition schema fixture. Keep the workflow synthetic and do not create factor observations, event ingestion, company exposure mappings, replay evidence bundles, signal score implementation, model training, active weights, active thresholds, stock profile validation, paper validation, buy-review eligibility, performance validation, or trading permission.",
        ]
    )


def _field_description(field: str) -> str:
    descriptions = {
        "factor_id": "Stable synthetic factor definition identifier.",
        "factor_version": "Version of the factor definition rule.",
        "taxonomy_layer_id": "Canonical 8-layer taxonomy identifier.",
        "taxonomy_layer_name": "Canonical layer display name supplied by the task.",
        "legacy_12_factor_tags": "Checklist-only legacy tags; not primary classification.",
        "source_registry_required": "Must be true before downstream use.",
        "raw_document_store_required": "Must be true before downstream use.",
        "available_time_policy": "PIT availability rule for future observations.",
        "revision_policy": "Revision and supersession rule for future observations.",
        "trade_usage": "Non-actionable research/governance usage category.",
        "report_only": "Must be true for this workflow.",
        "diagnostic_only": "Must be true for this workflow.",
    }
    return descriptions.get(field, "Factor definition schema fixture field.")


def _data_type_hint(field: str) -> str:
    if field in {
        "source_registry_required",
        "raw_document_store_required",
        "backtestable",
        "is_live_signal",
        "is_alpha_claim",
        "signal_score_component_allowed",
        "model_training_allowed",
        "active_weight_allowed",
        "active_threshold_allowed",
        "real_buy_review_allowed",
        "trading_allowed",
        "report_only",
        "diagnostic_only",
    }:
        return "boolean"
    return "string"


def _allowed_downstream_use(row: dict[str, Any]) -> str:
    if row["factor_kind"] == "RISK_VETO":
        return "review_blocker_context_only"
    if row["trade_usage"] in {"research_feature", "event_context", "market_confirmation"}:
        return "research_schema_reference_only"
    return "observe_only"


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


def _is_non_empty_string(value: Any) -> bool:
    return bool(_text(value))


def _contains_secret_like(text: str) -> bool:
    return bool(re.search(r"(api[_-]?key|access[_-]?token|secret|password|bearer\s+[a-z0-9])", text))
