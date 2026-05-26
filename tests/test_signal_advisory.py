import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.signal_advisory import (
    SIGNAL_COLUMNS,
    build_signal_advisory_from_candidates,
    classify_signal_action,
)


def test_demo_candidates_become_demo_only_not_buy(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    result = build_signal_advisory_from_candidates(
        candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.signal_count == 2
    assert set(result.signals["advisory_action"]) == {"DEMO_ONLY"}
    assert "REVIEW_BUY_CANDIDATE" not in set(result.signals["advisory_action"])
    assert result.signals["not_strategy_recommendation"].map(bool).all()


def test_signal_output_preserves_leading_zero_symbols(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    result = build_signal_advisory_from_candidates(
        candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    output = pd.read_csv(result.artifact_paths["signals"], dtype={"symbol": str})

    assert "000001" in output["symbol"].tolist()
    assert set(SIGNAL_COLUMNS).issubset(output.columns)


def test_alert_preview_includes_manual_confirmation_and_no_auto_order(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    result = build_signal_advisory_from_candidates(
        candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )
    preview = result.artifact_paths["signal_alert_preview"].read_text(encoding="utf-8")

    assert "Manual confirmation required" in preview
    assert "No auto-order" in preview
    assert "No message was sent" in preview


def test_safety_flags_are_written_to_signals_and_metadata(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    result = build_signal_advisory_from_candidates(
        candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )
    metadata_payload = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert result.signals["auto_order_allowed"].eq(False).all()
    assert result.signals["no_live_trading"].eq(True).all()
    assert result.signals["no_broker_api"].eq(True).all()
    assert metadata_payload["auto_order_allowed"] is False
    assert metadata_payload["no_live_trading"] is True
    assert metadata_payload["no_broker_api"] is True
    assert metadata_payload["message_sent"] is False
    assert metadata_payload["alert_delivery_enabled"] is False


def test_preliminary_non_demo_actions_still_require_manual_review() -> None:
    row = {
        "selection_profile": "default",
        "demo_mode": False,
        "not_strategy_recommendation": False,
        "score_action": "PAPER_TRADE",
        "action": "PAPER_TRADE",
        "risk_precheck_status": "PASS",
    }

    assert classify_signal_action(row) == "REVIEW_BUY_CANDIDATE"


def test_demo_action_overrides_preliminary_buy_signal() -> None:
    row = {
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "score_action": "PAPER_TRADE",
        "action": "PAPER_TRADE",
        "risk_precheck_status": "PASS",
    }

    assert classify_signal_action(row) == "DEMO_ONLY"


def test_cli_signal_advisory_works(tmp_path: Path, capsys) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    code = cli.main(
        [
            "signal-advisory",
            "--candidates",
            str(candidates),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(tmp_path / "signals"),
            "--alert-preview",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "signal_run_id:" in output.out
    assert "signal_count: 2" in output.out
    assert "DEMO_ONLY: 2" in output.out
    assert "alert_preview_path:" in output.out
    assert "No alert message was sent." in output.out


def test_no_live_trading_broker_network_or_message_sending(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    result = build_signal_advisory_from_candidates(
        candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["message_delivery_enabled"] is False
    assert result.audit_metadata["message_sent"] is False


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "signal_advisory": settings.signal_advisory.model_copy(
                update={"output_dir": tmp_path / "signals", "write_artifacts": True}
            )
        }
    )


def _write_demo_candidate_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "current_candidates" / "2024-05-20_etf_core_demo123"
    artifact_dir.mkdir(parents=True)
    candidates = pd.DataFrame(
        [
            {
                "rank": 1,
                "symbol": "000001",
                "name": "Ping An Bank",
                "instrument_type": "STOCK",
                "decision_date": "2024-05-20",
                "final_score": 82.5,
                "score_action": "PAPER_TRADE",
                "action": "PAPER_TRADE",
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "score_breakdown": '{"final_score":82.5}',
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
                "current_candidate_run_id": "demo123",
                "source_run_id": "demo123",
                "source_report_path": str(artifact_dir / "current_candidates_report.md"),
            },
            {
                "rank": 2,
                "symbol": "510300",
                "name": "CSI 300 ETF",
                "instrument_type": "ETF",
                "decision_date": "2024-05-20",
                "final_score": 55.0,
                "score_action": "NO_TRADE",
                "action": "NO_TRADE",
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "score_breakdown": '{"final_score":55.0}',
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
                "current_candidate_run_id": "demo123",
                "source_run_id": "demo123",
                "source_report_path": str(artifact_dir / "current_candidates_report.md"),
            },
        ]
    )
    candidates_path = artifact_dir / "candidates.csv"
    candidates.to_csv(candidates_path, index=False)
    report_path = artifact_dir / "current_candidates_report.md"
    report_path.write_text("# Current Candidate Report\n", encoding="utf-8")
    metadata = {
        "run_id": "demo123",
        "decision_date": "2024-05-20T00:00:00",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "audit_metadata": {
            "selection_profile": "demo",
            "demo_mode": True,
            "not_strategy_recommendation": True,
            "snapshot_quality_manifest_path": "snapshots/demo_manifest.json",
        },
        "warnings": [
            "Demo candidates are for local artifact/workflow validation only and are not strategy recommendations."
        ],
    }
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return candidates_path, metadata_path
