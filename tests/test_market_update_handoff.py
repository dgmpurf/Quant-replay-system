import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from quant_replay_system import cli
import quant_replay_system.market_update_handoff as handoff_module
from quant_replay_system.config import load_settings
from quant_replay_system.market_update_handoff import (
    build_cache_backed_pipeline_manifest,
    build_batch_market_csv,
    collect_accepted_update_rows,
    run_market_update_snapshot_handoff,
)


def test_collect_accepted_update_rows_includes_warn_accept_by_default() -> None:
    frame = _symbol_results_frame(
        [
            _symbol_result(symbol="000001", preflight_status="ACCEPT", status="PASS"),
            _symbol_result(symbol="510300", preflight_status="WARN_ACCEPT", status="WARN"),
            _symbol_result(symbol="600000", preflight_status="REJECT", status="BLOCKED_PREFLIGHT_REJECT"),
        ]
    )

    rows = collect_accepted_update_rows(frame)

    assert rows["included"].tolist() == [True, True, False]
    assert rows["handoff_status"].tolist() == ["INCLUDED_ACCEPT", "INCLUDED_WARN_ACCEPT", "EXCLUDED"]


def test_collect_accepted_update_rows_strict_mode_excludes_warn_accept() -> None:
    frame = _symbol_results_frame(
        [_symbol_result(symbol="510300", preflight_status="WARN_ACCEPT", status="WARN")]
    )

    rows = collect_accepted_update_rows(frame, strict_accept_only=True)

    assert bool(rows.iloc[0]["included"]) is False
    assert "strict_accept_only" in rows.iloc[0]["inclusion_reason"]


def test_batch_market_csv_preserves_leading_zero_symbols(tmp_path: Path) -> None:
    raw_000001, metadata_000001 = _write_raw_and_metadata(tmp_path / "stock", symbol="000001")
    raw_510300, metadata_510300 = _write_raw_and_metadata(
        tmp_path / "etf",
        symbol="510300",
        upstream_source="SINA",
        successful_function="fund_etf_hist_sina",
    )
    rows = collect_accepted_update_rows(
        _symbol_results_frame(
            [
                _symbol_result(symbol="000001", raw_data_path=raw_000001, metadata_path=metadata_000001),
                _symbol_result(
                    symbol="510300",
                    status="WARN",
                    preflight_status="WARN_ACCEPT",
                    raw_data_path=raw_510300,
                    metadata_path=metadata_510300,
                ),
            ]
        )
    )

    batch_path, counts = build_batch_market_csv(rows, tmp_path / "batch" / "market_raw_data.csv")
    batch = pd.read_csv(batch_path, dtype={"symbol": str})

    assert counts == {
        f"2|000001|{raw_000001}": 2,
        f"2|510300|{raw_510300}": 2,
    }
    assert batch["symbol"].tolist() == ["000001", "000001", "510300", "510300"]
    assert "upstream_source" in batch.columns


def test_generated_data_pipeline_manifest_uses_local_csv_paths(tmp_path: Path) -> None:
    manifest = build_cache_backed_pipeline_manifest(
        market_path=tmp_path / "market.csv",
        universe_path=tmp_path / "universe.csv",
        trading_calendar_path=tmp_path / "calendar.csv",
        output_path=tmp_path / "manifest.json",
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert [item["source"] for item in payload["datasets"]] == ["LOCAL_CSV", "LOCAL_CSV", "LOCAL_CSV"]
    assert [item["dataset_type"] for item in payload["datasets"]] == ["market", "universe", "trading_calendar"]


def test_handoff_excludes_rejected_rows_and_does_not_mutate_cache(tmp_path: Path, monkeypatch) -> None:
    good_raw, good_metadata = _write_raw_and_metadata(tmp_path / "good", symbol="000001")
    bad_raw, bad_metadata = _write_raw_and_metadata(tmp_path / "bad", symbol="600000", invalid_ohlc=True)
    manifest = _write_offline_manifest(
        tmp_path,
        [
            _manifest_row(symbol="000001", raw_input=good_raw, metadata_path=good_metadata, reference_source=""),
            _manifest_row(symbol="600000", raw_input=bad_raw, metadata_path=bad_metadata, reference_source=""),
        ],
    )
    universe = _write_universe(tmp_path)
    calendar = _write_calendar(tmp_path)
    cache_path = tmp_path / "cache" / "daily_bars.csv"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("sentinel\n", encoding="utf-8")

    result = run_market_update_snapshot_handoff(
        symbol_manifest=manifest,
        universe=universe,
        trading_calendar=calendar,
        decision_date="2024-05-20",
        universe_name="etf_core",
        run_validation=False,
        config=_settings(tmp_path, cache_path=cache_path),
    )

    assert result.status == "WARN"
    assert result.included_row_count == 1
    assert "BLOCKED_PREFLIGHT_REJECT" in set(result.handoff_rows_frame["source_row_status"])
    assert cache_path.read_text(encoding="utf-8") == "sentinel\n"


def test_handoff_runs_mocked_validation_chain_for_offline_manifest(tmp_path: Path, monkeypatch) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, symbol="510300", upstream_source="SINA")
    manifest = _write_offline_manifest(
        tmp_path,
        [
            _manifest_row(
                symbol="510300",
                security_type="ETF",
                preferred_upstream="SINA",
                raw_input=raw_path,
                metadata_path=metadata_path,
                reference_source="",
            )
        ],
    )
    universe = _write_universe(tmp_path, symbol="510300")
    calendar = _write_calendar(tmp_path)

    def _fake_validation_chain(**_kwargs):
        return _fake_pipeline_result(), _fake_snapshot_result(), _fake_current_result()

    monkeypatch.setattr(handoff_module, "_run_validation_chain", _fake_validation_chain)

    result = run_market_update_snapshot_handoff(
        symbol_manifest=manifest,
        universe=universe,
        trading_calendar=calendar,
        decision_date="2024-05-20",
        universe_name="etf_core",
        selection_profile="demo",
        config=_settings(tmp_path),
    )

    assert result.status == "WARN"
    assert result.pipeline_result.pipeline_id == "pipeline-test"
    assert result.snapshot_quality_result.status == "PASS"
    assert result.current_candidate_result.run_id == "candidate-test"
    assert result.artifact_paths["market_update_handoff_report"].exists()
    assert result.artifact_paths["market_update_handoff_rows"].exists()
    assert result.artifact_paths["generated_pipeline_manifest"].exists()


