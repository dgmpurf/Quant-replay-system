import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.advisory_profile_calibration import (
    CALIBRATION_COLUMNS,
    CALIBRATION_ISSUE_COLUMNS,
    CALIBRATION_SUMMARY_COLUMNS,
)
from quant_replay_system.advisory_profile_calibration_health import check_advisory_profile_calibration_health
from quant_replay_system.advisory_profile_calibration_index import build_advisory_profile_calibration_index
from quant_replay_system.advisory_profile_calibration_status import run_advisory_profile_calibration_status


def test_advisory_profile_calibration_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001")

    result = build_advisory_profile_calibration_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["calibration_run_id"] == "cal001"
    assert int(row["row_count"]) == 1
    assert int(row["demo_only_count"]) == 1
    assert row["profile"] == "balanced"
    assert row["calibration_csv_path"].endswith("advisory_profile_calibration.csv")


def test_advisory_profile_calibration_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_advisory_profile_calibration_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_advisory_profile_calibration_health_passes_safe_demo_calibration(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001")

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_advisory_profile_calibration_health_passes_safe_synthetic_non_demo_calibration(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(
        root,
        "cal001",
        profile="experimental",
        row_updates={
            "selection_profile": "reviewed_local_v0",
            "demo_mode": False,
            "not_strategy_recommendation": False,
            "simulated_advisory_label": "REVIEW_BUY_CANDIDATE",
        },
        metadata_updates={
            "label_counts": {"REVIEW_BUY_CANDIDATE": 1, "WATCH": 0, "NO_ACTION": 0, "BLOCKED": 0, "DEMO_ONLY": 0},
        },
    )

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_advisory_profile_calibration_health_fails_when_demo_has_review_buy(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001", row_updates={"simulated_advisory_label": "REVIEW_BUY_CANDIDATE"})

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_PROFILE_ACTION_UNSAFE" in set(result.health_frame["issue_code"])


def test_advisory_profile_calibration_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001", metadata_updates={"auto_order_allowed": True})

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_advisory_profile_calibration_health_fails_when_no_live_trading_missing_or_false(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001", row_updates={"no_live_trading": False})

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MISSING_NO_LIVE_TRADING_STATEMENT" in set(result.health_frame["issue_code"])


def test_advisory_profile_calibration_health_detects_lost_leading_zero_symbol(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001", row_updates={"symbol": "1"})

    result = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_advisory_profile_calibration_status_summarizes_latest_run(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001", created_at="2024-05-19T00:00:00")
    _write_calibration_artifact(
        root,
        "cal002",
        created_at="2024-05-20T00:00:00",
        profile="experimental",
        row_updates={
            "selection_profile": "reviewed_local_v0",
            "demo_mode": False,
            "not_strategy_recommendation": False,
            "simulated_advisory_label": "REVIEW_BUY_CANDIDATE",
        },
        metadata_updates={
            "label_counts": {"REVIEW_BUY_CANDIDATE": 1, "WATCH": 0, "NO_ACTION": 0, "BLOCKED": 0, "DEMO_ONLY": 0},
        },
    )

    result = run_advisory_profile_calibration_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_calibration_run_id == "cal002"
    assert result.workflow_stage == "ADVISORY_PROFILE_CALIBRATION_READY_FOR_REVIEW"
    assert result.status == "PASS"
    assert "REVIEW_BUY_CANDIDATE is not an order" in result.next_manual_action


def test_advisory_profile_calibration_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_advisory_profile_calibration_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_ADVISORY_PROFILE_CALIBRATION_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_calibration_run_id == ""


def test_cli_advisory_profile_calibration_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001")

    index_code = cli.main(
        [
            "advisory-profile-calibration-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "advisory-profile-calibration-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "advisory-profile-calibration-status",
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
    assert "workflow_stage: DEMO_ADVISORY_PROFILE_CALIBRATION_VALIDATED" in status_output.out
    assert "No live trading, broker API, order placement, or message delivery was invoked." in status_output.out


def test_advisory_profile_calibration_artifact_views_do_not_enable_live_or_message_delivery(tmp_path: Path) -> None:
    root = tmp_path / "advisory_profile_calibration"
    _write_calibration_artifact(root, "cal001")

    index = build_advisory_profile_calibration_index(root=root, output_dir=tmp_path / "index")
    health = check_advisory_profile_calibration_health(root=root, output_dir=tmp_path / "health")
    status = run_advisory_profile_calibration_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False


def _write_calibration_artifact(
    root: Path,
    calibration_run_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    profile: str = "balanced",
    row_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / calibration_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    row = _safe_calibration_row(calibration_run_id, profile=profile)
    row.update(row_updates or {})
    calibration = pd.DataFrame([row], columns=CALIBRATION_COLUMNS)
    calibration.to_csv(artifact_dir / "advisory_profile_calibration.csv", index=False)
    issues = pd.DataFrame([], columns=CALIBRATION_ISSUE_COLUMNS)
    issues.to_csv(artifact_dir / "advisory_profile_calibration_issues.csv", index=False)
    (artifact_dir / "advisory_profile_calibration_report.md").write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    counts = {
        "REVIEW_BUY_CANDIDATE": 1 if row["simulated_advisory_label"] == "REVIEW_BUY_CANDIDATE" else 0,
        "WATCH": 1 if row["simulated_advisory_label"] == "WATCH" else 0,
        "NO_ACTION": 1 if row["simulated_advisory_label"] == "NO_ACTION" else 0,
        "BLOCKED": 1 if row["simulated_advisory_label"] == "BLOCKED" else 0,
        "DEMO_ONLY": 1 if row["simulated_advisory_label"] == "DEMO_ONLY" else 0,
    }
    metadata = {
        "calibration_run_id": calibration_run_id,
        "created_at": created_at,
        "status": "WARN" if counts["DEMO_ONLY"] else "PASS",
        "input_path": "candidates.csv",
        "input_type": "candidates",
        "profile": profile,
        "row_count": 1,
        "symbol_count": 1,
        "label_counts": counts,
        "issue_count": 0,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "calibration_only": True,
        "not_trading_recommendation": True,
        "output_files": {
            "advisory_profile_calibration": str(artifact_dir / "advisory_profile_calibration.csv"),
            "advisory_profile_calibration_summary": str(artifact_dir / "advisory_profile_calibration_summary.csv"),
            "advisory_profile_calibration_issues": str(artifact_dir / "advisory_profile_calibration_issues.csv"),
            "advisory_profile_calibration_report": str(artifact_dir / "advisory_profile_calibration_report.md"),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    metadata.update(metadata_updates or {})
    label_counts = metadata["label_counts"]
    summary = {
        "calibration_run_id": calibration_run_id,
        "status": metadata["status"],
        "input_path": metadata["input_path"],
        "input_type": metadata["input_type"],
        "profile": profile,
        "row_count": metadata["row_count"],
        "symbol_count": metadata["symbol_count"],
        "final_score_min": row["final_score"],
        "final_score_median": row["final_score"],
        "final_score_max": row["final_score"],
        "review_buy_candidate_count": label_counts.get("REVIEW_BUY_CANDIDATE", 0),
        "watch_count": label_counts.get("WATCH", 0),
        "no_action_count": label_counts.get("NO_ACTION", 0),
        "blocked_count": label_counts.get("BLOCKED", 0),
        "demo_only_count": label_counts.get("DEMO_ONLY", 0),
        "issue_count": metadata["issue_count"],
        "risk_precheck_status_counts": "{}",
        "score_action_counts": "{}",
        "action_counts": "{}",
        "requires_manual_confirmation": metadata["requires_manual_confirmation"],
        "auto_order_allowed": metadata["auto_order_allowed"],
        "no_live_trading": metadata["no_live_trading"],
        "no_broker_api": metadata["no_broker_api"],
        "no_message_sent": metadata["no_message_sent"],
    }
    pd.DataFrame([summary], columns=CALIBRATION_SUMMARY_COLUMNS).to_csv(
        artifact_dir / "advisory_profile_calibration_summary.csv",
        index=False,
    )
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _safe_calibration_row(calibration_run_id: str, *, profile: str) -> dict:
    return {
        "calibration_run_id": calibration_run_id,
        "source_row_index": 0,
        "symbol": "000001",
        "name": "Ping An Bank",
        "instrument_type": "STOCK",
        "profile": profile,
        "simulated_advisory_label": "DEMO_ONLY",
        "final_score": 72.0,
        "reviewed_buy_min_score": 70.0,
        "watch_min_score": 55.0,
        "risk_precheck_status": "PASS",
        "risk_precheck_reason": "eligible",
        "score_action": "NO_TRADE",
        "action": "NO_TRADE",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "snapshot_quality_status": "PASS",
        "data_quality_status": "PASS",
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "calibration_only": True,
        "not_trading_recommendation": True,
        "reason_summary": "Demo calibration validation only.",
        "issue_codes": "",
    }
