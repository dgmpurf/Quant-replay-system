import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.first_batch_reviewer_evidence_completion_plan import (
    build_first_batch_reviewer_evidence_completion_plan,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_health import (
    check_first_batch_reviewer_evidence_completion_plan_health,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_index import (
    build_first_batch_reviewer_evidence_completion_plan_index,
)
from quant_replay_system.first_batch_reviewer_evidence_completion_plan_status import (
    run_first_batch_reviewer_evidence_completion_plan_status,
)
from quant_replay_system.local_research_dashboard import run_local_research_dashboard


DATES = [
    "2024-04-02",
    "2024-04-09",
    "2024-04-11",
    "2024-04-16",
    "2024-04-19",
    "2024-04-24",
    "2024-04-26",
    "2024-05-06",
]
EXCEPTION_TYPES = [
    "DELISTING",
    "ST_RISK_WARNING",
    "SUSPENSION_RESUMPTION",
    "SURVIVORSHIP_RATIONALE",
]


def test_builds_report_only_first_batch_completion_plan(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)

    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )

    assert result.row_count == 16
    assert result.stock_core_row_count == 8
    assert result.etf_core_row_count == 8
    assert result.reviewer_completion_required_count == 16
    assert result.no_hit_acceptance_required_count == 16
    assert result.survivorship_rationale_required_count == 16
    assert result.metadata_completion_required_count == 16
    assert result.checklist_pass_count == 0
    assert result.remaining_blocked_count == 16
    assert result.clean_review_updates_created is False
    assert result.approval_applied is False

    plan = pd.read_csv(result.artifact_paths["plan_csv"], dtype=str, keep_default_na=False)
    assert len(plan) == 16
    assert set(plan["symbol"]) == {"000001", "159915"}
    assert set(plan["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert set(plan["include_flag"]) == {"False"}
    assert set(plan["valid_for_signal_date"]) == {"False"}
    assert set(plan["survivorship_bias_resolved"]) == {"False"}
    assert set(plan["approved_for_pit_universe_candidate"]) == {"False"}
    assert set(plan["reviewer_completion_required"]) == {"True"}
    assert set(plan["strong_official_date_specific_quotation"]) == {"True"}
    assert set(plan["quotation_proves_not_delisted"]) == {"False"}
    assert set(plan["quotation_proves_st_no_st"]) == {"False"}
    assert set(plan["quotation_resolves_survivorship"]) == {"False"}

    template = pd.read_csv(result.artifact_paths["reviewer_completion_template"], dtype=str, keep_default_na=False)
    assert "APPROVED_FOR_PIT_UNIVERSE" not in set(template["review_status"])
    assert set(template["include_flag"]) == {"False"}
    assert set(template["valid_for_signal_date"]) == {"False"}
    assert set(template["symbol"]) == {"000001", "159915"}

    assert not (result.artifact_paths["artifact_dir"] / "review_updates.csv").exists()
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def test_outputs_missing_evidence_and_todo_matrices(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )

    missing = pd.read_csv(result.artifact_paths["row_level_missing_evidence_matrix"], dtype=str, keep_default_na=False)
    no_hit = pd.read_csv(result.artifact_paths["reviewer_no_hit_acceptance_todo"], dtype=str, keep_default_na=False)
    survivorship = pd.read_csv(result.artifact_paths["survivorship_rationale_todo"], dtype=str, keep_default_na=False)
    metadata = pd.read_csv(result.artifact_paths["metadata_completion_todo"], dtype=str, keep_default_na=False)

    assert len(missing) == 16
    assert "as_of_date" in missing.loc[0, "missing_evidence_fields"]
    assert len(no_hit) == 64
    assert set(no_hit["exception_type"]) == set(EXCEPTION_TYPES)
    assert set(no_hit["acceptance_status"]) == {"NEEDS_REVIEW"}
    assert len(survivorship) == 16
    assert len(metadata) == 16

    reusable = pd.read_csv(result.artifact_paths["reusable_symbol_level_evidence_plan"], dtype=str, keep_default_na=False)
    date_specific = pd.read_csv(result.artifact_paths["date_specific_evidence_plan"], dtype=str, keep_default_na=False)
    assert set(reusable["symbol"]) == {"000001", "159915"}
    assert set(date_specific["symbol"]) == {"000001", "159915"}
    assert set(date_specific["signal_date"]) == set(DATES)


def test_index_health_status_and_cli_for_completion_plan(tmp_path: Path, capsys) -> None:
    inputs = _write_inputs(tmp_path)
    assert (
        cli.main(
            [
                "first-batch-reviewer-evidence-completion-plan",
                "--evidence-update-plan",
                str(inputs["evidence_update_plan"]),
                "--downstream-impact",
                str(inputs["downstream_impact"]),
                "--enrichment",
                str(inputs["enrichment"]),
                "--validator",
                str(inputs["validator"]),
                "--policy-comparison",
                str(inputs["policy_comparison"]),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        == 0
    )
    assert "row_count: 16" in capsys.readouterr().out

    index = build_first_batch_reviewer_evidence_completion_plan_index(
        root=tmp_path / "out",
        output_dir=tmp_path / "index",
    )
    assert index.artifact_count == 1
    assert index.index_frame.iloc[0]["reviewer_completion_required_count"] == 16

    health = check_first_batch_reviewer_evidence_completion_plan_health(
        root=tmp_path / "out",
        output_dir=tmp_path / "health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_first_batch_reviewer_evidence_completion_plan_status(
        root=tmp_path / "out",
        output_dir=tmp_path / "status",
    )
    assert status.status == "WARN"
    assert status.workflow_stage == "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW"
    assert status.row_count == 16
    assert status.clean_review_updates_created is False
    assert status.approval_applied is False

    for command in [
        "first-batch-reviewer-evidence-completion-plan-index",
        "first-batch-reviewer-evidence-completion-plan-health",
        "first-batch-reviewer-evidence-completion-plan-status",
    ]:
        assert cli.main([command, "--root", str(tmp_path / "out"), "--output-dir", str(tmp_path / command)]) == 0
    output = capsys.readouterr().out
    assert "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW" in output


def test_health_fails_if_completion_plan_claims_approval_or_clean_updates(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    result = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=tmp_path / "out",
    )
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    metadata["approval_applied"] = True
    metadata["clean_review_updates_created"] = True
    result.artifact_paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

    health = check_first_batch_reviewer_evidence_completion_plan_health(
        root=tmp_path / "out",
        output_dir=tmp_path / "health",
    )

    assert health.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in set(health.health_frame["issue_code"])
    assert "CLEAN_REVIEW_UPDATES_DETECTED" in set(health.health_frame["issue_code"])


def test_research_status_includes_completion_plan_and_preserves_paper_priority(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    inputs = _write_inputs(tmp_path / "inputs")
    plan = build_first_batch_reviewer_evidence_completion_plan(
        evidence_update_plan=inputs["evidence_update_plan"],
        downstream_impact=inputs["downstream_impact"],
        enrichment=inputs["enrichment"],
        validator=inputs["validator"],
        policy_comparison=inputs["policy_comparison"],
        output_dir=reports / "first_batch_reviewer_evidence_completion_plan",
    )
    _write_paper_workflow_status(reports)

    result = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_first_batch_reviewer_evidence_completion_plan_id == plan.plan_id
    assert result.first_batch_reviewer_evidence_completion_plan_stage == (
        "FIRST_BATCH_REVIEWER_EVIDENCE_COMPLETION_PLAN_NEEDS_REVIEW"
    )
    assert result.first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count == 16
    assert result.first_batch_reviewer_evidence_completion_plan_clean_review_updates_created is False
    assert result.first_batch_reviewer_evidence_completion_plan_approval_applied is False

    summary = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str, keep_default_na=False)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert summary.iloc[0]["latest_first_batch_reviewer_evidence_completion_plan_id"] == plan.plan_id
    assert metadata["first_batch_reviewer_evidence_completion_plan_reviewer_completion_required_count"] == 16


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    evidence_update_plan = _write_evidence_update_plan(tmp_path)
    downstream = _write_downstream_impact(tmp_path)
    enrichment = _write_enrichment(tmp_path)
    validator = _write_validator(tmp_path)
    policy = _write_policy_comparison(tmp_path)
    return {
        "evidence_update_plan": evidence_update_plan,
        "downstream_impact": downstream,
        "enrichment": enrichment,
        "validator": validator,
        "policy_comparison": policy,
    }


def _write_evidence_update_plan(tmp_path: Path) -> Path:
    root = tmp_path / "activated_replacement_worklist_evidence_update_plan" / "plan123"
    root.mkdir(parents=True)
    rows = [_first_batch_row(date, "000001", "stock_core", "STOCK") for date in DATES]
    rows += [_first_batch_row(date, "159915", "etf_core", "ETF") for date in DATES]
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "activated_replacement_worklist_evidence_update_plan.csv", index=False)
    frame.loc[frame["universe_name"] == "stock_core"].to_csv(root / "stock_core_first_batch_package.csv", index=False)
    frame.loc[frame["universe_name"] == "etf_core"].to_csv(root / "etf_core_first_batch_package.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "plan_id": "plan123",
                "activation_id": "activation123",
                "acceptance_id": "acceptance123",
                "replacement_plan_id": "replacement123",
                "source_split_plan_id": "split123",
                "source_policy_audit_id": "policy123",
                "source_worklist_id": "legacy123",
                "output_files": {
                    "stock_core_first_batch_package": str(root / "stock_core_first_batch_package.csv"),
                    "etf_core_first_batch_package": str(root / "etf_core_first_batch_package.csv"),
                },
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_downstream_impact(tmp_path: Path) -> Path:
    root = tmp_path / "reviewer_no_hit_acceptance_downstream_impact" / "impact123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        for exception_type in EXCEPTION_TYPES:
            rows.append(
                {
                    "impact_id": "impact123",
                    "acceptance_id": "acceptance_no_hit123",
                    "enrichment_id": "enrichment123",
                    "source_packet_id": "packet123",
                    "reviewed_no_hit_policy_comparison_id": "comparison123",
                    "validator_id": "validator123",
                    "signal_date": date,
                    "symbol": symbol,
                    "universe_name": universe,
                    "exception_type": exception_type,
                    "acceptance_status": "NEEDS_REVIEW",
                    "accepted_no_hit_context": False,
                    "accepted_no_hit_context_only": False,
                    "checklist_pass_after": False,
                    "remaining_blocked": True,
                    "approval_applied": False,
                    "pit_review_run": False,
                    "export_readiness_run": False,
                    "export_staging_run": False,
                    "universe_exported": False,
                    "no_clean_review_updates_created": True,
                    "no_data_raw_write": True,
                    "no_data_processed_write": True,
                    "no_current_candidates_generated": True,
                    "impact_only": True,
                }
            )
    pd.DataFrame(rows).to_csv(root / "reviewer_no_hit_acceptance_downstream_impact.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "impact_id": "impact123",
                "acceptance_id": "acceptance_no_hit123",
                "enrichment_id": "enrichment123",
                "source_packet_id": "packet123",
                "reviewed_no_hit_policy_comparison_id": "comparison123",
                "validator_id": "validator123",
                "accepted_no_hit_context_count": 0,
                "checklist_pass_count": 0,
                "remaining_blocked_count": 16,
                "approval_applied": False,
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_enrichment(tmp_path: Path) -> Path:
    root = tmp_path / "pit_official_status_evidence_packet_enrichment" / "enrichment123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        rows.append(
            {
                "enrichment_id": "enrichment123",
                "source_packet_id": "packet123",
                "policy_comparison_id": "comparison123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "strong_official_date_specific_quotation": True,
                "quotation_source_url": f"https://example.test/{symbol}/{date}",
                "reviewed_no_hit_context_supported": True,
                "reviewer_acceptance_required": True,
                "missing_evidence_categories": (
                    "active_not_delisted_evidence; pit_safe_as_of_date; reviewer_no_hit_acceptance; "
                    "stock_st_no_st_evidence; survivorship_bias_resolution"
                ),
                "remaining_blocked": True,
                "checklist_pass": False,
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_current_candidates_generated": True,
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_official_status_evidence_packet_enrichment.csv", index=False)
    (root / "metadata.json").write_text(json.dumps({"enrichment_id": "enrichment123"}), encoding="utf-8")
    return root


def _write_validator(tmp_path: Path) -> Path:
    root = tmp_path / "pit_evidence_checklist_validator" / "validator123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        missing = "as_of_date, industry, is_active, is_active_evidence, revision_id, t_plus_rule"
        if symbol == "000001":
            missing += ", is_st"
        rows.append(
            {
                "validator_id": "validator123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "checklist_pass": False,
                "blocked": True,
                "missing_required_fields": missing,
                "blocker_reason": "missing evidence; PIT timing blocked; survivorship unresolved",
                "survivorship_blocker": True,
                "stock_st_blocker": symbol == "000001",
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_evidence_checklist_validation.csv", index=False)
    (root / "metadata.json").write_text(
        json.dumps({"validator_id": "validator123", "checklist_pass_count": 0, "blocked_count": 16}),
        encoding="utf-8",
    )
    return root


def _write_policy_comparison(tmp_path: Path) -> Path:
    root = tmp_path / "pit_evidence_policy_profile_comparison" / "comparison123"
    root.mkdir(parents=True)
    rows = []
    for date, symbol, universe in _targets():
        rows.append(
            {
                "comparison_id": "comparison123",
                "signal_date": date,
                "symbol": symbol,
                "universe_name": universe,
                "recommended_future_universe": universe,
                "reviewed_no_hit_support_pass": False,
                "remaining_blockers": "survivorship_bias_resolved remains false",
            }
        )
    pd.DataFrame(rows).to_csv(root / "pit_evidence_policy_profile_comparison.csv", index=False)
    (root / "metadata.json").write_text(json.dumps({"comparison_id": "comparison123"}), encoding="utf-8")
    return root


def _targets() -> list[tuple[str, str, str]]:
    return [(date, "000001", "stock_core") for date in DATES] + [(date, "159915", "etf_core") for date in DATES]


def _first_batch_row(date: str, symbol: str, universe: str, instrument_type: str) -> dict[str, object]:
    return {
        "plan_id": "plan123",
        "activation_id": "activation123",
        "acceptance_id": "acceptance123",
        "replacement_plan_id": "replacement123",
        "source_split_plan_id": "split123",
        "source_policy_audit_id": "policy123",
        "source_worklist_id": "legacy123",
        "signal_date": date,
        "symbol": symbol,
        "current_universe_name": "etf_core",
        "future_universe_name": universe,
        "universe_name": universe,
        "resolved_instrument_type": instrument_type,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "include_flag": False,
        "valid_for_signal_date": False,
        "survivorship_bias_resolved": False,
        "manual_review_required": True,
        "evidence_update_planning_only": True,
        "clean_review_updates_created": False,
        "active_worklist_mutated": False,
        "no_approval_applied": True,
        "no_rejection_applied": True,
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
    }


def _write_paper_workflow_status(root: Path) -> None:
    status_dir = root / "paper_trading" / "workflow_status" / "paper-ready"
    status_dir.mkdir(parents=True)
    report = status_dir / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    (status_dir / "metadata.json").write_text(
        json.dumps(
            {
                "workflow_status_id": "paper-ready",
                "created_at": "2024-05-20T16:15:00",
                "status": "WARN",
                "workflow_stage": "WATCH_ONLY_DEMO_VALIDATED_NO_FILLS",
                "latest_decision_date": "2024-05-20",
                "next_manual_action": "Continue WATCH_ONLY paper workflow.",
                "total_warning_count": 1,
                "expected_demo_warning_count": 1,
                "stale_warning_count": 0,
                "actionable_warning_count": 0,
                "blocking_error_count": 0,
                "component_statuses": {
                    "total_warning_count": 1,
                    "expected_demo_warning_count": 1,
                    "stale_warning_count": 0,
                    "actionable_warning_count": 0,
                    "blocking_error_count": 0,
                },
                "output_files": {"paper_workflow_status_report": str(report)},
                "warnings": [],
                "live_trading_enabled": False,
                "broker_api_invoked": False,
            }
        ),
        encoding="utf-8",
    )
