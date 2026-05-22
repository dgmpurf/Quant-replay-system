import builtins
import json
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
