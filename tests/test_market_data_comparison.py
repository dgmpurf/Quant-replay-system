import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_data_cache import MARKET_CACHE_COLUMNS
from quant_replay_system.market_data_comparison import (
    build_market_source_comparison_frame,
    run_market_source_comparison,
)


def test_comparison_detects_exact_match(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02"),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    row = result.comparison_frame.iloc[0]
    assert result.status == "PASS"
    assert row["row_match_status"] == "MATCHED"
    assert row["tolerance_status"] == "PASS"
    assert bool(row["likely_volume_unit_mismatch"]) is False
    assert bool(row["likely_amount_unit_mismatch"]) is False
    assert result.summary_frame.iloc[0]["diagnostic_classification"] == "NO_UNIT_MISMATCH"
    assert result.matched_row_count == 1
    assert result.pass_count == 1


def test_comparison_detects_price_difference(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", close=10.0),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", close=10.5),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    row = result.comparison_frame.iloc[0]
    assert result.status == "FAIL"
    assert row["tolerance_status"] == "FAIL"
    assert "close" in row["tolerance_reason"]
    assert float(row["close_diff_pct"]) > 0
    assert int(result.summary_frame.iloc[0]["fail_count"]) == 1


def test_comparison_detects_volume_difference(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=1000),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=2000),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    row = result.comparison_frame.iloc[0]
    assert result.status == "FAIL"
    assert row["tolerance_status"] == "FAIL"
    assert "volume" in row["tolerance_reason"]
    assert float(row["volume_diff_pct"]) == 1.0


def test_comparison_detects_stable_volume_scale_factor(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=100, amount=10200),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=10000, amount=10200),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03", volume=120, amount=12240),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", volume=12000, amount=12240),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    summary = result.summary_frame.iloc[0]

    assert result.status == "FAIL"
    assert result.comparison_frame["likely_volume_unit_mismatch"].all()
    assert bool(summary["stable_volume_ratio_detected"]) is True
    assert abs(float(summary["median_volume_ratio"]) - 0.01) < 1e-9
    assert abs(float(summary["suspected_volume_scale_factor"]) - 0.01) < 1e-9
    assert summary["diagnostic_classification"] == "VOLUME_UNIT_MISMATCH"


def test_comparison_no_longer_reports_zero_volume_ratio_when_tencent_volume_matches(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=100000, amount=0),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=100000, amount=1020000),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    row = result.comparison_frame.iloc[0]

    assert float(row["volume_ratio_a_to_b"]) == 1.0
    assert bool(row["likely_volume_unit_mismatch"]) is False
    assert result.summary_frame.iloc[0]["median_volume_ratio"] == 1.0


def test_comparison_can_pass_when_tencent_raw_turnover_matches_baostock(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=100000, amount=1020000),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=100000, amount=1020000),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    row = result.comparison_frame.iloc[0]

    assert result.status == "PASS"
    assert float(row["volume_ratio_a_to_b"]) == 1.0
    assert float(row["amount_ratio_a_to_b"]) == 1.0
    assert result.summary_frame.iloc[0]["diagnostic_classification"] == "NO_UNIT_MISMATCH"


def test_comparison_detects_stable_amount_scale_factor(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", amount=102),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", amount=10200),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03", amount=122.4),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", amount=12240),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    summary = result.summary_frame.iloc[0]

    assert result.status == "FAIL"
    assert result.comparison_frame["likely_amount_unit_mismatch"].all()
    assert bool(summary["stable_amount_ratio_detected"]) is True
    assert abs(float(summary["median_amount_ratio"]) - 0.01) < 1e-9
    assert abs(float(summary["suspected_amount_scale_factor"]) - 0.01) < 1e-9
    assert summary["diagnostic_classification"] == "AMOUNT_UNIT_MISMATCH"


def test_comparison_classifies_price_match_volume_amount_mismatch(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=100, amount=102),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=10000, amount=10200),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03", volume=120, amount=122.4),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", volume=12000, amount=12240),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    assert result.summary_frame.iloc[0]["diagnostic_classification"] == "PRICE_MATCH_VOLUME_AMOUNT_MISMATCH"


def test_comparison_classifies_unstable_ratios_as_source_semantics(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", volume=100, amount=102),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", volume=10000, amount=10200),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03", volume=6000, amount=6120),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", volume=12000, amount=12240),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    summary = result.summary_frame.iloc[0]

    assert bool(summary["stable_volume_ratio_detected"]) is False
    assert bool(summary["stable_amount_ratio_detected"]) is False
    assert summary["diagnostic_classification"] == "SOURCE_SEMANTICS_DIFFER"


