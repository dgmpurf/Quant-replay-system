import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.activated_replacement_worklist_evidence_update_plan import (
    build_activated_replacement_worklist_evidence_update_plan,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_health import (
    check_activated_replacement_worklist_evidence_update_plan_health,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_index import (
    build_activated_replacement_worklist_evidence_update_plan_index,
)
from quant_replay_system.activated_replacement_worklist_evidence_update_plan_status import (
    run_activated_replacement_worklist_evidence_update_plan_status,
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
STOCKS = ["000001", "000002", "300750", "600000", "600519", "601318", "688981"]
ETFS = ["159915", "510300"]


def test_builds_profile_specific_evidence_update_plan(tmp_path: Path) -> None:
    activation = _write_activation_csv(tmp_path)

    result = build_activated_replacement_worklist_evidence_update_plan(
        activation=activation,
        output_dir=tmp_path / "plan",
    )

    assert result.row_count == 72
    assert result.stock_core_row_count == 56
    assert result.etf_core_row_count == 16
    assert result.mixed_demo_core_row_count == 0
    assert result.include_flag_true_count == 0
    assert result.valid_for_signal_date_count == 0
    assert result.approved_count == 0
    assert result.rejected_count == 0
    assert result.clean_review_updates_created is False

    stock_template = pd.read_csv(result.artifact_paths["stock_core_update_template"], dtype=str).fillna("")
    etf_template = pd.read_csv(result.artifact_paths["etf_core_update_template"], dtype=str).fillna("")
    assert len(stock_template) == 56
    assert len(etf_template) == 16
    assert stock_template.iloc[0]["symbol"] == "000001"
    assert set(stock_template["universe_name"]) == {"stock_core"}
    assert set(etf_template["universe_name"]) == {"etf_core"}
    assert set(stock_template["review_status"]) == {"NEEDS_MANUAL_REVIEW"}
    assert set(stock_template["include_flag"]) == {"False"}
    assert set(stock_template["valid_for_signal_date"]) == {"False"}
    assert set(stock_template["survivorship_bias_resolved"]) == {"False"}
    assert "listed_date" in stock_template.columns
    assert "as_of_date" in stock_template.columns
    assert "activation_id" in stock_template.columns
    assert "source_policy_audit_id" in stock_template.columns

    stock_batch = pd.read_csv(result.artifact_paths["stock_core_first_batch_package"], dtype=str).fillna("")
    etf_batch = pd.read_csv(result.artifact_paths["etf_core_first_batch_package"], dtype=str).fillna("")
    assert set(stock_batch["symbol"]) == {"000001"}
    assert len(stock_batch) == 8
    assert set(etf_batch["symbol"]) == {"159915"}
    assert len(etf_batch) == 8


def test_index_health_and_status_for_safe_plan(tmp_path: Path) -> None:
    activation = _write_activation_csv(tmp_path)
    build_activated_replacement_worklist_evidence_update_plan(activation=activation, output_dir=tmp_path / "plan")

    index = build_activated_replacement_worklist_evidence_update_plan_index(
        root=tmp_path / "plan",
        output_dir=tmp_path / "index",
    )
    assert index.artifact_count == 1
    row = index.index_frame.iloc[0]
    assert row["row_count"] == 72
    assert row["stock_core_row_count"] == 56
    assert row["etf_core_row_count"] == 16
    assert row["no_universe_export"] == True  # noqa: E712

    health = check_activated_replacement_worklist_evidence_update_plan_health(
        root=tmp_path / "plan",
        output_dir=tmp_path / "health",
    )
    assert health.status == "PASS"
    assert health.issue_count == 0

    status = run_activated_replacement_worklist_evidence_update_plan_status(
        root=tmp_path / "plan",
        output_dir=tmp_path / "status",
    )
    assert status.status == "PASS"
    assert status.workflow_stage == "ACTIVATED_REPLACEMENT_WORKLIST_EVIDENCE_UPDATE_PLAN_READY"
    assert status.row_count == 72
    assert status.stock_core_row_count == 56
    assert status.etf_core_row_count == 16
    assert "profile-specific" in status.next_manual_action


def test_health_fails_if_plan_claims_approval_or_data_write(tmp_path: Path) -> None:
    activation = _write_activation_csv(tmp_path)
    result = build_activated_replacement_worklist_evidence_update_plan(
        activation=activation,
        output_dir=tmp_path / "plan",
    )
    metadata_path = result.artifact_paths["metadata"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["no_approval_applied"] = False
    metadata["no_data_raw_write"] = False
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    health = check_activated_replacement_worklist_evidence_update_plan_health(
        root=tmp_path / "plan",
        output_dir=tmp_path / "health",
    )

    assert health.status == "FAIL"
    issues = set(health.health_frame["issue_code"])
    assert "APPROVAL_APPLIED_DETECTED" in issues
    assert "DATA_RAW_WRITE_DETECTED" in issues


def test_cli_commands_work(tmp_path: Path, capsys) -> None:
    activation = _write_activation_csv(tmp_path)

    assert (
        cli.main(
            [
                "activated-replacement-worklist-evidence-update-plan",
                "--activation",
                str(activation),
                "--output-dir",
                str(tmp_path / "plan"),
            ]
        )
        == 0
    )
    assert "stock_core_row_count: 56" in capsys.readouterr().out

    assert (
        cli.main(
            [
                "activated-replacement-worklist-evidence-update-plan-index",
                "--root",
                str(tmp_path / "plan"),
                "--output-dir",
                str(tmp_path / "index"),
            ]
        )
        == 0
    )
    assert "artifact_count: 1" in capsys.readouterr().out

    assert (
        cli.main(
            [
                "activated-replacement-worklist-evidence-update-plan-health",
                "--root",
                str(tmp_path / "plan"),
                "--output-dir",
                str(tmp_path / "health"),
            ]
        )
        == 0
    )
    assert "Health status: PASS" in capsys.readouterr().out

    assert (
        cli.main(
            [
                "activated-replacement-worklist-evidence-update-plan-status",
                "--root",
                str(tmp_path / "plan"),
                "--output-dir",
                str(tmp_path / "status"),
            ]
        )
        == 0
    )
    assert "workflow_stage: ACTIVATED_REPLACEMENT_WORKLIST_EVIDENCE_UPDATE_PLAN_READY" in capsys.readouterr().out


def test_research_status_includes_evidence_update_plan_and_preserves_paper_priority(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    activation = _write_activation_csv(tmp_path)
    plan = build_activated_replacement_worklist_evidence_update_plan(
        activation=activation,
        output_dir=reports / "activated_replacement_worklist_evidence_update_plan",
    )
    _write_paper_workflow_status(reports)

    result = run_local_research_dashboard(root=reports, output_dir=tmp_path / "dashboard")

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_activated_replacement_worklist_evidence_update_plan_id == plan.plan_id
    assert result.activated_replacement_worklist_evidence_update_plan_status == "PASS"
    assert (
        result.activated_replacement_worklist_evidence_update_plan_stage
        == "ACTIVATED_REPLACEMENT_WORKLIST_EVIDENCE_UPDATE_PLAN_READY"
    )
    assert result.activated_replacement_worklist_evidence_update_plan_stock_core_row_count == 56
    assert result.activated_replacement_worklist_evidence_update_plan_etf_core_row_count == 16
    assert result.activated_replacement_worklist_evidence_update_plan_valid_for_signal_date_count == 0
    assert result.activated_replacement_worklist_evidence_update_plan_clean_review_updates_created is False

    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert exported.iloc[0]["latest_activated_replacement_worklist_evidence_update_plan_id"] == plan.plan_id
    assert metadata["activated_replacement_worklist_evidence_update_plan_stock_core_row_count"] == 56
    assert (
        metadata["component_statuses"]["latest_activated_replacement_worklist_evidence_update_plan_id"]
        == plan.plan_id
    )


def test_no_generation_export_or_trading_side_effects(tmp_path: Path) -> None:
    activation = _write_activation_csv(tmp_path)
    result = build_activated_replacement_worklist_evidence_update_plan(
        activation=activation,
        output_dir=tmp_path / "plan",
    )

    assert result.audit_metadata["active_worklist_mutated"] is False
    assert result.audit_metadata["no_approval_applied"] is True
    assert result.audit_metadata["no_rejection_applied"] is True
    assert result.audit_metadata["no_universe_export"] is True
    assert result.audit_metadata["no_data_raw_write"] is True
    assert result.audit_metadata["no_data_processed_write"] is True
    assert result.audit_metadata["no_current_candidates_generated"] is True
    assert result.audit_metadata["no_snapshot_built"] is True
    assert result.audit_metadata["no_forward_labels"] is True
    assert result.audit_metadata["no_network_api"] is True
    assert result.audit_metadata["no_live_trading"] is True
    assert result.audit_metadata["no_broker_api"] is True
    assert result.audit_metadata["no_order_placement"] is True
    assert result.audit_metadata["no_message_sent"] is True


def _write_activation_csv(tmp_path: Path) -> Path:
    rows = []
    for date in DATES:
        for symbol in STOCKS:
            rows.append(_activation_row(date, symbol, "stock_core", "STOCK", profile_conflict=True))
        for symbol in ETFS:
            rows.append(_activation_row(date, symbol, "etf_core", "ETF", profile_conflict=False))
    path = tmp_path / "activation.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _activation_row(
    signal_date: str,
    symbol: str,
    future_universe_name: str,
    instrument_type: str,
    *,
    profile_conflict: bool,
) -> dict:
    return {
        "activation_id": "a8e74161f9bb",
        "replacement_plan_id": "0774d0a1fdb9",
        "source_split_plan_id": "db2c09268c14",
        "source_worklist_id": "1c7972988f59",
        "source_policy_audit_id": "844794b3aae1",
        "signal_date": signal_date,
        "symbol": symbol,
        "current_universe_name": "etf_core",
        "future_universe_name": future_universe_name,
        "resolved_instrument_type": instrument_type,
        "legacy_classification": "legacy_mixed_demo_universe",
        "profile_rule_applied": "LEGACY_ETF_CORE_SPLIT_BY_INSTRUMENT_TYPE",
        "profile_conflict": profile_conflict,
        "conflict_reason": "Legacy mixed universe split by instrument type." if profile_conflict else "",
        "activation_status": "ACTIVATED_AS_PLANNING_CONTEXT",
        "activated_by": "codex_report_only_review",
        "activated_at": "2026-06-04T00:00:00+08:00",
        "activation_reason": "Activated replacement templates as planning context only.",
        "activation_acknowledged": True,
        "review_status": "NEEDS_MANUAL_REVIEW",
        "include_flag": False,
        "valid_for_signal_date": False,
        "reviewer": "",
        "reviewed_at": "",
        "review_reason": "",
        "evidence_source": "",
        "evidence_path": "",
        "evidence_reference": "",
        "manual_review_required": True,
        "activation_only": True,
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
    folder = root / "paper_trading" / "workflow_status" / "paper-workflow-ready"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
        "workflow_status_id": "paper-workflow-ready",
        "created_at": "2024-05-20T16:15:00",
        "status": "READY",
        "workflow_stage": "PAPER_WORKFLOW_READY",
        "latest_decision_date": "2024-05-20",
        "next_manual_action": "Demo WATCH_ONLY paper workflow validated; no fills were supplied.",
        "total_warning_count": 0,
        "expected_demo_warning_count": 0,
        "stale_warning_count": 0,
        "actionable_warning_count": 0,
        "blocking_error_count": 0,
        "component_statuses": {
            "total_warning_count": 0,
            "expected_demo_warning_count": 0,
            "stale_warning_count": 0,
            "actionable_warning_count": 0,
            "blocking_error_count": 0,
        },
        "output_files": {"paper_workflow_status_report": str(report)},
        "warnings": [],
        "live_trading_enabled": False,
        "broker_api_invoked": False,
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
