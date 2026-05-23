import builtins
import json
import sys
from types import ModuleType
from pathlib import Path

import pandas as pd
import pytest

import quant_replay_system.data_sources as data_sources
from quant_replay_system import cli
from quant_replay_system.config import DataSourceSettings
from quant_replay_system.data_sources import (
    DataSourceRequest,
    from_baostock_code,
    get_data_source_adapter,
    infer_akshare_market_symbol_type,
    infer_baostock_exchange_prefix,
    list_data_source_adapters,
    normalize_tencent_raw_market_output,
    run_data_source_fetch,
    to_baostock_code,
)
from quant_replay_system.market_data_cache import ingest_market_cache_csv


def test_local_csv_adapter_copies_and_loads_local_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="LOCAL_CSV",
            dataset_type="market",
            input_path=input_path,
        ),
        settings=_settings(tmp_path),
    )

    assert result.source == "LOCAL_CSV"
    assert result.dataset_type == "market"
    assert result.row_count == 2
    assert result.artifact_paths["raw_data"].exists()
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str, "name": str})
    assert list(exported["symbol"]) == ["AAA", "BBB"]


def test_mock_adapter_uses_configured_mock_data(tmp_path: Path) -> None:
    result = run_data_source_fetch(
        DataSourceRequest(source="MOCK", dataset_type="market"),
        settings=_settings(tmp_path),
    )

    assert result.source == "MOCK"
    assert result.row_count > 0
    assert result.artifact_paths["raw_data"].exists()
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    assert "symbol" in exported.columns


def test_missing_local_input_path_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Local CSV input not found"):
        run_data_source_fetch(
            DataSourceRequest(
                source="LOCAL_CSV",
                dataset_type="market",
                input_path=tmp_path / "missing.csv",
            ),
            settings=_settings(tmp_path),
        )


def test_unknown_adapter_fails_clearly() -> None:
    with pytest.raises(ValueError, match="Unknown data source adapter"):
        get_data_source_adapter("NOT_A_SOURCE")


def test_real_network_adapter_is_blocked_by_default(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="AKSHARE_OPTIONAL", dataset_type="market"),
            settings=_settings(tmp_path),
        )


