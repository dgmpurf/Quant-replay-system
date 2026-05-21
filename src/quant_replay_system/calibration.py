"""Parameter calibration over batch replay results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from quant_replay_system.batch_replay import BatchReplayResult, run_batch_replay
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import CalibrationSettings, Settings, load_settings
from quant_replay_system.report_generation import KNOWN_LIMITATIONS


SCORE_WEIGHT_KEYS = [
    "reality_score",
    "technical_score",
    "expectation_score",
    "liquidity_score",
    "sentiment_score",
    "risk_penalty",
]

DEFAULT_WEIGHT_PROFILES = {
    "baseline": {
        "reality_score": 0.35,
        "technical_score": 0.25,
        "expectation_score": 0.15,
        "liquidity_score": 0.10,
        "sentiment_score": 0.05,
        "risk_penalty": 0.25,
    },
    "technical_heavy": {
        "reality_score": 0.25,
        "technical_score": 0.35,
        "expectation_score": 0.15,
        "liquidity_score": 0.10,
        "sentiment_score": 0.05,
        "risk_penalty": 0.25,
    },
    "risk_heavy": {
        "reality_score": 0.30,
        "technical_score": 0.20,
        "expectation_score": 0.15,
        "liquidity_score": 0.10,
        "sentiment_score": 0.05,
        "risk_penalty": 0.35,
    },
    "liquidity_heavy": {
        "reality_score": 0.30,
        "technical_score": 0.20,
        "expectation_score": 0.15,
        "liquidity_score": 0.20,
        "sentiment_score": 0.05,
        "risk_penalty": 0.25,
    },
}

CALIBRATION_LIMITATIONS = [
    *KNOWN_LIMITATIONS,
    "MVP calibration compares explicit small parameter grids only.",
    "Objective score is explainable but not a proof of future performance.",
    "Train, validation, and test split metadata is recorded but walk-forward enforcement is not implemented yet.",
    "Calibration should be reviewed for stability, not chosen only by highest historical return.",
]


@dataclass(frozen=True)
class CalibrationPlan:
    """A record of what should be calibrated after baseline replay works."""

    weights: bool = True
    thresholds: bool = True
    risk_rules: bool = True


@dataclass(frozen=True)
class CalibrationParameterSet:
    """One explicit parameter configuration to test through batch replay."""

    parameter_set_id: str
    scoring_weights: dict[str, float]
    min_final_score: float | None = 70.0
    min_action: str = "PAPER_TRADE"
    top_n: int = 5
    holding_horizon: int = 10
    skip_non_trading_days: bool = True
    fail_fast: bool = False
    label: str = ""
    weight_profile: str = "custom"
    split_name: str = "full"
    train_dates: tuple[pd.Timestamp, ...] = ()
    validation_dates: tuple[pd.Timestamp, ...] = ()
    test_dates: tuple[pd.Timestamp, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "parameter_set_id": self.parameter_set_id,
            "label": self.label,
            "weight_profile": self.weight_profile,
            "top_n": self.top_n,
            "holding_horizon": self.holding_horizon,
            "min_final_score": self.min_final_score,
            "min_action": self.min_action,
            "skip_non_trading_days": self.skip_non_trading_days,
            "fail_fast": self.fail_fast,
            "split_name": self.split_name,
            "train_dates": list(self.train_dates),
            "validation_dates": list(self.validation_dates),
            "test_dates": list(self.test_dates),
            "scoring_weights": dict(sorted(self.scoring_weights.items())),
        }


@dataclass(frozen=True)
class CalibrationArtifactPaths:
    """Stable artifact paths for one calibration run."""

    artifact_dir: Path
    calibration_report: Path
    ranked_results: Path
    parameter_sets: Path
    batch_runs: Path
    aggregate_metrics: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "calibration_report": self.calibration_report,
            "ranked_results": self.ranked_results,
            "parameter_sets": self.parameter_sets,
            "batch_runs": self.batch_runs,
            "aggregate_metrics": self.aggregate_metrics,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CalibrationResult:
    """Structured result from parameter calibration."""

    calibration_id: str
    parameter_sets: list[CalibrationParameterSet]
    decision_dates: list[pd.Timestamp]
    batch_results: list[BatchReplayResult]
    ranked_results: pd.DataFrame
    best_parameter_set: CalibrationParameterSet | None
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    parameter_sets_frame: pd.DataFrame
    batch_runs_frame: pd.DataFrame
    aggregate_metrics: pd.DataFrame
    split_name: str
    train_dates: list[pd.Timestamp]
    validation_dates: list[pd.Timestamp]
    test_dates: list[pd.Timestamp]


def default_calibration_plan() -> CalibrationPlan:
    """Return the MVP calibration roadmap."""

    return CalibrationPlan()


def build_parameter_grid(
    top_n_values: Iterable[int] = (3, 5, 10),
    holding_horizon_values: Iterable[int] = (3, 5, 10),
    min_final_score_values: Iterable[float | None] = (60.0, 70.0, 80.0),
    weight_profiles: dict[str, dict[str, float]] | None = None,
    min_action_values: Iterable[str] = ("PAPER_TRADE",),
    *,
    skip_non_trading_days: bool = True,
    fail_fast: bool = False,
    split_name: str = "full",
    train_dates: Iterable[str | pd.Timestamp] | None = None,
    validation_dates: Iterable[str | pd.Timestamp] | None = None,
    test_dates: Iterable[str | pd.Timestamp] | None = None,
    max_parameter_sets: int | None = None,
) -> list[CalibrationParameterSet]:
    """Build a deterministic explicit parameter grid."""

    profiles = weight_profiles or DEFAULT_WEIGHT_PROFILES
    train = tuple(_normalize_date_list(train_dates or []))
    validation = tuple(_normalize_date_list(validation_dates or []))
    test = tuple(_normalize_date_list(test_dates or []))
    parameter_sets: list[CalibrationParameterSet] = []

    for profile_name, weights in profiles.items():
        normalized_weights = _normalize_weights(weights)
        for top_n in top_n_values:
            for horizon in holding_horizon_values:
                for threshold in min_final_score_values:
                    for min_action in min_action_values:
                        payload = {
                            "weight_profile": profile_name,
                            "weights": normalized_weights,
                            "top_n": int(top_n),
                            "holding_horizon": int(horizon),
                            "min_final_score": threshold,
                            "min_action": str(min_action),
                            "skip_non_trading_days": bool(skip_non_trading_days),
                            "fail_fast": bool(fail_fast),
                            "split_name": split_name,
                        }
                        parameter_id = _hash_payload(payload, length=8)
                        label = (
                            f"{profile_name}_top{int(top_n)}_h{int(horizon)}_"
                            f"min{_threshold_label(threshold)}"
                        )
                        parameter_sets.append(
                            CalibrationParameterSet(
                                parameter_set_id=parameter_id,
                                scoring_weights=normalized_weights,
                                min_final_score=None if threshold is None else float(threshold),
                                min_action=str(min_action),
                                top_n=int(top_n),
                                holding_horizon=int(horizon),
                                skip_non_trading_days=bool(skip_non_trading_days),
                                fail_fast=bool(fail_fast),
                                label=label,
                                weight_profile=profile_name,
                                split_name=split_name,
                                train_dates=train,
                                validation_dates=validation,
                                test_dates=test,
                            )
                        )

    if max_parameter_sets is not None and len(parameter_sets) > max_parameter_sets:
        raise ValueError(
            f"Parameter grid contains {len(parameter_sets)} sets, exceeding max_parameter_sets={max_parameter_sets}"
        )
    return parameter_sets


def run_parameter_calibration(
    decision_dates: Iterable[str | pd.Timestamp] | str | pd.Timestamp,
    universe_name: str = "default",
    parameter_sets: Iterable[CalibrationParameterSet | dict[str, Any]] | None = None,
    *,
    top_n_values: Iterable[int] | None = None,
    holding_horizon_values: Iterable[int] | None = None,
    min_final_score_values: Iterable[float | None] | None = None,
    weight_profiles: dict[str, dict[str, float]] | None = None,
    min_action_values: Iterable[str] | None = None,
    config: Settings | str | Path | None = None,
    market_data: pd.DataFrame | None = None,
    universe_snapshot: pd.DataFrame | None = None,
    benchmark_data: pd.DataFrame | None = None,
    corporate_actions: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    calibration_id: str | None = None,
    split_name: str = "full",
    train_dates: Iterable[str | pd.Timestamp] | None = None,
    validation_dates: Iterable[str | pd.Timestamp] | None = None,
    test_dates: Iterable[str | pd.Timestamp] | None = None,
) -> CalibrationResult:
    """Run batch replay for each parameter set and rank the results."""

    settings = _load_calibration_settings(config)
    calibration_settings = settings.calibration
    normalized_dates = _normalize_date_list([decision_dates] if isinstance(decision_dates, (str, pd.Timestamp)) else decision_dates)
    train = _normalize_date_list(train_dates or [])
    validation = _normalize_date_list(validation_dates or [])
    test = _normalize_date_list(test_dates or [])

    if parameter_sets is None:
        effective_parameter_sets = build_parameter_grid(
            top_n_values=top_n_values or calibration_settings.default_top_n_values,
            holding_horizon_values=holding_horizon_values or calibration_settings.default_holding_horizon_values,
            min_final_score_values=min_final_score_values or calibration_settings.default_min_final_score_values,
            weight_profiles=weight_profiles,
            min_action_values=min_action_values or (calibration_settings.default_min_action,),
            split_name=split_name,
            train_dates=train,
            validation_dates=validation,
            test_dates=test,
            max_parameter_sets=calibration_settings.max_parameter_sets,
        )
    else:
        effective_parameter_sets = [_coerce_parameter_set(item) for item in parameter_sets]

    effective_calibration_id = calibration_id or generate_calibration_id(
        decision_dates=normalized_dates,
        universe_name=universe_name,
        parameter_sets=effective_parameter_sets,
        config_version=calibration_settings.config_version,
    )
    paths = resolve_calibration_artifact_paths(calibration_settings.output_dir, effective_calibration_id)

    batch_results: list[BatchReplayResult] = []
    warnings: list[str] = []
    for parameter_set in effective_parameter_sets:
        parameter_settings = _settings_for_parameter_set(settings, parameter_set, paths)
        try:
            batch_result = run_batch_replay(
                decision_dates=normalized_dates,
                universe_name=universe_name,
                top_n=parameter_set.top_n,
                holding_horizon=parameter_set.holding_horizon,
                config=parameter_settings,
                market_data=market_data,
                universe_snapshot=universe_snapshot,
                benchmark_data=benchmark_data,
                corporate_actions=corporate_actions,
                trading_calendar=trading_calendar,
            )
            batch_results.append(batch_result)
            warnings.extend(f"{parameter_set.parameter_set_id}: {warning}" for warning in batch_result.warnings)
        except Exception as exc:
            if parameter_set.fail_fast:
                raise
            warnings.append(f"{parameter_set.parameter_set_id} calibration batch failed: {exc}")
            batch_results.append(_failed_batch_result(parameter_set, normalized_dates, universe_name, str(exc)))

    ranked_results = rank_calibration_results(effective_parameter_sets, batch_results, calibration_settings)
    best_parameter_set = _best_parameter_set(effective_parameter_sets, ranked_results)
    parameter_sets_frame = build_parameter_sets_frame(effective_parameter_sets)
    batch_runs_frame = build_calibration_batch_runs_frame(effective_parameter_sets, batch_results)
    aggregate_metrics = build_aggregate_metrics_frame(ranked_results)

    result = CalibrationResult(
        calibration_id=effective_calibration_id,
        parameter_sets=effective_parameter_sets,
        decision_dates=normalized_dates,
        batch_results=batch_results,
        ranked_results=ranked_results,
        best_parameter_set=best_parameter_set,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=CALIBRATION_LIMITATIONS,
        parameter_sets_frame=parameter_sets_frame,
        batch_runs_frame=batch_runs_frame,
        aggregate_metrics=aggregate_metrics,
        split_name=split_name,
        train_dates=train,
        validation_dates=validation,
        test_dates=test,
    )
    if calibration_settings.write_artifacts:
        write_calibration_report(result)
    return result


def generate_calibration_id(
    decision_dates: Iterable[str | pd.Timestamp],
    universe_name: str,
    parameter_sets: Iterable[CalibrationParameterSet],
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic short calibration id."""

    payload = {
        "decision_dates": [str(_normalize_date(date).date()) for date in decision_dates],
        "universe_name": universe_name,
        "parameter_sets": [parameter_set.as_dict() for parameter_set in parameter_sets],
        "config_version": config_version,
    }
    return _hash_payload(payload, length=10)


