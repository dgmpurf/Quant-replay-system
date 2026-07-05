import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.personal_mvp_daily_advisory_review import (
    REQUIRED_FALSE_SAFETY_FIELDS,
    run_personal_mvp_daily_advisory_review,
)
from quant_replay_system.personal_mvp_daily_advisory_review_health import (
    check_personal_mvp_daily_advisory_review_health,
)
from quant_replay_system.personal_mvp_daily_advisory_review_index import (
    build_personal_mvp_daily_advisory_review_index,
)
from quant_replay_system.personal_mvp_daily_advisory_review_status import (
    run_personal_mvp_daily_advisory_review_status,
)


def test_index_discovers_no_context_daily_advisory_review_run(tmp_path: Path) -> None:
    run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = build_personal_mvp_daily_advisory_review_index(root=tmp_path / "out")

    assert result.artifact_count == 1
    assert result.rows[0]["status"] == "DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT"
    assert result.rows[0]["health_status"] == "WARN"
    assert result.artifact_paths["index_csv"].exists()


def test_index_preserves_leading_zero_symbol_rows(tmp_path: Path) -> None:
    source_root = tmp_path / "reports"
    _write_signal_artifact(source_root)
    run_personal_mvp_daily_advisory_review(root=source_root, output_dir=tmp_path / "out")

    result = build_personal_mvp_daily_advisory_review_index(root=tmp_path / "out")

    assert result.rows[0]["symbols_preview"].split(";")[0] == "000001"
    rows = pd.read_csv(result.artifact_paths["index_csv"], dtype=str).fillna("")
    assert rows.iloc[0]["symbols_preview"].split(";")[0] == "000001"


def test_health_warns_for_safe_no_context_artifact(tmp_path: Path) -> None:
    run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert result.warning_count >= 1


def test_health_passes_for_safe_daily_review_rows_artifact(tmp_path: Path) -> None:
    source_root = tmp_path / "reports"
    _write_signal_artifact(source_root)
    run_personal_mvp_daily_advisory_review(root=source_root, output_dir=tmp_path / "out", review_date="2024-05-20")

    result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")

    assert result.status == "PASS"
    assert result.error_count == 0


def test_health_warns_for_stale_context_without_unsafe_flags(tmp_path: Path) -> None:
    source_root = tmp_path / "reports"
    _write_signal_artifact(source_root, decision_date="2024-05-01")
    run_personal_mvp_daily_advisory_review(
        root=source_root,
        output_dir=tmp_path / "out",
        review_date="2024-05-20",
        stale_after_days=7,
    )

    result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")

    assert result.status == "WARN"
    assert result.error_count == 0


def test_health_fails_for_missing_required_artifact_files(tmp_path: Path) -> None:
    run = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")
    run.artifact_paths["daily_advisory_review_report"].unlink()

    result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")

    assert result.status == "FAIL"
    assert "MISSING_REQUIRED_ARTIFACT" in _issue_codes(result)


def test_health_fails_for_forbidden_runtime_flags(tmp_path: Path) -> None:
    run = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    for field in ["buy_review_allowed", "trading_allowed", "broker_api_called", "order_placed", "message_sent"]:
        _set_flag(run.artifact_paths["metadata"], field, True)
        result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")
        assert result.status == "FAIL"
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)
        _set_flag(run.artifact_paths["metadata"], field, False)


def test_health_fails_for_unsafe_report_wording(tmp_path: Path) -> None:
    run = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")
    run.artifact_paths["daily_advisory_review_report"].write_text("buy now and place order\n", encoding="utf-8")

    result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")

    assert result.status == "FAIL"
    assert "UNSAFE_ACTION_WORDING" in _issue_codes(result)


