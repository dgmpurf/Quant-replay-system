import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_data_cache import (
    MARKET_CACHE_COLUMNS,
    ingest_market_cache_csv,
    query_market_cache,
    summarize_market_cache_status,
)


def test_ingest_canonical_market_csv_into_empty_cache(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame().to_csv(input_path, index=False)
    _metadata("TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)

    result = ingest_market_cache_csv(
        input_path,
        metadata_path=metadata_path,
        config=_settings(tmp_path),
    )

    cached = pd.read_csv(result.cache_path, dtype={"symbol": str})
    assert result.status == "PASS"
    assert result.row_count == 3
    assert result.cache_row_count == 3
    assert result.symbol_count == 2
    assert list(cached.columns) == MARKET_CACHE_COLUMNS


def test_ingest_preserves_six_digit_symbols(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().to_csv(input_path, index=False)

    result = ingest_market_cache_csv(input_path, config=_settings(tmp_path))

    cached = pd.read_csv(result.cache_path, dtype={"symbol": str})
    assert "000001" in set(cached["symbol"])
    assert "510300" in set(cached["symbol"])


def test_duplicate_rows_are_deduplicated_deterministically(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    frame = _market_frame()
    duplicate = frame.iloc[[0]].copy()
    duplicate["close"] = 99.0
    pd.concat([frame, duplicate], ignore_index=True).to_csv(input_path, index=False)

    result = ingest_market_cache_csv(input_path, config=_settings(tmp_path))
    cached = pd.read_csv(result.cache_path, dtype={"symbol": str})
    row = cached[(cached["symbol"] == "000001") & (cached["trade_date"] == "2024-01-02")].iloc[0]

    assert result.cache_row_count == 3
    assert float(row["close"]) == 99.0


def test_query_returns_requested_symbol_and_date_range(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().to_csv(input_path, index=False)
    ingest_market_cache_csv(input_path, config=_settings(tmp_path))

    result = query_market_cache(
        symbol="510300",
        start_date="2024-01-01",
        end_date="2024-05-20",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.row_count == 1
    assert result.result_frame.iloc[0]["symbol"] == "510300"


def test_query_writes_output_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    output_path = tmp_path / "query.csv"
    _market_frame().to_csv(input_path, index=False)
    ingest_market_cache_csv(input_path, config=_settings(tmp_path))

    result = query_market_cache(
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-02",
        output_path=output_path,
        config=_settings(tmp_path),
    )

    exported = pd.read_csv(output_path, dtype={"symbol": str})
    assert result.row_count == 1
    assert exported.iloc[0]["symbol"] == "000001"


def test_status_reports_cache_counts_and_date_range(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().to_csv(input_path, index=False)
    ingest_market_cache_csv(input_path, config=_settings(tmp_path))

    result = summarize_market_cache_status(config=_settings(tmp_path))
    summary = result.summary_frame.iloc[0]

    assert result.status == "PASS"
    assert int(summary["cache_row_count"]) == 3
    assert int(summary["symbol_count"]) == 2
    assert summary["min_trade_date"] == "2024-01-02"
    assert summary["max_trade_date"] == "2024-01-03"


def test_ingest_fails_for_missing_required_column(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    frame = _market_frame().drop(columns=["available_time"])
    frame.to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="missing required columns: available_time"):
        ingest_market_cache_csv(input_path, config=_settings(tmp_path))


def test_ingest_fails_for_invalid_ohlc_sanity(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    frame = _market_frame()
    frame.loc[0, "high"] = 1.0
    frame.loc[0, "low"] = 2.0
    frame.to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="high is less than low"):
        ingest_market_cache_csv(input_path, config=_settings(tmp_path))


def test_metadata_contains_no_live_trading_flags(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame().to_csv(input_path, index=False)
    _metadata("SINA", "fund_etf_hist_sina").write_text_to(metadata_path)

    result = ingest_market_cache_csv(input_path, metadata_path=metadata_path, config=_settings(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    cached = pd.read_csv(result.cache_path, dtype={"symbol": str})

    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert "secret" not in json.dumps(metadata).lower()
    assert set(cached["upstream_source"]) == {"SINA"}
    assert set(cached["successful_function"]) == {"fund_etf_hist_sina"}


def test_baostock_canonical_output_can_be_ingested_into_market_cache(tmp_path: Path) -> None:
    input_path = tmp_path / "baostock_raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    frame = _market_frame().iloc[[0, 1]].copy()
    frame["source"] = "BAOSTOCK_OPTIONAL"
    frame.to_csv(input_path, index=False)
    _metadata("BAOSTOCK", "query_history_k_data_plus", source="BAOSTOCK_OPTIONAL").write_text_to(metadata_path)

    result = ingest_market_cache_csv(input_path, metadata_path=metadata_path, config=_settings(tmp_path))
    cached = pd.read_csv(result.cache_path, dtype={"symbol": str})

    assert result.status == "PASS"
    assert result.cache_row_count == 2
    assert set(cached["source"]) == {"BAOSTOCK_OPTIONAL"}
    assert set(cached["upstream_source"]) == {"BAOSTOCK"}
    assert set(cached["successful_function"]) == {"query_history_k_data_plus"}


def test_cli_market_cache_ingest_query_and_status_work(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "raw_data.csv"
    query_path = tmp_path / "query.csv"
    _market_frame().to_csv(input_path, index=False)

    code = cli.main(
        [
            "market-cache-ingest",
            "--input",
            str(input_path),
            "--cache-path",
            str(tmp_path / "cache" / "daily_bars.csv"),
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    ingest_output = capsys.readouterr()
    assert code == 0
    assert "Market cache status: PASS" in ingest_output.out
    assert "No live trading or broker API was invoked." in ingest_output.out

    code = cli.main(
        [
            "market-cache-query",
            "--symbol",
            "510300",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-05-20",
            "--cache-path",
            str(tmp_path / "cache" / "daily_bars.csv"),
            "--output",
            str(query_path),
        ]
    )
    query_output = capsys.readouterr()
    assert code == 0
    assert "Market cache query status: PASS" in query_output.out
    assert query_path.exists()

    code = cli.main(
        [
            "market-cache-status",
            "--cache-path",
            str(tmp_path / "cache" / "daily_bars.csv"),
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    status_output = capsys.readouterr()
    assert code == 0
    assert "Market cache status: PASS" in status_output.out
    assert "symbol_count: 2" in status_output.out


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().to_csv(input_path, index=False)

    result = ingest_market_cache_csv(input_path, config=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["market_data_cache_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(
                update={
                    "cache_path": tmp_path / "cache" / "daily_bars.csv",
                    "output_dir": tmp_path / "reports",
                }
            )
        }
    )


def _market_frame() -> pd.DataFrame:
    base = {
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "volume": 1000,
        "amount": 10200,
        "pre_close": 10.0,
        "adj_factor": 1.0,
        "is_suspended": False,
        "limit_up": "",
        "limit_down": "",
        "event_time": "2024-01-02 15:00:00",
        "publish_time": "2024-01-02 15:30:00",
        "ingest_time": "2024-01-02 16:00:00",
        "available_time": "2024-01-02 15:30:00",
        "revision_id": "v1",
        "source": "AKSHARE_OPTIONAL",
    }
    return pd.DataFrame(
        [
            {
                **base,
                "symbol": "000001",
                "trade_date": "2024-01-02",
            },
            {
                **base,
                "symbol": "000001",
                "trade_date": "2024-01-03",
                "event_time": "2024-01-03 15:00:00",
                "publish_time": "2024-01-03 15:30:00",
                "ingest_time": "2024-01-03 16:00:00",
                "available_time": "2024-01-03 15:30:00",
            },
            {
                **base,
                "symbol": "510300",
                "trade_date": "2024-01-02",
            },
        ]
    )


class _Metadata:
    def __init__(self, upstream_source: str, successful_function: str, *, source: str = "AKSHARE_OPTIONAL") -> None:
        self.upstream_source = upstream_source
        self.successful_function = successful_function
        self.source = source

    def write_text_to(self, path: Path) -> None:
        payload = {
            "source": self.source,
            "dataset_type": "market",
            "upstream_source": self.upstream_source,
            "successful_function": self.successful_function,
            "created_at": "1970-01-01T00:00:00+00:00",
            "no_live_trading": True,
            "no_broker_api": True,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")


def _metadata(upstream_source: str, successful_function: str, *, source: str = "AKSHARE_OPTIONAL") -> _Metadata:
    return _Metadata(upstream_source, successful_function, source=source)
