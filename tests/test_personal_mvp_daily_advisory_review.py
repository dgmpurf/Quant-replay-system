import json
from pathlib import Path

import pandas as pd
import pytest

from quant_replay_system.personal_mvp_daily_advisory_review import (
    DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT,
    DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW,
    DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED,
    REQUIRED_FALSE_SAFETY_FIELDS,
    run_personal_mvp_daily_advisory_review,
)


def test_no_local_advisory_artifacts_creates_safe_no_context_report(tmp_path: Path) -> None:
    result = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    assert result.status == DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT
    assert result.row_count == 0
    assert result.warning_count == 1
    assert result.artifact_paths["daily_advisory_review_report"].exists()
    assert result.artifact_paths["daily_advisory_review_rows"].exists()
    assert result.audit_metadata["report_only"] is True
    assert result.audit_metadata["local_only"] is True
    assert result.audit_metadata["manual_confirmation_required"] is True
    assert result.audit_metadata["current_candidates_run"] is False
    assert result.audit_metadata["snapshot_built"] is False


def test_no_context_report_is_warn_safe_review_required_context(tmp_path: Path) -> None:
    result = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata["status"] == DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT
    assert metadata["health_status"] == "WARN"
    assert "No local advisory context" in metadata["recommended_next_manual_action"]
    assert metadata["real_buy_review_approved"] is False
    assert metadata["trading_allowed"] is False


def test_signal_advisory_rows_create_daily_review_rows(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH"), _signal_row("600519", "NO_ACTION")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out", review_date="2024-05-20")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")
    summary = pd.read_csv(result.artifact_paths["daily_advisory_review_summary"], dtype=str).fillna("").iloc[0]

    assert result.status == DAILY_ADVISORY_REVIEW_READY_FOR_MANUAL_REVIEW
    assert rows["symbol"].tolist() == ["000001", "600519"]
    assert summary["row_count"] == "2"
    assert summary["watch_count"] == "1"
    assert summary["no_action_count"] == "1"


def test_leading_zero_symbols_remain_strings(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype={"symbol": str})

    assert rows.iloc[0]["symbol"] == "000001"


def test_demo_only_remains_workflow_validation_only(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "DEMO_ONLY", demo_mode=True)])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["advisory_action"] == "DEMO_ONLY"
    assert rows.iloc[0]["review_bucket"] == "DEMO_ONLY"
    assert rows.iloc[0]["next_manual_check"] == "Workflow validation context only."
    assert "workflow validation context only" in result.artifact_paths["daily_advisory_review_report"].read_text(encoding="utf-8")


def test_watch_remains_observe_and_review_only(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["review_bucket"] == "WATCH"
    assert rows.iloc[0]["next_manual_check"] == "Observe and review only."


def test_review_buy_candidate_remains_manual_review_candidate_only(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "REVIEW_BUY_CANDIDATE")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["review_bucket"] == "MANUAL_REVIEW"
    assert rows.iloc[0]["next_manual_check"] == "Manual review candidate only."
    assert "not an order" in result.artifact_paths["daily_advisory_review_report"].read_text(encoding="utf-8")


def test_review_sell_candidate_remains_manual_review_candidate_only(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "REVIEW_SELL_CANDIDATE")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["review_bucket"] == "MANUAL_REVIEW"
    assert rows.iloc[0]["next_manual_check"] == "Manual review candidate only."


def test_blocked_rows_remain_blocked_and_not_promoted(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "BLOCKED", blocked_reason="risk failed")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["review_bucket"] == "BLOCKED"
    assert rows.iloc[0]["blocked_reason"] == "risk failed"
    assert rows.iloc[0]["next_manual_check"] == "Inspect blocker before downstream interpretation."


def test_not_found_context_does_not_invent_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_answer_status(root, symbol="999999", action="NO_ACTION", stage="SINGLE_SYMBOL_ADVISORY_ANSWER_NOT_FOUND")

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["symbol"] == "999999"
    assert rows.iloc[0]["advisory_action"] == "NOT_FOUND"
    assert rows.iloc[0]["not_found_reason"] == "No local evidence for the requested symbol."
    assert "No recommendation was invented" in result.artifact_paths["daily_advisory_review_report"].read_text(encoding="utf-8")


def test_stale_signal_artifact_marks_stale_context(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH", decision_date="2024-05-01")])

    result = run_personal_mvp_daily_advisory_review(
        root=root,
        output_dir=tmp_path / "out",
        review_date="2024-05-20",
        stale_after_days=7,
    )
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert result.status == DAILY_ADVISORY_REVIEW_STALE_CONTEXT_REVIEW_REQUIRED
    assert rows.iloc[0]["stale_context_reason"] == "Artifact freshness requires review before use."


def test_paper_context_is_optional_and_does_not_change_advisory_labels(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])
    _write_paper_status(root)

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out", include_paper_context=True)
    rows = pd.read_csv(result.artifact_paths["daily_advisory_review_rows"], dtype=str).fillna("")

    assert rows.iloc[0]["advisory_action"] == "WATCH"
    assert rows.iloc[0]["linked_paper_context_path"].endswith("paper_workflow_status_report.md")


def test_single_symbol_answer_path_is_linked_when_present(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])
    _write_answer_status(root, symbol="000001", action="WATCH")

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    drilldown = pd.read_csv(result.artifact_paths["single_symbol_drilldown_index"], dtype=str).fillna("")

    assert drilldown.iloc[0]["symbol"] == "000001"
    assert drilldown.iloc[0]["answer_markdown_path"].endswith("single_symbol_advisory_answer.md")


