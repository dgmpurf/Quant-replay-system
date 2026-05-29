"""Configuration loading for the replay system."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal

import yaml
from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    name: str
    timezone: str = "Asia/Shanghai"
    market: str = "China A-share"


class DataSettings(BaseModel):
    root: Path = Path("data")
    mock_prices: Path = Path("data/mock/prices.csv")
    mock_universe_snapshots: Path = Path("data/mock/universe_snapshots.csv")
    mock_corporate_actions: Path = Path("data/mock/corporate_actions.csv")
    mock_trading_calendar: Path = Path("data/mock/trading_calendar.csv")


class OutputSettings(BaseModel):
    root: Path = Path("outputs")
    reports: Path = Path("outputs/reports")


class ScoringSettings(BaseModel):
    weights: Dict[str, float] = Field(default_factory=dict)
    min_score: float = 0.0
    max_candidates: int = Field(default=5, gt=0)


class FactorDatasetSettings(BaseModel):
    exclude_st: bool = True
    exclude_suspended: bool = True
    require_market_data: bool = True
    include_technical_score: bool = True


class ScoreEngineSettings(BaseModel):
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "reality_score": 0.35,
            "technical_score": 0.25,
            "expectation_score": 0.15,
            "liquidity_score": 0.10,
            "sentiment_score": 0.05,
            "risk_penalty": 0.25,
        }
    )
    reality_score_default: float = 50.0
    sentiment_score_default: float = 50.0
    technical_score_default: float = 50.0
    expectation_score_default: float = 50.0
    liquidity_score_default: float = 0.0
    rsi_overheat_threshold: float = 80.0
    hard_block_st: bool = True
    hard_block_suspended: bool = True
    hard_block_missing_market: bool = True
    hard_block_limit_up: bool = True


class CandidateSelectionSettings(BaseModel):
    top_n: int = Field(default=5, gt=0)
    min_action: str = "PAPER_TRADE"
    min_final_score: float | None = None
    exclude_blocked: bool = True


class CurrentCandidateSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/current_candidates")
    default_top_n: int = Field(default=10, gt=0)
    min_final_score: float | None = 70.0
    min_action: str = "PAPER_TRADE"
    selection_profile: Literal["default", "demo"] = "default"
    enable_snapshot_quality_preflight: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalAdvisorySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/signals")
    default_validity_days: int = Field(default=1, ge=0)
    medium_confidence_score: float = Field(default=60.0, ge=0, le=100)
    high_confidence_score: float = Field(default=80.0, ge=0, le=100)
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_alert_delivery: Literal[False] = False
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    auto_order_allowed: Literal[False] = False


class SignalSemanticsSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/signal_semantics")
    reviewed_buy_min_score: float = Field(default=70.0, ge=0, le=100)
    watch_min_score: float = Field(default=55.0, ge=0, le=100)
    require_snapshot_quality_pass: bool = True
    require_data_quality_pass: bool = True
    allow_review_buy_for_demo: bool = False
    allow_auto_order: Literal[False] = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    enable_message_delivery: Literal[False] = False


class SignalSemanticsIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/signal_semantics")
    output_dir: Path = Path("outputs/reports/signal_semantics/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalSemanticsHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/signal_semantics/index/signal_semantics_index.csv")
    root_dir: Path = Path("outputs/reports/signal_semantics")
    output_dir: Path = Path("outputs/reports/signal_semantics/health")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalSemanticsStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/signal_semantics")
    output_dir: Path = Path("outputs/reports/signal_semantics/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryProfileCalibrationSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/advisory_profile_calibration")
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    enable_message_delivery: Literal[False] = False
    auto_order_allowed: Literal[False] = False


class AdvisoryProfileCalibrationIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/advisory_profile_calibration")
    output_dir: Path = Path("outputs/reports/advisory_profile_calibration/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryProfileCalibrationHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/advisory_profile_calibration/index/advisory_profile_calibration_index.csv")
    root_dir: Path = Path("outputs/reports/advisory_profile_calibration")
    output_dir: Path = Path("outputs/reports/advisory_profile_calibration/health")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryProfileCalibrationStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/advisory_profile_calibration")
    output_dir: Path = Path("outputs/reports/advisory_profile_calibration/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalAdvisoryIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/signals")
    output_dir: Path = Path("outputs/reports/signals/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalAdvisoryHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/signals/index/signal_advisory_index.csv")
    root_dir: Path = Path("outputs/reports/signals")
    output_dir: Path = Path("outputs/reports/signals/health")
    strict: bool = False
    require_alert_preview: bool = True
    missing_alert_preview_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SignalAdvisoryStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/signals")
    output_dir: Path = Path("outputs/reports/signals/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisorySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/single_symbol_advisory")
    answer_output_dir: Path = Path("outputs/reports/single_symbol_advisory_answer")
    default_validity_days: int = Field(default=1, ge=0)
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_alert_delivery: Literal[False] = False
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    auto_order_allowed: Literal[False] = False


class SingleSymbolAdvisoryIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/single_symbol_advisory")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisoryHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/single_symbol_advisory/index/single_symbol_advisory_index.csv")
    root_dir: Path = Path("outputs/reports/single_symbol_advisory")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory/health")
    strict: bool = False
    require_alert_preview: bool = True
    missing_alert_preview_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisoryStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/single_symbol_advisory")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisoryAnswerIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/single_symbol_advisory_answer")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory_answer/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisoryAnswerHealthSettings(BaseModel):
    index_path: Path = Path(
        "outputs/reports/single_symbol_advisory_answer/index/single_symbol_advisory_answer_index.csv"
    )
    root_dir: Path = Path("outputs/reports/single_symbol_advisory_answer")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory_answer/health")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SingleSymbolAdvisoryAnswerStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/single_symbol_advisory_answer")
    output_dir: Path = Path("outputs/reports/single_symbol_advisory_answer/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryConversationSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/advisory_conversation")
    answer_style: Literal["concise", "detailed"] = "concise"
    parser_type: str = "deterministic_rule_based"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    enable_message_delivery: Literal[False] = False
    enable_llm_api: Literal[False] = False
    auto_order_allowed: Literal[False] = False


class AdvisoryConversationIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/advisory_conversation")
    output_dir: Path = Path("outputs/reports/advisory_conversation/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryConversationHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/advisory_conversation/index/advisory_conversation_index.csv")
    root_dir: Path = Path("outputs/reports/advisory_conversation")
    output_dir: Path = Path("outputs/reports/advisory_conversation/health")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class AdvisoryConversationStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/advisory_conversation")
    output_dir: Path = Path("outputs/reports/advisory_conversation/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class CurrentCandidateArtifactIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/current_candidates")
    output_dir: Path = Path("outputs/reports/current_candidates/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class CurrentCandidateArtifactHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/current_candidates/index/current_candidate_artifact_index.csv")
    root_dir: Path = Path("outputs/reports/current_candidates")
    output_dir: Path = Path("outputs/reports/current_candidates/health")
    strict: bool = False
    empty_candidates_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_metadata_field_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class CurrentToPaperHandoffSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/current_to_paper_handoff")
    require_health_pass: bool = True
    allow_health_warn: bool = False
    prefer_latest: bool = True
    default_paper_date_from_decision_date: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class CurrentToPaperReviewHandoffSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/current_to_paper_review_handoff")
    default_reviewer_id: str = ""
    default_manual_review_status: Literal["PENDING_REVIEW"] = "PENDING_REVIEW"
    include_suggested_status: bool = True
    auto_approve_above_score: float | None = None
    auto_reject_below_score: float | None = None
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class ReplayRunSettings(BaseModel):
    default_top_n: int = Field(default=5, gt=0)
    default_holding_horizon: int = Field(default=10, gt=0)
    output_dir: Path = Path("outputs/reports")
    min_action: str = "PAPER_TRADE"
    min_final_score: float | None = 70.0
    config_version: str = "mvp"
    write_artifacts: bool = True


class BatchReplaySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/batch_replays")
    skip_non_trading_days: bool = True
    fail_fast: bool = False
    default_top_n: int = Field(default=5, gt=0)
    default_holding_horizon: int = Field(default=10, gt=0)
    enable_portfolio_simulation: bool = True
    portfolio_initial_cash: float = Field(default=10_000.0, gt=0)
    portfolio_max_gross_exposure: float = Field(default=0.60, ge=0, le=1)
    portfolio_max_position_weight: float = Field(default=0.20, ge=0, le=1)
    portfolio_reserve_cash_pct: float = Field(default=0.40, ge=0, le=1)
    config_version: str = "mvp"
    write_artifacts: bool = True


class CalibrationSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/calibrations")
    default_top_n_values: list[int] = Field(default_factory=lambda: [3, 5])
    default_holding_horizon_values: list[int] = Field(default_factory=lambda: [3, 5])
    default_min_final_score_values: list[float | None] = Field(default_factory=lambda: [60.0, 70.0])
    default_min_action: str = "PAPER_TRADE"
    min_trade_count: int = Field(default=3, ge=0)
    max_parameter_sets: int = Field(default=40, gt=0)
    use_portfolio_metrics: bool = True
    objective_metric_mode: Literal["trade_level", "portfolio_aware"] = "portfolio_aware"
    config_version: str = "mvp"
    write_artifacts: bool = True


class PortfolioSimulationSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/portfolio_simulations")
    initial_cash: float = Field(default=10_000.0, gt=0)
    max_gross_exposure: float = Field(default=0.60, ge=0, le=1)
    max_position_weight: float = Field(default=0.20, ge=0, le=1)
    sizing_method: Literal["equal_weight"] = "equal_weight"
    round_lots: bool = True
    lot_size: int = Field(default=100, gt=0)
    allow_fractional_shares: bool = False
    reserve_cash_pct: float = Field(default=0.40, ge=0, le=1)
    commission_bps: float = Field(default=0.0, ge=0)
    min_commission: float = Field(default=0.0, ge=0)
    slippage_bps: float = Field(default=0.0, ge=0)
    tax_bps: float = Field(default=0.0, ge=0)
    allow_reinvestment: bool = True
    mark_to_market: bool = True
    allow_negative_cash: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True


class WalkForwardSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/walk_forward")
    require_validation: bool = True
    require_test: bool = False
    overfit_warning_threshold: float = Field(default=0.50, ge=0, le=1)
    severe_overfit_threshold: float = Field(default=0.75, ge=0, le=1)
    min_train_dates: int = Field(default=3, ge=0)
    min_validation_dates: int = Field(default=1, ge=0)
    min_test_dates: int = Field(default=0, ge=0)
    config_version: str = "mvp"
    write_artifacts: bool = True


class PaperTradingSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/paper_trading")
    initial_paper_cash: float = Field(default=10_000.0, gt=0)
    default_lot_size: int = Field(default=100, gt=0)
    round_lots: bool = True
    allow_fractional_shares: bool = False
    allow_short_selling: bool = False
    require_approved_decision_for_fills: bool = True
    prevent_negative_cash: bool = True
    default_fee_bps: float = Field(default=0.0, ge=0)
    default_slippage_bps: float = Field(default=0.0, ge=0)
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False
    fail_daily_report_on_reconciliation_error: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True


class PaperReconciliationSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/paper_trading/reconciliation")
    duplicate_fill_id_severity: Literal["WARN", "ERROR"] = "WARN"
    negative_cash_severity: Literal["WARN", "ERROR"] = "ERROR"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class PaperReviewSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/paper_trading/reviews")
    allow_pending_reviews: bool = True
    enable_template_health_check: bool = False
    require_template_health_pass: bool = False
    allow_template_health_warn: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class PaperReviewTemplateHealthSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/paper_trading/review_template_health")
    duplicate_update_severity: Literal["WARN", "ERROR"] = "ERROR"
    invalid_reason_code_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_reviewer_severity: Literal["INFO", "WARN", "ERROR"] = "WARN"
    blank_status_severity: Literal["WARN", "ERROR"] = "ERROR"
    approve_non_pass_risk_severity: Literal["WARN", "ERROR"] = "WARN"
    low_score_approval_threshold: float = 70.0
    low_score_approval_severity: Literal["INFO", "WARN", "ERROR"] = "WARN"
    high_score_threshold: float = 80.0
    rejected_high_score_severity: Literal["INFO", "WARN"] = "INFO"
    watch_high_score_severity: Literal["INFO", "WARN"] = "INFO"
    require_decisions_for_id_validation: bool = False
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DailyPaperRunnerSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/paper_trading/daily")
    error_on_both_candidates_and_reviewed_decisions: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class PaperArtifactIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/paper_trading")
    output_dir: Path = Path("outputs/reports/paper_trading/index")
    include_missing_metadata: bool = False
    artifact_type: Literal["daily", "review", "reconciliation", "all"] = "all"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class PaperArtifactHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/paper_trading/index/paper_artifact_index.csv")
    root_dir: Path = Path("outputs/reports/paper_trading")
    output_dir: Path = Path("outputs/reports/paper_trading/health")
    strict: bool = False
    empty_csv_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_metadata_field_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class PaperWorkflowStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports")
    current_candidates_root: Path = Path("outputs/reports/current_candidates")
    paper_trading_root: Path = Path("outputs/reports/paper_trading")
    output_dir: Path = Path("outputs/reports/paper_trading/workflow_status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataSourceSettings(BaseModel):
    default_source: str = "LOCAL_CSV"
    raw_output_dir: Path = Path("data/raw")
    allow_network_sources: bool = False
    allow_real_data_fetch: bool = False
    require_manual_real_data_flag: bool = True
    akshare_market_stock_fallback_order: list[str] = Field(
        default_factory=lambda: ["TENCENT", "SINA", "EASTMONEY"]
    )
    akshare_market_etf_fallback_order: list[str] = Field(default_factory=lambda: ["SINA", "EASTMONEY"])
    akshare_market_index_fallback_order: list[str] = Field(
        default_factory=lambda: ["SINA", "TENCENT", "EASTMONEY"]
    )
    akshare_market_retry_count: int = Field(default=1, ge=0)
    akshare_market_retry_sleep_seconds: float = Field(default=0.0, ge=0)
    akshare_market_enable_curl_cffi_fallback: bool = True
    akshare_market_curl_cffi_impersonate: str = "chrome"
    default_revision_id: str = "v1"
    default_source_name: str = "LOCAL_CSV"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataSourceHealthSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/data_source_health")
    check_individual_akshare_upstreams: bool = True
    fail_empty_result: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketDataCacheSettings(BaseModel):
    cache_path: Path = Path("data/cache/market/daily_bars.csv")
    output_dir: Path = Path("outputs/reports/market_data_cache")
    duplicate_policy: Literal["keep_latest"] = "keep_latest"
    require_available_time: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_cache_export")
    export_output_dir: Path = Path("data/raw/manual_cache_exports")
    manifest_output_dir: Path = Path("data/raw/manual_manifests")
    default_required_fields: list[str] = Field(default_factory=lambda: ["close", "volume", "amount"])
    require_explicit_source: bool = True
    reject_duplicate_business_keys: bool = True
    fail_fast: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportPolicySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_cache_export_policy")
    manifest_output_dir: Path = Path("data/raw/manual_manifests")
    default_required_fields: list[str] = Field(default_factory=lambda: ["close", "volume", "amount"])
    source_preference: dict[str, list[list[str]]] = Field(
        default_factory=lambda: {
            "STOCK": [
                ["AKSHARE_OPTIONAL", "TENCENT"],
                ["BAOSTOCK_OPTIONAL", "BAOSTOCK"],
            ],
            "ETF": [
                ["AKSHARE_OPTIONAL", "SINA"],
            ],
        }
    )
    require_comparison_for_reliable_stock: bool = False
    comparison_reference_preference: dict[str, list[list[str]]] = Field(
        default_factory=lambda: {
            "STOCK": [
                ["BAOSTOCK_OPTIONAL", "BAOSTOCK"],
                ["AKSHARE_OPTIONAL", "TENCENT"],
            ],
            "ETF": [
                ["BAOSTOCK_OPTIONAL", "BAOSTOCK"],
            ],
        }
    )
    strict_reliable: bool = False
    fail_fast: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportPolicyIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_cache_export_policy")
    output_dir: Path = Path("outputs/reports/market_cache_export_policy/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportPolicyHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/market_cache_export_policy/index/market_cache_export_policy_index.csv")
    root_dir: Path = Path("outputs/reports/market_cache_export_policy")
    output_dir: Path = Path("outputs/reports/market_cache_export_policy/health")
    strict: bool = False
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportPolicyStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_cache_export_policy")
    output_dir: Path = Path("outputs/reports/market_cache_export_policy/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_cache_export")
    output_dir: Path = Path("outputs/reports/market_cache_export/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/market_cache_export/index/market_cache_export_index.csv")
    root_dir: Path = Path("outputs/reports/market_cache_export")
    output_dir: Path = Path("outputs/reports/market_cache_export/health")
    strict: bool = False
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_linked_artifact_severity: Literal["WARN", "ERROR"] = "ERROR"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCacheExportStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_cache_export")
    output_dir: Path = Path("outputs/reports/market_cache_export/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketDataComparisonSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_data_comparison")
    price_abs_tolerance: float = Field(default=0.0001, ge=0)
    price_pct_tolerance: float = Field(default=0.001, ge=0)
    volume_pct_tolerance: float = Field(default=0.05, ge=0)
    amount_pct_tolerance: float = Field(default=0.05, ge=0)
    unit_ratio_stability_tolerance: float = Field(default=0.05, ge=0)
    unit_ratio_far_from_one_tolerance: float = Field(default=0.05, ge=0)
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


def _default_market_source_field_reliability() -> dict[str, Any]:
    return {
        "AKSHARE_OPTIONAL": {
            "TENCENT": {
                "STOCK": {
                    "open": "RELIABLE",
                    "high": "RELIABLE",
                    "low": "RELIABLE",
                    "close": "RELIABLE",
                    "volume": "RELIABLE",
                    "amount": "RELIABLE",
                    "pre_close": "CAVEAT_FIRST_WINDOW_ROW",
                    "notes": [
                        "Requires raw Tencent turnover extraction path for amount.",
                        "AKShare stock_zh_a_hist_tx DataFrame amount field is volume in hands, not turnover amount.",
                    ],
                }
            },
            "SINA": {
                "ETF": {
                    "open": "PROVISIONAL",
                    "high": "PROVISIONAL",
                    "low": "PROVISIONAL",
                    "close": "PROVISIONAL",
                    "volume": "PROVISIONAL",
                    "amount": "PROVISIONAL",
                    "pre_close": "UNKNOWN",
                    "notes": [
                        "ETF data is available locally but lacks second-source comparison in current tests.",
                    ],
                }
            },
            "EASTMONEY": {
                "STOCK": {
                    "open": "UNSTABLE",
                    "high": "UNSTABLE",
                    "low": "UNSTABLE",
                    "close": "UNSTABLE",
                    "volume": "UNSTABLE",
                    "amount": "UNSTABLE",
                    "pre_close": "UNSTABLE",
                    "notes": [
                        "Eastmoney market endpoints were unstable in local diagnostics.",
                    ],
                }
            },
        },
        "BAOSTOCK_OPTIONAL": {
            "BAOSTOCK": {
                "STOCK": {
                    "open": "RELIABLE",
                    "high": "RELIABLE",
                    "low": "RELIABLE",
                    "close": "RELIABLE",
                    "volume": "RELIABLE",
                    "amount": "RELIABLE",
                    "pre_close": "CAVEAT_FIRST_WINDOW_ROW",
                    "notes": [
                        "Stock OHLC, volume, and amount aligned with AKShare/Tencent in representative comparisons.",
                    ],
                },
                "ETF": {
                    "open": "UNAVAILABLE",
                    "high": "UNAVAILABLE",
                    "low": "UNAVAILABLE",
                    "close": "UNAVAILABLE",
                    "volume": "UNAVAILABLE",
                    "amount": "UNAVAILABLE",
                    "pre_close": "UNAVAILABLE",
                    "notes": [
                        "BaoStock returned 0 rows for 510300 and 159915 in current local tests.",
                    ],
                },
            }
        },
    }


class MarketSourcePolicySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_source_policy")
    field_reliability: dict[str, Any] = Field(default_factory=_default_market_source_field_reliability)
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketCachePreflightSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_cache_preflight")
    default_required_fields: list[str] = Field(default_factory=lambda: ["close", "volume", "amount"])
    require_available_time: bool = True
    strict_provisional: bool = False
    unstable_policy_action: Literal["WARN_ACCEPT", "REJECT"] = "WARN_ACCEPT"
    reject_on_comparison_fail: bool = True
    allow_first_window_pre_close_caveat: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketDailyUpdateSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_daily_update")
    default_required_fields: list[str] = Field(default_factory=lambda: ["close", "volume", "amount"])
    run_health_check: bool = True
    run_cache_status: bool = True
    default_dry_run: bool = True
    fail_fast: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class HistoricalBackfillSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/historical_backfill")
    default_required_fields: list[str] = Field(default_factory=lambda: ["close", "volume", "amount"])
    run_health_check: bool = True
    default_dry_run: bool = True
    fail_fast: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class HistoricalBackfillIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/historical_backfill")
    output_dir: Path = Path("outputs/reports/historical_backfill/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class HistoricalBackfillHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/historical_backfill/index/historical_backfill_index.csv")
    root_dir: Path = Path("outputs/reports/historical_backfill")
    output_dir: Path = Path("outputs/reports/historical_backfill/health")
    strict: bool = False
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_manifest_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class HistoricalBackfillStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/historical_backfill")
    output_dir: Path = Path("outputs/reports/historical_backfill/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketUpdateHandoffSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/market_update_handoff")
    batch_output_dir: Path = Path("data/raw/manual_update_batches")
    manifest_output_dir: Path = Path("data/raw/manual_manifests")
    include_warn_accept: bool = True
    run_pipeline_validation: bool = True
    default_top_n: int = 5
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketUpdateHandoffIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_update_handoff")
    output_dir: Path = Path("outputs/reports/market_update_handoff/index")
    include_missing_metadata: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketUpdateHandoffHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/market_update_handoff/index/market_update_handoff_index.csv")
    root_dir: Path = Path("outputs/reports/market_update_handoff")
    output_dir: Path = Path("outputs/reports/market_update_handoff/health")
    strict: bool = False
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_linked_artifact_severity: Literal["WARN", "ERROR"] = "ERROR"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class MarketUpdateHandoffStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports/market_update_handoff")
    output_dir: Path = Path("outputs/reports/market_update_handoff/status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataPipelineSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/data_pipeline")
    raw_output_dir: Path = Path("data/raw")
    processed_output_dir: Path = Path("data/processed")
    snapshot_output_dir: Path = Path("data/snapshots")
    run_data_quality: bool = True
    build_snapshot_manifest: bool = True
    fail_on_ingestion_error: bool = True
    fail_on_data_quality_fail: bool = False
    allow_data_quality_warn: bool = True
    allow_real_data: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class UniverseOverlaySettings(BaseModel):
    output_dir: Path = Path("data/raw/LOCAL_CSV/universe_overlay")
    allow_override_existing: bool = False
    duplicate_overlay_symbol_severity: Literal["ERROR"] = "ERROR"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataPreparationArtifactIndexSettings(BaseModel):
    root_dir: Path = Path("outputs/reports")
    output_dir: Path = Path("outputs/reports/data_preparation/index")
    include_missing_metadata: bool = False
    artifact_type: Literal["data_pipeline", "data_quality", "snapshot_quality", "current_candidates", "all"] = "all"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataPreparationArtifactHealthSettings(BaseModel):
    index_path: Path = Path("outputs/reports/data_preparation/index/data_preparation_artifact_index.csv")
    root_dir: Path = Path("outputs/reports")
    output_dir: Path = Path("outputs/reports/data_preparation/health")
    strict: bool = False
    empty_candidates_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_no_live_statement_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_metadata_field_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_optional_field_severity: Literal["INFO", "WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataPreparationWorkflowStatusSettings(BaseModel):
    root_dir: Path = Path("outputs/reports")
    data_pipeline_root: Path = Path("outputs/reports/data_pipeline")
    data_quality_root: Path = Path("outputs/reports/data_quality")
    snapshot_quality_root: Path = Path("outputs/reports/snapshot_quality")
    current_candidates_root: Path = Path("outputs/reports/current_candidates")
    output_dir: Path = Path("outputs/reports/data_preparation/workflow_status")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class LocalResearchDashboardSettings(BaseModel):
    root_dir: Path = Path("outputs/reports")
    historical_backfill_root: Path = Path("outputs/reports/historical_backfill")
    market_cache_export_policy_root: Path = Path("outputs/reports/market_cache_export_policy")
    market_cache_export_root: Path = Path("outputs/reports/market_cache_export")
    data_preparation_root: Path = Path("outputs/reports/data_preparation")
    current_candidates_root: Path = Path("outputs/reports/current_candidates")
    current_candidates_backfill_plan_root: Path = Path("outputs/reports/current_candidates_backfill_plan")
    current_candidates_backfill_execution_manifest_root: Path = Path(
        "outputs/reports/current_candidates_backfill_execution_manifest"
    )
    point_in_time_universe_overlay_plan_root: Path = Path("outputs/reports/point_in_time_universe_overlay_plan")
    point_in_time_universe_overlay_review_root: Path = Path("outputs/reports/point_in_time_universe_overlay_review")
    advisory_profile_calibration_root: Path = Path("outputs/reports/advisory_profile_calibration")
    signal_semantics_root: Path = Path("outputs/reports/signal_semantics")
    signal_advisory_root: Path = Path("outputs/reports/signals")
    single_symbol_advisory_root: Path = Path("outputs/reports/single_symbol_advisory")
    single_symbol_advisory_answer_root: Path = Path("outputs/reports/single_symbol_advisory_answer")
    advisory_conversation_root: Path = Path("outputs/reports/advisory_conversation")
    market_update_handoff_root: Path = Path("outputs/reports/market_update_handoff")
    paper_trading_root: Path = Path("outputs/reports/paper_trading")
    output_dir: Path = Path("outputs/reports/local_research_dashboard")
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataIngestionSettings(BaseModel):
    output_dir: Path = Path("data/processed")
    snapshot_dir: Path = Path("data/snapshots")
    allow_default_available_time: bool = True
    allow_default_corporate_action_available_time: bool = False
    default_source: str = "LOCAL_CSV"
    default_revision_id: str = "v1"
    exchange_timezone: str = "Asia/Shanghai"
    duplicate_key_severity: Literal["WARN", "ERROR"] = "WARN"
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class DataQualitySettings(BaseModel):
    output_dir: Path = Path("outputs/reports/data_quality")
    duplicate_key_severity: Literal["WARN", "ERROR"] = "WARN"
    missing_available_time_severity: Literal["WARN", "ERROR"] = "ERROR"
    missing_source_revision_severity: Literal["WARN", "ERROR"] = "WARN"
    suspicious_available_time_severity: Literal["INFO", "WARN", "ERROR"] = "WARN"
    strict: bool = False
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SnapshotQualityGateSettings(BaseModel):
    output_dir: Path = Path("outputs/reports/snapshot_quality")
    required_datasets: list[str] = Field(default_factory=lambda: ["market", "universe", "trading_calendar"])
    optional_datasets: list[str] = Field(default_factory=lambda: ["benchmark", "corporate_actions"])
    fail_on_required_dataset_warn: bool = False
    fail_on_optional_dataset_fail: bool = False
    allow_missing_optional_datasets: bool = True
    missing_optional_dataset_severity: Literal["INFO", "WARN"] = "INFO"
    block_replay_on_fail: bool = True
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class SnapshotQualityPreflightSettings(BaseModel):
    enabled: bool = False
    manifest_path: Path | None = None
    block_on_fail: bool = True
    block_on_warn: bool = False
    attach_report_paths: bool = True
    config_version: str = "mvp"
    enable_live_trading: Literal[False] = False
    enable_broker_api: Literal[False] = False


class ExecutionSettings(BaseModel):
    mode: Literal["t_plus_1"] = "t_plus_1"
    price_field: str = "open"
    slippage_bps: float = 0.0
    max_exit_delay_trading_days: int = Field(default=5, ge=0)
    block_buy_on_limit_up: bool = True
    block_sell_on_limit_down: bool = True
    default_slippage_bps: float = 10.0
    default_holding_horizon_trading_days: int = Field(default=1, gt=0)


class RiskSettings(BaseModel):
    max_single_position_pct: float = Field(default=0.20, gt=0, le=1)
    max_drawdown_stop_pct: float = Field(default=0.12, gt=0, le=1)
    allow_live_trading: Literal[False] = False


class Settings(BaseModel):
    project: ProjectSettings
    data: DataSettings
    output: OutputSettings
    scoring: ScoringSettings
    factor_dataset: FactorDatasetSettings = Field(default_factory=FactorDatasetSettings)
    score_engine: ScoreEngineSettings = Field(default_factory=ScoreEngineSettings)
    candidate_selection: CandidateSelectionSettings = Field(default_factory=CandidateSelectionSettings)
    current_candidates: CurrentCandidateSettings = Field(default_factory=CurrentCandidateSettings)
    signal_advisory: SignalAdvisorySettings = Field(default_factory=SignalAdvisorySettings)
    signal_semantics: SignalSemanticsSettings = Field(default_factory=SignalSemanticsSettings)
    signal_semantics_index: SignalSemanticsIndexSettings = Field(default_factory=SignalSemanticsIndexSettings)
    signal_semantics_health: SignalSemanticsHealthSettings = Field(default_factory=SignalSemanticsHealthSettings)
    signal_semantics_status: SignalSemanticsStatusSettings = Field(default_factory=SignalSemanticsStatusSettings)
    advisory_profile_calibration: AdvisoryProfileCalibrationSettings = Field(
        default_factory=AdvisoryProfileCalibrationSettings
    )
    advisory_profile_calibration_index: AdvisoryProfileCalibrationIndexSettings = Field(
        default_factory=AdvisoryProfileCalibrationIndexSettings
    )
    advisory_profile_calibration_health: AdvisoryProfileCalibrationHealthSettings = Field(
        default_factory=AdvisoryProfileCalibrationHealthSettings
    )
    advisory_profile_calibration_status: AdvisoryProfileCalibrationStatusSettings = Field(
        default_factory=AdvisoryProfileCalibrationStatusSettings
    )
    signal_advisory_index: SignalAdvisoryIndexSettings = Field(default_factory=SignalAdvisoryIndexSettings)
    signal_advisory_health: SignalAdvisoryHealthSettings = Field(default_factory=SignalAdvisoryHealthSettings)
    signal_advisory_status: SignalAdvisoryStatusSettings = Field(default_factory=SignalAdvisoryStatusSettings)
    single_symbol_advisory: SingleSymbolAdvisorySettings = Field(default_factory=SingleSymbolAdvisorySettings)
    single_symbol_advisory_index: SingleSymbolAdvisoryIndexSettings = Field(default_factory=SingleSymbolAdvisoryIndexSettings)
    single_symbol_advisory_health: SingleSymbolAdvisoryHealthSettings = Field(default_factory=SingleSymbolAdvisoryHealthSettings)
    single_symbol_advisory_status: SingleSymbolAdvisoryStatusSettings = Field(default_factory=SingleSymbolAdvisoryStatusSettings)
    single_symbol_advisory_answer_index: SingleSymbolAdvisoryAnswerIndexSettings = Field(default_factory=SingleSymbolAdvisoryAnswerIndexSettings)
    single_symbol_advisory_answer_health: SingleSymbolAdvisoryAnswerHealthSettings = Field(default_factory=SingleSymbolAdvisoryAnswerHealthSettings)
    single_symbol_advisory_answer_status: SingleSymbolAdvisoryAnswerStatusSettings = Field(default_factory=SingleSymbolAdvisoryAnswerStatusSettings)
    advisory_conversation: AdvisoryConversationSettings = Field(default_factory=AdvisoryConversationSettings)
    advisory_conversation_index: AdvisoryConversationIndexSettings = Field(default_factory=AdvisoryConversationIndexSettings)
    advisory_conversation_health: AdvisoryConversationHealthSettings = Field(default_factory=AdvisoryConversationHealthSettings)
    advisory_conversation_status: AdvisoryConversationStatusSettings = Field(default_factory=AdvisoryConversationStatusSettings)
    current_candidate_artifact_index: CurrentCandidateArtifactIndexSettings = Field(default_factory=CurrentCandidateArtifactIndexSettings)
    current_candidate_artifact_health: CurrentCandidateArtifactHealthSettings = Field(default_factory=CurrentCandidateArtifactHealthSettings)
    current_to_paper_handoff: CurrentToPaperHandoffSettings = Field(default_factory=CurrentToPaperHandoffSettings)
    current_to_paper_review_handoff: CurrentToPaperReviewHandoffSettings = Field(default_factory=CurrentToPaperReviewHandoffSettings)
    replay_run: ReplayRunSettings = Field(default_factory=ReplayRunSettings)
    batch_replay: BatchReplaySettings = Field(default_factory=BatchReplaySettings)
    calibration: CalibrationSettings = Field(default_factory=CalibrationSettings)
    portfolio_simulation: PortfolioSimulationSettings = Field(default_factory=PortfolioSimulationSettings)
    walk_forward: WalkForwardSettings = Field(default_factory=WalkForwardSettings)
    paper_trading: PaperTradingSettings = Field(default_factory=PaperTradingSettings)
    paper_reconciliation: PaperReconciliationSettings = Field(default_factory=PaperReconciliationSettings)
    paper_review: PaperReviewSettings = Field(default_factory=PaperReviewSettings)
    paper_review_template_health: PaperReviewTemplateHealthSettings = Field(default_factory=PaperReviewTemplateHealthSettings)
    daily_paper_runner: DailyPaperRunnerSettings = Field(default_factory=DailyPaperRunnerSettings)
    paper_artifact_index: PaperArtifactIndexSettings = Field(default_factory=PaperArtifactIndexSettings)
    paper_artifact_health: PaperArtifactHealthSettings = Field(default_factory=PaperArtifactHealthSettings)
    paper_workflow_status: PaperWorkflowStatusSettings = Field(default_factory=PaperWorkflowStatusSettings)
    data_sources: DataSourceSettings = Field(default_factory=DataSourceSettings)
    data_source_health: DataSourceHealthSettings = Field(default_factory=DataSourceHealthSettings)
    market_data_cache: MarketDataCacheSettings = Field(default_factory=MarketDataCacheSettings)
    market_cache_export: MarketCacheExportSettings = Field(default_factory=MarketCacheExportSettings)
    market_cache_export_policy: MarketCacheExportPolicySettings = Field(default_factory=MarketCacheExportPolicySettings)
    market_cache_export_policy_index: MarketCacheExportPolicyIndexSettings = Field(default_factory=MarketCacheExportPolicyIndexSettings)
    market_cache_export_policy_health: MarketCacheExportPolicyHealthSettings = Field(default_factory=MarketCacheExportPolicyHealthSettings)
    market_cache_export_policy_status: MarketCacheExportPolicyStatusSettings = Field(default_factory=MarketCacheExportPolicyStatusSettings)
    market_cache_export_index: MarketCacheExportIndexSettings = Field(default_factory=MarketCacheExportIndexSettings)
    market_cache_export_health: MarketCacheExportHealthSettings = Field(default_factory=MarketCacheExportHealthSettings)
    market_cache_export_status: MarketCacheExportStatusSettings = Field(default_factory=MarketCacheExportStatusSettings)
    market_data_comparison: MarketDataComparisonSettings = Field(default_factory=MarketDataComparisonSettings)
    market_source_policy: MarketSourcePolicySettings = Field(default_factory=MarketSourcePolicySettings)
    market_cache_preflight: MarketCachePreflightSettings = Field(default_factory=MarketCachePreflightSettings)
    market_daily_update: MarketDailyUpdateSettings = Field(default_factory=MarketDailyUpdateSettings)
    historical_backfill: HistoricalBackfillSettings = Field(default_factory=HistoricalBackfillSettings)
    historical_backfill_index: HistoricalBackfillIndexSettings = Field(default_factory=HistoricalBackfillIndexSettings)
    historical_backfill_health: HistoricalBackfillHealthSettings = Field(default_factory=HistoricalBackfillHealthSettings)
    historical_backfill_status: HistoricalBackfillStatusSettings = Field(default_factory=HistoricalBackfillStatusSettings)
    market_update_handoff: MarketUpdateHandoffSettings = Field(default_factory=MarketUpdateHandoffSettings)
    market_update_handoff_index: MarketUpdateHandoffIndexSettings = Field(default_factory=MarketUpdateHandoffIndexSettings)
    market_update_handoff_health: MarketUpdateHandoffHealthSettings = Field(default_factory=MarketUpdateHandoffHealthSettings)
    market_update_handoff_status: MarketUpdateHandoffStatusSettings = Field(default_factory=MarketUpdateHandoffStatusSettings)
    data_pipeline: DataPipelineSettings = Field(default_factory=DataPipelineSettings)
    universe_overlay: UniverseOverlaySettings = Field(default_factory=UniverseOverlaySettings)
    data_preparation_artifact_index: DataPreparationArtifactIndexSettings = Field(default_factory=DataPreparationArtifactIndexSettings)
    data_preparation_artifact_health: DataPreparationArtifactHealthSettings = Field(default_factory=DataPreparationArtifactHealthSettings)
    data_preparation_workflow_status: DataPreparationWorkflowStatusSettings = Field(default_factory=DataPreparationWorkflowStatusSettings)
    local_research_dashboard: LocalResearchDashboardSettings = Field(default_factory=LocalResearchDashboardSettings)
    data_ingestion: DataIngestionSettings = Field(default_factory=DataIngestionSettings)
    data_quality: DataQualitySettings = Field(default_factory=DataQualitySettings)
    snapshot_quality_gate: SnapshotQualityGateSettings = Field(default_factory=SnapshotQualityGateSettings)
    snapshot_quality_preflight: SnapshotQualityPreflightSettings = Field(default_factory=SnapshotQualityPreflightSettings)
    execution: ExecutionSettings
    risk: RiskSettings


def load_settings(path: str | Path) -> Settings:
    """Load YAML settings and validate MVP safety constraints."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return Settings(**payload)
