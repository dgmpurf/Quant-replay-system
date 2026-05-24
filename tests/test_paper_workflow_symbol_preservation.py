from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.current_to_paper_handoff import run_current_to_paper_handoff
from quant_replay_system.current_to_paper_review_handoff import run_current_to_paper_review_handoff
from quant_replay_system.daily_paper_runner import run_daily_paper_trading
from quant_replay_system.paper_review import apply_paper_review_updates
from quant_replay_system.paper_review_template_health import check_review_template_health


PAPER_DATE = "2024-05-20"
EXPECTED_SYMBOLS = {"000001", "510300"}


def test_leading_zero_symbols_survive_paper_workflow_watch_only_csv_boundaries(tmp_path: Path) -> None:
    candidates_path = _write_synthetic_candidates(tmp_path)
    settings = _settings(tmp_path)

    handoff = run_current_to_paper_handoff(
        candidates_path=candidates_path,
        paper_date=PAPER_DATE,
        config=settings,
    )
    decisions_path = handoff.paper_artifact_paths["decisions"]
    decisions = _assert_symbols_preserved(decisions_path)
    assert set(decisions["manual_review_status"]) == {"PENDING_REVIEW"}
    assert set(decisions["action"]) == {"SKIP"}

    review_handoff = run_current_to_paper_review_handoff(
        decisions_path=decisions_path,
        output_dir=tmp_path / "review_handoff",
        config=settings,
    )
    review_template_path = review_handoff.template_path
    review_template = _assert_symbols_preserved(review_template_path)
    assert set(review_template["manual_review_status"]) == {"PENDING_REVIEW"}
    assert "APPROVED_FOR_PAPER" not in set(review_template["manual_review_status"])

    watch_updates_path = tmp_path / "watch_only_review_updates.csv"
    watch_updates = review_template.copy(deep=True)
    watch_updates["manual_review_status"] = "WATCH_ONLY"
    watch_updates["reviewer_id"] = "regression_test"
    watch_updates["review_reason_code"] = "WATCHLIST_ONLY"
    watch_updates["manual_review_notes"] = "Regression test only; not a trading recommendation."
    watch_updates.to_csv(watch_updates_path, index=False)
    _assert_symbols_preserved(watch_updates_path)

    health = check_review_template_health(
        watch_updates_path,
        decisions=decisions_path,
        settings=settings,
    )
    assert health.status == "PASS"
    assert health.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False

    review = apply_paper_review_updates(
        decisions_path,
        watch_updates_path,
        reviewer_id="regression_test",
        settings=settings,
        template_health_metadata=health.audit_metadata,
    )
    reviewed_decisions_path = review.artifact_paths["reviewed_decisions"]
    reviewed_decisions = _assert_symbols_preserved(reviewed_decisions_path)
    assert set(reviewed_decisions["manual_review_status"]) == {"WATCH_ONLY"}
    assert "APPROVED_FOR_PAPER" not in set(reviewed_decisions["manual_review_status"])
    assert review.audit_metadata["live_trading_enabled"] is False
    assert review.audit_metadata["broker_api_invoked"] is False

    daily = run_daily_paper_trading(
        PAPER_DATE,
        reviewed_decisions_path=reviewed_decisions_path,
        config=settings,
    )
    daily_decisions = _assert_symbols_preserved(daily.artifact_paths["decisions"])
    assert set(daily_decisions["manual_review_status"]) == {"WATCH_ONLY"}
    assert "APPROVED_FOR_PAPER" not in set(daily_decisions["manual_review_status"])
    assert daily.reviewed_decisions_used is True
    assert daily.open_position_count == 0
    assert daily.closed_trade_count == 0
    assert daily.audit_metadata["live_trading_enabled"] is False
    assert daily.audit_metadata["broker_api_invoked"] is False


