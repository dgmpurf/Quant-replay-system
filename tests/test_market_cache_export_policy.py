import hashlib
import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_cache_export import load_market_cache_export_manifest, run_market_cache_export
from quant_replay_system.market_cache_export_policy import (
    load_policy_export_request,
    run_market_cache_export_policy_plan,
)
from quant_replay_system.market_data_cache import ingest_market_cache_csv


def test_policy_plan_recommends_tencent_for_stock_when_reliable_and_available(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "AKSHARE_OPTIONAL", "TENCENT"), ("000001", "BAOSTOCK_OPTIONAL", "BAOSTOCK")])
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "PASS"
    assert row["status"] == "RECOMMENDED"
    assert row["recommended_source"] == "AKSHARE_OPTIONAL"
    assert row["recommended_upstream_source"] == "TENCENT"
    assert row["symbol"] == "000001"
    assert bool(row["comparison_available"]) is True
    assert row["comparison_reference_source"] == "BAOSTOCK_OPTIONAL"
    assert row["comparison_reference_upstream"] == "BAOSTOCK"
    assert row["comparison_status"] == "PASS"
    assert int(row["comparison_matched_rows"]) == 2
    assert row["comparison_diagnostic_classification"] == "NO_UNIT_MISMATCH"


def test_policy_plan_downgrades_stock_recommendation_when_comparison_fails(tmp_path: Path) -> None:
    _ingest_cache_rows_with_values(
        tmp_path,
        [
            ("000001", "AKSHARE_OPTIONAL", "TENCENT", 10.2),
            ("000001", "BAOSTOCK_OPTIONAL", "BAOSTOCK", 11.0),
        ],
    )
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert row["status"] == "RECOMMENDED_WITH_WARNINGS"
    assert row["recommended_source"] == "AKSHARE_OPTIONAL"
    assert bool(row["comparison_available"]) is True
    assert row["comparison_status"] == "FAIL"
    assert int(row["comparison_matched_rows"]) == 2
    assert "Comparison against BAOSTOCK_OPTIONAL/BAOSTOCK failed" in row["warnings"]


def test_policy_plan_required_field_comparison_ignores_non_required_pre_close_caveat(tmp_path: Path) -> None:
    _ingest_cache_rows_with_pre_close_values(
        tmp_path,
        [
            ("000001", "AKSHARE_OPTIONAL", "TENCENT", 10.0),
            ("000001", "BAOSTOCK_OPTIONAL", "BAOSTOCK", 9.5),
        ],
    )
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "PASS"
    assert row["status"] == "RECOMMENDED"
    assert row["comparison_status"] == "PASS"
    assert int(row["comparison_matched_rows"]) == 2
    assert row["warnings"] == ""


def test_policy_plan_recommends_baostock_for_stock_when_akshare_unavailable(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "BAOSTOCK_OPTIONAL", "BAOSTOCK")])
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "PASS"
    assert row["status"] == "RECOMMENDED"
    assert row["recommended_source"] == "BAOSTOCK_OPTIONAL"
    assert row["recommended_upstream_source"] == "BAOSTOCK"


def test_policy_plan_recommends_sina_etf_with_warning_when_provisional(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("510300", "AKSHARE_OPTIONAL", "SINA")])
    request = _request_manifest(tmp_path, [_request_row("510300", "ETF")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert row["status"] == "RECOMMENDED_WITH_WARNINGS"
    assert row["recommended_source"] == "AKSHARE_OPTIONAL"
    assert row["recommended_upstream_source"] == "SINA"
    assert "PROVISIONAL" in row["warnings"]
    assert bool(row["comparison_available"]) is False
    assert row["comparison_status"] == "UNAVAILABLE"
    assert row["comparison_diagnostic_classification"] == "NO_REFERENCE_SOURCE"
    assert "No comparison reference" in row["comparison_warning_reason"]


def test_policy_plan_rejects_baostock_etf_when_policy_unavailable(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("510300", "BAOSTOCK_OPTIONAL", "BAOSTOCK")])
    request = _request_manifest(tmp_path, [_request_row("510300", "ETF")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    row = result.recommendations_frame.iloc[0].to_dict()

    assert result.status == "FAIL"
    assert row["status"] == "NO_RELIABLE_SOURCE"
    assert "NO_RELIABLE_SOURCE" in set(result.issues_frame["category"])


def test_policy_plan_strict_mode_rejects_provisional_etf(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("510300", "AKSHARE_OPTIONAL", "SINA")])
    request = _request_manifest(tmp_path, [_request_row("510300", "ETF")])

    result = run_market_cache_export_policy_plan(request, strict_reliable=True, config=_settings(tmp_path))

    assert result.status == "FAIL"
    assert result.recommendations_frame.iloc[0]["status"] == "NO_RELIABLE_SOURCE"
    assert "strict_reliable" in result.recommendations_frame.iloc[0]["warnings"]


def test_policy_plan_no_cache_rows_returns_no_cache_rows(tmp_path: Path) -> None:
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))

    assert result.status == "FAIL"
    assert result.recommendations_frame.iloc[0]["status"] == "NO_CACHE_ROWS"
    assert "NO_CACHE_ROWS" in set(result.issues_frame["category"])


