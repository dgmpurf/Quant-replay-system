import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.calibration_to_signal_semantics_health import check_calibration_to_signal_semantics_health
from quant_replay_system.calibration_to_signal_semantics_index import build_calibration_to_signal_semantics_index
from quant_replay_system.calibration_to_signal_semantics_status import run_calibration_to_signal_semantics_status


def test_calibration_to_signal_semantics_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001")

    result = build_calibration_to_signal_semantics_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["proposal_run_id"] == "prop001"
    assert int(row["calibration_run_count"]) == 10
    assert int(row["observed_review_buy_candidate_count"]) == 7
    assert row["defaults_changed"] is False
    assert "KEEP_CURRENT_DEFAULTS" in row["proposal_categories"]


def test_calibration_to_signal_semantics_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_calibration_to_signal_semantics_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_calibration_to_signal_semantics_health_passes_safe_proposal(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001")

    result = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_calibration_to_signal_semantics_health_fails_if_defaults_changed(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001", metadata_updates={"defaults_changed": True})

    result = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEFAULTS_CHANGED" in set(result.health_frame["issue_code"])


def test_calibration_to_signal_semantics_health_fails_on_strategy_performance_claim(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(
        root,
        "prop001",
        report_text="This proposal says strategy performance is validated.",
    )

    result = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "STRATEGY_PERFORMANCE_CLAIM_DETECTED" in set(result.health_frame["issue_code"])


def test_calibration_to_signal_semantics_health_fails_on_trading_approval_claim(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001", report_text="This proposal is approved for live trading.")

    result = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "TRADING_APPROVAL_DETECTED" in set(result.health_frame["issue_code"])


def test_calibration_to_signal_semantics_health_fails_if_safety_statement_missing(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001", metadata_updates={"no_live_trading": False})

    result = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MISSING_SAFETY_STATEMENT" in set(result.health_frame["issue_code"])


def test_calibration_to_signal_semantics_status_summarizes_latest_proposal(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001", created_at="2024-05-19T00:00:00")
    _write_proposal_artifact(root, "prop002", created_at="2024-05-20T00:00:00", observed_watch=11)

    result = run_calibration_to_signal_semantics_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_proposal_run_id == "prop002"
    assert result.workflow_stage == "CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE"
    assert result.health_status == "PASS"
    assert "Keep current defaults" in result.next_manual_action
    assert "do not expand BUY review yet" in result.next_manual_action


def test_calibration_to_signal_semantics_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_calibration_to_signal_semantics_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_CALIBRATION_TO_SEMANTICS_PROPOSALS"
    assert result.status == "WARN"
    assert result.latest_proposal_run_id == ""


def test_cli_calibration_to_signal_semantics_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001")

    index_code = cli.main(
        [
            "calibration-to-signal-semantics-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "calibration-to-signal-semantics-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "calibration-to-signal-semantics-status",
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
    assert "workflow_stage: CALIBRATION_TO_SEMANTICS_NEEDS_MORE_EVIDENCE" in status_output.out
    assert "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in status_output.out


def test_calibration_to_signal_semantics_views_do_not_enable_trading_network_or_config_mutation(tmp_path: Path) -> None:
    root = tmp_path / "calibration_to_signal_semantics"
    _write_proposal_artifact(root, "prop001")

    index = build_calibration_to_signal_semantics_index(root=root, output_dir=tmp_path / "index")
    health = check_calibration_to_signal_semantics_health(root=root, output_dir=tmp_path / "health")
    status = run_calibration_to_signal_semantics_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False
    assert status.audit_metadata["config_mutated"] is False


def _write_proposal_artifact(
    root: Path,
    proposal_run_id: str,
    *,
    created_at: str = "2024-05-20T00:00:00",
    observed_watch: int = 8,
    metadata_updates: dict | None = None,
    report_text: str | None = None,
) -> None:
    artifact_dir = root / proposal_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    categories = [
        "KEEP_CURRENT_DEFAULTS",
        "CONSIDER_WATCH_EXPANSION",
        "DO_NOT_EXPAND_BUY_REVIEW_YET",
        "REQUIRE_MORE_EVIDENCE",
        "NEED_MULTI_DATE_VALIDATION",
        "NEED_MORE_SYMBOLS",
        "NEED_BACKTEST_OR_PAPER_EVIDENCE",
    ]
    summary = {
        "proposal_run_id": proposal_run_id,
        "status": "WARN",
        "calibration_root": "outputs/reports/advisory_profile_calibration",
        "semantics_config": "config/default.yaml",
        "calibration_run_count": 10,
        "calibration_row_count": 54,
        "observed_review_buy_candidate_count": 7,
        "observed_watch_count": observed_watch,
        "observed_no_action_count": 6,
        "observed_blocked_count": 24,
        "observed_demo_only_count": 9,
        "semantics_reviewed_buy_min_score": 70.0,
        "semantics_watch_min_score": 55.0,
        "data_quality_fail_gate_observed": True,
        "snapshot_quality_fail_gate_observed": True,
        "risk_block_gate_observed": True,
        "keep_current_defaults": True,
        "defaults_changed": False,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
    }
    summary_path = artifact_dir / "calibration_to_signal_semantics_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    proposals_path = artifact_dir / "calibration_to_signal_semantics_proposals.csv"
    pd.DataFrame(
        [
            {
                "proposal_run_id": proposal_run_id,
                "category": category,
                "severity": "WARN" if category not in {"KEEP_CURRENT_DEFAULTS", "CONSIDER_WATCH_EXPANSION"} else "INFO",
                "recommendation": category,
                "rationale": "Local proposal text only.",
                "evidence": "Local calibration artifacts only.",
                "changes_defaults": False,
            }
            for category in categories
        ]
    ).to_csv(proposals_path, index=False)
    report_path = artifact_dir / "calibration_to_signal_semantics_report.md"
    safe_report = (
        "This is not strategy validation.\n"
        "This report does not approve non-demo trading.\n"
        "REVIEW_BUY_CANDIDATE remains human-review-only.\n"
        "No live trading, broker API, automated order placement, message delivery, LLM API, or external API was invoked.\n"
        "The next safe implementation should focus on WATCH semantics or evidence collection, not automatic buy-review expansion.\n"
        "DO_NOT_EXPAND_BUY_REVIEW_YET\n"
        "REQUIRE_MORE_EVIDENCE\n"
    )
    report_path.write_text(report_text or safe_report, encoding="utf-8")
    metadata = {
        "proposal_run_id": proposal_run_id,
        "status": "WARN",
        "created_at": created_at,
        "calibration_root": "outputs/reports/advisory_profile_calibration",
        "semantics_config": "config/default.yaml",
        "calibration_run_count": 10,
        "proposal_categories": categories,
        "comparison": {
            "observed_review_buy_candidate_count": 7,
            "observed_watch_count": observed_watch,
            "observed_blocked_count": 24,
            "defaults_changed": False,
        },
        "defaults_changed": False,
        "signal_semantics_defaults_changed": False,
        "config_mutated": False,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "llm_api_called": False,
        "approved_for_paper_applied": False,
        "report_only": True,
        "not_strategy_validation": True,
        "review_buy_candidate_is_order": False,
        "output_files": {
            "calibration_to_signal_semantics_report": str(report_path),
            "calibration_to_signal_semantics_summary": str(summary_path),
            "calibration_to_signal_semantics_proposals": str(proposals_path),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    metadata.update(metadata_updates or {})
    if metadata_updates and "defaults_changed" in metadata_updates:
        summary["defaults_changed"] = metadata_updates["defaults_changed"]
        pd.DataFrame([summary]).to_csv(summary_path, index=False)
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
