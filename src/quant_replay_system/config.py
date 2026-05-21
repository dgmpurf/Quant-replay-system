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
    config_version: str = "mvp"
    write_artifacts: bool = True


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
    execution: ExecutionSettings
    risk: RiskSettings


def load_settings(path: str | Path) -> Settings:
    """Load YAML settings and validate MVP safety constraints."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return Settings(**payload)