def test_generated_recommended_manifest_preserves_leading_zero_and_is_export_compatible(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "AKSHARE_OPTIONAL", "TENCENT")])
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    manifest_rows = load_market_cache_export_manifest(
        result.recommended_manifest_path,
        settings=_settings(tmp_path).market_cache_export,
    )
    export_result = run_market_cache_export(result.recommended_manifest_path, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert manifest_rows[0].symbol == "000001"
    assert manifest_rows[0].source == "AKSHARE_OPTIONAL"
    assert manifest_rows[0].upstream_source == "TENCENT"
    assert export_result.status == "PASS"
    assert export_result.exported_market_frame["symbol"].tolist() == ["000001", "000001"]


def test_policy_request_loading_preserves_leading_zero_symbols(tmp_path: Path) -> None:
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    rows = load_policy_export_request(request, settings=_settings(tmp_path).market_cache_export_policy)

    assert rows[0].symbol == "000001"
    assert rows[0].required_fields == ["close", "volume", "amount"]


def test_cli_market_cache_export_plan_works(tmp_path: Path, monkeypatch, capsys) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "AKSHARE_OPTIONAL", "TENCENT"), ("000001", "BAOSTOCK_OPTIONAL", "BAOSTOCK")])
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])
    monkeypatch.setattr("quant_replay_system.cli.load_settings", lambda path: _settings(tmp_path))

    code = cli.main(["market-cache-export-plan", "--manifest", str(request)])
    output = capsys.readouterr()

    assert code == 0
    assert "Market cache export plan status: PASS" in output.out
    assert "generated_reviewed_manifest_path:" in output.out
    assert "RECOMMENDATION: 000001 -> AKSHARE_OPTIONAL/TENCENT" in output.out
    assert "comparison=PASS vs BAOSTOCK_OPTIONAL/BAOSTOCK" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_policy_plan_does_not_mutate_market_cache(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "AKSHARE_OPTIONAL", "TENCENT")])
    cache_path = _settings(tmp_path).market_data_cache.cache_path
    before_hash = _sha256(cache_path)
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))

    assert result.status == "PASS"
    assert _sha256(cache_path) == before_hash
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["market_cache_export_run"] is False


def test_no_live_trading_broker_or_network_calls_are_used(tmp_path: Path) -> None:
    _ingest_cache_rows(tmp_path, [("000001", "AKSHARE_OPTIONAL", "TENCENT")])
    request = _request_manifest(tmp_path, [_request_row("000001", "STOCK")])

    result = run_market_cache_export_policy_plan(request, config=_settings(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True


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
            "market_cache_export_policy": settings.market_cache_export_policy.model_copy(
                update={
                    "output_dir": tmp_path / "policy_reports",
                    "manifest_output_dir": tmp_path / "manual_manifests",
                }
            ),
        }
    )


def _request_manifest(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "policy_request.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _request_row(symbol: str, security_type: str) -> dict[str, str]:
    return {
        "symbol": symbol,
        "start_date": "2024-01-02",
        "end_date": "2024-01-03",
        "required_fields": "close,volume,amount",
        "enabled": "true",
        "security_type": security_type,
        "notes": "test request",
    }


def _ingest_cache_rows(tmp_path: Path, rows: list[tuple[str, str, str]]) -> None:
    for index, (symbol, source, upstream_source) in enumerate(rows):
        input_path = tmp_path / f"{source}_{upstream_source}_{index}.csv"
        metadata_path = tmp_path / f"{source}_{upstream_source}_{index}.json"
        _market_frame(symbol, source).to_csv(input_path, index=False)
        _metadata(source, upstream_source).write_text_to(metadata_path)
        ingest_market_cache_csv(input_path, metadata_path=metadata_path, config=_settings(tmp_path))


def _ingest_cache_rows_with_values(tmp_path: Path, rows: list[tuple[str, str, str, float]]) -> None:
    for index, (symbol, source, upstream_source, close) in enumerate(rows):
        input_path = tmp_path / f"{source}_{upstream_source}_{index}.csv"
        metadata_path = tmp_path / f"{source}_{upstream_source}_{index}.json"
        _market_frame(symbol, source, close=close).to_csv(input_path, index=False)
        _metadata(source, upstream_source).write_text_to(metadata_path)
        ingest_market_cache_csv(input_path, metadata_path=metadata_path, config=_settings(tmp_path))


def _ingest_cache_rows_with_pre_close_values(tmp_path: Path, rows: list[tuple[str, str, str, float]]) -> None:
    for index, (symbol, source, upstream_source, pre_close) in enumerate(rows):
        input_path = tmp_path / f"{source}_{upstream_source}_{index}.csv"
        metadata_path = tmp_path / f"{source}_{upstream_source}_{index}.json"
        _market_frame(symbol, source, pre_close=pre_close).to_csv(input_path, index=False)
        _metadata(source, upstream_source).write_text_to(metadata_path)
        ingest_market_cache_csv(input_path, metadata_path=metadata_path, config=_settings(tmp_path))


def _market_frame(symbol: str, source: str, *, close: float = 10.2, pre_close: float = 10.0) -> pd.DataFrame:
    base = {
        "open": 10.0,
        "high": max(10.5, close),
        "low": 9.8,
        "close": close,
        "volume": 1000,
        "amount": 10200,
        "pre_close": pre_close,
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
                "symbol": symbol,
                "trade_date": "2024-01-02",
            },
            {
                **base,
                "symbol": symbol,
                "trade_date": "2024-01-03",
                "event_time": "2024-01-03 15:00:00",
                "publish_time": "2024-01-03 15:30:00",
                "ingest_time": "2024-01-03 16:00:00",
                "available_time": "2024-01-03 15:30:00",
            },
        ]
    )


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
