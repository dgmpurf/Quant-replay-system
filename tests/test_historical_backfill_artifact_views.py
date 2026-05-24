import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.historical_backfill import (
    HISTORICAL_BACKFILL_RESULT_COLUMNS,
    HISTORICAL_BACKFILL_TASK_COLUMNS,
)
from quant_replay_system.historical_backfill_health import check_historical_backfill_health
from quant_replay_system.historical_backfill_index import build_historical_backfill_index
from quant_replay_system.historical_backfill_status import run_historical_backfill_status


def test_historical_backfill_index_detects_fake_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    artifact = _write_fake_backfill_artifact(root, "bf_pass")

    result = build_historical_backfill_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["backfill_id"] == "bf_pass"
    assert row["status"] == "PASS"
    assert row["task_count"] == 2
    assert row["pass_count"] == 2
    assert row["fail_count"] == 0
    assert row["symbols"] == "000001,510300"
    assert row["report_path"] == str(artifact / "historical_backfill_report.md")
    assert row["no_live_trading_statement_present"] == True


def test_historical_backfill_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_historical_backfill_index(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "index",
        settings=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root not found" in warning for warning in result.warnings)


def test_historical_backfill_health_pass_for_complete_artifact_set(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_pass")
    index = build_historical_backfill_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))

    result = check_historical_backfill_health(
        index_df=index.index_frame,
        output_dir=tmp_path / "health",
        settings=_settings(tmp_path, root),
    )

    assert result.status == "PASS"
    assert result.checked_artifact_count == 1
    assert result.issue_count == 0


