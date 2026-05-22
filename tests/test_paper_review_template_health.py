import json
import sys
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.paper_review_template_health import (
    PaperReviewTemplateHealthResult,
    build_review_template_health_frame,
    check_review_template_health,
    summarize_review_template_health,
)


def test_clean_review_template_returns_pass(tmp_path: Path) -> None:
    result = check_review_template_health(_clean_updates(), decisions=_decisions(), settings=_settings(tmp_path))

    assert isinstance(result, PaperReviewTemplateHealthResult)
    assert result.status == "PASS"
    assert result.issue_count == 0


def test_missing_required_column_returns_fail(tmp_path: Path) -> None:
    updates = _clean_updates().drop(columns=["reviewer_id"])

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "MISSING_REQUIRED_COLUMN")


def test_unknown_decision_id_returns_fail_when_decisions_provided(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "decision_id"] = "missing-id"

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "UNKNOWN_DECISION_ID")


def test_duplicate_decision_id_returns_fail(tmp_path: Path) -> None:
    updates = pd.concat([_clean_updates(), _clean_updates().iloc[[0]]], ignore_index=True)

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _issue(result.health_frame, "DUPLICATE_DECISION_ID")["severity"] == "ERROR"


def test_invalid_manual_review_status_returns_fail(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "manual_review_status"] = "MAYBE"

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _has_issue(result.health_frame, "INVALID_MANUAL_REVIEW_STATUS")


def test_blank_status_returns_fail_by_default(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "manual_review_status"] = ""

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "FAIL"
    assert _issue(result.health_frame, "BLANK_MANUAL_REVIEW_STATUS")["severity"] == "ERROR"


def test_invalid_review_reason_code_returns_warn_by_default(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "review_reason_code"] = "BAD_REASON"

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _issue(result.health_frame, "INVALID_REVIEW_REASON_CODE")["severity"] == "WARN"


def test_missing_reviewer_id_returns_warn(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "reviewer_id"] = ""

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _issue(result.health_frame, "MISSING_REVIEWER_ID")["severity"] == "WARN"


