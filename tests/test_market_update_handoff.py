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
from quant_replay_system.market_update_handoff_health import check_market_update_handoff_health
from quant_replay_system.market_update_handoff_index import build_market_update_handoff_index
from quant_replay_system.market_update_handoff_status import run_market_update_handoff_status


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


def test_market_update_handoff_index_detects_fake_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "handoff_root"
    paths = _write_fake_handoff_artifact(root, handoff_id="handoff-a", candidate_count=2)

    result = build_market_update_handoff_index(
        root=root,
        output_dir=tmp_path / "handoff_index",
    )

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["handoff_id"] == "handoff-a"
    assert row["batch_market_csv_path"] == str(paths["batch_market_csv"])
    assert row["generated_pipeline_manifest_path"] == str(paths["pipeline_manifest"])
    assert row["pipeline_id"] == "pipeline-handoff-a"
    assert row["snapshot_quality_status"] == "PASS"
    assert row["current_candidate_run_id"] == "candidate-handoff-a"
    assert int(row["factor_dataset_rows"]) == 2
    assert int(row["scored_dataset_rows"]) == 2
    assert int(row["candidate_count"]) == 2
    assert result.artifact_paths["market_update_handoff_index_csv"].exists()


def test_market_update_handoff_health_passes_complete_artifact_set(tmp_path: Path) -> None:
    root = tmp_path / "handoff_root"
    _write_fake_handoff_artifact(root, handoff_id="handoff-pass")
    index = build_market_update_handoff_index(root=root, output_dir=tmp_path / "handoff_index")

    result = check_market_update_handoff_health(
        index_df=index.index_frame,
        output_dir=tmp_path / "handoff_health",
    )

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.error_count == 0
    assert result.artifact_paths["market_update_handoff_health_report"].exists()


def test_market_update_handoff_health_fails_for_missing_batch_market_csv(tmp_path: Path) -> None:
    root = tmp_path / "handoff_root"
    paths = _write_fake_handoff_artifact(root, handoff_id="handoff-missing")
    paths["batch_market_csv"].unlink()
    index = build_market_update_handoff_index(root=root, output_dir=tmp_path / "handoff_index")

    result = check_market_update_handoff_health(
        index_df=index.index_frame,
        output_dir=tmp_path / "handoff_health",
    )

    assert result.status == "FAIL"
    assert "FILE_NOT_FOUND" in set(result.health_frame["issue_code"])


def test_market_update_handoff_status_summarizes_latest_handoff(tmp_path: Path) -> None:
    root = tmp_path / "handoff_root"
    _write_fake_handoff_artifact(root, handoff_id="handoff-old", created_at="2024-05-19T00:00:00+00:00")
    _write_fake_handoff_artifact(root, handoff_id="handoff-new", created_at="2024-05-20T00:00:00+00:00")

    result = run_market_update_handoff_status(
        root=root,
        output_dir=tmp_path / "handoff_status",
    )

    assert result.status == "PASS"
    assert result.latest_handoff_id == "handoff-new"
    assert result.workflow_stage == "CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST"
    assert "current-to-paper" in result.next_manual_action
    assert result.artifact_paths["market_update_handoff_status_report"].exists()


def test_cli_market_update_handoff_index_health_status_commands(tmp_path: Path, capsys) -> None:
    root = tmp_path / "handoff_root"
    _write_fake_handoff_artifact(root, handoff_id="handoff-cli")

    index_code = cli.main(
        [
            "market-update-handoff-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "handoff_index"),
        ]
    )
    index_output = capsys.readouterr()
    index_csv = tmp_path / "handoff_index" / "market_update_handoff_index.csv"
    assert index_code == 0
    assert "artifact_count: 1" in index_output.out
    assert index_csv.exists()

    health_code = cli.main(
        [
            "market-update-handoff-health",
            "--index",
            str(index_csv),
            "--output-dir",
            str(tmp_path / "handoff_health"),
        ]
    )
    health_output = capsys.readouterr()
    assert health_code == 0
    assert "Market update handoff health status: PASS" in health_output.out

    status_code = cli.main(
        [
            "market-update-handoff-status",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "handoff_status"),
        ]
    )
    status_output = capsys.readouterr()
    assert status_code == 0
    assert "workflow_stage: CURRENT_CANDIDATES_READY_FOR_PAPER_SMOKE_TEST" in status_output.out
    assert "No live trading or broker API was invoked." in status_output.out


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


def _write_fake_handoff_artifact(
    root: Path,
    *,
    handoff_id: str,
    created_at: str = "2024-05-20T00:00:00+00:00",
    candidate_count: int = 1,
) -> dict[str, Path]:
    artifact_dir = root / handoff_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    linked_dir = root / "_linked" / handoff_id
    linked_dir.mkdir(parents=True, exist_ok=True)

    batch_market_csv = linked_dir / "market_raw_data.csv"
    _market_frame(symbol="000001").to_csv(batch_market_csv, index=False)
    pipeline_manifest = linked_dir / "market_update_handoff_manifest.json"
    pipeline_manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(batch_market_csv)}
                ]
            }
        ),
        encoding="utf-8",
    )
    pipeline_report = linked_dir / "data_pipeline_report.md"
    snapshot_report = linked_dir / "snapshot_quality_gate_report.md"
    current_report = linked_dir / "current_candidates_report.md"
    no_live = "No live trading or broker API was invoked."
    pipeline_report.write_text(no_live, encoding="utf-8")
    snapshot_report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    current_report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    snapshot_manifest = linked_dir / "snapshot_manifest.json"
    snapshot_manifest.write_text("{}", encoding="utf-8")

    current_metadata = linked_dir / "current_candidate_metadata.json"
    factor_dataset = linked_dir / "factor_dataset.csv"
    scored_dataset = linked_dir / "scored_dataset.csv"
    candidates = linked_dir / "candidates.csv"
    pd.DataFrame([{"symbol": "000001"}] * candidate_count).to_csv(factor_dataset, index=False)
    pd.DataFrame([{"symbol": "000001", "final_score": 50.0}] * candidate_count).to_csv(scored_dataset, index=False)
    pd.DataFrame([{"symbol": "000001"}] * candidate_count).to_csv(candidates, index=False)
    current_metadata.write_text(
        json.dumps({"run_id": f"candidate-{handoff_id}", "no_live_trading": True}),
        encoding="utf-8",
    )

    handoff_report = artifact_dir / "market_update_handoff_report.md"
    handoff_rows = artifact_dir / "market_update_handoff_rows.csv"
    manifest_artifact = artifact_dir / "generated_pipeline_manifest.json"
    handoff_report.write_text(no_live, encoding="utf-8")
    pd.DataFrame(
        [
            {
                "symbol": "000001",
                "included": True,
                "handoff_status": "INCLUDED_ACCEPT",
                "raw_data_path": str(batch_market_csv),
            }
        ]
    ).to_csv(handoff_rows, index=False)
    manifest_artifact.write_text(pipeline_manifest.read_text(encoding="utf-8"), encoding="utf-8")

    metadata = {
        "handoff_id": handoff_id,
        "status": "PASS",
        "created_at": created_at,
        "summary": [{"included_row_count": 1}],
        "batch_market_csv_path": str(batch_market_csv),
        "generated_pipeline_manifest_path": str(pipeline_manifest),
        "pipeline_id": f"pipeline-{handoff_id}",
        "pipeline_status": "PASS",
        "data_pipeline_report_path": str(pipeline_report),
        "snapshot_manifest_path": str(snapshot_manifest),
        "snapshot_quality_status": "PASS",
        "snapshot_quality_report_path": str(snapshot_report),
        "current_candidate_run_id": f"candidate-{handoff_id}",
        "current_candidate_artifact_paths": {
            "current_candidates_report": str(current_report),
            "metadata": str(current_metadata),
            "factor_dataset": str(factor_dataset),
            "scored_dataset": str(scored_dataset),
            "candidates": str(candidates),
        },
        "factor_dataset_shape": [candidate_count, 1],
        "scored_dataset_shape": [candidate_count, 2],
        "candidates_shape": [candidate_count, 1],
        "candidate_count": candidate_count,
        "warnings": [],
        "artifact_paths": {
            "market_update_handoff_report": str(handoff_report),
            "market_update_handoff_rows": str(handoff_rows),
            "generated_pipeline_manifest": str(manifest_artifact),
            "metadata": str(artifact_dir / "metadata.json"),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": no_live,
    }
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "artifact_dir": artifact_dir,
        "metadata": metadata_path,
        "handoff_report": handoff_report,
        "handoff_rows": handoff_rows,
        "batch_market_csv": batch_market_csv,
        "pipeline_manifest": pipeline_manifest,
        "manifest_artifact": manifest_artifact,
        "pipeline_report": pipeline_report,
        "snapshot_report": snapshot_report,
        "current_report": current_report,
    }
