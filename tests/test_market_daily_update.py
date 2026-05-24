import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_daily_update import (
    MarketDailyUpdateRequest,
    build_market_daily_update_plan,
    run_market_daily_update,
)
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS, load_market_cache


def test_build_market_daily_update_plan_uses_raw_and_skips_cache_write() -> None:
    request = MarketDailyUpdateRequest(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input="raw_data.csv",
        dry_run=True,
        accept_cache_write=False,
    )

    plan = build_market_daily_update_plan(request)

    assert plan == [
        "use_existing_raw_input",
        "market_cache_preflight",
        "cache_write_skipped",
        "market_cache_status",
    ]


def test_daily_update_dry_run_does_not_mutate_cache(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )
    before = cache_path.read_text(encoding="utf-8")

    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input=raw_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        dry_run=True,
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.cache_write_occurred is False
    assert "cache_write_skipped" in set(result.steps_frame["step_name"])
    assert cache_path.read_text(encoding="utf-8") == before


def test_daily_update_accept_without_cache_write_does_not_ingest(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )

    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input=raw_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        accept_cache_write=False,
        config=_settings(tmp_path),
    )
    cache = load_market_cache(cache_path, config=_settings(tmp_path))

    assert result.preflight_result is not None
    assert result.preflight_result.status == "ACCEPT"
    assert result.cache_write_occurred is False
    assert set(cache["source"]) == {"BAOSTOCK_OPTIONAL"}


def test_daily_update_accept_with_cache_write_ingests(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input=raw_path,
        metadata_path=metadata_path,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )
    cache = load_market_cache(cache_path, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert result.cache_write_occurred is True
    assert "market_cache_ingest" in set(result.steps_frame["step_name"])
    assert set(cache["source"]) == {"AKSHARE_OPTIONAL"}
    assert cache["symbol"].tolist() == ["000001", "000001"]


def test_daily_update_rejected_preflight_blocks_ingest(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, invalid_ohlc=True)
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input=raw_path,
        metadata_path=metadata_path,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.cache_write_occurred is False
    assert "market_cache_ingest" in set(result.steps_frame["step_name"])
    ingest_step = result.steps_frame.loc[result.steps_frame["step_name"] == "market_cache_ingest"].iloc[0]
    assert ingest_step["status"] == "SKIPPED"
    assert not cache_path.exists()


def test_daily_update_real_source_without_allow_real_data_is_blocked(tmp_path: Path) -> None:
    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.preflight_result is None
    assert result.steps_frame.iloc[0]["step_name"] == "real_data_guardrail"
    assert result.steps_frame.iloc[0]["status"] == "FAIL"


def test_cli_market_daily_update_works_with_raw_input(tmp_path: Path, capsys) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )

    code = cli.main(
        [
            "market-daily-update",
            "--source",
            "AKSHARE_OPTIONAL",
            "--symbol",
            "000001",
            "--start-date",
            "2024-01-02",
            "--end-date",
            "2024-01-03",
            "--raw-input",
            str(raw_path),
            "--metadata",
            str(metadata_path),
            "--reference-source",
            "BAOSTOCK_OPTIONAL",
            "--cache-path",
            str(cache_path),
            "--output-dir",
            str(tmp_path / "daily_update"),
            "--dry-run",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Market daily update status: PASS" in output.out
    assert "cache_write_occurred: False" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_daily_update_does_not_invoke_live_trading_or_broker_integration(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    result = run_market_daily_update(
        source="AKSHARE_OPTIONAL",
        symbol="000001",
        start_date="2024-01-02",
        end_date="2024-01-03",
        raw_input=raw_path,
        metadata_path=metadata_path,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["market_daily_update_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(
                update={
                    "cache_path": tmp_path / "cache" / "daily_bars.csv",
                    "output_dir": tmp_path / "cache_reports",
                }
            ),
            "market_cache_preflight": settings.market_cache_preflight.model_copy(
                update={"output_dir": tmp_path / "preflight"}
            ),
            "market_data_comparison": settings.market_data_comparison.model_copy(
                update={"output_dir": tmp_path / "comparison"}
            ),
            "market_daily_update": settings.market_daily_update.model_copy(
                update={"output_dir": tmp_path / "daily_update"}
            ),
        }
    )


def _write_raw_and_metadata(tmp_path: Path, *, invalid_ohlc: bool = False) -> tuple[Path, Path]:
    raw_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    frame = _market_frame()
    if invalid_ohlc:
        frame.loc[0, "high"] = 1.0
        frame.loc[0, "low"] = 2.0
    frame.to_csv(raw_path, index=False)
    metadata = {
        "source": "AKSHARE_OPTIONAL",
        "dataset_type": "market",
        "upstream_source": "TENCENT",
        "successful_function": "stock_zh_a_hist_tx",
        "created_at": "1970-01-01T00:00:00+00:00",
        "no_live_trading": True,
        "no_broker_api": True,
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return raw_path, metadata_path


def _market_frame() -> pd.DataFrame:
    rows = []
    for trade_date in ["2024-01-02", "2024-01-03"]:
        rows.append(
            {
                "symbol": "000001",
                "trade_date": trade_date,
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "amount": 10200,
                "pre_close": 10.0,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": 11.0,
                "limit_down": 9.0,
                "event_time": f"{trade_date} 15:00:00",
                "publish_time": f"{trade_date} 15:30:00",
                "ingest_time": f"{trade_date} 16:00:00",
                "available_time": f"{trade_date} 15:30:00",
                "revision_id": "v1",
                "source": "AKSHARE_OPTIONAL",
            }
        )
    return pd.DataFrame(rows)


def _write_cache(tmp_path: Path, rows: list[dict]) -> Path:
    cache_path = tmp_path / "cache" / "daily_bars.csv"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=MARKET_CACHE_COLUMNS).to_csv(cache_path, index=False)
    return cache_path


def _cache_row(source: str, upstream: str, symbol: str, trade_date: str) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "volume": 1000,
        "amount": 10200,
        "pre_close": 10.0,
        "adj_factor": 1.0,
        "is_suspended": False,
        "limit_up": 11.0,
        "limit_down": 9.0,
        "event_time": f"{trade_date} 15:00:00",
        "publish_time": f"{trade_date} 15:30:00",
        "ingest_time": f"{trade_date} 16:00:00",
        "available_time": f"{trade_date} 15:30:00",
        "revision_id": "v1",
        "source": source,
        "upstream_source": upstream,
        "successful_function": "query_history_k_data_plus" if source == "BAOSTOCK_OPTIONAL" else "stock_zh_a_hist_tx",
        "fetched_at": "1970-01-01T00:00:00+00:00",
        "cache_ingested_at": "1970-01-01T00:00:00+00:00",
    }
