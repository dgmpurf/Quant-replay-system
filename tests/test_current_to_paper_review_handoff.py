import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import CurrentToPaperReviewHandoffSettings, load_settings
from quant_replay_system.current_to_paper_handoff import run_current_to_paper_handoff
from quant_replay_system.current_to_paper_review_handoff import (
    CurrentToPaperReviewHandoffResult,
    build_review_updates_template,
    run_current_to_paper_review_handoff,
)
from quant_replay_system.paper_review import apply_paper_review_updates
from quant_replay_system.paper_trading import create_paper_decision_log


PAPER_DATE = "2024-05-20"


def test_review_handoff_creates_template_from_decisions_dataframe(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert isinstance(result, CurrentToPaperReviewHandoffResult)
    assert result.decision_count == 3
    assert len(result.review_updates_template) == 3


def test_review_handoff_creates_template_from_decisions_csv(tmp_path: Path) -> None:
    decisions_path = _decisions_path(tmp_path)

    result = run_current_to_paper_review_handoff(
        decisions_path=decisions_path,
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert result.decision_count == 3
    assert result.template_path.exists()


def test_review_handoff_preserves_leading_zero_symbols_from_decisions_csv(tmp_path: Path) -> None:
    decisions_path = tmp_path / "decisions.csv"
    decisions = _decisions()
    decisions.loc[0, "symbol"] = "000001"
    decisions.to_csv(decisions_path, index=False)

    result = run_current_to_paper_review_handoff(
        decisions_path=decisions_path,
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert result.review_updates_template.iloc[0]["symbol"] == "000001"


def test_review_handoff_can_load_from_handoff_artifact_directory(tmp_path: Path) -> None:
    handoff = _current_to_paper_handoff(tmp_path)

    result = run_current_to_paper_review_handoff(
        handoff_artifact_dir=handoff.handoff_artifact_paths["artifact_dir"],
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert result.decision_count == 3
    assert result.audit_metadata["source_metadata"]["handoff_id"] == handoff.handoff_id


def test_template_includes_required_review_columns(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        reviewer_id="reviewer-a",
        config=_settings(tmp_path),
    )

    for column in [
        "decision_id",
        "symbol",
        "manual_review_status",
        "manual_review_notes",
        "reviewer_id",
        "review_reason_code",
    ]:
        assert column in result.review_updates_template.columns
    assert set(result.review_updates_template["reviewer_id"]) == {"reviewer-a"}


def test_default_manual_review_status_remains_pending_review(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert set(result.review_updates_template["manual_review_status"]) == {"PENDING_REVIEW"}


def test_suggested_status_column_does_not_auto_approve_by_default(tmp_path: Path) -> None:
    template = build_review_updates_template(
        _decisions(),
        settings=CurrentToPaperReviewHandoffSettings(auto_approve_above_score=80.0),
    )

    high_score = template.loc[template["symbol"] == "AAA"].iloc[0]
    assert high_score["suggested_manual_review_status"] == "APPROVED_FOR_PAPER"
    assert high_score["manual_review_status"] == "PENDING_REVIEW"


def test_high_final_score_can_produce_suggested_status_without_changing_actual_status(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings = settings.model_copy(
        update={
            "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                update={"auto_approve_above_score": 80.0}
            )
        }
    )

    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=settings,
    )

    row = result.review_updates_template.loc[result.review_updates_template["symbol"] == "AAA"].iloc[0]
    assert row["suggested_manual_review_status"] == "APPROVED_FOR_PAPER"
    assert row["manual_review_status"] == "PENDING_REVIEW"


def test_low_final_score_can_produce_suggested_reject_reason_without_changing_status(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings = settings.model_copy(
        update={
            "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                update={"auto_reject_below_score": 60.0}
            )
        }
    )

    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=settings,
    )

    row = result.review_updates_template.loc[result.review_updates_template["symbol"] == "CCC"].iloc[0]
    assert row["suggested_manual_review_status"] == "REJECTED"
    assert row["review_reason_code"] == "RISK_TOO_HIGH"
    assert row["manual_review_status"] == "PENDING_REVIEW"


def test_template_can_be_used_by_existing_paper_review_decisions_flow(tmp_path: Path) -> None:
    decisions = _decisions()
    result = run_current_to_paper_review_handoff(
        decisions=decisions,
        output_dir=tmp_path / "review_handoff",
        reviewer_id="reviewer-a",
        config=_settings(tmp_path),
    )

    review = apply_paper_review_updates(
        decisions,
        result.review_updates_template,
        reviewer_id="reviewer-a",
        settings=_settings(tmp_path),
    )

    assert len(review.reviewed_decisions) == len(decisions)
    assert set(review.reviewed_decisions["manual_review_status"]) == {"PENDING_REVIEW"}


def test_review_handoff_artifacts_are_written(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert result.template_path.exists()
    assert result.report_path.exists()
    assert result.metadata_path.exists()


def test_metadata_json_is_written(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["review_handoff_id"] == result.review_handoff_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_report_is_written(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )
    content = result.report_path.read_text(encoding="utf-8")

    assert "# Current Candidate To Paper Review Handoff" in content
    assert "No broker or live trading integration was invoked" in content


def test_cli_current_to_paper_review_works_with_decisions(tmp_path: Path, capsys) -> None:
    decisions_path = _decisions_path(tmp_path)

    code = cli.main(
        [
            "current-to-paper-review",
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "review_cli"),
            "--reviewer-id",
            "cli-reviewer",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "template_path:" in output.out
    assert "report_path:" in output.out


def test_cli_current_to_paper_review_works_with_handoff_dir(tmp_path: Path, capsys) -> None:
    handoff = _current_to_paper_handoff(tmp_path)

    code = cli.main(
        [
            "current-to-paper-review",
            "--handoff-dir",
            str(handoff.handoff_artifact_paths["artifact_dir"]),
            "--output-dir",
            str(tmp_path / "review_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "decision_count: 3" in output.out


def test_cli_prints_no_live_trading_statement(tmp_path: Path, capsys) -> None:
    decisions_path = _decisions_path(tmp_path)

    code = cli.main(
        [
            "current-to-paper-review",
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "review_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "No live trading or broker API was invoked." in output.out


def test_output_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    decisions_path = _decisions_path(tmp_path)
    first = run_current_to_paper_review_handoff(
        decisions_path=decisions_path,
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )
    second = run_current_to_paper_review_handoff(
        decisions_path=decisions_path,
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert first.review_handoff_id == second.review_handoff_id
    assert first.template_path == second.template_path
    assert first.review_updates_template.to_dict("records") == second.review_updates_template.to_dict("records")


def test_no_live_trading_or_network_is_invoked(tmp_path: Path) -> None:
    result = run_current_to_paper_review_handoff(
        decisions=_decisions(),
        output_dir=tmp_path / "review_handoff",
        config=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["current_to_paper_review_handoff_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                update={"output_dir": tmp_path / "review_handoff", "write_artifacts": True}
            ),
            "current_to_paper_handoff": settings.current_to_paper_handoff.model_copy(
                update={"output_dir": tmp_path / "handoff", "write_artifacts": True}
            ),
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": tmp_path / "paper_daily", "write_artifacts": True}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": tmp_path / "reconciliation", "write_artifacts": True}
            ),
            "paper_review": settings.paper_review.model_copy(
                update={"output_dir": tmp_path / "paper_review", "write_artifacts": True}
            ),
        }
    )


def _decisions_path(tmp_path: Path) -> Path:
    path = tmp_path / "decisions.csv"
    _decisions().to_csv(path, index=False)
    return path


def _decisions() -> pd.DataFrame:
    decisions = create_paper_decision_log(
        _candidates(),
        decision_date=PAPER_DATE,
        source_run_id="current-run",
        source_report_path="outputs/reports/current_candidates/current-run/current_candidates_report.md",
        manual_review_status="PENDING_REVIEW",
    )
    return decisions


def _candidates_path(tmp_path: Path) -> Path:
    path = tmp_path / "candidates.csv"
    _candidates().to_csv(path, index=False)
    return path


def _current_to_paper_handoff(tmp_path: Path):
    return run_current_to_paper_handoff(
        candidates_path=_candidates_path(tmp_path),
        paper_date=PAPER_DATE,
        config=_settings(tmp_path),
    )


def _candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_date": PAPER_DATE,
                "rank": 1,
                "symbol": "AAA",
                "name": "AAA Fund",
                "final_score": 88.0,
                "action": "PAPER_TRADE",
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "source_run_id": "current-run",
                "source_report_path": "outputs/reports/current_candidates/current-run/current_candidates_report.md",
            },
            {
                "decision_date": PAPER_DATE,
                "rank": 2,
                "symbol": "BBB",
                "name": "BBB Fund",
                "final_score": 72.0,
                "action": "OBSERVE",
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "source_run_id": "current-run",
                "source_report_path": "outputs/reports/current_candidates/current-run/current_candidates_report.md",
            },
            {
                "decision_date": PAPER_DATE,
                "rank": 3,
                "symbol": "CCC",
                "name": "CCC Fund",
                "final_score": 52.0,
                "action": "NO_TRADE",
                "risk_precheck_status": "BLOCK",
                "risk_precheck_reason": "risk too high",
                "source_run_id": "current-run",
                "source_report_path": "outputs/reports/current_candidates/current-run/current_candidates_report.md",
            },
        ]
    )
