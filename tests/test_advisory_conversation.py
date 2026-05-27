import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.advisory_conversation import (
    classify_advisory_question_intent,
    parse_advisory_question,
    run_advisory_conversation,
)
from quant_replay_system.config import load_settings


def test_parse_chinese_buy_question_extracts_symbol_and_intent() -> None:
    result = parse_advisory_question("000001 现在能不能买？")

    assert result.status == "PARSED"
    assert result.parsed_symbol == "000001"
    assert result.parsed_intent == "BUY_REVIEW"
    assert result.parser_type == "deterministic_rule_based"


def test_parse_english_sell_question_extracts_symbol_and_intent() -> None:
    result = parse_advisory_question("Should I sell 510300?")

    assert result.status == "PARSED"
    assert result.parsed_symbol == "510300"
    assert result.parsed_intent == "SELL_REVIEW"


def test_parse_question_without_symbol_fails_without_invented_recommendation() -> None:
    result = parse_advisory_question("这个现在能买吗？")

    assert result.status == "PARSE_FAILED"
    assert result.parsed_symbol == ""
    assert result.parsed_intent == "BUY_REVIEW"
    assert "No six-digit symbol" in result.issue


def test_intent_classifier_supports_watch_hold_and_general() -> None:
    assert classify_advisory_question_intent("510300 要不要继续看？") == "WATCH_REVIEW"
    assert classify_advisory_question_intent("510300 should I hold?") == "HOLD_REVIEW"
    assert classify_advisory_question_intent("510300 怎么样？") == "GENERAL_REVIEW"


def test_conversation_routes_parsed_symbol_to_single_symbol_answer(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = run_advisory_conversation(
        question="000001 现在能不能买？",
        candidates_path=candidates,
        metadata_path=metadata,
        answer_style="detailed",
        settings=_settings(tmp_path),
    )

    assert result.status == "READY"
    assert result.parsed_symbol == "000001"
    assert result.parsed_intent == "BUY_REVIEW"
    assert result.advisory_action == "DEMO_ONLY"
    assert result.linked_answer_run_id
    assert Path(result.linked_answer_markdown_path).exists()
    assert "real trading recommendation" in result.answer_summary
    assert result.semantics_policy_source == "signal_semantics"
    assert result.semantics_classifier == "classify_signal_semantics_action"
    assert result.semantics_action == "DEMO_ONLY"
    assert result.semantics_auto_order_allowed is False
    assert result.llm_api_called is False
    assert result.no_message_sent is True


def test_demo_conversation_does_not_produce_real_buy_instruction(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = run_advisory_conversation(
        question="Should I buy 000001?",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )
    report = result.artifact_paths["advisory_conversation_report"].read_text(encoding="utf-8")

    assert result.advisory_action == "DEMO_ONLY"
    assert "buy now" not in report.lower()
    assert "sell now" not in report.lower()
    assert "demo-only local advisory review" in report.lower()
    assert result.auto_order_allowed is False


def test_missing_symbol_returns_not_found_not_invented_recommendation(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = run_advisory_conversation(
        question="999999 现在能买吗？",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.status == "NOT_FOUND"
    assert result.parsed_symbol == "999999"
    assert result.advisory_action == "NO_ACTION"
    assert "cannot review this symbol" in result.answer_summary
    assert result.auto_order_allowed is False


def test_parse_failed_conversation_writes_safe_no_action_artifact(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = run_advisory_conversation(
        question="这个现在能买吗？",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )
    payload = json.loads(result.artifact_paths["advisory_conversation_json"].read_text(encoding="utf-8"))

    assert result.status == "PARSE_FAILED"
    assert result.parsed_symbol == ""
    assert result.advisory_action == "NO_ACTION"
    assert result.linked_answer_run_id == ""
    assert "recommendation was invented" in result.artifact_paths["advisory_conversation_report"].read_text(
        encoding="utf-8"
    )
    assert payload["llm_api_called"] is False
    assert payload["no_message_sent"] is True
    assert payload["semantics_policy_source"] == "signal_semantics"
    assert payload["semantics_action"] == "NO_ACTION"
    assert payload["semantics_auto_order_allowed"] is False


def test_conversation_records_no_live_broker_message_or_llm_use(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = run_advisory_conversation(
        question="Should I sell 510300?",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )
    metadata_payload = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata_payload["llm_api_called"] is False
    assert metadata_payload["external_api_called"] is False
    assert metadata_payload["message_sent"] is False
    assert metadata_payload["broker_api_invoked"] is False
    assert metadata_payload["live_trading_enabled"] is False
    assert metadata_payload["approved_for_paper_applied"] is False
    assert metadata_payload["semantics_policy_source"] == "signal_semantics"
    assert metadata_payload["semantics_classifier"] == "classify_signal_semantics_action"
    assert metadata_payload["semantics_auto_order_allowed"] is False


def test_cli_advisory_conversation_works(tmp_path: Path, capsys) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    code = cli.main(
        [
            "advisory-conversation",
            "--question",
            "000001 现在能不能买？",
            "--candidates",
            str(candidates),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(tmp_path / "advisory_conversation"),
            "--answer-style",
            "detailed",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "conversation_run_id:" in output.out
    assert "parsed_symbol: 000001" in output.out
    assert "parsed_intent: BUY_REVIEW" in output.out
    assert "advisory_action: DEMO_ONLY" in output.out
    assert "llm_api_called: False" in output.out
    assert "No live trading, broker API, order placement, LLM API, external API, or message delivery was invoked." in output.out


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "single_symbol_advisory": settings.single_symbol_advisory.model_copy(
                update={
                    "output_dir": tmp_path / "single_symbol_advisory",
                    "answer_output_dir": tmp_path / "single_symbol_advisory_answer",
                    "write_artifacts": True,
                }
            ),
            "advisory_conversation": settings.advisory_conversation.model_copy(
                update={"output_dir": tmp_path / "advisory_conversation", "write_artifacts": True}
            ),
        }
    )


def _write_demo_candidate_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "current_candidates" / "2024-05-20_etf_core_demo123"
    artifact_dir.mkdir(parents=True)
    candidates = pd.DataFrame(
        [
            _candidate_row(
                symbol="000001",
                name="Ping An Bank",
                final_score=82.5,
                score_action="PAPER_TRADE",
                action="PAPER_TRADE",
                instrument_type="STOCK",
            ),
            _candidate_row(
                symbol="510300",
                name="CSI 300 ETF",
                final_score=55.0,
                score_action="NO_TRADE",
                action="NO_TRADE",
                instrument_type="ETF",
            ),
        ]
    )
    candidates_path = artifact_dir / "candidates.csv"
    candidates.to_csv(candidates_path, index=False)
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "run_id": "demo123",
                "decision_date": "2024-05-20T00:00:00",
                "selection_profile": "demo",
                "demo_mode": True,
                "not_strategy_recommendation": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return candidates_path, metadata_path


def _candidate_row(
    *,
    symbol: str,
    name: str,
    final_score: float,
    score_action: str,
    action: str,
    instrument_type: str,
) -> dict:
    return {
        "rank": 1,
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type,
        "decision_date": "2024-05-20",
        "final_score": final_score,
        "score_action": score_action,
        "action": action,
        "risk_precheck_status": "PASS",
        "risk_precheck_reason": "eligible",
        "score_breakdown": '{"final_score":82.5}',
        "score_reason": "unit test score context",
        "selection_profile": "demo",
        "demo_mode": True,
        "not_strategy_recommendation": True,
        "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
        "current_candidate_run_id": "demo123",
        "source_run_id": "demo123",
    }