def test_rejected_decision_with_blank_notes_returns_warn(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[2, "manual_review_status"] = "REJECTED"
    updates.loc[2, "review_reason_code"] = "TECHNICAL_WEAK"
    updates.loc[2, "manual_review_notes"] = ""

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _has_issue(result.health_frame, "REJECTED_WITHOUT_NOTES")


def test_approval_of_non_pass_risk_returns_warn_when_decisions_provided(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[1, "manual_review_status"] = "APPROVED_FOR_PAPER"
    updates.loc[1, "review_reason_code"] = "MANUAL_OVERRIDE"
    updates.loc[1, "manual_review_notes"] = "Manual paper test despite risk flag."

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _has_issue(result.health_frame, "APPROVED_NON_PASS_RISK")


def test_approval_of_low_final_score_returns_warn(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[2, "manual_review_status"] = "APPROVED_FOR_PAPER"
    updates.loc[2, "review_reason_code"] = "MANUAL_OVERRIDE"
    updates.loc[2, "manual_review_notes"] = "Manual score override for paper test."

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))

    assert result.status == "WARN"
    assert _has_issue(result.health_frame, "APPROVED_LOW_SCORE")


def test_input_dataframes_are_not_mutated(tmp_path: Path) -> None:
    updates = _clean_updates()
    decisions = _decisions()
    updates_before = updates.copy(deep=True)
    decisions_before = decisions.copy(deep=True)

    check_review_template_health(updates, decisions=decisions, settings=_settings(tmp_path))

    pd.testing.assert_frame_equal(updates, updates_before)
    pd.testing.assert_frame_equal(decisions, decisions_before)


def test_artifacts_are_written(tmp_path: Path) -> None:
    result = check_review_template_health(_clean_updates(), decisions=_decisions(), settings=_settings(tmp_path))

    assert result.artifact_paths["review_template_health_report"].exists()
    assert result.artifact_paths["review_template_health_issues"].exists()
    assert result.artifact_paths["review_template_health_summary"].exists()
    assert result.artifact_paths["metadata"].exists()


def test_issue_csv_is_readable_by_pandas(tmp_path: Path) -> None:
    updates = _clean_updates()
    updates.loc[0, "review_reason_code"] = "BAD_REASON"

    result = check_review_template_health(updates, decisions=_decisions(), settings=_settings(tmp_path))
    exported = pd.read_csv(result.artifact_paths["review_template_health_issues"])

    assert "issue_code" in exported.columns


def test_summary_csv_is_readable_by_pandas(tmp_path: Path) -> None:
    result = check_review_template_health(_clean_updates(), decisions=_decisions(), settings=_settings(tmp_path))
    exported = pd.read_csv(result.artifact_paths["review_template_health_summary"])

    assert exported.iloc[0]["status"] == "PASS"


def test_metadata_json_is_written(tmp_path: Path) -> None:
    result = check_review_template_health(_clean_updates(), decisions=_decisions(), settings=_settings(tmp_path))
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["health_check_id"] == result.health_check_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_cli_paper_review_template_health_works(tmp_path: Path, capsys) -> None:
    updates_path, decisions_path = _write_updates_and_decisions(tmp_path)

    code = cli.main(
        [
            "paper-review-template-health",
            "--updates",
            str(updates_path),
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "health_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Review template health status: PASS" in output.out
    assert "Report path:" in output.out


def test_cli_exits_nonzero_on_fail(tmp_path: Path, capsys) -> None:
    updates_path, decisions_path = _write_updates_and_decisions(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "manual_review_status"] = "BAD_STATUS"
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-template-health",
            "--updates",
            str(updates_path),
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "health_cli"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Review template health status: FAIL" in output.out


def test_cli_strict_exits_nonzero_on_warn(tmp_path: Path, capsys) -> None:
    updates_path, decisions_path = _write_warn_updates_and_decisions(tmp_path)

    code = cli.main(
        [
            "paper-review-template-health",
            "--updates",
            str(updates_path),
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "health_cli"),
            "--strict",
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Review template health status: WARN" in output.out


def test_cli_allow_warn_exits_zero_on_warn(tmp_path: Path, capsys) -> None:
    updates_path, decisions_path = _write_warn_updates_and_decisions(tmp_path)

    code = cli.main(
        [
            "paper-review-template-health",
            "--updates",
            str(updates_path),
            "--decisions",
            str(decisions_path),
            "--output-dir",
            str(tmp_path / "health_cli"),
            "--strict",
            "--allow-warn",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Review template health status: WARN" in output.out


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = check_review_template_health(_clean_updates(), decisions=_decisions(), settings=_settings(tmp_path))

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def test_health_frame_and_summary_helpers_work() -> None:
    updates = _clean_updates()
    updates.loc[0, "review_reason_code"] = "BAD_REASON"

    frame = build_review_template_health_frame(updates, decisions=_decisions())
    summary = summarize_review_template_health(frame, update_row_count=len(updates), decision_row_count=len(_decisions()))

    assert _has_issue(frame, "INVALID_REVIEW_REASON_CODE")
    assert summary.iloc[0]["status"] == "WARN"


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "paper_review_template_health": settings.paper_review_template_health.model_copy(
                update={"output_dir": tmp_path / "review_template_health", "write_artifacts": True}
            )
        }
    )


def _write_updates_and_decisions(tmp_path: Path) -> tuple[Path, Path]:
    updates_path = tmp_path / "review_updates_template.csv"
    decisions_path = tmp_path / "decisions.csv"
    _clean_updates().to_csv(updates_path, index=False)
    _decisions().to_csv(decisions_path, index=False)
    return updates_path, decisions_path


def _write_warn_updates_and_decisions(tmp_path: Path) -> tuple[Path, Path]:
    updates_path, decisions_path = _write_updates_and_decisions(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "review_reason_code"] = "BAD_REASON"
    updates.to_csv(updates_path, index=False)
    return updates_path, decisions_path


def _clean_updates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_id": "d1",
                "manual_review_status": "APPROVED_FOR_PAPER",
                "manual_review_notes": "Score and risk confirmed.",
                "reviewer_id": "reviewer-a",
                "review_reason_code": "SCORE_CONFIRMED",
                "symbol": "AAA",
            },
            {
                "decision_id": "d2",
                "manual_review_status": "REJECTED",
                "manual_review_notes": "Risk block respected.",
                "reviewer_id": "reviewer-a",
                "review_reason_code": "RISK_TOO_HIGH",
                "symbol": "BBB",
            },
            {
                "decision_id": "d3",
                "manual_review_status": "WATCH_ONLY",
                "manual_review_notes": "Low score, watch only.",
                "reviewer_id": "reviewer-a",
                "review_reason_code": "WATCHLIST_ONLY",
                "symbol": "CCC",
            },
            {
                "decision_id": "d4",
                "manual_review_status": "PENDING_REVIEW",
                "manual_review_notes": "Review later.",
                "reviewer_id": "reviewer-a",
                "review_reason_code": "OTHER",
                "symbol": "DDD",
            },
        ]
    )


def _decisions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_id": "d1",
                "symbol": "AAA",
                "name": "AAA Fund",
                "final_score": 82.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
            },
            {
                "decision_id": "d2",
                "symbol": "BBB",
                "name": "BBB Fund",
                "final_score": 55.0,
                "risk_precheck_status": "BLOCK",
                "risk_precheck_reason": "risk block",
            },
            {
                "decision_id": "d3",
                "symbol": "CCC",
                "name": "CCC Fund",
                "final_score": 64.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
            },
            {
                "decision_id": "d4",
                "symbol": "DDD",
                "name": "DDD Fund",
                "final_score": 85.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
            },
        ]
    )


def _has_issue(frame: pd.DataFrame, issue_code: str) -> bool:
    return bool((frame["issue_code"] == issue_code).any()) if not frame.empty else False


def _issue(frame: pd.DataFrame, issue_code: str) -> dict:
    rows = frame.loc[frame["issue_code"] == issue_code]
    assert not rows.empty
    return rows.iloc[0].to_dict()