def test_comparison_detects_source_only_rows(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03"),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    assert result.status == "WARN"
    assert set(result.comparison_frame["row_match_status"]) == {"SOURCE_A_ONLY", "SOURCE_B_ONLY"}
    assert result.source_a_only_count == 1
    assert result.source_b_only_count == 1
    assert result.warn_count == 2


def test_comparison_preserves_symbol_leading_zeros(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", symbol="000001"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", symbol="000001"),
        ],
    )

    result = run_market_source_comparison(
        symbol="1",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    assert result.symbol == "000001"
    assert result.comparison_frame["symbol"].tolist() == ["000001"]


def test_comparison_summary_counts_pass_warn_and_fail(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02"),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", close=11.0),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-04"),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    summary = result.summary_frame.iloc[0]

    assert result.status == "FAIL"
    assert int(summary["matched_row_count"]) == 2
    assert int(summary["source_a_only_count"]) == 1
    assert int(summary["pass_count"]) == 1
    assert int(summary["warn_count"]) == 1
    assert int(summary["fail_count"]) == 1


def test_comparison_writes_artifacts_and_metadata(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02"),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    rows = pd.read_csv(result.artifact_paths["market_data_comparison_rows"], dtype={"symbol": str})

    assert result.artifact_paths["market_data_comparison_report"].exists()
    assert len(rows) == 1
    assert rows.iloc[0]["symbol"] == "000001"
    assert "volume_ratio_a_to_b" in rows.columns
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert "secret" not in json.dumps(metadata).lower()


def test_cli_market_cache_compare_works(tmp_path: Path, capsys) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02"),
        ],
    )

    code = cli.main(
        [
            "market-cache-compare",
            "--symbol",
            "000001",
            "--source-a",
            "AKSHARE_OPTIONAL",
            "--source-b",
            "BAOSTOCK_OPTIONAL",
            "--cache-path",
            str(cache_path),
            "--output-dir",
            str(tmp_path / "comparison"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Market cache comparison status: PASS" in output.out
    assert "matched_row_count: 1" in output.out
    assert "diagnostic_classification: NO_UNIT_MISMATCH" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_market_cache_compare_report_includes_diagnostics(tmp_path: Path) -> None:
    cache_path = _write_cache(
        tmp_path,
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02", amount=102),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02", amount=10200),
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-03", amount=122.4),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-03", amount=12240),
        ],
    )

    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )
    report = result.artifact_paths["market_data_comparison_report"].read_text(encoding="utf-8")

    assert "## Unit And Semantic Diagnostics" in report
    assert "diagnostic_classification" in report
    assert "AMOUNT_UNIT_MISMATCH" in report


def test_comparison_does_not_invoke_live_trading_or_network(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            _cache_row("AKSHARE_OPTIONAL", "TENCENT", "2024-01-02"),
            _cache_row("BAOSTOCK_OPTIONAL", "BAOSTOCK", "2024-01-02"),
        ],
        columns=MARKET_CACHE_COLUMNS,
    )

    comparison = build_market_source_comparison_frame(
        frame,
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        settings=load_settings(Path("config/default.yaml")).market_data_comparison,
    )
    cache_path = _write_cache(tmp_path, frame.to_dict("records"))
    result = run_market_source_comparison(
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
        cache_path=cache_path,
        config=_settings(tmp_path),
    )

    assert not comparison.empty
    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_data_cache": settings.market_data_cache.model_copy(
                update={"cache_path": tmp_path / "cache" / "daily_bars.csv"}
            ),
            "market_data_comparison": settings.market_data_comparison.model_copy(
                update={"output_dir": tmp_path / "comparison"}
            ),
        }
    )


def _write_cache(tmp_path: Path, rows: list[dict]) -> Path:
    cache_path = tmp_path / "cache" / "daily_bars.csv"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=MARKET_CACHE_COLUMNS).to_csv(cache_path, index=False)
    return cache_path


def _cache_row(
    source: str,
    upstream: str,
    trade_date: str,
    *,
    symbol: str = "000001",
    close: float = 10.2,
    volume: float = 1000,
    amount: float = 10200,
) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": close,
        "volume": volume,
        "amount": amount,
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
