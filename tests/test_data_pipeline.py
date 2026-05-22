import json
import sys
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import DataPipelineSettings, load_settings
from quant_replay_system.data_pipeline import (
    DataPipelineDatasetRequest,
    run_data_source_ingestion_pipeline,
)


def test_single_market_dataset_pipeline_succeeds_from_local_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.dataset_results[0].dataset_type == "market"
    assert result.dataset_results[0].processed_data_path is not None
    assert result.dataset_results[0].processed_data_path.exists()


def test_single_universe_dataset_pipeline_succeeds(tmp_path: Path) -> None:
    input_path = tmp_path / "universe.csv"
    _universe_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [DataPipelineDatasetRequest(dataset_type="universe", source="LOCAL_CSV", input_path=input_path)],
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.dataset_results[0].row_count == 2


def test_single_trading_calendar_dataset_pipeline_succeeds(tmp_path: Path) -> None:
    input_path = tmp_path / "calendar.csv"
    _calendar_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )

    assert result.status == "PASS"
    assert result.processed_paths["trading_calendar"].exists()


def test_unknown_dataset_type_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="dataset_type must be one of"):
        run_data_source_ingestion_pipeline(
            [{"dataset_type": "unknown", "source": "LOCAL_CSV"}],
            config=_settings(tmp_path),
        )


def test_missing_input_path_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Local CSV input not found"):
        run_data_source_ingestion_pipeline(
            [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": tmp_path / "missing.csv"}],
            config=_settings(tmp_path),
        )


def test_data_quality_runs_when_enabled(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
        run_data_quality=True,
    )

    assert result.dataset_results[0].data_quality_status == "PASS"
    assert result.dataset_results[0].data_quality_report_path is not None
    assert result.dataset_results[0].data_quality_report_path.exists()


def test_data_quality_can_be_skipped(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
        run_data_quality=False,
    )

    assert result.status == "PASS"
    assert result.quality_results == {}
    assert result.dataset_results[0].data_quality_status is None
    assert "data_quality_summary" not in result.artifact_paths


def test_data_quality_fail_changes_pipeline_status_according_to_config(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    frame = _market_frame()
    frame.loc[0, "pre_close"] = 0
    frame.to_csv(input_path, index=False)

    warn_result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )
    fail_result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path, fail_on_data_quality_fail=True),
    )

    assert warn_result.status == "WARN"
    assert warn_result.dataset_results[0].data_quality_status == "FAIL"
    assert fail_result.status == "FAIL"


def test_processed_csv_is_written_and_readable_by_pandas(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )
    processed = pd.read_csv(result.processed_paths["market"])

    assert len(processed) == 2
    assert "available_time" in processed.columns


def test_data_quality_report_path_is_recorded_when_run(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )

    assert result.dataset_results[0].data_quality_report_path == result.quality_results["market"].artifact_paths["data_quality_report"]


def test_multi_dataset_manifest_mode_builds_snapshot_manifest(tmp_path: Path) -> None:
    manifest = _pipeline_manifest(tmp_path)

    result = run_data_source_ingestion_pipeline(
        _load_manifest_requests(manifest),
        config=_settings(tmp_path),
    )

    assert result.snapshot_manifest_path is not None
    payload = json.loads(result.snapshot_manifest_path.read_text(encoding="utf-8"))
    assert set(payload["processed_files"]) == {"market", "universe", "trading_calendar"}


def test_snapshot_manifest_includes_required_dataset_paths(tmp_path: Path) -> None:
    manifest = _pipeline_manifest(tmp_path)

    result = run_data_source_ingestion_pipeline(_load_manifest_requests(manifest), config=_settings(tmp_path))
    payload = json.loads(result.snapshot_manifest_path.read_text(encoding="utf-8"))

    assert Path(payload["processed_files"]["market"]).exists()
    assert Path(payload["processed_files"]["universe"]).exists()
    assert Path(payload["processed_files"]["trading_calendar"]).exists()


def test_pipeline_artifacts_are_written(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )

    assert result.artifact_paths["data_pipeline_report"].exists()
    assert result.artifact_paths["dataset_results"].exists()
    assert result.artifact_paths["processed_paths"].exists()
    assert result.artifact_paths["data_quality_summary"].exists()


def test_metadata_json_is_written(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["pipeline_id"] == result.pipeline_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_pipeline_id_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)
    request = [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}]

    first = run_data_source_ingestion_pipeline(request, config=_settings(tmp_path))
    second = run_data_source_ingestion_pipeline(request, config=_settings(tmp_path))

    assert first.pipeline_id == second.pipeline_id
    assert first.artifact_paths == second.artifact_paths


