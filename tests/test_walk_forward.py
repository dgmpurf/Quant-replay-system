import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.calibration import DEFAULT_WEIGHT_PROFILES, CalibrationParameterSet
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import WalkForwardSettings, load_settings
from quant_replay_system.walk_forward import (
    WalkForwardResult,
    build_walk_forward_splits,
    compute_overfitting_diagnostics,
    run_walk_forward_validation,
)


TRAIN_DATES = [pd.Timestamp("2024-03-01")]
VALIDATION_DATES = [pd.Timestamp("2024-03-04")]
TEST_DATES = [pd.Timestamp("2024-03-05")]


@pytest.fixture(scope="module")
def walk_forward_result_bundle(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, WalkForwardResult]:
    tmp_path = tmp_path_factory.mktemp("walk_forward_result")
    return tmp_path, _run_walk_forward(tmp_path)


@pytest.fixture(scope="module")
def walk_forward_result(walk_forward_result_bundle: tuple[Path, WalkForwardResult]) -> WalkForwardResult:
    return walk_forward_result_bundle[1]


@pytest.fixture(scope="module")
def walk_forward_tmp_path(walk_forward_result_bundle: tuple[Path, WalkForwardResult]) -> Path:
    return walk_forward_result_bundle[0]


def test_explicit_train_validation_test_split_creation() -> None:
    split = build_walk_forward_splits(
        train_dates=TRAIN_DATES,
        validation_dates=VALIDATION_DATES,
        test_dates=TEST_DATES,
    )

    assert split.train_dates == TRAIN_DATES
    assert split.validation_dates == VALIDATION_DATES
    assert split.test_dates == TEST_DATES


def test_explicit_split_dates_must_be_disjoint() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        build_walk_forward_splits(
            train_dates=[pd.Timestamp("2024-03-01")],
            validation_dates=[pd.Timestamp("2024-03-01")],
            test_dates=[],
        )


