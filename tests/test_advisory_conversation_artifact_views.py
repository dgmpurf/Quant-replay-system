import json
from pathlib import Path

from quant_replay_system import cli
from quant_replay_system.advisory_conversation_health import check_advisory_conversation_health
from quant_replay_system.advisory_conversation_index import build_advisory_conversation_index
from quant_replay_system.advisory_conversation_status import run_advisory_conversation_status


def test_advisory_conversation_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001")

    result = build_advisory_conversation_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["conversation_run_id"] == "conv001"
    assert row["parsed_symbol"] == "000001"
    assert row["parsed_intent"] == "BUY_REVIEW"
    assert row["advisory_action"] == "DEMO_ONLY"


def test_advisory_conversation_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_advisory_conversation_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_advisory_conversation_health_passes_safe_demo_conversation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001")

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_advisory_conversation_health_fails_when_llm_api_called(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001", metadata_updates={"llm_api_called": True})

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "LLM_API_CALLED" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_when_message_sent(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001", metadata_updates={"no_message_sent": False})

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MESSAGE_DELIVERY_DETECTED" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001", metadata_updates={"auto_order_allowed": True})

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_when_leading_zero_symbol_is_lost(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="1")

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_allows_parse_failed_without_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(
        root,
        "conv001",
        symbol="",
        status="PARSE_FAILED",
        advisory_action="NO_ACTION",
        answer_summary="I could not find a six-digit local symbol. No recommendation was invented.",
    )

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert "PARSE_FAILED_WITH_RECOMMENDATION" not in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_parse_failed_with_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(
        root,
        "conv001",
        symbol="",
        status="PARSE_FAILED",
        advisory_action="NO_ACTION",
        answer_summary="You should buy now.",
    )

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "PARSE_FAILED_WITH_RECOMMENDATION" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_allows_not_found_without_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(
        root,
        "conv001",
        symbol="999999",
        status="NOT_FOUND",
        advisory_action="NO_ACTION",
        answer_summary="Symbol was not present in the local artifact; no recommendation was invented.",
    )

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert "NOT_FOUND_WITH_RECOMMENDATION" not in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_not_found_with_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(
        root,
        "conv001",
        symbol="999999",
        status="NOT_FOUND",
        advisory_action="NO_ACTION",
        answer_summary="You should buy now.",
    )

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "NOT_FOUND_WITH_RECOMMENDATION" in set(result.health_frame["issue_code"])


def test_advisory_conversation_health_fails_demo_real_buy_action(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(
        root,
        "conv001",
        symbol="000001",
        advisory_action="REVIEW_BUY_CANDIDATE",
        metadata_updates={"demo_mode": True, "not_strategy_recommendation": True},
    )

    result = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_CONVERSATION_ACTION_UNSAFE" in set(result.health_frame["issue_code"])


def test_advisory_conversation_status_summarizes_latest_conversation(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001", created_at="2024-05-19T00:00:00+00:00")
    _write_conversation_artifact(root, "conv002", symbol="510300", parsed_intent="SELL_REVIEW", created_at="2024-05-20T00:00:00+00:00")

    result = run_advisory_conversation_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_conversation_run_id == "conv002"
    assert result.latest_parsed_symbol == "510300"
    assert result.latest_parsed_intent == "SELL_REVIEW"
    assert result.workflow_stage == "DEMO_ADVISORY_CONVERSATION_VALIDATED"
    assert result.status == "WARN"


def test_advisory_conversation_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_advisory_conversation_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_ADVISORY_CONVERSATION_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_conversation_run_id == ""


def test_cli_advisory_conversation_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001")

    index_code = cli.main(
        [
            "advisory-conversation-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "advisory-conversation-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "advisory-conversation-status",
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
    assert "workflow_stage: DEMO_ADVISORY_CONVERSATION_VALIDATED" in status_output.out
    assert "No live trading, broker API, order placement, LLM/API call, external API call, or message delivery was invoked." in status_output.out


def test_advisory_conversation_views_do_not_enable_live_broker_message_or_llm(tmp_path: Path) -> None:
    root = tmp_path / "advisory_conversation"
    _write_conversation_artifact(root, "conv001", symbol="000001")

    index = build_advisory_conversation_index(root=root, output_dir=tmp_path / "index")
    health = check_advisory_conversation_health(root=root, output_dir=tmp_path / "health")
    status = run_advisory_conversation_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False
    assert status.audit_metadata["llm_api_called"] is False


def _write_conversation_artifact(
    root: Path,
    conversation_run_id: str,
    *,
    symbol: str,
    original_question: str = "000001 现在能不能买？",
    parsed_intent: str = "BUY_REVIEW",
    status: str = "READY",
    advisory_action: str = "DEMO_ONLY",
    parser_type: str = "deterministic_rule_based",
    linked_advisory_run_id: str = "adv001",
    linked_answer_run_id: str = "ans001",
    answer_summary: str = "Demo-only review for workflow validation; not a real trading recommendation.",
    created_at: str = "2024-05-20T00:00:00+00:00",
    metadata_updates: dict | None = None,
    json_updates: dict | None = None,
) -> None:
    artifact_dir = root / conversation_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    linked_answer_path = ""
    if status == "READY":
        answer_dir = root.parent / "single_symbol_advisory_answer" / linked_answer_run_id
        answer_dir.mkdir(parents=True, exist_ok=True)
        linked_answer_path = str(answer_dir / "single_symbol_advisory_answer.md")
        Path(linked_answer_path).write_text("Linked answer artifact.", encoding="utf-8")
    report_path = artifact_dir / "advisory_conversation_report.md"
    json_path = artifact_dir / "advisory_conversation.json"
    metadata_path = artifact_dir / "metadata.json"
    report_text = "\n".join(
        [
            f"# Advisory Conversation: {symbol or 'PARSE_FAILED'}",
            "",
            original_question,
            "",
            answer_summary,
            "",
            "This is a demo-only local advisory review. It is not a real trading recommendation.",
            "Manual confirmation required. Auto-order allowed: False.",
            "No live trading: True. No broker API: True. No message sent: True. LLM API called: False.",
        ]
    )
    report_path.write_text(report_text, encoding="utf-8")
    payload = {
        "conversation_run_id": conversation_run_id,
        "status": status,
        "original_question": original_question,
        "parsed_symbol": symbol,
        "parsed_intent": parsed_intent,
        "parser_type": parser_type,
        "advisory_action": advisory_action,
        "answer_summary": answer_summary,
        "linked_advisory_run_id": linked_advisory_run_id if status != "PARSE_FAILED" else "",
        "linked_answer_run_id": linked_answer_run_id if status != "PARSE_FAILED" else "",
        "linked_answer_markdown_path": linked_answer_path,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "llm_api_called": False,
        "external_api_called": False,
        "demo_mode": advisory_action == "DEMO_ONLY",
        "not_strategy_recommendation": advisory_action == "DEMO_ONLY",
    }
    payload.update(json_updates or {})
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    metadata = {
        **payload,
        "created_at": created_at,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "output_files": {
            "advisory_conversation_report": str(report_path),
            "advisory_conversation_json": str(json_path),
            "metadata": str(metadata_path),
        },
    }
    metadata.update(metadata_updates or {})
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
