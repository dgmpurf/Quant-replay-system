from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.local_research_dashboard import run_local_research_dashboard
from quant_replay_system.universe_profile_policy_audit import build_universe_profile_policy_audit
from quant_replay_system.universe_profile_split_worklist_plan import build_universe_profile_split_worklist_plan
from quant_replay_system.universe_profile_split_worklist_plan_health import (
    check_universe_profile_split_worklist_plan_health,
)
from quant_replay_system.universe_profile_split_worklist_plan_index import (
    build_universe_profile_split_worklist_plan_index,
)
from quant_replay_system.universe_profile_split_worklist_plan_status import (
    run_universe_profile_split_worklist_plan_status,
)


def test_index_detects_fake_split_worklist_plan_artifacts(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=True)

    result = build_universe_profile_split_worklist_plan_index(root=root, output_dir=tmp_path / "index")

    assert result.artifact_count == 1
    row = result.index_frame.iloc[0]
    assert row["row_count"] == 2
    assert row["stock_row_count"] == 1
    assert row["etf_row_count"] == 1
    assert row["legacy_mixed_demo_row_count"] == 2
    assert row["profile_conflict_count"] == 1
    assert row["active_worklist_mutated"] == False  # noqa: E712
    assert row["no_approval_applied"] == True  # noqa: E712


def test_health_warns_for_profile_conflict_context(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=True)

    result = check_universe_profile_split_worklist_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "WARN"
    assert result.error_count == 0
    assert "PROFILE_CONFLICT_CONTEXT" in set(result.health_frame["issue_code"])


