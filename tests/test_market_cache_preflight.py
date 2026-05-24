import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_cache_preflight import run_market_cache_preflight
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS


def test_preflight_accepts_reliable_source_fields_and_valid_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="000001", source="AKSHARE_OPTIONAL").to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        required_fields=["close", "volume", "amount"],
        config=_settings(tmp_path),
    )

    assert result.status == "ACCEPT"
    assert result.error_count == 0
    assert result.summary_frame.iloc[0]["upstream_source"] == "TENCENT"


def test_preflight_warn_accepts_provisional_etf_source_fields(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="510300", source="AKSHARE_OPTIONAL").to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "SINA", "fund_etf_hist_sina").write_text_to(metadata_path)

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        required_fields=["close", "volume", "amount"],
        config=_settings(tmp_path),
    )

    assert result.status == "WARN_ACCEPT"
    assert set(result.issues_frame["category"]) == {"SOURCE_POLICY_PROVISIONAL"}
    assert result.warning_count == 3


def test_preflight_rejects_required_unavailable_amount(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="510300", source="BAOSTOCK_OPTIONAL").to_csv(input_path, index=False)
    _metadata("BAOSTOCK_OPTIONAL", "BAOSTOCK", "query_history_k_data_plus").write_text_to(metadata_path)

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        required_fields=["amount"],
        config=_settings(tmp_path),
    )

    assert result.status == "REJECT"
    assert result.error_count == 1
    assert result.issues_frame.iloc[0]["category"] == "SOURCE_POLICY_UNAVAILABLE_FIELD"


def test_preflight_rejects_missing_required_canonical_column(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().drop(columns=["available_time"]).to_csv(input_path, index=False)

    result = run_market_cache_preflight(input_path, config=_settings(tmp_path))

    assert result.status == "REJECT"
    assert result.issues_frame.iloc[0]["category"] == "SCHEMA_ERROR"


def test_preflight_rejects_invalid_ohlc(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    frame = _market_frame()
    frame.loc[0, "high"] = 1.0
    frame.loc[0, "low"] = 2.0
    frame.to_csv(input_path, index=False)

    result = run_market_cache_preflight(input_path, config=_settings(tmp_path))

    assert result.status == "REJECT"
    assert "OHLC_SANITY_ERROR" in set(result.issues_frame["category"])


def test_preflight_known_first_window_pre_close_caveat_does_not_reject(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    candidate = _market_frame(symbol="600000", source="AKSHARE_OPTIONAL", pre_close=6.63)
    candidate.loc[1, "pre_close"] = 6.50
    candidate.to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)
    _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "600000", "2024-01-02", pre_close=6.62),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "600000", "2024-01-03", pre_close=6.50),
        ],
    )

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        config=_settings(tmp_path),
    )

    assert result.status == "WARN_ACCEPT"
    assert "KNOWN_CAVEAT" in set(result.issues_frame["category"])
    assert result.error_count == 0
    assert result.comparison_summary_frame.iloc[0]["status"] == "FAIL"


def test_preflight_optional_comparison_pass_supports_accept(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="000001", source="AKSHARE_OPTIONAL").to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)
    _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        config=_settings(tmp_path),
    )

    assert result.status == "ACCEPT"
    assert result.comparison_summary_frame.iloc[0]["status"] == "PASS"


def test_preflight_optional_comparison_fail_rejects_when_not_known_caveat(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="000001", source="AKSHARE_OPTIONAL", close=10.8).to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)
    _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02", close=10.2),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03", close=10.2),
        ],
    )

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        config=_settings(tmp_path),
    )

    assert result.status == "REJECT"
    assert "COMPARISON_FAIL" in set(result.issues_frame["category"])


def test_cli_market_cache_preflight_works(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="000001", source="AKSHARE_OPTIONAL").to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)

    code = cli.main(
        [
            "market-cache-preflight",
            "--input",
            str(input_path),
            "--metadata",
            str(metadata_path),
            "--require-fields",
            "close,volume,amount",
            "--output-dir",
            str(tmp_path / "preflight"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Market cache preflight status: ACCEPT" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_preflight_does_not_mutate_cache(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    _market_frame(symbol="000001", source="AKSHARE_OPTIONAL").to_csv(input_path, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT", "stock_zh_a_hist_tx").write_text_to(metadata_path)
    cache_path = _write_cache(tmp_path, [_cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02")])
    before = cache_path.read_text(encoding="utf-8")

    result = run_market_cache_preflight(
        input_path,
        metadata_path=metadata_path,
        reference_source="BAOSTOCK_OPTIONAL",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["cache_mutated"] is False
    assert cache_path.read_text(encoding="utf-8") == before


def test_preflight_does_not_invoke_live_trading_or_broker_integration(tmp_path: Path) -> None:
    input_path = tmp_path / "raw_data.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_market_cache_preflight(input_path, config=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["market_cache_preflight_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(
                update={"cache_path": tmp_path / "cache" / "daily_bars.csv"}
            ),
            "market_cache_preflight": settings.market_cache_preflight.model_copy(
                update={"output_dir": tmp_path / "preflight"}
            ),
            "market_data_comparison": settings.market_data_comparison.model_copy(
                update={"output_dir": tmp_path / "comparison"}
            ),
        }
    )


def _market_frame(
    *,
    symbol: str = "000001",
    source: str = "AKSHARE_OPTIONAL",
    close: float = 10.2,
    pre_close: float = 10.0,
) -> pd.DataFrame:
    rows = []
    for trade_date in ["2024-01-02", "2024-01-03"]:
        rows.append(
            {
                "symbol": symbol,
                "trade_date": trade_date,
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": close,
                "volume": 1000,
                "amount": 10200,
                "pre_close": pre_close,
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
            }
        )
    return pd.DataFrame(rows)


def _write_cache(tmp_path: Path, rows: list[dict]) -> Path:
    cache_path = tmp_path / "cache" / "daily_bars.csv"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=MARKET_CACHE_COLUMNS).to_csv(cache_path, index=False)
    return cache_path


def _cache_row(
    source: str,
    upstream: str,
    symbol: str,
    trade_date: str,
    *,
    close: float = 10.2,
    pre_close: float = 10.0,
) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": close,
        "volume": 1000,
        "amount": 10200,
        "pre_close": pre_close,
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


class _Metadata:
    def __init__(self, source: str, upstream_source: str, successful_function: str) -> None:
        self.source = source
        self.upstream_source = upstream_source
        self.successful_function = successful_function

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


def _metadata(source: str, upstream_source: str, successful_function: str) -> _Metadata:
    return _Metadata(source, upstream_source, successful_function)
