import json
import os
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


def test_historical_backfill_status_uses_artifact_update_time_when_created_at_ties(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    old = _write_fake_backfill_artifact(root, "zzz_old", created_at="1970-01-01T00:00:00+00:00")
    latest = _write_fake_backfill_artifact(
        root,
        "aaa_latest",
        cache_write_occurred=True,
        created_at="1970-01-01T00:00:00+00:00",
    )
    os.utime(old / "metadata.json", (1000, 1000))
    os.utime(latest / "metadata.json", (2000, 2000))

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))

    assert result.latest_backfill_id == "aaa_latest"
    assert result.workflow_stage == "BACKFILL_COMPLETED"


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


def test_historical_backfill_status_classifies_partial_cache_write_rejections(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_partial_backfill_artifact(root, "bf_partial")

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "WARN"
    assert result.workflow_stage == "BACKFILL_PARTIAL_WITH_REJECTIONS"
    assert "Review rejected rows" in result.next_manual_action
    assert summary["accepted_task_count"] == 1
    assert summary["rejected_task_count"] == 1
    assert summary["preflight_rejected_count"] == 1
    assert summary["comparison_failed_count"] == 1
    assert summary["cache_write_partial"] is True
    assert summary["rejected_symbols"] == "300750"
    assert summary["rejected_sources"] == "BAOSTOCK_OPTIONAL"
    assert "COMPARISON_FAIL" in summary["rejected_issue_categories"]


def test_historical_backfill_status_keeps_all_rejected_rows_blocking(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_all_rejected_backfill_artifact(root, "bf_all_rejected")

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.status == "FAIL"
    assert result.workflow_stage == "BACKFILL_FAILED"
    assert "failed backfill" in result.next_manual_action
    assert summary["accepted_task_count"] == 0
    assert summary["rejected_task_count"] == 2
    assert summary["cache_write_partial"] is False


def test_historical_backfill_status_metadata_preserves_rejected_rows(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    _write_partial_backfill_artifact(root, "bf_partial_metadata")

    result = run_historical_backfill_status(root=root, output_dir=tmp_path / "status", config=_settings(tmp_path, root))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["status"] == "WARN"
    assert metadata["workflow_stage"] == "BACKFILL_PARTIAL_WITH_REJECTIONS"
    assert metadata["accepted_task_count"] == 1
    assert metadata["rejected_task_count"] == 1
    assert metadata["preflight_rejected_count"] == 1
    assert metadata["comparison_failed_count"] == 1
    assert metadata["cache_write_partial"] is True
    assert metadata["rejected_symbols"] == "300750"


def test_historical_backfill_health_still_surfaces_partial_artifact_issues(tmp_path: Path) -> None:
    root = tmp_path / "historical_backfill"
    artifact = _write_partial_backfill_artifact(root, "bf_partial_missing_report")
    (artifact / "historical_backfill_report.md").unlink()

    result = check_historical_backfill_health(root=root, output_dir=tmp_path / "health", settings=_settings(tmp_path, root))

    assert result.status == "FAIL"
    assert "MISSING_REPORT" in result.health_frame["issue_code"].tolist()


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
    assert "rejected_task_count: 0" in output.out


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


def _write_partial_backfill_artifact(root: Path, backfill_id: str) -> Path:
    artifact = _write_fake_backfill_artifact(
        root,
        backfill_id,
        status="FAIL",
        result_statuses=["WARN", "BLOCKED_PREFLIGHT_REJECT"],
        cache_write_occurred=True,
        warnings=["One source row was blocked by preflight comparison."],
    )
    preflight_report = _write_fake_preflight_issue(artifact, "task_2", "300750")
    rows = [
        _result_row(
            "task_1",
            2,
            "000002",
            "WARN",
            cache_write_occurred=True,
            preflight_status="WARN_ACCEPT",
            message="accepted with reviewable warning",
        ),
        _result_row(
            "task_2",
            3,
            "300750",
            "BLOCKED_PREFLIGHT_REJECT",
            source="BAOSTOCK_OPTIONAL",
            preflight_status="REJECT",
            error_count=1,
            message="COMPARISON_FAIL rejected before cache ingest",
            preflight_report_path=str(preflight_report),
        ),
    ]
    pd.DataFrame(rows, columns=HISTORICAL_BACKFILL_RESULT_COLUMNS).to_csv(
        artifact / "historical_backfill_results.csv",
        index=False,
    )
    metadata_path = artifact / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["task_result_counts"] = {"WARN": 1, "BLOCKED_PREFLIGHT_REJECT": 1}
    metadata["task_count"] = 2
    metadata["cache_write_occurred"] = True
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return artifact


def _write_all_rejected_backfill_artifact(root: Path, backfill_id: str) -> Path:
    artifact = _write_fake_backfill_artifact(
        root,
        backfill_id,
        status="FAIL",
        result_statuses=["BLOCKED_PREFLIGHT_REJECT", "BLOCKED_PREFLIGHT_REJECT"],
    )
    first_preflight = _write_fake_preflight_issue(artifact, "task_1", "300750")
    second_preflight = _write_fake_preflight_issue(artifact, "task_2", "688981")
    rows = [
        _result_row(
            "task_1",
            2,
            "300750",
            "BLOCKED_PREFLIGHT_REJECT",
            source="BAOSTOCK_OPTIONAL",
            preflight_status="REJECT",
            error_count=1,
            message="COMPARISON_FAIL rejected before cache ingest",
            preflight_report_path=str(first_preflight),
        ),
        _result_row(
            "task_2",
            3,
            "688981",
            "BLOCKED_PREFLIGHT_REJECT",
            source="BAOSTOCK_OPTIONAL",
            preflight_status="REJECT",
            error_count=1,
            message="COMPARISON_FAIL rejected before cache ingest",
            preflight_report_path=str(second_preflight),
        ),
    ]
    pd.DataFrame(rows, columns=HISTORICAL_BACKFILL_RESULT_COLUMNS).to_csv(
        artifact / "historical_backfill_results.csv",
        index=False,
    )
    metadata_path = artifact / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["task_result_counts"] = {"BLOCKED_PREFLIGHT_REJECT": 2}
    metadata["task_count"] = 2
    metadata["cache_write_occurred"] = False
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return artifact


def _write_fake_preflight_issue(artifact: Path, task_id: str, symbol: str) -> Path:
    preflight_dir = artifact / f"preflight_{task_id}"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    report_path = preflight_dir / "market_cache_preflight_report.md"
    report_path.write_text("No live trading or broker API was invoked.", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "category": "COMPARISON_FAIL",
                "severity": "ERROR",
                "field": "close",
                "symbol": symbol,
                "trade_date": "2024-01-02",
                "message": "comparison failed",
                "decision_impact": "Reject cache ingest for this source row.",
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    ).to_csv(preflight_dir / "market_cache_preflight_issues.csv", index=False)
    return report_path


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


def _result_row(
    task_id: str,
    manifest_row: int,
    symbol: str,
    status: str,
    *,
    source: str = "AKSHARE_OPTIONAL",
    cache_write_occurred: bool = False,
    preflight_status: str | None = None,
    error_count: int | None = None,
    message: str = "test fixture",
    preflight_report_path: str = "outputs/reports/fake/preflight_report.md",
) -> dict:
    return {
        "task_id": task_id,
        "manifest_row": manifest_row,
        "symbol": symbol,
        "source": source,
        "dataset_type": "market",
        "chunk_start_date": "2024-01-01",
        "chunk_end_date": "2024-01-10",
        "status": status,
        "preflight_status": preflight_status or ("WARN_ACCEPT" if status == "WARN" else "ACCEPT"),
        "health_status": "",
        "cache_write_occurred": cache_write_occurred,
        "raw_data_path": f"data/raw/fake/{symbol}/raw_data.csv",
        "metadata_path": f"data/raw/fake/{symbol}/metadata.json",
        "health_report_path": "",
        "preflight_report_path": preflight_report_path,
        "cache_report_path": "",
        "row_count": 10,
        "issue_count": 1 if status == "WARN" else 0,
        "warning_count": 1 if status == "WARN" else 0,
        "error_count": 0 if error_count is None else error_count,
        "message": message,
        "no_live_trading": True,
        "no_broker_api": True,
    }
