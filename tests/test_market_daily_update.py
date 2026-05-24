import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_daily_update import (
    MarketDailyUpdateRequest,
    build_market_daily_update_plan,
    load_market_daily_update_symbol_manifest,
    run_market_daily_update,
    run_market_daily_update_manifest,
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


def test_load_symbol_manifest_csv_preserves_symbols_and_skips_disabled(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", enabled="true"),
            _manifest_row(symbol="510300", enabled="false", security_type="ETF", preferred_upstream="SINA"),
        ],
    )

    rows = load_market_daily_update_symbol_manifest(manifest_path, settings=_settings(tmp_path).market_daily_update)

    assert [row.symbol for row in rows] == ["000001", "510300"]
    assert rows[0].enabled is True
    assert rows[1].enabled is False
    assert rows[1].security_type == "ETF"
    assert rows[1].preferred_upstream == "SINA"


def test_manifest_disabled_rows_are_skipped(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_manifest_row(symbol="000001", enabled="false")])

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.symbol_results_frame.iloc[0]["status"] == "SKIPPED_DISABLED"
    assert result.cache_write_occurred is False


def test_manifest_dry_run_does_not_mutate_cache(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest_path = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path, reference_source="")],
    )
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )
    before = cache_path.read_text(encoding="utf-8")

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.symbol_results_frame.iloc[0]["status"] == "PASS"
    assert result.cache_write_occurred is False
    assert cache_path.read_text(encoding="utf-8") == before


def test_manifest_real_fetch_without_allow_real_data_is_blocked(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, [_manifest_row(symbol="000001")])

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.symbol_results_frame.iloc[0]["status"] == "BLOCKED_NEEDS_ALLOW_REAL_DATA"
    assert result.cache_write_occurred is False


def test_manifest_accept_without_cache_write_does_not_ingest(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest_path = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path, reference_source="")],
    )
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-03"),
        ],
    )

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    cache = load_market_cache(cache_path, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert result.symbol_results_frame.iloc[0]["preflight_status"] == "ACCEPT"
    assert set(cache["source"]) == {"BAOSTOCK_OPTIONAL"}


def test_manifest_accept_with_cache_write_ingests_fake_local_data(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest_path = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path, reference_source="")],
    )
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )
    cache = load_market_cache(cache_path, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert result.cache_write_occurred is True
    assert bool(result.symbol_results_frame.iloc[0]["cache_write_occurred"]) is True
    assert set(cache["source"]) == {"AKSHARE_OPTIONAL"}


def test_manifest_rejected_preflight_blocks_ingest(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, invalid_ohlc=True)
    manifest_path = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)],
    )
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.symbol_results_frame.iloc[0]["status"] == "BLOCKED_PREFLIGHT_REJECT"
    assert result.cache_write_occurred is False
    assert not cache_path.exists()


def test_manifest_fail_fast_false_continues_after_failed_row(tmp_path: Path) -> None:
    bad_raw, bad_metadata = _write_raw_and_metadata(tmp_path / "bad", invalid_ohlc=True)
    good_raw, good_metadata = _write_raw_and_metadata(tmp_path / "good", symbol="600000")
    manifest_path = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=bad_raw, metadata_path=bad_metadata, notes="bad"),
            _manifest_row(symbol="600000", raw_input=good_raw, metadata_path=good_metadata, reference_source=""),
        ],
    )
    cache_path = _write_cache(tmp_path, [_cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02")])

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=cache_path,
        fail_fast=False,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.symbol_results_frame["status"].tolist() == ["BLOCKED_PREFLIGHT_REJECT", "PASS"]


def test_manifest_fail_fast_true_stops_after_first_failed_row(tmp_path: Path) -> None:
    bad_raw, bad_metadata = _write_raw_and_metadata(tmp_path / "bad", invalid_ohlc=True)
    good_raw, good_metadata = _write_raw_and_metadata(tmp_path / "good", symbol="600000")
    manifest_path = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=bad_raw, metadata_path=bad_metadata),
            _manifest_row(symbol="600000", raw_input=good_raw, metadata_path=good_metadata),
        ],
    )

    result = run_market_daily_update_manifest(
        manifest_path,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        fail_fast=True,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert len(result.symbol_results_frame) == 1
    assert result.symbol_results_frame.iloc[0]["status"] == "BLOCKED_PREFLIGHT_REJECT"


def test_cli_market_daily_update_symbol_manifest_works(tmp_path: Path, capsys) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest_path = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)],
    )
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
            "--symbol-manifest",
            str(manifest_path),
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
    assert "symbol_row_count: 1" in output.out
    assert "cache_write_occurred: False" in output.out
    assert "No live trading or broker API was invoked." in output.out


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


def _write_raw_and_metadata(
    tmp_path: Path,
    *,
    invalid_ohlc: bool = False,
    symbol: str = "000001",
) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    frame = _market_frame(symbol=symbol)
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


def _write_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    manifest_path = tmp_path / "symbol_manifest.csv"
    pd.DataFrame(rows).to_csv(manifest_path, index=False)
    return manifest_path


def _manifest_row(
    *,
    symbol: str,
    enabled: str = "true",
    source: str = "AKSHARE_OPTIONAL",
    dataset_type: str = "market",
    start_date: str = "2024-01-02",
    end_date: str = "2024-01-03",
    security_type: str = "STOCK",
    preferred_upstream: str = "TENCENT",
    require_fields: str = "close,volume,amount",
    reference_source: str = "BAOSTOCK_OPTIONAL",
    strict_provisional: str = "false",
    notes: str = "test row",
    raw_input: Path | None = None,
    metadata_path: Path | None = None,
) -> dict:
    return {
        "symbol": symbol,
        "source": source,
        "dataset_type": dataset_type,
        "start_date": start_date,
        "end_date": end_date,
        "enabled": enabled,
        "security_type": security_type,
        "preferred_upstream": preferred_upstream,
        "require_fields": require_fields,
        "reference_source": reference_source,
        "strict_provisional": strict_provisional,
        "notes": notes,
        "raw_input": str(raw_input) if raw_input is not None else "",
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
    }


def _market_frame(*, symbol: str = "000001") -> pd.DataFrame:
    rows = []
    for trade_date in ["2024-01-02", "2024-01-03"]:
        rows.append(
            {
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