def test_run_walk_forward_validation_returns_structured_result(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result

    assert isinstance(result, WalkForwardResult)
    assert result.train_dates == TRAIN_DATES
    assert result.validation_dates == VALIDATION_DATES
    assert result.test_dates == TEST_DATES


def test_calibration_is_run_on_train_dates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_calibration(monkeypatch)
    _run_walk_forward(tmp_path, fake=True)

    assert calls[0]["decision_dates"] == TRAIN_DATES
    assert calls[0]["split_name"] == "train"


def test_selected_parameter_set_comes_from_train_calibration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_calibration(monkeypatch)
    result = _run_walk_forward(tmp_path, fake=True)

    assert result.selected_parameter_set == _parameter_sets()[1]


def test_validation_evaluates_selected_parameter_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_calibration(monkeypatch)
    _run_walk_forward(tmp_path, fake=True)

    assert calls[1]["split_name"] == "validation"
    assert calls[1]["decision_dates"] == VALIDATION_DATES
    assert calls[1]["parameter_sets"] == [_parameter_sets()[1]]


def test_test_evaluates_selected_parameter_set_if_test_dates_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_calibration(monkeypatch)
    _run_walk_forward(tmp_path, fake=True)

    assert calls[2]["split_name"] == "test"
    assert calls[2]["decision_dates"] == TEST_DATES
    assert calls[2]["parameter_sets"] == [_parameter_sets()[1]]


def test_diagnostics_include_objective_decay_and_overfit_risk_score() -> None:
    diagnostics = _diagnostics(train_objective=80.0, validation_objective=60.0)

    assert diagnostics.objective_decay > 0
    assert diagnostics.overfit_risk_score >= 0


def test_overfit_risk_label_is_assigned() -> None:
    diagnostics = _diagnostics(train_objective=90.0, validation_objective=20.0)

    assert diagnostics.overfit_risk_label in {"LOW", "MEDIUM", "HIGH", "SEVERE"}


def test_high_train_poor_validation_produces_higher_overfit_risk() -> None:
    stable = _diagnostics(train_objective=70.0, validation_objective=68.0, validation_return=0.02)
    unstable = _diagnostics(train_objective=90.0, validation_objective=20.0, validation_return=-0.10)

    assert unstable.overfit_risk_score > stable.overfit_risk_score


def test_low_trade_count_increases_overfit_risk() -> None:
    enough_trades = _diagnostics(validation_trades=5)
    few_trades = _diagnostics(validation_trades=0)

    assert few_trades.low_trade_count_penalty > enough_trades.low_trade_count_penalty
    assert few_trades.overfit_risk_score > enough_trades.overfit_risk_score


@pytest.mark.slow
def test_artifact_folder_is_created(walk_forward_result: WalkForwardResult, walk_forward_tmp_path: Path) -> None:
    result = walk_forward_result

    assert result.artifact_paths["artifact_dir"].exists()
    assert result.artifact_paths["artifact_dir"].parent == walk_forward_tmp_path / "walk_forward"


@pytest.mark.slow
def test_walk_forward_report_is_written(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result

    assert result.artifact_paths["walk_forward_report"].exists()
    assert result.artifact_paths["walk_forward_report"].name == "walk_forward_report.md"


@pytest.mark.slow
def test_diagnostics_csv_is_written_and_readable_by_pandas(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result

    exported = pd.read_csv(result.artifact_paths["diagnostics"])
    assert "objective_decay" in exported.columns
    assert "overfit_risk_score" in exported.columns


@pytest.mark.slow
def test_selected_parameter_set_json_is_written(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result
    payload = json.loads(result.artifact_paths["selected_parameter_set"].read_text(encoding="utf-8"))

    assert payload["parameter_set_id"] == result.selected_parameter_set.parameter_set_id


@pytest.mark.slow
def test_metadata_json_is_written(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["walk_forward_id"] == result.walk_forward_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


@pytest.mark.slow
def test_deterministic_walk_forward_id_for_same_inputs(tmp_path: Path) -> None:
    first = _run_walk_forward(tmp_path)
    second = _run_walk_forward(tmp_path)

    assert first.walk_forward_id == second.walk_forward_id
    assert first.artifact_paths["artifact_dir"] == second.artifact_paths["artifact_dir"]


@pytest.mark.slow
def test_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first = _run_walk_forward(tmp_path)
    second = _run_walk_forward(tmp_path)

    assert first.diagnostics == second.diagnostics
    assert first.selected_parameter_set == second.selected_parameter_set
    assert_frame_equal(first.train_calibration_result.ranked_results, second.train_calibration_result.ranked_results)


def test_no_live_trading_or_broker_integration_is_invoked(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    for calibration in [result.train_calibration_result, result.validation_result, result.test_result]:
        if calibration is None:
            continue
        for batch in calibration.batch_results:
            for replay in batch.replay_results:
                assert replay.audit_metadata["live_trading_enabled"] is False
                assert replay.audit_metadata["broker_api_invoked"] is False


def test_point_in_time_and_replay_contracts_are_not_bypassed(walk_forward_result: WalkForwardResult) -> None:
    result = walk_forward_result

    for calibration in [result.train_calibration_result, result.validation_result, result.test_result]:
        if calibration is None:
            continue
        for batch in calibration.batch_results:
            for replay in batch.replay_results:
                assert replay.audit_metadata["point_in_time_rule"] == "available_time <= decision_time"
                latest_market = replay.audit_metadata["latest_market_available_time"]
                if latest_market is not None:
                    assert latest_market <= replay.decision_time


def _install_fake_calibration(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls = []

    def fake_run_parameter_calibration(*args, **kwargs):
        decision_dates = list(kwargs["decision_dates"])
        parameter_sets = list(kwargs["parameter_sets"])
        split_name = kwargs["split_name"]
        calls.append(
            {
                "decision_dates": decision_dates,
                "parameter_sets": parameter_sets,
                "split_name": split_name,
            }
        )
        if split_name == "train":
            return _fake_calibration_result(parameter_sets, best=parameter_sets[1], objective_scores=[50.0, 80.0])
        return _fake_calibration_result(parameter_sets, best=parameter_sets[0], objective_scores=[60.0])

    monkeypatch.setattr("quant_replay_system.walk_forward.run_parameter_calibration", fake_run_parameter_calibration)
    return calls


def _run_walk_forward(tmp_path: Path, *, fake: bool = False) -> WalkForwardResult:
    kwargs = {
        "train_dates": TRAIN_DATES,
        "validation_dates": VALIDATION_DATES,
        "test_dates": TEST_DATES,
        "universe_name": "walk_test",
        "parameter_sets": _parameter_sets(),
        "config": _settings(tmp_path),
        "split_name": "explicit",
    }
    if fake:
        return run_walk_forward_validation(**kwargs)
    return run_walk_forward_validation(
        **kwargs,
        market_data=_make_market_data(["AAA", "BBB"]),
        universe_snapshot=_make_universe_snapshot(["AAA", "BBB"]),
        benchmark_data=_make_benchmark_data(),
        trading_calendar=_make_calendar(),
    )


def _diagnostics(
    *,
    train_objective: float = 80.0,
    validation_objective: float = 70.0,
    train_return: float = 0.04,
    validation_return: float = 0.02,
    train_drawdown: float = -0.02,
    validation_drawdown: float = -0.03,
    validation_trades: int = 3,
):
    parameter_set = _parameter_sets()[0]
    train = _fake_calibration_result(
        [parameter_set],
        best=parameter_set,
        objective_scores=[train_objective],
        portfolio_returns=[train_return],
        drawdowns=[train_drawdown],
        trades=[3],
    )
    validation = _fake_calibration_result(
        [parameter_set],
        best=parameter_set,
        objective_scores=[validation_objective],
        portfolio_returns=[validation_return],
        drawdowns=[validation_drawdown],
        trades=[validation_trades],
    )
    return compute_overfitting_diagnostics(
        train_calibration_result=train,
        validation_result=validation,
        selected_parameter_set=parameter_set,
        settings=WalkForwardSettings(min_train_dates=1),
        min_trade_count=3,
    )


def _fake_calibration_result(
    parameter_sets: list[CalibrationParameterSet],
    *,
    best: CalibrationParameterSet,
    objective_scores: list[float],
    portfolio_returns: list[float] | None = None,
    drawdowns: list[float] | None = None,
    trades: list[int] | None = None,
) -> SimpleNamespace:
    rows = []
    portfolio_returns = portfolio_returns or [0.02 for _ in parameter_sets]
    drawdowns = drawdowns or [-0.02 for _ in parameter_sets]
    trades = trades or [3 for _ in parameter_sets]
    for idx, parameter_set in enumerate(parameter_sets):
        objective = objective_scores[min(idx, len(objective_scores) - 1)]
        rows.append(
            {
                "parameter_set_id": parameter_set.parameter_set_id,
                "ranking_score": objective,
                "objective_score": objective,
                "portfolio_objective_score": objective,
                "average_return": portfolio_returns[min(idx, len(portfolio_returns) - 1)],
                "portfolio_total_return": portfolio_returns[min(idx, len(portfolio_returns) - 1)],
                "portfolio_max_drawdown": drawdowns[min(idx, len(drawdowns) - 1)],
                "portfolio_number_of_trades": trades[min(idx, len(trades) - 1)],
                "total_trades": trades[min(idx, len(trades) - 1)],
            }
        )
    ranked = pd.DataFrame(rows).sort_values("ranking_score", ascending=False).reset_index(drop=True)
    return SimpleNamespace(
        calibration_id="fake",
        parameter_sets=parameter_sets,
        best_parameter_set=best,
        ranked_results=ranked,
        warnings=[],
        batch_results=[],
    )


def _parameter_sets() -> list[CalibrationParameterSet]:
    return [
        CalibrationParameterSet(
            parameter_set_id="baseline",
            scoring_weights=DEFAULT_WEIGHT_PROFILES["baseline"],
            min_final_score=None,
            min_action="NO_TRADE",
            top_n=2,
            holding_horizon=2,
            label="baseline",
            weight_profile="baseline",
        ),
        CalibrationParameterSet(
            parameter_set_id="risk_heavy",
            scoring_weights=DEFAULT_WEIGHT_PROFILES["risk_heavy"],
            min_final_score=None,
            min_action="NO_TRADE",
            top_n=2,
            holding_horizon=2,
            label="risk_heavy",
            weight_profile="risk_heavy",
        ),
    ]


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "replay_run": settings.replay_run.model_copy(
                update={
                    "output_dir": tmp_path / "single_replays",
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "default_top_n": 2,
                    "default_holding_horizon": 2,
                }
            ),
            "batch_replay": settings.batch_replay.model_copy(
                update={
                    "output_dir": tmp_path / "batch_replays",
                    "default_top_n": 2,
                    "default_holding_horizon": 2,
                    "enable_portfolio_simulation": True,
                }
            ),
            "calibration": settings.calibration.model_copy(
                update={
                    "output_dir": tmp_path / "calibrations",
                    "min_trade_count": 1,
                    "use_portfolio_metrics": True,
                    "objective_metric_mode": "portfolio_aware",
                    "write_artifacts": True,
                }
            ),
            "portfolio_simulation": settings.portfolio_simulation.model_copy(
                update={
                    "output_dir": tmp_path / "portfolio_simulations",
                    "initial_cash": 10_000.0,
                    "max_gross_exposure": 0.60,
                    "max_position_weight": 0.20,
                    "reserve_cash_pct": 0.40,
                }
            ),
            "walk_forward": settings.walk_forward.model_copy(
                update={
                    "output_dir": tmp_path / "walk_forward",
                    "min_train_dates": 1,
                    "min_validation_dates": 1,
                    "min_test_dates": 1,
                    "require_test": True,
                    "write_artifacts": True,
                }
            ),
            "candidate_selection": settings.candidate_selection.model_copy(update={"exclude_blocked": True}),
        }
    )


def _make_calendar() -> TradingCalendar:
    dates = pd.date_range("2024-01-01", "2024-03-15", freq="D")
    rows = []
    for date in dates:
        is_weekend = date.weekday() >= 5
        is_holiday = date == pd.Timestamp("2024-03-06")
        is_trading = not is_weekend and not is_holiday
        rows.append(
            {
                "trade_date": date,
                "is_trading_day": is_trading,
                "session_open": "09:30" if is_trading else "",
                "session_close": "15:00" if is_trading else "",
                "decision_time": "15:30" if is_trading else "",
                "reason": "normal" if is_trading else ("holiday" if is_holiday else "weekend"),
            }
        )
    return TradingCalendar(pd.DataFrame(rows))


def _make_universe_snapshot(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": pd.Timestamp("2024-03-01"),
                "symbol": symbol,
                "name": f"{symbol} Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": pd.Timestamp("2023-01-01"),
                "delisted_date": pd.NaT,
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "Test",
                "min_lot": 100,
                "t_plus_rule": "t_plus_1",
                "available_time": pd.Timestamp("2024-03-01 09:00:00"),
                "revision_id": "u1",
                "source": "unit-test",
            }
            for symbol in symbols
        ]
    )


def _make_market_data(symbols: list[str]) -> pd.DataFrame:
    rows = []
    dates = pd.bdate_range("2024-01-01", "2024-03-15")
    dates = dates[dates != pd.Timestamp("2024-03-06")]
    for symbol_index, symbol in enumerate(symbols):
        offset = symbol_index * 25
        previous_close = None
        for idx, trade_date in enumerate(dates):
            close = 20 + offset + idx * (1.0 + symbol_index * 0.1)
            open_price = close - 0.25
            high = close + 0.8
            low = close - 0.8
            pre_close = previous_close if previous_close is not None else close - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1_000_000 + idx * 1_000 + symbol_index * 5_000,
                    "amount": 50_000_000 + idx * 500_000 + symbol_index * 1_000_000,
                    "pre_close": pre_close,
                    "adj_factor": 1.0,
                    "is_suspended": False,
                    "limit_up": close * 1.1,
                    "limit_down": close * 0.9,
                    "event_time": trade_date + pd.Timedelta(hours=15),
                    "publish_time": trade_date + pd.Timedelta(hours=15, minutes=5),
                    "ingest_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                    "revision_id": "m1",
                    "source": "unit-test",
                }
            )
            previous_close = close
    return pd.DataFrame(rows)


def _make_benchmark_data() -> pd.DataFrame:
    rows = []
    for idx, trade_date in enumerate(pd.bdate_range("2024-01-01", "2024-03-15")):
        if trade_date == pd.Timestamp("2024-03-06"):
            continue
        rows.append(
            {
                "symbol": "BENCH",
                "trade_date": trade_date,
                "close": 100 + idx * 0.5,
                "available_time": trade_date + pd.Timedelta(hours=15, minutes=10),
                "revision_id": "b1",
                "source": "unit-test",
            }
        )
    return pd.DataFrame(rows)
