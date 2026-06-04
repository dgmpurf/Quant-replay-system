from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.pit_evidence_policy_profile_comparison import (
    COMPARISON_COLUMNS,
    build_pit_evidence_policy_profile_comparison,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_health import (
    check_pit_evidence_policy_profile_comparison_health,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_index import (
    build_pit_evidence_policy_profile_comparison_index,
)
from quant_replay_system.pit_evidence_policy_profile_comparison_status import (
    run_pit_evidence_policy_profile_comparison_status,
)


def test_eod_profile_is_opt_in_and_keeps_strict_reference(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path)
    updates = _write_updates(tmp_path)
    policy_audit = _write_policy_audit(tmp_path)

    result = build_pit_evidence_policy_profile_comparison(
        validator=validator,
        completed_updates=updates,
        policy_audit=policy_audit,
        profile="EOD_POST_CLOSE_LOW_BUDGET_PIT",
        decision_policy="EOD_POST_CLOSE",
        output_dir=tmp_path / "comparison",
    )

    assert result.profile_name == "EOD_POST_CLOSE_LOW_BUDGET_PIT"
    assert result.reference_profile_name == "STRICT_PIT"
    assert result.profile_is_opt_in is True
    assert result.strict_default_unchanged is True
    assert result.row_count == 4
    assert result.strict_checklist_pass_count == 0
    assert result.eod_low_budget_checklist_pass_count == 0
    assert result.remaining_blocked_count == 4
    assert set(result.comparison_frame["symbol"]) == {"000001", "159915"}
    assert result.comparison_frame["symbol"].iloc[0] == "000001"


def test_eod_policy_relaxes_timing_only_and_keeps_non_relaxed_blockers(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path)
    updates = _write_updates(tmp_path)
    policy_audit = _write_policy_audit(tmp_path)

    result = build_pit_evidence_policy_profile_comparison(
        validator=validator,
        completed_updates=updates,
        policy_audit=policy_audit,
        profile="EOD_POST_CLOSE_LOW_BUDGET_PIT",
        decision_policy="EOD_POST_CLOSE",
        decision_time="16:00:00",
        output_dir=tmp_path / "comparison",
    )

    row = result.comparison_frame.loc[result.comparison_frame["symbol"] == "000001"].iloc[0]
    assert row["available_time_within_decision_time"] is True
    assert "PIT_TIMING_BLOCKED" in row["relaxed_blockers"]
    assert row["same_day_market_cache_used_as_support"] is True
    assert row["active_context_supported_by_cache"] is True
    assert row["suspension_context_supported_by_cache"] is True
    assert row["not_delisted_still_required"] is True
    assert row["st_no_st_still_required"] is True
    assert row["survivorship_still_required"] is True
    assert row["checklist_pass_under_eod_low_budget"] is False
    assert row["should_apply_approval"] is False


def test_complete_etf_row_can_be_preview_only_under_eod_profile(tmp_path: Path) -> None:
    validator = _write_validator_artifact(tmp_path, complete_etf=True)
    updates = _write_updates(tmp_path, complete_etf=True)
    policy_audit = _write_policy_audit(tmp_path)

    result = build_pit_evidence_policy_profile_comparison(
        validator=validator,
        completed_updates=updates,
        policy_audit=policy_audit,
        profile="EOD_POST_CLOSE_LOW_BUDGET_PIT",
        decision_policy="EOD_POST_CLOSE",
        decision_time="16:00:00",
        output_dir=tmp_path / "comparison",
    )

    assert result.eod_low_budget_checklist_pass_count == 1
    etf = result.comparison_frame.loc[result.comparison_frame["symbol"] == "159915"].iloc[0]
    assert etf["approval_candidate_preview_only"] is True
    assert etf["should_apply_approval"] is False
    assert etf["no_pit_review_run"] is True
    assert etf["no_universe_export"] is True


def test_index_health_status_and_cli_work(tmp_path: Path, capsys) -> None:
    validator = _write_validator_artifact(tmp_path)
    updates = _write_updates(tmp_path)
    policy_audit = _write_policy_audit(tmp_path)
    root = tmp_path / "comparison"
    build_pit_evidence_policy_profile_comparison(
        validator=validator,
        completed_updates=updates,
        policy_audit=policy_audit,
        profile="EOD_POST_CLOSE_LOW_BUDGET_PIT",
        decision_policy="EOD_POST_CLOSE",
        output_dir=root,
    )

    index = build_pit_evidence_policy_profile_comparison_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_evidence_policy_profile_comparison_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_evidence_policy_profile_comparison_status(root=root, output_dir=tmp_path / "status")

    assert index["artifact_count"] == 1
    assert health["status"] == "PASS"
    assert status["workflow_stage"] == "PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED"

    code = cli.main(["pit-evidence-policy-profile-comparison-status", "--root", str(root), "--output-dir", str(tmp_path / "cli-status")])
    output = capsys.readouterr()
    assert code == 0
    assert "workflow_stage: PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED" in output.out


def test_cli_comparison_command_works(tmp_path: Path, capsys) -> None:
    validator = _write_validator_artifact(tmp_path)
    updates = _write_updates(tmp_path)
    policy_audit = _write_policy_audit(tmp_path)

    code = cli.main(
        [
            "pit-evidence-policy-profile-comparison",
            "--validator",
            str(validator),
            "--completed-updates",
            str(updates),
            "--policy-audit",
            str(policy_audit),
            "--profile",
            "EOD_POST_CLOSE_LOW_BUDGET_PIT",
            "--decision-policy",
            "EOD_POST_CLOSE",
            "--output-dir",
            str(tmp_path / "comparison"),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "profile_name: EOD_POST_CLOSE_LOW_BUDGET_PIT" in output.out
    assert "eod_low_budget_checklist_pass_count: 0" in output.out
    assert "No approval applied" in output.out


def _write_validator_artifact(tmp_path: Path, *, complete_etf: bool = False) -> Path:
    root = tmp_path / "validator" / "validator-a"
    root.mkdir(parents=True, exist_ok=True)
    validation_rows = []
    for row in _update_rows(complete_etf=complete_etf):
        is_complete_etf = complete_etf and row["symbol"] == "159915" and row["signal_date"] == "2024-04-02"
        validation_rows.append(
            {
                "validator_id": "validator-a",
                "signal_date": row["signal_date"],
                "symbol": row["symbol"],
                "universe_name": row["universe_name"],
                "profile": row["universe_name"],
                "review_status": row["review_status"],
                "checklist_status": "CHECKLIST_PASS_APPROVAL_CANDIDATE" if is_complete_etf else "CHECKLIST_BLOCKED_PIT_TIMING",
                "checklist_pass": is_complete_etf,
                "blocked": not is_complete_etf,
                "blocker_reason": "" if is_complete_etf else "PIT timing blocked; survivorship unresolved",
                "missing_required_fields": "" if is_complete_etf else "as_of_date, is_active, listed_date",
                "unacceptable_source_fields": "",
                "pit_timing_blocker": not is_complete_etf,
                "survivorship_blocker": not is_complete_etf,
                "stock_st_blocker": row["universe_name"] == "stock_core",
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "checklist_validation_only": True,
            }
        )
    validation = pd.DataFrame(validation_rows)
    summary = pd.DataFrame(
        [
            {
                "validator_id": "validator-a",
                "status": "WARN",
                "row_count": len(validation),
                "checklist_pass_count": int(validation["checklist_pass"].sum()),
                "blocked_count": int(validation["blocked"].sum()),
                "stock_core_blocked_count": int(((validation["profile"] == "stock_core") & validation["blocked"]).sum()),
                "etf_core_blocked_count": int(((validation["profile"] == "etf_core") & validation["blocked"]).sum()),
                "missing_evidence_count": int((validation["missing_required_fields"] != "").sum()),
                "unacceptable_source_count": 0,
                "pit_timing_blocked_count": int(validation["pit_timing_blocker"].sum()),
                "survivorship_blocked_count": int(validation["survivorship_blocker"].sum()),
                "stock_st_blocked_count": int(validation["stock_st_blocker"].sum()),
            }
        ]
    )
    validation.to_csv(root / "pit_evidence_checklist_validation.csv", index=False)
    summary.to_csv(root / "pit_evidence_checklist_validation_summary.csv", index=False)
    pd.DataFrame().to_csv(root / "missing_evidence_matrix.csv", index=False)
    pd.DataFrame().to_csv(root / "approval_candidate_preview.csv", index=False)
    (root / "report.md").write_text("No approval applied.", encoding="utf-8")
    (root / "metadata.json").write_text(
        '{"validator_id":"validator-a","status":"WARN","row_count":4,"checklist_pass_count":0,'
        '"blocked_count":4,"stock_core_blocked_count":2,"etf_core_blocked_count":2,'
        '"no_approval_applied":true,"no_universe_export":true,"no_data_raw_write":true,'
        '"no_data_processed_write":true,"no_current_candidates_generated":true,'
        '"no_snapshot_built":true,"no_forward_labels":true,"no_live_trading":true,'
        '"no_broker_api":true,"no_order_placement":true,"no_message_sent":true,'
        '"checklist_validation_only":true,'
        '"output_files":{"report":"report.md","validation_csv":"pit_evidence_checklist_validation.csv",'
        '"summary_csv":"pit_evidence_checklist_validation_summary.csv"}}',
        encoding="utf-8",
    )
    return root


def _write_updates(tmp_path: Path, *, complete_etf: bool = False) -> Path:
    path = tmp_path / "updates.csv"
    pd.DataFrame(_update_rows(complete_etf=complete_etf), columns=COMPARISON_COLUMNS[:0] or None).to_csv(path, index=False)
    return path


def _update_rows(*, complete_etf: bool = False) -> list[dict]:
    rows = []
    for symbol, universe in [("000001", "stock_core"), ("159915", "etf_core")]:
        for date in ["2024-04-02", "2024-04-09"]:
            complete = complete_etf and symbol == "159915" and date == "2024-04-02"
            rows.append(
                {
                    "signal_date": date,
                    "symbol": symbol,
                    "universe_name": universe,
                    "review_status": "NEEDS_MORE_EVIDENCE",
                    "include_flag": "False",
                    "reviewer": "tester",
                    "reviewed_at": "2026-06-04T10:00:00+08:00",
                    "review_reason": "comparison test",
                    "evidence_source": "official_public_sources;local_market_cache_context",
                    "evidence_path": "data/cache/market/daily_bars.csv",
                    "evidence_reference": f"local_market_cache:{symbol}:{date}",
                    "listed_date": "1991-04-03" if symbol == "000001" else "2011-12-09",
                    "delisted_date": "",
                    "is_active": "True" if complete else "",
                    "is_st": "False" if universe == "stock_core" else "",
                    "is_suspended": "False",
                    "listed_date_evidence": "official",
                    "delisted_date_evidence": "official" if complete else "",
                    "is_active_evidence": "reviewed_local_cache_eod" if complete else "",
                    "survivorship_bias_resolved": "True" if complete else "False",
                    "as_of_date": date if complete else "",
                    "name": "Ping An Bank" if symbol == "000001" else "ChiNext ETF",
                    "instrument_type": "STOCK" if universe == "stock_core" else "ETF",
                    "exchange": "SZSE",
                    "industry": "Bank" if universe == "stock_core" else "ETF",
                    "min_lot": "100",
                    "t_plus_rule": "T+1",
                    "available_time": f"{date} 15:30:00",
                    "revision_id": "draft",
                    "source": "AKSHARE_OPTIONAL",
                }
            )
    return rows


def _write_policy_audit(tmp_path: Path) -> Path:
    root = tmp_path / "policy-audit"
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "field_name": "available_time",
                "eod_post_close_low_budget_rule": "May accept if available_time <= decision_time.",
            }
        ]
    ).to_csv(root / "policy_profile_field_rules.csv", index=False)
    (root / "eod_post_close_low_budget_pit_policy_report.md").write_text("profile is opt-in", encoding="utf-8")
    return root
