import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.local_research_dashboard import run_local_research_dashboard
from quant_replay_system.reviewed_replacement_worklist_acceptance import (
    build_reviewed_replacement_worklist_acceptance,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_health import (
    check_reviewed_replacement_worklist_acceptance_health,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_index import (
    build_reviewed_replacement_worklist_acceptance_index,
)
from quant_replay_system.reviewed_replacement_worklist_acceptance_status import (
    run_reviewed_replacement_worklist_acceptance_status,
)
from quant_replay_system.reviewed_replacement_worklist_plan import build_reviewed_replacement_worklist_plan
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_split_worklist_plan import build_universe_profile_split_worklist_plan


def test_index_detects_acceptance_artifacts(tmp_path: Path) -> None:
    root = _build_acceptance_root(tmp_path)

    result = build_reviewed_replacement_worklist_acceptance_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["row_count"] == 3
    assert row["stock_core_row_count"] == 2
    assert row["etf_core_row_count"] == 1
    assert row["acceptance_acknowledged"] == True  # noqa: E712
    assert row["active_worklist_mutated"] == False  # noqa: E712
    assert row["no_approval_applied"] == True  # noqa: E712


def test_health_passes_for_safe_acceptance(tmp_path: Path) -> None:
    root = _build_acceptance_root(tmp_path)

    result = check_reviewed_replacement_worklist_acceptance_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "PASS"
    assert result.issue_count == 0
    assert result.error_count == 0


def test_health_fails_if_approval_or_active_mutation_detected(tmp_path: Path) -> None:
    root = _build_acceptance_root(tmp_path)
    metadata_path = next(root.glob("*/metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["active_worklist_mutated"] = True
    metadata["no_approval_applied"] = False
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_reviewed_replacement_worklist_acceptance_health(root=root, output_dir=tmp_path / "health")

    issues = set(result.health_frame["issue_code"])
    assert result.status == "FAIL"
    assert "ACTIVE_WORKLIST_MUTATION_DETECTED" in issues
    assert "APPROVAL_APPLIED_DETECTED" in issues


def test_status_summarizes_latest_acceptance(tmp_path: Path) -> None:
    root = _build_acceptance_root(tmp_path)

    result = run_reviewed_replacement_worklist_acceptance_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == "REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT"
    assert result.row_count == 3
    assert result.stock_core_row_count == 2
    assert result.etf_core_row_count == 1
    assert result.acceptance_acknowledged is True


def test_research_status_includes_acceptance_and_preserves_paper_priority(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    acceptance_root = _build_acceptance_root(tmp_path)
    _write_paper_workflow_status(root)

    result = run_local_research_dashboard(
        root=root,
        reviewed_replacement_worklist_acceptance_root=acceptance_root,
        output_dir=tmp_path / "dashboard",
    )

    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.latest_reviewed_replacement_worklist_acceptance_id
    assert result.reviewed_replacement_worklist_acceptance_status == "PASS"
    assert result.reviewed_replacement_worklist_acceptance_stage == (
        "REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT"
    )
    assert result.reviewed_replacement_worklist_acceptance_stock_core_row_count == 2
    assert result.reviewed_replacement_worklist_acceptance_active_worklist_mutated is False
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert exported.iloc[0]["reviewed_replacement_worklist_acceptance_stock_core_row_count"] == "2"
    assert metadata["reviewed_replacement_worklist_acceptance_stock_core_row_count"] == 2


def test_cli_index_health_status_and_research_status_work(tmp_path: Path, capsys) -> None:
    root = _build_acceptance_root(tmp_path)

    assert (
        cli.main(
            [
                "reviewed-replacement-worklist-acceptance-index",
                "--root",
                str(root),
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
                "reviewed-replacement-worklist-acceptance-health",
                "--root",
                str(root),
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
                "reviewed-replacement-worklist-acceptance-status",
                "--root",
                str(root),
                "--output-dir",
                str(tmp_path / "status"),
            ]
        )
        == 0
    )
    assert "workflow_stage: REVIEWED_REPLACEMENT_WORKLIST_ACCEPTED_AS_PLANNING_CONTEXT" in capsys.readouterr().out

    assert (
        cli.main(
            [
                "research-status",
                "--root",
                str(tmp_path / "reports"),
                "--reviewed-replacement-worklist-acceptance-root",
                str(root),
                "--output-dir",
                str(tmp_path / "dashboard"),
            ]
        )
        == 0
    )
    assert "latest_reviewed_replacement_worklist_acceptance_id:" in capsys.readouterr().out


def test_no_generation_or_trading_side_effects(tmp_path: Path) -> None:
    root = _build_acceptance_root(tmp_path)
    result = check_reviewed_replacement_worklist_acceptance_health(root=root, output_dir=tmp_path / "health")

    assert result.audit_metadata["active_worklist_mutated"] is False
    assert result.audit_metadata["no_approval_applied"] is True
    assert result.audit_metadata["no_rejection_applied"] is True
    assert result.audit_metadata["no_universe_export"] is True
    assert result.audit_metadata["no_data_raw_write"] is True
    assert result.audit_metadata["no_data_processed_write"] is True
    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["forward_returns_computed"] is False
    assert result.audit_metadata["network_api_called"] is False
    assert result.audit_metadata["broker_api_invoked"] is False
    assert result.audit_metadata["message_sent"] is False


def _build_acceptance_root(tmp_path: Path) -> Path:
    split_plan = _build_split_plan(tmp_path)
    plan = build_reviewed_replacement_worklist_plan(
        split_plan=split_plan.artifact_paths["plan_csv"],
        output_dir=tmp_path / "replacement_plan",
    )
    root = tmp_path / "acceptance"
    build_reviewed_replacement_worklist_acceptance(
        replacement_plan=plan.artifact_paths["reviewed_replacement_worklist_plan"],
        accepted_by="reviewer-a",
        accepted_at="2024-05-30T10:00:00",
        acceptance_reason="Reviewed split templates for planning.",
        manual_acceptance=True,
        output_dir=root,
    )
    return root


def _build_split_plan(tmp_path: Path):
    rows = [
        _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
        _worklist_row("2024-04-02", "000002", "etf_core", "STOCK"),
        _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
    ]
    worklist = _write_worklist(tmp_path / "worklist.csv", rows)
    registry = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")
    return build_universe_profile_split_worklist_plan(
        worklist=worklist,
        policy_audit=policy.artifact_paths["audit_csv"],
        profiles=registry,
        output_dir=tmp_path / "split_plan",
    )


def _write_registry(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "profiles:",
                "  stock_core:",
                "    allowed_instrument_types: [STOCK]",
                "    profile_type: production_candidate",
                "    mixed_allowed: false",
                "    demo_only: false",
                "  etf_core:",
                "    allowed_instrument_types: [ETF]",
                "    profile_type: production_candidate",
                "    mixed_allowed: false",
                "    demo_only: false",
                "  mixed_demo_core:",
                "    allowed_instrument_types: [STOCK, ETF]",
                "    profile_type: demo_mixed",
                "    mixed_allowed: true",
                "    demo_only: true",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_worklist(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _worklist_row(signal_date: str, symbol: str, universe_name: str, instrument_type: str) -> dict:
    return {
        "worklist_id": "1c7972988f59",
        "review_id": "7bc8ba08bf5a",
        "signal_date": signal_date,
        "symbol": symbol,
        "universe_name": universe_name,
        "suggested_instrument_type": instrument_type,
        "current_review_status": "NEEDS_MANUAL_REVIEW",
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "worklist_only": True,
    }


def _write_paper_workflow_status(root: Path) -> None:
    folder = root / "paper_trading" / "workflow_status" / "paper-workflow-status-a"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "paper_workflow_status_report.md"
    report.write_text("No broker or live trading integration was invoked.", encoding="utf-8")
    metadata = {
        "workflow_status_id": "paper-workflow-status-a",
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
