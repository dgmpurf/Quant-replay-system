import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_overlay_export_readiness import READINESS_OUTPUT_COLUMNS
from quant_replay_system.point_in_time_universe_overlay_export_readiness_health import (
    check_pit_universe_overlay_export_readiness_health,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_index import (
    build_pit_universe_overlay_export_readiness_index,
)
from quant_replay_system.point_in_time_universe_overlay_export_readiness_status import (
    run_pit_universe_overlay_export_readiness_status,
)


def test_pit_universe_overlay_export_readiness_index_detects_fake_artifact(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(root, "ready001")

    result = build_pit_universe_overlay_export_readiness_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["export_readiness_id"] == "ready001"
    assert row["review_id"] == "review001"
    assert int(row["row_count"]) == 2
    assert int(row["approved_count"]) == 0
    assert int(row["export_ready_count"]) == 0
    assert int(row["blocked_count"]) == 2
    assert row["no_approved_rows"] is True
    assert row["would_write_data_raw"] is False
    assert row["would_write_data_processed"] is False
    assert row["no_current_candidates_generated"] is True


def test_pit_universe_overlay_export_readiness_health_passes_no_approved_blocked_context(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(root, "ready001")

    result = check_pit_universe_overlay_export_readiness_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_pit_universe_overlay_export_readiness_health_fails_if_data_write_occurred(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(
        root,
        "ready001",
        metadata_updates={"would_write_data_raw": True, "would_write_data_processed": True},
    )

    result = check_pit_universe_overlay_export_readiness_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert {"DATA_RAW_WRITE_DETECTED", "DATA_PROCESSED_WRITE_DETECTED"}.issubset(
        set(result.health_frame["issue_code"])
    )


def test_pit_universe_overlay_export_readiness_health_fails_if_current_candidates_generated(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(
        root,
        "ready001",
        metadata_updates={"no_current_candidates_generated": False, "current_candidates_executed": True},
    )

    result = check_pit_universe_overlay_export_readiness_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "CURRENT_CANDIDATES_GENERATED" in set(result.health_frame["issue_code"])


def test_pit_universe_overlay_export_readiness_status_summarizes_latest_artifact(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(root, "ready001", created_at="2024-05-28T00:00:00")
    _write_export_readiness_artifact(root, "ready002", created_at="2024-05-29T00:00:00", ready=True)

    result = run_pit_universe_overlay_export_readiness_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_export_readiness_id == "ready002"
    assert result.workflow_stage == "PIT_UNIVERSE_EXPORT_READY_FOR_DRY_RUN"
    assert result.health_status == "PASS"
    assert result.approved_count == 1
    assert result.export_ready_count == 1
    assert "explicit universe export" in result.next_manual_action


def test_cli_pit_universe_overlay_export_readiness_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(root, "ready001")

    index_code = cli.main(
        [
            "pit-universe-overlay-export-readiness-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "pit-universe-overlay-export-readiness-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "pit-universe-overlay-export-readiness-status",
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
    assert "workflow_stage: PIT_UNIVERSE_EXPORT_BLOCKED_NO_APPROVED_ROWS" in status_output.out
    assert "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked." in status_output.out


def test_pit_universe_overlay_export_readiness_artifact_views_do_not_enable_execution(tmp_path: Path) -> None:
    root = tmp_path / "export_readiness"
    _write_export_readiness_artifact(root, "ready001")

    index = build_pit_universe_overlay_export_readiness_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_universe_overlay_export_readiness_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_universe_overlay_export_readiness_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["universe_exported"] is False
    assert health.audit_metadata["would_write_data_raw"] is False
    assert status.audit_metadata["current_candidates_executed"] is False
    assert status.audit_metadata["snapshot_manifest_built"] is False
    assert status.audit_metadata["forward_returns_computed"] is False
    assert status.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_sent"] is False


def _write_export_readiness_artifact(
    root: Path,
    export_readiness_id: str,
    *,
    created_at: str = "2024-05-29T00:00:00",
    ready: bool = False,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / export_readiness_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    readiness_csv = artifact_dir / "pit_universe_overlay_export_readiness.csv"
    report = artifact_dir / "pit_universe_overlay_export_readiness_report.md"
    metadata_path = artifact_dir / "metadata.json"
    rows = [_ready_row(export_readiness_id) if ready else _blocked_row(export_readiness_id, "000001")]
    if not ready:
        rows.append(_blocked_row(export_readiness_id, "510300"))
    pd.DataFrame(rows, columns=READINESS_OUTPUT_COLUMNS).to_csv(readiness_csv, index=False)
    report.write_text(
        "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "export_readiness_id": export_readiness_id,
        "review_id": "review001",
        "created_at": created_at,
        "status": "PASS" if ready else "WARN",
        "readiness_status": "EXPORT_READY_FOR_DRY_RUN" if ready else "EXPORT_BLOCKED_NO_APPROVED_ROWS",
        "row_count": len(rows),
        "approved_count": 1 if ready else 0,
        "export_ready_count": 1 if ready else 0,
        "blocked_count": 0 if ready else len(rows),
        "no_approved_rows": not ready,
        "missing_required_columns_count": 0 if ready else len(rows),
        "unresolved_survivorship_warning_count": 0 if ready else len(rows),
        "duplicate_key_count": 0,
        "would_write_data_raw": False,
        "would_write_data_processed": False,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "universe_exported": False,
        "current_candidates_executed": False,
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
            "readiness_csv": str(readiness_csv),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _blocked_row(export_readiness_id: str, symbol: str) -> dict:
    return {
        "export_readiness_id": export_readiness_id,
        "review_id": "review001",
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "review_status": "NEEDS_MANUAL_REVIEW",
        "include_flag": False,
        "valid_for_signal_date": False,
        "export_ready": False,
        "export_readiness_status": "EXPORT_BLOCKED_NEEDS_MORE_EVIDENCE",
        "export_blocker_reason": "review_status must be APPROVED_FOR_PIT_UNIVERSE before export readiness",
        "required_column_missing_count": 13,
        "missing_required_columns": "as_of_date,name,instrument_type,exchange,is_active,is_st,is_suspended,industry,min_lot,t_plus_rule,available_time,revision_id,source",
        "reviewer": "",
        "reviewed_at": "",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "survivorship_bias_warning": True,
        "survivorship_bias_resolved": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "export_readiness_only": True,
    }


def _ready_row(export_readiness_id: str) -> dict:
    row = _blocked_row(export_readiness_id, "000001")
    row.update(
        {
            "review_status": "APPROVED_FOR_PIT_UNIVERSE",
            "include_flag": True,
            "valid_for_signal_date": True,
            "export_ready": True,
            "export_readiness_status": "EXPORT_READY_FOR_DRY_RUN",
            "export_blocker_reason": "",
            "required_column_missing_count": 0,
            "missing_required_columns": "",
            "reviewer": "reviewer-a",
            "reviewed_at": "2024-05-29T10:00:00+08:00",
            "evidence_source": "LOCAL_REVIEW_FIXTURE",
            "evidence_path": "outputs/reports/manual_diagnostics/local_evidence.csv",
            "survivorship_bias_warning": True,
            "survivorship_bias_resolved": True,
        }
    )
    return row
