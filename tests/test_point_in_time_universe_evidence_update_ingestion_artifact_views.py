import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.point_in_time_universe_evidence_update_ingestion import (
    INGESTION_OUTPUT_COLUMNS,
    REVIEW_UPDATE_COLUMNS,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_health import (
    check_pit_universe_evidence_update_ingestion_health,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_index import (
    build_pit_universe_evidence_update_ingestion_index,
)
from quant_replay_system.point_in_time_universe_evidence_update_ingestion_status import (
    run_pit_universe_evidence_update_ingestion_status,
)


def test_pit_universe_evidence_update_ingestion_index_detects_fake_artifact(tmp_path: Path) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(root, "ingest001", ready_count=0, blocked_count=2)

    result = build_pit_universe_evidence_update_ingestion_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["ingestion_id"] == "ingest001"
    assert int(row["row_count"]) == 2
    assert int(row["ready_for_review_update_count"]) == 0
    assert int(row["blocked_count"]) == 2
    assert row["no_universe_export"] is True
    assert row["no_data_raw_write"] is True
    assert row["no_data_processed_write"] is True
    assert row["no_current_candidates_generated"] is True
    assert row["ingestion_only"] is True


def test_pit_universe_evidence_update_ingestion_health_warns_not_fails_for_no_ready_rows(tmp_path: Path) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(root, "ingest001", ready_count=0, blocked_count=2)

    result = check_pit_universe_evidence_update_ingestion_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.error_count == 0
    assert result.issue_count == 0


def test_pit_universe_evidence_update_ingestion_health_fails_on_data_write_or_current_candidates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(
        root,
        "ingest001",
        ready_count=0,
        blocked_count=2,
        metadata_updates={
            "no_data_raw_write": False,
            "no_data_processed_write": False,
            "no_current_candidates_generated": False,
        },
    )

    result = check_pit_universe_evidence_update_ingestion_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert {
        "DATA_RAW_WRITE_DETECTED",
        "DATA_PROCESSED_WRITE_DETECTED",
        "CURRENT_CANDIDATES_GENERATED",
    }.issubset(set(result.health_frame["issue_code"]))


def test_pit_universe_evidence_update_ingestion_health_fails_if_blocked_rows_are_clean_updates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(root, "ingest001", ready_count=1, blocked_count=1, include_blocked_clean=True)

    result = check_pit_universe_evidence_update_ingestion_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "BLOCKED_ROWS_IN_CLEAN_REVIEW_UPDATES" in set(result.health_frame["issue_code"])


def test_pit_universe_evidence_update_ingestion_status_no_ready_and_partial_ready(tmp_path: Path) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(root, "ingest001", ready_count=0, blocked_count=2, created_at="2024-05-30T00:00:00")
    no_ready = run_pit_universe_evidence_update_ingestion_status(root=root, output_dir=tmp_path / "status1")

    assert no_ready.latest_ingestion_id == "ingest001"
    assert no_ready.workflow_stage == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES"
    assert no_ready.health_status == "PASS"
    assert no_ready.ready_for_review_update_count == 0
    assert no_ready.blocked_count == 2

    _write_ingestion_artifact(root, "ingest002", ready_count=1, blocked_count=1, created_at="2024-05-31T00:00:00")
    partial = run_pit_universe_evidence_update_ingestion_status(root=root, output_dir=tmp_path / "status2")

    assert partial.latest_ingestion_id == "ingest002"
    assert partial.workflow_stage == "PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_PARTIAL_READY"
    assert partial.ready_for_review_update_count == 1
    assert partial.blocked_count == 1
    assert "clean review_updates" in partial.next_manual_action


def test_cli_pit_universe_evidence_update_ingestion_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "ingestion"
    _write_ingestion_artifact(root, "ingest001", ready_count=0, blocked_count=2)

    index_code = cli.main(
        [
            "pit-universe-evidence-update-ingestion-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "pit-universe-evidence-update-ingestion-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "pit-universe-evidence-update-ingestion-status",
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
    assert "workflow_stage: PIT_UNIVERSE_EVIDENCE_UPDATE_INGESTION_NO_READY_UPDATES" in status_output.out
    assert "ready_for_review_update_count: 0" in status_output.out
    assert "No approval applied, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked." in status_output.out


def _write_ingestion_artifact(
    root: Path,
    ingestion_id: str,
    *,
    ready_count: int,
    blocked_count: int,
    created_at: str = "2024-05-30T00:00:00",
    include_blocked_clean: bool = False,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / ingestion_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ingestion_csv = artifact_dir / "pit_universe_evidence_update_ingestion.csv"
    review_updates = artifact_dir / "pit_universe_review_updates.csv"
    report = artifact_dir / "pit_universe_evidence_update_ingestion_report.md"
    metadata_path = artifact_dir / "metadata.json"
    rows = []
    for idx in range(ready_count):
        rows.append(_ingestion_row(ingestion_id, f"00000{idx + 1}", ready=True))
    for idx in range(blocked_count):
        rows.append(_ingestion_row(ingestion_id, f"51030{idx}", ready=False))
    pd.DataFrame(rows, columns=INGESTION_OUTPUT_COLUMNS).to_csv(ingestion_csv, index=False)
    clean_rows = [row for row in rows if row["ready_for_review_update"]]
    if include_blocked_clean and rows:
        clean_rows.append(rows[-1])
    pd.DataFrame([_clean_row(row) for row in clean_rows], columns=REVIEW_UPDATE_COLUMNS).to_csv(
        review_updates,
        index=False,
    )
    report.write_text(
        "Evidence update ingestion only. No approval, universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked.",
        encoding="utf-8",
    )
    metadata = {
        "ingestion_id": ingestion_id,
        "created_at": created_at,
        "row_count": len(rows),
        "ready_for_review_update_count": ready_count,
        "blocked_count": blocked_count,
        "approval_requested_count": ready_count,
        "approved_ready_count": ready_count,
        "rejected_ready_count": 0,
        "needs_more_evidence_ready_count": 0,
        "duplicate_identity_count": 0,
        "missing_identity_count": 0,
        "suggested_copy_risk_count": 0,
        "approval_applied": False,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "ingestion_only": True,
        "output_files": {
            "ingestion_csv": str(ingestion_csv),
            "review_updates": str(review_updates),
            "report": str(report),
            "metadata": str(metadata_path),
        },
    }
    if metadata_updates:
        metadata.update(metadata_updates)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def _ingestion_row(ingestion_id: str, symbol: str, *, ready: bool) -> dict:
    return {
        "ingestion_id": ingestion_id,
        "signal_date": "2024-04-02",
        "symbol": symbol,
        "universe_name": "etf_core",
        "input_review_status": "APPROVED_FOR_PIT_UNIVERSE" if ready else "",
        "normalized_review_status": "APPROVED_FOR_PIT_UNIVERSE" if ready else "",
        "include_flag": ready,
        "ingestion_status": "UPDATE_READY_FOR_REVIEW_APPLY" if ready else "UPDATE_BLOCKED_INVALID_STATUS",
        "ingestion_blocker_reason": "" if ready else "invalid review_status",
        "ready_for_review_update": ready,
        "approval_requested": ready,
        "reviewer": "reviewer-a" if ready else "",
        "reviewed_at": "2024-06-02 10:00:00" if ready else "",
        "review_reason": "Manual evidence reviewed." if ready else "",
        "evidence_source": "LOCAL_REVIEW" if ready else "",
        "evidence_path": "docs/evidence/local.csv" if ready else "",
        "evidence_reference": "",
        "listed_date": "1991-04-03" if ready else "",
        "delisted_date": "",
        "is_active": ready,
        "is_st": False,
        "is_suspended": False,
        "listed_date_evidence": "1991-04-03" if ready else "",
        "delisted_date_evidence": "",
        "is_active_evidence": ready,
        "survivorship_bias_resolved": ready,
        "as_of_date": "2024-04-02" if ready else "",
        "name": f"Sample {symbol}" if ready else "",
        "instrument_type": "STOCK" if ready else "",
        "exchange": "SZSE" if ready else "",
        "industry": "BANKING" if ready else "",
        "min_lot": "100" if ready else "",
        "t_plus_rule": "T+1" if ready else "",
        "available_time": "2024-04-02 08:00:00" if ready else "",
        "revision_id": "review-v1" if ready else "",
        "source": "LOCAL_REVIEW" if ready else "",
        "suggested_copy_risk": False,
        "no_universe_export": True,
        "no_data_raw_write": True,
        "no_data_processed_write": True,
        "no_current_candidates_generated": True,
        "no_snapshot_built": True,
        "no_forward_labels": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "ingestion_only": True,
    }


def _clean_row(row: dict) -> dict:
    return {column: row.get(column, "") for column in REVIEW_UPDATE_COLUMNS}
