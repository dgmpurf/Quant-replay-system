import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.signal_semantics import SIGNAL_SEMANTICS_COLUMNS, SIGNAL_SEMANTICS_ISSUE_COLUMNS
from quant_replay_system.signal_semantics_health import check_signal_semantics_health
from quant_replay_system.signal_semantics_index import build_signal_semantics_index
from quant_replay_system.signal_semantics_status import run_signal_semantics_status


def test_signal_semantics_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001")

    result = build_signal_semantics_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["semantics_run_id"] == "sem001"
    assert int(row["row_count"]) == 1
    assert int(row["demo_only_count"]) == 1
    assert row["profile"] == "demo"


def test_signal_semantics_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_signal_semantics_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_signal_semantics_health_passes_safe_demo_run(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001")

    result = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_signal_semantics_health_fails_when_demo_has_review_buy(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001", row_updates={"advisory_action": "REVIEW_BUY_CANDIDATE"})

    result = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_ACTION_UNSAFE" in set(result.health_frame["issue_code"])


def test_signal_semantics_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001", metadata_updates={"auto_order_allowed": True})

    result = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_signal_semantics_health_fails_when_no_live_trading_missing_or_false(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001", metadata_updates={"no_live_trading": False})

    result = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MISSING_NO_LIVE_TRADING_STATEMENT" in set(result.health_frame["issue_code"])


def test_signal_semantics_health_detects_lost_leading_zero_symbol(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001", row_updates={"symbol": "1"})

    result = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_signal_semantics_status_summarizes_latest_run(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001", created_at="2024-05-19T00:00:00")
    _write_semantics_artifact(root, "sem002", created_at="2024-05-20T00:00:00")

    result = run_signal_semantics_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_semantics_run_id == "sem002"
    assert result.workflow_stage == "DEMO_SIGNAL_SEMANTICS_VALIDATED"
    assert result.status == "WARN"
    assert "DEMO_ONLY" in result.next_manual_action


def test_signal_semantics_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_signal_semantics_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_SIGNAL_SEMANTICS_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_semantics_run_id == ""


def test_cli_signal_semantics_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001")

    index_code = cli.main(
        [
            "signal-semantics-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "signal-semantics-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "signal-semantics-status",
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
    assert "workflow_stage: DEMO_SIGNAL_SEMANTICS_VALIDATED" in status_output.out
    assert "No live trading, broker API, order placement, or message delivery was invoked." in status_output.out


def test_signal_semantics_artifact_views_do_not_enable_live_or_message_delivery(tmp_path: Path) -> None:
    root = tmp_path / "signal_semantics"
    _write_semantics_artifact(root, "sem001")

    index = build_signal_semantics_index(root=root, output_dir=tmp_path / "index")
    health = check_signal_semantics_health(root=root, output_dir=tmp_path / "health")
    status = run_signal_semantics_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "signal_semantics_index": settings.signal_semantics_index.model_copy(
                update={"root_dir": tmp_path / "signal_semantics", "output_dir": tmp_path / "index"}
            ),
            "signal_semantics_health": settings.signal_semantics_health.model_copy(
                update={"root_dir": tmp_path / "signal_semantics", "output_dir": tmp_path / "health"}
            ),
            "signal_semantics_status": settings.signal_semantics_status.model_copy(
                update={"root_dir": tmp_path / "signal_semantics", "output_dir": tmp_path / "status"}
            ),
        }
    )


def _write_semantics_artifact(
    root: Path,
    semantics_run_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    row_updates: dict | None = None,
    metadata_updates: dict | None = None,
) -> None:
    artifact_dir = root / semantics_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    row = _safe_semantics_row(semantics_run_id)
    row.update(row_updates or {})
    semantics = pd.DataFrame([row], columns=SIGNAL_SEMANTICS_COLUMNS)
    semantics.to_csv(artifact_dir / "signal_semantics.csv", index=False)
    issues = pd.DataFrame([], columns=SIGNAL_SEMANTICS_ISSUE_COLUMNS)
    issues.to_csv(artifact_dir / "signal_semantics_issues.csv", index=False)
    (artifact_dir / "signal_semantics_report.md").write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    counts = {
        "BLOCKED": 1 if row["advisory_action"] == "BLOCKED" else 0,
        "DEMO_ONLY": 1 if row["advisory_action"] == "DEMO_ONLY" else 0,
        "HOLD_REVIEW": 1 if row["advisory_action"] == "HOLD_REVIEW" else 0,
        "NO_ACTION": 1 if row["advisory_action"] == "NO_ACTION" else 0,
        "REVIEW_BUY_CANDIDATE": 1 if row["advisory_action"] == "REVIEW_BUY_CANDIDATE" else 0,
        "REVIEW_SELL_CANDIDATE": 1 if row["advisory_action"] == "REVIEW_SELL_CANDIDATE" else 0,
        "WATCH": 1 if row["advisory_action"] == "WATCH" else 0,
    }
    metadata = {
        "semantics_run_id": semantics_run_id,
        "created_at": created_at,
        "status": "WARN",
        "input_path": "candidates.csv",
        "input_type": "candidates",
        "profile": "demo",
        "row_count": 1,
        "issue_count": 0,
        "action_counts": counts,
        "blocked_count": counts["BLOCKED"],
        "demo_only_count": counts["DEMO_ONLY"],
        "watch_count": counts["WATCH"],
        "review_buy_candidate_count": counts["REVIEW_BUY_CANDIDATE"],
        "review_sell_candidate_count": counts["REVIEW_SELL_CANDIDATE"],
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
        "outputs": {
            "signal_semantics": str(artifact_dir / "signal_semantics.csv"),
            "signal_semantics_report": str(artifact_dir / "signal_semantics_report.md"),
            "signal_semantics_issues": str(artifact_dir / "signal_semantics_issues.csv"),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    metadata.update(metadata_updates or {})
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _safe_semantics_row(semantics_run_id: str) -> dict:
    return {
        "semantics_run_id": semantics_run_id,
        "source_row_index": 0,
        "symbol": "000001",
        "name": "Ping An Bank",
        "instrument_type": "STOCK",
        "advisory_action": "DEMO_ONLY",
        "source_action": "NO_TRADE",
        "score_action": "NO_TRADE",
        "final_score": 55.0,
        "risk_precheck_status": "PASS",
        "risk_precheck_reason": "eligible",
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
        "reason_summary": "Demo semantics validation only.",
        "score_breakdown": "{}",
        "supporting_factors": "{}",
        "issue_codes": "",
    }
