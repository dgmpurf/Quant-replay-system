import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_cache_export_health import check_market_cache_export_health
from quant_replay_system.market_cache_export_index import build_market_cache_export_index
from quant_replay_system.market_cache_export_status import run_market_cache_export_status


def test_market_cache_export_index_detects_fake_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    paths = _write_fake_export_artifact(root, export_id="export-pass")

    result = build_market_cache_export_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0].to_dict()
    assert row["export_id"] == "export-pass"
    assert row["status"] == "PASS"
    assert row["exported_market_csv_path"] == str(paths["exported_market_csv"])
    assert int(row["exported_row_count"]) == 2
    assert int(row["duplicate_key_count"]) == 0
    assert row["pipeline_id"] == "pipeline-export-pass"
    assert row["data_pipeline_status"] == "PASS"
    assert row["data_quality_status"] == "PASS"
    assert row["snapshot_quality_status"] == "PASS"
    assert row["symbols"] == "000001"
    assert row["source_upstream_selections"] == "AKSHARE_OPTIONAL/TENCENT"
    assert result.artifact_paths["market_cache_export_index_csv"].exists()


def test_market_cache_export_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_market_cache_export_index(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "index",
        settings=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root not found" in warning for warning in result.warnings)


def test_market_cache_export_health_pass_for_complete_artifact_set(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    _write_fake_export_artifact(root, export_id="export-pass")
    index = build_market_cache_export_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    result = check_market_cache_export_health(
        index_df=index.index_frame,
        output_dir=tmp_path / "health",
        settings=_settings(tmp_path, root),
    )

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0
    assert result.error_count == 0


def test_market_cache_export_health_fails_for_missing_exported_market_csv(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    paths = _write_fake_export_artifact(root, export_id="export-missing-csv")
    paths["exported_market_csv"].unlink()

    result = check_market_cache_export_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_EXPORTED_MARKET_CSV" in set(result.health_frame["issue_code"])


def test_market_cache_export_health_fails_for_duplicate_symbol_trade_date_keys(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    _write_fake_export_artifact(root, export_id="export-duplicate", duplicate_keys=True)

    result = check_market_cache_export_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "DUPLICATE_MARKET_KEYS" in set(result.health_frame["issue_code"])


def test_market_cache_export_health_fails_for_missing_linked_pipeline_report(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    paths = _write_fake_export_artifact(root, export_id="export-missing-link")
    paths["pipeline_report"].unlink()

    result = check_market_cache_export_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_PIPELINE_REPORT" in set(result.health_frame["issue_code"])


def test_market_cache_export_status_summarizes_latest_export(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    _write_fake_export_artifact(root, export_id="export-old", created_at="2024-05-19T00:00:00+00:00")
    _write_fake_export_artifact(root, export_id="export-new", created_at="2024-05-20T00:00:00+00:00")

    result = run_market_cache_export_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert result.status == "PASS"
    assert result.latest_export_id == "export-new"
    assert result.workflow_stage == "SNAPSHOT_READY_FROM_EXPORT"
    assert "current-candidates" in result.next_manual_action
    assert result.artifact_paths["market_cache_export_status_report"].exists()


def test_market_cache_export_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_market_cache_export_status(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "status",
        config=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.status == "WARN"
    assert result.workflow_stage == "NO_CACHE_EXPORT_ARTIFACTS"
    assert result.latest_export_id == ""


def test_cli_market_cache_export_index_health_status_commands(tmp_path: Path, capsys) -> None:
    root = tmp_path / "market_cache_export"
    _write_fake_export_artifact(root, export_id="export-cli")

    index_code = cli.main(
        [
            "market-cache-export-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    index_csv = tmp_path / "index" / "market_cache_export_index.csv"
    assert index_code == 0
    assert "artifact_count: 1" in index_output.out
    assert index_csv.exists()

    health_code = cli.main(
        [
            "market-cache-export-health",
            "--index",
            str(index_csv),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    assert health_code == 0
    assert "Market cache export health status: PASS" in health_output.out

    status_code = cli.main(
        [
            "market-cache-export-status",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "status"),
        ]
    )
    status_output = capsys.readouterr()
    assert status_code == 0
    assert "workflow_stage: SNAPSHOT_READY_FROM_EXPORT" in status_output.out
    assert "No live trading or broker API was invoked." in status_output.out


def test_market_cache_export_artifact_views_are_local_only(tmp_path: Path) -> None:
    root = tmp_path / "market_cache_export"
    _write_fake_export_artifact(root, export_id="export-safe")

    index = build_market_cache_export_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))
    health = check_market_cache_export_health(index_df=index.index_frame, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))
    status = run_market_cache_export_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert index.audit_metadata["live_trading_enabled"] is False
    assert index.audit_metadata["broker_api_invoked"] is False
    assert health.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["live_trading_enabled"] is False
    assert status.audit_metadata["broker_api_invoked"] is False


def _settings(tmp_path: Path, root: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "market_cache_export_index": settings.market_cache_export_index.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export" / "index",
                }
            ),
            "market_cache_export_health": settings.market_cache_export_health.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export" / "health",
                    "index_path": tmp_path / "market_cache_export" / "index" / "market_cache_export_index.csv",
                }
            ),
            "market_cache_export_status": settings.market_cache_export_status.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "market_cache_export" / "status",
                }
            ),
        }
    )


def _write_fake_export_artifact(
    root: Path,
    *,
    export_id: str,
    created_at: str = "2024-05-20T00:00:00+00:00",
    duplicate_keys: bool = False,
) -> dict[str, Path]:
    artifact_dir = root / export_id
    linked_dir = root / "_linked" / export_id
    export_data_dir = root / "_exports" / export_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    linked_dir.mkdir(parents=True, exist_ok=True)
    export_data_dir.mkdir(parents=True, exist_ok=True)

    exported_market_csv = export_data_dir / "market_raw_data.csv"
    frame = _market_frame(duplicate_keys=duplicate_keys)
    frame.to_csv(exported_market_csv, index=False)
    generated_manifest = linked_dir / f"market_cache_export_{export_id}.json"
    generated_manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {"dataset_type": "market", "source": "LOCAL_CSV", "input_path": str(exported_market_csv)}
                ]
            }
        ),
        encoding="utf-8",
    )
    no_live = "No live trading or broker API was invoked."
    pipeline_report = linked_dir / "data_pipeline_report.md"
    data_quality_report = linked_dir / "data_quality_report.md"
    snapshot_report = linked_dir / "snapshot_quality_gate_report.md"
    snapshot_manifest = linked_dir / "snapshot_manifest.json"
    pipeline_report.write_text(no_live, encoding="utf-8")
    data_quality_report.write_text(no_live, encoding="utf-8")
    snapshot_report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    snapshot_manifest.write_text("{}", encoding="utf-8")

    report_path = artifact_dir / "market_cache_export_report.md"
    rows_path = artifact_dir / "market_cache_export_rows.csv"
    issues_path = artifact_dir / "market_cache_export_issues.csv"
    metadata_path = artifact_dir / "metadata.json"
    report_path.write_text("# Market Cache Export\n\nNo live trading or broker API was invoked.\n", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "manifest_row": 2,
                "symbol": "000001",
                "source": "AKSHARE_OPTIONAL",
                "upstream_source": "TENCENT",
                "status": "PASS",
                "row_count": len(frame),
                "min_trade_date": "2024-01-02",
                "max_trade_date": "2024-01-03",
            }
        ]
    ).to_csv(rows_path, index=False)
    pd.DataFrame(columns=["category", "severity", "message"]).to_csv(issues_path, index=False)
    metadata = {
        "export_id": export_id,
        "status": "PASS",
        "created_at": created_at,
        "manifest_path": str(root / f"{export_id}_manifest.csv"),
        "exported_market_csv_path": str(exported_market_csv),
        "generated_pipeline_manifest_path": str(generated_manifest),
        "row_count": len(frame),
        "issue_count": 0,
        "duplicate_key_count": int(frame.duplicated(["symbol", "trade_date"]).sum()),
        "export_rows": [
            {
                "symbol": "000001",
                "source": "AKSHARE_OPTIONAL",
                "upstream_source": "TENCENT",
                "min_trade_date": "2024-01-02",
                "max_trade_date": "2024-01-03",
                "row_count": len(frame),
                "status": "PASS",
            }
        ],
        "warnings": [],
        "pipeline_id": f"pipeline-{export_id}",
        "data_pipeline_status": "PASS",
        "data_pipeline_report_path": str(pipeline_report),
        "data_quality_status": "PASS",
        "data_quality_report_path": str(data_quality_report),
        "snapshot_manifest_path": str(snapshot_manifest),
        "snapshot_quality_status": "PASS",
        "snapshot_quality_report_path": str(snapshot_report),
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "market_cache_export_report": str(report_path),
            "market_cache_export_rows": str(rows_path),
            "market_cache_export_issues": str(issues_path),
            "metadata": str(metadata_path),
            "exported_market_csv": str(exported_market_csv),
            "generated_pipeline_manifest": str(generated_manifest),
        },
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "cache_mutated": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": no_live,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "artifact_dir": artifact_dir,
        "metadata": metadata_path,
        "report": report_path,
        "rows": rows_path,
        "issues": issues_path,
        "exported_market_csv": exported_market_csv,
        "generated_manifest": generated_manifest,
        "pipeline_report": pipeline_report,
        "data_quality_report": data_quality_report,
        "snapshot_report": snapshot_report,
    }


def _market_frame(*, duplicate_keys: bool) -> pd.DataFrame:
    rows = [_market_row("2024-01-02"), _market_row("2024-01-03")]
    if duplicate_keys:
        rows.append(_market_row("2024-01-02"))
    return pd.DataFrame(rows)


def _market_row(trade_date: str) -> dict:
    return {
        "symbol": "000001",
        "trade_date": trade_date,
        "open": 10.0,
        "high": 10.5,
        "low": 9.8,
        "close": 10.2,
        "volume": 1000,
        "amount": 10200,
        "pre_close": 10.0,
        "adj_factor": 1.0,
        "is_suspended": False,
        "limit_up": "",
        "limit_down": "",
        "event_time": f"{trade_date} 15:00:00",
        "publish_time": f"{trade_date} 15:30:00",
        "ingest_time": f"{trade_date} 16:00:00",
        "available_time": f"{trade_date} 15:30:00",
        "revision_id": "v1",
        "source": "AKSHARE_OPTIONAL",
        "upstream_source": "TENCENT",
    }
