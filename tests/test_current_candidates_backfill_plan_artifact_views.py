import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.current_candidates_backfill_plan_health import check_current_candidates_backfill_plan_health
from quant_replay_system.current_candidates_backfill_plan_index import build_current_candidates_backfill_plan_index
from quant_replay_system.current_candidates_backfill_plan_status import run_current_candidates_backfill_plan_status


def test_current_candidates_backfill_plan_index_detects_fake_plan_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001")

    result = build_current_candidates_backfill_plan_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["plan_id"] == "plan001"
    assert int(row["selected_date_count"]) == 1
    assert int(row["warmup_feasible_count"]) == 1
    assert int(row["forward_10d_available_count"]) == 1
    assert row["source_policy"] == "reviewed_local_v0"


def test_current_candidates_backfill_plan_health_passes_safe_plan(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001")

    result = check_current_candidates_backfill_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_current_candidates_backfill_plan_health_fails_for_warmup_infeasible_selected_row(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001", row_updates={"warmup_available": False, "candidate_generation_feasible": False})

    result = check_current_candidates_backfill_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "WARMUP_INFEASIBLE_SELECTED" in set(result.health_frame["issue_code"])


def test_current_candidates_backfill_plan_health_fails_for_forward_infeasible_selected_row(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001", row_updates={"forward_10d_available": False, "candidate_generation_feasible": False})

    result = check_current_candidates_backfill_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "FORWARD_HORIZON_INFEASIBLE_SELECTED" in set(result.health_frame["issue_code"])


def test_current_candidates_backfill_plan_status_summarizes_latest_plan(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001", created_at="2024-05-19T00:00:00")
    _write_plan_artifact(root, "plan002", created_at="2024-05-20T00:00:00")

    result = run_current_candidates_backfill_plan_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_plan_id == "plan002"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert result.health_status == "PASS"
    assert result.selected_date_count == 1
    assert "Review the backfill plan" in result.next_manual_action


def test_current_candidates_backfill_plan_index_keeps_legacy_pre_warmup_artifacts_visible(
    tmp_path: Path,
) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_legacy_pre_warmup_plan_artifact(root, "legacy001", created_at="2024-05-19T00:00:00")
    _write_plan_artifact(root, "plan002", created_at="2024-05-20T00:00:00")

    result = build_current_candidates_backfill_plan_index(root=root, output_dir=tmp_path / "index")
    legacy_row = result.index_frame.loc[result.index_frame["plan_id"] == "legacy001"].iloc[0]
    active_row = result.index_frame.loc[result.index_frame["plan_id"] == "plan002"].iloc[0]

    assert result.artifact_count == 2
    assert legacy_row["warmup_aware"] is False
    assert active_row["warmup_aware"] is True


def test_current_candidates_backfill_plan_health_classifies_legacy_missing_warmup_separately(
    tmp_path: Path,
) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_legacy_pre_warmup_plan_artifact(root, "legacy001", created_at="2024-05-19T00:00:00")
    _write_plan_artifact(root, "plan002", created_at="2024-05-20T00:00:00")

    result = check_current_candidates_backfill_plan_health(root=root, output_dir=tmp_path / "health")
    summary = result.summary_frame.iloc[0].to_dict()
    issue = result.health_frame.loc[result.health_frame["plan_id"] == "legacy001"].iloc[0]

    assert result.status == "WARN"
    assert summary["latest_plan_id"] == "plan002"
    assert summary["latest_plan_is_warmup_aware"] is True
    assert summary["active_plan_issue_count"] == 0
    assert summary["active_plan_error_count"] == 0
    assert summary["legacy_plan_count"] == 1
    assert summary["legacy_missing_warmup_count"] == 1
    assert summary["stale_plan_warning_count"] == 1
    assert issue["issue_scope"] == "LEGACY_PLAN"
    assert issue["issue_code"] == "STALE_OR_PARTIAL_PLAN"


def test_current_candidates_backfill_plan_status_is_ready_despite_older_legacy_plan(
    tmp_path: Path,
) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_legacy_pre_warmup_plan_artifact(root, "legacy001", created_at="2024-05-19T00:00:00")
    _write_plan_artifact(root, "plan002", created_at="2024-05-20T00:00:00")

    result = run_current_candidates_backfill_plan_status(root=root, output_dir=tmp_path / "status")
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.latest_plan_id == "plan002"
    assert result.status == "PASS"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_READY"
    assert result.health_status == "PASS"
    assert summary["legacy_plan_count"] == 1
    assert summary["legacy_missing_warmup_count"] == 1
    assert summary["active_plan_issue_count"] == 0
    assert "Review the backfill plan" in result.next_manual_action


def test_current_candidates_backfill_plan_status_warns_for_active_warmup_plan_issue(
    tmp_path: Path,
) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_legacy_pre_warmup_plan_artifact(root, "legacy001", created_at="2024-05-19T00:00:00")
    _write_plan_artifact(
        root,
        "plan002",
        created_at="2024-05-20T00:00:00",
        row_updates={"warmup_available": False, "candidate_generation_feasible": False},
    )

    result = run_current_candidates_backfill_plan_status(root=root, output_dir=tmp_path / "status")
    summary = result.summary_frame.iloc[0].to_dict()

    assert result.latest_plan_id == "plan002"
    assert result.status == "FAIL"
    assert result.workflow_stage == "CURRENT_CANDIDATES_BACKFILL_PLAN_FAILED"
    assert result.health_status == "FAIL"
    assert summary["active_plan_issue_count"] >= 1
    assert summary["active_plan_error_count"] >= 1


def test_cli_current_candidates_backfill_plan_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001")

    index_code = cli.main(
        [
            "current-candidates-backfill-plan-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "current-candidates-backfill-plan-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "current-candidates-backfill-plan-status",
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
    assert "workflow_stage: CURRENT_CANDIDATES_BACKFILL_PLAN_READY" in status_output.out
    assert "No live trading, broker API, order placement, message delivery, or network/API call was invoked." in status_output.out


def test_current_candidates_backfill_plan_artifact_views_do_not_enable_execution_or_delivery(tmp_path: Path) -> None:
    root = tmp_path / "current_candidates_backfill_plan"
    _write_plan_artifact(root, "plan001")

    index = build_current_candidates_backfill_plan_index(root=root, output_dir=tmp_path / "index")
    health = check_current_candidates_backfill_plan_health(root=root, output_dir=tmp_path / "health")
    status = run_current_candidates_backfill_plan_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["current_candidates_executed"] is False
    assert health.audit_metadata["cache_mutated"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False


def _write_plan_artifact(
    root: Path,
    plan_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    row_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / plan_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    row = _safe_plan_row(plan_id)
    row.update(row_updates or {})
    plan_csv = artifact_dir / "current_candidates_backfill_plan.csv"
    report = artifact_dir / "current_candidates_backfill_plan_report.md"
    metadata_path = artifact_dir / "metadata.json"
    pd.DataFrame([row]).to_csv(plan_csv, index=False)
    report.write_text(
        "No live trading, broker API, order placement, message delivery, or network/API call was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "plan_id": plan_id,
        "created_at": created_at,
        "status": "PASS",
        "universe": "etf_core",
        "selection_profile": "demo",
        "selected_date_count": 1,
        "first_signal_date": "2024-04-02",
        "last_signal_date": "2024-04-02",
        "cache_start_date_in_scope": "2024-01-02",
        "cache_end_date_in_scope": "2024-05-20",
        "warmup_trading_days": 60,
        "warmup_feasibility_counts": {"warmup_available": 1, "candidate_generation_feasible": 1},
        "horizon_feasibility_counts": {
            "forward_1d_available": 1,
            "forward_3d_available": 1,
            "forward_5d_available": 1,
            "forward_10d_available": 1,
        },
        "horizons": [1, 3, 5, 10],
        "source_policy": "reviewed_local_v0",
        "recommended_source_filter": "AKSHARE_OPTIONAL",
        "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
        "plan_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
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
        "auto_order_allowed": False,
        "approved_for_paper_applied": False,
        "output_files": {
            "plan_csv": str(plan_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _write_legacy_pre_warmup_plan_artifact(
    root: Path,
    plan_id: str,
    *,
    created_at: str = "2024-05-19T00:00:00",
) -> None:
    artifact_dir = root / plan_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    row = _safe_plan_row(plan_id)
    for column in [
        "warmup_trading_days",
        "warmup_available",
        "earliest_required_warmup_date",
        "first_available_market_date",
        "warmup_start_date",
        "warmup_reason",
        "candidate_generation_feasible",
        "candidate_generation_blocker",
    ]:
        row.pop(column, None)
    plan_csv = artifact_dir / "current_candidates_backfill_plan.csv"
    report = artifact_dir / "current_candidates_backfill_plan_report.md"
    metadata_path = artifact_dir / "metadata.json"
    pd.DataFrame([row]).to_csv(plan_csv, index=False)
    report.write_text(
        "Legacy plan-only artifact. No live trading, broker API, order placement, message delivery, or network/API call was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "plan_id": plan_id,
        "created_at": created_at,
        "status": "PASS",
        "universe": "etf_core",
        "selection_profile": "demo",
        "selected_date_count": 1,
        "first_signal_date": "2024-01-02",
        "last_signal_date": "2024-01-02",
        "cache_start_date_in_scope": "2024-01-02",
        "cache_end_date_in_scope": "2024-05-20",
        "horizon_feasibility_counts": {
            "forward_1d_available": 1,
            "forward_3d_available": 1,
            "forward_5d_available": 1,
            "forward_10d_available": 1,
        },
        "horizons": [1, 3, 5, 10],
        "source_policy": "reviewed_local_v0",
        "recommended_source_filter": "AKSHARE_OPTIONAL",
        "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
        "plan_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
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
        "auto_order_allowed": False,
        "approved_for_paper_applied": False,
        "output_files": {
            "plan_csv": str(plan_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _safe_plan_row(plan_id: str) -> dict:
    return {
        "plan_id": plan_id,
        "signal_date": "2024-04-02",
        "universe": "etf_core",
        "selection_profile": "demo",
        "eligible_symbol_count": 9,
        "total_symbol_count": 9,
        "min_required_symbol_count": 4,
        "max_forward_horizon": 10,
        "warmup_trading_days": 60,
        "warmup_available": True,
        "earliest_required_warmup_date": "2024-01-02",
        "first_available_market_date": "2024-01-02",
        "warmup_start_date": "2024-01-02",
        "warmup_reason": "Warmup window has 60 trading-day coverage through signal date.",
        "forward_1d_available": True,
        "forward_3d_available": True,
        "forward_5d_available": True,
        "forward_10d_available": True,
        "latest_required_forward_date": "2024-04-18",
        "cache_start_date": "2024-01-02",
        "cache_end_date": "2024-05-20",
        "source_policy": "reviewed_local_v0",
        "recommended_source_filter": "AKSHARE_OPTIONAL",
        "recommended_upstream_filter": "TENCENT_FOR_STOCKS;SINA_FOR_ETFS",
        "status": "READY",
        "reason": "Plan row has required warmup, forward horizons, and symbol coverage.",
        "candidate_generation_feasible": True,
        "candidate_generation_blocker": "",
        "symbols": "000001;510300",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
    }
