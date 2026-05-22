import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.paper_review import (
    PaperReviewResult,
    apply_paper_review_updates,
    load_paper_decisions,
    summarize_review_status,
)
from quant_replay_system.paper_trading import create_paper_decision_log


PAPER_DATE = "2024-03-05"


def test_review_updates_change_pending_review_to_approved(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")])

    result = apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))

    assert isinstance(result, PaperReviewResult)
    assert result.reviewed_decisions.loc[0, "manual_review_status"] == "APPROVED_FOR_PAPER"
    assert result.reviewed_decisions.loc[0, "reviewer_id"] == "reviewer-a"


def test_review_updates_can_set_rejected(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(1, "REJECTED", "RISK_TOO_HIGH")])

    result = apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))

    row = result.reviewed_decisions.loc[result.reviewed_decisions["symbol"] == "BBB"].iloc[0]
    assert row["manual_review_status"] == "REJECTED"
    assert row["review_reason_code"] == "RISK_TOO_HIGH"


def test_review_updates_can_set_watch_only(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(2, "WATCH_ONLY", "WATCHLIST_ONLY")])

    result = apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))

    row = result.reviewed_decisions.loc[result.reviewed_decisions["symbol"] == "CCC"].iloc[0]
    assert row["manual_review_status"] == "WATCH_ONLY"


def test_invalid_decision_id_raises_validation_error(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = pd.DataFrame(
        [
            {
                "decision_id": "missing",
                "manual_review_status": "APPROVED_FOR_PAPER",
                "manual_review_notes": "bad id",
                "review_reason_code": "OTHER",
            }
        ]
    )

    with pytest.raises(ValueError, match="Unknown decision_id"):
        apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))


def test_invalid_status_raises_validation_error(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "MAYBE", "OTHER")])

    with pytest.raises(ValueError, match="Invalid manual_review_status"):
        apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))


def test_duplicate_updates_for_same_decision_id_are_rejected(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = pd.concat(
        [
            _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")]),
            _updates(decisions, [(0, "REJECTED", "RISK_TOO_HIGH")]),
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate review updates"):
        apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))


def test_audit_log_records_old_and_new_status(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")])

    result = apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))
    audit = result.review_audit_log.iloc[0]

    assert audit["old_status"] == "PENDING_REVIEW"
    assert audit["new_status"] == "APPROVED_FOR_PAPER"


