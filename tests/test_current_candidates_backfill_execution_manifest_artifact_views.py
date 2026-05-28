import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.current_candidates_backfill_execution_manifest import MANIFEST_COLUMNS
from quant_replay_system.current_candidates_backfill_execution_manifest_health import (
    check_current_candidates_backfill_execution_manifest_health,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_index import (
    build_current_candidates_backfill_execution_manifest_index,
)
from quant_replay_system.current_candidates_backfill_execution_manifest_status import (
    run_current_candidates_backfill_execution_manifest_status,
)


def test_execution_manifest_index_detects_fake_manifests(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(root, "manifest001")

    result = build_current_candidates_backfill_execution_manifest_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["execution_manifest_id"] == "manifest001"
    assert row["plan_id"] == "plan001"
    assert int(row["row_count"]) == 2
    assert int(row["ready_count"]) == 1
    assert int(row["blocked_universe_as_of_count"]) == 1
    assert row["no_order_placement"] is True


def test_execution_manifest_health_passes_valid_manifest(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(root, "manifest001")

    result = check_current_candidates_backfill_execution_manifest_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_execution_manifest_health_warns_for_blocked_row_without_reason(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(
        root,
        "manifest001",
        row_updates={"blocker_reason": ""},
        blocked_readiness_status="BLOCKED_UNIVERSE_AS_OF",
    )

    result = check_current_candidates_backfill_execution_manifest_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert "BLOCKED_WITHOUT_REASON" in set(result.health_frame["issue_code"])


def test_execution_manifest_health_fails_if_no_order_placement_false(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(
        root,
        "manifest001",
        row_updates={"no_order_placement": False},
        metadata_updates={"no_order_placement": False},
    )

    result = check_current_candidates_backfill_execution_manifest_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "ORDER_PLACEMENT_DETECTED" in set(result.health_frame["issue_code"])


def test_execution_manifest_status_summarizes_latest_manifest(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(root, "manifest001", created_at="2024-05-19T00:00:00")
    _write_manifest_artifact(root, "manifest002", created_at="2024-05-20T00:00:00")

    result = run_current_candidates_backfill_execution_manifest_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_execution_manifest_id == "manifest002"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED"
    assert result.health_status == "PASS"
    assert result.row_count == 2
    assert result.blocked_count == 1
    assert "blocked" in result.next_manual_action.lower()


def test_execution_manifest_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_current_candidates_backfill_execution_manifest_status(
        root=tmp_path / "missing",
        output_dir=tmp_path / "status",
    )

    assert result.workflow_stage == "NO_CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST"
    assert result.status == "WARN"
    assert result.latest_execution_manifest_id == ""


def test_cli_current_candidates_backfill_execution_manifest_index_health_status_work(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(root, "manifest001")

    index_code = cli.main(
        [
            "current-candidates-backfill-execution-manifest-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "current-candidates-backfill-execution-manifest-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "current-candidates-backfill-execution-manifest-status",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "status"),
        ]
    )
    status_output = capsys.readouterr()

    assert index_code == 0
    assert "artifact_count: 1" in index_output.out
    assert health_code == 0
    assert "Health status: PASS" in health_output.out
    assert status_code == 0
    assert "workflow_stage: CURRENT_CANDIDATES_BACKFILL_EXECUTION_MANIFEST_BLOCKED" in status_output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked." in status_output.out


def test_execution_manifest_artifact_views_do_not_enable_execution_or_delivery(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_execution_manifest"
    _write_manifest_artifact(root, "manifest001")

    index = build_current_candidates_backfill_execution_manifest_index(root=root, output_dir=tmp_path / "index")
    health = check_current_candidates_backfill_execution_manifest_health(root=root, output_dir=tmp_path / "health")
    status = run_current_candidates_backfill_execution_manifest_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["current_candidates_executed"] is False
    assert index.audit_metadata["snapshot_manifest_built"] is False
    assert health.audit_metadata["cache_mutated"] is False
    assert health.audit_metadata["network_api_called"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False
    assert status.audit_metadata["broker_api_invoked"] is False


def _write_manifest_artifact(
    root: Path,
    execution_manifest_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    blocked_readiness_status: str = "BLOCKED_UNIVERSE_AS_OF",
    row_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / execution_manifest_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_csv = artifact_dir / "current_candidates_backfill_execution_manifest.csv"
    report = artifact_dir / "current_candidates_backfill_execution_manifest_report.md"
    metadata_path = artifact_dir / "metadata.json"
    ready_row = _manifest_row(execution_manifest_id, readiness_status="READY_FOR_REVIEW")
    blocked_row = _manifest_row(
        execution_manifest_id,
        signal_date="2024-04-09",
        readiness_status=blocked_readiness_status,
        blocker_reason="Universe as_of_date is later than signal date.",
    )
    blocked_row.update(row_updates or {})
    pd.DataFrame([ready_row, blocked_row], columns=MANIFEST_COLUMNS).to_csv(manifest_csv, index=False)
    report.write_text(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, or network/API call was invoked.",
        encoding="utf-8",
    )
    readiness_counts = {
        "READY_FOR_REVIEW": 1,
        blocked_readiness_status: 1,
    }
    metadata = {
        "execution_manifest_id": execution_manifest_id,
        "created_at": created_at,
        "status": "WARN",
        "plan": "outputs/reports/current_candidates_backfill_plan/plan001/current_candidates_backfill_plan.csv",
        "row_count": 2,
        "ready_count": 1,
        "blocked_count": 1,
        "readiness_counts": readiness_counts,
        "reviewed_execution_required": True,
        "requires_manual_review": True,
        "plan_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
        "snapshot_manifest_built": False,
        "snapshot_manifests_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "order_placement_enabled": False,
        "approved_for_paper_applied": False,
        "output_files": {
            "execution_manifest_csv": str(manifest_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _manifest_row(
    execution_manifest_id: str,
    *,
    signal_date: str = "2024-04-02",
    readiness_status: str,
    blocker_reason: str = "",
) -> dict:
    return {
        "execution_manifest_id": execution_manifest_id,
        "plan_id": "plan001",
        "signal_date": signal_date,
        "universe": "etf_core",
        "selection_profile": "demo",
        "plan_status": "READY",
        "warmup_available": True,
        "candidate_generation_feasible": True,
        "forward_1d_available": True,
        "forward_3d_available": True,
        "forward_5d_available": True,
        "forward_10d_available": True,
        "required_snapshot_manifest_path": "outputs/reports/data_pipeline/snapshot/snapshot_manifest.json",
        "snapshot_manifest_found": True,
        "snapshot_quality_status": "PASS",
        "market_dataset_path": "data/processed/market/snapshot/raw_data_cleaned.csv",
        "universe_dataset_path": "data/processed/universe/snapshot/raw_data_cleaned.csv",
        "universe_as_of_date": "2024-04-01" if readiness_status == "READY_FOR_REVIEW" else "2024-05-20",
        "universe_valid_for_signal_date": readiness_status == "READY_FOR_REVIEW",
        "trading_calendar_path": "data/processed/trading_calendar/snapshot/raw_data_cleaned.csv",
        "source_policy": "reviewed_local_v0",
        "recommended_source_filter": "AKSHARE_OPTIONAL",
        "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
        "readiness_status": readiness_status,
        "blocker_reason": blocker_reason,
        "reviewed_execution_required": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "plan_only": True,
    }
