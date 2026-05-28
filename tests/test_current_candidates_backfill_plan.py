import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.current_candidates_backfill_plan import build_current_candidates_backfill_plan


def test_backfill_plan_preserves_leading_zero_symbols(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=8)

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-11",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1, 3],
        max_dates=3,
        warmup_trading_days=1,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )

    plan_csv = pd.read_csv(result.artifact_paths["plan_csv"], dtype={"symbols": str})

    assert "000001" in result.plan_frame["symbols"].iloc[0]
    assert "000001" in plan_csv["symbols"].iloc[0]


def test_dates_too_close_to_cache_end_are_excluded_when_max_horizon_required(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=8)

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-11",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1, 3],
        max_dates=10,
        warmup_trading_days=1,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )

    assert result.selected_date_count == 5
    assert result.plan_frame["signal_date"].max() == "2024-01-08"
    assert result.plan_frame["forward_3d_available"].eq(True).all()
    assert result.plan_frame["warmup_available"].eq(True).all()


def test_dates_too_early_for_warmup_are_excluded(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=12)

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-17",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1, 2],
        max_dates=20,
        warmup_trading_days=5,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )

    assert result.plan_frame["signal_date"].min() == "2024-01-08"
    assert "2024-01-02" not in result.plan_frame["signal_date"].tolist()
    assert result.plan_frame["warmup_trading_days"].eq(5).all()
    assert result.plan_frame["warmup_available"].eq(True).all()
    assert result.plan_frame["candidate_generation_feasible"].eq(True).all()
    assert result.plan_frame["candidate_generation_blocker"].fillna("").eq("").all()


def test_selected_rows_require_warmup_and_forward_horizon(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=12)

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-17",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1, 3],
        max_dates=20,
        warmup_trading_days=5,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )

    assert result.plan_frame["signal_date"].min() == "2024-01-08"
    assert result.plan_frame["signal_date"].max() == "2024-01-12"
    assert result.plan_frame["warmup_available"].eq(True).all()
    assert result.plan_frame["forward_3d_available"].eq(True).all()


def test_duplicate_source_rows_do_not_inflate_eligible_symbol_count(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=8, duplicate_sources=True)

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-11",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1],
        max_dates=2,
        warmup_trading_days=1,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )

    assert result.plan_frame["eligible_symbol_count"].tolist() == [2, 2]
    assert result.plan_frame["total_symbol_count"].tolist() == [2, 2]


def test_plan_artifacts_include_safety_flags_and_do_not_mutate_cache(tmp_path: Path) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300"], date_count=8)
    before = cache_path.read_text(encoding="utf-8")

    result = build_current_candidates_backfill_plan(
        cache_path=cache_path,
        start_date="2024-01-02",
        end_date="2024-01-11",
        universe="etf_core",
        selection_profile="demo",
        horizons=[1, 3],
        max_dates=3,
        warmup_trading_days=1,
        min_symbol_coverage=2,
        output_dir=tmp_path / "plans",
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert cache_path.read_text(encoding="utf-8") == before
    assert result.plan_frame["no_live_trading"].eq(True).all()
    assert result.plan_frame["no_broker_api"].eq(True).all()
    assert result.plan_frame["no_order_placement"].eq(True).all()
    assert result.plan_frame["no_message_sent"].eq(True).all()
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert metadata["no_order_placement"] is True
    assert metadata["no_message_sent"] is True
    assert metadata["cache_mutated"] is False
    assert metadata["current_candidates_executed"] is False


def test_cli_current_candidates_backfill_plan_works(tmp_path: Path, capsys) -> None:
    cache_path = _write_cache(tmp_path, ["000001", "510300", "600519", "159915"], date_count=12)

    code = cli.main(
        [
            "current-candidates-backfill-plan",
            "--cache-path",
            str(cache_path),
            "--start-date",
            "2024-01-02",
            "--end-date",
            "2024-01-17",
            "--universe",
            "etf_core",
            "--selection-profile",
            "demo",
            "--horizons",
            "1,3,5",
            "--max-dates",
            "4",
            "--warmup-trading-days",
            "5",
            "--min-symbol-coverage",
            "4",
            "--output-dir",
            str(tmp_path / "plans"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "plan_id:" in output.out
    assert "selected_date_count: 3" in output.out
    assert "warmup_feasibility_counts:" in output.out
    assert "No live trading, broker API, order placement, message delivery, or network/API call was invoked." in output.out


def _write_cache(
    tmp_path: Path,
    symbols: list[str],
    *,
    date_count: int,
    duplicate_sources: bool = False,
) -> Path:
    dates = pd.bdate_range("2024-01-02", periods=date_count)
    rows = []
    for symbol in symbols:
        for index, trade_date in enumerate(dates):
            rows.append(_market_row(symbol, trade_date, index, source="AKSHARE_OPTIONAL", upstream_source="TENCENT"))
            if duplicate_sources:
                rows.append(_market_row(symbol, trade_date, index, source="BAOSTOCK_OPTIONAL", upstream_source="BAOSTOCK"))
    path = tmp_path / "daily_bars.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _market_row(
    symbol: str,
    trade_date: pd.Timestamp,
    index: int,
    *,
    source: str,
    upstream_source: str,
) -> dict[str, object]:
    day = trade_date.strftime("%Y-%m-%d")
    return {
        "symbol": symbol,
        "trade_date": day,
        "open": 10 + index,
        "high": 11 + index,
        "low": 9 + index,
        "close": 10.5 + index,
        "volume": 100000 + index,
        "amount": 1000000 + index,
        "pre_close": 10 + index,
        "adj_factor": 1.0,
        "is_suspended": False,
        "limit_up": 12 + index,
        "limit_down": 8 + index,
        "event_time": f"{day} 15:00:00",
        "publish_time": f"{day} 15:20:00",
        "ingest_time": f"{day} 15:30:00",
        "available_time": f"{day} 15:30:00",
        "revision_id": "test",
        "source": source,
        "upstream_source": upstream_source,
    }
