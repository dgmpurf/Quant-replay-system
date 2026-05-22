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
    exported = pd.read_csv(result.artifact_paths["raw_data"])
    assert list(exported["symbol"]) == ["AAA", "BBB"]


def test_mock_adapter_uses_configured_mock_data(tmp_path: Path) -> None:
    result = run_data_source_fetch(
        DataSourceRequest(source="MOCK", dataset_type="market"),
        settings=_settings(tmp_path),
    )

    assert result.source == "MOCK"
    assert result.row_count > 0
    assert result.artifact_paths["raw_data"].exists()
    exported = pd.read_csv(result.artifact_paths["raw_data"])
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
    exported = pd.read_csv(result.artifact_paths["raw_data"])
    assert {"symbol", "trade_date", "open", "close", "available_time"}.issubset(exported.columns)
    assert exported["source"].eq("AKSHARE_OPTIONAL").all()
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["adapter_status"] == "SUCCESS"
    assert metadata["symbol"] == "510300"
    assert metadata["allow_real_data"] is True
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


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
    exported = pd.read_csv(result.artifact_paths["raw_data"])
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

    exported = pd.read_csv(result.artifact_paths["raw_data"])

    assert exported.loc[0, "exchange"] == "SSE"
    assert exported.loc[0, "industry"] == "UNKNOWN"
    assert bool(exported.loc[0, "is_active"]) is True
    assert bool(exported.loc[0, "is_st"]) is False
    assert bool(exported.loc[0, "is_suspended"]) is False
    assert exported.loc[0, "min_lot"] == 100
    assert exported.loc[0, "t_plus_rule"] == "T+1"


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
        module.calls.append(kwargs)
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

    module.fund_etf_hist_em = fund_etf_hist_em

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
