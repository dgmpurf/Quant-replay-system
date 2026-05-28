import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.calibration_to_signal_semantics import (
    build_calibration_to_semantics_proposal,
    run_calibration_to_signal_semantics,
)


def test_report_compares_semantics_defaults_to_calibration_profiles(tmp_path: Path) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(calibration_root, "demo1", profile="balanced", demo_only=3)
    _write_calibration_run(calibration_root, "con1", profile="conservative", review_buy=1, watch=2, no_action=1)
    _write_calibration_run(calibration_root, "bal1", profile="balanced", review_buy=1, watch=2, no_action=1)
    _write_calibration_run(calibration_root, "exp1", profile="experimental", review_buy=2, watch=1, no_action=1)

    result = run_calibration_to_signal_semantics(
        calibration_root=calibration_root,
        semantics_config=Path("config/default.yaml"),
        output_dir=tmp_path / "proposal",
    )
    summary = result.summary_frame.iloc[0].to_dict()

    assert summary["semantics_reviewed_buy_min_score"] == 70.0
    assert summary["semantics_watch_min_score"] == 55.0
    assert summary["balanced_reviewed_buy_min_score"] == 70.0
    assert summary["experimental_watch_min_score"] == 50.0
    assert "KEEP_CURRENT_DEFAULTS" in result.proposal_categories
    assert summary["defaults_changed"] is False


def test_demo_only_calibration_requires_more_evidence_not_threshold_change(tmp_path: Path) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(calibration_root, "demo1", profile="balanced", row_count=9, demo_only=9)

    result = build_calibration_to_semantics_proposal(
        calibration_root=calibration_root,
        semantics_config=Path("config/default.yaml"),
        output_dir=tmp_path / "proposal",
    )

    assert "REQUIRE_MORE_EVIDENCE" in result.proposal_categories
    assert "DO_NOT_EXPAND_BUY_REVIEW_YET" in result.proposal_categories
    assert result.defaults_changed is False


def test_synthetic_review_buy_does_not_become_production_recommendation(tmp_path: Path) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(calibration_root, "bal1", profile="balanced", review_buy=1, watch=1, blocked=1)

    result = run_calibration_to_signal_semantics(
        calibration_root=calibration_root,
        output_dir=tmp_path / "proposal",
    )
    report = result.artifact_paths["calibration_to_signal_semantics_report"].read_text(encoding="utf-8")

    assert "DO_NOT_EXPAND_BUY_REVIEW_YET" in result.proposal_categories
    assert "This is not strategy validation." in report
    assert "REVIEW_BUY_CANDIDATE remains human-review-only" in report
    assert "does not approve non-demo trading" in report


def test_quality_fail_runs_are_recognized_as_mandatory_gates(tmp_path: Path) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(
        calibration_root,
        "dqfail",
        profile="balanced",
        row_count=2,
        blocked=2,
        issue_codes=["DATA_QUALITY_FAILED", "DATA_QUALITY_FAILED"],
    )
    _write_calibration_run(
        calibration_root,
        "sqfail",
        profile="balanced",
        row_count=2,
        blocked=2,
        issue_codes=["SNAPSHOT_QUALITY_FAILED", "SNAPSHOT_QUALITY_FAILED"],
    )

    result = run_calibration_to_signal_semantics(
        calibration_root=calibration_root,
        output_dir=tmp_path / "proposal",
    )
    summary = result.summary_frame.iloc[0].to_dict()

    assert summary["data_quality_fail_gate_observed"] is True
    assert summary["snapshot_quality_fail_gate_observed"] is True
    assert "KEEP_CURRENT_DEFAULTS" in result.proposal_categories


