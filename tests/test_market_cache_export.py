import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_cache_export import (
    build_cache_export_pipeline_manifest,
    load_market_cache_export_manifest,
    run_market_cache_export,
)
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS, ingest_market_cache_csv


def test_manifest_loading_preserves_leading_zero_symbols(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])

    rows = load_market_cache_export_manifest(manifest, settings=_settings(tmp_path).market_cache_export)

    assert rows[0].symbol == "000001"
    assert rows[0].source == "AKSHARE_OPTIONAL"
    assert rows[0].upstream_source == "TENCENT"


def test_disabled_manifest_rows_are_skipped(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(
        tmp_path,
        [
            _manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT", enabled="true"),
            _manifest_row("510300", "AKSHARE_OPTIONAL", "SINA", enabled="false"),
        ],
    )

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert result.export_rows_frame["status"].tolist() == ["PASS", "SKIPPED_DISABLED"]
    assert set(result.exported_market_frame["symbol"]) == {"000001"}


def test_explicit_source_upstream_query_returns_only_selected_rows(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert result.row_count == 2
    assert set(result.exported_market_frame["source"]) == {"AKSHARE_OPTIONAL"}
    assert set(result.exported_market_frame["upstream_source"]) == {"TENCENT"}
    assert int(result.exported_market_frame.duplicated(["symbol", "trade_date"]).sum()) == 0


def test_export_rejects_duplicate_symbol_trade_date_rows(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(
        tmp_path,
        [
            _manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT", start_date="2024-01-02", end_date="2024-01-03"),
            _manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT", start_date="2024-01-02", end_date="2024-01-02"),
        ],
    )

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.status == "FAIL"
    assert "DUPLICATE_BUSINESS_KEY" in set(result.issues_frame["category"])
    assert result.duplicate_key_count == 1


def test_export_rejects_missing_rows(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(
        tmp_path,
        [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT", start_date="2024-02-01", end_date="2024-02-02")],
    )

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.status == "FAIL"
    assert "MISSING_ROWS" in set(result.issues_frame["category"])
    assert result.row_count == 0


def test_export_output_has_canonical_market_columns_and_preserves_symbols(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])

    result = run_market_cache_export(manifest, config=_settings(tmp_path))
    exported = pd.read_csv(result.exported_market_csv_path, dtype={"symbol": str})

    assert result.status == "PASS"
    assert set(MARKET_CACHE_COLUMNS).issubset(exported.columns)
    assert {"symbol", "trade_date", "open", "close", "source"}.issubset(exported.columns)
    assert exported["symbol"].tolist() == ["000001", "000001"]


def test_pipeline_manifest_generation_uses_local_csv_paths(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])
    universe = tmp_path / "universe.csv"
    calendar = tmp_path / "calendar.csv"
    universe.write_text("symbol\n000001\n", encoding="utf-8")
    calendar.write_text("trade_date\n2024-01-02\n", encoding="utf-8")

    result = run_market_cache_export(
        manifest,
        build_pipeline_manifest=True,
        universe=universe,
        trading_calendar=calendar,
        config=_settings(tmp_path),
    )
    payload = json.loads(result.pipeline_manifest_path.read_text(encoding="utf-8"))

    assert result.status == "PASS"
    assert result.pipeline_manifest_path == result.artifact_paths["generated_pipeline_manifest"]
    assert [dataset["source"] for dataset in payload["datasets"]] == ["LOCAL_CSV", "LOCAL_CSV", "LOCAL_CSV"]
    assert payload["datasets"][0]["input_path"] == str(result.exported_market_csv_path)


def test_build_cache_export_pipeline_manifest_writes_expected_shape(tmp_path: Path) -> None:
    manifest_path = build_cache_export_pipeline_manifest(
        market_path=tmp_path / "market.csv",
        universe_path=tmp_path / "universe.csv",
        trading_calendar_path=tmp_path / "calendar.csv",
        output_path=tmp_path / "manifest.json",
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["dataset_type"] for item in payload["datasets"]] == ["market", "universe", "trading_calendar"]


def test_cli_market_cache_export_works(tmp_path: Path, monkeypatch, capsys) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])
    monkeypatch.setattr("quant_replay_system.cli.load_settings", lambda path: _settings(tmp_path))

    code = cli.main(["market-cache-export", "--manifest", str(manifest)])
    output = capsys.readouterr()

    assert code == 0
    assert "Market cache export status: PASS" in output.out
    assert "duplicate_key_count: 0" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_export_does_not_mutate_market_cache(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    cache_path = _settings(tmp_path).market_data_cache.cache_path
    before_hash = _sha256(cache_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert _sha256(cache_path) == before_hash
    assert result.audit_metadata["cache_mutated"] is False


def test_no_live_trading_broker_or_network_calls_are_used(tmp_path: Path) -> None:
    _ingest_multi_source_cache(tmp_path)
    manifest = _manifest(tmp_path, [_manifest_row("000001", "AKSHARE_OPTIONAL", "TENCENT")])

    result = run_market_cache_export(manifest, config=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False
    assert result.audit_metadata["market_cache_export_only"] is True


def test_manifest_missing_required_column_fails_clearly(tmp_path: Path) -> None:
    manifest = tmp_path / "bad_manifest.csv"
    pd.DataFrame([{"symbol": "000001"}]).to_csv(manifest, index=False)

    with pytest.raises(ValueError, match="missing columns"):
        load_market_cache_export_manifest(manifest, settings=_settings(tmp_path).market_cache_export)


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
            "market_cache_export": settings.market_cache_export.model_copy(
                update={
                    "output_dir": tmp_path / "export_reports",
                    "export_output_dir": tmp_path / "manual_cache_exports",
                    "manifest_output_dir": tmp_path / "manual_manifests",
                }
            ),
        }
    )


def _market_frame(source: str = "AKSHARE_OPTIONAL") -> pd.DataFrame:
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
        "source": source,
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


def _ingest_multi_source_cache(tmp_path: Path) -> None:
    akshare_input = tmp_path / "akshare_raw_data.csv"
    akshare_metadata = tmp_path / "akshare_metadata.json"
    baostock_input = tmp_path / "baostock_raw_data.csv"
    baostock_metadata = tmp_path / "baostock_metadata.json"

    _market_frame("AKSHARE_OPTIONAL").to_csv(akshare_input, index=False)
    _metadata("AKSHARE_OPTIONAL", "TENCENT").write_text_to(akshare_metadata)
    ingest_market_cache_csv(akshare_input, metadata_path=akshare_metadata, config=_settings(tmp_path))

    baostock = _market_frame("BAOSTOCK_OPTIONAL").iloc[[0, 1]].copy()
    baostock["volume"] = baostock["volume"] + 1
    baostock["amount"] = baostock["amount"] + 1
    baostock.to_csv(baostock_input, index=False)
    _metadata("BAOSTOCK_OPTIONAL", "BAOSTOCK").write_text_to(baostock_metadata)
    ingest_market_cache_csv(baostock_input, metadata_path=baostock_metadata, config=_settings(tmp_path))


def _manifest(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    manifest = tmp_path / "reviewed_cache_export.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    return manifest


def _manifest_row(
    symbol: str,
    source: str,
    upstream_source: str,
    *,
    start_date: str = "2024-01-02",
    end_date: str = "2024-01-03",
    enabled: str = "true",
) -> dict[str, str]:
    return {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "source": source,
        "upstream_source": upstream_source,
        "enabled": enabled,
        "security_type": "STOCK" if symbol.startswith(("0", "6")) else "ETF",
        "require_fields": "close,volume,amount",
        "notes": "test row",
    }


class _Metadata:
    def __init__(self, source: str, upstream_source: str) -> None:
        self.source = source
        self.upstream_source = upstream_source

    def write_text_to(self, path: Path) -> None:
        payload = {
            "source": self.source,
            "dataset_type": "market",
            "upstream_source": self.upstream_source,
            "successful_function": "test_function",
            "created_at": "1970-01-01T00:00:00+00:00",
            "no_live_trading": True,
            "no_broker_api": True,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")


def _metadata(source: str, upstream_source: str) -> _Metadata:
    return _Metadata(source, upstream_source)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