def test_health_fails_for_current_candidates_snapshots_signal_semantics_and_protected_writes(tmp_path: Path) -> None:
    run = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    for field in ["current_candidates_run", "snapshot_built", "signal_semantics_mutated", "data_raw_written"]:
        _set_flag(run.artifact_paths["metadata"], field, True)
        result = check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")
        assert result.status == "FAIL"
        assert "FORBIDDEN_METADATA_FLAG_TRUE" in _issue_codes(result)
        _set_flag(run.artifact_paths["metadata"], field, False)


def test_status_summarizes_latest_artifact_and_recommended_next_task(tmp_path: Path) -> None:
    run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    result = run_personal_mvp_daily_advisory_review_status(root=tmp_path / "out")

    assert result.latest_status == "DAILY_ADVISORY_REVIEW_NO_LOCAL_CONTEXT"
    assert "Research-Status Integration Planning" in result.recommended_next_task
    assert result.artifact_paths["status_csv"].exists()
    assert result.artifact_paths["metadata_json"].exists()


def test_cli_index_health_status_commands(tmp_path: Path, capsys) -> None:
    run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")

    index_code = cli.main(["personal-mvp-daily-advisory-review-index", "--root", str(tmp_path / "out")])
    index_output = capsys.readouterr().out
    health_code = cli.main(["personal-mvp-daily-advisory-review-health", "--root", str(tmp_path / "out")])
    health_output = capsys.readouterr().out
    status_code = cli.main(["personal-mvp-daily-advisory-review-status", "--root", str(tmp_path / "out")])
    status_output = capsys.readouterr().out

    assert index_code == 0
    assert "artifact_count: 1" in index_output
    assert health_code == 0
    assert "status: WARN" in health_output
    assert status_code == 0
    assert "recommended_next_task:" in status_output


def test_cli_health_reports_fail_for_unsafe_artifacts(tmp_path: Path, capsys) -> None:
    run = run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")
    _set_flag(run.artifact_paths["metadata"], "trading_allowed", True)

    code = cli.main(["personal-mvp-daily-advisory-review-health", "--root", str(tmp_path / "out")])
    output = capsys.readouterr().out

    assert code == 1
    assert "status: FAIL" in output


def test_no_docs_project_sources_created(tmp_path: Path) -> None:
    run_personal_mvp_daily_advisory_review(root=tmp_path / "reports", output_dir=tmp_path / "out")
    build_personal_mvp_daily_advisory_review_index(root=tmp_path / "out")
    check_personal_mvp_daily_advisory_review_health(root=tmp_path / "out")
    run_personal_mvp_daily_advisory_review_status(root=tmp_path / "out")

    assert not (tmp_path / "docs" / "project_sources").exists()


def _issue_codes(result) -> set[str]:
    return {row["issue_code"] for row in result.rows}


def _set_flag(path: Path, field: str, value: bool) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[field] = value
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_signal_artifact(root: Path, decision_date: str = "2024-05-20") -> None:
    artifact = root / "signals" / "signal-run-views"
    artifact.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "signal_id": "signal-000001",
                "signal_run_id": "signal-run-views",
                "signal_date": decision_date,
                "decision_date": decision_date,
                "symbol": "000001",
                "name": "Name 000001",
                "instrument_type": "stock",
                "universe_name": "stock_core",
                "advisory_action": "WATCH",
                "final_score": 60.0,
                "confidence_level": "medium",
                "reason_summary": "watch reason",
                "risk_notes": "risk note",
                "data_source_notes": "data note",
                "demo_mode": False,
                "not_strategy_recommendation": False,
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
            }
        ]
    ).to_csv(artifact / "signals.csv", index=False)
    (artifact / "signal_advisory_report.md").write_text("# Signal report\n", encoding="utf-8")
    (artifact / "metadata.json").write_text(
        json.dumps(
            {
                "signal_run_id": "signal-run-views",
                "status": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "workflow_stage": "SIGNAL_ADVISORY_READY_FOR_REVIEW",
                "signal_count": 1,
                "report_path": str(artifact / "signal_advisory_report.md"),
                "signals_path": str(artifact / "signals.csv"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