def test_audit_log_records_reviewer_id_and_reason_code(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")])

    result = apply_paper_review_updates(
        decisions,
        updates,
        reviewer_id="reviewer-a",
        review_time="2024-03-05T16:30:00+08:00",
        settings=_settings(tmp_path),
    )
    audit = result.review_audit_log.iloc[0]

    assert audit["reviewer_id"] == "reviewer-a"
    assert audit["review_reason_code"] == "SCORE_CONFIRMED"
    assert "2024-03-05T16:30:00" in audit["review_time"]


def test_review_summary_counts_statuses_correctly(tmp_path: Path) -> None:
    decisions = _decisions()
    updates = _updates(
        decisions,
        [
            (0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED"),
            (1, "REJECTED", "RISK_TOO_HIGH"),
            (2, "WATCH_ONLY", "WATCHLIST_ONLY"),
        ],
    )

    result = apply_paper_review_updates(decisions, updates, reviewer_id="reviewer-a", settings=_settings(tmp_path))
    summary = result.review_summary.iloc[0]

    assert summary["total_decisions"] == 4
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["watch_only_count"] == 1
    assert summary["pending_count"] == 1
    assert summary["approval_rate"] == pytest.approx(0.25)


def test_reviewed_decisions_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _review_result(tmp_path)

    exported = pd.read_csv(result.artifact_paths["reviewed_decisions"])

    assert len(exported) == 4
    assert "reviewer_id" in exported.columns


def test_review_audit_log_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _review_result(tmp_path)

    exported = pd.read_csv(result.artifact_paths["review_audit_log"])

    assert len(exported) == 3
    assert "audit_id" in exported.columns


def test_review_summary_csv_is_written_and_readable(tmp_path: Path) -> None:
    result = _review_result(tmp_path)

    exported = pd.read_csv(result.artifact_paths["review_summary"])

    assert exported.iloc[0]["approved_count"] == 1


def test_metadata_json_is_written(tmp_path: Path) -> None:
    result = _review_result(tmp_path)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["review_id"] == result.review_id
    assert metadata["live_trading_enabled"] is False
    assert metadata["broker_api_invoked"] is False


def test_report_includes_approval_rejection_summary(tmp_path: Path) -> None:
    result = _review_result(tmp_path)
    content = result.artifact_paths["paper_review_report"].read_text(encoding="utf-8")

    assert "Approval / Rejection Summary" in content
    assert "No broker or live trading integration was invoked" in content


def test_cli_paper_review_decisions_works(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_decisions_and_updates(tmp_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--reviewer-id",
            "cli-reviewer",
            "--output-dir",
            str(tmp_path / "reviews"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "approved_count: 1" in output.out
    assert "No live trading or broker API was invoked." in output.out


def test_cli_paper_review_decisions_unchanged_without_health_check(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_decisions_and_updates(tmp_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--reviewer-id",
            "cli-reviewer",
            "--output-dir",
            str(tmp_path / "reviews"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Template health status:" not in output.out
    assert "approved_count: 1" in output.out


def test_cli_paper_review_decisions_runs_health_check_when_requested(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Template health status: PASS" in output.out
    assert "Template health report path:" in output.out


def test_cli_paper_review_decisions_health_fail_blocks_updates(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)
    decisions_before = pd.read_csv(decisions_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "manual_review_status"] = "BAD_STATUS"
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Template health status: FAIL" in output.out
    assert not list((tmp_path / "reviews").glob("*/reviewed_decisions.csv"))
    pd.testing.assert_frame_equal(pd.read_csv(decisions_path), decisions_before)


def test_cli_paper_review_decisions_health_warn_continues_by_default(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "reviewer_id"] = ""
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--reviewer-id",
            "cli-reviewer",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Template health status: WARN" in output.out
    assert "approved_count: 1" in output.out


def test_cli_paper_review_decisions_health_warn_continues_with_allow_warn(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "reviewer_id"] = ""
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--allow-template-health-warn",
            "--reviewer-id",
            "cli-reviewer",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Template health status: WARN" in output.out


def test_cli_paper_review_decisions_health_warn_blocks_when_pass_required(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "reviewer_id"] = ""
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--require-template-health-pass",
            "--reviewer-id",
            "cli-reviewer",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 1
    assert "Template health status: WARN" in output.out
    assert not list((tmp_path / "reviews").glob("*/reviewed_decisions.csv"))


def test_cli_paper_review_decisions_health_pass_allows_updates(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--require-template-health-pass",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "Template health status: PASS" in output.out
    assert "approved_count: 1" in output.out


def test_cli_paper_review_decisions_health_metadata_is_written(tmp_path: Path) -> None:
    decisions_path, updates_path = _write_pass_health_decisions_and_updates(tmp_path)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--health-check",
            "--output-dir",
            str(tmp_path / "reviews"),
            "--template-health-output-dir",
            str(tmp_path / "template_health"),
        ]
    )
    metadata_path = next((tmp_path / "reviews").glob("*/metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert code == 0
    assert metadata["template_health"]["template_health_status"] == "PASS"
    assert "template_health_report_path" in metadata["template_health"]


def test_cli_exits_nonzero_on_invalid_updates(tmp_path: Path, capsys) -> None:
    decisions_path, updates_path = _write_decisions_and_updates(tmp_path)
    updates = pd.read_csv(updates_path)
    updates.loc[0, "manual_review_status"] = "BAD_STATUS"
    updates.to_csv(updates_path, index=False)

    code = cli.main(
        [
            "paper-review-decisions",
            "--decisions",
            str(decisions_path),
            "--updates",
            str(updates_path),
            "--output-dir",
            str(tmp_path / "reviews"),
        ]
    )
    output = capsys.readouterr()

    assert code != 0
    assert "Invalid manual_review_status" in output.err


def test_load_paper_decisions_reads_csv(tmp_path: Path) -> None:
    path = tmp_path / "decisions.csv"
    _decisions().to_csv(path, index=False)

    loaded = load_paper_decisions(path)

    assert len(loaded) == 4
    assert "decision_id" in loaded.columns


def test_summarize_review_status_handles_empty_decisions() -> None:
    summary = summarize_review_status(pd.DataFrame())

    assert summary.iloc[0]["total_decisions"] == 0
    assert summary.iloc[0]["approval_rate"] == 0


def test_no_live_trading_or_broker_integration_is_invoked(tmp_path: Path) -> None:
    result = _review_result(tmp_path)

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["paper_trading_only"] is True
    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def _review_result(tmp_path: Path) -> PaperReviewResult:
    decisions = _decisions()
    updates = _updates(
        decisions,
        [
            (0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED"),
            (1, "REJECTED", "RISK_TOO_HIGH"),
            (2, "WATCH_ONLY", "WATCHLIST_ONLY"),
        ],
    )
    return apply_paper_review_updates(
        decisions,
        updates,
        reviewer_id="reviewer-a",
        review_time="2024-03-05T16:30:00+08:00",
        settings=_settings(tmp_path),
    )


def _write_decisions_and_updates(tmp_path: Path) -> tuple[Path, Path]:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")])
    decisions_path = tmp_path / "decisions.csv"
    updates_path = tmp_path / "review_updates.csv"
    decisions.to_csv(decisions_path, index=False)
    updates.to_csv(updates_path, index=False)
    return decisions_path, updates_path


def _write_pass_health_decisions_and_updates(tmp_path: Path) -> tuple[Path, Path]:
    decisions = _decisions()
    updates = _updates(decisions, [(0, "APPROVED_FOR_PAPER", "SCORE_CONFIRMED")])
    updates["reviewer_id"] = "cli-reviewer"
    decisions_path = tmp_path / "decisions.csv"
    updates_path = tmp_path / "review_updates.csv"
    decisions.to_csv(decisions_path, index=False)
    updates.to_csv(updates_path, index=False)
    return decisions_path, updates_path


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "paper_review": settings.paper_review.model_copy(
                update={"output_dir": tmp_path / "reviews", "write_artifacts": True}
            )
        }
    )


def _updates(decisions: pd.DataFrame, rows: list[tuple[int, str, str]]) -> pd.DataFrame:
    payload = []
    for idx, status, reason in rows:
        decision = decisions.iloc[idx]
        payload.append(
            {
                "decision_id": decision["decision_id"],
                "manual_review_status": status,
                "manual_review_notes": f"reviewed {decision['symbol']}",
                "reviewer_id": "",
                "review_reason_code": reason,
            }
        )
    return pd.DataFrame(payload)


def _decisions() -> pd.DataFrame:
    return create_paper_decision_log(
        _candidates(),
        decision_date=PAPER_DATE,
        source_run_id="review-run",
        source_report_path="outputs/reports/review-run/report.md",
        manual_review_status="PENDING_REVIEW",
    )


def _candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "AAA",
                "name": "AAA Fund",
                "action": "PAPER_TRADE",
                "final_score": 82.5,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 1,
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "BBB",
                "name": "BBB Fund",
                "action": "PAPER_TRADE",
                "final_score": 78.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "eligible",
                "rank": 2,
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "CCC",
                "name": "CCC Fund",
                "action": "OBSERVE",
                "final_score": 65.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 3,
            },
            {
                "decision_date": pd.Timestamp(PAPER_DATE),
                "symbol": "DDD",
                "name": "DDD Fund",
                "action": "OBSERVE",
                "final_score": 61.0,
                "risk_precheck_status": "PASS",
                "risk_precheck_reason": "watch",
                "rank": 4,
            },
        ]
    )