def resolve_calibration_artifact_paths(output_dir: str | Path, calibration_id: str) -> CalibrationArtifactPaths:
    """Resolve stable artifact paths for one calibration run."""

    artifact_dir = Path(output_dir) / calibration_id
    return CalibrationArtifactPaths(
        artifact_dir=artifact_dir,
        calibration_report=artifact_dir / "calibration_report.md",
        ranked_results=artifact_dir / "ranked_results.csv",
        parameter_sets=artifact_dir / "parameter_sets.csv",
        batch_runs=artifact_dir / "batch_runs.csv",
        aggregate_metrics=artifact_dir / "aggregate_metrics.csv",
        metadata=artifact_dir / "metadata.json",
    )


def rank_calibration_results(
    parameter_sets: list[CalibrationParameterSet],
    batch_results: list[BatchReplayResult],
    config: CalibrationSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Convert batch results into ranked calibration rows."""

    cfg = _coerce_calibration_settings(config)
    rows = []
    for parameter_set, batch_result in zip(parameter_sets, batch_results):
        aggregate = dict(batch_result.aggregate_performance)
        trade_returns = _trade_return_series(batch_result)
        run_returns = _run_equal_weight_returns(batch_result)
        variance_penalty = _variance_penalty(trade_returns)
        worst_penalty = _worst_return_penalty(aggregate.get("worst_return"))
        low_trade_penalty = _low_trade_count_penalty(aggregate.get("total_simulated_trades"), cfg.min_trade_count)
        normalized_average_return = _return_to_score(aggregate.get("average_return"))
        normalized_win_rate = _win_rate_to_score(aggregate.get("win_rate"))
        normalized_excess_return = _return_to_score(aggregate.get("average_excess_return"))
        stability_score = _clip_score(
            100.0 - 0.50 * variance_penalty - 0.30 * worst_penalty - 0.20 * low_trade_penalty
        )
        objective_score = _clip_score(
            0.35 * normalized_average_return
            + 0.20 * normalized_win_rate
            + 0.15 * normalized_excess_return
            - 0.15 * worst_penalty
            - 0.10 * variance_penalty
            - 0.05 * low_trade_penalty
        )

        rows.append(
            {
                "parameter_set_id": parameter_set.parameter_set_id,
                "label": parameter_set.label,
                "weight_profile": parameter_set.weight_profile,
                "top_n": parameter_set.top_n,
                "holding_horizon": parameter_set.holding_horizon,
                "min_final_score": parameter_set.min_final_score,
                "min_action": parameter_set.min_action,
                "split_name": parameter_set.split_name,
                "batch_id": getattr(batch_result, "batch_id", ""),
                "number_of_runs": aggregate.get("number_of_executed_dates", 0),
                "executed_dates": aggregate.get("number_of_executed_dates", 0),
                "skipped_dates": aggregate.get("number_of_skipped_dates", 0),
                "failed_dates": aggregate.get("number_of_failed_dates", 0),
                "total_candidates": aggregate.get("total_candidates", 0),
                "total_trades": aggregate.get("total_simulated_trades", 0),
                "average_return": aggregate.get("average_return"),
                "median_return": aggregate.get("median_return"),
                "win_rate": aggregate.get("win_rate"),
                "best_return": aggregate.get("best_return"),
                "worst_return": aggregate.get("worst_return"),
                "average_excess_return": aggregate.get("average_excess_return"),
                "max_drawdown_proxy": _max_drawdown_proxy(run_returns),
                "stability_score": stability_score,
                "penalty_for_low_trade_count": low_trade_penalty,
                "penalty_for_high_variance": variance_penalty,
                "worst_return_penalty": worst_penalty,
                "normalized_average_return": normalized_average_return,
                "normalized_win_rate": normalized_win_rate,
                "normalized_average_excess_return": normalized_excess_return,
                "objective_score": objective_score,
                "warning_count": len(getattr(batch_result, "warnings", [])),
            }
        )

    ranked = _ordered_frame(rows, _ranked_columns())
    if ranked.empty:
        return ranked
    return ranked.sort_values(
        ["objective_score", "stability_score", "parameter_set_id"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_parameter_sets_frame(parameter_sets: list[CalibrationParameterSet]) -> pd.DataFrame:
    """Build export rows for parameter set definitions."""

    return _ordered_frame([parameter_set.as_dict() for parameter_set in parameter_sets], _parameter_set_columns())


def build_calibration_batch_runs_frame(
    parameter_sets: list[CalibrationParameterSet],
    batch_results: list[BatchReplayResult],
) -> pd.DataFrame:
    """Build one row per parameter-set batch replay."""

    rows = []
    for parameter_set, batch_result in zip(parameter_sets, batch_results):
        artifact_paths = getattr(batch_result, "artifact_paths", {})
        aggregate = getattr(batch_result, "aggregate_performance", {})
        rows.append(
            {
                "parameter_set_id": parameter_set.parameter_set_id,
                "batch_id": getattr(batch_result, "batch_id", ""),
                "batch_report_path": artifact_paths.get("batch_report"),
                "batch_index_path": artifact_paths.get("batch_index"),
                "aggregate_performance_path": artifact_paths.get("aggregate_performance"),
                "executed_dates": aggregate.get("number_of_executed_dates", 0),
                "skipped_dates": aggregate.get("number_of_skipped_dates", 0),
                "failed_dates": aggregate.get("number_of_failed_dates", 0),
                "total_candidates": aggregate.get("total_candidates", 0),
                "total_trades": aggregate.get("total_simulated_trades", 0),
                "average_return": aggregate.get("average_return"),
                "win_rate": aggregate.get("win_rate"),
                "average_excess_return": aggregate.get("average_excess_return"),
                "status": "FAILED" if aggregate.get("number_of_failed_dates", 0) else "COMPLETED",
                "warning_count": len(getattr(batch_result, "warnings", [])),
            }
        )
    return _ordered_frame(rows, _batch_run_columns())


def build_aggregate_metrics_frame(ranked_results: pd.DataFrame) -> pd.DataFrame:
    """Build aggregate metric export rows from ranked calibration results."""

    return _ordered_frame(ranked_results.to_dict("records"), _aggregate_metric_columns())


def write_calibration_report(result: CalibrationResult, path: str | Path | None = None) -> Path:
    """Write calibration markdown, CSV, and metadata artifacts."""

    paths = CalibrationArtifactPaths(**result.artifact_paths)
    if path is not None:
        paths = CalibrationArtifactPaths(
            artifact_dir=Path(path).parent,
            calibration_report=Path(path),
            ranked_results=paths.ranked_results,
            parameter_sets=paths.parameter_sets,
            batch_runs=paths.batch_runs,
            aggregate_metrics=paths.aggregate_metrics,
            metadata=paths.metadata,
        )

    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.ranked_results, paths.ranked_results)
    _export_dataframe(result.parameter_sets_frame, paths.parameter_sets)
    _export_dataframe(result.batch_runs_frame, paths.batch_runs)
    _export_dataframe(result.aggregate_metrics, paths.aggregate_metrics)

    metadata = build_calibration_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.calibration_report.write_text(render_calibration_report(result, paths, metadata), encoding="utf-8")
    return paths.calibration_report


def build_calibration_metadata(result: CalibrationResult, paths: CalibrationArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for calibration."""

    output_files = {name: str(path) for name, path in paths.as_dict().items() if name != "artifact_dir"}
    return {
        "calibration_id": result.calibration_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision_dates": result.decision_dates,
        "split_name": result.split_name,
        "train_dates": result.train_dates,
        "validation_dates": result.validation_dates,
        "test_dates": result.test_dates,
        "parameter_sets": [parameter_set.as_dict() for parameter_set in result.parameter_sets],
        "best_parameter_set": None if result.best_parameter_set is None else result.best_parameter_set.as_dict(),
        "output_files": output_files,
        "row_counts": {
            "parameter_sets": len(result.parameter_sets_frame),
            "batch_runs": len(result.batch_runs_frame),
            "ranked_results": len(result.ranked_results),
            "aggregate_metrics": len(result.aggregate_metrics),
        },
        "known_limitations": result.known_limitations,
        "warnings": result.warnings,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "contract_note": "Calibration calls batch replay and does not bypass point-in-time or execution contracts.",
    }


def render_calibration_report(
    result: CalibrationResult,
    paths: CalibrationArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render the calibration markdown report."""

    best = result.best_parameter_set.as_dict() if result.best_parameter_set is not None else {}
    lines = [
        f"# Parameter Calibration Report: {result.calibration_id}",
        "",
        "## Calibration Metadata",
        "",
        _dict_table(
            {
                "calibration_id": result.calibration_id,
                "artifact_dir": paths.artifact_dir,
                "parameter_sets": len(result.parameter_sets),
                "decision_dates": len(result.decision_dates),
                "split_name": result.split_name,
            }
        ),
        "",
        "## Best Parameter Set",
        "",
        _dict_table(best) if best else "_No parameter set ranked._",
        "",
        "## Objective Formula",
        "",
        (
            "`objective_score = 0.35 * normalized_average_return + 0.20 * normalized_win_rate "
            "+ 0.15 * normalized_average_excess_return - 0.15 * normalized_worst_return_penalty "
            "- 0.10 * normalized_variance_penalty - 0.05 * low_trade_count_penalty`"
        ),
        "",
        "## Ranked Results",
        "",
        _markdown_table(
            result.ranked_results,
            [
                "parameter_set_id",
                "label",
                "objective_score",
                "stability_score",
                "total_trades",
                "average_return",
                "win_rate",
                "average_excess_return",
                "penalty_for_low_trade_count",
                "penalty_for_high_variance",
            ],
        ),
        "",
        "## Parameter Sets",
        "",
        _markdown_table(
            result.parameter_sets_frame,
            ["parameter_set_id", "label", "weight_profile", "top_n", "holding_horizon", "min_final_score", "min_action"],
        ),
        "",
        "## Batch Runs",
        "",
        _markdown_table(
            result.batch_runs_frame,
            ["parameter_set_id", "batch_id", "executed_dates", "skipped_dates", "total_trades", "batch_report_path"],
        ),
        "",
        "## Split Metadata",
        "",
        _dict_table(
            {
                "split_name": result.split_name,
                "train_dates": result.train_dates,
                "validation_dates": result.validation_dates,
                "test_dates": result.test_dates,
            }
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known Limitations",
        "",
        "\n".join(f"- {item}" for item in metadata["known_limitations"]),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _settings_for_parameter_set(
    settings: Settings,
    parameter_set: CalibrationParameterSet,
    paths: CalibrationArtifactPaths,
) -> Settings:
    score_engine = settings.score_engine.model_copy(update={"weights": parameter_set.scoring_weights})
    version = f"{settings.calibration.config_version}:{parameter_set.parameter_set_id}"
    replay_run = settings.replay_run.model_copy(
        update={
            "min_action": parameter_set.min_action,
            "min_final_score": parameter_set.min_final_score,
            "config_version": version,
            "output_dir": paths.artifact_dir / "replay_runs",
        }
    )
    batch_replay = settings.batch_replay.model_copy(
        update={
            "skip_non_trading_days": parameter_set.skip_non_trading_days,
            "fail_fast": parameter_set.fail_fast,
            "config_version": version,
            "output_dir": paths.artifact_dir / "batch_replays",
        }
    )
    return settings.model_copy(
        update={
            "score_engine": score_engine,
            "replay_run": replay_run,
            "batch_replay": batch_replay,
        }
    )


def _failed_batch_result(
    parameter_set: CalibrationParameterSet,
    decision_dates: list[pd.Timestamp],
    universe_name: str,
    detail: str,
) -> Any:
    aggregate = {
        "number_of_requested_dates": len(decision_dates),
        "number_of_executed_dates": 0,
        "number_of_skipped_dates": len(decision_dates),
        "number_of_failed_dates": len(decision_dates),
        "total_candidates": 0,
        "total_simulated_trades": 0,
        "total_skipped_trades": 0,
        "average_return": None,
        "median_return": None,
        "win_rate": None,
        "best_return": None,
        "worst_return": None,
        "average_equal_weight_return_by_run": None,
        "average_benchmark_return": None,
        "average_excess_return": None,
    }
    artifact_paths: dict[str, Path] = {}
    return type(
        "FailedBatchReplayResult",
        (),
        {
            "batch_id": f"failed_{parameter_set.parameter_set_id}",
            "universe_name": universe_name,
            "top_n": parameter_set.top_n,
            "holding_horizon": parameter_set.holding_horizon,
            "requested_decision_dates": decision_dates,
            "executed_decision_dates": [],
            "skipped_decision_dates": pd.DataFrame(
                [{"decision_date": date, "reason": "RUN_FAILED", "detail": detail} for date in decision_dates]
            ),
            "replay_results": [],
            "aggregate_performance": aggregate,
            "artifact_paths": artifact_paths,
            "warnings": [detail],
            "batch_index": pd.DataFrame(),
            "replay_runs_frame": pd.DataFrame(),
            "config_summary": {},
        },
    )()


def _best_parameter_set(
    parameter_sets: list[CalibrationParameterSet],
    ranked_results: pd.DataFrame,
) -> CalibrationParameterSet | None:
    if ranked_results.empty:
        return None
    best_id = ranked_results.iloc[0]["parameter_set_id"]
    by_id = {parameter_set.parameter_set_id: parameter_set for parameter_set in parameter_sets}
    return by_id.get(best_id)


def _coerce_parameter_set(value: CalibrationParameterSet | dict[str, Any]) -> CalibrationParameterSet:
    if isinstance(value, CalibrationParameterSet):
        return value
    if not isinstance(value, dict):
        raise TypeError("parameter_sets must contain CalibrationParameterSet instances or dictionaries")
    payload = dict(value)
    payload["scoring_weights"] = _normalize_weights(payload["scoring_weights"])
    for key in ["train_dates", "validation_dates", "test_dates"]:
        payload[key] = tuple(_normalize_date_list(payload.get(key, [])))
    return CalibrationParameterSet(**payload)


def _coerce_calibration_settings(config: CalibrationSettings | dict[str, Any] | None) -> CalibrationSettings:
    if config is None:
        return CalibrationSettings()
    if isinstance(config, CalibrationSettings):
        return config
    if isinstance(config, dict):
        return CalibrationSettings(**config)
    if hasattr(config, "model_dump"):
        return CalibrationSettings(**config.model_dump())
    raise TypeError("config must be a CalibrationSettings instance, dict, or None")


def _load_calibration_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _normalize_weights(weights: dict[str, Any]) -> dict[str, float]:
    normalized = {}
    for key in SCORE_WEIGHT_KEYS:
        if key not in weights:
            raise ValueError(f"Calibration scoring weights missing required key: {key}")
        normalized[key] = float(weights[key])
    return normalized


def _normalize_date_list(values: Iterable[str | pd.Timestamp]) -> list[pd.Timestamp]:
    return [_normalize_date(value) for value in values]


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _threshold_label(value: float | None) -> str:
    if value is None:
        return "none"
    return str(value).replace(".", "p")


def _trade_return_series(batch_result: Any) -> pd.Series:
    values = []
    for replay_result in getattr(batch_result, "replay_results", []):
        trades = replay_result.simulated_trades
        if "trade_return" in trades.columns:
            values.extend(pd.to_numeric(trades["trade_return"], errors="coerce").dropna().tolist())
    return pd.Series(values, dtype="float64")


def _run_equal_weight_returns(batch_result: Any) -> pd.Series:
    values = []
    for replay_result in getattr(batch_result, "replay_results", []):
        value = replay_result.performance_summary.get("total_equal_weight_return")
        if value is not None and not pd.isna(value):
            values.append(float(value))
    return pd.Series(values, dtype="float64")


def _return_to_score(value: Any) -> float:
    if value is None or pd.isna(value):
        return 50.0
    return _clip_score(50.0 + float(value) * 500.0)


def _win_rate_to_score(value: Any) -> float:
    if value is None or pd.isna(value):
        return 50.0
    return _clip_score(float(value) * 100.0)


def _worst_return_penalty(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return _clip_score(max(0.0, -float(value) * 500.0))


def _variance_penalty(returns: pd.Series) -> float:
    if returns.empty or len(returns) < 2:
        return 0.0
    return _clip_score(float(returns.std(ddof=0)) * 500.0)


def _low_trade_count_penalty(total_trades: Any, minimum_trade_count: int) -> float:
    if minimum_trade_count <= 0:
        return 0.0
    count = 0 if total_trades is None or pd.isna(total_trades) else int(total_trades)
    if count >= minimum_trade_count:
        return 0.0
    return _clip_score((minimum_trade_count - count) / minimum_trade_count * 100.0)


def _max_drawdown_proxy(run_returns: pd.Series) -> float | None:
    if run_returns.empty:
        return None
    equity = (1.0 + run_returns).cumprod()
    peaks = equity.cummax()
    drawdowns = equity / peaks - 1.0
    return float(drawdowns.min())


def _clip_score(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(np.clip(float(value), 0.0, 100.0))


def _ranked_columns() -> list[str]:
    return [
        "parameter_set_id",
        "label",
        "weight_profile",
        "top_n",
        "holding_horizon",
        "min_final_score",
        "min_action",
        "split_name",
        "batch_id",
        "number_of_runs",
        "executed_dates",
        "skipped_dates",
        "failed_dates",
        "total_candidates",
        "total_trades",
        "average_return",
        "median_return",
        "win_rate",
        "best_return",
        "worst_return",
        "average_excess_return",
        "max_drawdown_proxy",
        "stability_score",
        "penalty_for_low_trade_count",
        "penalty_for_high_variance",
        "worst_return_penalty",
        "normalized_average_return",
        "normalized_win_rate",
        "normalized_average_excess_return",
        "objective_score",
        "warning_count",
    ]


def _parameter_set_columns() -> list[str]:
    return [
        "parameter_set_id",
        "label",
        "weight_profile",
        "top_n",
        "holding_horizon",
        "min_final_score",
        "min_action",
        "skip_non_trading_days",
        "fail_fast",
        "split_name",
        "train_dates",
        "validation_dates",
        "test_dates",
        "scoring_weights",
    ]


def _batch_run_columns() -> list[str]:
    return [
        "parameter_set_id",
        "batch_id",
        "batch_report_path",
        "batch_index_path",
        "aggregate_performance_path",
        "executed_dates",
        "skipped_dates",
        "failed_dates",
        "total_candidates",
        "total_trades",
        "average_return",
        "win_rate",
        "average_excess_return",
        "status",
        "warning_count",
    ]


def _aggregate_metric_columns() -> list[str]:
    return [
        "parameter_set_id",
        "objective_score",
        "stability_score",
        "total_trades",
        "average_return",
        "median_return",
        "win_rate",
        "best_return",
        "worst_return",
        "average_excess_return",
        "max_drawdown_proxy",
        "penalty_for_low_trade_count",
        "penalty_for_high_variance",
        "worst_return_penalty",
    ]


def _ordered_frame(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    remaining = [column for column in frame.columns if column not in columns]
    return frame[[*columns, *remaining]]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