def test_allow_real_data_flag_is_required_for_real_adapter_without_importing_akshare(
    tmp_path: Path,
    monkeypatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "akshare":
            raise AssertionError("akshare should not be imported when real data is blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="AKSHARE_OPTIONAL", dataset_type="market"),
            settings=_settings(tmp_path),
        )


def test_real_adapter_with_allow_flag_is_still_disabled_by_config(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="disabled by config"):
        run_data_source_fetch(
            DataSourceRequest(source="AKSHARE_OPTIONAL", dataset_type="market", allow_real_data=True),
            settings=_settings(tmp_path),
        )


def test_akshare_missing_installation_returns_clear_error_in_real_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    original_import = builtins.__import__
    monkeypatch.delitem(sys.modules, "akshare", raising=False)

    def guarded_import(name, *args, **kwargs):
        if name == "akshare":
            raise ImportError("akshare unavailable in offline test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError, match="python -m pip install akshare"):
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                allow_real_data=True,
                symbol="510300",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_akshare_unsupported_dataset_returns_not_implemented(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare_module())

    with pytest.raises(NotImplementedError, match="does not support dataset_type"):
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="corporate_actions",
                allow_real_data=True,
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_akshare_universe_fetch_is_blocked_without_allow_real_data(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="AKSHARE_OPTIONAL", dataset_type="universe", as_of_date="2024-05-20"),
            settings=_settings(tmp_path),
        )


def test_akshare_universe_does_not_import_when_blocked(tmp_path: Path, monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "akshare":
            raise AssertionError("akshare should not be imported when universe fetch is blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="AKSHARE_OPTIONAL", dataset_type="universe", as_of_date="2024-05-20"),
            settings=_settings(tmp_path),
        )


def test_akshare_universe_missing_installation_returns_clear_error(tmp_path: Path, monkeypatch) -> None:
    original_import = builtins.__import__
    monkeypatch.delitem(sys.modules, "akshare", raising=False)

    def guarded_import(name, *args, **kwargs):
        if name == "akshare":
            raise ImportError("akshare unavailable in offline test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError, match="python -m pip install akshare"):
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="universe",
                allow_real_data=True,
                as_of_date="2024-05-20",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_tushare_adapter_is_registered() -> None:
    adapters = list_data_source_adapters()

    assert "TUSHARE_OPTIONAL" in adapters
    assert "TUSHARE_OPTIONAL" not in list_data_source_adapters(include_real=False)


def test_tushare_adapter_blocks_without_allow_real_data(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="TUSHARE_OPTIONAL", dataset_type="market"),
            settings=_settings(tmp_path),
        )


def test_tushare_adapter_does_not_import_when_blocked(tmp_path: Path, monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "tushare":
            raise AssertionError("tushare should not be imported when real data is blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="TUSHARE_OPTIONAL", dataset_type="market"),
            settings=_settings(tmp_path),
        )


def test_tushare_missing_token_returns_clear_error_without_importing_tushare(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    monkeypatch.setattr("quant_replay_system.data_sources._read_env_file_value", lambda path, key: "")
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "tushare":
            raise AssertionError("tushare should not be imported before token validation")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="TUSHARE_OPTIONAL",
                dataset_type="market",
                allow_real_data=True,
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )

    message = str(exc_info.value)
    assert "TUSHARE_TOKEN is required" in message
    assert "fake_token" not in message


def test_tushare_missing_installation_returns_clear_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "fake_token")
    monkeypatch.delitem(sys.modules, "tushare", raising=False)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "tushare":
            raise ImportError("tushare unavailable in offline test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError, match="python -m pip install tushare"):
        run_data_source_fetch(
            DataSourceRequest(
                source="TUSHARE_OPTIONAL",
                dataset_type="market",
                allow_real_data=True,
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_tushare_market_success_writes_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "fake_token")
    fake_tushare = _fake_tushare_module()
    monkeypatch.setitem(sys.modules, "tushare", fake_tushare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="TUSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001.SZ",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert result.source == "TUSHARE_OPTIONAL"
    assert result.row_count == 2
    assert {"symbol", "trade_date", "open", "close", "available_time", "source"}.issubset(exported.columns)
    assert exported["symbol"].eq("000001.SZ").all()
    assert exported["source"].eq("TUSHARE_OPTIONAL").all()
    assert metadata["token_present"] is True
    assert "fake_token" not in json.dumps(metadata)
    assert fake_tushare.calls[0]["token"] == "fake_token"
    assert fake_tushare.calls[1]["function"] == "daily"


def test_tushare_universe_success_writes_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "fake_token")
    fake_tushare = _fake_tushare_module()
    monkeypatch.setitem(sys.modules, "tushare", fake_tushare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="TUSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="all",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert result.row_count == 3
    assert list(exported.columns) == _UNIVERSE_COLUMNS
    assert set(exported["instrument_type"]) == {"STOCK", "ETF"}
    assert exported["source"].eq("TUSHARE_OPTIONAL").all()
    assert metadata["token_present"] is True
    assert "fake_token" not in json.dumps(metadata)
    assert {"stock_basic", "fund_basic"}.issubset({call["function"] for call in fake_tushare.calls})


def test_tushare_trading_calendar_success_writes_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "fake_token")
    fake_tushare = _fake_tushare_module()
    monkeypatch.setitem(sys.modules, "tushare", fake_tushare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="TUSHARE_OPTIONAL",
            dataset_type="trading_calendar",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"])

    assert result.row_count == 3
    assert {"trade_date", "is_trading_day", "session_open", "session_close", "decision_time", "reason"}.issubset(exported.columns)
    assert metadata["token_present"] is True
    assert "fake_token" not in json.dumps(metadata)


def test_baostock_adapter_is_registered() -> None:
    adapters = list_data_source_adapters()

    assert "BAOSTOCK_OPTIONAL" in adapters
    assert "BAOSTOCK_OPTIONAL" not in list_data_source_adapters(include_real=False)


def test_baostock_adapter_blocks_without_allow_real_data(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="BAOSTOCK_OPTIONAL", dataset_type="market", symbol="000001"),
            settings=_settings(tmp_path),
        )


def test_baostock_adapter_does_not_import_when_blocked(tmp_path: Path, monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "baostock":
            raise AssertionError("baostock should not be imported when real data is blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="requires explicit --allow-real-data"):
        run_data_source_fetch(
            DataSourceRequest(source="BAOSTOCK_OPTIONAL", dataset_type="market", symbol="000001"),
            settings=_settings(tmp_path),
        )


def test_baostock_missing_installation_returns_clear_error(tmp_path: Path, monkeypatch) -> None:
    original_import = builtins.__import__
    monkeypatch.delitem(sys.modules, "baostock", raising=False)

    def guarded_import(name, *args, **kwargs):
        if name == "baostock":
            raise ImportError("baostock unavailable in offline test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError, match="python -m pip install baostock"):
        run_data_source_fetch(
            DataSourceRequest(
                source="BAOSTOCK_OPTIONAL",
                dataset_type="market",
                allow_real_data=True,
                symbol="000001",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_baostock_symbol_conversion_preserves_six_digit_codes() -> None:
    assert infer_baostock_exchange_prefix("000001") == "sz"
    assert infer_baostock_exchange_prefix("600000") == "sh"
    assert infer_baostock_exchange_prefix("510300") == "sh"
    assert to_baostock_code("000001") == "sz.000001"
    assert to_baostock_code("600000") == "sh.600000"
    assert to_baostock_code("510300") == "sh.510300"
    assert from_baostock_code("sz.000001") == "000001"
    assert from_baostock_code("600000.SH") == "600000"


def test_baostock_market_success_writes_canonical_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    fake_baostock = _fake_baostock_module()
    monkeypatch.setitem(sys.modules, "baostock", fake_baostock)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="BAOSTOCK_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.source == "BAOSTOCK_OPTIONAL"
    assert result.row_count == 2
    assert list(exported.columns) == _canonical_market_columns()
    assert exported["symbol"].tolist() == ["000001", "000001"]
    assert exported["source"].eq("BAOSTOCK_OPTIONAL").all()
    assert metadata["baostock_code"] == "sz.000001"
    assert metadata["upstream_source"] == "BAOSTOCK"
    assert metadata["successful_function"] == "query_history_k_data_plus"
    assert metadata["attempted_upstreams"] == ["BAOSTOCK"]
    assert metadata["allow_real_data"] is True
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False
    assert fake_baostock.calls[0]["function"] == "login"
    assert fake_baostock.calls[1]["function"] == "query_history_k_data_plus"
    assert fake_baostock.calls[1]["code"] == "sz.000001"
    assert fake_baostock.calls[-1]["function"] == "logout"


def test_baostock_market_success_preserves_etf_symbol(tmp_path: Path, monkeypatch) -> None:
    fake_baostock = _fake_baostock_module(symbol_code="sh.510300")
    monkeypatch.setitem(sys.modules, "baostock", fake_baostock)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="BAOSTOCK_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="510300",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.row_count == 2
    assert exported["symbol"].tolist() == ["510300", "510300"]
    assert metadata["baostock_code"] == "sh.510300"
    assert fake_baostock.calls[1]["code"] == "sh.510300"


def test_baostock_unsupported_dataset_returns_not_implemented(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "baostock", _fake_baostock_module())

    with pytest.raises(NotImplementedError, match="Supported dataset types: market"):
        run_data_source_fetch(
            DataSourceRequest(
                source="BAOSTOCK_OPTIONAL",
                dataset_type="universe",
                allow_real_data=True,
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )


def test_infer_akshare_market_symbol_type_etf_and_stock_and_index() -> None:
    assert infer_akshare_market_symbol_type("510300") == "ETF"
    assert infer_akshare_market_symbol_type("159915") == "ETF"
    assert infer_akshare_market_symbol_type("000001") == "STOCK"
    assert infer_akshare_market_symbol_type("000300") == "INDEX"
    assert infer_akshare_market_symbol_type("ABC") == "UNKNOWN"


def test_akshare_success_path_with_fake_module_writes_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    fake_akshare = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="510300",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    assert result.source == "AKSHARE_OPTIONAL"
    assert result.row_count == 2
    assert fake_akshare.calls[0]["function"] == "fund_etf_hist_sina"
    assert fake_akshare.calls[0]["symbol"] == "sh510300"
    assert result.artifact_paths["raw_data"].exists()
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    assert {"symbol", "trade_date", "open", "close", "available_time"}.issubset(exported.columns)
    assert exported["symbol"].eq("510300").all()
    assert exported["source"].eq("AKSHARE_OPTIONAL").all()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["adapter_status"] == "SUCCESS"
    assert metadata["symbol"] == "510300"
    assert metadata["allow_real_data"] is True
    assert metadata["inferred_symbol_type"] == "ETF"
    assert metadata["attempted_functions"] == ["fund_etf_hist_sina"]
    assert metadata["attempted_upstreams"] == ["SINA"]
    assert metadata["successful_function"] == "fund_etf_hist_sina"
    assert metadata["upstream_source"] == "SINA"
    assert metadata["fallback_used"] is False
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_akshare_stock_market_success_uses_stock_route(tmp_path: Path, monkeypatch) -> None:
    fake_akshare = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert result.row_count == 2
    assert exported["symbol"].eq("000001").all()
    assert fake_akshare.calls[0]["function"] == "stock_zh_a_hist_tx"
    assert fake_akshare.calls[0]["symbol"] == "sz000001"
    assert metadata["inferred_symbol_type"] == "STOCK"
    assert metadata["attempted_functions"] == ["stock_zh_a_hist_tx"]
    assert metadata["attempted_upstreams"] == ["TENCENT"]
    assert metadata["successful_function"] == "stock_zh_a_hist_tx"
    assert metadata["upstream_source"] == "TENCENT"
    assert metadata["fallback_used"] is False


def test_akshare_tencent_amount_field_maps_to_volume_shares(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def stock_zh_a_hist_tx(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist_tx", **kwargs})
        return pd.DataFrame(
            [
                {"date": "2024-01-02", "open": 10.0, "close": 10.2, "high": 10.5, "low": 9.8, "amount": 1000},
                {"date": "2024-01-03", "open": 10.2, "close": 10.6, "high": 10.8, "low": 10.1, "amount": 1100},
            ]
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert exported["symbol"].tolist() == ["000001", "000001"]
    assert exported["volume"].tolist() == [100000, 110000]
    assert exported["amount"].tolist() == [0, 0]
    assert "TENCENT_VOLUME_CONVERTED_FROM_HANDS_TO_SHARES" in metadata["mapping_warnings"]
    assert "TENCENT_AMOUNT_FIELD_INTERPRETED_AS_VOLUME_HANDS" in metadata["mapping_warnings"]
    assert "TENCENT_TURNOVER_AMOUNT_FIELD_UNAVAILABLE" in metadata["mapping_warnings"]


def test_tencent_raw_list_maps_volume_and_turnover_amount() -> None:
    raw = [
        ["2024-01-02", "7.83", "7.65", "7.86", "7.65", "1158366.00", {}, "0.60", "107574.23", ""]
    ]

    normalized = normalize_tencent_raw_market_output(raw, symbol="sz000001")
    prepared, warnings = data_sources._prepare_tencent_stock_market_frame(normalized)

    assert float(prepared.iloc[0]["volume"]) == 115836600
    assert float(prepared.iloc[0]["amount"]) == 1075742300
    assert "TENCENT_VOLUME_CONVERTED_FROM_HANDS_TO_SHARES" in warnings
    assert "TENCENT_AMOUNT_CONVERTED_FROM_WAN_YUAN_TO_YUAN" in warnings


def test_fetch_tencent_stock_market_raw_parses_fake_payload(monkeypatch) -> None:
    class FakeResponse:
        text = (
            'kline_day2024={"data":{"sz000001":{"day":[["2024-01-02","7.83","7.65",'
            '"7.86","7.65","1158366.00",{},"0.60","107574.23",""]]}}}'
        )

        def raise_for_status(self) -> None:
            return None

    def fake_get(url, params, timeout):
        assert "proxy.finance.qq.com" in url
        assert params["param"].startswith("sz000001,day,2024-01-01")
        assert timeout == 15
        return FakeResponse()

    monkeypatch.setattr(data_sources, "_import_requests_get", lambda: fake_get)

    frame = data_sources.fetch_tencent_stock_market_raw(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
            allow_real_data=True,
        )
    )

    assert frame.iloc[0]["date"] == "2024-01-02"
    assert frame.iloc[0]["tencent_volume_hands"] == "1158366.00"
    assert frame.iloc[0]["tencent_turnover_amount_10k_yuan"] == "107574.23"


def test_akshare_tencent_raw_turnover_path_maps_amount_yuan(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")
    module.__file__ = "fake-akshare.py"

    def stock_zh_a_hist_tx(**kwargs):
        raise AssertionError("AKShare truncated DataFrame path should not be called when raw path succeeds")

    def fake_raw(request):
        return normalize_tencent_raw_market_output(
            [
                ["2024-01-02", "7.83", "7.65", "7.86", "7.65", "1158366.00", {}, "0.60", "107574.23", ""]
            ],
            symbol="sz000001",
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)
    monkeypatch.setattr(data_sources, "fetch_tencent_stock_market_raw", fake_raw)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert exported.iloc[0]["symbol"] == "000001"
    assert float(exported.iloc[0]["volume"]) == 115836600
    assert float(exported.iloc[0]["amount"]) == 1075742300
    assert "TENCENT_AMOUNT_CONVERTED_FROM_WAN_YUAN_TO_YUAN" in metadata["mapping_warnings"]
    assert "TENCENT_TURNOVER_AMOUNT_FIELD_UNAVAILABLE" not in metadata["mapping_warnings"]


def test_akshare_tencent_raw_missing_turnover_keeps_amount_unavailable(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")
    module.__file__ = "fake-akshare.py"

    def fake_raw(request):
        return normalize_tencent_raw_market_output(
            [["2024-01-02", "7.83", "7.65", "7.86", "7.65", "1158366.00"]],
            symbol="sz000001",
        )

    module.stock_zh_a_hist_tx = lambda **kwargs: pd.DataFrame()
    monkeypatch.setitem(sys.modules, "akshare", module)
    monkeypatch.setattr(data_sources, "fetch_tencent_stock_market_raw", fake_raw)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert float(exported.iloc[0]["volume"]) == 115836600
    assert float(exported.iloc[0]["amount"]) == 0
    assert "TENCENT_TURNOVER_AMOUNT_FIELD_UNAVAILABLE" in metadata["mapping_warnings"]


def test_akshare_tencent_volume_column_maps_nonzero_volume(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist_tx(**kwargs):
        return pd.DataFrame(
            [
                {
                    "date": "2024-01-02",
                    "open": 10.0,
                    "close": 10.2,
                    "high": 10.5,
                    "low": 9.8,
                    "volume": 100000,
                    "turnover": 1020000,
                }
            ]
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert int(exported.iloc[0]["volume"]) == 100000
    assert int(exported.iloc[0]["amount"]) == 1020000
    assert metadata["mapping_warnings"] == []


def test_akshare_tencent_chinese_hands_volume_maps_nonzero_volume(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist_tx(**kwargs):
        return pd.DataFrame(
            [
                {
                    "\u65e5\u671f": "2024-01-02",
                    "\u5f00\u76d8": 10.0,
                    "\u6536\u76d8": 10.2,
                    "\u6700\u9ad8": 10.5,
                    "\u6700\u4f4e": 9.8,
                    "\u6210\u4ea4\u91cf(\u624b)": 1000,
                    "\u6210\u4ea4\u989d": 1020000,
                }
            ]
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert int(exported.iloc[0]["volume"]) == 100000
    assert int(exported.iloc[0]["amount"]) == 1020000
    assert "TENCENT_VOLUME_CONVERTED_FROM_HANDS_TO_SHARES" in metadata["mapping_warnings"]


def test_akshare_tencent_missing_volume_adds_mapping_warning(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist_tx(**kwargs):
        return pd.DataFrame(
            [
                {"date": "2024-01-02", "open": 10.0, "close": 10.2, "high": 10.5, "low": 9.8},
            ]
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert int(exported.iloc[0]["volume"]) == 0
    assert "TENCENT_VOLUME_FIELD_UNAVAILABLE" in metadata["mapping_warnings"]


def test_akshare_tencent_corrected_volume_survives_market_cache_ingest(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist_tx(**kwargs):
        return pd.DataFrame(
            [
                {"date": "2024-01-02", "open": 10.0, "close": 10.2, "high": 10.5, "low": 9.8, "amount": 1000},
            ]
        )

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    fetch_result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )
    cache_result = ingest_market_cache_csv(
        fetch_result.artifact_paths["raw_data"],
        metadata_path=fetch_result.artifact_paths["metadata"],
        config={"market_data_cache": {"cache_path": tmp_path / "cache" / "daily_bars.csv"}},
    )

    assert int(cache_result.cache_frame.iloc[0]["volume"]) == 100000
    assert cache_result.cache_frame.iloc[0]["symbol"] == "000001"


def test_akshare_etf_market_success_uses_etf_route(tmp_path: Path, monkeypatch) -> None:
    fake_akshare = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="159915",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.row_count == 2
    assert fake_akshare.calls[0]["function"] == "fund_etf_hist_sina"
    assert fake_akshare.calls[0]["symbol"] == "sz159915"
    assert metadata["inferred_symbol_type"] == "ETF"
    assert metadata["attempted_functions"] == ["fund_etf_hist_sina"]
    assert metadata["successful_function"] == "fund_etf_hist_sina"
    assert metadata["upstream_source"] == "SINA"
    assert metadata["fallback_used"] is False


def test_akshare_etf_primary_failure_tries_fallback(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def fund_etf_hist_sina(**kwargs):
        module.calls.append({"function": "fund_etf_hist_sina", **kwargs})
        raise ConnectionError("RemoteDisconnected('Remote end closed connection without response')")

    def fund_etf_hist_em(**kwargs):
        module.calls.append({"function": "fund_etf_hist_em", **kwargs})
        return _akshare_market_rows()

    module.fund_etf_hist_sina = fund_etf_hist_sina
    module.fund_etf_hist_em = fund_etf_hist_em
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="510300",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(
            tmp_path,
            allow_network_sources=True,
            allow_real_data_fetch=True,
            akshare_market_retry_count=0,
        ),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert [call["function"] for call in module.calls] == ["fund_etf_hist_sina", "fund_etf_hist_em"]
    assert result.row_count == 2
    assert metadata["attempted_functions"] == ["fund_etf_hist_sina", "fund_etf_hist_em"]
    assert metadata["attempted_upstreams"] == ["SINA", "EASTMONEY"]
    assert metadata["successful_function"] == "fund_etf_hist_em"
    assert metadata["upstream_source"] == "EASTMONEY"
    assert metadata["fallback_used"] is True
    assert metadata["audit_metadata"]["adapter_metadata"]["failed_attempts"][0]["exception_type"] == "ConnectionError"


def test_akshare_market_curl_cffi_fallback_success_with_fake_response(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise ConnectionError("AKShare Eastmoney requests path failed")

    module.stock_zh_a_hist = stock_zh_a_hist
    monkeypatch.setitem(sys.modules, "akshare", module)
    fake_curl = _fake_curl_cffi_module(
        {
            "data": {
                "klines": [
                    "2024-01-02,10.0,10.2,10.5,9.8,1000,10200,0,0,0,0,0",
                    "2024-01-03,10.2,10.6,10.8,10.1,1100,11660,0,0,0,0,0",
                ]
            }
        }
    )
    monkeypatch.setitem(sys.modules, "curl_cffi", fake_curl)
    monkeypatch.setitem(sys.modules, "curl_cffi.requests", fake_curl.requests)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(
            tmp_path,
            allow_network_sources=True,
            allow_real_data_fetch=True,
            akshare_market_retry_count=0,
            akshare_market_stock_fallback_order=["EASTMONEY"],
        ),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert result.row_count == 2
    assert set(
        [
            "symbol",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "available_time",
            "revision_id",
            "source",
        ]
    ).issubset(exported.columns)
    assert exported["symbol"].eq("000001").all()
    assert metadata["attempted_functions"] == ["stock_zh_a_hist", "eastmoney_curl_cffi_kline"]
    assert metadata["successful_function"] == "eastmoney_curl_cffi_kline"
    assert metadata["fallback_used"] is True
    assert fake_curl.requests.calls[0]["params"]["secid"] == "0.000001"
    assert fake_curl.requests.calls[0]["impersonate"] == "chrome"


def test_akshare_market_curl_cffi_missing_dependency_is_clear(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise ConnectionError("AKShare path failed")

    module.stock_zh_a_hist = stock_zh_a_hist
    monkeypatch.setitem(sys.modules, "akshare", module)
    monkeypatch.delitem(sys.modules, "curl_cffi", raising=False)
    monkeypatch.delitem(sys.modules, "curl_cffi.requests", raising=False)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("curl_cffi"):
            raise ImportError("curl_cffi unavailable in offline test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                symbol="000001",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(
                tmp_path,
                allow_network_sources=True,
                allow_real_data_fetch=True,
                akshare_market_retry_count=0,
                akshare_market_stock_fallback_order=["EASTMONEY"],
            ),
        )

    message = str(exc_info.value)
    assert "eastmoney_curl_cffi_kline" in message
    assert "curl_cffi fallback requires curl_cffi" in message
    assert "python -m pip install curl_cffi" in message


def test_akshare_market_curl_cffi_fallback_can_be_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise ConnectionError("AKShare path failed")

    module.stock_zh_a_hist = stock_zh_a_hist
    monkeypatch.setitem(sys.modules, "akshare", module)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("curl_cffi"):
            raise AssertionError("curl_cffi should not be imported when fallback is disabled")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                symbol="000001",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(
                tmp_path,
                allow_network_sources=True,
                allow_real_data_fetch=True,
                akshare_market_retry_count=0,
                akshare_market_stock_fallback_order=["EASTMONEY"],
                akshare_market_enable_curl_cffi_fallback=False,
            ),
        )

    message = str(exc_info.value)
    assert "attempted_functions=['stock_zh_a_hist']" in message
    assert "eastmoney_curl_cffi_kline" not in message


def test_akshare_market_curl_cffi_failure_redacts_secret_like_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise ConnectionError("AKShare path token=abc123")

    module.stock_zh_a_hist = stock_zh_a_hist
    monkeypatch.setitem(sys.modules, "akshare", module)
    fake_curl = _fake_curl_cffi_module(
        {"data": {"klines": []}},
        error=RuntimeError("curl path api_key=secret123"),
    )
    monkeypatch.setitem(sys.modules, "curl_cffi", fake_curl)
    monkeypatch.setitem(sys.modules, "curl_cffi.requests", fake_curl.requests)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                symbol="000001",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(
                tmp_path,
                allow_network_sources=True,
                allow_real_data_fetch=True,
                akshare_market_retry_count=0,
                akshare_market_stock_fallback_order=["EASTMONEY"],
            ),
        )

    message = str(exc_info.value)
    assert "token=<redacted>" in message
    assert "api_key=<redacted>" in message
    assert "abc123" not in message
    assert "secret123" not in message


def test_akshare_market_all_failures_produce_clear_diagnostic_without_secrets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def fund_etf_hist_sina(**kwargs):
        _ = kwargs
        raise ConnectionError("RemoteDisconnected token=abc123")

    def fund_etf_hist_em(**kwargs):
        _ = kwargs
        raise RuntimeError("endpoint changed api_key=secret123")

    module.fund_etf_hist_sina = fund_etf_hist_sina
    module.fund_etf_hist_em = fund_etf_hist_em
    monkeypatch.setitem(sys.modules, "akshare", module)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                symbol="510300",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(
                tmp_path,
                allow_network_sources=True,
                allow_real_data_fetch=True,
                akshare_market_retry_count=0,
                akshare_market_enable_curl_cffi_fallback=False,
            ),
        )

    message = str(exc_info.value)
    assert "dataset_type=market" in message
    assert "symbol=510300" in message
    assert "inferred_symbol_type=ETF" in message
    assert "attempted_functions=['fund_etf_hist_sina', 'fund_etf_hist_em']" in message
    assert "ConnectionError" in message
    assert "RuntimeError" in message
    assert "token=<redacted>" in message
    assert "api_key=<redacted>" in message
    assert "abc123" not in message
    assert "secret123" not in message
    assert "LOCAL_CSV fallback" in message


def test_akshare_stock_fallback_order_tries_tencent_sina_then_eastmoney(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def failing_function(function_name: str):
        def _inner(**kwargs):
            module.calls.append({"function": function_name, **kwargs})
            raise ConnectionError(f"{function_name} unavailable")

        return _inner

    module.stock_zh_a_hist_tx = failing_function("stock_zh_a_hist_tx")
    module.stock_zh_a_daily = failing_function("stock_zh_a_daily")
    module.stock_zh_a_hist = failing_function("stock_zh_a_hist")
    monkeypatch.setitem(sys.modules, "akshare", module)

    with pytest.raises(RuntimeError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="market",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                symbol="000001",
                start_date="2024-01-01",
                end_date="2024-01-03",
            ),
            settings=_settings(
                tmp_path,
                allow_network_sources=True,
                allow_real_data_fetch=True,
                akshare_market_retry_count=0,
                akshare_market_enable_curl_cffi_fallback=False,
            ),
        )

    assert [call["function"] for call in module.calls] == [
        "stock_zh_a_hist_tx",
        "stock_zh_a_daily",
        "stock_zh_a_hist",
    ]
    assert "attempted_functions=['stock_zh_a_hist_tx', 'stock_zh_a_daily', 'stock_zh_a_hist']" in str(exc_info.value)


def test_akshare_stock_tencent_failure_then_sina_success(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def stock_zh_a_hist_tx(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist_tx", **kwargs})
        raise ConnectionError("Tencent unavailable")

    def stock_zh_a_daily(**kwargs):
        module.calls.append({"function": "stock_zh_a_daily", **kwargs})
        return _akshare_chinese_market_rows()

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    module.stock_zh_a_daily = stock_zh_a_daily
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(
            tmp_path,
            allow_network_sources=True,
            allow_real_data_fetch=True,
            akshare_market_retry_count=0,
            akshare_market_enable_curl_cffi_fallback=False,
        ),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert [call["function"] for call in module.calls] == ["stock_zh_a_hist_tx", "stock_zh_a_daily"]
    assert set(_canonical_market_columns()).issubset(exported.columns)
    assert exported["symbol"].tolist() == ["000001", "000001"]
    assert metadata["attempted_functions"] == ["stock_zh_a_hist_tx", "stock_zh_a_daily"]
    assert metadata["attempted_upstreams"] == ["TENCENT", "SINA"]
    assert metadata["successful_function"] == "stock_zh_a_daily"
    assert metadata["upstream_source"] == "SINA"
    assert metadata["fallback_used"] is True


def test_akshare_index_uses_sina_then_tencent_before_eastmoney(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def stock_zh_index_daily(**kwargs):
        module.calls.append({"function": "stock_zh_index_daily", **kwargs})
        raise ConnectionError("Sina index unavailable")

    def stock_zh_index_daily_tx(**kwargs):
        module.calls.append({"function": "stock_zh_index_daily_tx", **kwargs})
        return _akshare_market_rows()

    module.stock_zh_index_daily = stock_zh_index_daily
    module.stock_zh_index_daily_tx = stock_zh_index_daily_tx
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="market",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            symbol="000300",
            start_date="2024-01-01",
            end_date="2024-01-03",
        ),
        settings=_settings(
            tmp_path,
            allow_network_sources=True,
            allow_real_data_fetch=True,
            akshare_market_retry_count=0,
            akshare_market_enable_curl_cffi_fallback=False,
        ),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert [call["function"] for call in module.calls] == ["stock_zh_index_daily", "stock_zh_index_daily_tx"]
    assert module.calls[0]["symbol"] == "sh000300"
    assert result.row_count == 2
    assert metadata["attempted_functions"] == ["stock_zh_index_daily", "stock_zh_index_daily_tx"]
    assert metadata["successful_function"] == "stock_zh_index_daily_tx"
    assert metadata["upstream_source"] == "TENCENT"
    assert metadata["fallback_used"] is True


def test_akshare_universe_success_path_writes_canonical_raw_artifacts(tmp_path: Path, monkeypatch) -> None:
    fake_akshare = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="all",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    assert result.source == "AKSHARE_OPTIONAL"
    assert result.dataset_type == "universe"
    assert result.row_count == 3
    assert {call["function"] for call in fake_akshare.universe_calls} == {
        "stock_info_a_code_name",
        "fund_etf_spot_em",
    }
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    assert list(exported.columns) == _UNIVERSE_COLUMNS
    assert pd.to_datetime(exported["as_of_date"]).dt.date.eq(pd.Timestamp("2024-05-20").date()).all()
    assert set(exported["instrument_type"]) == {"STOCK", "ETF"}
    assert exported["min_lot"].eq(100).all()
    assert exported["t_plus_rule"].eq("T+1").all()
    assert exported["source"].eq("AKSHARE_OPTIONAL").all()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["adapter_status"] == "SUCCESS"
    assert metadata["as_of_date"] == "2024-05-20"
    assert metadata["market_type"] == "all"
    assert metadata["allow_real_data"] is True
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_akshare_universe_defaults_missing_optional_fields(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")

    def stock_info_a_code_name():
        return pd.DataFrame([{"code": "600000", "name": "PF Bank"}])

    module.stock_info_a_code_name = stock_info_a_code_name
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert exported.loc[0, "exchange"] == "SSE"
    assert exported.loc[0, "industry"] == "UNKNOWN"
    assert bool(exported.loc[0, "is_active"]) is True
    assert bool(exported.loc[0, "is_st"]) is False
    assert bool(exported.loc[0, "is_suspended"]) is False
    assert exported.loc[0, "min_lot"] == 100
    assert exported.loc[0, "t_plus_rule"] == "T+1"


def test_akshare_universe_chinese_columns_are_mapped(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_universe_module(
        pd.DataFrame(
            [
                {
                    "\u4ee3\u7801": "600000",
                    "\u540d\u79f0": "\u6d66\u53d1\u94f6\u884c",
                    "\u6240\u5c5e\u884c\u4e1a": "Banking",
                    "\u4e0a\u5e02\u65e5\u671f": "1999-11-10",
                    "\u4ea4\u6613\u6240": "SH",
                }
            ]
        )
    )
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert exported.loc[0, "symbol"] == "600000"
    assert exported.loc[0, "name"] == "\u6d66\u53d1\u94f6\u884c"
    assert exported.loc[0, "industry"] == "Banking"
    assert exported.loc[0, "exchange"] == "SSE"
    assert exported.loc[0, "listed_date"].startswith("1999-11-10")


def test_akshare_universe_english_columns_are_mapped(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_universe_module(
        pd.DataFrame(
            [
                {
                    "symbol": "000001",
                    "name": "Ping An Bank",
                    "industry": "Banking",
                    "listed_date": "1991-04-03",
                    "exchange": "SZ",
                }
            ]
        )
    )
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert exported.loc[0, "symbol"] == "000001"
    assert exported.loc[0, "name"] == "Ping An Bank"
    assert exported.loc[0, "exchange"] == "SZSE"
    assert exported.loc[0, "industry"] == "Banking"


def test_akshare_universe_duplicate_columns_do_not_trigger_dataframe_str_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    duplicate_frame = pd.DataFrame(
        [["600000", "SHOULD_NOT_BE_USED", "PF Bank"]],
        columns=["code", "code", "name"],
    )
    module = _fake_akshare_universe_module(duplicate_frame)
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert exported.loc[0, "symbol"] == "600000"
    assert exported.loc[0, "name"] == "PF Bank"
    assert any("Duplicate AKShare universe columns for symbol" in warning for warning in metadata["mapping_warnings"])
    assert metadata["raw_columns"].count("code") == 2


def test_akshare_universe_missing_symbol_column_raises_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _fake_akshare_universe_module(pd.DataFrame([{"name": "No Code"}]))
    monkeypatch.setitem(sys.modules, "akshare", module)

    with pytest.raises(ValueError) as exc_info:
        run_data_source_fetch(
            DataSourceRequest(
                source="AKSHARE_OPTIONAL",
                dataset_type="universe",
                output_dir=tmp_path / "raw",
                allow_real_data=True,
                as_of_date="2024-05-20",
                market_type="stock",
            ),
            settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
        )

    message = str(exc_info.value)
    assert "dataset_type=universe" in message
    assert "raw_shape=(1, 3)" in message
    assert "raw_columns=['name', '_akshare_instrument_type', '_akshare_function']" in message
    assert "missing_required_conceptual_fields=['symbol']" in message
    assert "LOCAL_CSV universe snapshot fallback" in message


def test_akshare_universe_missing_name_defaults_to_symbol(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_universe_module(pd.DataFrame([{"code": "600000"}]))
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str, "name": str})

    assert exported.loc[0, "symbol"] == "600000"
    assert exported.loc[0, "name"] == "600000"


def test_akshare_universe_st_detection_from_name(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_universe_module(pd.DataFrame([{"code": "000001", "name": "*ST Example"}]))
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert bool(exported.loc[0, "is_st"]) is True


def test_akshare_universe_exchange_inference_from_symbol_prefix(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_universe_module(
        pd.DataFrame(
            [
                {"code": "600000", "name": "SSE Stock"},
                {"code": "000001", "name": "SZSE Stock"},
                {"code": "833000", "name": "BSE Stock"},
            ]
        )
    )
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})

    assert dict(zip(exported["symbol"], exported["exchange"])) == {
        "000001": "SZSE",
        "600000": "SSE",
        "833000": "BSE",
    }


def test_akshare_universe_metadata_includes_columns_and_mapping_warnings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    duplicate_frame = pd.DataFrame([["600000", "PF Bank"]], columns=["code", "code"])
    module = _fake_akshare_universe_module(duplicate_frame)
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_fetch(
        DataSourceRequest(
            source="AKSHARE_OPTIONAL",
            dataset_type="universe",
            output_dir=tmp_path / "raw",
            allow_real_data=True,
            as_of_date="2024-05-20",
            market_type="stock",
        ),
        settings=_settings(tmp_path, allow_network_sources=True, allow_real_data_fetch=True),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    adapter_metadata = metadata["audit_metadata"]["adapter_metadata"]

    assert metadata["raw_columns"] == ["code", "code", "_akshare_instrument_type", "_akshare_function"]
    assert metadata["normalized_columns"] == _UNIVERSE_COLUMNS
    assert metadata["mapping_warnings"] == adapter_metadata["mapping_warnings"]
    assert adapter_metadata["row_count"] == 1
    assert adapter_metadata["adapter_status"] == "SUCCESS"


def test_metadata_json_is_written(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_fetch(
        DataSourceRequest(source="LOCAL_CSV", dataset_type="market", input_path=input_path),
        settings=_settings(tmp_path),
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["source"] == "LOCAL_CSV"
    assert metadata["dataset_type"] == "market"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_raw_data_csv_is_written_and_readable(tmp_path: Path) -> None:
    input_path = tmp_path / "universe.csv"
    _universe_frame().to_csv(input_path, index=False)

    result = run_data_source_fetch(
        DataSourceRequest(source="LOCAL_CSV", dataset_type="universe", input_path=input_path),
        settings=_settings(tmp_path),
    )
    exported = pd.read_csv(result.artifact_paths["raw_data"])

    assert len(exported) == 1
    assert "symbol" in exported.columns


def test_local_csv_data_source_reads_symbol_columns_as_strings(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    frame = _market_frame().iloc[[0]].copy()
    frame["symbol"] = "000001"
    frame.to_csv(input_path, index=False)

    result = run_data_source_fetch(
        DataSourceRequest(source="LOCAL_CSV", dataset_type="market", input_path=input_path),
        settings=_settings(tmp_path),
    )

    assert result.raw_data["symbol"].tolist() == ["000001"]


def test_run_id_is_deterministic_for_same_request(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)
    request = DataSourceRequest(source="LOCAL_CSV", dataset_type="market", input_path=input_path)

    first = run_data_source_fetch(request, settings=_settings(tmp_path))
    second = run_data_source_fetch(request, settings=_settings(tmp_path))

    assert first.run_id == second.run_id
    assert first.artifact_paths == second.artifact_paths


def test_adapter_registry_lists_local_and_optional_sources() -> None:
    adapters = list_data_source_adapters()

    assert {"LOCAL_CSV", "MOCK", "AKSHARE_OPTIONAL", "TUSHARE_OPTIONAL"}.issubset(set(adapters))
    assert "AKSHARE_OPTIONAL" not in list_data_source_adapters(include_real=False)
    assert "TUSHARE_OPTIONAL" not in list_data_source_adapters(include_real=False)


def test_cli_data_source_fetch_works_for_local_csv(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "LOCAL_CSV",
            "--dataset-type",
            "market",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: LOCAL_CSV" in output.out
    assert "raw_data:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_data_source_fetch_works_for_mock(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "MOCK",
            "--dataset-type",
            "market",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: MOCK" in output.out
    assert "row_count:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_blocks_real_source_without_allow_real_data(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "AKSHARE_OPTIONAL",
            "--dataset-type",
            "market",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "requires explicit --allow-real-data" in output.err


def test_cli_blocks_akshare_universe_without_allow_real_data(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "AKSHARE_OPTIONAL",
            "--dataset-type",
            "universe",
            "--as-of-date",
            "2024-05-20",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "requires explicit --allow-real-data" in output.err


def test_cli_blocks_tushare_without_allow_real_data(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "TUSHARE_OPTIONAL",
            "--dataset-type",
            "market",
            "--symbol",
            "000001.SZ",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-03",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "requires explicit --allow-real-data" in output.err


def test_cli_allows_tushare_with_fake_client_and_token(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "fake_token")
    monkeypatch.setitem(sys.modules, "tushare", _fake_tushare_module())

    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "TUSHARE_OPTIONAL",
            "--dataset-type",
            "market",
            "--symbol",
            "000001.SZ",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-03",
            "--allow-real-data",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: TUSHARE_OPTIONAL" in output.out
    assert "row_count: 2" in output.out
    assert "No live trading or broker API was invoked." in output.out
    assert "fake_token" not in output.out
    assert "fake_token" not in output.err


def test_cli_allows_baostock_with_fake_client(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setitem(sys.modules, "baostock", _fake_baostock_module())

    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "BAOSTOCK_OPTIONAL",
            "--dataset-type",
            "market",
            "--symbol",
            "000001",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-03",
            "--allow-real-data",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: BAOSTOCK_OPTIONAL" in output.out
    assert "row_count: 2" in output.out
    assert "No live trading or broker API was invoked." in output.out
    raw_line = next(line for line in output.out.splitlines() if line.startswith("raw_data:"))
    raw_path = Path(raw_line.split(":", 1)[1].strip())
    exported = pd.read_csv(raw_path, dtype={"symbol": str})
    assert exported["symbol"].tolist() == ["000001", "000001"]


def test_cli_allows_akshare_with_allow_real_data_using_fake_module(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare_module())

    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "AKSHARE_OPTIONAL",
            "--dataset-type",
            "market",
            "--symbol",
            "510300",
            "--start-date",
            "2024-01-01",
            "--end-date",
            "2024-01-03",
            "--allow-real-data",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: AKSHARE_OPTIONAL" in output.out
    assert "row_count: 2" in output.out
    assert "No live trading or broker API was invoked." in output.out
    raw_line = next(line for line in output.out.splitlines() if line.startswith("raw_data:"))
    raw_path = Path(raw_line.split(":", 1)[1].strip())
    assert raw_path.exists()
    exported = pd.read_csv(raw_path)
    assert len(exported) == 2


def test_cli_allows_akshare_universe_with_allow_real_data_using_fake_module(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare_module())

    code = cli.main(
        [
            "data-source-fetch",
            "--source",
            "AKSHARE_OPTIONAL",
            "--dataset-type",
            "universe",
            "--as-of-date",
            "2024-05-20",
            "--market-type",
            "all",
            "--allow-real-data",
            "--output-dir",
            str(tmp_path / "raw"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "source: AKSHARE_OPTIONAL" in output.out
    assert "dataset_type: universe" in output.out
    assert "row_count: 3" in output.out
    assert "No live trading or broker API was invoked." in output.out
    raw_line = next(line for line in output.out.splitlines() if line.startswith("raw_data:"))
    raw_path = Path(raw_line.split(":", 1)[1].strip())
    exported = pd.read_csv(raw_path)
    assert list(exported.columns) == _UNIVERSE_COLUMNS


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_fetch(
        DataSourceRequest(source="LOCAL_CSV", dataset_type="market", input_path=input_path),
        settings=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_no_real_network_api_calls_are_used_in_tests(tmp_path: Path) -> None:
    result = run_data_source_fetch(
        DataSourceRequest(source="MOCK", dataset_type="market"),
        settings=_settings(tmp_path),
    )

    assert result.audit_metadata["network_api_calls_used_in_tests"] is False
    assert result.audit_metadata["data_source_fetch_only"] is True


def _settings(tmp_path: Path, **overrides) -> DataSourceSettings:
    payload = {
        "raw_output_dir": tmp_path / "raw",
        "write_artifacts": True,
    }
    payload.update(overrides)
    return DataSourceSettings(**payload)


def _market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "trade_date": "2024-05-20",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "amount": 10200,
            },
            {
                "symbol": "BBB",
                "trade_date": "2024-05-20",
                "open": 20.0,
                "high": 20.5,
                "low": 19.8,
                "close": 20.2,
                "volume": 2000,
                "amount": 40400,
            },
        ]
    )


def _universe_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": "2024-05-20",
                "symbol": "AAA",
                "name": "AAA ETF",
                "instrument_type": "ETF",
                "exchange": "SSE",
            }
        ]
    )


def _fake_akshare_module() -> ModuleType:
    module = ModuleType("akshare")
    module.calls = []
    module.universe_calls = []

    def stock_zh_a_hist_tx(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist_tx", **kwargs})
        return _akshare_market_rows()

    def stock_zh_a_daily(**kwargs):
        module.calls.append({"function": "stock_zh_a_daily", **kwargs})
        return _akshare_market_rows()

    def fund_etf_hist_sina(**kwargs):
        module.calls.append({"function": "fund_etf_hist_sina", **kwargs})
        return _akshare_market_rows()

    def fund_etf_hist_em(**kwargs):
        module.calls.append({"function": "fund_etf_hist_em", **kwargs})
        return _akshare_market_rows()

    def stock_zh_a_hist(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist", **kwargs})
        return _akshare_market_rows()

    def stock_zh_index_daily(**kwargs):
        module.calls.append({"function": "stock_zh_index_daily", **kwargs})
        return _akshare_market_rows()

    def stock_zh_index_daily_tx(**kwargs):
        module.calls.append({"function": "stock_zh_index_daily_tx", **kwargs})
        return _akshare_market_rows()

    def stock_zh_index_daily_em(**kwargs):
        module.calls.append({"function": "stock_zh_index_daily_em", **kwargs})
        return _akshare_market_rows()

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    module.stock_zh_a_daily = stock_zh_a_daily
    module.fund_etf_hist_sina = fund_etf_hist_sina
    module.fund_etf_hist_em = fund_etf_hist_em
    module.stock_zh_a_hist = stock_zh_a_hist
    module.stock_zh_index_daily = stock_zh_index_daily
    module.stock_zh_index_daily_tx = stock_zh_index_daily_tx
    module.stock_zh_index_daily_em = stock_zh_index_daily_em

    def stock_info_a_code_name():
        module.universe_calls.append({"function": "stock_info_a_code_name"})
        return pd.DataFrame(
            [
                {"code": "600000", "name": "PF Bank", "industry": "Banking", "listed_date": "1999-11-10"},
                {"code": "000001", "name": "Ping An Bank", "industry": "Banking", "listed_date": "1991-04-03"},
            ]
        )

    def fund_etf_spot_em():
        module.universe_calls.append({"function": "fund_etf_spot_em"})
        return pd.DataFrame(
            [
                {"code": "510300", "name": "CSI 300 ETF", "listed_date": "2012-05-28"},
            ]
        )

    module.stock_info_a_code_name = stock_info_a_code_name
    module.fund_etf_spot_em = fund_etf_spot_em
    return module


def _akshare_market_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "amount": 10200,
            },
            {
                "date": "2024-01-03",
                "open": 10.2,
                "high": 10.8,
                "low": 10.1,
                "close": 10.6,
                "volume": 1100,
                "amount": 11660,
            },
        ]
    )


def _akshare_chinese_market_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "\u65e5\u671f": "2024-01-02",
                "\u5f00\u76d8": 10.0,
                "\u6700\u9ad8": 10.5,
                "\u6700\u4f4e": 9.8,
                "\u6536\u76d8": 10.2,
                "\u6210\u4ea4\u91cf": 1000,
                "\u6210\u4ea4\u989d": 10200,
            },
            {
                "\u65e5\u671f": "2024-01-03",
                "\u5f00\u76d8": 10.2,
                "\u6700\u9ad8": 10.8,
                "\u6700\u4f4e": 10.1,
                "\u6536\u76d8": 10.6,
                "\u6210\u4ea4\u91cf": 1100,
                "\u6210\u4ea4\u989d": 11660,
            },
        ]
    )


def _canonical_market_columns() -> list[str]:
    return [
        "symbol",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "pre_close",
        "adj_factor",
        "is_suspended",
        "limit_up",
        "limit_down",
        "event_time",
        "publish_time",
        "ingest_time",
        "available_time",
        "revision_id",
        "source",
    ]


def _fake_akshare_universe_module(frame: pd.DataFrame) -> ModuleType:
    module = ModuleType("akshare")
    module.universe_calls = []

    def stock_info_a_code_name():
        module.universe_calls.append({"function": "stock_info_a_code_name"})
        return frame.copy()

    module.stock_info_a_code_name = stock_info_a_code_name
    return module


def _fake_tushare_module() -> ModuleType:
    module = ModuleType("tushare")
    module.calls = []

    class FakeProClient:
        def daily(self, **kwargs):
            module.calls.append({"function": "daily", **kwargs})
            return pd.DataFrame(
                [
                    {
                        "ts_code": kwargs["ts_code"],
                        "trade_date": "20240102",
                        "open": 10.0,
                        "high": 10.5,
                        "low": 9.8,
                        "close": 10.2,
                        "pre_close": 9.9,
                        "vol": 1000,
                        "amount": 10200,
                    },
                    {
                        "ts_code": kwargs["ts_code"],
                        "trade_date": "20240103",
                        "open": 10.2,
                        "high": 10.8,
                        "low": 10.1,
                        "close": 10.6,
                        "pre_close": 10.2,
                        "vol": 1100,
                        "amount": 11660,
                    },
                ]
            )

        def index_daily(self, **kwargs):
            module.calls.append({"function": "index_daily", **kwargs})
            return self.daily(**kwargs)

        def stock_basic(self, **kwargs):
            module.calls.append({"function": "stock_basic", **kwargs})
            return pd.DataFrame(
                [
                    {
                        "ts_code": "000001.SZ",
                        "symbol": "000001",
                        "name": "Ping An Bank",
                        "industry": "Banking",
                        "market": "main",
                        "list_date": "19910403",
                        "delist_date": "",
                        "exchange": "SZSE",
                    },
                    {
                        "ts_code": "600000.SH",
                        "symbol": "600000",
                        "name": "PF Bank",
                        "industry": "Banking",
                        "market": "main",
                        "list_date": "19991110",
                        "delist_date": "",
                        "exchange": "SSE",
                    },
                ]
            )

        def fund_basic(self, **kwargs):
            module.calls.append({"function": "fund_basic", **kwargs})
            return pd.DataFrame(
                [
                    {
                        "ts_code": "510300.SH",
                        "name": "CSI 300 ETF",
                        "fund_type": "ETF",
                        "list_date": "20120528",
                        "delist_date": "",
                    }
                ]
            )

        def trade_cal(self, **kwargs):
            module.calls.append({"function": "trade_cal", **kwargs})
            return pd.DataFrame(
                [
                    {"cal_date": "20240101", "is_open": 0},
                    {"cal_date": "20240102", "is_open": 1},
                    {"cal_date": "20240103", "is_open": 1},
                ]
            )

    def pro_api(token=None):
        module.calls.append({"function": "pro_api", "token": token})
        return FakeProClient()

    module.pro_api = pro_api
    return module


def _fake_baostock_module(symbol_code: str = "sz.000001") -> ModuleType:
    module = ModuleType("baostock")
    module.calls = []

    class FakeResult:
        def __init__(self, code: str) -> None:
            self.error_code = "0"
            self.error_msg = "success"
            self.fields = [
                "date",
                "code",
                "open",
                "high",
                "low",
                "close",
                "preclose",
                "volume",
                "amount",
                "adjustflag",
                "turn",
                "tradestatus",
                "pctChg",
                "isST",
            ]
            self._rows = [
                [
                    "2024-01-02",
                    code,
                    "10.0",
                    "10.5",
                    "9.8",
                    "10.2",
                    "9.9",
                    "1000",
                    "10200",
                    "3",
                    "1.0",
                    "1",
                    "1.0",
                    "0",
                ],
                [
                    "2024-01-03",
                    code,
                    "10.2",
                    "10.8",
                    "10.1",
                    "10.6",
                    "10.2",
                    "1100",
                    "11660",
                    "3",
                    "1.1",
                    "1",
                    "1.2",
                    "0",
                ],
            ]
            self._index = -1

        def next(self) -> bool:
            self._index += 1
            return self._index < len(self._rows)

        def get_row_data(self) -> list[str]:
            return self._rows[self._index]

    class SuccessResult:
        error_code = "0"
        error_msg = "success"

    def login():
        module.calls.append({"function": "login"})
        return SuccessResult()

    def logout():
        module.calls.append({"function": "logout"})
        return SuccessResult()

    def query_history_k_data_plus(code, fields, start_date, end_date, frequency, adjustflag):
        module.calls.append(
            {
                "function": "query_history_k_data_plus",
                "code": code,
                "fields": fields,
                "start_date": start_date,
                "end_date": end_date,
                "frequency": frequency,
                "adjustflag": adjustflag,
            }
        )
        return FakeResult(code if code else symbol_code)

    module.login = login
    module.logout = logout
    module.query_history_k_data_plus = query_history_k_data_plus
    return module


def _fake_curl_cffi_module(payload: dict, error: Exception | None = None) -> ModuleType:
    module = ModuleType("curl_cffi")
    requests_module = ModuleType("curl_cffi.requests")
    requests_module.calls = []

    class Response:
        status_code = 200
        text = json.dumps(payload)

        def json(self):
            return payload

    def get(url, **kwargs):
        requests_module.calls.append({"url": url, **kwargs})
        if error is not None:
            raise error
        return Response()

    requests_module.get = get
    module.requests = requests_module
    return module


_UNIVERSE_COLUMNS = [
    "as_of_date",
    "symbol",
    "name",
    "instrument_type",
    "exchange",
    "listed_date",
    "delisted_date",
    "is_active",
    "is_st",
    "is_suspended",
    "industry",
    "min_lot",
    "t_plus_rule",
    "available_time",
    "revision_id",
    "source",
]
