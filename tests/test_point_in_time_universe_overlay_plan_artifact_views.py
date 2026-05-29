import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_plan import OVERLAY_PLAN_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_plan_health import check_point_in_time_universe_overlay_plan_health
from quant_replay_system.point_in_time_universe_overlay_plan_index import (
    build_point_in_time_universe_overlay_plan_index,
)
from quant_replay_system.point_in_time_universe_overlay_plan_status import (
    run_point_in_time_universe_overlay_plan_status,
)


def test_pit_universe_overlay_plan_index_detects_fake_plan(tmp_path: Path) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001")

    result = build_point_in_time_universe_overlay_plan_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["overlay_plan_id"] == "plan001"
    assert int(row["row_count"]) == 2
    assert int(row["signal_date_count"]) == 1
    assert int(row["symbol_count"]) == 2
    assert int(row["needs_manual_review_count"]) == 2
    assert int(row["survivorship_bias_warning_count"]) == 2
    assert int(row["valid_for_signal_date_count"]) == 0
    assert row["plan_only"] is True


def test_pit_universe_overlay_plan_health_passes_safe_plan_needing_review(tmp_path: Path) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001")

    result = check_point_in_time_universe_overlay_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_pit_universe_overlay_plan_health_fails_if_include_flag_auto_approved_without_review(
    tmp_path: Path,
) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001", row_updates={"include_flag": True})

    result = check_point_in_time_universe_overlay_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_APPROVAL_DETECTED" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_plan_health_fails_if_no_order_placement_false(tmp_path: Path) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(
        root,
        "plan001",
        row_updates={"no_order_placement": False},
        metadata_updates={"no_order_placement": False},
    )

    result = check_point_in_time_universe_overlay_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "ORDER_PLACEMENT_DETECTED" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_plan_health_fails_if_future_derived_warning_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001", row_updates={"survivorship_bias_warning": False})

    result = check_point_in_time_universe_overlay_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MISSING_SURVIVORSHIP_WARNING" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_plan_status_summarizes_latest_plan(tmp_path: Path) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001", created_at="2024-05-19T00:00:00")
    _write_overlay_plan_artifact(root, "plan002", created_at="2024-05-20T00:00:00")

    result = run_point_in_time_universe_overlay_plan_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_overlay_plan_id == "plan002"
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW"
    assert result.health_status == "PASS"
    assert result.row_count == 2
    assert result.needs_manual_review_count == 2
    assert "manual review" in result.next_manual_action.lower()


def test_pit_universe_overlay_plan_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_point_in_time_universe_overlay_plan_status(
        root=tmp_path / "missing",
        output_dir=tmp_path / "status",
    )

    assert result.workflow_stage == "NO_PIT_UNIVERSE_OVERLAY_PLAN"
    assert result.status == "WARN"
    assert result.latest_overlay_plan_id == ""


def test_cli_pit_universe_overlay_plan_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001")

    index_code = cli.main(
        [
            "pit-universe-overlay-plan-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "pit-universe-overlay-plan-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "pit-universe-overlay-plan-status",
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
    assert "workflow_stage: PIT_UNIVERSE_OVERLAY_PLAN_NEEDS_REVIEW" in status_output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in status_output.out


def test_pit_universe_overlay_plan_artifact_views_do_not_enable_execution_or_delivery(tmp_path: Path) -> None:
    root = tmp_path / "pit"
    _write_overlay_plan_artifact(root, "plan001")

    index = build_point_in_time_universe_overlay_plan_index(root=root, output_dir=tmp_path / "index")
    health = check_point_in_time_universe_overlay_plan_health(root=root, output_dir=tmp_path / "health")
    status = run_point_in_time_universe_overlay_plan_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["current_candidates_executed"] is False
    assert index.audit_metadata["snapshot_manifest_built"] is False
    assert health.audit_metadata["cache_mutated"] is False
    assert health.audit_metadata["network_api_called"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False
    assert status.audit_metadata["broker_api_invoked"] is False


def _write_overlay_plan_artifact(
    root: Path,
    overlay_plan_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    row_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / overlay_plan_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    plan_csv = artifact_dir / "point_in_time_universe_overlay_plan.csv"
    template_csv = artifact_dir / "point_in_time_universe_overlay_template.csv"
    report = artifact_dir / "point_in_time_universe_overlay_plan_report.md"
    metadata_path = artifact_dir / "metadata.json"
    rows = [
        _overlay_row(overlay_plan_id, "000001"),
        _overlay_row(overlay_plan_id, "510300"),
    ]
    for row in rows:
        row.update(row_updates or {})
    pd.DataFrame(rows, columns=OVERLAY_PLAN_COLUMNS).to_csv(plan_csv, index=False)
    pd.DataFrame(rows, columns=OVERLAY_PLAN_COLUMNS).to_csv(template_csv, index=False)
    report.write_text(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "overlay_plan_id": overlay_plan_id,
        "created_at": created_at,
        "status": "WARN",
        "row_count": 2,
        "signal_date_count": 1,
        "symbol_count": 2,
        "review_status_counts": {"NEEDS_MANUAL_REVIEW": 2},
        "survivorship_bias_warning_count": 2,
        "valid_for_signal_date_count": 0,
        "requires_manual_review": True,
        "reviewed_execution_required": True,
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
            "overlay_plan_csv": str(plan_csv),
            "overlay_template_csv": str(template_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _overlay_row(overlay_plan_id: str, symbol: str) -> dict:
    return {
        "overlay_plan_id": overlay_plan_id,
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "proposed_as_of_date": "2024-04-02",
        "proposed_available_time": "2024-04-02 08:00:00",
        "base_universe_path": "data/raw/LOCAL_CSV/universe_overlay/base/raw_data.csv",
        "base_universe_as_of_date": "2024-05-20",
        "base_universe_available_time": "2024-05-20 08:00:00",
        "include_flag": "",
        "review_status": "NEEDS_MANUAL_REVIEW",
        "review_reason": "Base universe is later than the signal date; manual point-in-time review is required before inclusion.",
        "source": "LOCAL_TEST",
        "upstream_source": "LOCAL_TEST",
        "survivorship_bias_warning": True,
        "manual_review_required": True,
        "valid_for_signal_date": False,
        "blocker_reason": "Universe as_of_date is later than signal date.",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "plan_only": True,
    }
