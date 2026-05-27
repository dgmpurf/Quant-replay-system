import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.single_symbol_advisory import (
    SINGLE_SYMBOL_ADVISORY_COLUMNS,
    build_single_symbol_advisory,
    build_single_symbol_advisory_answer,
    classify_single_symbol_advisory_action,
)


def test_finds_leading_zero_symbol_in_candidates(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        alert_preview=True,
        settings=_settings(tmp_path),
    )

    output = pd.read_csv(result.artifact_paths["single_symbol_advisory_csv"], dtype={"symbol": str})
    assert result.status == "READY"
    assert result.symbol == "000001"
    assert output.loc[0, "symbol"] == "000001"
    assert set(SINGLE_SYMBOL_ADVISORY_COLUMNS).issubset(output.columns)


def test_demo_candidate_becomes_demo_only_not_real_buy(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.advisory_action == "DEMO_ONLY"
    assert result.not_strategy_recommendation is True
    assert result.requires_manual_confirmation is True
    assert result.auto_order_allowed is False
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_message_sent is True
    assert result.semantics_policy_source == "signal_semantics"
    assert result.semantics_policy_version == "v0.1"
    assert result.semantics_classifier == "classify_signal_semantics_action"
    assert result.semantics_action == "DEMO_ONLY"
    assert result.semantics_auto_order_allowed is False
    metadata_payload = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert metadata_payload["semantics_policy_source"] == "signal_semantics"
    assert metadata_payload["semantics_auto_order_allowed"] is False


def test_single_symbol_synthetic_non_demo_high_score_can_be_review_buy_candidate_manual_only(tmp_path: Path) -> None:
    candidates, metadata = _write_non_demo_candidate_artifacts(
        tmp_path,
        row_updates={"final_score": 82.5, "score_action": "OBSERVE", "action": "OBSERVE"},
    )

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.advisory_action == "REVIEW_BUY_CANDIDATE"
    assert result.requires_manual_confirmation is True
    assert result.auto_order_allowed is False
    assert result.no_live_trading is True
    assert result.no_broker_api is True
    assert result.no_message_sent is True
    assert "Manual research review required" in result.reason_summary


def test_missing_symbol_returns_not_found_without_invented_recommendation(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = build_single_symbol_advisory(
        "999999",
        candidates_path=candidates,
        metadata_path=metadata,
        alert_preview=True,
        settings=_settings(tmp_path),
    )

    assert result.status == "NOT_FOUND"
    assert result.advisory_action == "NO_ACTION"
    assert "not present" in result.reason_summary
    assert result.source_artifact_path is None
    assert any(issue.category == "SYMBOL_NOT_FOUND" for issue in result.issues)


def test_blocked_source_row_produces_blocked(tmp_path: Path) -> None:
    candidates, metadata = _write_non_demo_candidate_artifacts(
        tmp_path,
        row_updates={
            "risk_precheck_status": "BLOCK",
            "risk_precheck_reason": "limit up risk",
            "score_action": "BLOCKED",
            "action": "BLOCKED",
        },
    )

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.advisory_action == "BLOCKED"
    assert "blocked" in result.reason_summary.lower()
    assert result.auto_order_allowed is False


def test_failed_risk_semantics_produces_blocked(tmp_path: Path) -> None:
    candidates, metadata = _write_non_demo_candidate_artifacts(
        tmp_path,
        row_updates={
            "risk_precheck_status": "FAIL",
            "risk_precheck_reason": "risk gate failed",
            "score_action": "PAPER_TRADE",
            "action": "PAPER_TRADE",
            "final_score": 91.0,
        },
    )

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.advisory_action == "BLOCKED"
    assert result.auto_order_allowed is False


def test_no_trade_source_row_produces_no_action(tmp_path: Path) -> None:
    candidates, metadata = _write_non_demo_candidate_artifacts(
        tmp_path,
        row_updates={"score_action": "NO_TRADE", "action": "NO_TRADE", "final_score": 45.0},
    )

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.advisory_action == "NO_ACTION"
    assert result.requires_manual_confirmation is True


def test_single_symbol_classifier_uses_conservative_semantics_fallback() -> None:
    row = {
        "symbol": "000001",
        "selection_profile": "default",
        "demo_mode": False,
        "not_strategy_recommendation": False,
        "final_score": 42.0,
        "score_action": "",
        "action": "",
        "risk_precheck_status": "PASS",
    }

    assert classify_single_symbol_advisory_action(row) == "NO_ACTION"


def test_alert_preview_includes_manual_confirmation_and_no_auto_order(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = build_single_symbol_advisory(
        "510300",
        candidates_path=candidates,
        metadata_path=metadata,
        alert_preview=True,
        settings=_settings(tmp_path),
    )
    preview = result.artifact_paths["alert_preview"].read_text(encoding="utf-8")

    assert "Manual confirmation" in preview
    assert "No auto-order" in preview
    assert "No message was sent" in preview


def test_cli_single_symbol_advisory_works(tmp_path: Path, capsys) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    code = cli.main(
        [
            "single-symbol-advisory",
            "--symbol",
            "000001",
            "--candidates",
            str(candidates),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(tmp_path / "single_symbol_advisory"),
            "--alert-preview",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "advisory_run_id:" in output.out
    assert "status: READY" in output.out
    assert "symbol: 000001" in output.out
    assert "advisory_action: DEMO_ONLY" in output.out
    assert "no_message_sent: True" in output.out
    assert "No alert message was sent." in output.out


def test_question_style_answer_preserves_leading_zero_and_avoids_real_buy_sell_instruction(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    settings = _settings(tmp_path)
    advisory = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=settings,
    )

    answer = build_single_symbol_advisory_answer(
        advisory,
        question="should I buy?",
        answer_style="detailed",
        settings=settings,
    )
    text = answer.artifact_paths["single_symbol_advisory_answer"].read_text(encoding="utf-8")

    assert answer.symbol == "000001"
    assert "Symbol: `000001`" in text
    assert "buy now" not in text.lower()
    assert "sell now" not in text.lower()
    assert "Demo-only review" in text
    assert "not a real trading recommendation" in text
    assert "Manual confirmation required: `True`" in text
    assert "Auto-order allowed: `False`" in text


def test_question_style_not_found_answer_does_not_invent_recommendation(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    settings = _settings(tmp_path)
    advisory = build_single_symbol_advisory(
        "999999",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=settings,
    )

    answer = build_single_symbol_advisory_answer(
        advisory,
        question="should I buy?",
        settings=settings,
    )
    payload = json.loads(answer.artifact_paths["single_symbol_advisory_answer_json"].read_text(encoding="utf-8"))
    text = answer.artifact_paths["single_symbol_advisory_answer"].read_text(encoding="utf-8")

    assert advisory.status == "NOT_FOUND"
    assert answer.advisory_action == "NO_ACTION"
    assert "cannot review this symbol" in answer.short_answer
    assert "No recommendation was invented" in text
    assert payload["auto_order_allowed"] is False
    assert payload["no_live_trading"] is True
    assert payload["no_broker_api"] is True
    assert payload["no_message_sent"] is True
    assert payload["semantics_policy_source"] == "signal_semantics"
    assert payload["semantics_auto_order_allowed"] is False


def test_cli_single_symbol_question_style_writes_answer(tmp_path: Path, capsys) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    code = cli.main(
        [
            "single-symbol-advisory",
            "--symbol",
            "000001",
            "--candidates",
            str(candidates),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(tmp_path / "single_symbol_advisory"),
            "--answer-output-dir",
            str(tmp_path / "single_symbol_advisory_answer"),
            "--question",
            "should I buy?",
            "--question-style",
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "answer_run_id:" in output.out
    assert "answer_path:" in output.out
    assert "short_answer:" in output.out
    assert "No alert message was sent." in output.out


def test_question_style_answer_records_no_message_or_external_api_use(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)
    settings = _settings(tmp_path)
    advisory = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=settings,
    )

    answer = build_single_symbol_advisory_answer(advisory, settings=settings)
    metadata_payload = json.loads(answer.artifact_paths["metadata"].read_text(encoding="utf-8"))

    assert metadata_payload["message_sent"] is False
    assert metadata_payload["llm_api_called"] is False
    assert metadata_payload["external_api_called"] is False
    assert metadata_payload["broker_api_invoked"] is False
    assert metadata_payload["live_trading_enabled"] is False
    assert metadata_payload["approved_for_paper_applied"] is False
    assert metadata_payload["semantics_policy_source"] == "signal_semantics"
    assert metadata_payload["semantics_classifier"] == "classify_signal_semantics_action"
    assert metadata_payload["semantics_auto_order_allowed"] is False


def test_no_live_trading_broker_network_or_message_sending(tmp_path: Path) -> None:
    candidates, metadata = _write_demo_candidate_artifacts(tmp_path)

    result = build_single_symbol_advisory(
        "000001",
        candidates_path=candidates,
        metadata_path=metadata,
        settings=_settings(tmp_path),
    )

    assert result.audit_metadata["live_trading_enabled"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["message_delivery_enabled"] is False
    assert result.audit_metadata["message_sent"] is False
    assert result.audit_metadata["approved_for_paper_applied"] is False


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
            )
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
                "audit_metadata": {
                    "selection_profile": "demo",
                    "demo_mode": True,
                    "not_strategy_recommendation": True,
                    "snapshot_quality_manifest_path": "snapshots/demo_manifest.json",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return candidates_path, metadata_path


def _write_non_demo_candidate_artifacts(tmp_path: Path, *, row_updates: dict) -> tuple[Path, Path]:
    artifact_dir = tmp_path / "current_candidates" / "2024-05-20_etf_core_default123"
    artifact_dir.mkdir(parents=True)
    row = _candidate_row(
        symbol="000001",
        name="Ping An Bank",
        final_score=70.0,
        score_action="PAPER_TRADE",
        action="PAPER_TRADE",
        instrument_type="STOCK",
        selection_profile="default",
        demo_mode=False,
        not_strategy_recommendation=False,
    )
    row.update(row_updates)
    candidates_path = artifact_dir / "candidates.csv"
    pd.DataFrame([row]).to_csv(candidates_path, index=False)
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "run_id": "default123",
                "decision_date": "2024-05-20T00:00:00",
                "selection_profile": "default",
                "demo_mode": False,
                "not_strategy_recommendation": False,
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
    selection_profile: str = "demo",
    demo_mode: bool = True,
    not_strategy_recommendation: bool = True,
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
        "selection_profile": selection_profile,
        "demo_mode": demo_mode,
        "not_strategy_recommendation": not_strategy_recommendation,
        "selection_reason": "DEMO_PROFILE_SELECTED_FOR_WORKFLOW_VALIDATION",
        "current_candidate_run_id": "demo123" if demo_mode else "default123",
        "source_run_id": "demo123" if demo_mode else "default123",
    }
