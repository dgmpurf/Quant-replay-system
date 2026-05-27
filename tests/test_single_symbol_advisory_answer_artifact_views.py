import json
from pathlib import Path

from quant_replay_system import cli
from quant_replay_system.single_symbol_advisory_answer_health import check_single_symbol_advisory_answer_health
from quant_replay_system.single_symbol_advisory_answer_index import build_single_symbol_advisory_answer_index
from quant_replay_system.single_symbol_advisory_answer_status import run_single_symbol_advisory_answer_status


def test_single_symbol_advisory_answer_index_detects_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001")

    result = build_single_symbol_advisory_answer_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["answer_run_id"] == "ans001"
    assert row["advisory_run_id"] == "adv001"
    assert row["symbol"] == "000001"
    assert row["advisory_action"] == "DEMO_ONLY"


def test_single_symbol_advisory_answer_index_handles_no_artifacts(tmp_path: Path) -> None:
    result = build_single_symbol_advisory_answer_index(root=tmp_path / "missing", output_dir=tmp_path / "index")

    assert result.artifact_count == 0
    assert result.index_frame.empty
    assert any("root does not exist" in warning for warning in result.warnings)


def test_single_symbol_advisory_answer_health_passes_safe_demo_answer(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001")

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0


def test_single_symbol_advisory_answer_health_fails_when_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001", metadata_updates={"auto_order_allowed": True})

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_warns_when_legacy_provenance_missing(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001", include_semantics_provenance=False)

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert "MISSING_SEMANTICS_PROVENANCE" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_semantics_auto_order_allowed(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(
        root,
        "ans001",
        advisory_run_id="adv001",
        symbol="000001",
        metadata_updates={"semantics_auto_order_allowed": True},
    )

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_AUTO_ORDER_ALLOWED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_semantics_source_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(
        root,
        "ans001",
        advisory_run_id="adv001",
        symbol="000001",
        metadata_updates={"semantics_policy_source": "other_policy"},
    )

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SEMANTICS_POLICY_SOURCE_MISMATCH" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_llm_api_called(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001", metadata_updates={"llm_api_called": True})

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "LLM_API_CALLED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_message_sent(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001", metadata_updates={"no_message_sent": False})

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "MESSAGE_DELIVERY_DETECTED" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_demo_answer_has_buy_instruction(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(
        root,
        "ans001",
        advisory_run_id="adv001",
        symbol="000001",
        short_answer="You should buy now.",
    )

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "DEMO_ANSWER_UNSAFE" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_when_leading_zero_symbol_is_lost(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="1")

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "SYMBOL_FORMAT_ERROR" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_allows_not_found_without_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(
        root,
        "ans001",
        advisory_run_id="adv001",
        symbol="999999",
        status="NOT_FOUND",
        advisory_action="NO_ACTION",
        demo_mode=False,
        not_strategy_recommendation=False,
        short_answer="I cannot review this symbol from the provided artifact; no recommendation was invented.",
    )

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert "NOT_FOUND_WITH_RECOMMENDATION" not in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_health_fails_not_found_with_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(
        root,
        "ans001",
        advisory_run_id="adv001",
        symbol="999999",
        status="NOT_FOUND",
        advisory_action="NO_ACTION",
        demo_mode=False,
        not_strategy_recommendation=False,
        short_answer="You should buy now.",
    )

    result = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "NOT_FOUND_WITH_RECOMMENDATION" in set(result.health_frame["issue_code"])


def test_single_symbol_advisory_answer_status_summarizes_latest_answer(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001", created_at="2024-05-19T00:00:00")
    _write_answer_artifact(root, "ans002", advisory_run_id="adv002", symbol="510300", created_at="2024-05-20T00:00:00")

    result = run_single_symbol_advisory_answer_status(root=root, output_dir=tmp_path / "status")

    assert result.latest_answer_run_id == "ans002"
    assert result.latest_symbol == "510300"
    assert result.workflow_stage == "DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED"
    assert result.status == "WARN"


def test_single_symbol_advisory_answer_status_handles_no_artifacts(tmp_path: Path) -> None:
    result = run_single_symbol_advisory_answer_status(root=tmp_path / "missing", output_dir=tmp_path / "status")

    assert result.workflow_stage == "NO_SINGLE_SYMBOL_ADVISORY_ANSWER_ARTIFACTS"
    assert result.status == "WARN"
    assert result.latest_answer_run_id == ""


def test_cli_single_symbol_advisory_answer_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001")

    index_code = cli.main(
        [
            "single-symbol-advisory-answer-index",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "index"),
        ]
    )
    index_output = capsys.readouterr()
    health_code = cli.main(
        [
            "single-symbol-advisory-answer-health",
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path / "health"),
        ]
    )
    health_output = capsys.readouterr()
    status_code = cli.main(
        [
            "single-symbol-advisory-answer-status",
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
    assert "workflow_stage: DEMO_SINGLE_SYMBOL_ADVISORY_ANSWER_VALIDATED" in status_output.out
    assert "No live trading, broker API, order placement, LLM API, or message delivery was invoked." in status_output.out


def test_single_symbol_answer_artifact_views_do_not_enable_live_broker_message_or_llm(tmp_path: Path) -> None:
    root = tmp_path / "single_symbol_advisory_answer"
    _write_answer_artifact(root, "ans001", advisory_run_id="adv001", symbol="000001")

    index = build_single_symbol_advisory_answer_index(root=root, output_dir=tmp_path / "index")
    health = check_single_symbol_advisory_answer_health(root=root, output_dir=tmp_path / "health")
    status = run_single_symbol_advisory_answer_status(root=root, output_dir=tmp_path / "status")

    assert index.audit_metadata["live_trading_enabled"] is False
    assert health.audit_metadata["broker_api_invoked"] is False
    assert status.audit_metadata["message_delivery_enabled"] is False
    assert status.audit_metadata["llm_api_called"] is False


def _write_answer_artifact(
    root: Path,
    answer_run_id: str,
    *,
    advisory_run_id: str,
    symbol: str,
    status: str = "READY",
    advisory_action: str = "DEMO_ONLY",
    question: str = "should I buy?",
    answer_style: str = "concise",
    demo_mode: bool = True,
    not_strategy_recommendation: bool = True,
    short_answer: str = "Demo-only review for workflow validation; not a real trading recommendation.",
    created_at: str = "2024-05-20T00:00:00",
    metadata_updates: dict | None = None,
    json_updates: dict | None = None,
    include_semantics_provenance: bool = True,
) -> None:
    artifact_dir = root / answer_run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    answer_body = "\n".join(
        [
            f"# Single-Symbol Advisory Answer: {symbol}",
            "",
            question,
            "",
            short_answer,
            "",
            "Manual confirmation required. Auto-order allowed: False.",
            "No live trading: True. No broker API: True. No message sent: True.",
            "This answer is local and deterministic. It is not LLM-generated.",
        ]
    )
    (artifact_dir / "single_symbol_advisory_answer.md").write_text(answer_body, encoding="utf-8")
    payload = {
        "answer_run_id": answer_run_id,
        "advisory_run_id": advisory_run_id,
        "symbol": symbol,
        "status": status,
        "advisory_action": advisory_action,
        **(_semantics_provenance(advisory_action) if include_semantics_provenance else {}),
        "question": question,
        "answer_style": answer_style,
        "short_answer": short_answer,
        "answer_body": answer_body,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "audit_metadata": {
            "demo_mode": demo_mode,
            "not_strategy_recommendation": not_strategy_recommendation,
            **(_semantics_provenance(advisory_action) if include_semantics_provenance else {}),
            "llm_api_called": False,
            "external_api_called": False,
            "message_delivery_enabled": False,
            "message_sent": False,
        },
        "advisory_record": {
            "symbol": symbol,
            "status": status,
            "advisory_action": advisory_action,
            **(_semantics_provenance(advisory_action) if include_semantics_provenance else {}),
            "demo_mode": demo_mode,
            "not_strategy_recommendation": not_strategy_recommendation,
            "requires_manual_confirmation": True,
            "auto_order_allowed": False,
            "no_live_trading": True,
            "no_broker_api": True,
            "no_message_sent": True,
        },
    }
    payload.update(json_updates or {})
    (artifact_dir / "single_symbol_advisory_answer.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    metadata = {
        "answer_run_id": answer_run_id,
        "created_at": created_at,
        "advisory_run_id": advisory_run_id,
        "symbol": symbol,
        "status": status,
        "advisory_action": advisory_action,
        **(_semantics_provenance(advisory_action) if include_semantics_provenance else {}),
        "question": question,
        "answer_style": answer_style,
        "short_answer": short_answer,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_delivery_enabled": False,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "approved_for_paper_applied": False,
        "llm_api_called": False,
        "external_api_called": False,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy_recommendation,
        "output_files": {
            "single_symbol_advisory_answer": str(artifact_dir / "single_symbol_advisory_answer.md"),
            "single_symbol_advisory_answer_json": str(artifact_dir / "single_symbol_advisory_answer.json"),
            "metadata": str(artifact_dir / "metadata.json"),
        },
    }
    metadata.update(metadata_updates or {})
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _semantics_provenance(action: str) -> dict:
    return {
        "semantics_policy_source": "signal_semantics",
        "semantics_policy_version": "v0.1",
        "semantics_classifier": "classify_signal_semantics_action",
        "semantics_settings_profile": "demo",
        "semantics_action": action,
        "semantics_reason": "Test artifact classified by shared signal semantics.",
        "semantics_manual_confirmation_required": True,
        "semantics_auto_order_allowed": False,
        "semantics_no_live_trading": True,
        "semantics_no_broker_api": True,
    }
