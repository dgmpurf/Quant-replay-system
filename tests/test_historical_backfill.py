import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
import quant_replay_system.historical_backfill as historical_backfill_module
from quant_replay_system.config import load_settings
from quant_replay_system.historical_backfill import (
    build_historical_backfill_plan,
    load_historical_backfill_manifest,
    run_historical_backfill,
)
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS, load_market_cache


def test_load_historical_backfill_manifest_preserves_symbols(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=tmp_path / "raw1.csv"),
            _manifest_row(symbol="510300", enabled="false", security_type="ETF", preferred_upstream="SINA"),
        ],
    )

    rows = load_historical_backfill_manifest(manifest, settings=_settings(tmp_path).historical_backfill)

    assert [row.symbol for row in rows] == ["000001", "510300"]
    assert rows[0].enabled is True
    assert rows[1].enabled is False
    assert rows[1].security_type == "ETF"
    assert rows[1].preferred_upstream == "SINA"


def test_build_historical_backfill_plan_chunks_date_range(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", start_date="2024-01-01", end_date="2024-01-10", chunk_days="3")],
    )
    rows = load_historical_backfill_manifest(manifest, settings=_settings(tmp_path).historical_backfill)

    plan = build_historical_backfill_plan(rows)

    assert [(task.chunk_start_date, task.chunk_end_date) for task in plan.tasks] == [
        ("2024-01-01", "2024-01-03"),
        ("2024-01-04", "2024-01-06"),
        ("2024-01-07", "2024-01-09"),
        ("2024-01-10", "2024-01-10"),
    ]


def test_historical_backfill_disabled_rows_are_skipped(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", enabled="false")])

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.results_frame.iloc[0]["status"] == "SKIPPED_DISABLED"
    assert result.cache_write_occurred is False


def test_historical_backfill_dry_run_does_not_mutate_cache(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])
    cache_path = _write_cache(tmp_path, [_cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "000001", "2024-01-02")])
    before = cache_path.read_text(encoding="utf-8")

    result = run_historical_backfill(
        manifest,
        cache_path=cache_path,
        config=_settings(tmp_path, cache_path=cache_path),
    )

    assert result.status == "PASS"
    assert result.cache_write_occurred is False
    assert cache_path.read_text(encoding="utf-8") == before


def test_historical_backfill_blocks_real_fetch_without_allow_real_data(tmp_path: Path, monkeypatch) -> None:
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001")])
    fetch_called = False

    def _fail_if_fetch_called(*_args, **_kwargs):
        nonlocal fetch_called
        fetch_called = True
        raise AssertionError("data-source-fetch should not run without allow_real_data")

    monkeypatch.setattr(historical_backfill_module, "run_data_source_fetch", _fail_if_fetch_called)

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert fetch_called is False
    assert result.status == "FAIL"
    assert result.results_frame.iloc[0]["status"] == "BLOCKED_NEEDS_ALLOW_REAL_DATA"
    assert result.cache_write_occurred is False


def test_historical_backfill_raw_input_does_not_require_allow_real_data_or_fetch(tmp_path: Path, monkeypatch) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])
    fetch_called = False

    def _fail_if_fetch_called(*_args, **_kwargs):
        nonlocal fetch_called
        fetch_called = True
        raise AssertionError("data-source-fetch should not run for raw_input rows")

    monkeypatch.setattr(historical_backfill_module, "run_data_source_fetch", _fail_if_fetch_called)

    result = run_historical_backfill(
        manifest,
        allow_real_data=False,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert fetch_called is False
    assert result.status == "PASS"
    assert result.results_frame.iloc[0]["preflight_status"] == "ACCEPT"
    assert result.results_frame.iloc[0]["row_count"] == 2


def test_historical_backfill_preflight_accept_can_pass(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.results_frame.iloc[0]["status"] == "PASS"
    assert result.results_frame.iloc[0]["preflight_status"] == "ACCEPT"


def test_historical_backfill_preflight_reject_blocks_ingest(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, invalid_ohlc=True)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    result = run_historical_backfill(
        manifest,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.results_frame.iloc[0]["status"] == "BLOCKED_PREFLIGHT_REJECT"
    assert result.cache_write_occurred is False
    assert not cache_path.exists()


def test_historical_backfill_accept_cache_write_controls_cache_mutation(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])
    cache_path = tmp_path / "cache" / "daily_bars.csv"

    dry_result = run_historical_backfill(
        manifest,
        cache_path=cache_path,
        accept_cache_write=False,
        config=_settings(tmp_path),
    )

    assert dry_result.cache_write_occurred is False
    assert not cache_path.exists()

    write_result = run_historical_backfill(
        manifest,
        cache_path=cache_path,
        accept_cache_write=True,
        config=_settings(tmp_path),
    )
    cache = load_market_cache(cache_path, config=_settings(tmp_path, cache_path=cache_path))

    assert write_result.status == "PASS"
    assert write_result.cache_write_occurred is True
    assert cache["symbol"].tolist() == ["000001", "000001"]


def test_historical_backfill_fail_fast_false_continues_after_failure(tmp_path: Path) -> None:
    bad_raw, bad_metadata = _write_raw_and_metadata(tmp_path / "bad", invalid_ohlc=True)
    good_raw, good_metadata = _write_raw_and_metadata(tmp_path / "good", symbol="600000")
    manifest = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=bad_raw, metadata_path=bad_metadata),
            _manifest_row(symbol="600000", raw_input=good_raw, metadata_path=good_metadata, reference_source=""),
        ],
    )

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        fail_fast=False,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.results_frame["status"].tolist() == ["BLOCKED_PREFLIGHT_REJECT", "PASS"]


def test_historical_backfill_fail_fast_true_stops_after_failure(tmp_path: Path) -> None:
    bad_raw, bad_metadata = _write_raw_and_metadata(tmp_path / "bad", invalid_ohlc=True)
    good_raw, good_metadata = _write_raw_and_metadata(tmp_path / "good", symbol="600000")
    manifest = _write_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=bad_raw, metadata_path=bad_metadata),
            _manifest_row(symbol="600000", raw_input=good_raw, metadata_path=good_metadata),
        ],
    )

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        fail_fast=True,
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert len(result.results_frame) == 1
    assert result.results_frame.iloc[0]["status"] == "BLOCKED_PREFLIGHT_REJECT"


def test_cli_historical_backfill_works_with_fake_local_data(tmp_path: Path, capsys) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])

    code = cli.main(
        [
            "historical-backfill",
            "--manifest",
            str(manifest),
            "--cache-path",
            str(tmp_path / "cache" / "daily_bars.csv"),
            "--output-dir",
            str(tmp_path / "historical_backfill"),
            "--dry-run",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Historical backfill status: PASS" in output.out
    assert "task_count: 1" in output.out
    assert "cache_write_occurred: False" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_historical_backfill_audit_metadata_has_no_live_trading_or_broker(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path)
    manifest = _write_manifest(tmp_path, [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path)])

    result = run_historical_backfill(
        manifest,
        cache_path=tmp_path / "cache" / "daily_bars.csv",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["historical_backfill_only"] is True


def _settings(tmp_path: Path, *, cache_path: Path | None = None):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(
                update={
                    "cache_path": cache_path or tmp_path / "cache" / "daily_bars.csv",
                    "output_dir": tmp_path / "cache_reports",
                }
            ),
            "market_cache_preflight": settings.market_cache_preflight.model_copy(
                update={"output_dir": tmp_path / "preflight"}
            ),
            "market_data_comparison": settings.market_data_comparison.model_copy(
                update={"output_dir": tmp_path / "comparison"}
            ),
            "data_source_health": settings.data_source_health.model_copy(
                update={"output_dir": tmp_path / "health"}
            ),
            "data_sources": settings.data_sources.model_copy(
                update={"raw_output_dir": tmp_path / "raw"}
            ),
            "historical_backfill": settings.historical_backfill.model_copy(
                update={"output_dir": tmp_path / "historical_backfill"}
            ),
        }
    )


def _write_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest_path = tmp_path / "historical_backfill_manifest.csv"
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
    reference_source: str = "",
    strict_provisional: str = "false",
    chunk_days: str = "",
    raw_input: Path | None = None,
    metadata_path: Path | None = None,
    notes: str = "test row",
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
        "chunk_days": chunk_days,
        "raw_input": str(raw_input) if raw_input is not None else "",
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
        "notes": notes,
    }


def _write_raw_and_metadata(
    tmp_path: Path,
    *,
    invalid_ohlc: bool = False,
    symbol: str = "000001",
    upstream_source: str = "TENCENT",
    successful_function: str = "stock_zh_a_hist_tx",
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
        "symbol": symbol,
        "upstream_source": upstream_source,
        "successful_function": successful_function,
        "created_at": "1970-01-01T00:00:00+00:00",
        "no_live_trading": True,
        "no_broker_api": True,
    }
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return raw_path, metadata_path


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
