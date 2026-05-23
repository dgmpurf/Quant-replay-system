import json
import sys
from pathlib import Path
from types import ModuleType

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.data_source_health import run_data_source_health_check


def test_local_csv_health_passes_with_readable_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_health_check(
        source="LOCAL_CSV",
        dataset_type="market",
        input_path=input_path,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.health_frame.iloc[0]["source"] == "LOCAL_CSV"
    assert int(result.health_frame.iloc[0]["row_count"]) == 2


def test_local_csv_health_fails_for_missing_path(tmp_path: Path) -> None:
    result = run_data_source_health_check(
        source="LOCAL_CSV",
        dataset_type="market",
        input_path=tmp_path / "missing.csv",
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.error_count == 1
    assert "Local CSV input not found" in result.health_frame.iloc[0]["safe_error_message"]


def test_mock_health_passes(tmp_path: Path) -> None:
    result = run_data_source_health_check(
        source="MOCK",
        dataset_type="market",
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.health_frame.iloc[0]["source"] == "MOCK"
    assert int(result.health_frame.iloc[0]["row_count"]) > 0


def test_akshare_health_blocks_without_allow_real_data_without_importing_akshare(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delitem(sys.modules, "akshare", raising=False)

    result = run_data_source_health_check(
        source="AKSHARE_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.status == "WARN"
    assert set(result.health_frame["error_type"]) == {"BLOCKED_REAL_DATA"}
    assert "akshare" not in sys.modules


def test_akshare_health_fake_tencent_stock_passes(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_health_check(
        source="AKSHARE_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        allow_real_data=True,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path, allow_real=True),
    )

    configured = result.health_frame[result.health_frame["requested_upstream"] == "CONFIGURED_ORDER"].iloc[0]
    assert result.status == "PASS"
    assert configured["successful_upstream"] == "TENCENT"
    assert configured["successful_function"] == "stock_zh_a_hist_tx"
    assert int(configured["row_count"]) == 2


def test_akshare_health_fake_sina_etf_passes(tmp_path: Path, monkeypatch) -> None:
    module = _fake_akshare_module()
    monkeypatch.setitem(sys.modules, "akshare", module)

    result = run_data_source_health_check(
        source="AKSHARE_OPTIONAL",
        dataset_type="market",
        symbol="510300",
        start_date="2024-01-01",
        end_date="2024-01-03",
        allow_real_data=True,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path, allow_real=True),
    )

    configured = result.health_frame[result.health_frame["requested_upstream"] == "CONFIGURED_ORDER"].iloc[0]
    assert result.status == "PASS"
    assert configured["successful_upstream"] == "SINA"
    assert configured["successful_function"] == "fund_etf_hist_sina"


def test_akshare_health_eastmoney_failure_with_fallback_route_passes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")
    module.calls = []

    def stock_zh_a_hist(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist", **kwargs})
        raise ConnectionError("RemoteDisconnected token=super_secret_value")

    def stock_zh_a_daily(**kwargs):
        module.calls.append({"function": "stock_zh_a_daily", **kwargs})
        return _market_rows()

    module.stock_zh_a_hist = stock_zh_a_hist
    module.stock_zh_a_daily = stock_zh_a_daily
    monkeypatch.setitem(sys.modules, "akshare", module)

    settings = _settings(
        tmp_path,
        allow_real=True,
        stock_order=["EASTMONEY", "SINA"],
        retry_count=0,
    )
    result = run_data_source_health_check(
        source="AKSHARE_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        allow_real_data=True,
        output_dir=tmp_path / "health",
        config=settings,
    )

    configured = result.health_frame[result.health_frame["requested_upstream"] == "CONFIGURED_ORDER"].iloc[0]
    eastmoney = result.health_frame[result.health_frame["requested_upstream"] == "EASTMONEY"].iloc[0]
    assert result.status == "PASS"
    assert configured["successful_upstream"] == "SINA"
    assert json.loads(configured["attempted_upstreams"]) == ["EASTMONEY", "SINA"]
    assert eastmoney["status"] == "FAIL"
    assert "super_secret_value" not in eastmoney["safe_error_message"]


def test_akshare_health_all_routes_fail_with_recommended_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = ModuleType("akshare")

    def stock_zh_a_hist_tx(**kwargs):
        _ = kwargs
        raise TimeoutError("Tencent timeout")

    def stock_zh_a_daily(**kwargs):
        _ = kwargs
        raise ConnectionError("Sina disconnected")

    def stock_zh_a_hist(**kwargs):
        _ = kwargs
        raise ConnectionError("Eastmoney disconnected")

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    module.stock_zh_a_daily = stock_zh_a_daily
    module.stock_zh_a_hist = stock_zh_a_hist
    monkeypatch.setitem(sys.modules, "akshare", module)

    settings = _settings(tmp_path, allow_real=True, curl_fallback=False, retry_count=0)
    result = run_data_source_health_check(
        source="AKSHARE_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        allow_real_data=True,
        output_dir=tmp_path / "health",
        config=settings,
    )

    configured = result.health_frame[result.health_frame["requested_upstream"] == "CONFIGURED_ORDER"].iloc[0]
    assert result.status == "FAIL"
    assert configured["status"] == "FAIL"
    assert "LOCAL_CSV" in configured["recommended_fallback"]
    assert "stock_zh_a_hist_tx" in configured["safe_error_message"]


def test_baostock_health_blocks_without_allow_real_data_without_importing_baostock(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delitem(sys.modules, "baostock", raising=False)

    result = run_data_source_health_check(
        source="BAOSTOCK_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.status == "WARN"
    assert set(result.health_frame["error_type"]) == {"BLOCKED_REAL_DATA"}
    assert "baostock" not in sys.modules


def test_baostock_health_fake_market_passes(tmp_path: Path, monkeypatch) -> None:
    module = _fake_baostock_module()
    monkeypatch.setitem(sys.modules, "baostock", module)

    result = run_data_source_health_check(
        source="BAOSTOCK_OPTIONAL",
        dataset_type="market",
        symbol="000001",
        start_date="2024-01-01",
        end_date="2024-01-03",
        allow_real_data=True,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path, allow_real=True),
    )

    row = result.health_frame.iloc[0]
    assert result.status == "PASS"
    assert row["successful_upstream"] == "BAOSTOCK"
    assert row["successful_function"] == "query_history_k_data_plus"
    assert int(row["row_count"]) == 2
    assert module.calls[1]["code"] == "sz.000001"


def test_data_source_health_writes_artifacts_readable_by_pandas(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_health_check(
        source="LOCAL_CSV",
        dataset_type="market",
        input_path=input_path,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    paths = result.artifact_paths
    assert paths["data_source_health_report"].exists()
    results = pd.read_csv(paths["data_source_health_results"])
    summary = pd.read_csv(paths["data_source_health_summary"])
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert len(results) == 1
    assert summary.iloc[0]["status"] == "PASS"
    assert metadata["no_live_trading"] is True
    assert "secret" not in json.dumps(metadata).lower()


def test_cli_data_source_health_works_for_local_csv(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    code = cli.main(
        [
            "data-source-health",
            "--source",
            "LOCAL_CSV",
            "--dataset-type",
            "market",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Data source health status: PASS" in output.out
    assert "Report path:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_no_live_trading_or_network_calls_are_used_by_local_health(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_health_check(
        source="LOCAL_CSV",
        dataset_type="market",
        input_path=input_path,
        output_dir=tmp_path / "health",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


def _settings(
    tmp_path: Path,
    *,
    allow_real: bool = False,
    stock_order: list[str] | None = None,
    retry_count: int = 1,
    curl_fallback: bool = False,
):
    settings = load_settings(Path("config/default.yaml"))
    data_source_updates = {
        "raw_output_dir": tmp_path / "raw",
        "allow_network_sources": allow_real,
        "allow_real_data_fetch": allow_real,
        "akshare_market_retry_count": retry_count,
        "akshare_market_enable_curl_cffi_fallback": curl_fallback,
    }
    if stock_order is not None:
        data_source_updates["akshare_market_stock_fallback_order"] = stock_order
    return settings.model_copy(
        update={
            "data_sources": settings.data_sources.model_copy(update=data_source_updates),
            "data_source_health": settings.data_source_health.model_copy(
                update={"output_dir": tmp_path / "health"}
            ),
        }
    )


def _market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "000001",
                "trade_date": "2024-01-02",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "amount": 10200,
            },
            {
                "symbol": "510300",
                "trade_date": "2024-01-03",
                "open": 20.0,
                "high": 20.5,
                "low": 19.8,
                "close": 20.2,
                "volume": 2000,
                "amount": 40400,
            },
        ]
    )


def _fake_akshare_module() -> ModuleType:
    module = ModuleType("akshare")
    module.calls = []

    def stock_zh_a_hist_tx(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist_tx", **kwargs})
        return _market_rows()

    def stock_zh_a_daily(**kwargs):
        module.calls.append({"function": "stock_zh_a_daily", **kwargs})
        return _market_rows()

    def stock_zh_a_hist(**kwargs):
        module.calls.append({"function": "stock_zh_a_hist", **kwargs})
        return _market_rows()

    def fund_etf_hist_sina(**kwargs):
        module.calls.append({"function": "fund_etf_hist_sina", **kwargs})
        return _market_rows()

    def fund_etf_hist_em(**kwargs):
        module.calls.append({"function": "fund_etf_hist_em", **kwargs})
        return _market_rows()

    module.stock_zh_a_hist_tx = stock_zh_a_hist_tx
    module.stock_zh_a_daily = stock_zh_a_daily
    module.stock_zh_a_hist = stock_zh_a_hist
    module.fund_etf_hist_sina = fund_etf_hist_sina
    module.fund_etf_hist_em = fund_etf_hist_em
    return module


def _fake_baostock_module() -> ModuleType:
    module = ModuleType("baostock")
    module.calls = []

    class SuccessResult:
        error_code = "0"
        error_msg = "success"

    class QueryResult(SuccessResult):
        fields = [
            "date",
            "code",
            "open",
            "high",
            "low",
            "close",
            "preclose",
            "volume",
            "amount",
            "tradestatus",
        ]

        def __init__(self, code: str) -> None:
            self._rows = [
                ["2024-01-02", code, "10.0", "10.5", "9.8", "10.2", "9.9", "1000", "10200", "1"],
                ["2024-01-03", code, "10.2", "10.8", "10.1", "10.6", "10.2", "1100", "11660", "1"],
            ]
            self._index = -1

        def next(self) -> bool:
            self._index += 1
            return self._index < len(self._rows)

        def get_row_data(self) -> list[str]:
            return self._rows[self._index]

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
        return QueryResult(code)

    module.login = login
    module.logout = logout
    module.query_history_k_data_plus = query_history_k_data_plus
    return module


def _market_rows() -> pd.DataFrame:
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