def test_cli_market_update_handoff_works_with_offline_manifest(tmp_path: Path, capsys) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, symbol="000001")
    manifest = _write_offline_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path, reference_source="")],
    )
    universe = _write_universe(tmp_path)
    calendar = _write_calendar(tmp_path)

    code = cli.main(
        [
            "market-update-handoff",
            "--symbol-manifest",
            str(manifest),
            "--universe",
            str(universe),
            "--trading-calendar",
            str(calendar),
            "--decision-date",
            "2024-05-20",
            "--universe-name",
            "etf_core",
            "--skip-validation",
            "--output-dir",
            str(tmp_path / "handoff"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Market update handoff status: PASS" in output.out
    assert "included_row_count: 1" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_handoff_audit_metadata_has_no_live_trading_or_broker(tmp_path: Path) -> None:
    raw_path, metadata_path = _write_raw_and_metadata(tmp_path, symbol="000001")
    manifest = _write_offline_manifest(
        tmp_path,
        [_manifest_row(symbol="000001", raw_input=raw_path, metadata_path=metadata_path, reference_source="")],
    )
    result = run_market_update_snapshot_handoff(
        symbol_manifest=manifest,
        universe=_write_universe(tmp_path),
        trading_calendar=_write_calendar(tmp_path),
        decision_date="2024-05-20",
        universe_name="etf_core",
        run_validation=False,
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["cache_mutated"] is False
    assert result.audit_metadata["network_api_calls_used_in_tests"] is False


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
            "market_daily_update": settings.market_daily_update.model_copy(
                update={"output_dir": tmp_path / "daily_update"}
            ),
            "market_update_handoff": settings.market_update_handoff.model_copy(
                update={
                    "output_dir": tmp_path / "handoff",
                    "batch_output_dir": tmp_path / "manual_update_batches",
                    "manifest_output_dir": tmp_path / "manual_manifests",
                }
            ),
            "data_pipeline": settings.data_pipeline.model_copy(
                update={
                    "output_dir": tmp_path / "pipeline_reports",
                    "raw_output_dir": tmp_path / "pipeline_raw",
                    "processed_output_dir": tmp_path / "processed",
                }
            ),
            "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                update={"output_dir": tmp_path / "snapshot_quality"}
            ),
            "current_candidates": settings.current_candidates.model_copy(
                update={"output_dir": tmp_path / "current_candidates"}
            ),
        }
    )


def _write_raw_and_metadata(
    tmp_path: Path,
    *,
    symbol: str = "000001",
    upstream_source: str = "TENCENT",
    successful_function: str = "stock_zh_a_hist_tx",
    invalid_ohlc: bool = False,
) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw_path = tmp_path / "raw_data.csv"
    metadata_path = tmp_path / "metadata.json"
    frame = _market_frame(symbol=symbol)
    if invalid_ohlc:
        frame.loc[0, "high"] = 1.0
        frame.loc[0, "low"] = 2.0
    frame.to_csv(raw_path, index=False)
    metadata_path.write_text(
        json.dumps(
            {
                "source": "AKSHARE_OPTIONAL",
                "dataset_type": "market",
                "symbol": symbol,
                "upstream_source": upstream_source,
                "successful_function": successful_function,
                "created_at": "1970-01-01T00:00:00+00:00",
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ),
        encoding="utf-8",
    )
    return raw_path, metadata_path


def _market_frame(*, symbol: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            _market_row(symbol, "2024-05-17", 10.0),
            _market_row(symbol, "2024-05-20", 10.2),
        ]
    )


def _market_row(symbol: str, trade_date: str, close: float) -> dict:
    return {
        "symbol": symbol,
        "trade_date": trade_date,
        "open": close - 0.1,
        "high": close + 0.2,
        "low": close - 0.3,
        "close": close,
        "volume": 1000,
        "amount": close * 1000,
        "pre_close": close - 0.2,
        "adj_factor": 1.0,
        "is_suspended": False,
        "limit_up": close * 1.1,
        "limit_down": close * 0.9,
        "event_time": f"{trade_date} 15:00:00",
        "publish_time": f"{trade_date} 15:30:00",
        "ingest_time": f"{trade_date} 16:00:00",
        "available_time": f"{trade_date} 15:30:00",
        "revision_id": "v1",
        "source": "AKSHARE_OPTIONAL",
    }


def _write_offline_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "offline_manifest.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _manifest_row(
    *,
    symbol: str,
    raw_input: Path,
    metadata_path: Path,
    status_enabled: str = "true",
    security_type: str = "STOCK",
    preferred_upstream: str = "TENCENT",
    reference_source: str = "",
) -> dict:
    return {
        "symbol": symbol,
        "source": "AKSHARE_OPTIONAL",
        "dataset_type": "market",
        "start_date": "2024-05-17",
        "end_date": "2024-05-20",
        "enabled": status_enabled,
        "security_type": security_type,
        "preferred_upstream": preferred_upstream,
        "require_fields": "close,volume,amount",
        "reference_source": reference_source,
        "strict_provisional": "false",
        "raw_input": str(raw_input),
        "metadata_path": str(metadata_path),
        "notes": "offline test row",
    }


def _symbol_results_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _symbol_result(
    *,
    symbol: str,
    source: str = "AKSHARE_OPTIONAL",
    dataset_type: str = "market",
    start_date: str = "2024-05-17",
    end_date: str = "2024-05-20",
    status: str = "PASS",
    preflight_status: str = "ACCEPT",
    raw_data_path: Path | str = "raw_data.csv",
    metadata_path: Path | str = "metadata.json",
) -> dict:
    return {
        "manifest_row": 2,
        "symbol": symbol,
        "source": source,
        "dataset_type": dataset_type,
        "start_date": start_date,
        "end_date": end_date,
        "enabled": True,
        "status": status,
        "preflight_status": preflight_status,
        "cache_write_occurred": False,
        "raw_data_path": str(raw_data_path),
        "metadata_path": str(metadata_path),
        "report_path": "",
        "row_count": 2,
        "issue_count": 0,
        "warning_count": 0,
        "error_count": 0,
        "reference_source": "",
        "require_fields": "close,volume,amount",
        "strict_provisional": False,
        "preferred_upstream": "",
        "message": "",
        "no_live_trading": True,
        "no_broker_api": True,
    }


def _write_universe(tmp_path: Path, *, symbol: str = "000001") -> Path:
    path = tmp_path / f"universe_{symbol}.csv"
    pd.DataFrame(
        [
            {
                "as_of_date": "2024-05-20",
                "symbol": symbol,
                "name": f"{symbol} demo",
                "instrument_type": "ETF" if symbol.startswith(("510", "159")) else "STOCK",
                "exchange": "SSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "demo",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "LOCAL_CSV",
            }
        ]
    ).to_csv(path, index=False)
    return path


def _write_calendar(tmp_path: Path) -> Path:
    path = tmp_path / "calendar.csv"
    pd.DataFrame(
        [
            {
                "trade_date": "2024-05-17",
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            },
            {
                "trade_date": "2024-05-20",
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _fake_pipeline_result():
    return SimpleNamespace(pipeline_id="pipeline-test", status="PASS", warnings=[], snapshot_manifest_path=Path("snapshot.json"))


def _fake_snapshot_result():
    return SimpleNamespace(
        status="PASS",
        warnings=[],
        artifact_paths={"snapshot_quality_gate_report": Path("snapshot_report.md")},
    )


def _fake_current_result():
    return SimpleNamespace(
        run_id="candidate-test",
        factor_dataset_row_count=1,
        scored_dataset_row_count=1,
        candidate_count=1,
        factor_dataset=pd.DataFrame([{"symbol": "510300"}]),
        scored_dataset=pd.DataFrame([{"symbol": "510300", "final_score": 50.0}]),
        candidates=pd.DataFrame([{"symbol": "510300"}]),
        warnings=[],
    )
