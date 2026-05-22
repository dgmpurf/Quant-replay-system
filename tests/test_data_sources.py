import builtins
import json
import sys
from types import ModuleType
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import DataSourceSettings
from quant_replay_system.data_sources import (
    DataSourceRequest,
    get_data_source_adapter,
    infer_akshare_market_symbol_type,
    list_data_source_adapters,
    run_data_source_fetch,
)


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
    assert fake_akshare.calls[0]["symbol"] == "510300"
    assert fake_akshare.calls[0]["start_date"] == "20240101"
    assert result.artifact_paths["raw_data"].exists()
    exported = pd.read_csv(result.artifact_paths["raw_data"], dtype={"symbol": str})
    assert {"symbol", "trade_date", "open", "close", "available_time"}.issubset(exported.columns)
    assert exported["source"].eq("AKSHARE_OPTIONAL").all()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["adapter_status"] == "SUCCESS"
    assert metadata["symbol"] == "510300"
    assert metadata["allow_real_data"] is True
    assert metadata["inferred_symbol_type"] == "ETF"
    assert metadata["attempted_functions"] == ["fund_etf_hist_em"]
    assert metadata["successful_function"] == "fund_etf_hist_em"
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
    assert fake_akshare.calls[0]["function"] == "stock_zh_a_hist"
    assert metadata["inferred_symbol_type"] == "STOCK"
    assert metadata["attempted_functions"] == ["stock_zh_a_hist"]
    assert metadata["successful_function"] == "stock_zh_a_hist"


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
    assert fake_akshare.calls[0]["function"] == "fund_etf_hist_em"
    assert metadata["inferred_symbol_type"] == "ETF"
    assert metadata["attempted_functions"] == ["fund_etf_hist_em"]
    assert metadata["successful_function"] == "fund_etf_hist_em"


def test_akshare_etf_primary_failure_tries_fallback(tmp_path: Path, monkeypatch) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def fund_etf_hist_em(**kwargs):
        module.calls.append({"function": "fund_etf_hist_em", **kwargs})
        raise ConnectionError("RemoteDisconnected('Remote end closed connection without response')")

    def stock_zh_a_hist(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist", **kwargs})
        return _akshare_market_rows()

    module.fund_etf_hist_em = fund_etf_hist_em
    module.stock_zh_a_hist = stock_zh_a_hist
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

    assert [call["function"] for call in module.calls] == ["fund_etf_hist_em", "stock_zh_a_hist"]
    assert result.row_count == 2
    assert metadata["attempted_functions"] == ["fund_etf_hist_em", "stock_zh_a_hist"]
    assert metadata["successful_function"] == "stock_zh_a_hist"
    assert metadata["audit_metadata"]["adapter_metadata"]["failed_attempts"][0]["exception_type"] == "ConnectionError"


def test_akshare_market_all_failures_produce_clear_diagnostic_without_secrets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def fund_etf_hist_em(**kwargs):
        _ = kwargs
        raise ConnectionError("RemoteDisconnected token=abc123")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise RuntimeError("endpoint changed api_key=secret123")

    module.fund_etf_hist_em = fund_etf_hist_em
    module.stock_zh_a_hist = stock_zh_a_hist
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
            ),
        )

    message = str(exc_info.value)
    assert "dataset_type=market" in message
    assert "symbol=510300" in message
    assert "inferred_symbol_type=ETF" in message
    assert "attempted_functions=['fund_etf_hist_em', 'stock_zh_a_hist']" in message
    assert "ConnectionError" in message
    assert "RuntimeError" in message
    assert "token=<redacted>" in message
    assert "api_key=<redacted>" in message
    assert "abc123" not in message
    assert "secret123" not in message
    assert "LOCAL_CSV fallback" in message


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

    assert {"LOCAL_CSV", "MOCK", "AKSHARE_OPTIONAL"}.issubset(set(adapters))
    assert "AKSHARE_OPTIONAL" not in list_data_source_adapters(include_real=False)


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

    def fund_etf_hist_em(**kwargs):
        module.calls.append({"function": "fund_etf_hist_em", **kwargs})
        return _akshare_market_rows()

    def stock_zh_a_hist(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist", **kwargs})
        return _akshare_market_rows()

    module.fund_etf_hist_em = fund_etf_hist_em
    module.stock_zh_a_hist = stock_zh_a_hist

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


def _fake_akshare_universe_module(frame: pd.DataFrame) -> ModuleType:
    module = ModuleType("akshare")
    module.universe_calls = []

    def stock_info_a_code_name():
        module.universe_calls.append({"function": "stock_info_a_code_name"})
        return frame.copy()

    module.stock_info_a_code_name = stock_info_a_code_name
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
