import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import SnapshotQualityGateSettings
from quant_replay_system.snapshot_quality_gate import (
    assert_snapshot_quality_passed,
    load_snapshot_manifest,
    run_snapshot_quality_gate,
)


def test_valid_manifest_with_clean_required_datasets_returns_pass(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.status == "PASS"
    assert result.required_dataset_count == 3
    assert result.failed_required_datasets == []


def test_missing_required_market_path_returns_fail(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, include_market=False)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert "market" in result.failed_required_datasets


def test_missing_optional_benchmark_path_returns_configured_warn_or_info(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, include_benchmark=False)

    info_result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "info")
    warn_result = run_snapshot_quality_gate(
        manifest,
        output_dir=tmp_path / "warn",
        settings=SnapshotQualityGateSettings(missing_optional_dataset_severity="WARN"),
    )

    assert info_result.status == "PASS"
    assert warn_result.status == "WARN"
    assert warn_result.gate_summary_frame.loc[
        warn_result.gate_summary_frame["dataset_type"] == "benchmark",
        "gate_effect",
    ].iloc[0] == "WARN"


def test_required_dataset_fail_makes_gate_fail(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.status == "FAIL"
    assert result.failed_required_datasets == ["market"]


def test_optional_dataset_fail_makes_gate_warn_by_default(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_benchmark=True)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.status == "WARN"
    assert result.failed_optional_datasets == ["benchmark"]
    row = result.gate_summary_frame.loc[result.gate_summary_frame["dataset_type"] == "benchmark"].iloc[0]
    assert row["gate_effect"] == "WARN"


def test_cli_strict_mode_treats_warn_as_nonzero(tmp_path: Path, capsys) -> None:
    manifest = _write_manifest(tmp_path, bad_benchmark=True)

    code = cli.main(
        [
            "snapshot-quality",
            "--manifest",
            str(manifest),
            "--output-dir",
            str(tmp_path / "quality"),
            "--strict",
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Snapshot quality status: WARN" in output.out


def test_gate_summary_csv_is_written_and_readable(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    frame = pd.read_csv(result.artifact_paths["snapshot_quality_summary"])

    assert "dataset_type" in frame.columns
    assert len(frame) == 5


def test_dataset_quality_results_csv_is_written_and_readable(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    frame = pd.read_csv(result.artifact_paths["dataset_quality_results"])

    assert "quality_status" in frame.columns
    assert "quality_run_id" in frame.columns


def test_dataset_issue_counts_csv_is_written_and_readable(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    frame = pd.read_csv(result.artifact_paths["dataset_issue_counts"])

    assert "issue_count" in frame.columns
    assert frame["error_count"].sum() == 0


def test_metadata_json_is_written(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["snapshot_id"] == "snapshot-a"
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_markdown_report_is_written(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    content = result.artifact_paths["snapshot_quality_gate_report"].read_text(encoding="utf-8")

    assert "# Snapshot Quality Gate" in content
    assert "No broker or live trading integration was invoked" in content


def test_quality_gate_id_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    first = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")
    second = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert first.quality_gate_id == second.quality_gate_id
    assert first.gate_summary_frame.to_dict("records") == second.gate_summary_frame.to_dict("records")


def test_assert_snapshot_quality_passed_raises_on_fail(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)
    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    with pytest.raises(ValueError, match="Snapshot quality gate failed"):
        assert_snapshot_quality_passed(result)


def test_cli_snapshot_quality_works(tmp_path: Path, capsys) -> None:
    manifest = _write_manifest(tmp_path)

    code = cli.main(["snapshot-quality", "--manifest", str(manifest), "--output-dir", str(tmp_path / "quality")])
    output = capsys.readouterr()

    assert code == 0
    assert "Snapshot quality status: PASS" in output.out


def test_cli_snapshot_quality_exits_nonzero_on_fail_by_default(tmp_path: Path, capsys) -> None:
    manifest = _write_manifest(tmp_path, bad_market=True)

    code = cli.main(["snapshot-quality", "--manifest", str(manifest), "--output-dir", str(tmp_path / "quality")])
    output = capsys.readouterr()

    assert code == 1
    assert "Snapshot quality status: FAIL" in output.out


def test_cli_snapshot_quality_prints_no_live_statement(tmp_path: Path, capsys) -> None:
    manifest = _write_manifest(tmp_path)

    code = cli.main(["snapshot-quality", "--manifest", str(manifest), "--output-dir", str(tmp_path / "quality")])
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_snapshot_quality_makes_no_network_calls(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.audit_metadata["snapshot_quality_only"] is True


def test_snapshot_quality_does_not_invoke_live_trading_or_broker(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    result = run_snapshot_quality_gate(manifest, output_dir=tmp_path / "quality")

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False


def test_load_snapshot_manifest_supports_processed_files_shape(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, processed_files_shape=True)

    loaded = load_snapshot_manifest(manifest)

    assert loaded["snapshot_id"] == "snapshot-a"
    assert "market" in loaded["dataset_paths"]
    assert "trading_calendar" in loaded["dataset_paths"]


def _write_manifest(
    tmp_path: Path,
    *,
    include_market: bool = True,
    include_benchmark: bool = True,
    bad_market: bool = False,
    bad_benchmark: bool = False,
    processed_files_shape: bool = False,
) -> Path:
    data_dir = tmp_path / "snapshot_files"
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "market": data_dir / "market.csv",
        "universe": data_dir / "universe.csv",
        "trading_calendar": data_dir / "trading_calendar.csv",
        "benchmark": data_dir / "benchmark.csv",
        "corporate_actions": data_dir / "corporate_actions.csv",
    }
    if include_market:
        market = _market_frame()
        if bad_market:
            market.loc[0, "close"] = -1
        market.to_csv(paths["market"], index=False)
    _universe_frame().to_csv(paths["universe"], index=False)
    _calendar_frame().to_csv(paths["trading_calendar"], index=False)
    if include_benchmark:
        benchmark = _market_frame().iloc[[0]].copy()
        benchmark["symbol"] = "CSI300"
        if bad_benchmark:
            benchmark.loc[0, "high"] = 1
        benchmark.to_csv(paths["benchmark"], index=False)
    _corporate_actions_frame().to_csv(paths["corporate_actions"], index=False)

    payload = {
        "snapshot_id": "snapshot-a",
        "created_at": "2024-05-20T00:00:00",
        "source": "TEST",
        "revision_id": "v1",
        "notes": "unit test snapshot",
    }
    dataset_paths = {
        key: str(path)
        for key, path in paths.items()
        if path.exists()
    }
    if processed_files_shape:
        payload["processed_files"] = dataset_paths
    else:
        for key, value in dataset_paths.items():
            payload[f"{key}_path"] = value
    manifest = tmp_path / "snapshot_manifest.json"
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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


def _corporate_actions_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "action_type": "CASH_DIVIDEND",
                "ex_date": "2024-05-20",
                "record_date": "2024-05-17",
                "cash_dividend": 0.1,
                "split_ratio": 1.0,
                "rights_issue": False,
                "event_time": "2024-05-20 15:00:00",
                "publish_time": "2024-05-20 16:00:00",
                "ingest_time": "2024-05-20 16:30:00",
                "available_time": "2024-05-20 17:00:00",
                "revision_id": "v1",
                "source": "TEST",
            }
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
