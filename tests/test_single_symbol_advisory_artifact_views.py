import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.single_symbol_advisory import SINGLE_SYMBOL_ADVISORY_COLUMNS
from quant_replay_system.single_symbol_advisory_health import check_single_symbol_advisory_health
from quant_replay_system.single_symbol_advisory_index import build_single_symbol_advisory_index
from quant_replay_system.single_symbol_advisory_status import run_single_symbol_advisory_status


def test_single_symbol_advisory_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001")

    result = build_single_symbol_advisory_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["advisory_run_id"] == "adv001"
    assert row["symbol"] == "000001"
    assert row["advisory_action"] == "DEMO_ONLY"
    assert row["semantics_policy_source"] == "signal_semantics"
    assert row["semantics_policy_version"] == "v0.1"
    assert row["semantics_action"] == "DEMO_ONLY"
    assert bool(row["semantics_provenance_present"]) is True
    assert bool(row["semantics_missing_provenance_legacy_warning_only"]) is False


def test_single_symbol_advisory_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_single_symbol_advisory_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_single_symbol_advisory_health_passes_safe_demo_review(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001")

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_single_symbol_advisory_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001", metadata_updates={"auto_order_allowed": True})

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_warns_when_legacy_provenance_missing(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001", include_semantics_provenance=False)

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")
    index = build_single_symbol_advisory_index(root=root, output_dir=tmp_path / "index")

    assert result.status == "WARN"
    assert "MISSING_SEMANTICS_PROVENANCE" in set(result.health_frame["issue_code"])
    legacy_row = index.index_frame.iloc[0]
    assert legacy_row["semantics_policy_source"] == ""
    assert bool(legacy_row["semantics_provenance_present"]) is False
    assert bool(legacy_row["semantics_missing_provenance_legacy_warning_only"]) is True


def test_single_symbol_advisory_health_fails_when_semantics_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(
        root,
        "adv001",
        symbol="000001",
        metadata_updates={"semantics_auto_order_allowed": True},
    )

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_fails_when_semantics_source_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(
        root,
        "adv001",
        symbol="000001",
        metadata_updates={"semantics_policy_source": "other_policy"},
    )

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_POLICY_SOURCE_MISMATCH" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_fails_when_demo_review_has_buy_action(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001", record_updates={"advisory_action": "REVIEW_BUY_CANDIDATE"})

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_ACTION_UNSAFE" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_fails_when_leading_zero_symbol_is_lost(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="1", metadata_updates={"symbol": "1"})

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_allows_not_found_without_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(
        root,
        "adv001",
        symbol="999999",
        record_updates={"status": "NOT_FOUND", "advisory_action": "NO_ACTION", "demo_mode": False, "not_strategy_recommendation": False},
        metadata_updates={"status": "NOT_FOUND", "advisory_action": "NO_ACTION", "demo_mode": False, "not_strategy_recommendation": False},
    )

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert "NOT_FOUND_WITH_RECOMMENDATION" not in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_health_fails_not_found_with_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(
        root,
        "adv001",
        symbol="999999",
        record_updates={"status": "NOT_FOUND", "advisory_action": "REVIEW_BUY_CANDIDATE", "demo_mode": False, "not_strategy_recommendation": False},
        metadata_updates={"status": "NOT_FOUND", "advisory_action": "REVIEW_BUY_CANDIDATE", "demo_mode": False, "not_strategy_recommendation": False},
    )

    result = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "NOT_FOUND_WITH_RECOMMENDATION" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_status_summarizes_latest_review(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001", created_at="2024-05-19T00:00:00")
    _write_single_symbol_artifact(root, "adv002", symbol="510300", created_at="2024-05-20T00:00:00")

    result = run_single_symbol_advisory_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_advisory_run_id == "adv002"
    assert result.latest_symbol == "510300"
    assert result.workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED"
    assert result.status == "WARN"
    summary = result.summary_frame.iloc[0]
    assert summary["semantics_policy_source"] == "signal_semantics"
    assert summary["semantics_policy_version"] == "v0.1"
    assert summary["semantics_action"] == "DEMO_ONLY"
    assert bool(summary["semantics_provenance_present"]) is True
    assert bool(summary["semantics_missing_provenance_legacy_warning_only"]) is False


def test_single_symbol_advisory_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_single_symbol_advisory_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_SINGLE_SYMBOL_ADVISORY_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_advisory_run_id == ""


def test_cli_single_symbol_advisory_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001")

    index_code = cli.main(
        [
            "single-symbol-advisory-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "single-symbol-advisory-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "single-symbol-advisory-status",
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
    assert "workflow_stage: DEMO_SINGLE_SYMBOL_ADVISORY_VALIDATED" in status_output.out
    assert "semantics_policy_source: signal_semantics" in status_output.out
    assert "semantics_provenance_present: True" in status_output.out
    assert "No live trading, broker API, order placement, or message delivery was invoked." in status_output.out


def test_single_symbol_artifact_views_do_not_enable_live_or_message_delivery(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory"
    _write_single_symbol_artifact(root, "adv001", symbol="000001")

    index = build_single_symbol_advisory_index(root=root, output_dir=tmp_path / "index")
    health = check_single_symbol_advisory_health(root=root, output_dir=tmp_path / "health")
    status = run_single_symbol_advisory_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False


def _write_single_symbol_artifact(
    root: Path,
    advisory_run_id: str,
    *,
    symbol: str,
    created_at: str = "2024-05-20T00:00:00",
    record_updates: dict | None = None,
    metadata_updates: dict | None = None,
    write_alert_preview: bool = True,
    include_semantics_provenance: bool = True,
) -> None:
    artifact_dir = root / advisory_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    record = _safe_record(advisory_run_id, symbol)
    if not include_semantics_provenance:
        for key in _semantics_provenance("DEMO_ONLY"):
            record.pop(key, None)
    record.update(record_updates or {})
    pd.DataFrame([record], columns=SINGLE_SYMBOL_ADVISORY_COLUMNS).to_csv(
        artifact_dir / "single_symbol_advisory.csv",
        index=False,
    )
    (artifact_dir / "single_symbol_advisory.json").write_text(
        json.dumps({"record": record, "source_row": {}, "known_limitations": []}, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "single_symbol_advisory_report.md").write_text(
        "No live trading, broker API, order placement, or message delivery was invoked.",
        encoding="utf-8",
    )
    if write_alert_preview:
        (artifact_dir / "alert_preview.md").write_text(
            "No message was sent. Manual confirmation required. No auto-order.",
            encoding="utf-8",
        )
    metadata = {
        "advisory_run_id": advisory_run_id,
        "created_at": created_at,
        "status": record["status"],
        "symbol": record["symbol"],
        "advisory_action": record["advisory_action"],
        "source_artifact_path": "candidates.csv",
        "source_candidate_run_id": "candidate123",
        "final_score": record["final_score"],
        "selection_profile": record["selection_profile"],
        "demo_mode": record["demo_mode"],
        "not_strategy_recommendation": record["not_strategy_recommendation"],
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "alert_delivery_enabled": False,
        "output_files": {
            "single_symbol_advisory_report": str(artifact_dir / "single_symbol_advisory_report.md"),
            "single_symbol_advisory_json": str(artifact_dir / "single_symbol_advisory.json"),
            "single_symbol_advisory_csv": str(artifact_dir / "single_symbol_advisory.csv"),
            "alert_preview": str(artifact_dir / "alert_preview.md"),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    if include_semantics_provenance:
        metadata.update(_semantics_provenance(record["advisory_action"]))
    metadata.update(metadata_updates or {})
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _safe_record(advisory_run_id: str, symbol: str) -> dict:
    return {
        "advisory_run_id": advisory_run_id,
        "status": "READY",
        "symbol": symbol,
        "advisory_date": "2024-05-20",
        "source_artifact_path": "candidates.csv",
        "source_candidate_run_id": "candidate123",
        "found_in_candidates": True,
        "found_in_scored_dataset": False,
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "current_action": "NO_TRADE",
        "score_action": "NO_TRADE",
        "final_score": 55.0,
        "advisory_action": "DEMO_ONLY",
        **_semantics_provenance("DEMO_ONLY"),
        "reason_summary": "Demo workflow validation only.",
        "supporting_factors": "{}",
        "risk_notes": "manual confirmation required",
        "data_quality_notes": "local artifact",
        "entry_condition": "No entry condition.",
        "exit_condition": "No exit condition.",
        "invalidation_condition": "Invalid outside demo context.",
        "valid_until": "2024-05-21",
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
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
