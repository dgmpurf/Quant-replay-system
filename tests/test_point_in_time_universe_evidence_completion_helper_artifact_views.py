import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_evidence_completion_helper import HELPER_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_evidence_completion_helper_health import (
    check_pit_universe_evidence_completion_helper_health,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper_index import (
    build_pit_universe_evidence_completion_helper_index,
)
from quant_replay_system.point_in_time_universe_evidence_completion_helper_status import (
    run_pit_universe_evidence_completion_helper_status,
)


def test_pit_universe_evidence_completion_helper_index_detects_fake_artifact(tmp_path: Path) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001")

    result = build_pit_universe_evidence_completion_helper_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["helper_id"] == "helper001"
    assert row["review_id"] == "review001"
    assert int(row["row_count"]) == 2
    assert int(row["needs_evidence_count"]) == 2
    assert int(row["rows_with_base_hints_count"]) == 2
    assert int(row["future_dated_hint_count"]) == 2
    assert int(row["authoritative_hint_count"]) == 0
    assert int(row["approved_count"]) == 0
    assert int(row["valid_for_signal_date_count"]) == 0
    assert row["no_universe_export"] is True
    assert row["no_data_raw_write"] is True
    assert row["no_data_processed_write"] is True
    assert row["no_current_candidates_generated"] is True


def test_pit_universe_evidence_completion_helper_health_passes_safe_helper(tmp_path: Path) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001")

    result = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_pit_universe_evidence_completion_helper_health_fails_if_helper_approves_rows(tmp_path: Path) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001", approved=True)

    result = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "HELPER_APPROVED_ROWS" in set(result.health_frame["issue_code"])


def test_pit_universe_evidence_completion_helper_health_fails_if_helper_sets_valid_for_signal_date(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001", valid_for_signal_date=True)

    result = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "HELPER_SET_VALID_FOR_SIGNAL_DATE" in set(result.health_frame["issue_code"])


def test_pit_universe_evidence_completion_helper_health_fails_if_data_write_occurred(tmp_path: Path) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(
        root,
        "helper001",
        metadata_updates={
            "no_data_raw_write": False,
            "would_write_data_raw": True,
            "no_data_processed_write": False,
            "would_write_data_processed": True,
        },
    )

    result = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert {"DATA_RAW_WRITE_DETECTED", "DATA_PROCESSED_WRITE_DETECTED"}.issubset(
        set(result.health_frame["issue_code"])
    )


def test_pit_universe_evidence_completion_helper_health_fails_if_current_candidates_generated(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(
        root,
        "helper001",
        metadata_updates={"no_current_candidates_generated": False, "current_candidates_executed": True},
    )

    result = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "CURRENT_CANDIDATES_GENERATED" in set(result.health_frame["issue_code"])


def test_pit_universe_evidence_completion_helper_status_summarizes_latest_artifact(tmp_path: Path) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001", created_at="2024-05-28T00:00:00")
    _write_helper_artifact(root, "helper002", created_at="2024-05-29T00:00:00")

    result = run_pit_universe_evidence_completion_helper_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_helper_id == "helper002"
    assert result.workflow_stage == "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW"
    assert result.health_status == "PASS"
    assert result.row_count == 2
    assert result.needs_evidence_count == 2
    assert result.rows_with_base_hints_count == 2
    assert result.future_dated_hint_count == 2
    assert result.authoritative_hint_count == 0
    assert "Complete PIT universe evidence" in result.next_manual_action


def test_cli_pit_universe_evidence_completion_helper_index_health_status_work(
    tmp_path: Path,
    capsys,
) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001")

    index_code = cli.main(
        [
            "pit-universe-evidence-completion-helper-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "pit-universe-evidence-completion-helper-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "pit-universe-evidence-completion-helper-status",
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
    assert "workflow_stage: PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_NEEDS_REVIEW" in status_output.out
    assert "authoritative_hint_count: 0" in status_output.out
    assert "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked." in status_output.out


def test_pit_universe_evidence_completion_helper_artifact_views_do_not_enable_execution(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence_helper"
    _write_helper_artifact(root, "helper001")

    index = build_pit_universe_evidence_completion_helper_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_universe_evidence_completion_helper_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_universe_evidence_completion_helper_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["universe_exported"] is False
    assert health.audit_metadata["would_write_data_raw"] is False
    assert status.audit_metadata["current_candidates_executed"] is False
    assert status.audit_metadata["snapshot_manifest_built"] is False
    assert status.audit_metadata["forward_returns_computed"] is False
    assert status.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_sent"] is False


def _write_helper_artifact(
    root: Path,
    helper_id: str,
    *,
    created_at: str = "2024-05-29T00:00:00",
    approved: bool = False,
    valid_for_signal_date: bool = False,
    authoritative_hint: bool = False,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / helper_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    template_csv = artifact_dir / "pit_universe_evidence_completion_template.csv"
    report = artifact_dir / "pit_universe_evidence_gap_report.md"
    metadata_path = artifact_dir / "metadata.json"
    rows = [
        _helper_row(helper_id, "000001", approved, valid_for_signal_date, authoritative_hint),
        _helper_row(helper_id, "510300", approved, valid_for_signal_date, authoritative_hint),
    ]
    pd.DataFrame(rows, columns=HELPER_OUTPUT_COLUMNS).to_csv(template_csv, index=False)
    report.write_text(
        "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "helper_id": helper_id,
        "review_id": "review001",
        "review": "outputs/reports/point_in_time_universe_overlay_review/review001/reviewed_pit_universe_overlay.csv",
        "base_universe": "data/processed/universe/base/raw_data_cleaned.csv",
        "created_at": created_at,
        "status": "WARN",
        "row_count": len(rows),
        "needs_evidence_count": len(rows),
        "rows_with_base_hints_count": len(rows),
        "future_dated_hint_count": len(rows),
        "authoritative_hint_count": len(rows) if authoritative_hint else 0,
        "approved_count": len(rows) if approved else 0,
        "valid_for_signal_date_count": len(rows) if valid_for_signal_date else 0,
        "evidence_completion_only": True,
        "no_universe_export": True,
        "universe_exported": False,
        "no_data_raw_write": True,
        "would_write_data_raw": False,
        "no_data_processed_write": True,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "current_candidates_executed": False,
        "no_snapshot_built": True,
        "snapshot_manifest_built": False,
        "no_forward_labels": True,
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
            "evidence_completion_template": str(template_csv),
            "gap_report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _helper_row(
    helper_id: str,
    symbol: str,
    approved: bool,
    valid_for_signal_date: bool,
    authoritative_hint: bool,
) -> dict:
    return {
        "helper_id": helper_id,
        "review_id": "review001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "current_review_status": "APPROVED_FOR_PIT_UNIVERSE" if approved else "NEEDS_MANUAL_REVIEW",
        "current_valid_for_signal_date": valid_for_signal_date,
        "current_survivorship_bias_warning": True,
        "current_survivorship_bias_resolved": False,
        "missing_reviewer": True,
        "missing_reviewed_at": True,
        "missing_review_reason": True,
        "missing_evidence_source": True,
        "missing_evidence_path_or_reference": True,
        "missing_listed_date_evidence": True,
        "missing_is_active_evidence": True,
        "missing_survivorship_bias_resolution": True,
        "suggested_name": "Ping An Bank" if symbol == "000001" else "CSI 300 ETF",
        "suggested_instrument_type": "STOCK" if symbol == "000001" else "ETF",
        "suggested_exchange": "SZSE" if symbol == "000001" else "SSE",
        "suggested_industry": "UNKNOWN",
        "suggested_min_lot": 100,
        "suggested_t_plus_rule": "T+1",
        "suggested_is_active": True,
        "suggested_is_st": False,
        "suggested_is_suspended": False,
        "suggested_source": "LOCAL_HINT_FIXTURE",
        "suggested_revision_id": "v1",
        "suggested_available_time": "2024-05-20 08:00:00",
        "hint_source_path": "data/processed/universe/base/raw_data_cleaned.csv",
        "hint_as_of_date": "2024-05-20",
        "hint_available_time": "2024-05-20 08:00:00",
        "hint_is_future_dated_for_signal_date": True,
        "hint_authoritative_for_pit": authoritative_hint,
        "next_review_action": "Fill reviewer, reviewed_at, evidence, listed-date, active-status, and survivorship-resolution fields.",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "evidence_completion_only": True,
    }