def test_advisory_conversation_report_path_is_linked_when_present(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])
    _write_conversation_status(root, symbol="000001", action="WATCH")

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    drilldown = pd.read_csv(result.artifact_paths["single_symbol_drilldown_index"], dtype=str).fillna("")

    assert drilldown.iloc[0]["conversation_report_path"].endswith("advisory_conversation_report.md")


def test_manual_checklist_is_written_for_visible_rows(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH"), _signal_row("600519", "BLOCKED")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    checklist = pd.read_csv(result.artifact_paths["manual_review_checklist"], dtype=str).fillna("")

    assert set(checklist["symbol"]) == {"000001", "600519"}
    assert "confirm_artifact_date" in set(checklist["check_id"])
    assert "confirm_no_order_message_broker_trading" in set(checklist["check_id"])


def test_all_required_safety_fields_are_present_and_safe(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    safety = json.loads(result.artifact_paths["safety_flags"].read_text(encoding="utf-8"))

    for field in REQUIRED_FALSE_SAFETY_FIELDS:
        assert safety[field] is False
        assert result.audit_metadata[field] is False
    assert safety["report_only"] is True
    assert safety["diagnostic_only"] is True
    assert safety["local_only"] is True
    assert safety["manual_confirmation_required"] is True


@pytest.mark.parametrize("blocked", ["data/raw", "data/processed", "data/cache", "docs/project_sources"])
def test_output_root_rejects_protected_paths(tmp_path: Path, blocked: str) -> None:
    with pytest.raises(ValueError, match="protected output path"):
        run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=Path(blocked))


def test_report_wording_contains_required_non_approval_statements(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    report = result.artifact_paths["daily_advisory_review_report"].read_text(encoding="utf-8")

    for phrase in [
        "local advisory review context",
        "manual confirmation required",
        "not an order",
        "not broker, order, message, or trading authorization",
        "does not create real buy-review eligibility",
        "does not validate strategy performance",
        "does not mutate signal semantics",
        "does not run current-candidates or snapshots",
        "does not write protected data paths",
    ]:
        assert phrase in report


def test_report_wording_does_not_contain_unsafe_command_like_phrases(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "REVIEW_BUY_CANDIDATE")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")
    report = result.artifact_paths["daily_advisory_review_report"].read_text(encoding="utf-8").lower()

    assert "buy now" not in report
    assert "sell now" not in report
    assert "place order" not in report
    assert "submit order" not in report


def test_no_protected_data_path_writes_or_runtime_side_effects(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    _write_signal_artifact(root, rows=[_signal_row("000001", "WATCH")])

    result = run_personal_mvp_daily_advisory_review(root=root, output_dir=tmp_path / "out")

    assert result.audit_metadata["data_raw_written"] is False
    assert result.audit_metadata["data_processed_written"] is False
    assert result.audit_metadata["data_cache_written"] is False
    assert result.audit_metadata["signal_semantics_mutated"] is False
    assert result.audit_metadata["current_candidates_run"] is False
    assert result.audit_metadata["snapshot_built"] is False
    assert result.audit_metadata["buy_review_allowed"] is False
    assert result.audit_metadata["trading_allowed"] is False


def _signal_row(
    symbol: str,
    action: str,
    *,
    demo_mode: bool = False,
    blocked_reason: str = "",
    decision_date: str = "2024-05-20",
) -> dict[str, object]:
    return {
        "signal_id": f"signal-{symbol}",
        "signal_run_id": "signal-run-1",
        "signal_date": decision_date,
        "decision_date": decision_date,
        "symbol": symbol,
        "name": f"Name {symbol}",
        "instrument_type": "stock",
        "universe_name": "stock_core",
        "advisory_action": action,
        "final_score": 75.0,
        "confidence_level": "medium",
        "reason_summary": "synthetic reason",
        "entry_condition": "already present entry context",
        "exit_condition": "already present exit context",
        "invalidation_condition": "invalidate if local context changes",
        "valid_until": "2024-05-21",
        "risk_notes": "risk note",
        "data_source_notes": "data note",
        "demo_mode": demo_mode,
        "not_strategy_recommendation": demo_mode,
        "blocked_reason": blocked_reason,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
    }


def _write_signal_artifact(root: Path, *, rows: list[dict[str, object]]) -> Path:
    artifact = root / "signals" / "signal-run-1"
    artifact.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(artifact / "signals.csv", index=False)
    (artifact / "signal_advisory_report.md").write_text("# Signal report\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "signal_run_id": "signal-run-1",
                "status": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "workflow_stage": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "signal_count": len(rows),
                "report_path": str(artifact / "signal_advisory_report.md"),
                "signals_path": str(artifact / "signals.csv"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def _write_answer_status(root: Path, *, symbol: str, action: str, stage: str = "SINGLE_SYMBOL_ADVISORY_ANSWER_READY_FOR_REVIEW") -> Path:
    artifact = root / "single_symbol_advisory_answer" / f"answer-{symbol}"
    artifact.mkdir(parents=True)
    answer = artifact / "single_symbol_advisory_answer.md"
    answer.write_text("# Answer\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "answer_run_id": f"answer-{symbol}",
                "advisory_run_id": f"single-{symbol}",
                "symbol": symbol,
                "status": stage,
                "workflow_stage": stage,
                "advisory_action": action,
                "question": "should I review?",
                "answer_style": "concise",
                "health_status": "PASS",
                "answer_markdown_path": str(answer),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def _write_conversation_status(root: Path, *, symbol: str, action: str) -> Path:
    artifact = root / "advisory_conversation" / f"conversation-{symbol}"
    artifact.mkdir(parents=True)
    report = artifact / "advisory_conversation_report.md"
    report.write_text("# Conversation\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "conversation_run_id": f"conversation-{symbol}",
                "original_question": f"Should I review {symbol}?",
                "parsed_symbol": symbol,
                "parsed_intent": "WATCH_REVIEW",
                "status": "ADVISORY_CONVERSATION_READY_FOR_REVIEW",
                "workflow_stage": "ADVISORY_CONVERSATION_READY_FOR_REVIEW",
                "advisory_action": action,
                "health_status": "PASS",
                "report_path": str(report),
                "linked_answer_markdown_path": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact


def _write_paper_status(root: Path) -> Path:
    artifact = root / "paper_trading" / "workflow_status" / "paper-status-1"
    artifact.mkdir(parents=True)
    report = artifact / "paper_workflow_status_report.md"
    report.write_text("# Paper status\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "workflow_status_id": "paper-status-1",
                "status": "PASS",
                "workflow_stage": "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
                "paper_workflow_status_report": str(report),
                "report_path": str(report),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact
