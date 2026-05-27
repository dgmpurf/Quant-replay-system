import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.signal_advisory import SIGNAL_COLUMNS
from quant_replay_system.signal_advisory_health import check_signal_advisory_health
from quant_replay_system.signal_advisory_index import build_signal_advisory_index
from quant_replay_system.signal_advisory_status import run_signal_advisory_status


def test_signal_advisory_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001")

    result = build_signal_advisory_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["signal_run_id"] == "sig001"
    assert int(row["signal_count"]) == 1
    assert int(row["demo_signal_count"]) == 1
    assert row["source_candidate_run_id"] == "candidate123"


def test_signal_advisory_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_signal_advisory_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_signal_advisory_health_passes_safe_demo_run(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001")

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_signal_advisory_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", metadata_updates={"auto_order_allowed": True})

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_warns_when_legacy_provenance_missing(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", include_semantics_provenance=False)

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert "MISSING_SEMANTICS_PROVENANCE" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_fails_when_semantics_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", signal_updates={"semantics_auto_order_allowed": True})

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_fails_when_semantics_source_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", metadata_updates={"semantics_policy_source": "other_policy"})

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_POLICY_SOURCE_MISMATCH" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_fails_when_demo_signal_has_buy_action(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", signal_updates={"advisory_action": "REVIEW_BUY_CANDIDATE"})

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_SIGNAL_ACTION_UNSAFE" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_fails_when_leading_zero_symbol_is_lost(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", signal_updates={"symbol": "1"})

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_signal_advisory_health_warns_when_alert_preview_missing(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", write_alert_preview=False)

    result = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert "MISSING_ALERT_PREVIEW" in set(result.health_frame["issue_code"])


def test_signal_advisory_status_summarizes_latest_signal_run(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001", created_at="2024-05-19T00:00:00")
    _write_signal_artifact(root, "sig002", created_at="2024-05-20T00:00:00")

    result = run_signal_advisory_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_signal_run_id == "sig002"
    assert result.workflow_stage == "DEMO_SIGNAL_ADVISORY_VALIDATED"
    assert result.status == "WARN"
    assert "DEMO_ONLY" in result.next_manual_action


def test_signal_advisory_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_signal_advisory_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_SIGNAL_ADVISORY_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_signal_run_id == ""


def test_cli_signal_advisory_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001")

    index_code = cli.main(
        [
            "signal-advisory-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "signal-advisory-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "signal-advisory-status",
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
    assert "workflow_stage: DEMO_SIGNAL_ADVISORY_VALIDATED" in status_output.out
    assert "No live trading, broker API, order placement, or message delivery was invoked." in status_output.out


def test_signal_advisory_artifact_views_do_not_enable_live_or_message_delivery(tmp_path: Path) -> None:
    root = tmp_path / "signals"
    _write_signal_artifact(root, "sig001")

    index = build_signal_advisory_index(root=root, output_dir=tmp_path / "index")
    health = check_signal_advisory_health(root=root, output_dir=tmp_path / "health")
    status = run_signal_advisory_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "signal_advisory_index": settings.signal_advisory_index.model_copy(
                update={"root_dir": tmp_path / "signals", "output_dir": tmp_path / "index"}
            ),
            "signal_advisory_health": settings.signal_advisory_health.model_copy(
                update={"root_dir": tmp_path / "signals", "output_dir": tmp_path / "health"}
            ),
            "signal_advisory_status": settings.signal_advisory_status.model_copy(
                update={"root_dir": tmp_path / "signals", "output_dir": tmp_path / "status"}
            ),
        }
    )


def _write_signal_artifact(
    root: Path,
    signal_run_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    signal_updates: dict | None = None,
    metadata_updates: dict | None = None,
    write_alert_preview: bool = True,
    include_semantics_provenance: bool = True,
) -> None:
    artifact_dir = root / signal_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    signal = _safe_signal(signal_run_id)
    if not include_semantics_provenance:
        for key in _semantics_provenance("DEMO_ONLY"):
            signal.pop(key, None)
    signal.update(signal_updates or {})
    signals = pd.DataFrame([signal], columns=SIGNAL_COLUMNS)
    signals.to_csv(artifact_dir / "signals.csv", index=False)
    (artifact_dir / "signal_advisory_report.md").write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    if write_alert_preview:
        (artifact_dir / "signal_alert_preview.md").write_text(
            "No message was sent. Manual confirmation required. No auto-order.",
            encoding="utf-8",
        )
    metadata = {
        "signal_run_id": signal_run_id,
        "created_at": created_at,
        "status": "READY",
        "signal_count": 1,
        "advisory_action_counts": {
            "BLOCKED": 0,
            "DEMO_ONLY": 1 if signal["advisory_action"] == "DEMO_ONLY" else 0,
            "HOLD_REVIEW": 0,
            "NO_ACTION": 0,
            "REVIEW_BUY_CANDIDATE": 1 if signal["advisory_action"] == "REVIEW_BUY_CANDIDATE" else 0,
            "REVIEW_SELL_CANDIDATE": 0,
            "WATCH": 1 if signal["advisory_action"] == "WATCH" else 0,
        },
        "source_candidate_run_id": "candidate123",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "alert_delivery_enabled": False,
        "output_files": {
            "signals": str(artifact_dir / "signals.csv"),
            "signal_alert_preview": str(artifact_dir / "signal_alert_preview.md"),
            "signal_advisory_report": str(artifact_dir / "signal_advisory_report.md"),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    if include_semantics_provenance:
        metadata.update(_semantics_provenance(signal["advisory_action"]))
    metadata.update(metadata_updates or {})
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _safe_signal(signal_run_id: str) -> dict:
    return {
        "signal_id": f"{signal_run_id}_000001",
        "signal_run_id": signal_run_id,
        "signal_date": "2024-05-20",
        "decision_date": "2024-05-20",
        "symbol": "000001",
        "name": "Ping An Bank",
        "instrument_type": "STOCK",
        "source_candidate_run_id": "candidate123",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "advisory_action": "DEMO_ONLY",
        **_semantics_provenance("DEMO_ONLY"),
        "original_score_action": "NO_TRADE",
        "original_candidate_action": "NO_TRADE",
        "final_score": 55.0,
        "confidence_level": "LOW_REVIEW",
        "reason_summary": "Demo workflow validation only.",
        "score_breakdown": "{}",
        "entry_condition": "No entry condition.",
        "exit_condition": "No exit condition.",
        "invalidation_condition": "Invalid outside demo context.",
        "valid_until": "2024-05-21",
        "risk_notes": "manual confirmation required",
        "data_source_notes": "local artifact",
        "snapshot_manifest_path": "snapshot_manifest.json",
        "candidates_path": "candidates.csv",
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "alert_title": "000001 DEMO_ONLY preview",
        "alert_body": "Manual confirmation required. No auto-order. No live trading or broker API.",
    }


def _semantics_provenance(action: str) -> dict:
    return {
        "semantics_policy_source": "signal_semantics",
        "semantics_policy_version": "v0.1",
        "semantics_classifier": "classify_signal_semantics_action",
        "semantics_settings_profile": "demo",
        "semantics_action": action,
        "semantics_reason": "Test artifact classified by shared signal semantics.",
        "semantics_manual_confirmation_required": True,
        "semantics_auto_order_allowed": False,
        "semantics_no_live_trading": True,
        "semantics_no_broker_api": True,
    }