def test_cli_data_pipeline_works_in_single_dataset_mode(tmp_path: Path, monkeypatch, capsys) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)
    monkeypatch.setattr("quant_replay_system.cli.load_settings", lambda path: _project_settings(tmp_path))

    code = cli.main(
        [
            "data-pipeline",
            "--dataset-type",
            "market",
            "--source",
            "LOCAL_CSV",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Data pipeline status: PASS" in output.out
    assert "processed_market:" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_data_pipeline_works_in_manifest_mode(tmp_path: Path, monkeypatch, capsys) -> None:
    manifest = _pipeline_manifest(tmp_path)
    monkeypatch.setattr("quant_replay_system.cli.load_settings", lambda path: _project_settings(tmp_path))

    code = cli.main(
        [
            "data-pipeline",
            "--manifest",
            str(manifest),
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Data pipeline status: PASS" in output.out
    assert "Snapshot manifest path:" in output.out


def test_cli_blocks_real_source_unless_allow_real_data_is_passed(tmp_path: Path, capsys) -> None:
    code = cli.main(
        [
            "data-pipeline",
            "--dataset-type",
            "market",
            "--source",
            "AKSHARE_OPTIONAL",
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "requires explicit --allow-real-data" in output.err


def test_pipeline_akshare_optional_uses_fake_module_when_real_data_allowed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setitem(sys.modules, "akshare", _fake_akshare_module())

    result = run_data_source_ingestion_pipeline(
        [
            {
                "dataset_type": "market",
                "source": "AKSHARE_OPTIONAL",
                "allow_real_data": True,
                "symbol": "510300",
                "start_date": "2024-01-01",
                "end_date": "2024-01-03",
            }
        ],
        config=_settings(tmp_path, allow_real_data=True),
        run_data_quality=False,
        build_snapshot_manifest=False,
    )

    assert result.status == "PASS"
    assert result.dataset_results[0].source == "AKSHARE_OPTIONAL"
    assert result.dataset_results[0].source_result is not None
    assert result.dataset_results[0].source_result.audit_metadata["real_data_allowed"] is True
    assert result.processed_paths["market"].exists()
    processed = pd.read_csv(result.processed_paths["market"])
    assert processed["symbol"].astype(str).tolist() == ["510300", "510300"]


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    input_path = tmp_path / "market.csv"
    _market_frame().to_csv(input_path, index=False)

    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "LOCAL_CSV", "input_path": input_path}],
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_no_real_network_api_calls_are_used_in_tests(tmp_path: Path) -> None:
    result = run_data_source_ingestion_pipeline(
        [{"dataset_type": "market", "source": "MOCK"}],
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["network_api_calls_used_in_tests"] is False
    assert result.dataset_results[0].source_result.audit_metadata["network_api_calls_used_in_tests"] is False


def _settings(tmp_path: Path, **overrides) -> DataPipelineSettings:
    payload = {
        "output_dir": tmp_path / "reports",
        "raw_output_dir": tmp_path / "raw",
        "processed_output_dir": tmp_path / "processed",
        "snapshot_output_dir": tmp_path / "snapshots",
        "write_artifacts": True,
    }
    payload.update(overrides)
    return DataPipelineSettings(**payload)


def _project_settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(update={"data_pipeline": _settings(tmp_path)})


def _load_manifest_requests(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["datasets"]


def _pipeline_manifest(tmp_path: Path) -> Path:
    market = tmp_path / "market.csv"
    universe = tmp_path / "universe.csv"
    calendar = tmp_path / "calendar.csv"
    _market_frame().to_csv(market, index=False)
    _universe_frame().to_csv(universe, index=False)
    _calendar_frame().to_csv(calendar, index=False)
    manifest = tmp_path / "data_pipeline_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(market)},
                    {"dataset_type": "universe", "source": "LOCAL_CSV", "input_path": str(universe)},
                    {"dataset_type": "trading_calendar", "source": "LOCAL_CSV", "input_path": str(calendar)},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


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
                "pre_close": 9.9,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": 10.89,
                "limit_down": 8.91,
                "event_time": "2024-05-20 15:00:00",
                "publish_time": "2024-05-20 15:10:00",
                "ingest_time": "2024-05-20 15:20:00",
                "available_time": "2024-05-20 15:30:00",
                "revision_id": "v1",
                "source": "TEST",
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
                "pre_close": 19.9,
                "adj_factor": 1.0,
                "is_suspended": False,
                "limit_up": 21.89,
                "limit_down": 17.91,
                "event_time": "2024-05-20 15:00:00",
                "publish_time": "2024-05-20 15:10:00",
                "ingest_time": "2024-05-20 15:20:00",
                "available_time": "2024-05-20 15:30:00",
                "revision_id": "v1",
                "source": "TEST",
            },
        ]
    )


def _universe_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "as_of_date": "2024-05-20",
                "symbol": "AAA",
                "name": "AAA Fund",
                "instrument_type": "ETF",
                "exchange": "SSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "ETF",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
            {
                "as_of_date": "2024-05-20",
                "symbol": "BBB",
                "name": "BBB Stock",
                "instrument_type": "STOCK",
                "exchange": "SZSE",
                "listed_date": "2020-01-01",
                "delisted_date": "",
                "is_active": True,
                "is_st": False,
                "is_suspended": False,
                "industry": "Tech",
                "min_lot": 100,
                "t_plus_rule": "T+1",
                "available_time": "2024-05-20 08:00:00",
                "revision_id": "v1",
                "source": "TEST",
            },
        ]
    )


def _calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-05-20",
                "is_trading_day": True,
                "session_open": "09:30",
                "session_close": "15:00",
                "decision_time": "15:30",
                "reason": "normal",
            },
            {
                "trade_date": "2024-05-21",
                "is_trading_day": False,
                "session_open": "",
                "session_close": "",
                "decision_time": "",
                "reason": "holiday",
            },
        ]
    )


def _fake_akshare_module() -> ModuleType:
    module = ModuleType("akshare")

    def fund_etf_hist_em(**kwargs):
        _ = kwargs
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
    return module
