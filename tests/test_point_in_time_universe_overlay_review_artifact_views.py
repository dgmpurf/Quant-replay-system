import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_review import REVIEW_OUTPUT_COLUMNS, REVIEW_UPDATE_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_review_health import check_pit_universe_overlay_review_health
from quant_replay_system.point_in_time_universe_overlay_review_index import build_pit_universe_overlay_review_index
from quant_replay_system.point_in_time_universe_overlay_review_status import run_pit_universe_overlay_review_status


def test_pit_universe_overlay_review_index_detects_fake_review_artifact(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001")

    result = build_pit_universe_overlay_review_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["review_id"] == "review001"
    assert row["overlay_plan_id"] == "overlay001"
    assert int(row["row_count"]) == 2
    assert int(row["approved_count"]) == 1
    assert int(row["needs_more_evidence_count"]) == 1
    assert int(row["valid_for_signal_date_count"]) == 1
    assert int(row["unresolved_survivorship_warning_count"]) == 1
    assert int(row["evidence_missing_count"]) == 0
    assert row["review_only"] is True


def test_pit_universe_overlay_review_health_passes_valid_approved_row_with_evidence(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001")

    result = check_pit_universe_overlay_review_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_pit_universe_overlay_review_health_fails_for_approved_row_missing_evidence(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001", approved_updates={"evidence_source": "", "evidence_path": ""})

    result = check_pit_universe_overlay_review_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "APPROVED_ROW_MISSING_EVIDENCE" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_review_health_fails_for_unresolved_survivorship_warning(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001", approved_updates={"survivorship_bias_resolved": False})

    result = check_pit_universe_overlay_review_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "APPROVED_ROW_UNRESOLVED_SURVIVORSHIP_WARNING" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_review_health_fails_if_no_order_placement_false(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(
        root,
        "review001",
        approved_updates={"no_order_placement": False},
        metadata_updates={"no_order_placement": False},
    )

    result = check_pit_universe_overlay_review_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "ORDER_PLACEMENT_DETECTED" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_review_status_summarizes_latest_review(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001", created_at="2024-05-28T00:00:00")
    _write_review_artifact(root, "review002", created_at="2024-05-29T00:00:00", all_approved=True)

    result = run_pit_universe_overlay_review_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_review_id == "review002"
    assert result.workflow_stage == "PIT_UNIVERSE_OVERLAY_REVIEW_ALL_APPROVED"
    assert result.health_status == "PASS"
    assert result.approved_count == 2
    assert result.valid_for_signal_date_count == 2
    assert "snapshot preparation" in result.next_manual_action


def test_cli_pit_universe_overlay_review_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001")

    index_code = cli.main(
        [
            "pit-universe-overlay-review-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "pit-universe-overlay-review-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "pit-universe-overlay-review-status",
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
    assert "workflow_stage: PIT_UNIVERSE_OVERLAY_REVIEW_HAS_APPROVED_ROWS" in status_output.out
    assert "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in status_output.out


def test_pit_universe_overlay_review_artifact_views_do_not_enable_execution_or_delivery(tmp_path: Path) -> None:
    root = tmp_path / "review"
    _write_review_artifact(root, "review001")

    index = build_pit_universe_overlay_review_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_universe_overlay_review_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_universe_overlay_review_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["current_candidates_executed"] is False
    assert health.audit_metadata["snapshot_manifest_built"] is False
    assert status.audit_metadata["forward_returns_computed"] is False
    assert status.audit_metadata["cache_mutated"] is False
    assert status.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_sent"] is False


def _write_review_artifact(
    root: Path,
    review_id: str,
    *,
    created_at: str = "2024-05-29T00:00:00",
    all_approved: bool = False,
    approved_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / review_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    reviewed_csv = artifact_dir / "reviewed_pit_universe_overlay.csv"
    template_csv = artifact_dir / "pit_universe_overlay_review_template.csv"
    report = artifact_dir / "pit_universe_overlay_review_report.md"
    metadata_path = artifact_dir / "metadata.json"
    rows = [_approved_row(review_id, "000001"), _needs_more_evidence_row(review_id, "510300")]
    if all_approved:
        rows = [_approved_row(review_id, "000001"), _approved_row(review_id, "510300")]
    rows[0].update(approved_updates or {})
    pd.DataFrame(rows, columns=REVIEW_OUTPUT_COLUMNS).to_csv(reviewed_csv, index=False)
    pd.DataFrame([_template_row("000001"), _template_row("510300")], columns=REVIEW_UPDATE_COLUMNS).to_csv(
        template_csv,
        index=False,
    )
    report.write_text(
        "No current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM API, or external API was invoked.",
        encoding="utf-8",
    )
    approved_count = sum(1 for row in rows if row["review_status"] == "APPROVED_FOR_PIT_UNIVERSE")
    needs_more_evidence_count = sum(1 for row in rows if row["review_status"] == "NEEDS_MORE_EVIDENCE")
    valid_count = sum(1 for row in rows if row["valid_for_signal_date"] is True)
    unresolved_count = sum(
        1
        for row in rows
        if row["survivorship_bias_warning"] is True and row["survivorship_bias_resolved"] is not True
    )
    metadata = {
        "review_id": review_id,
        "overlay_plan_id": "overlay001",
        "created_at": created_at,
        "status": "PASS" if approved_count else "WARN",
        "row_count": len(rows),
        "approved_count": approved_count,
        "rejected_count": 0,
        "needs_more_evidence_count": needs_more_evidence_count,
        "needs_manual_review_count": 0,
        "valid_for_signal_date_count": valid_count,
        "unresolved_survivorship_warning_count": unresolved_count,
        "evidence_missing_count": 0,
        "review_only": True,
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
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "order_placement_enabled": False,
        "message_delivery_enabled": False,
        "message_sent": False,
        "output_files": {
            "reviewed_overlay": str(reviewed_csv),
            "review_template": str(template_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _approved_row(review_id: str, symbol: str) -> dict:
    return {
        "review_id": review_id,
        "overlay_plan_id": "overlay001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "include_flag": True,
        "review_status": "APPROVED_FOR_PIT_UNIVERSE",
        "valid_for_signal_date": True,
        "blocker_reason": "",
        "reviewer": "reviewer-a",
        "reviewed_at": "2024-05-29T10:00:00+08:00",
        "review_reason": "Local PIT evidence reviewed.",
        "evidence_source": "LOCAL_REVIEW_FIXTURE",
        "evidence_path": "outputs/reports/manual_diagnostics/local_evidence.csv",
        "evidence_reference": "",
        "listed_date": "1991-04-03",
        "delisted_date": "",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "listed_date_evidence": "1991-04-03",
        "delisted_date_evidence": "",
        "is_active_evidence": True,
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": True,
        "manual_review_required": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "review_only": True,
    }


def _needs_more_evidence_row(review_id: str, symbol: str) -> dict:
    row = _approved_row(review_id, symbol)
    row.update(
        {
            "include_flag": False,
            "review_status": "NEEDS_MORE_EVIDENCE",
            "valid_for_signal_date": False,
            "blocker_reason": "Need PIT evidence.",
            "evidence_source": "",
            "evidence_path": "",
            "listed_date": "",
            "listed_date_evidence": "",
            "is_active": "",
            "is_active_evidence": "",
            "survivorship_bias_resolved": False,
        }
    )
    return row


def _template_row(symbol: str) -> dict:
    return {
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "include_flag": "",
        "review_status": "NEEDS_MANUAL_REVIEW",
        "reviewer": "",
        "reviewed_at": "",
        "review_reason": "",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "listed_date_evidence": "",
        "delisted_date_evidence": "",
        "is_active_evidence": "",
        "is_st": "",
        "is_suspended": "",
        "survivorship_bias_resolved": "",
    }