def test_output_keeps_report_only_safety_flags(tmp_path: Path) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(calibration_root, "bal1", profile="balanced", review_buy=1, watch=1)

    result = run_calibration_to_signal_semantics(
        calibration_root=calibration_root,
        output_dir=tmp_path / "proposal",
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["requires_manual_confirmation"] is True
    assert metadata["auto_order_allowed"] is False
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True
    assert metadata["no_message_sent"] is True
    assert metadata["external_api_called"] is False
    assert metadata["llm_api_called"] is False
    assert metadata["defaults_changed"] is False


def test_cli_calibration_to_signal_semantics_works(tmp_path: Path, capsys) -> None:
    calibration_root = tmp_path / "advisory_profile_calibration"
    _write_calibration_run(calibration_root, "demo1", profile="balanced", demo_only=3)
    _write_calibration_run(calibration_root, "bal1", profile="balanced", review_buy=1, watch=1)

    code = cli.main(
        [
            "calibration-to-signal-semantics",
            "--calibration-root",
            str(calibration_root),
            "--semantics-config",
            "config/default.yaml",
            "--output-dir",
            str(tmp_path / "proposal"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "proposal_run_id:" in output.out
    assert "KEEP_CURRENT_DEFAULTS" in output.out
    assert "defaults_changed: False" in output.out
    assert "No live trading, broker API, order placement, message delivery, LLM API, or external API was invoked." in output.out


def _write_calibration_run(
    root: Path,
    run_id: str,
    *,
    profile: str,
    row_count: int = 4,
    review_buy: int = 0,
    watch: int = 0,
    no_action: int = 0,
    blocked: int = 0,
    demo_only: int = 0,
    issue_codes: list[str] | None = None,
) -> None:
    artifact_dir = root / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    reviewed_buy_min_score, watch_min_score = {
        "conservative": (75.0, 60.0),
        "balanced": (70.0, 55.0),
        "experimental": (65.0, 50.0),
    }[profile]
    issue_codes = issue_codes or []
    summary = {
        "calibration_run_id": run_id,
        "status": "WARN" if issue_codes or demo_only else "PASS",
        "input_path": f"fixtures/{run_id}.csv",
        "input_type": "candidates",
        "profile": profile,
        "row_count": row_count,
        "symbol_count": max(1, row_count - (1 if issue_codes else 0)),
        "final_score_min": 50.0,
        "final_score_median": 65.0,
        "final_score_max": 88.0,
        "review_buy_candidate_count": review_buy,
        "watch_count": watch,
        "no_action_count": no_action,
        "blocked_count": blocked,
        "demo_only_count": demo_only,
        "issue_count": len(issue_codes),
        "risk_precheck_status_counts": '{"PASS": 1}',
        "score_action_counts": '{"PAPER_TRADE": 1}',
        "action_counts": '{"PAPER_TRADE": 1}',
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
    }
    summary_path = artifact_dir / "advisory_profile_calibration_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    calibration_path = artifact_dir / "advisory_profile_calibration.csv"
    pd.DataFrame(
        [
            {
                "calibration_run_id": run_id,
                "symbol": "000001",
                "profile": profile,
                "simulated_advisory_label": "REVIEW_BUY_CANDIDATE" if review_buy else "WATCH",
                "final_score": 88.0,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
                "calibration_only": True,
                "not_trading_recommendation": True,
                "issue_codes": ";".join(issue_codes),
            }
        ]
    ).to_csv(calibration_path, index=False)
    issues_path = artifact_dir / "advisory_profile_calibration_issues.csv"
    pd.DataFrame(
        [
            {
                "calibration_run_id": run_id,
                "source_row_index": index,
                "symbol": "000001",
                "severity": "ERROR",
                "issue_code": issue_code,
                "issue_message": issue_code,
                "suggested_action": "Keep gate mandatory.",
            }
            for index, issue_code in enumerate(issue_codes)
        ],
        columns=[
            "calibration_run_id",
            "source_row_index",
            "symbol",
            "severity",
            "issue_code",
            "issue_message",
            "suggested_action",
        ],
    ).to_csv(issues_path, index=False)
    report_path = artifact_dir / "advisory_profile_calibration_report.md"
    report_path.write_text("# Calibration fixture\n", encoding="utf-8")
    metadata = {
        "calibration_run_id": run_id,
        "status": summary["status"],
        "created_at": "2024-05-20T00:00:00",
        "profile": profile,
        "profile_definition": {
            "reviewed_buy_min_score": reviewed_buy_min_score,
            "watch_min_score": watch_min_score,
            "require_data_quality_pass": True,
            "require_snapshot_quality_pass": True,
        },
        "row_count": row_count,
        "label_counts": {
            "REVIEW_BUY_CANDIDATE": review_buy,
            "WATCH": watch,
            "NO_ACTION": no_action,
            "BLOCKED": blocked,
            "DEMO_ONLY": demo_only,
        },
        "issue_count": len(issue_codes),
        "output_files": {
            "advisory_profile_calibration": str(calibration_path),
            "advisory_profile_calibration_summary": str(summary_path),
            "advisory_profile_calibration_issues": str(issues_path),
            "advisory_profile_calibration_report": str(report_path),
            "metadata": str(artifact_dir / "metadata.json"),
        },
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "external_api_called": False,
        "llm_api_called": False,
        "calibration_only": True,
        "not_trading_recommendation": True,
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
