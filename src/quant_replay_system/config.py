"""Configuration loading for the replay system."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal

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
    replay_run: ReplayRunSettings = Field(default_factory=ReplayRunSettings)
    batch_replay: BatchReplaySettings = Field(default_factory=BatchReplaySettings)
    calibration: CalibrationSettings = Field(default_factory=CalibrationSettings)
    portfolio_simulation: PortfolioSimulationSettings = Field(default_factory=PortfolioSimulationSettings)
    walk_forward: WalkForwardSettings = Field(default_factory=WalkForwardSettings)
    paper_trading: PaperTradingSettings = Field(default_factory=PaperTradingSettings)
    paper_reconciliation: PaperReconciliationSettings = Field(default_factory=PaperReconciliationSettings)
    paper_review: PaperReviewSettings = Field(default_factory=PaperReviewSettings)
    daily_paper_runner: DailyPaperRunnerSettings = Field(default_factory=DailyPaperRunnerSettings)
    paper_artifact_index: PaperArtifactIndexSettings = Field(default_factory=PaperArtifactIndexSettings)
    paper_artifact_health: PaperArtifactHealthSettings = Field(default_factory=PaperArtifactHealthSettings)
    data_ingestion: DataIngestionSettings = Field(default_factory=DataIngestionSettings)
    data_quality: DataQualitySettings = Field(default_factory=DataQualitySettings)
    execution: ExecutionSettings
    risk: RiskSettings


def load_settings(path: str | Path) -> Settings:
    """Load YAML settings and validate MVP safety constraints."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return Settings(**payload)