def test_cli_paper_workflow_preserves_leading_zero_symbols(tmp_path: Path, capsys) -> None:
    candidates_path = _write_synthetic_candidates(tmp_path)

    code = cli.main(
        [
            "current-to-paper",
            "--candidates",
            str(candidates_path),
            "--paper-date",
            PAPER_DATE,
            "--output-dir",
            str(tmp_path / "cli_current_to_paper"),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "No live trading or broker API was invoked." in output.out
    decisions_path = _single_path(tmp_path / "cli_current_to_paper" / "paper_daily", "*/decisions.csv")
    decisions = _assert_symbols_preserved(decisions_path)
    assert set(decisions["manual_review_status"]) == {"PENDING_REVIEW"}
    assert "APPROVED_FOR_PAPER" not in set(decisions["manual_review_status"])

    code = cli.main(
        [
            "current-to-paper-review",
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "cli_review_handoff"),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "No live trading or broker API was invoked." in output.out
    review_template_path = _single_path(tmp_path / "cli_review_handoff", "*/review_updates_template.csv")
    review_template = _assert_symbols_preserved(review_template_path)
    assert set(review_template["manual_review_status"]) == {"PENDING_REVIEW"}

    watch_updates_path = tmp_path / "cli_watch_only_review_updates.csv"
    watch_updates = review_template.copy(deep=True)
    watch_updates["manual_review_status"] = "WATCH_ONLY"
    watch_updates["reviewer_id"] = "cli_regression_test"
    watch_updates["review_reason_code"] = "WATCHLIST_ONLY"
    watch_updates["manual_review_notes"] = "CLI regression test only; not a trading recommendation."
    watch_updates.to_csv(watch_updates_path, index=False)
    _assert_symbols_preserved(watch_updates_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(watch_updates_path),
            "--health-check",
            "--output-dir",
            str(tmp_path / "cli_paper_review"),
            "--template-health-output-dir",
            str(tmp_path / "cli_template_health"),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "Template health status: PASS" in output.out
    assert "approved_count: 0" in output.out
    assert "watch_only_count: 2" in output.out
    assert "No live trading or broker API was invoked." in output.out
    reviewed_decisions_path = _single_path(tmp_path / "cli_paper_review", "*/reviewed_decisions.csv")
    reviewed_decisions = _assert_symbols_preserved(reviewed_decisions_path)
    assert set(reviewed_decisions["manual_review_status"]) == {"WATCH_ONLY"}
    assert "APPROVED_FOR_PAPER" not in set(reviewed_decisions["manual_review_status"])

    code = cli.main(
        [
            "paper-daily",
            "--date",
            PAPER_DATE,
            "--reviewed-decisions",
            str(reviewed_decisions_path),
            "--output-dir",
            str(tmp_path / "cli_paper_daily_reviewed"),
            "--journal-id",
            "cli-symbol-preservation",
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "reviewed_decisions_used: True" in output.out
    assert "open_position_count: 0" in output.out
    assert "closed_trade_count: 0" in output.out
    assert "No live trading or broker API was invoked." in output.out
    daily_decisions_path = (
        tmp_path
        / "cli_paper_daily_reviewed"
        / f"{PAPER_DATE}_cli-symbol-preservation"
        / "decisions.csv"
    )
    daily_decisions = _assert_symbols_preserved(daily_decisions_path)
    assert set(daily_decisions["manual_review_status"]) == {"WATCH_ONLY"}
    assert "APPROVED_FOR_PAPER" not in set(daily_decisions["manual_review_status"])


def _write_synthetic_candidates(tmp_path: Path) -> Path:
    candidates = pd.DataFrame(
        [
            {
                "decision_date": PAPER_DATE,
                "rank": 1,
                "symbol": "000001",
                "name": "Ping An Bank",
                "action": "NO_TRADE",
                "score_action": "NO_TRADE",
                "final_score": 55.6,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "workflow validation",
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
                "source_run_id": "offline-batch-regression",
                "source_report_path": "outputs/reports/current_candidates/offline-batch-regression/report.md",
            },
            {
                "decision_date": PAPER_DATE,
                "rank": 2,
                "symbol": "510300",
                "name": "ETF 510300",
                "action": "NO_TRADE",
                "score_action": "NO_TRADE",
                "final_score": 52.9,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "workflow validation",
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
                "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
                "source_run_id": "offline-batch-regression",
                "source_report_path": "outputs/reports/current_candidates/offline-batch-regression/report.md",
            },
        ]
    )
    path = tmp_path / "candidates.csv"
    candidates.to_csv(path, index=False)
    return path


def _assert_symbols_preserved(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8")
    assert "000001" in text
    assert "1.0" not in text
    frame = pd.read_csv(path, dtype={"symbol": str}, keep_default_na=False)
    assert set(frame["symbol"]) == EXPECTED_SYMBOLS
    assert "1" not in set(frame["symbol"])
    assert "1.0" not in set(frame["symbol"])
    return frame


def _single_path(root: Path, pattern: str) -> Path:
    matches = sorted(root.glob(pattern))
    assert len(matches) == 1
    return matches[0]


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "current_to_paper_handoff": settings.current_to_paper_handoff.model_copy(
                update={"output_dir": tmp_path / "current_to_paper_handoff", "write_artifacts": True}
            ),
            "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                update={"output_dir": tmp_path / "current_to_paper_review_handoff", "write_artifacts": True}
            ),
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "paper_daily", "write_artifacts": True}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "paper_reconciliation", "write_artifacts": True}
            ),
            "paper_review": settings.paper_review.model_copy(
                update={"output_dir": tmp_path / "paper_review", "write_artifacts": True}
            ),
            "paper_review_template_health": settings.paper_review_template_health.model_copy(
                update={"output_dir": tmp_path / "paper_review_template_health", "write_artifacts": True}
            ),
        }
    )