def test_historical_backfill_health_warn_for_expected_dry_run_warnings(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(
        root,
        "bf_warn",
        status="WARN",
        result_statuses=["PASS", "WARN"],
        warnings=["ETF/Sina remains provisional in this reviewed dry-run."],
    )

    result = check_historical_backfill_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "WARN"
    assert "EXPECTED_DRY_RUN_WARNING" in result.health_frame["issue_code"].tolist()


def test_historical_backfill_health_fail_for_missing_metadata(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    artifact = _write_fake_backfill_artifact(root, "bf_missing_metadata")
    (artifact / "metadata.json").unlink()

    result = check_historical_backfill_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_METADATA" in result.health_frame["issue_code"].tolist()


def test_historical_backfill_health_fail_for_missing_report(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    artifact = _write_fake_backfill_artifact(root, "bf_missing_report")
    (artifact / "historical_backfill_report.md").unlink()

    result = check_historical_backfill_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_REPORT" in result.health_frame["issue_code"].tolist()


def test_historical_backfill_status_summarizes_latest_backfill(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_old", created_at="1970-01-01T00:00:00+00:00")
    _write_fake_backfill_artifact(
        root,
        "bf_latest",
        status="WARN",
        result_statuses=["PASS", "WARN"],
        warnings=["Known first-window pre_close caveat."],
        created_at="1970-01-02T00:00:00+00:00",
    )

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert result.status == "WARN"
    assert result.latest_backfill_id == "bf_latest"
    assert result.workflow_stage == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert "Review WARN tasks" in result.next_manual_action


def test_historical_backfill_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_historical_backfill_status(
        root=tmp_path / "missing_root",
        output_dir=tmp_path / "status",
        config=_settings(tmp_path, tmp_path / "missing_root"),
    )

    assert result.status == "WARN"
    assert result.workflow_stage == "NO_BACKFILL_ARTIFACTS"
    assert result.latest_backfill_id == ""


def test_historical_backfill_status_reviewable_next_action_for_warn_dry_run(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(
        root,
        "bf_warn",
        status="WARN",
        result_statuses=["PASS", "WARN"],
        warnings=["ETF/Sina remains provisional."],
    )

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert result.workflow_stage == "BACKFILL_WARNINGS_NEED_REVIEW"
    assert "--accept-cache-write" in result.next_manual_action


def test_cli_historical_backfill_index_works(tmp_path: Path, capsys) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_pass")

    code = cli.main(
        [
            "historical-backfill-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "artifact_count: 1" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_historical_backfill_health_works(tmp_path: Path, capsys) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_pass")

    code = cli.main(
        [
            "historical-backfill-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Health status: PASS" in output.out
    assert "checked_artifact_count: 1" in output.out


def test_cli_historical_backfill_status_works(tmp_path: Path, capsys) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_pass")

    code = cli.main(
        [
            "historical-backfill-status",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "status"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Historical backfill workflow status: PASS" in output.out
    assert "workflow_stage: BACKFILL_CACHE_WRITE_READY" in output.out


def test_historical_backfill_artifact_views_are_local_only(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_fake_backfill_artifact(root, "bf_pass")

    index = build_historical_backfill_index(root=root, output_dir=tmp_path / "index", settings=_settings(tmp_path, root))
    health = check_historical_backfill_health(index_df=index.index_frame, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))
    status = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

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
            "historical_backfill_index": settings.historical_backfill_index.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "historical_backfill" / "index",
                }
            ),
            "historical_backfill_health": settings.historical_backfill_health.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "historical_backfill" / "health",
                    "index_path": tmp_path / "historical_backfill" / "index" / "historical_backfill_index.csv",
                }
            ),
            "historical_backfill_status": settings.historical_backfill_status.model_copy(
                update={
                    "root_dir": root,
                    "output_dir": tmp_path / "historical_backfill" / "status",
                }
            ),
        }
    )


def _write_fake_backfill_artifact(
    root: Path,
    backfill_id: str,
    *,
    status: str = "PASS",
    result_statuses: list[str] | None = None,
    warnings: list[str] | None = None,
    cache_write_occurred: bool = False,
    created_at: str = "1970-01-01T00:00:00+00:00",
) -> Path:
    artifact_dir = root / backfill_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"{backfill_id}_manifest.csv"
    pd.DataFrame(
        [
            {"symbol": "000001", "source": "AKSHARE_OPTIONAL", "dataset_type": "market", "start_date": "2024-01-01", "end_date": "2024-01-10", "enabled": True},
            {"symbol": "510300", "source": "AKSHARE_OPTIONAL", "dataset_type": "market", "start_date": "2024-01-01", "end_date": "2024-01-10", "enabled": True},
        ]
    ).to_csv(manifest_path, index=False)
    result_statuses = result_statuses or ["PASS", "PASS"]
    warnings = warnings or []
    task_rows = [
        _task_row("task_1", 2, "000001", "STOCK"),
        _task_row("task_2", 3, "510300", "ETF"),
    ]
    result_rows = [
        _result_row("task_1", 2, "000001", result_statuses[0]),
        _result_row("task_2", 3, "510300", result_statuses[1]),
    ]
    tasks_path = artifact_dir / "historical_backfill_tasks.csv"
    results_path = artifact_dir / "historical_backfill_results.csv"
    report_path = artifact_dir / "historical_backfill_report.md"
    metadata_path = artifact_dir / "metadata.json"
    pd.DataFrame(task_rows, columns=HISTORICAL_BACKFILL_TASK_COLUMNS).to_csv(tasks_path, index=False)
    pd.DataFrame(result_rows, columns=HISTORICAL_BACKFILL_RESULT_COLUMNS).to_csv(results_path, index=False)
    report_path.write_text(
        "# Historical Backfill Report\n\nNo live trading or broker API was invoked.\n",
        encoding="utf-8",
    )
    counts = pd.Series(result_statuses).value_counts().to_dict()
    metadata = {
        "backfill_id": backfill_id,
        "status": status,
        "manifest_path": str(manifest_path),
        "task_count": len(task_rows),
        "cache_write_occurred": cache_write_occurred,
        "task_result_counts": {key: int(value) for key, value in counts.items()},
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "historical_backfill_report": str(report_path),
            "historical_backfill_tasks": str(tasks_path),
            "historical_backfill_results": str(results_path),
            "metadata": str(metadata_path),
        },
        "warnings": warnings,
        "known_limitations": ["test fixture"],
        "audit_metadata": {"test_fixture": True},
        "created_at": created_at,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return artifact_dir


def _task_row(task_id: str, manifest_row: int, symbol: str, security_type: str) -> dict:
    return {
        "task_id": task_id,
        "manifest_row": manifest_row,
        "symbol": symbol,
        "source": "AKSHARE_OPTIONAL",
        "dataset_type": "market",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "chunk_start_date": "2024-01-01",
        "chunk_end_date": "2024-01-10",
        "enabled": True,
        "security_type": security_type,
        "preferred_upstream": "TENCENT" if security_type == "STOCK" else "SINA",
        "require_fields": "close,volume,amount",
        "reference_source": "BAOSTOCK_OPTIONAL" if security_type == "STOCK" else "",
        "strict_provisional": False,
        "chunk_days": "",
        "raw_input": f"data/raw/fake/{symbol}/raw_data.csv",
        "metadata_path": f"data/raw/fake/{symbol}/metadata.json",
        "notes": "test fixture",
        "no_live_trading": True,
        "no_broker_api": True,
    }


def _result_row(task_id: str, manifest_row: int, symbol: str, status: str) -> dict:
    return {
        "task_id": task_id,
        "manifest_row": manifest_row,
        "symbol": symbol,
        "source": "AKSHARE_OPTIONAL",
        "dataset_type": "market",
        "chunk_start_date": "2024-01-01",
        "chunk_end_date": "2024-01-10",
        "status": status,
        "preflight_status": "WARN_ACCEPT" if status == "WARN" else "ACCEPT",
        "health_status": "",
        "cache_write_occurred": False,
        "raw_data_path": f"data/raw/fake/{symbol}/raw_data.csv",
        "metadata_path": f"data/raw/fake/{symbol}/metadata.json",
        "health_report_path": "",
        "preflight_report_path": "outputs/reports/fake/preflight_report.md",
        "cache_report_path": "",
        "row_count": 10,
        "issue_count": 1 if status == "WARN" else 0,
        "warning_count": 1 if status == "WARN" else 0,
        "error_count": 0,
        "message": "test fixture",
        "no_live_trading": True,
        "no_broker_api": True,
    }