def test_health_fails_if_active_worklist_mutated(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=False)
    metadata_path = next(root.glob("*/metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["active_worklist_mutated"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_universe_profile_split_worklist_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "ACTIVE_WORKLIST_MUTATION_DETECTED" in set(result.health_frame["issue_code"])


def test_health_fails_if_approval_or_rejection_applied(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=False)
    plan_csv = next(root.glob("*/universe_profile_split_worklist_plan.csv"))
    frame = pd.read_csv(plan_csv, keep_default_na=False)
    frame.loc[0, "should_approve"] = True
    frame.to_csv(plan_csv, index=False)

    result = check_universe_profile_split_worklist_plan_health(root=root, output_dir=tmp_path / "health")

    assert result.status == "FAIL"
    assert "APPROVAL_APPLIED_DETECTED" in set(result.health_frame["issue_code"])


def test_health_fails_if_data_write_or_current_candidates_generation_detected(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=False)
    metadata_path = next(root.glob("*/metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["no_data_raw_write"] = False
    metadata["no_data_processed_write"] = False
    metadata["current_candidates_executed"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = check_universe_profile_split_worklist_plan_health(root=root, output_dir=tmp_path / "health")

    issues = set(result.health_frame["issue_code"])
    assert result.status == "FAIL"
    assert "DATA_RAW_WRITE_DETECTED" in issues
    assert "DATA_PROCESSED_WRITE_DETECTED" in issues
    assert "CURRENT_CANDIDATES_GENERATED" in issues


def test_status_stage_has_profile_conflicts_for_current_mixed_legacy_case(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=True)

    result = run_universe_profile_split_worklist_plan_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "WARN"
    assert result.workflow_stage == "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS"
    assert result.profile_conflict_count == 1


def test_status_stage_ready_for_clean_split_case(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=False)

    result = run_universe_profile_split_worklist_plan_status(root=root, output_dir=tmp_path / "status")

    assert result.status == "PASS"
    assert result.workflow_stage == "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_READY"
    assert result.profile_conflict_count == 0


def test_research_status_includes_split_plan_fields(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    plan_root = _build_split_plan_root(tmp_path, mixed=True)

    result = run_local_research_dashboard(
        root=root,
        universe_profile_split_worklist_plan_root=plan_root,
        output_dir=tmp_path / "dashboard",
    )

    assert result.latest_universe_profile_split_worklist_plan_id
    assert result.universe_profile_split_worklist_plan_status == "WARN"
    assert result.universe_profile_split_worklist_plan_stage == "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS"
    assert result.universe_profile_split_worklist_plan_stock_row_count == 1
    assert result.universe_profile_split_worklist_plan_etf_row_count == 1
    assert result.universe_profile_split_worklist_plan_profile_conflict_count == 1
    assert result.workflow_stage == "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS"
    exported = pd.read_csv(result.artifact_paths["local_research_summary"], dtype=str).fillna("")
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert exported.iloc[0]["universe_profile_split_worklist_plan_profile_conflict_count"] == "1"
    assert metadata["universe_profile_split_worklist_plan_profile_conflict_count"] == 1


def test_research_status_preserves_later_paper_workflow_priority(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    plan_root = _build_split_plan_root(tmp_path, mixed=True)
    _write_paper_workflow_status(root)

    result = run_local_research_dashboard(
        root=root,
        universe_profile_split_worklist_plan_root=plan_root,
        output_dir=tmp_path / "dashboard",
    )

    plan_row = result.dashboard_frame.loc[
        result.dashboard_frame["component"] == "UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_STATUS"
    ].iloc[0]
    assert result.workflow_stage == "PAPER_WORKFLOW_READY"
    assert result.universe_profile_split_worklist_plan_profile_conflict_count == 1
    assert plan_row["warning_classification"] == "STALE_ARTIFACT_WARNING"


def test_cli_index_health_status_work(tmp_path: Path, capsys) -> None:
    root = _build_split_plan_root(tmp_path, mixed=True)

    assert cli.main(["universe-profile-split-worklist-plan-index", "--root", str(root), "--output-dir", str(tmp_path / "index")]) == 0
    assert "artifact_count: 1" in capsys.readouterr().out

    assert cli.main(["universe-profile-split-worklist-plan-health", "--root", str(root), "--output-dir", str(tmp_path / "health")]) == 0
    assert "Health status: WARN" in capsys.readouterr().out

    assert cli.main(["universe-profile-split-worklist-plan-status", "--root", str(root), "--output-dir", str(tmp_path / "status")]) == 0
    output = capsys.readouterr().out
    assert "workflow_stage: UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS" in output
    assert "No approval, rejection, active worklist mutation" in output


def test_cli_research_status_prints_split_worklist_plan_fields(tmp_path: Path, capsys) -> None:
    root = tmp_path / "reports"
    plan_root = _build_split_plan_root(tmp_path, mixed=True)

    assert (
        cli.main(
            [
                "research-status",
                "--root",
                str(root),
                "--universe-profile-split-worklist-plan-root",
                str(plan_root),
                "--output-dir",
                str(tmp_path / "dashboard"),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "latest_universe_profile_split_worklist_plan_id:" in output
    assert "universe_profile_split_worklist_plan_stage: UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS" in output
    assert "universe_profile_split_worklist_plan_profile_conflict_count: 1" in output


def test_no_trading_or_export_side_effects(tmp_path: Path) -> None:
    root = _build_split_plan_root(tmp_path, mixed=False)
    result = check_universe_profile_split_worklist_plan_health(root=root, output_dir=tmp_path / "health")

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
    assert not (tmp_path / "data" / "raw").exists()
    assert not (tmp_path / "data" / "processed").exists()


def _build_split_plan_root(tmp_path: Path, *, mixed: bool) -> Path:
    rows = (
        [
            _worklist_row("2024-04-02", "000001", "etf_core", "STOCK"),
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
        ]
        if mixed
        else [
            _worklist_row("2024-04-02", "510300", "etf_core", "ETF"),
            _worklist_row("2024-04-09", "159915", "etf_core", "ETF"),
        ]
    )
    worklist = _write_worklist(tmp_path / "worklist.csv", rows)
    registry_path = _write_registry(tmp_path / "profiles.yaml")
    policy = build_universe_profile_policy_audit(worklist=worklist, output_dir=tmp_path / "audit")
    root = tmp_path / "split_plans"
    build_universe_profile_split_worklist_plan(
        worklist=worklist,
        policy_audit=policy.artifact_paths["audit_csv"],
        profiles=registry_path,
        output_dir=root,
    )
    return root


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
        "worklist_id": "worklist001",
        "review_id": "review001",
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
